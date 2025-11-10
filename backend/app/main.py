"""FastAPI application entry point"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.core.logging import setup_logging  # T313
from app.core.scheduler import start_scheduler, stop_scheduler
from app.middleware.metrics import MetricsMiddleware
from app.middleware.csrf_middleware import CSRFMiddleware
from app.middleware.rate_limit_middleware import RateLimitMiddleware
from app.middleware.resource_limit_middleware import ResourceLimitMiddleware
from app.middleware.performance_middleware import PerformanceMonitoringMiddleware
from app.core.business_metrics import update_all_business_metrics
import asyncio

# Setup logging before anything else (T313)
setup_logging()
logger = logging.getLogger(__name__)


def validate_production_config():
    """Validate production environment configuration (T312, T315)"""
    if settings.ENVIRONMENT == "production":
        warnings = []
        errors = []

        # Check SECRET_KEY strength (T315)
        if settings.is_default_secret_key():
            errors.append(
                "❌ CRITICAL: Using default or weak SECRET_KEY in production!"
            )
            errors.append(
                "   Generate a strong key: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
            )
            errors.append("   Set SECRET_KEY environment variable")

        # Check secure cookie settings (T312)
        if not settings.cookie_secure:
            errors.append(
                "❌ CRITICAL: cookie_secure is False in production. "
                "Cookies will be transmitted over HTTP!"
            )
            errors.append("   Set COOKIE_SECURE=true or ENVIRONMENT=development")

        if settings.cookie_samesite != "strict":
            warnings.append(
                f"⚠️  SECURITY WARNING: cookie_samesite is '{settings.cookie_samesite}' in production. "
                "Consider using 'strict' for maximum security."
            )

        # Log all warnings
        for warning in warnings:
            logger.warning(warning)

        # Log all errors
        for error in errors:
            logger.error(error)

        # Fail startup if any critical errors found
        if errors:
            raise RuntimeError(f"Production environment has {len(errors)} critical security issue(s)")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Validate production configuration (T312)
    validate_production_config()
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION} in {settings.ENVIRONMENT} mode")

    # Startup: Start the scheduler
    start_scheduler()

    # Initialize Prometheus business metrics
    asyncio.create_task(update_all_business_metrics())

    yield

    # Shutdown: Stop the scheduler
    logger.info("Shutting down application...")
    stop_scheduler()

# Create FastAPI app
# Note: Model loading happens on first request (lazy loading) to avoid blocking server startup
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Local LLM Web Application API for Local Government",
    lifespan=lifespan,
)

# Configure middleware stack (FR-111)
# IMPORTANT: Middleware execution order is REVERSE of registration order
# (last registered = first executed)
# Execution flow: CORS → CSRF → RateLimit → ResourceLimit → Performance → Metrics

# 6. Metrics middleware (innermost - executed last, measures actual request time)
app.add_middleware(MetricsMiddleware)

# 5. Performance monitoring (logs slow requests before rate limiting)
app.add_middleware(PerformanceMonitoringMiddleware, slow_threshold_ms=1000.0)

# 4. Resource limit enforcement (prevents resource exhaustion)
app.add_middleware(
    ResourceLimitMiddleware,
    max_react_sessions=10,
    max_agent_workflows=5
)

# 3. Rate limiting (blocks excessive requests per IP)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60)

# 2. CSRF protection (validates tokens for POST/PUT/DELETE/PATCH)
app.add_middleware(CSRFMiddleware)

# 1. CORS configuration (outermost - executed first, handles preflight)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Local LLM Web Application API",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


# Import API routers
from app.api.v1 import admin, auth, chat, conversations, documents, health, setup, metrics, monitoring, langgraph_adapter

# Register routers
app.include_router(setup.router, prefix="/api/v1", tags=["Setup"])  # No auth required for setup
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["Chat"])
app.include_router(conversations.router, prefix="/api/v1/conversations", tags=["Conversations"])
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(admin.router, prefix="/api/v1/admin", tags=["Admin"])
app.include_router(metrics.router, prefix="/api/v1/metrics", tags=["Metrics"])
app.include_router(monitoring.router, tags=["Monitoring"])  # Prometheus metrics (no auth, no prefix)
app.include_router(health.router, prefix="/api/v1", tags=["Health"])
app.include_router(langgraph_adapter.router, tags=["LangGraph"])  # LangGraph Server API compatibility (no prefix, already has /api)
