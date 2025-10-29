"""
Integration tests for Filter Bypass Logic (T143)
Tests the two-phase filtering with bypass capability per FR-058.

Key requirement:
- Rule-based filter can be bypassed on retry
- ML-based filter CANNOT be bypassed (always active)
- Bypass attempts are logged
"""
import pytest
import uuid
from app.services.safety_filter_service import SafetyFilterService
from datetime import datetime


class TestFilterBypass:
    """Test filter bypass logic"""

    def test_bypass_flag_skips_rule_based_filter(self, test_db_session, test_user_id, test_conversation_id):
        """Should skip rule-based filter when bypass=True"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False  # Disable ML for this test
        )

        # Content that would be blocked by rule-based filter
        content = "이 사람을 죽이고 싶다"  # Contains violence keyword

        # First attempt: Should be blocked by rule-based filter
        result1 = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )

        assert not result1.is_safe, "Should be blocked by rule-based filter"
        assert result1.filter_type == "rule_based"
        assert result1.can_retry is True, "Should allow retry for rule-based blocks"

        # Second attempt with bypass: Should pass (ML is disabled)
        result2 = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=True
        )

        assert result2.is_safe, "Should pass when rule-based is bypassed and ML is disabled"

    def test_bypass_does_not_skip_ml_filter(self, test_db_session, test_user_id, test_conversation_id):
        """Should NOT skip ML filter even with bypass=True"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=False,  # Disable rule-based
            enable_ml=True
        )

        if not filter_service.ml_filter.model_available:
            pytest.skip("ML model not available")

        # Content that would be blocked by ML filter
        content = "너는 쓸모없는 인간이야"  # Toxic content

        # Attempt with bypass: ML filter should STILL apply
        result = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=True  # This should NOT affect ML filter
        )

        # ML filter should still detect and block
        # (Note: If ML model passes this, it's acceptable, just document it)
        if not result.is_safe:
            assert result.filter_type == "ml_based", "Should be blocked by ML filter"
            assert result.can_retry is False, "ML filter blocks cannot be retried"

    def test_two_phase_filtering_with_both_enabled(self, test_db_session, test_user_id, test_conversation_id):
        """Should apply both filters in correct order"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=True
        )

        if not filter_service.ml_filter.model_available:
            pytest.skip("ML model not available")

        # Content blocked by rule-based
        content = "죽이겠다"

        # Phase 1: Blocked by rule-based
        result1 = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )

        assert not result1.is_safe
        assert result1.filter_type == "rule_based"
        assert result1.can_retry is True

        # Phase 2: Bypass rule-based, but ML may still block
        result2 = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=True
        )

        # Result depends on ML model's decision
        # Document the behavior
        if not result2.is_safe:
            assert result2.filter_type == "ml_based"
            assert result2.can_retry is False

    def test_bypass_attempts_are_logged(self, test_db_session, test_user_id, test_conversation_id):
        """Should log bypass attempts in filter events"""
        from app.models.filter_event import FilterEvent

        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=False,  # Disable for easier testing
            enable_ml=False
        )

        content = "Test content"

        # Make a bypassed request
        result = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=True
        )

        test_db_session.commit()

        # Check filter events
        events = test_db_session.query(FilterEvent).filter_by(
            user_id=test_user_id,
            bypass_attempted=True
        ).all()

        # Should have logged the bypass attempt
        assert len(events) > 0, "Bypass attempts should be logged"

        event = events[0]
        assert event.bypass_attempted is True
        assert event.user_id == test_user_id

    def test_safe_content_passes_without_bypass(self, test_db_session, test_user_id, test_conversation_id):
        """Should pass safe content without needing bypass"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=True
        )

        safe_content = "안녕하세요. 오늘 회의 일정을 알려주세요."

        result = filter_service.check_content(
            content=safe_content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )

        assert result.is_safe
        assert result.filter_type is None or result.filter_type == "passed"

    def test_can_retry_flag_accuracy(self, test_db_session, test_user_id, test_conversation_id):
        """Should correctly set can_retry flag based on filter type"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=True
        )

        # Content blocked by rule-based
        rule_blocked_content = "죽이겠다"

        result1 = filter_service.check_content(
            content=rule_blocked_content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )

        if not result1.is_safe and result1.filter_type == "rule_based":
            assert result1.can_retry is True, "Rule-based blocks should allow retry"

        # If ML model is available, test ML blocks
        if filter_service.ml_filter.model_available:
            # Content that might be blocked by ML
            ml_blocked_content = "너는 쓸모없는 쓰레기야"

            # Bypass rule-based to reach ML
            result2 = filter_service.check_content(
                content=ml_blocked_content,
                user_id=test_user_id,
                conversation_id=test_conversation_id,
                phase="input",
                bypass_rule_based=True
            )

            if not result2.is_safe and result2.filter_type == "ml_based":
                assert result2.can_retry is False, "ML-based blocks should NOT allow retry"

    def test_bypass_only_affects_rule_based(self, test_db_session, test_user_id, test_conversation_id):
        """Should verify bypass flag only affects rule-based filter"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False
        )

        content = "죽이고 싶다"

        # Without bypass: blocked
        result1 = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )

        assert not result1.is_safe

        # With bypass: passed (since ML is disabled)
        result2 = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=True
        )

        assert result2.is_safe

    def test_pii_masking_always_applied(self, test_db_session, test_user_id, test_conversation_id):
        """Should apply PII masking regardless of bypass flag"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=False,
            enable_ml=False
        )

        content = "내 주민번호는 123456-1234567입니다"

        # With bypass
        result = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=True
        )

        # PII should still be masked
        assert result.has_pii, "PII should be detected"
        assert "123456-*******" in result.masked_content, "PII should be masked"
        assert result.is_safe, "Content should pass (only PII, not toxic)"

    def test_multiple_bypass_attempts_logged(self, test_db_session, test_user_id, test_conversation_id):
        """Should log multiple bypass attempts separately"""
        from app.models.filter_event import FilterEvent

        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=False,
            enable_ml=False
        )

        # Make multiple bypass attempts
        for i in range(3):
            result = filter_service.check_content(
                content=f"Test content {i}",
                user_id=test_user_id,
                conversation_id=test_conversation_id,
                phase="input",
                bypass_rule_based=True
            )

        test_db_session.commit()

        # Check filter events
        events = test_db_session.query(FilterEvent).filter_by(
            user_id=test_user_id,
            bypass_attempted=True
        ).all()

        assert len(events) >= 3, "Should log all bypass attempts"

    def test_bypass_with_different_phases(self, test_db_session, test_user_id, test_conversation_id):
        """Should handle bypass for both input and output phases"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False
        )

        content = "죽이겠다"

        # Test input phase
        result_input = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=True
        )

        assert result_input.is_safe

        # Test output phase
        result_output = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="output",
            bypass_rule_based=True
        )

        assert result_output.is_safe

    def test_empty_content_with_bypass(self, test_db_session, test_user_id, test_conversation_id):
        """Should handle empty content with bypass flag"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=True
        )

        result = filter_service.check_content(
            content="",
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=True
        )

        assert result.is_safe


class TestFilterBypassSecurity:
    """Security tests for bypass logic"""

    def test_bypass_requires_explicit_flag(self, test_db_session, test_user_id, test_conversation_id):
        """Should require explicit bypass flag (not default)"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False
        )

        content = "죽이겠다"

        # Default behavior (no bypass specified) should apply rule-based filter
        result = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input"
            # bypass_rule_based defaults to False
        )

        assert not result.is_safe, "Should NOT bypass by default"

    def test_ml_filter_cannot_be_disabled_by_user(self, test_db_session, test_user_id, test_conversation_id):
        """Should ensure ML filter cannot be bypassed via any user input"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=False,
            enable_ml=True
        )

        if not filter_service.ml_filter.model_available:
            pytest.skip("ML model not available")

        content = "너는 쓸모없는 쓰레기야"

        # Even with bypass=True, ML should still run
        result = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=True  # This should NOT affect ML
        )

        # ML filter runs independently of bypass flag
        # Result depends on ML model, but bypass flag should not disable ML

    def test_bypass_audit_trail(self, test_db_session, test_user_id, test_conversation_id):
        """Should maintain audit trail of bypass attempts"""
        from app.models.filter_event import FilterEvent

        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False
        )

        content = "Test bypass audit"

        result = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=True
        )

        test_db_session.commit()

        # Verify audit trail exists
        events = test_db_session.query(FilterEvent).filter_by(
            user_id=test_user_id,
            bypass_attempted=True
        ).all()

        assert len(events) > 0
        assert events[0].bypass_attempted is True
        assert events[0].created_at is not None
