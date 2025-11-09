"""
Rate limiting middleware (T232, T317)

Uses Redis for distributed rate limiting across multiple workers.
Falls back to in-memory storage if Redis is unavailable.
"""

import logging
import time
from collections import defaultdict, deque
from typing import Callable, Dict, Optional

from fastapi import HTTPException, Request, status
from redis.exceptions import RedisError
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.redis_client import get_redis

logger = logging.getLogger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, requests_per_minute: int = 60):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        # Fallback in-memory storage (if Redis unavailable)
        self.requests: Dict[str, deque] = defaultdict(deque)
        # Try to get Redis client
        self.redis = get_redis()
        if self.redis:
            logger.info("Rate limiting using Redis (distributed)")
        else:
            logger.warning("Rate limiting using in-memory storage (non-distributed)")

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

        # Use Redis if available, otherwise fallback to in-memory
        if self.redis:
            count, remaining = await self._check_rate_limit_redis(client_ip)
        else:
            count, remaining = self._check_rate_limit_memory(client_ip)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response

    async def _check_rate_limit_redis(self, client_ip: str) -> tuple[int, int]:
        """
        Check rate limit using Redis (distributed across workers).

        Uses Redis sliding window algorithm:
        1. Increment counter for current minute
        2. Set expiry to 60 seconds
        3. Check if count exceeds limit

        Args:
            client_ip: Client IP address

        Returns:
            Tuple of (current_count, remaining_requests)

        Raises:
            HTTPException: If rate limit exceeded
        """
        try:
            # Current minute timestamp (rounded to minute)
            current_minute = int(time.time() / 60)
            key = f"rate_limit:{client_ip}:{current_minute}"

            # Increment counter atomically
            count = self.redis.incr(key)

            # Set expiry on first request of this minute
            if count == 1:
                self.redis.expire(key, 60)

            # Check limit
            if count > self.requests_per_minute:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="요청 횟수가 제한을 초과했습니다. 잠시 후 다시 시도해주세요.",
                )

            remaining = max(0, self.requests_per_minute - count)
            return count, remaining

        except RedisError as e:
            logger.warning(f"Redis error in rate limiting, falling back to in-memory: {e}")
            # Fallback to in-memory
            return self._check_rate_limit_memory(client_ip)

    def _check_rate_limit_memory(self, client_ip: str) -> tuple[int, int]:
        """
        Check rate limit using in-memory storage (fallback).

        NOTE: This is NOT distributed across workers, so each worker
        tracks limits independently. This is a degraded mode.

        Args:
            client_ip: Client IP address

        Returns:
            Tuple of (current_count, remaining_requests)

        Raises:
            HTTPException: If rate limit exceeded
        """
        # Clean old requests (older than 1 minute)
        now = time.time()
        if client_ip in self.requests:
            while self.requests[client_ip] and self.requests[client_ip][0] < now - 60:
                self.requests[client_ip].popleft()

        # Check rate limit
        count = len(self.requests[client_ip])
        if count >= self.requests_per_minute:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="요청 횟수가 제한을 초과했습니다. 잠시 후 다시 시도해주세요.",
            )

        # Add current request
        self.requests[client_ip].append(now)
        count += 1

        remaining = max(0, self.requests_per_minute - count)
        return count, remaining
