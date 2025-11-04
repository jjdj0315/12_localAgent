"""
Conversations API endpoints for managing conversation history.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func, select

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.models.message import Message
from app.models.document import Document
from app.schemas.conversation import (
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
    ConversationWithMessages,
    MessageResponse,
)
from app.services.conversation_service import conversation_service

router = APIRouter()


@router.get("", response_model=ConversationListResponse)
async def list_conversations(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search in titles and tags"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List user's conversations with pagination and filtering.

    - **page**: Page number (1-indexed)
    - **page_size**: Items per page (1-100)
    - **search**: Keyword search in title and tags
    - **tag**: Filter by specific tag
    """
    conversations, total = await conversation_service.list_conversations(
        db=db,
        user_id=current_user.id,
        page=page,
        page_size=page_size,
        search=search,
        tag=tag,
    )

    # Get message count and document count for each conversation
    conversation_responses = []
    for conv in conversations:
        # Count messages for this conversation
        count_query = select(func.count()).where(Message.conversation_id == conv.id)
        result = await db.execute(count_query)
        message_count = result.scalar() or 0

        # Count documents for this conversation
        doc_count_query = select(func.count()).where(Document.conversation_id == conv.id)
        doc_result = await db.execute(doc_count_query)
        document_count = doc_result.scalar() or 0

        conv_dict = {
            "id": conv.id,
            "user_id": conv.user_id,
            "title": conv.title,
            "tags": conv.tags or [],
            "created_at": conv.created_at,
            "updated_at": conv.updated_at,
            "message_count": message_count,
            "document_count": document_count,
        }
        conversation_responses.append(ConversationResponse(**conv_dict))

    has_next = (page * page_size) < total

    return ConversationListResponse(
        conversations=conversation_responses,
        total=total,
        page=page,
        page_size=page_size,
        has_next=has_next,
    )


@router.post("", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new conversation.

    - **title**: Conversation title
    - **tags**: Optional tags for organization
    """
    new_conversation = await conversation_service.create_conversation(
        db=db,
        user_id=current_user.id,
        title=conversation.title,
        tags=conversation.tags,
    )

    return ConversationResponse(
        id=new_conversation.id,
        user_id=new_conversation.user_id,
        title=new_conversation.title,
        tags=new_conversation.tags or [],
        created_at=new_conversation.created_at,
        updated_at=new_conversation.updated_at,
        message_count=0,
        document_count=0,
    )


@router.get("/{conversation_id}", response_model=ConversationWithMessages)
async def get_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieve a conversation with all its messages.

    - **conversation_id**: UUID of the conversation
    """
    conversation = await conversation_service.get_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Convert messages to response format (sorted by created_at)
    sorted_messages = sorted(conversation.messages, key=lambda msg: msg.created_at)
    message_responses = [
        MessageResponse(
            id=msg.id,
            conversation_id=msg.conversation_id,
            role=msg.role.value,
            content=msg.content,
            char_count=msg.char_count,
            created_at=msg.created_at,
        )
        for msg in sorted_messages
    ]

    return ConversationWithMessages(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        tags=conversation.tags or [],
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=message_responses,
    )


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    updates: ConversationUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update conversation metadata (title, tags).

    - **conversation_id**: UUID of the conversation
    - **title**: New title (optional)
    - **tags**: New tags array (optional)
    """
    updated_conversation = await conversation_service.update_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        title=updates.title,
        tags=updates.tags,
    )

    if not updated_conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Get message count
    count_query = select(func.count()).where(Message.conversation_id == updated_conversation.id)
    result = await db.execute(count_query)
    message_count = result.scalar() or 0

    # Get document count
    doc_count_query = select(func.count()).where(Document.conversation_id == updated_conversation.id)
    doc_result = await db.execute(doc_count_query)
    document_count = doc_result.scalar() or 0

    return ConversationResponse(
        id=updated_conversation.id,
        user_id=updated_conversation.user_id,
        title=updated_conversation.title,
        tags=updated_conversation.tags or [],
        created_at=updated_conversation.created_at,
        updated_at=updated_conversation.updated_at,
        message_count=message_count,
        document_count=document_count,
    )


@router.delete("/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a conversation and all its messages.

    - **conversation_id**: UUID of the conversation
    """
    deleted = await conversation_service.delete_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return None
