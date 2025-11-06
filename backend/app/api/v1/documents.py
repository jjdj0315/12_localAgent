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

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.document import (
    DocumentListResponse,
    DocumentResponse,
    DocumentWithText,
)
from app.services.document_service import document_service

# Import Prometheus metrics
from app.core.metrics import documents_uploaded_total

router = APIRouter()


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    conversation_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Upload a document for analysis.

    Supported formats: PDF, DOCX, TXT
    Maximum size: 50MB

    - **file**: Document file to upload
    - **conversation_id**: (Optional) ID of conversation to attach document to. If not provided, a new conversation will be created.
    """
    # Check user storage quota (80% warning threshold)
    from app.services.admin_service import AdminService
    storage_stats = await AdminService.get_storage_stats(db)

    # Get user's current storage usage
    user_storage = 0
    for user_stat in storage_stats.get("per_user_storage", []):
        if user_stat["user_id"] == str(current_user.id):
            user_storage = user_stat["total_bytes"]
            break

    # Assume 10GB quota per user (10 * 1024 * 1024 * 1024 bytes)
    user_quota = 10 * 1024 * 1024 * 1024
    usage_percent = (user_storage / user_quota * 100) if user_quota > 0 else 0

    # Read file content
    file_content = await file.read()

    # Check if upload would exceed quota
    if usage_percent > 80:
        # Return warning in response headers but allow upload
        pass  # Can add warning header here

    # Validate file
    is_valid, error_msg, file_type = await document_service.validate_file(
        file_content, file.filename
    )

    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    # Get or create conversation
    from app.models.conversation import Conversation
    from uuid import UUID as PyUUID

    target_conversation_id = None
    if conversation_id:
        # Use existing conversation
        try:
            target_conversation_id = PyUUID(conversation_id)
            # Verify conversation belongs to user
            from sqlalchemy import select
            conv_query = select(Conversation).where(
                Conversation.id == target_conversation_id,
                Conversation.user_id == current_user.id
            )
            conv_result = await db.execute(conv_query)
            conversation = conv_result.scalar_one_or_none()

            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="대화를 찾을 수 없거나 접근 권한이 없습니다.",
                )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="잘못된 대화 ID 형식입니다.",
            )
    else:
        # Create new conversation for this document
        conversation = Conversation(
            user_id=current_user.id,
            title=f"문서: {file.filename}",
        )
        db.add(conversation)
        await db.flush()  # Get the ID
        target_conversation_id = conversation.id

    # Save document
    try:
        document = await document_service.save_document(
            db=db,
            user_id=current_user.id,
            conversation_id=target_conversation_id,
            filename=file.filename,
            file_content=file_content,
            file_type=file_type,
        )

        # Track successful document upload
        documents_uploaded_total.labels(status='success').inc()

    except ValueError as e:
        # Track failed upload
        documents_uploaded_total.labels(status='error').inc()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        # Track failed upload
        documents_uploaded_total.labels(status='error').inc()

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"문서 업로드 중 오류가 발생했습니다: {str(e)}",
        )

    return DocumentResponse(
        id=document.id,
        user_id=document.user_id,
        filename=document.filename,
        file_path=document.file_path,
        file_type=document.file_type,
        file_size=document.file_size,
        uploaded_at=document.uploaded_at,
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
    documents, total = await document_service.list_documents(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
    )

    document_responses = [
        DocumentResponse(
            id=doc.id,
            user_id=doc.user_id,
            filename=doc.filename,
            file_path=doc.file_path,
            file_type=doc.file_type,
            file_size=doc.file_size,
            uploaded_at=doc.uploaded_at,
        )
        for doc in documents
    ]

    has_next = (page * page_size) < total

    return DocumentListResponse(
        documents=document_responses,
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
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
    document = await document_service.get_document(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
    )

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return DocumentWithText(
        id=document.id,
        user_id=document.user_id,
        filename=document.filename,
        file_type=document.file_type,
        file_size=document.file_size,
        uploaded_at=document.uploaded_at,
        extracted_text=document.extracted_text,
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
    deleted = await document_service.delete_document(
        db=db,
        document_id=document_id,
        user_id=current_user.id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found",
        )

    return None
