"""
LangGraph Server API Adapter

Provides LangGraph Server-compatible API endpoints for agent-chat-ui integration.
Maps LangGraph SDK calls to our existing UnifiedOrchestrator system.

Endpoints:
- GET /api/info - Server information
- GET /api/assistants/{assistant_id} - Get assistant details
- POST /api/threads - Create new thread (conversation)
- GET /api/threads/{thread_id} - Get thread details
- POST /api/threads/{thread_id}/runs/stream - Stream agent execution
"""
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID, uuid4
from datetime import datetime
from typing import Optional, Dict, Any, List
import json
import asyncio

from app.core.database import get_db
from app.models.user import User
from app.models.conversation import Conversation
from app.models.message import Message
from app.api.deps import get_current_user_optional
from app.services.unified_orchestrator_service import UnifiedOrchestrator

router = APIRouter(prefix="/api/v1", tags=["langgraph-adapter"])


# ============================================================
# Server Info
# ============================================================

@router.get("/info")
async def get_server_info():
    """
    GET /api/info

    Returns server information (LangGraph Server API compatible)
    """
    return {
        "version": "1.0.0",
        "server_type": "unified-agent",
        "capabilities": ["streaming", "progress_tracking", "tool_calls"]
    }


# ============================================================
# Assistants
# ============================================================

@router.post("/assistants/search")
async def search_assistants(request: Request):
    """
    POST /api/v1/assistants/search

    Search for assistants (LangGraph Server API compatible)

    For our use case, we return our fixed "unified-agent"
    """
    try:
        body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    except:
        body = {}

    # Return our unified agent as the only available assistant
    return [
        {
            "assistant_id": "unified-agent",
            "graph_id": "unified_orchestrator",
            "name": "Unified Agent",
            "description": "3-way intelligent routing agent (Direct/Reasoning/Specialized)",
            "config": {
                "configurable": {
                    "routes": ["direct", "reasoning", "specialized"],
                    "streaming": True
                }
            },
            "metadata": {
                "version": "1.0.0",
                "langgraph_integration": True
            },
            "created_at": "2025-11-10T00:00:00Z",
            "updated_at": "2025-11-10T00:00:00Z"
        }
    ]


@router.get("/assistants/{assistant_id}")
async def get_assistant(assistant_id: str):
    """
    GET /api/assistants/{assistant_id}

    Returns assistant information (LangGraph Server API compatible)

    We use a fixed assistant_id "unified-agent" for our UnifiedOrchestrator
    """
    if assistant_id != "unified-agent":
        raise HTTPException(status_code=404, detail=f"Assistant '{assistant_id}' not found")

    return {
        "assistant_id": "unified-agent",
        "graph_id": "unified_orchestrator",
        "name": "Unified Agent",
        "description": "3-way intelligent routing agent (Direct/Reasoning/Specialized)",
        "config": {
            "configurable": {
                "routes": ["direct", "reasoning", "specialized"],
                "streaming": True
            }
        },
        "metadata": {
            "version": "1.0.0",
            "langgraph_integration": True
        },
        "created_at": "2025-11-10T00:00:00Z",
        "updated_at": "2025-11-10T00:00:00Z"
    }


# ============================================================
# Threads (Conversations)
# ============================================================

