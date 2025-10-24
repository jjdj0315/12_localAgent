"""Authentication service"""

from datetime import datetime, timezone
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


class AuthService:
    """Service for authentication operations"""

    @staticmethod
    async def authenticate_user(
        db: AsyncSession, username: str, password: str
    ) -> Optional[User]:
        """
        Authenticate user with username and password.

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

        # Verify password
        if not verify_password(password, user.password_hash):
            return None

        return user

    @staticmethod
    async def create_session(db: AsyncSession, user_id: UUID) -> Session:
        """
        Create a new session for user.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Created session
        """
        session_token = generate_session_token()
        expires_at = get_session_expiry()

        session = Session(
            user_id=user_id, session_token=session_token, expires_at=expires_at
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
        session.expires_at = get_session_expiry()
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


# Singleton instance
auth_service = AuthService()
