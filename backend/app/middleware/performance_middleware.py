"""
Performance monitoring middleware (T229)
"""

import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging

logger = logging.getLogger(__name__)


class PerformanceMonitoringMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, slow_threshold_ms: float = 1000.0):
        super().__init__(app)
        self.slow_threshold_ms = slow_threshold_ms

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        response = await call_next(request)
        duration_ms = (time.time() - start_time) * 1000

        if duration_ms > self.slow_threshold_ms:
            logger.warning(f"Slow: {request.method} {request.url.path} - {duration_ms:.2f}ms")

        response.headers["X-Response-Time"] = f"{duration_ms:.2f}ms"
        return response