@router.post("/threads")
async def create_thread(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    POST /api/threads

    Create new thread (conversation) - LangGraph Server API compatible

    Request body (optional):
    {
        "metadata": {...}
    }
    """
    # Use authenticated user or create anonymous
    if not current_user:
        # For agent-chat-ui without auth, create anonymous user
        # In production, you should handle this differently
        raise HTTPException(status_code=401, detail="Authentication required")

    # Parse request body
    try:
        body = await request.json() if request.headers.get("content-type") == "application/json" else {}
    except:
        body = {}

    metadata = body.get("metadata", {})

    # Create conversation (thread)
    conversation = Conversation(
        user_id=current_user.id,
        title=metadata.get("title", "New Conversation"),
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    return {
        "thread_id": str(conversation.id),
        "created_at": conversation.created_at.isoformat(),
        "metadata": metadata,
        "status": "active"
    }


@router.get("/threads/{thread_id}")
async def get_thread(
    thread_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    GET /api/threads/{thread_id}

    Get thread (conversation) details - LangGraph Server API compatible
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        thread_uuid = UUID(thread_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid thread_id format")

    # Get conversation
    result = await db.execute(
        select(Conversation).filter(
            Conversation.id == thread_uuid,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()

    if not conversation:
        raise HTTPException(status_code=404, detail=f"Thread '{thread_id}' not found")

    # Get messages
    messages_result = await db.execute(
        select(Message).filter(
            Message.conversation_id == thread_uuid
        ).order_by(Message.created_at)
    )
    messages = messages_result.scalars().all()

    # Convert to LangGraph format
    langgraph_messages = []
    for msg in messages:
        langgraph_messages.append({
            "type": "human" if msg.role == "user" else "ai",
            "content": msg.content,
            "additional_kwargs": {},
            "response_metadata": {}
        })

    return {
        "thread_id": str(conversation.id),
        "created_at": conversation.created_at.isoformat(),
        "updated_at": conversation.updated_at.isoformat(),
        "metadata": {
            "title": conversation.title
        },
        "status": "active",
        "values": {
            "messages": langgraph_messages
        }
    }


# ============================================================
# Streaming Runs
# ============================================================

@router.post("/threads/{thread_id}/runs/stream")
async def stream_thread_run(
    thread_id: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional)
):
    """
    POST /api/threads/{thread_id}/runs/stream

    Stream agent execution - LangGraph Server API compatible

    Request body:
    {
        "assistant_id": "unified-agent",
        "input": {
            "messages": [{"type": "human", "content": "..."}]
        },
        "config": {...},
        "stream_mode": ["values", "updates", "messages", "custom"]
    }

    SSE Response format:
    event: metadata
    data: {"run_id": "..."}

    event: updates
    data: {"node": "...", "state": {...}}

    event: messages/0/content
    data: "token"

    event: end
    data: null
    """
    if not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    try:
        thread_uuid = UUID(thread_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid thread_id format")

    # Verify conversation exists and belongs to user
    result = await db.execute(
        select(Conversation).filter(
            Conversation.id == thread_uuid,
            Conversation.user_id == current_user.id
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail=f"Thread '{thread_id}' not found")

    # Parse request body
    body = await request.json()
    assistant_id = body.get("assistant_id", "unified-agent")
    input_data = body.get("input", {})
    stream_modes = body.get("stream_mode", ["updates", "messages"])

    # Extract user message
    messages = input_data.get("messages", [])
    if not messages:
        raise HTTPException(status_code=400, detail="No messages in input")

    user_message = messages[-1]["content"]

    # Save user message
    user_msg = Message(
        conversation_id=thread_uuid,
        role="user",
        content=user_message
    )
    db.add(user_msg)
    await db.commit()

    # Get conversation history
    history_result = await db.execute(
        select(Message).filter(
            Message.conversation_id == thread_uuid
        ).order_by(Message.created_at).limit(10)
    )
    history = history_result.scalars().all()
    conversation_history = [
        {"role": msg.role, "content": msg.content}
        for msg in history
    ]

    # Stream generator
    async def event_generator():
        """Generate SSE events from UnifiedOrchestrator streaming"""
        run_id = str(uuid4())

        # Event: metadata
        yield f"event: metadata\n"
        yield f"data: {json.dumps({'run_id': run_id})}\n\n"

        try:
            # Initialize orchestrator
            orchestrator = UnifiedOrchestrator(db)

            # Streaming execution with astream
            final_response = None

            async for chunk in orchestrator.graph.astream(
                {
                    "query": user_message,
                    "conversation_id": thread_uuid,
                    "conversation_history": conversation_history[:-1],  # Exclude current message
                    "classification_confidence": 0.0,
                    "classification_method": "",
                    "route": "",
                    "complexity": "",
                    "clarified_intent": "",
                    "rerouted_to": None,
                    "agent_type": None,
                    "agent_sequence": [],
                    "tools_used": [],
                    "final_response": "",
                    "execution_log": [],
                    "processing_time_ms": 0,
                    "error": None
                },
                stream_mode=["updates", "messages", "custom"]
            ):
                # Handle different chunk types
                if isinstance(chunk, tuple) and len(chunk) == 2:
                    event_type, data = chunk

                    if event_type == "updates":
                        # Node state updates
                        node_name = data
                        yield f"event: updates\n"
                        yield f"data: {json.dumps({'node': node_name, 'type': 'node_update'})}\n\n"

                    elif event_type == "custom":
                        # Custom progress events from get_stream_writer()
                        yield f"event: custom\n"
                        yield f"data: {json.dumps(data)}\n\n"

                    elif event_type == "messages":
                        # LLM token streaming (if ChatModel is used)
                        yield f"event: messages/0/content\n"
                        yield f"data: {json.dumps(data)}\n\n"

                    # Track final response
                    if isinstance(data, dict) and "final_response" in data:
                        final_response = data["final_response"]

            # Event: end
            yield f"event: end\n"
            yield f"data: null\n\n"

            # Save assistant response
            if final_response:
                assistant_msg = Message(
                    conversation_id=thread_uuid,
                    role="assistant",
                    content=final_response
                )
                db.add(assistant_msg)
                await db.commit()

        except Exception as e:
            # Event: error
            yield f"event: error\n"
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )
