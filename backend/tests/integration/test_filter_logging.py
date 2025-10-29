"""
Integration tests for Filter Event Logging (T144)
Tests that filter events are logged correctly without storing message content per FR-056.

Key requirements:
- Log timestamp, user_id, category, filter_type, action, confidence
- Do NOT store message content (privacy requirement)
- Log bypass attempts
- Log processing time
"""
import pytest
import uuid
import time
from datetime import datetime, timedelta
from app.services.safety_filter_service import SafetyFilterService
from app.models.filter_event import FilterEvent


class TestFilterEventLogging:
    """Test filter event logging"""

    def test_event_logged_on_filter_trigger(self, test_db_session, test_user_id, test_conversation_id):
        """Should log event when filter is triggered"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False
        )

        content = "죽이겠다"  # Will trigger violence filter

        result = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )

        test_db_session.commit()

        # Check that event was logged
        events = test_db_session.query(FilterEvent).filter_by(
            user_id=test_user_id
        ).all()

        assert len(events) > 0, "Event should be logged"

        event = events[0]
        assert event.user_id == test_user_id
        assert event.conversation_id == test_conversation_id
        assert event.category is not None
        assert event.filter_type in ["rule_based", "ml_based"]
        assert event.action in ["blocked", "masked", "warned", "passed"]

    def test_no_message_content_stored(self, test_db_session, test_user_id, test_conversation_id):
        """Should NOT store message content per FR-056 (privacy requirement)"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False
        )

        sensitive_content = "죽이겠다 - 민감한 개인 정보 포함"

        result = filter_service.check_content(
            content=sensitive_content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )

        test_db_session.commit()

        # Check all filter events
        events = test_db_session.query(FilterEvent).filter_by(
            user_id=test_user_id
        ).all()

        assert len(events) > 0

        for event in events:
            # Verify NO message content fields exist or are None
            assert not hasattr(event, 'message_content') or event.message_content is None, \
                   "Should NOT store message content"
            assert not hasattr(event, 'content') or event.content is None, \
                   "Should NOT store content"

            # Should store message length instead
            if hasattr(event, 'message_length'):
                assert isinstance(event.message_length, int)
                assert event.message_length > 0

    def test_logs_required_metadata(self, test_db_session, test_user_id, test_conversation_id):
        """Should log all required metadata fields"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False
        )

        content = "죽이겠다"

        result = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )

        test_db_session.commit()

        events = test_db_session.query(FilterEvent).filter_by(
            user_id=test_user_id
        ).all()

        assert len(events) > 0

        event = events[0]

        # Required fields
        assert event.id is not None, "Should have event ID"
        assert event.user_id == test_user_id, "Should log user ID"
        assert event.conversation_id == test_conversation_id, "Should log conversation ID"
        assert event.category is not None, "Should log category"
        assert event.filter_type is not None, "Should log filter type"
        assert event.action is not None, "Should log action"
        assert event.created_at is not None, "Should log timestamp"
        assert isinstance(event.created_at, datetime), "Timestamp should be datetime"

        # Optional but expected fields
        if hasattr(event, 'message_length'):
            assert isinstance(event.message_length, int)

        if hasattr(event, 'processing_time_ms'):
            assert isinstance(event.processing_time_ms, (int, float))

    def test_logs_bypass_attempts(self, test_db_session, test_user_id, test_conversation_id):
        """Should log bypass attempts"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=False,
            enable_ml=False
        )

        content = "Test bypass"

        result = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=True  # Bypass attempt
        )

        test_db_session.commit()

        events = test_db_session.query(FilterEvent).filter_by(
            user_id=test_user_id,
            bypass_attempted=True
        ).all()

        assert len(events) > 0, "Bypass attempts should be logged"
        assert events[0].bypass_attempted is True

    def test_logs_confidence_score_for_ml(self, test_db_session, test_user_id, test_conversation_id):
        """Should log confidence score for ML-based filtering"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=False,
            enable_ml=True
        )

        if not filter_service.ml_filter.model_available:
            pytest.skip("ML model not available")

        content = "쓸모없는 인간"

        result = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )

        test_db_session.commit()

        events = test_db_session.query(FilterEvent).filter_by(
            user_id=test_user_id,
            filter_type="ml_based"
        ).all()

        if len(events) > 0:
            event = events[0]
            assert event.confidence_score is not None, "Should log confidence score for ML"
            assert isinstance(event.confidence_score, float)
            assert 0.0 <= event.confidence_score <= 1.0

    def test_logs_processing_time(self, test_db_session, test_user_id, test_conversation_id):
        """Should log processing time"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False
        )

        content = "죽이겠다"

        start_time = time.time()
        result = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )
        end_time = time.time()

        test_db_session.commit()

        events = test_db_session.query(FilterEvent).filter_by(
            user_id=test_user_id
        ).all()

        if len(events) > 0 and hasattr(events[0], 'processing_time_ms'):
            event = events[0]
            assert event.processing_time_ms is not None
            assert event.processing_time_ms > 0

            # Should be reasonably close to actual time
            actual_time_ms = (end_time - start_time) * 1000
            # Allow some variance
            assert event.processing_time_ms < actual_time_ms * 2

    def test_separate_events_for_input_and_output(self, test_db_session, test_user_id, test_conversation_id):
        """Should log separate events for input and output phases"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False
        )

        content = "죽이겠다"

        # Input phase
        result1 = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )

        # Output phase
        result2 = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="output",
            bypass_rule_based=False
        )

        test_db_session.commit()

        events = test_db_session.query(FilterEvent).filter_by(
            user_id=test_user_id,
            conversation_id=test_conversation_id
        ).all()

        # Should have at least 2 events (one for each phase)
        assert len(events) >= 2

        # Check phases are logged
        if hasattr(events[0], 'phase'):
            phases = [e.phase for e in events]
            assert "input" in phases or "output" in phases

    def test_multiple_events_for_same_conversation(self, test_db_session, test_user_id, test_conversation_id):
        """Should log multiple events for same conversation"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False
        )

        # Make 3 filter checks
        for i in range(3):
            content = f"죽이겠다 {i}"
            result = filter_service.check_content(
                content=content,
                user_id=test_user_id,
                conversation_id=test_conversation_id,
                phase="input",
                bypass_rule_based=False
            )

        test_db_session.commit()

        events = test_db_session.query(FilterEvent).filter_by(
            user_id=test_user_id,
            conversation_id=test_conversation_id
        ).all()

        assert len(events) >= 3, "Should log all filter checks"

    def test_no_duplicate_events(self, test_db_session, test_user_id, test_conversation_id):
        """Should not create duplicate events for same check"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False
        )

        content = "죽이겠다"

        # Count events before
        events_before = test_db_session.query(FilterEvent).filter_by(
            user_id=test_user_id
        ).count()

        result = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )

        test_db_session.commit()

        # Count events after
        events_after = test_db_session.query(FilterEvent).filter_by(
            user_id=test_user_id
        ).count()

        # Should have exactly 1 more event
        assert events_after == events_before + 1

    def test_query_events_by_time_range(self, test_db_session, test_user_id, test_conversation_id):
        """Should be able to query events by time range"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False
        )

        content = "죽이겠다"

        # Create event
        result = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )

        test_db_session.commit()

        # Query events from last hour
        time_threshold = datetime.utcnow() - timedelta(hours=1)
        recent_events = test_db_session.query(FilterEvent).filter(
            FilterEvent.user_id == test_user_id,
            FilterEvent.created_at >= time_threshold
        ).all()

        assert len(recent_events) > 0

    def test_query_events_by_category(self, test_db_session, test_user_id, test_conversation_id):
        """Should be able to query events by category"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False
        )

        # Trigger violence category
        content = "죽이겠다"

        result = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )

        test_db_session.commit()

        # Query violence events
        violence_events = test_db_session.query(FilterEvent).filter_by(
            user_id=test_user_id,
            category="violence"
        ).all()

        assert len(violence_events) > 0

    def test_logs_action_type_correctly(self, test_db_session, test_user_id, test_conversation_id):
        """Should log correct action type"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False
        )

        # Test blocked action
        blocked_content = "죽이겠다"
        result1 = filter_service.check_content(
            content=blocked_content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )

        test_db_session.commit()

        events = test_db_session.query(FilterEvent).filter_by(
            user_id=test_user_id
        ).all()

        if len(events) > 0:
            event = events[0]
            assert event.action in ["blocked", "masked", "warned", "passed"]

            if not result1.is_safe:
                assert event.action == "blocked"

    def test_privacy_compliance_no_pii_in_logs(self, test_db_session, test_user_id, test_conversation_id):
        """Should ensure no PII is stored in logs (privacy compliance)"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=False,
            enable_ml=False
        )

        # Content with PII
        content_with_pii = "내 주민번호는 123456-1234567이고 전화번호는 010-1234-5678입니다"

        result = filter_service.check_content(
            content=content_with_pii,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )

        test_db_session.commit()

        # Check all events
        events = test_db_session.query(FilterEvent).all()

        for event in events:
            # Convert event to dict to check all fields
            event_dict = {c.name: getattr(event, c.name) for c in event.__table__.columns}

            # Check that no field contains the PII
            for key, value in event_dict.items():
                if isinstance(value, str):
                    assert "123456-1234567" not in value, f"PII found in field {key}"
                    assert "010-1234-5678" not in value, f"PII found in field {key}"


class TestFilterEventStatistics:
    """Test querying filter event statistics"""

    def test_count_events_by_category(self, test_db_session, test_user_id):
        """Should be able to count events by category"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False
        )

        # Create events in different categories
        test_cases = [
            ("죽이겠다", "violence"),
            ("음란한 내용", "sexual"),
            ("혐오스러워", "hate"),
        ]

        conversation_id = uuid.uuid4()

        for content, expected_category in test_cases:
            result = filter_service.check_content(
                content=content,
                user_id=test_user_id,
                conversation_id=conversation_id,
                phase="input",
                bypass_rule_based=False
            )

        test_db_session.commit()

        # Count by category
        from sqlalchemy import func
        category_counts = test_db_session.query(
            FilterEvent.category,
            func.count(FilterEvent.id)
        ).filter(
            FilterEvent.user_id == test_user_id
        ).group_by(FilterEvent.category).all()

        assert len(category_counts) > 0

    def test_average_processing_time(self, test_db_session, test_user_id):
        """Should be able to calculate average processing time"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False
        )

        conversation_id = uuid.uuid4()

        # Create multiple events
        for i in range(5):
            result = filter_service.check_content(
                content=f"죽이겠다 {i}",
                user_id=test_user_id,
                conversation_id=conversation_id,
                phase="input",
                bypass_rule_based=False
            )

        test_db_session.commit()

        # Calculate average
        from sqlalchemy import func
        avg_time = test_db_session.query(
            func.avg(FilterEvent.processing_time_ms)
        ).filter(
            FilterEvent.user_id == test_user_id
        ).scalar()

        if avg_time is not None:
            assert isinstance(avg_time, (int, float))
            assert avg_time > 0

    def test_bypass_attempt_rate(self, test_db_session, test_user_id):
        """Should be able to calculate bypass attempt rate"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=False,
            enable_ml=False
        )

        conversation_id = uuid.uuid4()

        # Create events with and without bypass
        for i in range(3):
            result = filter_service.check_content(
                content=f"Test {i}",
                user_id=test_user_id,
                conversation_id=conversation_id,
                phase="input",
                bypass_rule_based=i % 2 == 0  # Bypass every other
            )

        test_db_session.commit()

        # Count total and bypass events
        total_events = test_db_session.query(FilterEvent).filter_by(
            user_id=test_user_id
        ).count()

        bypass_events = test_db_session.query(FilterEvent).filter_by(
            user_id=test_user_id,
            bypass_attempted=True
        ).count()

        assert total_events > 0
        assert bypass_events > 0

        bypass_rate = (bypass_events / total_events) * 100
        assert 0 <= bypass_rate <= 100
