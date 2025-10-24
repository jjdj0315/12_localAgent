"""Message model"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, Enum, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import enum

from app.core.database import Base


def get_current_utc():
    """Get current UTC time with timezone"""
    return datetime.now(timezone.utc)


class MessageRole(str, enum.Enum):
    """Message role enum"""
    USER = "user"
    ASSISTANT = "assistant"


class Message(Base):
    """Message model for storing conversation messages"""

    __tablename__ = "messages"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    role = Column(Enum(MessageRole, name='messagetype', create_constraint=True, native_enum=True, values_callable=lambda obj: [e.value for e in obj]), nullable=False)
    content = Column(Text, nullable=False)
    char_count = Column(Integer, nullable=False)
    processing_time_ms = Column(Integer, nullable=True, comment="LLM response generation time in milliseconds")
    created_at = Column(DateTime(timezone=True), default=get_current_utc, nullable=False)

    # Relationships
    conversation = relationship("Conversation", back_populates="messages")

    def __repr__(self) -> str:
        return f"<Message {self.role.value}: {self.content[:50]}...>"
