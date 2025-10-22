"""Message schemas"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class MessageCreate(BaseModel):
    """Schema for creating a message"""
    conversation_id: Optional[UUID] = None
    content: str = Field(..., min_length=1, max_length=10000)
    document_ids: Optional[list[UUID]] = None


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


class ChatRequest(BaseModel):
    """Schema for chat request"""
    conversation_id: Optional[UUID] = None
    content: str = Field(..., min_length=1, max_length=10000)
    document_ids: Optional[list[UUID]] = None


class ChatResponse(BaseModel):
    """Schema for chat response"""
    conversation_id: UUID
    message: MessageResponse
