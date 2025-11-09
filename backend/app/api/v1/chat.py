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
from app.schemas.message import ChatRequest, ChatResponse, MessageResponse, ReActStepResponse, MultiAgentResult
from app.services.llm_service import llm_service
from app.services.document_service import document_service
from app.services.safety_filter_service import SafetyFilterService
from app.services.react_agent_service import ReActAgentService
from app.services.orchestrator_service import MultiAgentOrchestrator
from app.services.llm_cache_service import llm_cache_service

router = APIRouter()

# Initialize Multi-Agent Orchestrator (singleton)
try:
    orchestrator = MultiAgentOrchestrator()
    print("[Chat API] Multi-Agent Orchestrator initialized")
except Exception as e:
    print(f"[Chat API] Failed to initialize Multi-Agent Orchestrator: {e}")
    orchestrator = None


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

        # LLM generate function (async wrapper for sync context)
        def llm_generate(prompt: str) -> str:
            import asyncio
            # Run async generate in sync context (ThreadPoolExecutor thread)
            # Always create a new event loop for this thread
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                result = new_loop.run_until_complete(llm_service.generate(prompt))
                return result
            except Exception as e:
                print(f"[ReAct] LLM generation error: {e}")
                return f"Error: {str(e)}"
            finally:
                new_loop.close()

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

        # T226: Check message limit (FR-041: 1000 messages per conversation)
        message_count = len(history)
        MAX_MESSAGES = 1000

        if message_count >= MAX_MESSAGES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "message_limit_exceeded",
                    "message": f"이 대화는 최대 메시지 수({MAX_MESSAGES}개)에 도달했습니다. 새 대화를 시작해주세요.",
                    "current_count": message_count,
                    "max_count": MAX_MESSAGES
                }
            )
        elif message_count >= MAX_MESSAGES * 0.9:  # 90% warning
            # Add warning to response (will be included in ChatResponse)
            warning_msg = f"⚠️ 이 대화는 {message_count}/{MAX_MESSAGES}개 메시지를 사용 중입니다. 곧 제한에 도달합니다."
            # Store warning in request context for later use
            request.warning = warning_msg

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

    # ======== MULTI-AGENT OR REACT AGENT OR STANDARD LLM ========
    react_steps = None
    tools_used = None
    multi_agent_result = None

    if request.use_multi_agent:
        # Use Multi-Agent Orchestrator (Phase 10)
        if orchestrator:
            ma_result = await orchestrator.route_and_execute(
                user_query=filtered_input,
                context={"conversation_history": history}
            )

            # Combine agent outputs for response
            if ma_result["agent_outputs"]:
                # Combine all agent responses
                agent_responses = []
                for agent_name, output in ma_result["agent_outputs"].items():
                    agent_responses.append(f"[{agent_name}]\n{output}")

                response_text = "\n\n---\n\n".join(agent_responses)
            else:
                response_text = "죄송합니다. Multi-Agent 처리 중 오류가 발생했습니다."

            processing_time_ms = ma_result["execution_time_ms"]

            # Store multi-agent result
            multi_agent_result = MultiAgentResult(
                workflow_type=ma_result["workflow_type"],
                agent_outputs=ma_result["agent_outputs"],
                execution_log=ma_result["execution_log"],
                errors=ma_result["errors"],
                execution_time_ms=ma_result["execution_time_ms"]
            )
        else:
            response_text = "죄송합니다. Multi-Agent 시스템이 초기화되지 않았습니다."
            processing_time_ms = 0

    elif request.use_react_agent:
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
        import time
        start_time = time.time()

        # Check if response can be cached and try to get from cache
        is_cacheable = llm_cache_service.is_cacheable(
            query=request.content,  # Use original query (before PII masking) for cache key
            conversation_id=request.conversation_id,
            document_ids=request.document_ids
        )

        cached_response = None
        if is_cacheable:
            cached_response = llm_cache_service.get_cached_response(request.content)

        if cached_response:
            # Cache hit - use cached response
            response_text = cached_response
            processing_time_ms = int((time.time() - start_time) * 1000)  # Cache lookup time (~1ms)
        else:
            # Cache miss - generate new response
            response_text = await llm_service.generate(
                filtered_input, max_tokens=4000
            )
            processing_time_ms = int((time.time() - start_time) * 1000)

            # Cache the response if cacheable
            if is_cacheable:
                llm_cache_service.set_cached_response(request.content, response_text)

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
        tools_used=tools_used,
        multi_agent_result=multi_agent_result
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

        # T226: Check message limit (FR-041: 1000 messages per conversation)
        message_count = len(history)
        MAX_MESSAGES = 1000

        if message_count >= MAX_MESSAGES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "message_limit_exceeded",
                    "message": f"이 대화는 최대 메시지 수({MAX_MESSAGES}개)에 도달했습니다. 새 대화를 시작해주세요.",
                    "current_count": message_count,
                    "max_count": MAX_MESSAGES
                }
            )

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
            # Build prompt with history and document context
            prompt_parts = []

            # Add system prompt
            system_prompt = """당신은 도움이 되고 정확한 AI 어시스턴트입니다.
사용자의 질문에 친절하고 명확하게 답변해주세요.
한국어로 자연스럽게 대화하며, 간결하고 이해하기 쉬운 답변을 제공하세요."""
            prompt_parts.append(f"시스템: {system_prompt}\n")

            # Add document context if provided
            if document_context:
                prompt_parts.append(f"[참고 문서]\n{document_context}\n")

            # Add conversation history
            if history:
                for msg in history[-10:]:  # Last 10 messages
                    role = msg.get("role", "user")
                    content = msg.get("content", "")
                    if role == "user":
                        prompt_parts.append(f"사용자: {content}")
                    elif role == "assistant":
                        prompt_parts.append(f"답변: {content}")

            # Add current query
            prompt_parts.append(f"사용자: {filtered_input}")
            prompt_parts.append("답변:")

            full_prompt = "\n".join(prompt_parts)

            # Stream tokens
            async for token in llm_service.generate_stream(full_prompt):
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
