"""
PII Detection and Masking

Detects and masks personally identifiable information (PII) in Korean text.
Covers: 주민등록번호, phone numbers, email addresses.
"""

import re
from typing import Tuple, List, Dict


class PIIMasker:
    """
    PII Detection and Masking Service

    Detects and masks sensitive personal information while preserving
    message readability.

    Supported PII types:
    - 주민등록번호 (Korean ID number): 123456-1234567 → 123456-*******
    - Phone: 010-1234-5678 → 010-****-****
    - Email: user@domain.com → u***@domain.com
    """

    # Regex patterns for PII detection
    PATTERNS = {
        "korean_id": {
            "pattern": r'\b\d{6}[-\s]?\d{7}\b',
            "description": "주민등록번호",
            "replacement_fn": lambda m: PIIMasker._mask_korean_id(m.group(0))
        },
        "phone": {
            "pattern": r'\b0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}\b',
            "description": "전화번호",
            "replacement_fn": lambda m: PIIMasker._mask_phone(m.group(0))
        },
        "email": {
            "pattern": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            "description": "이메일",
            "replacement_fn": lambda m: PIIMasker._mask_email(m.group(0))
        }
    }

    @staticmethod
    def _mask_korean_id(id_number: str) -> str:
        """
        Mask Korean ID number: 123456-1234567 → 123456-*******

        Args:
            id_number: Korean ID number (with or without dash)

        Returns:
            Masked ID number
        """
        # Remove spaces and normalize dash
        normalized = id_number.replace(' ', '')

        if '-' in normalized:
            parts = normalized.split('-')
            if len(parts) == 2 and len(parts[0]) == 6:
                return f"{parts[0]}-*******"

        # No dash format: 1234567890123 → 123456-*******
        if len(normalized) == 13:
            return f"{normalized[:6]}-*******"

        # Fallback: mask all but first 6 digits
        return normalized[:6] + "*" * max(0, len(normalized) - 6)

    @staticmethod
    def _mask_phone(phone: str) -> str:
        """
        Mask phone number: 010-1234-5678 → 010-****-****

        Args:
            phone: Phone number (various formats)

        Returns:
            Masked phone number
        """
        # Remove all spaces and dashes
        digits = re.sub(r'[-\s]', '', phone)

        # Korean mobile: 010-xxxx-xxxx
        if digits.startswith('010') and len(digits) == 11:
            return '010-****-****'

        # Korean landline: 02-xxx-xxxx or 031-xxx-xxxx
        if digits.startswith('02') and len(digits) >= 9:
            return '02-***-****'
        if len(digits) >= 10:
            return f"{digits[:3]}-***-****"

        # Fallback: mask middle and end
        if len(digits) > 4:
            return digits[:3] + '*' * (len(digits) - 3)

        return '***-****-****'

    @staticmethod
    def _mask_email(email: str) -> str:
        """
        Mask email: user@domain.com → u***@domain.com

        Args:
            email: Email address

        Returns:
            Masked email
        """
        try:
            username, domain = email.split('@')

            # Mask username (keep first char)
            if len(username) > 1:
                masked_username = username[0] + '*' * (len(username) - 1)
            else:
                masked_username = '*'

            return f"{masked_username}@{domain}"

        except ValueError:
            # Invalid email format, return as-is
            return email

    def detect_and_mask(self, content: str) -> Tuple[str, bool, List[Dict]]:
        """
        Detect and mask all PII in content.

        Args:
            content: Text content to process

        Returns:
            Tuple of (masked_content, has_pii, detected_pii_list)
            - masked_content: Content with PII replaced by masked versions
            - has_pii: True if any PII was detected
            - detected_pii_list: List of {type, description, count}
        """
        if not content or not content.strip():
            return content, False, []

        masked_content = content
        detected_pii = {}

        # Apply each PII pattern
        for pii_type, config in self.PATTERNS.items():
            pattern = config["pattern"]
            description = config["description"]
            replacement_fn = config["replacement_fn"]

            # Find all matches
            matches = re.findall(pattern, masked_content)

            if matches:
                # Track detection
                detected_pii[pii_type] = {
                    "type": pii_type,
                    "description": description,
                    "count": len(matches)
                }

                # Replace all occurrences
                masked_content = re.sub(pattern, replacement_fn, masked_content)

        has_pii = len(detected_pii) > 0
        detected_pii_list = list(detected_pii.values())

        return masked_content, has_pii, detected_pii_list

    def check_only(self, content: str) -> Tuple[bool, List[Dict]]:
        """
        Check if content contains PII without masking.

        Args:
            content: Text content to check

        Returns:
            Tuple of (has_pii, detected_pii_list)
        """
        _, has_pii, detected_list = self.detect_and_mask(content)
        return has_pii, detected_list
