"""Authentication service"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    generate_session_token,
    get_session_expiry,
    hash_password,
    verify_password,
)
from app.models.session import Session
from app.models.user import User

# FR-031: Account lockout constants
MAX_FAILED_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 30


class AuthService:
    """Service for authentication operations"""

    @staticmethod
    async def authenticate_user(
        db: AsyncSession, username: str, password: str
    ) -> Optional[User]:
        """
        Authenticate user with username and password.

        FR-031: Implements account lockout after 5 failed attempts (30 minute lockout).

        Args:
            db: Database session
            username: Username
            password: Plain text password

        Returns:
            User if authentication successful, None otherwise
        """
        # Get user by username
        result = await db.execute(select(User).where(User.username == username))
        user = result.scalar_one_or_none()

        if not user:
            return None

        # FR-031: Check if account is locked
        now = datetime.now(timezone.utc)
        if user.is_locked:
            # Check if lockout has expired
            if user.locked_until and user.locked_until <= now:
                # Auto-unlock account
                user.is_locked = False
                user.locked_until = None
                user.failed_login_attempts = 0
                await db.commit()
            else:
                # Account still locked
                return None

        # Check if account is inactive
        if not user.is_active:
            return None

        # Verify password
        if not verify_password(password, user.password_hash):
            # FR-031: Increment failed login attempts
            user.failed_login_attempts += 1

            # Lock account if max attempts reached
            if user.failed_login_attempts >= MAX_FAILED_LOGIN_ATTEMPTS:
                user.is_locked = True
                user.locked_until = now + timedelta(minutes=LOCKOUT_DURATION_MINUTES)

            await db.commit()
            return None

        # Successful login - reset failed attempts
        user.failed_login_attempts = 0
        user.last_login_at = now
        await db.commit()

        return user

    @staticmethod
    async def create_session(db: AsyncSession, user_id: UUID) -> Session:
        """
        Create a new session for user.

        Per FR-030 and Clarification 2025-10-28:
        - Maximum MAX_CONCURRENT_SESSIONS (default 3) concurrent sessions per user (T316)
        - If limit exceeded, automatically terminate oldest session by last_activity
        - Terminated session will receive 401 on next request with message

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Created session
        """
        from sqlalchemy import desc, func
        from app.core.config import settings

        # Count active sessions for this user
        session_count_result = await db.execute(
            select(func.count(Session.id)).where(Session.user_id == user_id)
        )
        session_count = session_count_result.scalar() or 0

        # If user has MAX_CONCURRENT_SESSIONS+, delete oldest by last_activity (T316)
        if session_count >= settings.MAX_CONCURRENT_SESSIONS:
            # Get oldest session
            oldest_session_result = await db.execute(
                select(Session)
                .where(Session.user_id == user_id)
                .order_by(Session.last_activity.asc())
                .limit(1)
            )
            oldest_session = oldest_session_result.scalar_one_or_none()

            if oldest_session:
                await db.delete(oldest_session)
                await db.flush()  # Ensure deletion completes before creating new session
                # Note: The frontend will detect 401 on next API request from that session
                # and display "다른 위치에서 로그인하여 종료되었습니다."

        session_token = generate_session_token()
        expires_at = get_session_expiry()
        now = datetime.now(timezone.utc)

        session = Session(
            user_id=user_id,
            session_token=session_token,
            expires_at=expires_at,
            last_activity=now
        )

        db.add(session)
        await db.commit()
        await db.refresh(session)

        return session

    @staticmethod
    async def get_session_by_token(
        db: AsyncSession, session_token: str
    ) -> Optional[Session]:
        """
        Get session by token.

        Updates last_activity on every request (for session limit enforcement).

        Args:
            db: Database session
            session_token: Session token

        Returns:
            Session if found and not expired, None otherwise
        """
        result = await db.execute(
            select(Session).where(Session.session_token == session_token)
        )
        session = result.scalar_one_or_none()

        if not session:
            return None

        # Check if session expired
        now = datetime.now(timezone.utc)
        if session.expires_at < now:
            await db.delete(session)
            await db.commit()
            return None

        # Update session expiry (refresh session on each request - 30 minute sliding window)
        # Also update last_activity for session limit enforcement (Clarification 2025-10-28)
        session.expires_at = get_session_expiry()
        session.last_activity = now
        await db.commit()

        return session

    @staticmethod
    async def update_last_login(db: AsyncSession, user_id: UUID) -> None:
        """
        Update user's last login time.

        Args:
            db: Database session
            user_id: User ID
        """
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if user:
            user.last_login_at = datetime.now(timezone.utc)
            await db.commit()

    @staticmethod
    async def delete_session(db: AsyncSession, session_token: str) -> bool:
        """
        Delete session (logout).

        Args:
            db: Database session
            session_token: Session token

        Returns:
            True if session deleted, False if not found
        """
        result = await db.execute(
            select(Session).where(Session.session_token == session_token)
        )
        session = result.scalar_one_or_none()

        if session:
            await db.delete(session)
            await db.commit()
            return True

        return False

    @staticmethod
    async def get_user_by_id(db: AsyncSession, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            User if found, None otherwise
        """
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def cleanup_expired_sessions(db: AsyncSession) -> int:
        """
        Delete all expired sessions (background cleanup task).

        Args:
            db: Database session

        Returns:
            Number of sessions deleted
        """
        from sqlalchemy import delete

        now = datetime.now(timezone.utc)

        # Delete expired sessions
        stmt = delete(Session).where(Session.expires_at < now)
        result = await db.execute(stmt)
        await db.commit()

        return result.rowcount

    @staticmethod
    async def unlock_account(db: AsyncSession, user_id: UUID) -> Optional[User]:
        """
        Manually unlock a user account (FR-031).

        Administrators can unlock accounts before the 30-minute lockout expires.

        Args:
            db: Database session
            user_id: User ID to unlock

        Returns:
            User if found and unlocked, None otherwise
        """
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

        if not user:
            return None

        # Unlock account and reset failed attempts
        user.is_locked = False
        user.locked_until = None
        user.failed_login_attempts = 0
        await db.commit()
        await db.refresh(user)

        return user


# Singleton instance
auth_service = AuthService()
