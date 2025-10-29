"""Chat endpoints for LLM interaction"""

import asyncio
from typing import Optional
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core.database import get_db, SyncSessionLocal
from app.models.conversation import Conversation
from app.models.message import Message, MessageRole
from app.models.user import User
from app.schemas.message import ChatRequest, ChatResponse, MessageResponse, ReActStepResponse
from app.services.llm_service import llm_service
from app.services.document_service import document_service
from app.services.safety_filter_service import SafetyFilterService
from app.services.react_agent_service import ReActAgentService

router = APIRouter()


def run_safety_filter_sync(content: str, user_id: UUID, conversation_id: Optional[UUID], phase: str, bypass_rule_based: bool = False):
    """
    Run safety filter in sync context (called from async via run_in_executor).

    Args:
        content: Content to filter
        user_id: User ID
        conversation_id: Conversation ID
        phase: "input" or "output"
        bypass_rule_based: Bypass rule-based filter for retry

    Returns:
        FilterCheckResponse
    """
    sync_db = SyncSessionLocal()
    try:
        filter_service = SafetyFilterService(sync_db, enable_ml=True)
        result = filter_service.check_content(
            content=content,
            user_id=user_id,
            conversation_id=conversation_id,
            phase=phase,
            bypass_rule_based=bypass_rule_based
        )
        sync_db.commit()
        return result
    finally:
        sync_db.close()


