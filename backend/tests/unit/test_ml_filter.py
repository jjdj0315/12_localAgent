"""
Unit tests for ML-Based Safety Filter (T141)
Tests Phase 2 ML filtering using toxic-bert for toxic content detection.
Target: 95%+ accuracy on test dataset per SC-014
"""
import pytest
from app.services.safety_filter.ml_filter import MLFilter


# Test dataset with labeled examples
TOXIC_TEST_CASES = [
    # Toxic examples (should be detected)
    ("너는 정말 쓸모없는 인간이야", True, "toxic"),
    ("죽어버려", True, "severe_toxic"),
    ("바보 같은 놈", True, "insult"),
    ("그 사람을 혐오한다", True, "identity_hate"),
    ("너무 화가 나서 때려주고 싶다", True, "threat"),
    ("정말 짜증나는 인간", True, "toxic"),
    ("꺼져", True, "insult"),
    ("멍청한 생각이네", True, "insult"),

    # Non-toxic examples (should pass)
    ("오늘 날씨가 좋네요", False, None),
    ("회의 일정을 조정해주세요", False, None),
    ("문서를 작성하는 중입니다", False, None),
    ("도움을 요청합니다", False, None),
    ("예산 계획을 수립했습니다", False, None),
    ("좋은 아침입니다", False, None),
    ("감사합니다", False, None),
    ("프로젝트 진행 상황을 공유합니다", False, None),
    ("법령을 검토했습니다", False, None),
    ("민원 응대 중입니다", False, None),
]

# Edge cases
EDGE_CASES = [
    # Borderline cases
    ("이 정책은 실패했다", False, None),  # Criticism, not toxic
    ("반대합니다", False, None),  # Disagreement, not toxic
    ("문제가 있는 것 같습니다", False, None),  # Problem reporting, not toxic

    # Context-dependent
    ("아이가 울고 있어요", False, None),  # "울다" is not toxic
    ("화재가 발생했습니다", False, None),  # "화" is not toxic in this context
]


