"""Monitoring and metrics endpoints

Provides Prometheus metrics endpoint for system monitoring.
"""

from fastapi import APIRouter
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from starlette.responses import Response

router = APIRouter()


@router.get("/metrics")
async def metrics():
    """
    Prometheus metrics endpoint

    Returns metrics in Prometheus text format for scraping.
    This endpoint should be accessible without authentication for Prometheus server.
    """
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
