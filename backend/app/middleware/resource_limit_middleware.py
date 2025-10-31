"""
Resource limit middleware (T204, FR-086)

Limits:
- Max 10 ReAct sessions
- Max 5 multi-agent workflows
- Queue or return 503 when exceeded
"""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import asyncio
from collections import defaultdict

class ResourceLimitMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app,
        max_react_sessions: int = 10,
        max_agent_workflows: int = 5
    ):
        super().__init__(app)
        self.max_react_sessions = max_react_sessions
        self.max_agent_workflows = max_agent_workflows
        
        # Track active sessions
        self.active_react_sessions = 0
        self.active_agent_workflows = 0
        self.react_lock = asyncio.Lock()
        self.agent_lock = asyncio.Lock()
        
    async def dispatch(self, request: Request, call_next: Callable):
        path = request.url.path
        
        # Check if this is a ReAct or agent request
        is_react = "/react" in path or "/tools" in path
        is_agent = "/agent" in path or "/workflow" in path
        
        if is_react:
            async with self.react_lock:
                if self.active_react_sessions >= self.max_react_sessions:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="ReAct 세션이 최대 용량에 도달했습니다. 잠시 후 다시 시도해주세요."
                    )
                self.active_react_sessions += 1
            
            try:
                response = await call_next(request)
                return response
            finally:
                async with self.react_lock:
                    self.active_react_sessions -= 1
        
        elif is_agent:
            async with self.agent_lock:
                if self.active_agent_workflows >= self.max_agent_workflows:
                    raise HTTPException(
                        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                        detail="멀티 에이전트 워크플로우가 최대 용량에 도달했습니다. 잠시 후 다시 시도해주세요."
                    )
                self.active_agent_workflows += 1
            
            try:
                response = await call_next(request)
                return response
            finally:
                async with self.agent_lock:
                    self.active_agent_workflows -= 1
        
        else:
            # Regular request
            response = await call_next(request)
            return response
