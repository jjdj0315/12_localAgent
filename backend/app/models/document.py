"""Document model"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def get_current_utc():
    """Get current UTC time with timezone"""
    return datetime.now(timezone.utc)


class Document(Base):
    """
    Document model for uploaded files.

    IMPORTANT (Clarification 2025-10-28): Documents are conversation-scoped.
    Each document belongs to exactly ONE conversation and is automatically
    deleted when the parent conversation is deleted.
    """

    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Parent conversation (documents belong to one conversation per Clarification 2025-10-28)"
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="Document owner (redundant for isolation checks)"
    )
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False, unique=True)
    file_size = Column(Integer, nullable=False, comment="File size in bytes (max 50MB)")
    file_type = Column(String(50), nullable=False, comment="pdf, docx, txt")
    extracted_text = Column(Text, nullable=True, comment="Extracted text content for search/Q&A")
    uploaded_at = Column(DateTime(timezone=True), nullable=False, default=get_current_utc)
    last_accessed_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=get_current_utc,
        onupdate=get_current_utc,
        index=True,
        comment="Last access timestamp for auto-cleanup (Clarification 2025-10-28)"
    )

    # Relationships
    user = relationship("User", back_populates="documents")
    conversation = relationship("Conversation", back_populates="documents")
    conversation_documents = relationship("ConversationDocument", back_populates="document", cascade="all, delete-orphan")


class ConversationDocument(Base):
    """Association table for conversations and documents"""

    __tablename__ = "conversation_documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, index=True)
    added_at = Column(DateTime(timezone=True), nullable=False, default=get_current_utc)

    # Relationships
    conversation = relationship("Conversation", back_populates="conversation_documents")
    document = relationship("Document", back_populates="conversation_documents")
