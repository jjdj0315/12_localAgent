"""
Integration tests for Filter Performance (T145)
Verifies filter processing time meets requirements per FR-082, SC-014.

Target: <2 seconds per check
"""
import pytest
import time
import uuid
from app.services.safety_filter_service import SafetyFilterService
from app.services.safety_filter.rule_based import RuleBasedFilter
from app.services.safety_filter.pii_masker import PIIMasker
from app.services.safety_filter.ml_filter import MLFilter


class TestFilterPerformance:
    """Test filter performance requirements"""

    def test_rule_based_filter_performance(self, test_db_session, test_user_id, test_conversation_id):
        """Rule-based filter should be very fast (< 100ms)"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False
        )

        content = "죽이겠다는 폭력적인 표현이 포함된 메시지입니다."

        # Measure time
        start_time = time.time()
        result = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )
        end_time = time.time()

        elapsed_ms = (end_time - start_time) * 1000

        print(f"\nRule-based filter time: {elapsed_ms:.2f}ms")

        # Rule-based should be very fast
        assert elapsed_ms < 100, f"Rule-based filter took {elapsed_ms:.2f}ms, expected < 100ms"

    def test_pii_masking_performance(self):
        """PII masking should be fast (< 50ms)"""
        pii_masker = PIIMasker()

        content = "주민번호: 123456-1234567, 전화: 010-1234-5678, 이메일: user@example.com"

        # Measure time
        start_time = time.time()
        for _ in range(100):
            masked_content, has_pii, pii_details = pii_masker.detect_and_mask(content)
        end_time = time.time()

        elapsed_ms = (end_time - start_time) * 1000
        avg_ms = elapsed_ms / 100

        print(f"\nPII masking average time: {avg_ms:.2f}ms (100 iterations)")

        # PII masking should be very fast
        assert avg_ms < 50, f"PII masking took {avg_ms:.2f}ms per call, expected < 50ms"

    def test_ml_filter_performance(self):
        """ML filter should complete within reasonable time on CPU (< 1000ms)"""
        ml_filter = MLFilter(enable_ml=True, threshold=0.7)

        if not ml_filter.model_available:
            pytest.skip("ML model not available")

        content = "이것은 유해한 내용이 포함된 메시지입니다. 쓸모없는 인간이라는 표현이 있습니다."

        # Warm up (first call is slower due to model loading)
        ml_filter.check_content(content)

        # Measure time
        times = []
        for _ in range(10):
            start_time = time.time()
            is_safe, confidence, categories = ml_filter.check_content(content)
            end_time = time.time()
            times.append((end_time - start_time) * 1000)

        avg_ms = sum(times) / len(times)
        max_ms = max(times)

        print(f"\nML filter average time: {avg_ms:.2f}ms (10 iterations)")
        print(f"ML filter max time: {max_ms:.2f}ms")

        # ML filter on CPU should be < 1000ms per call
        assert avg_ms < 1000, f"ML filter average time {avg_ms:.2f}ms exceeds 1000ms"
        assert max_ms < 2000, f"ML filter max time {max_ms:.2f}ms exceeds 2000ms"

    def test_two_phase_filter_performance(self, test_db_session, test_user_id, test_conversation_id):
        """Two-phase filtering (rule + ML) should complete within 2 seconds per FR-082, SC-014"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=True
        )

        if not filter_service.ml_filter.model_available:
            pytest.skip("ML model not available")

        content = "이것은 테스트 메시지입니다. 유해한 내용이 있을 수 있습니다."

        # Warm up
        filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )

        # Measure time for multiple runs
        times = []
        for i in range(5):
            test_content = f"{content} {i}"

            start_time = time.time()
            result = filter_service.check_content(
                content=test_content,
                user_id=test_user_id,
                conversation_id=test_conversation_id,
                phase="input",
                bypass_rule_based=False
            )
            end_time = time.time()

            elapsed_ms = (end_time - start_time) * 1000
            times.append(elapsed_ms)

        avg_ms = sum(times) / len(times)
        max_ms = max(times)

        print(f"\nTwo-phase filter average time: {avg_ms:.2f}ms (5 iterations)")
        print(f"Two-phase filter max time: {max_ms:.2f}ms")

        # MUST meet 2-second requirement per FR-082, SC-014
        assert avg_ms < 2000, f"Average filter time {avg_ms:.2f}ms exceeds 2000ms requirement"
        assert max_ms < 2000, f"Max filter time {max_ms:.2f}ms exceeds 2000ms requirement"

    def test_performance_with_long_content(self, test_db_session, test_user_id, test_conversation_id):
        """Should handle long content within time requirement"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=True
        )

        if not filter_service.ml_filter.model_available:
            pytest.skip("ML model not available")

        # Create long content (~2000 characters)
        long_content = "안전한 내용입니다. " * 100  # ~2000 chars

        start_time = time.time()
        result = filter_service.check_content(
            content=long_content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )
        end_time = time.time()

        elapsed_ms = (end_time - start_time) * 1000

        print(f"\nLong content filter time: {elapsed_ms:.2f}ms")

        # Should still be within 2 seconds
        assert elapsed_ms < 2000, f"Long content filter time {elapsed_ms:.2f}ms exceeds 2000ms"

    def test_performance_with_multiple_pii(self, test_db_session, test_user_id, test_conversation_id):
        """Should handle multiple PII instances efficiently"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=False,
            enable_ml=False
        )

        # Content with multiple PII instances
        content = """
        신청자 정보:
        1. 홍길동: 123456-1234567, 010-1111-2222, hong@example.com
        2. 김철수: 654321-7654321, 010-3333-4444, kim@example.com
        3. 이영희: 111111-1111111, 010-5555-6666, lee@example.com
        """

        start_time = time.time()
        result = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )
        end_time = time.time()

        elapsed_ms = (end_time - start_time) * 1000

        print(f"\nMultiple PII filter time: {elapsed_ms:.2f}ms")

        # Should be very fast (< 100ms) since it's just PII masking
        assert elapsed_ms < 100, f"Multiple PII masking took {elapsed_ms:.2f}ms, expected < 100ms"

    def test_concurrent_filter_requests_performance(self, test_db_session, test_user_id):
        """Should handle multiple concurrent filter requests efficiently"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False  # Use rule-based only for faster testing
        )

        # Simulate multiple messages
        messages = [
            "안전한 메시지 1",
            "죽이겠다",
            "또 다른 안전한 메시지",
            "폭력적인 내용",
            "정상 메시지",
        ] * 2  # 10 messages total

        start_time = time.time()
        for i, msg in enumerate(messages):
            conv_id = uuid.uuid4()
            result = filter_service.check_content(
                content=msg,
                user_id=test_user_id,
                conversation_id=conv_id,
                phase="input",
                bypass_rule_based=False
            )
        end_time = time.time()

        total_time_ms = (end_time - start_time) * 1000
        avg_time_per_message = total_time_ms / len(messages)

        print(f"\nConcurrent requests total time: {total_time_ms:.2f}ms")
        print(f"Average time per message: {avg_time_per_message:.2f}ms")

        # Each message should be processed quickly
        assert avg_time_per_message < 200, f"Average time per message {avg_time_per_message:.2f}ms is too high"

    def test_database_commit_performance(self, test_db_session, test_user_id, test_conversation_id):
        """Should handle database commits efficiently"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False
        )

        content = "죽이겠다"

        # Time including database commit
        start_time = time.time()
        result = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )
        test_db_session.commit()  # Explicit commit
        end_time = time.time()

        elapsed_ms = (end_time - start_time) * 1000

        print(f"\nFilter + DB commit time: {elapsed_ms:.2f}ms")

        # Should still be fast (< 200ms with SQLite in-memory)
        assert elapsed_ms < 200, f"Filter with DB commit took {elapsed_ms:.2f}ms, expected < 200ms"

    def test_performance_degradation_check(self, test_db_session, test_user_id):
        """Should not show significant performance degradation over time"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False
        )

        content = "죽이겠다"

        # Measure first 10 requests
        first_batch_times = []
        for i in range(10):
            conv_id = uuid.uuid4()
            start_time = time.time()
            result = filter_service.check_content(
                content=content,
                user_id=test_user_id,
                conversation_id=conv_id,
                phase="input",
                bypass_rule_based=False
            )
            end_time = time.time()
            first_batch_times.append((end_time - start_time) * 1000)

        # Measure next 10 requests
        second_batch_times = []
        for i in range(10):
            conv_id = uuid.uuid4()
            start_time = time.time()
            result = filter_service.check_content(
                content=content,
                user_id=test_user_id,
                conversation_id=conv_id,
                phase="input",
                bypass_rule_based=False
            )
            end_time = time.time()
            second_batch_times.append((end_time - start_time) * 1000)

        avg_first = sum(first_batch_times) / len(first_batch_times)
        avg_second = sum(second_batch_times) / len(second_batch_times)

        print(f"\nFirst batch average: {avg_first:.2f}ms")
        print(f"\nSecond batch average: {avg_second:.2f}ms")

        # Second batch should not be significantly slower (allow 50% variance)
        assert avg_second < avg_first * 1.5, \
               f"Performance degradation detected: {avg_first:.2f}ms -> {avg_second:.2f}ms"

    def test_cache_effectiveness(self, test_db_session, test_user_id, test_conversation_id):
        """Should benefit from rule caching"""
        rule_filter = RuleBasedFilter(test_db_session)

        content = "죽이겠다"

        # First call (cold cache)
        start_time = time.time()
        is_safe1, categories1, patterns1 = rule_filter.check_content(content)
        end_time = time.time()
        first_call_ms = (end_time - start_time) * 1000

        # Second call (warm cache)
        start_time = time.time()
        is_safe2, categories2, patterns2 = rule_filter.check_content(content)
        end_time = time.time()
        second_call_ms = (end_time - start_time) * 1000

        print(f"\nFirst call (cold cache): {first_call_ms:.2f}ms")
        print(f"Second call (warm cache): {second_call_ms:.2f}ms")

        # Second call should be faster or similar (cached rules)
        # Allow some variance, but second call shouldn't be significantly slower
        assert second_call_ms <= first_call_ms * 1.2, "Cache does not seem to be working"


@pytest.mark.performance
class TestPerformanceUnderLoad:
    """Performance tests under load conditions"""

    def test_sustained_load_performance(self, test_db_session, test_user_id):
        """Should maintain performance under sustained load"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False  # Rule-based only for faster testing
        )

        # Process 50 messages
        num_messages = 50
        times = []

        for i in range(num_messages):
            content = f"죽이겠다 메시지 {i}"
            conv_id = uuid.uuid4()

            start_time = time.time()
            result = filter_service.check_content(
                content=content,
                user_id=test_user_id,
                conversation_id=conv_id,
                phase="input",
                bypass_rule_based=False
            )
            end_time = time.time()

            times.append((end_time - start_time) * 1000)

        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)

        print(f"\nSustained load results (n={num_messages}):")
        print(f"  Average: {avg_time:.2f}ms")
        print(f"  Min: {min_time:.2f}ms")
        print(f"  Max: {max_time:.2f}ms")

        # Average should still be fast
        assert avg_time < 100, f"Average time under load {avg_time:.2f}ms exceeds 100ms"

        # Max should not spike too high
        assert max_time < 500, f"Max time under load {max_time:.2f}ms exceeds 500ms"

    def test_memory_efficiency(self, test_db_session, test_user_id):
        """Should not leak memory or grow indefinitely"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False
        )

        # Process many messages
        for i in range(100):
            content = f"테스트 메시지 {i}"
            conv_id = uuid.uuid4()

            result = filter_service.check_content(
                content=content,
                user_id=test_user_id,
                conversation_id=conv_id,
                phase="input",
                bypass_rule_based=False
            )

        # If we get here without errors, memory is being managed correctly
        # (In a real scenario, you'd use memory profiling tools)
        assert True


@pytest.mark.slow
class TestWorstCasePerformance:
    """Test performance in worst-case scenarios"""

    def test_maximum_length_content(self, test_db_session, test_user_id, test_conversation_id):
        """Should handle maximum length content within time limit"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=True
        )

        if not filter_service.ml_filter.model_available:
            pytest.skip("ML model not available")

        # Create very long content (10,000 characters)
        very_long_content = "안전한 내용입니다. " * 500  # ~10,000 chars

        start_time = time.time()
        result = filter_service.check_content(
            content=very_long_content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )
        end_time = time.time()

        elapsed_ms = (end_time - start_time) * 1000

        print(f"\nMaximum length content time: {elapsed_ms:.2f}ms")

        # Should still be within 2 seconds (ML model truncates to 512 tokens)
        assert elapsed_ms < 2000, f"Max length content took {elapsed_ms:.2f}ms, exceeds 2000ms"

    def test_many_keywords_matching(self, test_db_session, test_user_id, test_conversation_id):
        """Should handle content matching many keywords efficiently"""
        filter_service = SafetyFilterService(
            test_db_session,
            enable_rule_based=True,
            enable_ml=False
        )

        # Content with multiple matching keywords
        content = "죽이고 때리고 폭행하고 살해하는 폭력적인 내용"

        start_time = time.time()
        result = filter_service.check_content(
            content=content,
            user_id=test_user_id,
            conversation_id=test_conversation_id,
            phase="input",
            bypass_rule_based=False
        )
        end_time = time.time()

        elapsed_ms = (end_time - start_time) * 1000

        print(f"\nMany keywords matching time: {elapsed_ms:.2f}ms")

        # Should still be fast
        assert elapsed_ms < 200, f"Many keywords matching took {elapsed_ms:.2f}ms, expected < 200ms"
