"""
Unit tests for PII Masking (T142)
Tests automatic detection and masking of personally identifiable information.
Target: 100% detection per SC-015
"""
import pytest
from app.services.safety_filter.pii_masker import PIIMasker


# Test cases for Korean ID (주민등록번호)
KOREAN_ID_CASES = [
    # Valid formats
    ("주민등록번호는 123456-1234567입니다", True, "123456-*******"),
    ("123456-1234567", True, "123456-*******"),
    ("1234561234567", True, "123456-*******"),  # Without dash
    ("123456 1234567", True, "123456-*******"),  # With space
    ("신원: 990101-2345678", True, "990101-*******"),

    # Multiple IDs in one message
    ("두 사람의 주민등록번호는 123456-1234567과 654321-7654321입니다", True, "masked"),

    # Edge cases
    ("생년월일 000101-3456789", True, "000101-*******"),  # 2000년대 출생
    ("991231-4567890", True, "991231-*******"),  # 1999년 출생
]

# Test cases for phone numbers
PHONE_NUMBER_CASES = [
    # Valid formats
    ("전화번호: 010-1234-5678", True, "010-****-****"),
    ("010-1234-5678", True, "010-****-****"),
    ("01012345678", True, "010-****-****"),  # Without dashes
    ("010 1234 5678", True, "010-****-****"),  # With spaces

    # Various area codes
    ("02-123-4567", True, "02-***-****"),
    ("031-1234-5678", True, "031-****-****"),
    ("051-123-4567", True, "051-***-****"),

    # Mobile prefixes
    ("011-1234-5678", True, "011-****-****"),
    ("016-1234-5678", True, "016-****-****"),
    ("017-1234-5678", True, "017-****-****"),
    ("018-1234-5678", True, "018-****-****"),
    ("019-1234-5678", True, "019-****-****"),

    # Multiple phone numbers
    ("연락처: 010-1111-2222, 010-3333-4444", True, "masked"),
]

# Test cases for email addresses
EMAIL_CASES = [
    # Valid formats
    ("이메일: user@example.com", True, "u***@example.com"),
    ("user@example.com", True, "u***@example.com"),
    ("john.doe@company.co.kr", True, "j***@company.co.kr"),

    # Various domains
    ("admin@government.go.kr", True, "a***@government.go.kr"),
    ("contact@domain.org", True, "c***@domain.org"),

    # Edge cases
    ("a@b.c", True, "a***@b.c"),  # Short email
    ("very.long.username@subdomain.example.com", True, "v***@subdomain.example.com"),

    # Multiple emails
    ("연락처: user1@domain.com, user2@domain.com", True, "masked"),
]

# Combined test cases
COMBINED_CASES = [
    # All three types
    ("이름: 홍길동, 주민번호: 123456-1234567, 전화: 010-1234-5678, 이메일: hong@example.com", True, ["korean_id", "phone", "email"]),

    # Two types
    ("주민번호 123456-1234567, 전화 010-1234-5678", True, ["korean_id", "phone"]),
    ("전화 010-1234-5678, 이메일 user@example.com", True, ["phone", "email"]),
]

# Negative cases (should NOT be detected)
NEGATIVE_CASES = [
    # Not PII
    "안전한 메시지입니다",
    "오늘 날씨가 좋네요",
    "회의 일정을 확인해주세요",

    # Look-alike but not valid
    "날짜: 2023-01-15",  # Date format similar to ID
    "코드: 123456-789",  # Too short
    "번호: 12345-1234567",  # First part wrong length
    "이메일 형식이 잘못됨: user@",  # Incomplete email
    "전화번호가 아님: 123-456",  # Too short
]


