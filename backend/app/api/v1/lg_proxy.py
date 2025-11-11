"""
LangGraph API Proxy Router
FastAPI를 통해 LangGraph API를 프록시하면서 인증/권한을 적용
"""
import os
import httpx
from typing import Optional
from fastapi import APIRouter, Request, Response, Depends, HTTPException
from fastapi.responses import StreamingResponse
import logging
import uuid

from app.api.deps import get_current_user
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter()

# 환경 변수에서 LangGraph 설정 읽기
LANGGRAPH_API_URL = os.getenv("LANGGRAPH_API_URL", "http://localhost:2024")
LANGGRAPH_API_KEY = os.getenv("LANGGRAPH_API_KEY", "")

# Hop-by-hop 헤더 제거 목록
HOP_BY_HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade"
}


@router.api_route("/lg/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"])
async def proxy_to_langgraph(
    request: Request,
    path: str,
    current_user: User = Depends(get_current_user)
):
    """
    LangGraph API로 요청을 프록시
    - 인증: get_current_user로 세션 확인
    - 포워딩: LANGGRAPH_API_URL로 요청 전달
    - 응답: 스트리밍 포함 그대로 반환
    """

    # Correlation ID 생성/전파
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

    # 대상 URL 구성
    target_url = f"{LANGGRAPH_API_URL}/{path}"
    if request.url.query:
        target_url += f"?{request.url.query}"

    logger.info(f"Proxying {request.method} {path} for user {current_user.email} (correlation_id={correlation_id})")

    # 헤더 준비 (민감한 쿠키 제거, LangGraph 인증 추가)
    headers = {}
    for name, value in request.headers.items():
        name_lower = name.lower()
        if name_lower not in HOP_BY_HOP_HEADERS and name_lower != "cookie" and name_lower != "host":
            headers[name] = value

    headers["X-Correlation-ID"] = correlation_id
    headers["X-Forwarded-For"] = request.client.host if request.client else "unknown"
    headers["X-Forwarded-User"] = current_user.email

    # LangGraph 인증 헤더 추가
    if LANGGRAPH_API_KEY:
        headers["Authorization"] = f"Bearer {LANGGRAPH_API_KEY}"

    # 바디 읽기
    body = await request.body() if request.method in ["POST", "PUT", "PATCH"] else None

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # LangGraph로 요청 전송
            response = await client.request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                follow_redirects=False
            )

            # 응답 헤더 준비 (hop-by-hop 제거)
            response_headers = {}
            for name, value in response.headers.items():
                if name.lower() not in HOP_BY_HOP_HEADERS:
                    response_headers[name] = value

            # 스트리밍 응답인 경우
            if "text/event-stream" in response.headers.get("content-type", ""):
                # SSE 스트리밍 처리
                async def stream_generator():
                    async for chunk in response.aiter_bytes(chunk_size=1024):
                        yield chunk

                return StreamingResponse(
                    stream_generator(),
                    status_code=response.status_code,
                    headers=response_headers,
                    media_type="text/event-stream"
                )
            else:
                # 일반 응답
                return Response(
                    content=response.content,
                    status_code=response.status_code,
                    headers=response_headers
                )

    except httpx.ConnectError as e:
        logger.error(f"Failed to connect to LangGraph: {e} (correlation_id={correlation_id})")
        raise HTTPException(status_code=502, detail="Bad Gateway - LangGraph service unavailable")
    except httpx.TimeoutException as e:
        logger.error(f"LangGraph request timeout: {e} (correlation_id={correlation_id})")
        raise HTTPException(status_code=504, detail="Gateway Timeout - LangGraph request timeout")
    except Exception as e:
        logger.error(f"Unexpected error in LangGraph proxy: {e} (correlation_id={correlation_id})")
        raise HTTPException(status_code=500, detail="Internal Server Error")