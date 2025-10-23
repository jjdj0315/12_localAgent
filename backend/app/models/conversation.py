"""Conversation model"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def get_current_utc():
    """Get current UTC time with timezone"""
    return datetime.now(timezone.utc)


class Conversation(Base):
    """Conversation model for storing chat sessions"""

    __tablename__ = "conversations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), default="New Conversation", nullable=False)
    tags = Column(JSONB, default=list, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_current_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_current_utc, onupdate=get_current_utc, nullable=False, index=True)

    # Relationships
    user = relationship("User", back_populates="conversations")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")
    conversation_documents = relationship("ConversationDocument", back_populates="conversation", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Conversation {self.title}>"
