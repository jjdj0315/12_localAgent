"""
Conversations API endpoints for managing conversation history.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.api.deps import get_current_user, get_db
from backend.app.models.user import User
from backend.app.schemas.conversation import (
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
    ConversationWithMessages,
)

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
    # TODO: Implement conversation listing with search and filtering
    # This will be implemented in Phase 4 (User Story 2)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Conversation listing not yet implemented",
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
    # TODO: Implement conversation creation
    # This will be implemented in Phase 4 (User Story 2)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Conversation creation not yet implemented",
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
    # TODO: Implement conversation retrieval
    # This will be implemented in Phase 4 (User Story 2)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Conversation retrieval not yet implemented",
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
    # TODO: Implement conversation update
    # This will be implemented in Phase 4 (User Story 2)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Conversation update not yet implemented",
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
    # TODO: Implement conversation deletion
    # This will be implemented in Phase 4 (User Story 2)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Conversation deletion not yet implemented",
    )
