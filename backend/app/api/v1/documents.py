"""
Documents API endpoints for file upload and document management.
"""
from typing import Optional
from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentWithText,
)

router = APIRouter()


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a document for analysis.

    Supported formats: PDF, DOCX, TXT
    Maximum size: 50MB

    - **file**: Document file to upload
    """
    # TODO: Implement document upload
    # This will be implemented in Phase 5 (User Story 3)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Document upload not yet implemented",
    )


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List user's uploaded documents with pagination.

    - **page**: Page number (1-indexed)
    - **page_size**: Items per page (1-100)
    """
    # TODO: Implement document listing
    # This will be implemented in Phase 5 (User Story 3)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Document listing not yet implemented",
    )


@router.get("/{document_id}", response_model=DocumentWithText)
async def get_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve document metadata and extracted text.

    - **document_id**: UUID of the document
    """
    # TODO: Implement document retrieval
    # This will be implemented in Phase 5 (User Story 3)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Document retrieval not yet implemented",
    )


@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a document and its associated file.

    - **document_id**: UUID of the document
    """
    # TODO: Implement document deletion
    # This will be implemented in Phase 5 (User Story 3)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Document deletion not yet implemented",
    )
