"""
Health check endpoints (T227)

Provides system health status for monitoring:
- Database connectivity
- LLM service status
- Storage availability
"""

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any
import os
import psutil
from datetime import datetime

from app.core.database import get_db

router = APIRouter()


@router.get("/health", tags=["health"])
async def health_check() -> Dict[str, Any]:
    """
    Basic health check endpoint

    Returns:
        - status: "healthy" or "unhealthy"
        - timestamp: Current server time
        - version: Application version
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": os.getenv("APP_VERSION", "1.0.0"),
        "service": "local-llm-webapp"
    }


@router.get("/health/detailed", tags=["health"])
async def detailed_health_check(db: AsyncSession = None) -> Dict[str, Any]:
    """
    Detailed health check with all components

    Checks:
    - Database connectivity
    - LLM service availability
    - Storage disk space
    - Memory usage

    Returns:
        Component-wise health status
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {}
    }

    # 1. Database check
    db_healthy = await check_database_health(db)
    health_status["components"]["database"] = db_healthy

    # 2. LLM service check
    llm_healthy = check_llm_service_health()
    health_status["components"]["llm_service"] = llm_healthy

    # 3. Storage check
    storage_healthy = check_storage_health()
    health_status["components"]["storage"] = storage_healthy

    # 4. System resources
    system_healthy = check_system_resources()
    health_status["components"]["system"] = system_healthy

    # Overall status
    all_healthy = all(
        comp.get("status") == "healthy"
        for comp in health_status["components"].values()
    )
    health_status["status"] = "healthy" if all_healthy else "degraded"

    return health_status


@router.get("/health/ready", tags=["health"])
async def readiness_check(db: AsyncSession = None) -> Dict[str, str]:
    """
    Readiness probe for Kubernetes/Docker

    Returns 200 if ready to serve traffic, 503 otherwise
    """
    try:
        # Check critical components
        db_ok = await check_database_health(db)
        llm_ok = check_llm_service_health()

        if db_ok["status"] == "healthy" and llm_ok["status"] == "healthy":
            return {"status": "ready"}
        else:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not ready"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Readiness check failed: {str(e)}"
        )


@router.get("/health/live", tags=["health"])
async def liveness_check() -> Dict[str, str]:
    """
    Liveness probe for Kubernetes/Docker

    Returns 200 if application is running, 503 otherwise
    """
    return {"status": "alive"}


# Helper functions

async def check_database_health(db: AsyncSession = None) -> Dict[str, Any]:
    """Check PostgreSQL database connectivity"""
    try:
        if db is None:
            # Get new session if not provided
            from app.core.database import SessionLocal
            async with SessionLocal() as session:
                result = await session.execute(text("SELECT 1"))
                result.fetchone()
        else:
            result = await db.execute(text("SELECT 1"))
            result.fetchone()

        return {
            "status": "healthy",
            "message": "Database connection successful",
            "response_time_ms": 0  # TODO: Add timing
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Database connection failed: {str(e)}",
            "error": str(e)
        }


def check_llm_service_health() -> Dict[str, Any]:
    """Check LLM service availability"""
    try:
        from app.services.llm_service import llm_service

        # Check if service is initialized
        if llm_service is None:
            return {
                "status": "unhealthy",
                "message": "LLM service not initialized"
            }

        # Check backend type
        backend = os.getenv("LLM_BACKEND", "llama_cpp")

        return {
            "status": "healthy",
            "message": "LLM service available",
            "backend": backend
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"LLM service check failed: {str(e)}",
            "error": str(e)
        }


def check_storage_health() -> Dict[str, Any]:
    """Check storage disk space"""
    try:
        # Check uploads directory
        uploads_path = os.getenv("UPLOADS_PATH", "/uploads")

        if os.path.exists(uploads_path):
            disk_usage = psutil.disk_usage(uploads_path)

            # Warning if less than 20% free
            percent_free = (disk_usage.free / disk_usage.total) * 100

            status_str = "healthy"
            if percent_free < 10:
                status_str = "critical"
            elif percent_free < 20:
                status_str = "warning"

            return {
                "status": status_str,
                "message": f"{percent_free:.1f}% free space",
                "total_gb": disk_usage.total / (1024**3),
                "used_gb": disk_usage.used / (1024**3),
                "free_gb": disk_usage.free / (1024**3),
                "percent_free": percent_free
            }
        else:
            return {
                "status": "warning",
                "message": f"Uploads directory not found: {uploads_path}"
            }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"Storage check failed: {str(e)}",
            "error": str(e)
        }


def check_system_resources() -> Dict[str, Any]:
    """Check system CPU and memory"""
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()

        status_str = "healthy"
        if memory.percent > 90 or cpu_percent > 90:
            status_str = "critical"
        elif memory.percent > 80 or cpu_percent > 80:
            status_str = "warning"

        return {
            "status": status_str,
            "cpu_percent": cpu_percent,
            "memory_percent": memory.percent,
            "memory_available_gb": memory.available / (1024**3),
            "memory_total_gb": memory.total / (1024**3)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "message": f"System resource check failed: {str(e)}",
            "error": str(e)
        }
