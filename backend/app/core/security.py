"""Security utilities for password hashing and verification"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

import bcrypt


class SecurityUtil:
    """Security utility class for password hashing and session management"""

    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.

        Args:
            password: Plain text password

        Returns:
            Hashed password string
        """
        rounds = int(os.getenv("BCRYPT_ROUNDS", "12"))
        salt = bcrypt.gensalt(rounds=rounds)
        hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
        return hashed.decode("utf-8")

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.

        Args:
            plain_password: Plain text password to verify
            hashed_password: Hashed password to compare against

        Returns:
            True if password matches, False otherwise
        """
        return bcrypt.checkpw(
            plain_password.encode("utf-8"), hashed_password.encode("utf-8")
        )

    @staticmethod
    def generate_session_token() -> str:
        """
        Generate a cryptographically secure random session token.

        Returns:
            64-character hex string
        """
        return secrets.token_hex(32)  # 32 bytes = 64 hex characters

    @staticmethod
    def generate_temp_password(length: int = 12) -> str:
        """
        Generate a temporary password for new users.

        Args:
            length: Password length (default 12)

        Returns:
            Random password string
        """
        # Use URL-safe characters for easier distribution
        return secrets.token_urlsafe(length)[:length]

    @staticmethod
    def get_session_expiry(timeout_minutes: Optional[int] = None) -> datetime:
        """
        Calculate session expiry datetime.

        Args:
            timeout_minutes: Timeout in minutes (default from env or 30)

        Returns:
            Datetime when session expires
        """
        if timeout_minutes is None:
            timeout_minutes = int(os.getenv("SESSION_TIMEOUT_MINUTES", "30"))
        return datetime.utcnow() + timedelta(minutes=timeout_minutes)


# Convenience functions
hash_password = SecurityUtil.hash_password
verify_password = SecurityUtil.verify_password
generate_session_token = SecurityUtil.generate_session_token
generate_temp_password = SecurityUtil.generate_temp_password
get_session_expiry = SecurityUtil.get_session_expiry