class TestPIIMasker:
    """Test PII detection and masking"""

    def test_korean_id_detection(self):
        """Should detect 100% of Korean ID numbers (주민등록번호)"""
        pii_masker = PIIMasker()

        detected_count = 0
        total_count = 0

        for content, should_detect, expected_masked in KOREAN_ID_CASES:
            total_count += 1
            masked_content, has_pii, pii_details = pii_masker.detect_and_mask(content)

            if has_pii and any(detail["type"] == "korean_id" for detail in pii_details):
                detected_count += 1

                # Verify masking format
                assert "123456-*******" in masked_content or "990101-*******" in masked_content or \
                       "000101-*******" in masked_content or "991231-*******" in masked_content or \
                       "654321-*******" in masked_content, \
                       f"Korean ID not properly masked in: {masked_content}"
            else:
                print(f"MISSED Korean ID: {content}")

        detection_rate = (detected_count / total_count) * 100
        print(f"\nKorean ID Detection Rate: {detection_rate:.1f}% ({detected_count}/{total_count})")

        # Must achieve 100% detection per SC-015
        assert detection_rate == 100.0, f"Korean ID detection rate {detection_rate:.1f}% is below 100%"

    def test_phone_number_detection(self):
        """Should detect 100% of phone numbers"""
        pii_masker = PIIMasker()

        detected_count = 0
        total_count = 0

        for content, should_detect, expected_masked in PHONE_NUMBER_CASES:
            total_count += 1
            masked_content, has_pii, pii_details = pii_masker.detect_and_mask(content)

            if has_pii and any(detail["type"] == "phone" for detail in pii_details):
                detected_count += 1

                # Verify masking contains asterisks
                assert "***" in masked_content or "****" in masked_content, \
                       f"Phone number not properly masked in: {masked_content}"
            else:
                print(f"MISSED Phone: {content}")

        detection_rate = (detected_count / total_count) * 100
        print(f"\nPhone Detection Rate: {detection_rate:.1f}% ({detected_count}/{total_count})")

        # Must achieve 100% detection per SC-015
        assert detection_rate == 100.0, f"Phone detection rate {detection_rate:.1f}% is below 100%"

    def test_email_detection(self):
        """Should detect 100% of email addresses"""
        pii_masker = PIIMasker()

        detected_count = 0
        total_count = 0

        for content, should_detect, expected_masked in EMAIL_CASES:
            total_count += 1
            masked_content, has_pii, pii_details = pii_masker.detect_and_mask(content)

            if has_pii and any(detail["type"] == "email" for detail in pii_details):
                detected_count += 1

                # Verify masking format (should have ***)
                assert "***@" in masked_content, \
                       f"Email not properly masked in: {masked_content}"
            else:
                print(f"MISSED Email: {content}")

        detection_rate = (detected_count / total_count) * 100
        print(f"\nEmail Detection Rate: {detection_rate:.1f}% ({detected_count}/{total_count})")

        # Must achieve 100% detection per SC-015
        assert detection_rate == 100.0, f"Email detection rate {detection_rate:.1f}% is below 100%"

    def test_combined_pii_detection(self):
        """Should detect multiple PII types in one message"""
        pii_masker = PIIMasker()

        for content, should_detect, expected_types in COMBINED_CASES:
            masked_content, has_pii, pii_details = pii_masker.detect_and_mask(content)

            assert has_pii, f"Should detect PII in: {content}"

            # Check all expected types are detected
            detected_types = [detail["type"] for detail in pii_details]
            for expected_type in expected_types:
                assert expected_type in detected_types, \
                       f"Should detect {expected_type} in: {content}. Found: {detected_types}"

    def test_no_false_positives(self):
        """Should not detect PII in safe content (no false positives)"""
        pii_masker = PIIMasker()

        false_positives = 0

        for content in NEGATIVE_CASES:
            masked_content, has_pii, pii_details = pii_masker.detect_and_mask(content)

            if has_pii:
                false_positives += 1
                print(f"FALSE POSITIVE: Detected PII in '{content}': {pii_details}")

        false_positive_rate = (false_positives / len(NEGATIVE_CASES)) * 100
        print(f"\nFalse Positive Rate: {false_positive_rate:.1f}% ({false_positives}/{len(NEGATIVE_CASES)})")

        # Should have 0% false positive rate
        assert false_positive_rate == 0.0, f"False positive rate should be 0%, got {false_positive_rate:.1f}%"

    def test_masking_format_korean_id(self):
        """Should mask Korean ID in correct format: 123456-*******"""
        pii_masker = PIIMasker()

        content = "주민번호: 123456-1234567"
        masked_content, has_pii, pii_details = pii_masker.detect_and_mask(content)

        assert has_pii
        assert "123456-*******" in masked_content
        assert "1234567" not in masked_content  # Should be masked

    def test_masking_format_phone(self):
        """Should mask phone number correctly"""
        pii_masker = PIIMasker()

        # Test 010 format
        content = "전화: 010-1234-5678"
        masked_content, has_pii, pii_details = pii_masker.detect_and_mask(content)

        assert has_pii
        assert "010-****-****" in masked_content or "010-" in masked_content
        assert "1234" not in masked_content or masked_content.count("1234") == 0  # Should be masked

    def test_masking_format_email(self):
        """Should mask email correctly: u***@domain.com"""
        pii_masker = PIIMasker()

        content = "이메일: user@example.com"
        masked_content, has_pii, pii_details = pii_masker.detect_and_mask(content)

        assert has_pii
        assert "***@example.com" in masked_content
        assert "user@" not in masked_content  # Username should be masked

    def test_pii_details_structure(self):
        """Should return detailed PII information"""
        pii_masker = PIIMasker()

        content = "주민번호: 123456-1234567, 전화: 010-1234-5678"
        masked_content, has_pii, pii_details = pii_masker.detect_and_mask(content)

        assert has_pii
        assert len(pii_details) >= 2  # Should detect both

        # Check structure
        for detail in pii_details:
            assert "type" in detail
            assert "description" in detail
            assert "count" in detail

            assert detail["type"] in ["korean_id", "phone", "email"]
            assert isinstance(detail["description"], str)
            assert isinstance(detail["count"], int)
            assert detail["count"] > 0

    def test_multiple_same_type_pii(self):
        """Should detect multiple instances of same PII type"""
        pii_masker = PIIMasker()

        content = "주민번호1: 123456-1234567, 주민번호2: 654321-7654321"
        masked_content, has_pii, pii_details = pii_masker.detect_and_mask(content)

        assert has_pii

        # Should detect both IDs
        korean_id_detail = next((d for d in pii_details if d["type"] == "korean_id"), None)
        assert korean_id_detail is not None
        assert korean_id_detail["count"] == 2, f"Should detect 2 Korean IDs, got {korean_id_detail['count']}"

        # Both should be masked
        assert "123456-*******" in masked_content
        assert "654321-*******" in masked_content

    def test_empty_content(self):
        """Should handle empty content safely"""
        pii_masker = PIIMasker()

        masked_content, has_pii, pii_details = pii_masker.detect_and_mask("")

        assert masked_content == ""
        assert has_pii is False
        assert len(pii_details) == 0

    def test_very_long_content_with_pii(self):
        """Should detect PII even in very long content"""
        pii_masker = PIIMasker()

        # Create long content with PII buried inside
        long_content = "안전한 내용입니다. " * 100 + "주민번호: 123456-1234567" + " 안전한 내용입니다." * 100

        masked_content, has_pii, pii_details = pii_masker.detect_and_mask(long_content)

        assert has_pii
        assert any(d["type"] == "korean_id" for d in pii_details)
        assert "123456-*******" in masked_content

    def test_special_characters_around_pii(self):
        """Should detect PII even with special characters around it"""
        pii_masker = PIIMasker()

        test_cases = [
            "[주민번호:123456-1234567]",
            "(전화:010-1234-5678)",
            "Email:user@example.com!",
        ]

        for content in test_cases:
            masked_content, has_pii, pii_details = pii_masker.detect_and_mask(content)
            assert has_pii, f"Should detect PII in: {content}"

    def test_pii_in_different_contexts(self):
        """Should detect PII in various sentence structures"""
        pii_masker = PIIMasker()

        contexts = [
            "민원인의 주민등록번호는 123456-1234567입니다.",
            "연락처를 남겨주세요. 010-1234-5678로 연락 가능합니다.",
            "회신 이메일: user@example.com",
            "제 번호는 010-1234-5678이고, 이메일은 user@example.com입니다.",
        ]

        for content in contexts:
            masked_content, has_pii, pii_details = pii_masker.detect_and_mask(content)
            assert has_pii, f"Should detect PII in: {content}"

    def test_performance(self):
        """Should perform masking quickly"""
        import time

        pii_masker = PIIMasker()

        content = "주민번호: 123456-1234567, 전화: 010-1234-5678, 이메일: user@example.com"

        start_time = time.time()
        for _ in range(100):
            masked_content, has_pii, pii_details = pii_masker.detect_and_mask(content)
        end_time = time.time()

        elapsed_ms = (end_time - start_time) * 1000
        avg_ms = elapsed_ms / 100

        print(f"\nPII Masking Performance: {avg_ms:.2f}ms per call (100 iterations)")

        # Should be very fast (< 10ms per call)
        assert avg_ms < 10, f"PII masking is too slow: {avg_ms:.2f}ms per call"

    def test_preserves_non_pii_content(self):
        """Should preserve non-PII content exactly"""
        pii_masker = PIIMasker()

        content = "안녕하세요. 제 주민번호는 123456-1234567입니다. 감사합니다."
        masked_content, has_pii, pii_details = pii_masker.detect_and_mask(content)

        assert has_pii
        assert "안녕하세요" in masked_content
        assert "감사합니다" in masked_content
        assert "123456-*******" in masked_content

    def test_overall_100_percent_detection(self):
        """Overall test: Should achieve 100% detection across all PII types"""
        pii_masker = PIIMasker()

        all_test_cases = KOREAN_ID_CASES + PHONE_NUMBER_CASES + EMAIL_CASES

        total_detected = 0
        total_cases = len(all_test_cases)

        for content, should_detect, _ in all_test_cases:
            masked_content, has_pii, pii_details = pii_masker.detect_and_mask(content)

            if has_pii:
                total_detected += 1
            else:
                print(f"MISSED: {content}")

        overall_detection_rate = (total_detected / total_cases) * 100
        print(f"\nOverall PII Detection Rate: {overall_detection_rate:.1f}% ({total_detected}/{total_cases})")

        # MUST achieve 100% detection per SC-015
        assert overall_detection_rate == 100.0, \
               f"Overall PII detection rate {overall_detection_rate:.1f}% is below required 100%"
