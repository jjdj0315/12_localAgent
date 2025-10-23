"""Conversation schemas"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation"""
    title: Optional[str] = Field(default="New Conversation", max_length=255)
    tags: Optional[List[str]] = Field(default_factory=list, max_items=10)


class ConversationUpdate(BaseModel):
    """Schema for updating a conversation"""
    title: Optional[str] = Field(None, max_length=255)
    tags: Optional[List[str]] = Field(None, max_items=10)


class ConversationResponse(BaseModel):
    """Schema for conversation response"""
    id: UUID
    user_id: UUID
    title: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    message_count: int = 0
    document_count: int = 0

    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Schema for message response"""
    id: UUID
    conversation_id: UUID
    role: str
    content: str
    char_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationWithMessages(BaseModel):
    """Schema for conversation with all messages"""
    id: UUID
    user_id: UUID
    title: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse]

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    """Schema for paginated conversation list"""
    conversations: List[ConversationResponse]
    total: int
    page: int
    page_size: int
    has_next: bool
