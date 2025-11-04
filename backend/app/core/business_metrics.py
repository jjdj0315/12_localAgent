"""Business metrics collection

Updates Prometheus metrics by querying the database.
This module provides functions to refresh business metrics from actual database state.
"""

from datetime import datetime, timedelta
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.metrics import (
    active_users_current,
    conversations_total,
    messages_total,
)
from app.models.session import Session as UserSession
from app.models.conversation import Conversation
from app.models.message import Message


async def update_active_users_metric(db: AsyncSession):
    """
    Update active users metric by counting valid sessions.

    A session is active if it was created within the last 30 minutes
    and hasn't been explicitly invalidated.
    """
    try:
        # Calculate cutoff time (30 minutes ago)
        cutoff_time = datetime.utcnow() - timedelta(minutes=30)

        # Count active sessions
        query = select(func.count(func.distinct(UserSession.user_id))).where(
            UserSession.created_at >= cutoff_time
        )
        result = await db.execute(query)
        active_count = result.scalar() or 0

        # Update metric
        active_users_current.set(active_count)

    except Exception as e:
        print(f"[Metrics] Error updating active users metric: {e}")


async def update_conversations_metric(db: AsyncSession):
    """
    Update total conversations metric.
    """
    try:
        query = select(func.count()).select_from(Conversation)
        result = await db.execute(query)
        total = result.scalar() or 0

        conversations_total.set(total)

    except Exception as e:
        print(f"[Metrics] Error updating conversations metric: {e}")


async def update_messages_metric(db: AsyncSession):
    """
    Update total messages metric.
    """
    try:
        query = select(func.count()).select_from(Message)
        result = await db.execute(query)
        total = result.scalar() or 0

        messages_total.set(total)

    except Exception as e:
        print(f"[Metrics] Error updating messages metric: {e}")


async def update_all_business_metrics():
    """
    Update all business metrics by querying the database.

    This function should be called periodically (e.g., every 5 minutes)
    to keep business metrics in sync with actual database state.
    """
    async with AsyncSessionLocal() as db:
        try:
            await update_active_users_metric(db)
            await update_conversations_metric(db)
            await update_messages_metric(db)

        except Exception as e:
            print(f"[Metrics] Error updating business metrics: {e}")
        finally:
            await db.close()
