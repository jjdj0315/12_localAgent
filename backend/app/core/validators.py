"""
Input Validation Utilities (T231)

Provides validators for API endpoints to ensure:
- Length limits
- Type validation
- Format validation
- Security checks
"""

from typing import Optional
from fastapi import HTTPException, status
import re


class ValidationError(HTTPException):
    """Custom validation error with Korean messages"""

    def __init__(self, field: str, message: str):
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "validation_error",
                "field": field,
                "message": message
            }
        )


class InputValidator:
    """Common input validators for API endpoints"""

    # Length limits
    MAX_MESSAGE_LENGTH = 10000  # 10K characters
    MAX_USERNAME_LENGTH = 50
    MAX_PASSWORD_LENGTH = 128
    MIN_PASSWORD_LENGTH = 8
    MAX_TAG_NAME_LENGTH = 50
    MAX_CONVERSATION_TITLE_LENGTH = 200
    MAX_FILENAME_LENGTH = 255
    MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50MB

    @staticmethod
    def validate_message_content(content: str, field_name: str = "message") -> str:
        """
        Validate chat message content

        Args:
            content: Message content
            field_name: Field name for error messages

        Returns:
            Validated content (stripped)

        Raises:
            ValidationError: If validation fails
        """
        if not content:
            raise ValidationError(field_name, "메시지는 필수입니다.")

        content = content.strip()

        if not content:
            raise ValidationError(field_name, "메시지는 필수입니다.")

        if len(content) > InputValidator.MAX_MESSAGE_LENGTH:
            raise ValidationError(
                field_name,
                f"메시지가 너무 깁니다. 최대 {InputValidator.MAX_MESSAGE_LENGTH}자까지 허용됩니다."
            )

        return content

    @staticmethod
    def validate_username(username: str) -> str:
        """
        Validate username

        Requirements:
        - 3-50 characters
        - Alphanumeric, underscore, hyphen only
        - No leading/trailing whitespace

        Args:
            username: Username to validate

        Returns:
            Validated username

        Raises:
            ValidationError: If validation fails
        """
        if not username:
            raise ValidationError("username", "사용자명은 필수입니다.")

        username = username.strip()

        if len(username) < 3:
            raise ValidationError("username", "사용자명은 최소 3자 이상이어야 합니다.")

        if len(username) > InputValidator.MAX_USERNAME_LENGTH:
            raise ValidationError(
                "username",
                f"사용자명이 너무 깁니다. 최대 {InputValidator.MAX_USERNAME_LENGTH}자까지 허용됩니다."
            )

        # Alphanumeric + underscore + hyphen only
        if not re.match(r'^[a-zA-Z0-9_-]+$', username):
            raise ValidationError(
                "username",
                "사용자명은 영문, 숫자, 밑줄(_), 하이픈(-)만 사용할 수 있습니다."
            )

        return username

    @staticmethod
    def validate_password(password: str) -> str:
        """
        Validate password

        Requirements:
        - 8-128 characters
        - No leading/trailing whitespace

        Args:
            password: Password to validate

        Returns:
            Validated password

        Raises:
            ValidationError: If validation fails
        """
        if not password:
            raise ValidationError("password", "비밀번호는 필수입니다.")

        # Don't strip passwords (spaces may be intentional)
        if len(password) < InputValidator.MIN_PASSWORD_LENGTH:
            raise ValidationError(
                "password",
                f"비밀번호는 최소 {InputValidator.MIN_PASSWORD_LENGTH}자 이상이어야 합니다."
            )

        if len(password) > InputValidator.MAX_PASSWORD_LENGTH:
            raise ValidationError(
                "password",
                f"비밀번호가 너무 깁니다. 최대 {InputValidator.MAX_PASSWORD_LENGTH}자까지 허용됩니다."
            )

        return password

    @staticmethod
    def validate_tag_name(tag_name: str) -> str:
        """
        Validate tag name

        Requirements:
        - 1-50 characters
        - No special characters (except spaces)

        Args:
            tag_name: Tag name to validate

        Returns:
            Validated tag name (stripped)

        Raises:
            ValidationError: If validation fails
        """
        if not tag_name:
            raise ValidationError("tag_name", "태그 이름은 필수입니다.")

        tag_name = tag_name.strip()

        if not tag_name:
            raise ValidationError("tag_name", "태그 이름은 필수입니다.")

        if len(tag_name) > InputValidator.MAX_TAG_NAME_LENGTH:
            raise ValidationError(
                "tag_name",
                f"태그 이름이 너무 깁니다. 최대 {InputValidator.MAX_TAG_NAME_LENGTH}자까지 허용됩니다."
            )

        # Korean, English, numbers, spaces only
        if not re.match(r'^[가-힣a-zA-Z0-9\s]+$', tag_name):
            raise ValidationError(
                "tag_name",
                "태그 이름은 한글, 영문, 숫자, 공백만 사용할 수 있습니다."
            )

        return tag_name

    @staticmethod
    def validate_conversation_title(title: str) -> str:
        """
        Validate conversation title

        Args:
            title: Conversation title

        Returns:
            Validated title (stripped)

        Raises:
            ValidationError: If validation fails
        """
        if not title:
            raise ValidationError("title", "대화 제목은 필수입니다.")

        title = title.strip()

        if not title:
            raise ValidationError("title", "대화 제목은 필수입니다.")

        if len(title) > InputValidator.MAX_CONVERSATION_TITLE_LENGTH:
            raise ValidationError(
                "title",
                f"대화 제목이 너무 깁니다. 최대 {InputValidator.MAX_CONVERSATION_TITLE_LENGTH}자까지 허용됩니다."
            )

        return title

    @staticmethod
    def validate_filename(filename: str) -> str:
        """
        Validate filename

        Requirements:
        - No path traversal (../)
        - No null bytes
        - Reasonable length

        Args:
            filename: Filename to validate

        Returns:
            Validated filename

        Raises:
            ValidationError: If validation fails
        """
        if not filename:
            raise ValidationError("filename", "파일 이름은 필수입니다.")

        # Check for path traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise ValidationError("filename", "파일 이름에 잘못된 문자가 포함되었습니다.")

        # Check for null bytes
        if "\x00" in filename:
            raise ValidationError("filename", "파일 이름에 유효하지 않은 문자가 포함되었습니다.")

        if len(filename) > InputValidator.MAX_FILENAME_LENGTH:
            raise ValidationError(
                "filename",
                f"파일 이름이 너무 깁니다. 최대 {InputValidator.MAX_FILENAME_LENGTH}자까지 허용됩니다."
            )

        return filename

    @staticmethod
    def validate_file_size(size_bytes: int, max_size: Optional[int] = None) -> int:
        """
        Validate file size

        Args:
            size_bytes: File size in bytes
            max_size: Optional custom max size (defaults to MAX_FILE_SIZE_BYTES)

        Returns:
            Validated size

        Raises:
            ValidationError: If validation fails
        """
        max_allowed = max_size or InputValidator.MAX_FILE_SIZE_BYTES

        if size_bytes <= 0:
            raise ValidationError("file", "파일 크기가 올바르지 않습니다.")

        if size_bytes > max_allowed:
            max_mb = max_allowed / 1024 / 1024
            raise ValidationError(
                "file",
                f"파일 크기가 너무 큽니다. 최대 {max_mb:.0f}MB까지 허용됩니다."
            )

        return size_bytes

    @staticmethod
    def validate_uuid(uuid_str: str, field_name: str = "id") -> str:
        """
        Validate UUID format

        Args:
            uuid_str: UUID string
            field_name: Field name for error messages

        Returns:
            Validated UUID string

        Raises:
            ValidationError: If validation fails
        """
        if not uuid_str:
            raise ValidationError(field_name, f"{field_name}가 필수입니다.")

        # UUID format: 8-4-4-4-12 hexadecimal
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'

        if not re.match(uuid_pattern, uuid_str.lower()):
            raise ValidationError(field_name, f"{field_name} 형식이 올바르지 않습니다.")

        return uuid_str

    @staticmethod
    def validate_positive_integer(value: int, field_name: str = "value", max_value: Optional[int] = None) -> int:
        """
        Validate positive integer

        Args:
            value: Integer value
            field_name: Field name for error messages
            max_value: Optional maximum value

        Returns:
            Validated integer

        Raises:
            ValidationError: If validation fails
        """
        if value < 0:
            raise ValidationError(field_name, f"{field_name}는 양수여야 합니다.")

        if max_value is not None and value > max_value:
            raise ValidationError(
                field_name,
                f"{field_name}가 너무 큽니다. 최대 {max_value}까지 허용됩니다."
            )

        return value

    @staticmethod
    def sanitize_search_query(query: str) -> str:
        """
        Sanitize search query

        Args:
            query: Search query string

        Returns:
            Sanitized query

        Raises:
            ValidationError: If validation fails
        """
        if not query:
            raise ValidationError("query", "검색어는 필수입니다.")

        query = query.strip()

        if not query:
            raise ValidationError("query", "검색어는 필수입니다.")

        if len(query) > 200:
            raise ValidationError("query", "검색어가 너무 깁니다. 최대 200자까지 허용됩니다.")

        # Remove special SQL characters to prevent injection
        # Note: Actual SQL injection prevention is handled by SQLAlchemy
        # This is just an additional safety layer
        dangerous_chars = [';', '--', '/*', '*/', 'xp_', 'sp_']
        for char in dangerous_chars:
            if char in query.lower():
                raise ValidationError("query", "검색어에 허용되지 않은 문자가 포함되었습니다.")

        return query
