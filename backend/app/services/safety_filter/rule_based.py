"""
Rule-Based Content Filter

Phase 1 filtering using keyword matching and regex patterns.
Covers 5 categories: violence, sexual, dangerous, hate, PII.
"""

import re
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from app.models.safety_filter_rule import SafetyFilterRule, FilterCategory


class RuleBasedFilter:
    """
    Rule-Based Content Filter

    Fast keyword and regex matching for content moderation.
    Optimized for Korean language content.

    Usage:
        filter = RuleBasedFilter(db)
        is_safe, categories, matched = filter.check_content("폭력적인 내용")
    """

    def __init__(self, db: Session):
        self.db = db
        self._rule_cache = None
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes

    def _load_rules(self) -> Dict[str, List[SafetyFilterRule]]:
        """
        Load active rules from database, grouped by category.
        Implements simple caching to reduce database queries.
        """
        now = datetime.utcnow()

        # Check cache
        if self._rule_cache and self._cache_timestamp:
            elapsed = (now - self._cache_timestamp).total_seconds()
            if elapsed < self._cache_ttl:
                return self._rule_cache

        # Load from database
        rules = self.db.query(SafetyFilterRule).filter(
            SafetyFilterRule.is_active == True
        ).order_by(
            SafetyFilterRule.priority.desc(),
            SafetyFilterRule.created_at
        ).all()

        # Group by category
        grouped = {cat.value: [] for cat in FilterCategory}
        for rule in rules:
            grouped[rule.category.value].append(rule)

        # Update cache
        self._rule_cache = grouped
        self._cache_timestamp = now

        return grouped

    def check_content(
        self,
        content: str,
        categories_to_check: Optional[List[str]] = None
    ) -> Tuple[bool, List[str], List[Dict]]:
        """
        Check content against rule-based filters.

        Args:
            content: Text content to check
            categories_to_check: Specific categories to check (None = all)

        Returns:
            Tuple of (is_safe, detected_categories, matched_patterns)
            - is_safe: True if no violations found
            - detected_categories: List of violated categories
            - matched_patterns: List of {category, rule_id, rule_name, keyword/pattern}
        """
        if not content or not content.strip():
            return True, [], []

        rules_by_category = self._load_rules()

        # Determine which categories to check
        if categories_to_check:
            categories = categories_to_check
        else:
            categories = list(rules_by_category.keys())

        detected_categories = []
        matched_patterns = []

        for category in categories:
            rules = rules_by_category.get(category, [])

            for rule in rules:
                # Check keywords (exact match, case-insensitive)
                for keyword in rule.keywords:
                    if keyword.lower() in content.lower():
                        detected_categories.append(category)
                        matched_patterns.append({
                            "category": category,
                            "rule_id": str(rule.id),
                            "rule_name": rule.name,
                            "matched": keyword,
                            "type": "keyword"
                        })
                        # Update match count
                        rule.match_count += 1
                        break  # One match per rule is enough

                # Check regex patterns
                for pattern in rule.regex_patterns:
                    try:
                        if re.search(pattern, content, re.IGNORECASE):
                            detected_categories.append(category)
                            matched_patterns.append({
                                "category": category,
                                "rule_id": str(rule.id),
                                "rule_name": rule.name,
                                "matched": pattern,
                                "type": "regex"
                            })
                            # Update match count
                            rule.match_count += 1
                            break  # One match per rule is enough
                    except re.error as e:
                        # Log regex error but don't fail
                        print(f"Invalid regex pattern in rule {rule.id}: {pattern} - {e}")
                        continue

        # Commit match count updates
        if matched_patterns:
            self.db.commit()

        is_safe = len(detected_categories) == 0

        # Remove duplicates from detected categories
        detected_categories = list(set(detected_categories))

        return is_safe, detected_categories, matched_patterns

    def get_safe_message(self, categories: List[str]) -> str:
        """
        Get user-friendly safe message based on detected categories.

        Args:
            categories: List of detected violation categories

        Returns:
            Korean safe message string
        """
        if not categories:
            return "이 메시지는 안전합니다."

        # Map categories to Korean messages
        category_messages = {
            "violence": "폭력적인 내용",
            "sexual": "부적절한 성적 내용",
            "dangerous": "위험한 정보",
            "hate": "혐오 발언",
            "pii": "개인정보"
        }

        detected = [category_messages.get(cat, cat) for cat in categories]

        if len(detected) == 1:
            return f"죄송합니다. 입력하신 내용에 {detected[0]}이(가) 감지되어 처리할 수 없습니다."
        else:
            detected_str = ", ".join(detected)
            return f"죄송합니다. 입력하신 내용에 다음 항목이 감지되어 처리할 수 없습니다: {detected_str}"

    def clear_cache(self):
        """Clear rule cache (call after updating rules)"""
        self._rule_cache = None
        self._cache_timestamp = None
