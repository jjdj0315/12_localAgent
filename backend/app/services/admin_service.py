"""
Admin service for user management and system monitoring.
"""

import secrets
import string
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.message import Message
from app.models.conversation import Conversation
from app.models.document import Document


def get_current_utc():
    """Get current UTC time with timezone"""
    return datetime.now(timezone.utc)


class AdminService:
    """Service for admin operations"""

    @staticmethod
    def generate_password(length: int = 12) -> str:
        """
        Generate a secure random password.

        Args:
            length: Password length (default 12)

        Returns:
            Random password string
        """
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        password = ''.join(secrets.choice(alphabet) for _ in range(length))
        return password

    @staticmethod
    async def list_users(
        db: AsyncSession,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[User], int]:
        """
        List all users with pagination.

        Args:
            db: Database session
            page: Page number (1-indexed)
            page_size: Items per page

        Returns:
            Tuple of (users list, total count)
        """
        # Get total count
        count_query = select(func.count()).select_from(User)
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Get paginated users
        offset = (page - 1) * page_size
        query = (
            select(User)
            .order_by(User.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        result = await db.execute(query)
        users = result.scalars().all()

        return list(users), total

    @staticmethod
    async def create_user(
        db: AsyncSession,
        username: str,
        password: str,
        is_admin: bool = False,
    ) -> User:
        """
        Create a new user account.

        Args:
            db: Database session
            username: Username
            password: Initial password
            is_admin: Admin privileges

        Returns:
            Created user
        """
        from app.services.auth_service import auth_service

        # Check if username already exists
        existing_query = select(User).where(User.username == username)
        existing_result = await db.execute(existing_query)
        existing_user = existing_result.scalar_one_or_none()

        if existing_user:
            raise ValueError(f"Username '{username}' already exists")

        # Hash password
        password_hash = auth_service.hash_password(password)

        # Create user
        new_user = User(
            username=username,
            password_hash=password_hash,
            is_admin=is_admin,
            created_at=get_current_utc(),
        )

        db.add(new_user)
        await db.commit()
        await db.refresh(new_user)

        return new_user

    @staticmethod
    async def delete_user(
        db: AsyncSession,
        user_id: UUID,
    ) -> bool:
        """
        Delete a user and all associated data.

        Args:
            db: Database session
            user_id: User ID to delete

        Returns:
            True if deleted, False if not found
        """
        # Get user
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return False

        # Delete user (cascade will delete conversations, messages, documents, sessions)
        await db.delete(user)
        await db.commit()

        return True

    @staticmethod
    async def reset_password(
        db: AsyncSession,
        user_id: UUID,
    ) -> Tuple[Optional[User], str]:
        """
        Reset user password and generate temporary password.

        Args:
            db: Database session
            user_id: User ID

        Returns:
            Tuple of (User, temporary_password) or (None, "") if not found
        """
        from app.services.auth_service import auth_service

        # Get user
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return None, ""

        # Generate temporary password
        temp_password = AdminService.generate_password(12)
        password_hash = auth_service.hash_password(temp_password)

        # Update user password
        user.password_hash = password_hash
        await db.commit()
        await db.refresh(user)

        return user, temp_password

    @staticmethod
    async def get_usage_stats(
        db: AsyncSession,
    ) -> dict:
        """
        Get usage statistics.

        Args:
            db: Database session

        Returns:
            Dictionary with usage statistics
        """
        now = get_current_utc()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)
        month_start = today_start - timedelta(days=30)

        # Active users (users who created messages)
        async def count_active_users(since: datetime) -> int:
            query = (
                select(func.count(func.distinct(Message.user_id)))
                .where(Message.created_at >= since)
            )
            result = await db.execute(query)
            return result.scalar() or 0

        active_users_today = await count_active_users(today_start)
        active_users_week = await count_active_users(week_start)
        active_users_month = await count_active_users(month_start)

        # Total queries (total messages with role='user')
        async def count_queries(since: datetime) -> int:
            query = (
                select(func.count(Message.id))
                .where(
                    and_(
                        Message.created_at >= since,
                        Message.role == 'user'
                    )
                )
            )
            result = await db.execute(query)
            return result.scalar() or 0

        total_queries_today = await count_queries(today_start)
        total_queries_week = await count_queries(week_start)
        total_queries_month = await count_queries(month_start)

        # Average response time (placeholder - requires processing_time_ms field)
        # For now, return 0 as we haven't implemented response time tracking yet
        avg_response_time_today = 0.0
        avg_response_time_week = 0.0
        avg_response_time_month = 0.0

        return {
            "active_users_today": active_users_today,
            "active_users_week": active_users_week,
            "active_users_month": active_users_month,
            "total_queries_today": total_queries_today,
            "total_queries_week": total_queries_week,
            "total_queries_month": total_queries_month,
            "avg_response_time_today": avg_response_time_today,
            "avg_response_time_week": avg_response_time_week,
            "avg_response_time_month": avg_response_time_month,
        }


admin_service = AdminService()
