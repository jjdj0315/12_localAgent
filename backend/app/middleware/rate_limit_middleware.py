"""
Rate limiting middleware (T232, T317)
"""

import time
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable, Dict, Optional
from collections import defaultdict, deque

class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.requests: Dict[str, deque] = defaultdict(deque)

    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP address from request (T317).

        Handles reverse proxy scenarios by checking:
        1. X-Forwarded-For (standard proxy header)
        2. X-Real-IP (nginx)
        3. request.client.host (direct connection)

        Returns first IP in X-Forwarded-For chain (original client).
        """
        # Check X-Forwarded-For (comma-separated list: client, proxy1, proxy2)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take first IP (original client)
            client_ip = forwarded_for.split(",")[0].strip()
            return client_ip

        # Check X-Real-IP (nginx)
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()

        # Fallback to direct connection IP
        return request.client.host if request.client else "unknown"

    async def dispatch(self, request: Request, call_next: Callable):
        # Get client IP (with proxy support - T317)
        client_ip = self._get_client_ip(request)
        
        # Clean old requests (older than 1 minute)
        now = time.time()
        if client_ip in self.requests:
            while self.requests[client_ip] and self.requests[client_ip][0] < now - 60:
                self.requests[client_ip].popleft()
        
        # Check rate limit
        if len(self.requests[client_ip]) >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="요청 횟수가 제한을 초과했습니다. 잠시 후 다시 시도해주세요."
            )
        
        # Add current request
        self.requests[client_ip].append(now)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = self.requests_per_minute - len(self.requests[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        
        return response
