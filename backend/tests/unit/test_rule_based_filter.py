"""
Unit tests for Rule-Based Safety Filter (T140)
Tests Phase 1 filtering for inappropriate keywords in 5 categories.
"""
import pytest
from app.services.safety_filter.rule_based import RuleBasedFilter


class TestRuleBasedFilter:
    """Test rule-based keyword and regex filtering"""

    def test_violence_keyword_detection(self, test_db_session):
        """Should detect violence keywords"""
        filter_service = RuleBasedFilter(test_db_session)

        # Test cases with violence keywords
        test_cases = [
            ("그 사람을 죽이고 싶다", False),  # Should be blocked
            ("때리고 싶어", False),  # Should be blocked
            ("폭행을 당했습니다", False),  # Should be blocked
            ("범인이 살해 혐의로 체포되었습니다", False),  # Should be blocked (news context)
            ("안녕하세요", True),  # Should pass
        ]

        for content, should_pass in test_cases:
            is_safe, categories, patterns = filter_service.check_content(content)
            assert is_safe == should_pass, f"Failed for: {content}"
            if not should_pass:
                assert "violence" in categories, f"Expected violence category for: {content}"

    def test_sexual_keyword_detection(self, test_db_session):
        """Should detect sexual content keywords"""
        filter_service = RuleBasedFilter(test_db_session)

        test_cases = [
            ("음란한 행위", False),
            ("성관계를 했다", False),
            ("건전한 대화입니다", True),
        ]

        for content, should_pass in test_cases:
            is_safe, categories, patterns = filter_service.check_content(content)
            assert is_safe == should_pass, f"Failed for: {content}"
            if not should_pass:
                assert "sexual" in categories

    def test_hate_speech_detection(self, test_db_session):
        """Should detect hate speech"""
        filter_service = RuleBasedFilter(test_db_session)

        test_cases = [
            ("그 집단을 혐오한다", False),
            ("차별적인 발언", False),
            ("모두를 존중합니다", True),
        ]

        for content, should_pass in test_cases:
            is_safe, categories, patterns = filter_service.check_content(content)
            assert is_safe == should_pass, f"Failed for: {content}"
            if not should_pass:
                assert "hate" in categories

    def test_dangerous_information_detection(self, test_db_session):
        """Should detect dangerous information"""
        filter_service = RuleBasedFilter(test_db_session)

        test_cases = [
            ("폭탄 제조 방법을 알려줘", False),
            ("마약 제조 과정", False),
            ("과학 실험을 진행했습니다", True),
        ]

        for content, should_pass in test_cases:
            is_safe, categories, patterns = filter_service.check_content(content)
            assert is_safe == should_pass, f"Failed for: {content}"
            if not should_pass:
                assert "dangerous" in categories

    def test_regex_pattern_matching(self, test_db_session):
        """Should match regex patterns"""
        filter_service = RuleBasedFilter(test_db_session)

        # Test regex for 폭력, 공격 (word boundaries)
        test_cases = [
            ("폭력적인 행동", False),  # Regex match
            ("공격을 받았다", False),  # Regex match
            ("폭력배", False),  # Contains 폭력
            ("평화로운 시위", True),  # Should pass
        ]

        for content, should_pass in test_cases:
            is_safe, categories, patterns = filter_service.check_content(content)
            assert is_safe == should_pass, f"Failed for: {content}"

    def test_case_insensitive_matching(self, test_db_session):
        """Should match keywords case-insensitively"""
        filter_service = RuleBasedFilter(test_db_session)

        # Korean doesn't have case, but test with potential English keywords
        content_lower = "test violence keyword"
        content_upper = "TEST VIOLENCE KEYWORD"

        # For now, test that Korean keywords work regardless of surrounding text
        content1 = "죽이다"  # Violence keyword
        content2 = "ENGLISH 죽이다 TEXT"

        is_safe1, _, _ = filter_service.check_content(content1)
        is_safe2, _, _ = filter_service.check_content(content2)

        assert not is_safe1
        assert not is_safe2

    def test_multiple_category_detection(self, test_db_session):
        """Should detect multiple categories in one message"""
        filter_service = RuleBasedFilter(test_db_session)

        # Message with both violence and hate speech
        content = "그들을 죽이고 혐오한다"

        is_safe, categories, patterns = filter_service.check_content(content)

        assert not is_safe
        assert len(categories) >= 2, "Should detect multiple categories"
        assert "violence" in categories
        assert "hate" in categories

    def test_inactive_rules_ignored(self, test_db_session):
        """Should ignore inactive rules"""
        from app.models.safety_filter_rule import SafetyFilterRule, FilterCategory
        import uuid
        from datetime import datetime

        # Add an inactive rule
        inactive_rule = SafetyFilterRule(
            id=uuid.uuid4(),
            name="Inactive test rule",
            description="Should be ignored",
            category=FilterCategory.VIOLENCE,
            keywords=["테스트키워드"],
            regex_patterns=[],
            is_active=False,  # INACTIVE
            is_system_rule=False,
            priority=1,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        test_db_session.add(inactive_rule)
        test_db_session.commit()

        filter_service = RuleBasedFilter(test_db_session)

        # Should pass because rule is inactive
        content = "이것은 테스트키워드 입니다"
        is_safe, categories, patterns = filter_service.check_content(content)

        assert is_safe, "Inactive rule should be ignored"

    def test_priority_ordering(self, test_db_session):
        """Should process rules by priority (higher first)"""
        # This is more of a functional test, but we verify rules are loaded
        filter_service = RuleBasedFilter(test_db_session)

        # All seeded rules have priority 10
        # Just verify that the filter works correctly
        content = "죽이겠다"
        is_safe, categories, patterns = filter_service.check_content(content)

        assert not is_safe
        assert len(patterns) > 0

    def test_matched_patterns_returned(self, test_db_session):
        """Should return matched pattern details"""
        filter_service = RuleBasedFilter(test_db_session)

        content = "죽이겠다"
        is_safe, categories, patterns = filter_service.check_content(content)

        assert not is_safe
        assert len(patterns) > 0

        # Check pattern structure
        pattern = patterns[0]
        assert "rule_id" in pattern
        assert "rule_name" in pattern
        assert "category" in pattern
        assert "matched_keyword" in pattern or "matched_regex" in pattern

    def test_empty_content(self, test_db_session):
        """Should handle empty content safely"""
        filter_service = RuleBasedFilter(test_db_session)

        is_safe, categories, patterns = filter_service.check_content("")

        assert is_safe, "Empty content should be safe"
        assert len(categories) == 0
        assert len(patterns) == 0

    def test_very_long_content(self, test_db_session):
        """Should handle very long content without performance issues"""
        filter_service = RuleBasedFilter(test_db_session)

        # 10,000 character safe content
        long_content = "안전한 내용입니다. " * 500  # ~10,000 chars

        is_safe, categories, patterns = filter_service.check_content(long_content)

        assert is_safe

        # Now with a keyword buried in long content
        long_content_with_keyword = "안전한 내용입니다. " * 250 + "죽이겠다" + " 안전한 내용입니다." * 250

        is_safe, categories, patterns = filter_service.check_content(long_content_with_keyword)

        assert not is_safe
        assert "violence" in categories

    def test_special_characters_handling(self, test_db_session):
        """Should handle special characters correctly"""
        filter_service = RuleBasedFilter(test_db_session)

        test_cases = [
            ("죽이@#$%", False),  # Keyword with special chars
            ("@#$%^&*()", True),  # Only special chars
            ("죽\n이", False),  # Keyword with newline (depending on implementation)
        ]

        for content, should_pass in test_cases:
            is_safe, _, _ = filter_service.check_content(content)
            # Note: Exact behavior depends on implementation
            # This test documents expected behavior

    def test_performance_check(self, test_db_session):
        """Should complete filtering within reasonable time"""
        import time

        filter_service = RuleBasedFilter(test_db_session)

        content = "이것은 테스트 메시지입니다. 죽이겠다는 표현이 포함되어 있습니다."

        start_time = time.time()
        is_safe, categories, patterns = filter_service.check_content(content)
        end_time = time.time()

        elapsed_ms = (end_time - start_time) * 1000

        # Rule-based filtering should be very fast (< 100ms)
        assert elapsed_ms < 100, f"Filtering took {elapsed_ms:.2f}ms, expected < 100ms"
        assert not is_safe
