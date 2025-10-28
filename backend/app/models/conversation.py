"""Conversation model"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import BigInteger, Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def get_current_utc():
    """Get current UTC time with timezone"""
    return datetime.now(timezone.utc)


class Conversation(Base):
    """
    Conversation model for storing chat sessions.

    Clarification 2025-10-28: Added last_accessed_at and storage_size_bytes
    for auto-cleanup when user storage reaches 10GB limit.
    """

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), default="New Conversation", nullable=False)
    tags = Column(JSONB, default=list, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_current_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_current_utc, onupdate=get_current_utc, nullable=False, index=True)
    last_accessed_at = Column(
        DateTime(timezone=True),
        default=get_current_utc,
        onupdate=get_current_utc,
        nullable=False,
        index=True,
        comment="Last access timestamp for auto-cleanup (Clarification 2025-10-28)"
    )
    storage_size_bytes = Column(
        BigInteger,
        default=0,
        nullable=False,
        comment="Total storage used by conversation + documents for quota enforcement (Clarification 2025-10-28)"
    )

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="conversation", cascade="all, delete-orphan")
    # DEPRECATED: conversation_documents will be removed in future migration (use documents relationship instead)
    conversation_documents = relationship("ConversationDocument", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Conversation {self.title}>"
