"""
Document Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class DocumentBase(BaseModel):
    """Base document schema with common fields."""

    filename: str = Field(..., description="Original filename")
    file_type: str = Field(..., description="File type (PDF, DOCX, TXT)")


class DocumentCreate(DocumentBase):
    """Schema for creating a new document (metadata only, file via multipart)."""

    pass


class DocumentUpdate(BaseModel):
    """Schema for updating document metadata."""

    filename: Optional[str] = Field(None, description="New filename")


class DocumentResponse(DocumentBase):
    """Schema for document response."""

    id: UUID
    user_id: UUID
    file_path: str
    file_size: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


class DocumentWithText(DocumentResponse):
    """Schema for document response including extracted text."""

    extracted_text: Optional[str] = Field(None, description="Extracted text content")


class DocumentListResponse(BaseModel):
    """Schema for paginated document list response."""

    documents: list[DocumentResponse]
    total: int
    page: int
    page_size: int
