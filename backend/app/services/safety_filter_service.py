"""
Safety Filter Service - Two-Phase Orchestrator

Coordinates rule-based and ML-based filtering for content moderation.
Logs filter events and provides bypass logic for false positives.
"""

import time
from typing import Tuple, Optional, Dict, List
from datetime import datetime
from sqlalchemy.orm import Session
from uuid import UUID

from app.services.safety_filter.rule_based import RuleBasedFilter
from app.services.safety_filter.pii_masker import PIIMasker
from app.services.safety_filter.ml_filter import MLFilter
from app.models.filter_event import FilterEvent
from app.schemas.safety_filter import FilterCheckResponse
import logging

logger = logging.getLogger(__name__)


class SafetyFilterService:
    """
    Two-Phase Safety Filter Orchestrator

    Phase 1: Rule-based filter (keywords + regex + PII masking)
    Phase 2: ML-based filter (toxic-bert)

    Features:
    - Input and output filtering
    - PII automatic masking
    - Filter event logging (NO message content per FR-056)
    - False positive bypass (retry with rule-based disabled)
    - Graceful degradation
    """

    def __init__(self, db: Session, enable_ml: bool = True):
        """
        Initialize Safety Filter Service.

        Args:
            db: Database session
            enable_ml: Enable ML-based filtering (default True)
        """
        self.db = db
        self.rule_based_filter = RuleBasedFilter(db)
        self.pii_masker = PIIMasker()

        # Try to load ML filter
        self.ml_filter = None
        if enable_ml:
            try:
                self.ml_filter = MLFilter(confidence_threshold=0.7)
                if self.ml_filter.is_available():
                    logger.info("ML filter loaded successfully")
                else:
                    logger.warning("ML filter not available, using rule-based only")
            except Exception as e:
                logger.warning(f"Failed to initialize ML filter: {e}")
                logger.warning("Continuing with rule-based filtering only")

    def check_content(
        self,
        content: str,
        user_id: UUID,
        conversation_id: Optional[UUID] = None,
        phase: str = "input",
        bypass_rule_based: bool = False
    ) -> FilterCheckResponse:
        """
        Check content through two-phase filtering.

        Args:
            content: Text content to check
            user_id: User ID for logging
            conversation_id: Associated conversation ID
            phase: "input" or "output"
            bypass_rule_based: Skip rule-based filter (retry scenario)

        Returns:
            FilterCheckResponse with results and masked content
        """
        start_time = time.time()

        # Step 1: PII Masking (always applied)
        masked_content, has_pii, pii_details = self.pii_masker.detect_and_mask(content)

        if has_pii:
            logger.info(f"PII detected and masked: {len(pii_details)} types")
            # Log PII masking event
            self._log_filter_event(
                user_id=user_id,
                conversation_id=conversation_id,
                category="pii",
                filter_type="rule_based",
                filter_phase=phase,
                action="masked",
                message_length=len(content),
                processing_time_ms=int((time.time() - start_time) * 1000)
            )

        # Step 2: Rule-Based Filter (unless bypassed)
        rule_violations = []
        rule_matched = []

        if not bypass_rule_based:
            is_safe_rule, detected_categories, matched_patterns = self.rule_based_filter.check_content(masked_content)

            if not is_safe_rule:
                logger.info(f"Rule-based filter violation: {detected_categories}")
                rule_violations = detected_categories
                rule_matched = matched_patterns

                # Log rule-based violation
                for match in matched_patterns:
                    self._log_filter_event(
                        user_id=user_id,
                        conversation_id=conversation_id,
                        category=match["category"],
                        filter_type="rule_based",
                        filter_phase=phase,
                        action="blocked",
                        rule_id=match.get("rule_id"),
                        rule_name=match.get("rule_name"),
                        matched_keyword=match.get("matched"),
                        message_length=len(content),
                        processing_time_ms=int((time.time() - start_time) * 1000)
                    )

                # Return early if rule-based blocked
                return FilterCheckResponse(
                    is_safe=False,
                    filtered_content=masked_content,
                    categories=rule_violations,
                    confidence=None,
                    matched_patterns=[m.get("matched", "") for m in rule_matched],
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    action_taken="blocked",
                    can_retry=True,
                    safe_message=self.rule_based_filter.get_safe_message(rule_violations)
                )

        # Step 3: ML-Based Filter (if available)
        ml_violations = []
        ml_confidence = None

        if self.ml_filter and self.ml_filter.is_available():
            is_safe_ml, confidence, ml_categories = self.ml_filter.check_content(masked_content)
            ml_confidence = confidence

            if not is_safe_ml:
                logger.info(f"ML filter violation: {ml_categories} (confidence: {confidence:.3f})")
                ml_violations = ml_categories

                # Log ML violation
                self._log_filter_event(
                    user_id=user_id,
                    conversation_id=conversation_id,
                    category="toxic",  # ML detects general toxicity
                    filter_type="ml_based",
                    filter_phase=phase,
                    action="blocked",
                    confidence_score=confidence,
                    message_length=len(content),
                    processing_time_ms=int((time.time() - start_time) * 1000)
                )

                return FilterCheckResponse(
                    is_safe=False,
                    filtered_content=masked_content,
                    categories=ml_violations,
                    confidence=ml_confidence,
                    matched_patterns=[],
                    processing_time_ms=int((time.time() - start_time) * 1000),
                    action_taken="blocked",
                    can_retry=False,  # Cannot bypass ML filter
                    safe_message="죄송합니다. 입력하신 내용이 부적절하여 처리할 수 없습니다."
                )

        # All checks passed
        processing_time = int((time.time() - start_time) * 1000)

        # Log if bypassed successfully
        if bypass_rule_based:
            self._log_filter_event(
                user_id=user_id,
                conversation_id=conversation_id,
                category="bypass",
                filter_type="rule_based",
                filter_phase=phase,
                action="bypassed",
                bypass_attempted=True,
                bypass_succeeded=True,
                message_length=len(content),
                processing_time_ms=processing_time
            )

        return FilterCheckResponse(
            is_safe=True,
            filtered_content=masked_content,
            categories=[],
            confidence=ml_confidence,
            matched_patterns=[],
            processing_time_ms=processing_time,
            action_taken="masked" if has_pii else "pass",
            can_retry=False,
            safe_message=None
        )

    def _log_filter_event(
        self,
        user_id: UUID,
        category: str,
        filter_type: str,
        filter_phase: str,
        action: str,
        conversation_id: Optional[UUID] = None,
        rule_id: Optional[str] = None,
        rule_name: Optional[str] = None,
        matched_keyword: Optional[str] = None,
        confidence_score: Optional[float] = None,
        bypass_attempted: bool = False,
        bypass_succeeded: bool = False,
        message_length: Optional[int] = None,
        processing_time_ms: Optional[int] = None
    ):
        """
        Log filter event to database.

        IMPORTANT: Per FR-056, message content is NEVER logged.
        """
        try:
            event = FilterEvent(
                user_id=user_id,
                conversation_id=conversation_id,
                category=category,
                filter_type=filter_type,
                filter_phase=filter_phase,
                rule_id=rule_id,
                rule_name=rule_name,
                matched_keyword=matched_keyword,
                confidence_score=confidence_score,
                action=action,
                bypass_attempted=bypass_attempted,
                bypass_succeeded=bypass_succeeded,
                processing_time_ms=processing_time_ms,
                message_length=message_length
            )
            self.db.add(event)
            self.db.commit()

        except Exception as e:
            logger.error(f"Failed to log filter event: {e}")
            self.db.rollback()

    def get_filter_status(self) -> Dict:
        """Get current filter configuration and status"""
        return {
            "rule_based_enabled": True,
            "ml_based_enabled": self.ml_filter is not None and self.ml_filter.is_available(),
            "pii_masking_enabled": True,
            "ml_model_info": self.ml_filter.get_model_info() if self.ml_filter else None
        }
