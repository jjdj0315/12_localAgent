"""Metrics collection middleware

Automatically tracks HTTP request metrics for all API endpoints.
"""

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from app.core.metrics import (
    http_request_duration,
    http_requests_total,
    http_requests_in_progress
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to collect HTTP request metrics

    Tracks:
    - Request duration
    - Request count (by method, endpoint, status code)
    - In-progress requests
    """

    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint to avoid recursion
        if request.url.path == "/metrics":
            return await call_next(request)

        # Extract endpoint path (without query params)
        endpoint = request.url.path
        method = request.method

        # Track in-progress requests
        http_requests_in_progress.inc()

        # Record start time
        start_time = time.time()

        try:
            # Process request
            response: Response = await call_next(request)
            status_code = response.status_code

            # Record successful request
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=status_code
            ).inc()

            return response

        except Exception as e:
            # Record failed request (500 error)
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status_code=500
            ).inc()

            # Re-raise exception
            raise

        finally:
            # Record request duration
            duration = time.time() - start_time
            http_request_duration.labels(
                method=method,
                endpoint=endpoint,
                status_code=getattr(response, 'status_code', 500) if 'response' in locals() else 500
            ).observe(duration)

            # Decrement in-progress counter
            http_requests_in_progress.dec()
