#!/usr/bin/env python3
"""
vLLM Server Wrapper

This script starts a vLLM server with the configured model and settings.
It provides a FastAPI endpoint that wraps the vLLM OpenAI-compatible API.
"""

import os
import yaml
from typing import Optional, List, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import httpx


# Load configuration
def load_config() -> dict:
    """Load configuration from config.yaml"""
    config_path = os.path.join(os.path.dirname(__file__), "config.yaml")
    with open(config_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


config = load_config()


# Pydantic models for API
class ChatMessage(BaseModel):
    """Chat message structure"""

    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")


class GenerateRequest(BaseModel):
    """Request model for text generation"""

    messages: List[ChatMessage] = Field(..., description="Conversation messages")
    max_tokens: int = Field(default=4096, ge=1, le=8192, description="Maximum tokens to generate")
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Sampling temperature")
    top_p: float = Field(default=0.9, ge=0.0, le=1.0, description="Top-p sampling")
    stream: bool = Field(default=False, description="Enable streaming response")


class GenerateResponse(BaseModel):
    """Response model for text generation"""

    text: str = Field(..., description="Generated text")
    finish_reason: str = Field(..., description="Reason for completion")
    usage: Dict[str, int] = Field(..., description="Token usage statistics")


# Global HTTP client for vLLM server
vllm_client: Optional[httpx.AsyncClient] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app"""
    global vllm_client

    # Startup: Create HTTP client
    vllm_client = httpx.AsyncClient(
        base_url=config["vllm"]["base_url"],
        timeout=httpx.Timeout(config["vllm"]["timeout"], read=300.0),
    )

    yield

    # Shutdown: Close HTTP client
    if vllm_client:
        await vllm_client.aclose()


# Create FastAPI app
app = FastAPI(
    title="LLM Service",
    description="vLLM wrapper service for Local LLM application",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check if vLLM server is responsive
        response = await vllm_client.get("/health")
        if response.status_code == 200:
            return {"status": "healthy", "vllm": "online"}
        else:
            return {"status": "degraded", "vllm": "unhealthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}


@app.post("/v1/chat/completions")
async def chat_completions(request: GenerateRequest):
    """
    Generate chat completions using vLLM server.

    This endpoint wraps the vLLM OpenAI-compatible API.
    """
    try:
        # Build request payload for vLLM
        vllm_request = {
            "model": config["model"]["name"],
            "messages": [{"role": msg.role, "content": msg.content} for msg in request.messages],
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "top_p": request.top_p,
            "stream": request.stream,
        }

        if request.stream:
            # Streaming response
            return StreamingResponse(
                stream_vllm_response(vllm_request),
                media_type="text/event-stream",
            )
        else:
            # Non-streaming response
            response = await vllm_client.post(
                "/v1/chat/completions",
                json=vllm_request,
            )
            response.raise_for_status()
            data = response.json()

            # Extract response text
            choice = data["choices"][0]
            text = choice["message"]["content"]
            finish_reason = choice["finish_reason"]
            usage = data.get("usage", {})

            return GenerateResponse(
                text=text,
                finish_reason=finish_reason,
                usage=usage,
            )

    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=e.response.status_code,
            detail=f"vLLM server error: {e.response.text}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating response: {str(e)}")


async def stream_vllm_response(vllm_request: dict) -> AsyncGenerator[str, None]:
    """
    Stream response from vLLM server.

    Args:
        vllm_request: Request payload for vLLM

    Yields:
        Server-sent event strings
    """
    try:
        async with vllm_client.stream(
            "POST",
            "/v1/chat/completions",
            json=vllm_request,
        ) as response:
            response.raise_for_status()

            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    # Forward SSE data
                    yield f"{line}\n\n"

    except httpx.HTTPStatusError as e:
        error_msg = f"data: {{\"error\": \"vLLM server error: {e.response.status_code}\"}}\n\n"
        yield error_msg
    except Exception as e:
        error_msg = f"data: {{\"error\": \"{str(e)}\"}}\n\n"
        yield error_msg


@app.get("/models")
async def list_models():
    """List available models"""
    return {
        "models": [
            {
                "id": config["model"]["name"],
                "path": config["model"]["path"],
                "max_model_len": config["model"]["max_model_len"],
            }
        ]
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app,
        host=config["server"]["host"],
        port=config["server"]["port"],
        log_level=config["server"]["log_level"],
    )