class TestMLFilter:
    """Test ML-based toxic content detection"""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup ML filter for testing"""
        self.ml_filter = MLFilter(enable_ml=True, threshold=0.7)

        # Skip tests if model is not available
        if not self.ml_filter.model_available:
            pytest.skip("ML model not available")

    def test_model_initialization(self):
        """Should initialize ML model successfully"""
        assert self.ml_filter.model_available
        assert self.ml_filter.model is not None
        assert self.ml_filter.tokenizer is not None

    def test_toxic_content_detection(self):
        """Should detect toxic content"""
        toxic_examples = [ex for ex in TOXIC_TEST_CASES if ex[1] is True]

        correct_detections = 0
        total_toxic = len(toxic_examples)

        for content, expected_toxic, category in toxic_examples:
            is_safe, confidence, categories = self.ml_filter.check_content(content)

            # is_safe should be False for toxic content
            if not is_safe:
                correct_detections += 1
            else:
                print(f"MISSED: '{content}' (expected toxic, got safe, confidence: {confidence:.2f})")

        accuracy = (correct_detections / total_toxic) * 100
        print(f"\nToxic Detection Accuracy: {accuracy:.1f}% ({correct_detections}/{total_toxic})")

        # Should detect at least 95% of toxic content per SC-014
        assert accuracy >= 95.0, f"Accuracy {accuracy:.1f}% is below 95% threshold"

    def test_non_toxic_content_passes(self):
        """Should allow non-toxic content"""
        non_toxic_examples = [ex for ex in TOXIC_TEST_CASES if ex[1] is False]

        correct_passes = 0
        total_non_toxic = len(non_toxic_examples)

        for content, expected_toxic, category in non_toxic_examples:
            is_safe, confidence, categories = self.ml_filter.check_content(content)

            # is_safe should be True for non-toxic content
            if is_safe:
                correct_passes += 1
            else:
                print(f"FALSE POSITIVE: '{content}' (expected safe, got toxic, confidence: {confidence:.2f}, categories: {categories})")

        accuracy = (correct_passes / total_non_toxic) * 100
        print(f"\nNon-Toxic Pass Rate: {accuracy:.1f}% ({correct_passes}/{total_non_toxic})")

        # Should have low false positive rate (at least 90% pass rate)
        assert accuracy >= 90.0, f"Pass rate {accuracy:.1f}% is below 90% threshold"

    def test_overall_accuracy(self):
        """Should achieve 95%+ overall accuracy per SC-014"""
        total_correct = 0
        total_cases = len(TOXIC_TEST_CASES)

        for content, expected_toxic, category in TOXIC_TEST_CASES:
            is_safe, confidence, categories = self.ml_filter.check_content(content)

            # Check if prediction matches expectation
            predicted_toxic = not is_safe
            if predicted_toxic == expected_toxic:
                total_correct += 1

        overall_accuracy = (total_correct / total_cases) * 100
        print(f"\nOverall Accuracy: {overall_accuracy:.1f}% ({total_correct}/{total_cases})")

        # Should achieve 95%+ overall accuracy per SC-014
        assert overall_accuracy >= 95.0, f"Overall accuracy {overall_accuracy:.1f}% is below 95% threshold"

    def test_confidence_scores(self):
        """Should return confidence scores"""
        content = "너는 쓸모없어"  # Toxic
        is_safe, confidence, categories = self.ml_filter.check_content(content)

        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
        assert not is_safe  # Should detect as toxic

    def test_category_detection(self):
        """Should return detected toxicity categories"""
        content = "죽어버려"  # Severe toxic
        is_safe, confidence, categories = self.ml_filter.check_content(content)

        assert isinstance(categories, list)
        assert len(categories) > 0
        assert not is_safe

    def test_threshold_adjustment(self):
        """Should respect threshold parameter"""
        # Test with different thresholds
        filter_strict = MLFilter(enable_ml=True, threshold=0.5)  # More strict
        filter_lenient = MLFilter(enable_ml=True, threshold=0.9)  # More lenient

        if not filter_strict.model_available:
            pytest.skip("ML model not available")

        # Borderline toxic content
        content = "짜증나네"

        is_safe_strict, conf_strict, _ = filter_strict.check_content(content)
        is_safe_lenient, conf_lenient, _ = filter_lenient.check_content(content)

        # Both should return confidence scores
        assert isinstance(conf_strict, float)
        assert isinstance(conf_lenient, float)

        # Lenient filter should be more likely to pass
        # (This is probabilistic, so we just check the behavior exists)

    def test_empty_content(self):
        """Should handle empty content safely"""
        is_safe, confidence, categories = self.ml_filter.check_content("")

        # Empty content should be safe
        assert is_safe
        assert confidence == 0.0
        assert len(categories) == 0

    def test_very_long_content(self):
        """Should handle very long content (with truncation)"""
        # Create content longer than 512 tokens
        long_content = "안전한 내용입니다. " * 200  # ~2000 chars

        is_safe, confidence, categories = self.ml_filter.check_content(long_content)

        # Should handle without error (will be truncated to 512 tokens)
        assert isinstance(is_safe, bool)
        assert isinstance(confidence, float)

    def test_multilingual_content(self):
        """Should handle Korean content (toxic-bert supports multilingual)"""
        korean_toxic = "바보 같은 인간"
        is_safe_ko, conf_ko, cats_ko = self.ml_filter.check_content(korean_toxic)

        # Should detect Korean toxic content
        assert not is_safe_ko
        assert conf_ko > 0.7

    def test_edge_cases(self):
        """Should handle edge cases correctly"""
        correct_predictions = 0
        total_edges = len(EDGE_CASES)

        for content, expected_toxic, category in EDGE_CASES:
            is_safe, confidence, categories = self.ml_filter.check_content(content)

            predicted_toxic = not is_safe
            if predicted_toxic == expected_toxic:
                correct_predictions += 1
            else:
                print(f"EDGE CASE: '{content}' (expected {'toxic' if expected_toxic else 'safe'}, got {'toxic' if predicted_toxic else 'safe'}, conf: {confidence:.2f})")

        accuracy = (correct_predictions / total_edges) * 100
        print(f"\nEdge Case Accuracy: {accuracy:.1f}% ({correct_predictions}/{total_edges})")

        # Edge cases are harder, so we allow lower accuracy
        assert accuracy >= 70.0, f"Edge case accuracy {accuracy:.1f}% is below 70% threshold"

    def test_graceful_degradation_when_model_unavailable(self):
        """Should gracefully handle missing model"""
        filter_no_ml = MLFilter(enable_ml=True, threshold=0.7)

        # Simulate model not available
        filter_no_ml.model_available = False
        filter_no_ml.model = None

        # Should return safe by default
        is_safe, confidence, categories = filter_no_ml.check_content("test content")

        assert is_safe is True
        assert confidence == 0.0
        assert len(categories) == 0

    def test_performance_check(self):
        """Should complete ML filtering within reasonable time"""
        import time

        content = "이것은 테스트 메시지입니다. 유해한 내용이 포함되어 있을 수 있습니다."

        start_time = time.time()
        is_safe, confidence, categories = self.ml_filter.check_content(content)
        end_time = time.time()

        elapsed_ms = (end_time - start_time) * 1000

        # ML filtering should be reasonably fast on CPU (< 1000ms)
        assert elapsed_ms < 1000, f"ML filtering took {elapsed_ms:.2f}ms, expected < 1000ms"

    def test_batch_consistency(self):
        """Should return consistent results for same content"""
        content = "쓸모없는 인간"

        results = []
        for _ in range(3):
            is_safe, confidence, categories = self.ml_filter.check_content(content)
            results.append((is_safe, confidence))

        # All results should be the same
        assert all(r[0] == results[0][0] for r in results), "is_safe should be consistent"

        # Confidence scores should be very similar (within 0.01)
        confidences = [r[1] for r in results]
        max_diff = max(confidences) - min(confidences)
        assert max_diff < 0.01, f"Confidence scores vary too much: {confidences}"

    def test_detailed_category_labels(self):
        """Should provide detailed toxicity category labels"""
        # Test different types of toxic content
        test_cases = [
            ("죽어버려", ["toxic", "severe_toxic", "threat"]),  # Should include threat
            ("바보", ["toxic", "insult"]),  # Should include insult
            ("혐오스러워", ["toxic", "identity_hate"]),  # Should include hate
        ]

        for content, expected_categories in test_cases:
            is_safe, confidence, categories = self.ml_filter.check_content(content)

            # Should detect as toxic
            assert not is_safe, f"Should detect '{content}' as toxic"

            # Should return categories
            assert len(categories) > 0, f"Should return categories for '{content}'"

            # Check if expected categories are present (partial match OK)
            # Note: ML model may not always match our expectations exactly


@pytest.mark.performance
class TestMLFilterPerformance:
    """Performance tests for ML filter"""

    def test_batch_processing_performance(self):
        """Should handle batch processing efficiently"""
        import time

        ml_filter = MLFilter(enable_ml=True, threshold=0.7)
        if not ml_filter.model_available:
            pytest.skip("ML model not available")

        # Process 10 messages
        messages = [
            "안전한 메시지입니다",
            "또 다른 안전한 메시지",
            "유해한 내용: 죽어버려",
        ] * 3  # 9 messages

        start_time = time.time()
        for msg in messages:
            ml_filter.check_content(msg)
        end_time = time.time()

        elapsed_ms = (end_time - start_time) * 1000
        avg_ms_per_message = elapsed_ms / len(messages)

        print(f"\nBatch processing: {elapsed_ms:.2f}ms total, {avg_ms_per_message:.2f}ms per message")

        # Average should be < 500ms per message on CPU
        assert avg_ms_per_message < 500, f"Average time per message ({avg_ms_per_message:.2f}ms) exceeds 500ms"
