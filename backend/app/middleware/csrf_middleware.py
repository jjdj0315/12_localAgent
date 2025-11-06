"""CSRF protection middleware

This module implements Cross-Site Request Forgery (CSRF) protection for all
state-changing requests (POST, PUT, DELETE, PATCH) per FR-110.

CSRF tokens are generated per session and validated on every state-changing request.
Login and setup endpoints are exempt to allow initial authentication.
"""
import secrets
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection for state-changing requests (FR-110)

    Flow:
    1. GET requests: Generate and set CSRF token cookie (only if missing)
    2. POST/PUT/DELETE/PATCH: Validate token from cookie matches X-CSRF-Token header
    3. Exempt paths: Login, setup, health checks

    Optimizations (T312):
    - Token reissue only when missing (not every GET)
    - Prefix-based exempt path matching
    """

    # Exact paths exempt from CSRF validation (allow unauthenticated access)
    CSRF_EXEMPT_PATHS = {
        "/api/v1/auth/login",
        "/health",
        "/api/v1/health",
        "/metrics",
        "/docs",
        "/openapi.json",
    }

    # Path prefixes exempt from CSRF validation
    CSRF_EXEMPT_PREFIXES = [
        "/api/v1/setup/",  # All setup wizard endpoints
    ]

    def _is_exempt_path(self, path: str) -> bool:
        """Check if path is exempt from CSRF validation (T312)"""
        # Check exact match
        if path in self.CSRF_EXEMPT_PATHS:
            return True

        # Check prefix match
        for prefix in self.CSRF_EXEMPT_PREFIXES:
            if path.startswith(prefix):
                return True

        return False

    async def dispatch(self, request: Request, call_next):
        """Process request with CSRF protection"""

        # GET, HEAD, OPTIONS bypass CSRF check (safe methods)
        if request.method in ("GET", "HEAD", "OPTIONS"):
            response = await call_next(request)

            # Generate CSRF token only if missing (T312 optimization)
            # Skip for exempt paths to avoid unnecessary tokens
            if not self._is_exempt_path(request.url.path):
                existing_token = request.cookies.get("csrf_token")

                if not existing_token:
                    # Generate new token only when missing
                    csrf_token = secrets.token_urlsafe(32)
                    response.set_cookie(
                        key="csrf_token",
                        value=csrf_token,
                        httponly=False,  # JavaScript needs to read this for headers
                        secure=settings.cookie_secure,     # Environment-based (FR-112)
                        samesite=settings.cookie_samesite,  # Environment-based (FR-112)
                        max_age=settings.SESSION_TIMEOUT_MINUTES * 60  # Match session timeout
                    )
                    logger.debug(f"CSRF token generated for path: {request.url.path}")
                else:
                    # Token already exists, reuse it (T312 optimization)
                    logger.debug(f"CSRF token reused for path: {request.url.path}")
            return response

        # POST, PUT, DELETE, PATCH require CSRF validation
        # Check if path is exempt (exact or prefix match)
        if self._is_exempt_path(request.url.path):
            logger.debug(f"CSRF exempt path: {request.url.path}")
            return await call_next(request)

        # Validate CSRF token
        csrf_cookie = request.cookies.get("csrf_token")
        csrf_header = request.headers.get("X-CSRF-Token")

        if not csrf_cookie or csrf_cookie != csrf_header:
            logger.warning(
                f"CSRF validation failed for {request.method} {request.url.path} - "
                f"cookie={'present' if csrf_cookie else 'missing'}, "
                f"header={'present' if csrf_header else 'missing'}, "
                f"match={csrf_cookie == csrf_header if csrf_cookie and csrf_header else False}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF 토큰이 유효하지 않습니다. 페이지를 새로고침 후 다시 시도해주세요."
            )

        logger.debug(f"CSRF validation passed for {request.method} {request.url.path}")
        return await call_next(request)
