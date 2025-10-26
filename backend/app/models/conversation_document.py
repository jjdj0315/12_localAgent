"""
ConversationDocument association model for linking conversations to documents.
"""
from sqlalchemy import Column, ForeignKey, Table
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

# Association table for many-to-many relationship between conversations and documents
conversation_document = Table(
    "conversation_documents",
    Base.metadata,
    Column(
        "conversation_id",
        UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    Column(
        "document_id",
        UUID(as_uuid=True),
        ForeignKey("documents.id", ondelete="CASCADE"),
        primary_key=True,
    ),
    extend_existing=True,
)
