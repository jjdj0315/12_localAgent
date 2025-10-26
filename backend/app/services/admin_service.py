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
from app.core.security import hash_password, generate_temp_password


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
        # Check if username already exists
        existing_query = select(User).where(User.username == username)
        existing_result = await db.execute(existing_query)
        existing_user = existing_result.scalar_one_or_none()

        if existing_user:
            raise ValueError(f"Username '{username}' already exists")

        # Hash password
        password_hash = hash_password(password)

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
        # Get user
        query = select(User).where(User.id == user_id)
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            return None, ""

        # Generate temporary password
        temp_password = AdminService.generate_password(12)
        password_hash = hash_password(temp_password)

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

        # Average response time from processing_time_ms field
        async def calc_avg_response_time(since: datetime) -> float:
            query = (
                select(func.avg(Message.processing_time_ms))
                .where(
                    and_(
                        Message.created_at >= since,
                        Message.role == 'assistant',
                        Message.processing_time_ms.isnot(None)
                    )
                )
            )
            result = await db.execute(query)
            avg_ms = result.scalar()
            return float(avg_ms) if avg_ms else 0.0

        avg_response_time_today = await calc_avg_response_time(today_start)
        avg_response_time_week = await calc_avg_response_time(week_start)
        avg_response_time_month = await calc_avg_response_time(month_start)

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


    @staticmethod
    async def get_system_health() -> dict:
        """
        Get system health metrics.

        Returns:
            Dictionary with system health information
        """
        import psutil
        import time
        import subprocess

        # Server uptime (using psutil boot time)
        boot_time = psutil.boot_time()
        uptime_seconds = int(time.time() - boot_time)

        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory usage
        memory = psutil.virtual_memory()
        memory_percent = memory.percent

        # Disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent
        available_gb = disk.free / (1024 ** 3)
        total_gb = disk.total / (1024 ** 3)

        # LLM service status (placeholder - check if vLLM is accessible)
        llm_status = "healthy"  # TODO: Implement actual health check

        # Database status
        db_status = "healthy"  # Connection is alive if we got here

        # GPU metrics (try nvidia-smi)
        gpu_usage = None
        gpu_memory = None
        try:
            result = subprocess.run(
                ['nvidia-smi', '--query-gpu=utilization.gpu,utilization.memory', '--format=csv,noheader,nounits'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                values = result.stdout.strip().split(',')
                if len(values) >= 2:
                    gpu_usage = float(values[0].strip())
                    gpu_memory = float(values[1].strip())
        except Exception:
            pass  # GPU metrics not available

        return {
            "server_uptime_seconds": uptime_seconds,
            "cpu_usage_percent": cpu_percent,
            "memory_usage_percent": memory_percent,
            "disk_usage_percent": disk_percent,
            "available_storage_gb": available_gb,
            "total_storage_gb": total_gb,
            "llm_service_status": llm_status,
            "database_status": db_status,
            "gpu_usage_percent": gpu_usage,
            "gpu_memory_usage_percent": gpu_memory,
        }

    @staticmethod
    async def get_storage_stats(db: AsyncSession) -> dict:
        """
        Get storage usage statistics.

        Args:
            db: Database session

        Returns:
            Dictionary with storage statistics
        """
        import psutil
        from sqlalchemy import and_

        # Get total disk usage
        disk = psutil.disk_usage('/')
        total_storage = disk.total
        used_storage = disk.used
        available_storage = disk.free
        usage_percent = disk.percent

        # Calculate per-user storage
        user_storage = []

        # Get all users
        users_query = select(User)
        users_result = await db.execute(users_query)
        users = users_result.scalars().all()

        for user in users:
            # Count documents
            doc_count_query = select(func.count()).where(Document.user_id == user.id)
            doc_count_result = await db.execute(doc_count_query)
            doc_count = doc_count_result.scalar() or 0

            # Sum file sizes
            size_query = select(func.sum(Document.file_size)).where(Document.user_id == user.id)
            size_result = await db.execute(size_query)
            total_size = size_result.scalar() or 0

            # Count conversations
            conv_count_query = select(func.count()).where(Conversation.user_id == user.id)
            conv_count_result = await db.execute(conv_count_query)
            conv_count = conv_count_result.scalar() or 0

            user_storage.append({
                "user_id": user.id,
                "username": user.username,
                "total_storage_bytes": total_size,
                "document_count": doc_count,
                "conversation_count": conv_count,
            })

        return {
            "total_storage_used_bytes": used_storage,
            "total_storage_available_bytes": available_storage,
            "usage_percent": usage_percent,
            "user_storage": user_storage,
            "warning_threshold_exceeded": usage_percent > 80,
            "critical_threshold_exceeded": usage_percent > 95,
        }


admin_service = AdminService()
