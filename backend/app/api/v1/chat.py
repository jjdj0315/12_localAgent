"""Chat endpoints for LLM interaction"""

from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.models.user import User
from app.schemas.message import ChatRequest, ChatResponse, MessageResponse
from app.services.llm_service import llm_service

router = APIRouter()


async def get_conversation_history(
    db: AsyncSession, conversation_id: UUID
) -> list[dict]:
    """Get conversation history for context"""
    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()

    return [{"role": msg.role.value, "content": msg.content} for msg in messages]


@router.post("/send", response_model=ChatResponse)
async def send_chat_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send chat message and get LLM response (non-streaming).

    Creates or uses existing conversation.
    Saves user message and assistant response to database.
    """
    # Create or get conversation
    conversation_id = request.conversation_id
    if not conversation_id:
        # Create new conversation
        conversation = Conversation(
            user_id=current_user.id, title=request.content[:50]  # First 50 chars as title
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        conversation_id = conversation.id
        history = []
    else:
        # Get existing conversation history
        history = await get_conversation_history(db, conversation_id)

    # Save user message
    user_message = Message(
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=request.content,
        char_count=len(request.content),
    )
    db.add(user_message)
    await db.commit()

    # Get LLM response
    response_text = await llm_service.generate(request.content, history)

    # Save assistant message
    assistant_message = Message(
        conversation_id=conversation_id,
        role=MessageRole.ASSISTANT,
        content=response_text,
        char_count=len(response_text),
    )
    db.add(assistant_message)
    await db.commit()
    await db.refresh(assistant_message)

    return ChatResponse(
        conversation_id=conversation_id,
        message=MessageResponse.from_orm(assistant_message),
    )


@router.post("/stream")
async def stream_chat_message(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Send chat message with streaming response (SSE).

    Returns Server-Sent Events stream of tokens.
    """
    # Create or get conversation
    conversation_id = request.conversation_id
    if not conversation_id:
        conversation = Conversation(
            user_id=current_user.id, title=request.content[:50]
        )
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        conversation_id = conversation.id
        history = []
    else:
        history = await get_conversation_history(db, conversation_id)

    # Save user message
    user_message = Message(
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=request.content,
        char_count=len(request.content),
    )
    db.add(user_message)
    await db.commit()

    # Stream generator
    async def generate():
        """Generate SSE stream"""
        import json
        full_response = []
        message_id = uuid4()

        try:
            # Stream tokens
            async for token in llm_service.generate_stream(request.content, history):
                full_response.append(token)
                data = json.dumps({"token": token})
                yield f"event: token\ndata: {data}\n\n"

            # Save complete response
            response_text = "".join(full_response)
            assistant_message = Message(
                id=message_id,
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=response_text,
                char_count=len(response_text),
            )
            db.add(assistant_message)
            await db.commit()

            # Send done event
            data = json.dumps({"conversation_id": str(conversation_id), "message_id": str(message_id)})
            yield f"event: done\ndata: {data}\n\n"

        except Exception as e:
            # Send error event
            data = json.dumps({"error": str(e)})
            yield f"event: error\ndata: {data}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
