"""Conversation service for managing conversations and messages"""

from datetime import datetime, timezone
from typing import List, Optional, Tuple
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.models.message import Message


def get_current_utc():
    """Get current UTC time with timezone"""
    return datetime.now(timezone.utc)


class ConversationService:
    """Service for conversation operations"""

    @staticmethod
    async def list_conversations(
        db: AsyncSession,
        user_id: UUID,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        tag: Optional[str] = None,
    ) -> Tuple[List[Conversation], int]:
        """
        List user's conversations with pagination and filtering.

        Args:
            db: Database session
            user_id: User ID
            page: Page number (1-indexed)
            page_size: Items per page
            search: Search keyword for title and tags
            tag: Filter by specific tag

        Returns:
            Tuple of (conversations list, total count)
        """
        # Base query
        query = select(Conversation).where(Conversation.user_id == user_id)

        # Apply search filter
        if search:
            search_pattern = f"%{search}%"
            # Use cast to text to search within JSONB array
            from sqlalchemy import cast, Text
            query = query.where(
                or_(
                    Conversation.title.ilike(search_pattern),
                    cast(Conversation.tags, Text).ilike(search_pattern),
                )
            )

        # Apply tag filter
        if tag:
            query = query.where(Conversation.tags.op("?")(tag))  # JSONB contains key

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        offset = (page - 1) * page_size
        query = (
            query.order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(page_size)
        )

        # Execute query
        result = await db.execute(query)
        conversations = result.scalars().all()

        return list(conversations), total

    @staticmethod
    async def get_conversation(
        db: AsyncSession, conversation_id: UUID, user_id: UUID
    ) -> Optional[Conversation]:
        """
        Get conversation by ID with all messages.

        Args:
            db: Database session
            conversation_id: Conversation ID
            user_id: User ID (for authorization)

        Returns:
            Conversation with messages or None
        """
        query = (
            select(Conversation)
            .where(
                and_(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id,
                )
            )
            .options(
                selectinload(Conversation.messages)
            )
        )

        result = await db.execute(query)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_conversation(
        db: AsyncSession,
        user_id: UUID,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Conversation:
        """
        Create a new conversation.

        Args:
            db: Database session
            user_id: User ID
            title: Conversation title
            tags: Conversation tags

        Returns:
            Created conversation
        """
        conversation = Conversation(
            user_id=user_id,
            title=title or "New Conversation",
            tags=tags or [],
        )

        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)

        return conversation

    @staticmethod
    async def update_conversation(
        db: AsyncSession,
        conversation_id: UUID,
        user_id: UUID,
        title: Optional[str] = None,
        tags: Optional[List[str]] = None,
    ) -> Optional[Conversation]:
        """
        Update conversation metadata.

        Args:
            db: Database session
            conversation_id: Conversation ID
            user_id: User ID (for authorization)
            title: New title
            tags: New tags

        Returns:
            Updated conversation or None if not found
        """
        query = select(Conversation).where(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )

        result = await db.execute(query)
        conversation = result.scalar_one_or_none()

        if not conversation:
            return None

        # Update fields
        if title is not None:
            conversation.title = title
        if tags is not None:
            conversation.tags = tags

        conversation.updated_at = get_current_utc()

        await db.commit()
        await db.refresh(conversation)

        return conversation

    @staticmethod
    async def delete_conversation(
        db: AsyncSession, conversation_id: UUID, user_id: UUID
    ) -> bool:
        """
        Delete conversation and all its messages.

        Args:
            db: Database session
            conversation_id: Conversation ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted, False if not found
        """
        query = select(Conversation).where(
            and_(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )

        result = await db.execute(query)
        conversation = result.scalar_one_or_none()

        if not conversation:
            return False

        await db.delete(conversation)
        await db.commit()

        return True

    @staticmethod
    async def auto_generate_title(
        db: AsyncSession, conversation_id: UUID, first_message: str
    ) -> str:
        """
        Auto-generate conversation title from first user message.

        Args:
            db: Database session
            conversation_id: Conversation ID
            first_message: First user message content

        Returns:
            Generated title
        """
        # Simple title generation: take first 50 chars
        title = first_message[:50].strip()
        if len(first_message) > 50:
            title += "..."

        # Update conversation title
        query = select(Conversation).where(Conversation.id == conversation_id)
        result = await db.execute(query)
        conversation = result.scalar_one_or_none()

        if conversation and conversation.title == "New Conversation":
            conversation.title = title
            conversation.updated_at = get_current_utc()
            await db.commit()

        return title


# Singleton instance
conversation_service = ConversationService()
