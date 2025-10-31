"""
Filter Event Model

This model logs all safety filter activations for monitoring and analysis.
Does NOT store message content for privacy (FR-056).
"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, DateTime, Text, Float, Boolean, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base
from app.models.safety_filter_rule import FilterCategory


class FilterEvent(Base):
    """
    Filter Event Logging Model

    Logs all filter activations without storing message content.
    Used for monitoring, statistics, and detecting false positives.

    IMPORTANT: Per FR-056, message content is NEVER stored.
    """
    __tablename__ = "filter_events"

    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Event metadata
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), nullable=True, index=True)

    # Filter details
    category = Column(String(50), nullable=False, index=True)  # FilterCategory value
    filter_type = Column(String(20), nullable=False)  # "rule_based" or "ml_based"
    filter_phase = Column(String(10), nullable=False)  # "input" or "output"

    # Rule information (if rule-based)
    rule_id = Column(UUID(as_uuid=True), nullable=True)
    rule_name = Column(String(100), nullable=True)
    matched_keyword = Column(String(100), nullable=True)  # Which keyword matched (for debugging)

    # ML filter information (if ML-based)
    confidence_score = Column(Float, nullable=True)  # ML model confidence (0.0-1.0)

    # Action taken
    action = Column(String(20), nullable=False)  # "blocked", "masked", "warned"
    bypass_attempted = Column(Boolean, default=False, nullable=False)  # User tried to bypass
    bypass_succeeded = Column(Boolean, default=False, nullable=False)

    # Timing
    processing_time_ms = Column(Integer, nullable=True)  # Filter processing time
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Additional context (NO message content)
    message_length = Column(Integer, nullable=True)  # Length of filtered message
    client_ip = Column(String(45), nullable=True)  # IPv4/IPv6 address
    user_agent = Column(String(200), nullable=True)

    def __repr__(self):
        return f"<FilterEvent(id={self.id}, category={self.category}, type={self.filter_type}, action={self.action})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id),
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
            "category": self.category,
            "filter_type": self.filter_type,
            "filter_phase": self.filter_phase,
            "rule_id": str(self.rule_id) if self.rule_id else None,
            "rule_name": self.rule_name,
            "matched_keyword": self.matched_keyword,
            "confidence_score": self.confidence_score,
            "action": self.action,
            "bypass_attempted": self.bypass_attempted,
            "bypass_succeeded": self.bypass_succeeded,
            "processing_time_ms": self.processing_time_ms,
            "created_at": self.created_at.isoformat(),
            "message_length": self.message_length,
            "client_ip": self.client_ip
        }