def run_react_agent_sync(query: str, user_id: UUID, conversation_id: UUID):
    """
    Run ReAct agent in sync context (called from async via run_in_executor).

    Args:
        query: User query
        user_id: User ID
        conversation_id: Conversation ID

    Returns:
        Dict with final_answer, steps, tools_used
    """
    sync_db = SyncSessionLocal()
    try:
        # Initialize ReAct agent
        agent = ReActAgentService(sync_db, user_id, conversation_id)

        # LLM generate function
        def llm_generate(prompt: str) -> str:
            return llm_service.generate(prompt)

        # Execute ReAct loop
        result = agent.execute_react_loop(query, llm_generate, max_iterations=5)

        sync_db.commit()
        return result
    finally:
        sync_db.close()


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
    Applies two-phase safety filtering (rule-based + ML-based).
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

    # ======== PHASE 1: INPUT FILTERING ========
    # Run safety filter on user input
    loop = asyncio.get_event_loop()
    filter_result = await loop.run_in_executor(
        None,
        run_safety_filter_sync,
        request.content,
        current_user.id,
        conversation_id,
        "input",
        getattr(request, 'bypass_filter', False)  # Check if bypass requested
    )

    # If content is unsafe, reject with safe message
    if not filter_result.is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "content_filtered",
                "message": filter_result.safe_message,
                "categories": filter_result.categories,
                "can_retry": filter_result.can_retry
            }
        )

    # Use filtered content (with PII masked)
    filtered_input = filter_result.filtered_content

    # Get document context if document_ids provided
    document_context = None
    if request.document_ids:
        documents = []
        for doc_id in request.document_ids:
            doc = await document_service.get_document(db, doc_id, current_user.id)
            if doc:
                documents.append(doc)
                # Attach document to conversation
                await document_service.attach_document_to_conversation(
                    db, conversation_id, doc_id
                )

        if documents:
            document_context = "\n\n---\n\n".join(
                [f"[{doc.filename}]\n{doc.extracted_text}" for doc in documents]
            )

    # Save user message (with PII masked)
    user_message = Message(
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=filtered_input,  # Store masked content
        char_count=len(filtered_input),
    )
    db.add(user_message)
    await db.commit()

    # ======== REACT AGENT OR STANDARD LLM ========
    react_steps = None
    tools_used = None

    if request.use_react_agent:
        # Use ReAct Agent with tools
        react_result = await loop.run_in_executor(
            None,
            run_react_agent_sync,
            filtered_input,
            current_user.id,
            conversation_id
        )

        response_text = react_result["final_answer"]
        processing_time_ms = 0  # Total time already tracked in tool executions

        # Convert steps for response
        react_steps = [
            ReActStepResponse(
                iteration=step.iteration,
                thought=step.thought,
                action=step.action,
                action_input=step.action_input,
                observation=step.observation,
                timestamp=step.timestamp
            )
            for step in react_result.get("steps", [])
        ]

        tools_used = react_result.get("tools_used", [])

    else:
        # Standard LLM response with document context
        response_text, processing_time_ms = await llm_service.generate(
            filtered_input, history, document_context
        )

    # ======== PHASE 2: OUTPUT FILTERING ========
    # Run safety filter on LLM output
    output_filter_result = await loop.run_in_executor(
        None,
        run_safety_filter_sync,
        response_text,
        current_user.id,
        conversation_id,
        "output",
        False  # Never bypass output filter
    )

    # If LLM output is unsafe, replace with safe message
    if not output_filter_result.is_safe:
        response_text = "죄송합니다. AI 응답에 부적절한 내용이 포함되어 처리할 수 없습니다. 다른 방식으로 질문해주세요."
    else:
        # Use filtered output (with PII masked)
        response_text = output_filter_result.filtered_content

    # Save assistant message with processing time
    assistant_message = Message(
        conversation_id=conversation_id,
        role=MessageRole.ASSISTANT,
        content=response_text,
        char_count=len(response_text),
        processing_time_ms=processing_time_ms,
    )
    db.add(assistant_message)
    await db.commit()
    await db.refresh(assistant_message)

    return ChatResponse(
        conversation_id=conversation_id,
        message=MessageResponse.from_orm(assistant_message),
        react_steps=react_steps,
        tools_used=tools_used
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
    Applies two-phase safety filtering (input before streaming, output after completion).
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

    # ======== INPUT FILTERING (Before Streaming) ========
    loop = asyncio.get_event_loop()
    filter_result = await loop.run_in_executor(
        None,
        run_safety_filter_sync,
        request.content,
        current_user.id,
        conversation_id,
        "input",
        getattr(request, 'bypass_filter', False)
    )

    # If content is unsafe, return error event
    if not filter_result.is_safe:
        async def error_generator():
            import json
            data = json.dumps({
                "error": "content_filtered",
                "message": filter_result.safe_message,
                "categories": filter_result.categories,
                "can_retry": filter_result.can_retry
            })
            yield f"event: error\ndata: {data}\n\n"

        return StreamingResponse(error_generator(), media_type="text/event-stream")

    # Use filtered input
    filtered_input = filter_result.filtered_content

    # Get document context if document_ids provided
    document_context = None
    if request.document_ids:
        documents = []
        for doc_id in request.document_ids:
            doc = await document_service.get_document(db, doc_id, current_user.id)
            if doc:
                documents.append(doc)
                # Attach document to conversation
                await document_service.attach_document_to_conversation(
                    db, conversation_id, doc_id
                )

        if documents:
            document_context = "\n\n---\n\n".join(
                [f"[{doc.filename}]\n{doc.extracted_text}" for doc in documents]
            )

    # Save user message (with PII masked)
    user_message = Message(
        conversation_id=conversation_id,
        role=MessageRole.USER,
        content=filtered_input,
        char_count=len(filtered_input),
    )
    db.add(user_message)
    await db.commit()

    # Stream generator
    async def generate():
        """Generate SSE stream with output filtering"""
        import json
        full_response = []
        message_id = uuid4()

        try:
            # Stream tokens with document context (use filtered input)
            async for token in llm_service.generate_stream(
                filtered_input, history, document_context
            ):
                full_response.append(token)
                data = json.dumps({"token": token})
                yield f"event: token\ndata: {data}\n\n"

            # ======== OUTPUT FILTERING (After Streaming Complete) ========
            response_text = "".join(full_response)

            # Run output filter
            output_filter_result = await loop.run_in_executor(
                None,
                run_safety_filter_sync,
                response_text,
                current_user.id,
                conversation_id,
                "output",
                False
            )

            # If unsafe, replace with safe message
            if not output_filter_result.is_safe:
                response_text = "죄송합니다. AI 응답에 부적절한 내용이 포함되어 처리할 수 없습니다."
                # Send warning event
                data = json.dumps({"warning": "output_filtered", "message": response_text})
                yield f"event: warning\ndata: {data}\n\n"
            else:
                # Use filtered output (PII masked)
                response_text = output_filter_result.filtered_content

            # Save complete response
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
