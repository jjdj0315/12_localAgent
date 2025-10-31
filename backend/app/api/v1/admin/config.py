"""
Resource limit configuration endpoint (T211, FR-084)
Admin-only access for adjusting concurrency limits
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
from pydantic import BaseModel, Field
import json
from pathlib import Path

from app.core.database import get_db

router = APIRouter()

# Resource limit configuration file
RESOURCE_CONFIG_FILE = Path("backend/config/resource_limits.json")
RESOURCE_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Default limits (FR-086)
DEFAULT_LIMITS = {
    "max_react_sessions": 10,
    "max_agent_workflows": 5,
    "max_conversation_messages": 1000,
    "max_response_length": 4000,
    "max_document_response_length": 10000,
    "max_upload_size_mb": 50,
    "rate_limit_per_minute": 60
}


class ResourceLimits(BaseModel):
    """Resource limit configuration"""
    max_react_sessions: int = Field(ge=1, le=50, default=10)
    max_agent_workflows: int = Field(ge=1, le=20, default=5)
    max_conversation_messages: int = Field(ge=100, le=5000, default=1000)
    max_response_length: int = Field(ge=1000, le=20000, default=4000)
    max_document_response_length: int = Field(ge=5000, le=50000, default=10000)
    max_upload_size_mb: int = Field(ge=10, le=500, default=50)
    rate_limit_per_minute: int = Field(ge=10, le=300, default=60)


class EffectTimeInfo(BaseModel):
    """Effect time information for configuration changes"""
    setting: str
    effect_time: str
    requires_restart: bool


def load_resource_limits() -> ResourceLimits:
    """Load resource limits from config file"""
    if not RESOURCE_CONFIG_FILE.exists():
        # Create default config
        save_resource_limits(ResourceLimits(**DEFAULT_LIMITS))
        return ResourceLimits(**DEFAULT_LIMITS)

    with open(RESOURCE_CONFIG_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
        return ResourceLimits(**data)


def save_resource_limits(limits: ResourceLimits):
    """Save resource limits to config file"""
    with open(RESOURCE_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(limits.dict(), f, ensure_ascii=False, indent=2)


@router.get("/resource-limits", response_model=ResourceLimits)
async def get_resource_limits(
    db: AsyncSession = Depends(get_db)
):
    """
    Get current resource limits (FR-084)

    Admin only access required
    """
    limits = load_resource_limits()
    return limits


@router.put("/resource-limits", response_model=ResourceLimits)
async def update_resource_limits(
    limits: ResourceLimits,
    db: AsyncSession = Depends(get_db)
):
    """
    Update resource limits (FR-084)

    Admin only access required

    Effect times:
    - max_react_sessions: Immediate (in-memory)
    - max_agent_workflows: Immediate (in-memory)
    - max_conversation_messages: Next message
    - max_response_length: Next message
    - max_upload_size_mb: Immediate
    - rate_limit_per_minute: Immediate
    """
    save_resource_limits(limits)

    return limits


@router.get("/resource-limits/effect-times")
async def get_effect_times(
    db: AsyncSession = Depends(get_db)
):
    """
    Get effect time information for all settings (FR-084)

    Admin only access required
    """
    effect_times = [
        EffectTimeInfo(
            setting="max_react_sessions",
            effect_time="â‹ (T®¨ t¥0)",
            requires_restart=False
        ),
        EffectTimeInfo(
            setting="max_agent_workflows",
            effect_time="â‹ (T®¨ t¥0)",
            requires_restart=False
        ),
        EffectTimeInfo(
            setting="max_conversation_messages",
            effect_time="‰L T‹¿Ä0",
            requires_restart=False
        ),
        EffectTimeInfo(
            setting="max_response_length",
            effect_time="‰L T‹¿Ä0",
            requires_restart=False
        ),
        EffectTimeInfo(
            setting="max_document_response_length",
            effect_time="‰L T‹¿Ä0",
            requires_restart=False
        ),
        EffectTimeInfo(
            setting="max_upload_size_mb",
            effect_time="â‹",
            requires_restart=False
        ),
        EffectTimeInfo(
            setting="rate_limit_per_minute",
            effect_time="â‹ (¯‰Ë¥ ¨\‹)",
            requires_restart=False
        )
    ]

    return {"effect_times": effect_times}


@router.post("/resource-limits/reset")
async def reset_resource_limits(
    db: AsyncSession = Depends(get_db)
):
    """
    Reset resource limits to default values (FR-084)

    Admin only access required
    """
    default_limits = ResourceLimits(**DEFAULT_LIMITS)
    save_resource_limits(default_limits)

    return {
        "message": "¨å§ \t 0¯<\ 0T»µ»‰.",
        "limits": default_limits
    }


@router.get("/resource-limits/current-usage")
async def get_current_usage(
    db: AsyncSession = Depends(get_db)
):
    """
    Get current resource usage (FR-084)

    Shows:
    - Active ReAct sessions
    - Active agent workflows
    - Rate limit usage by IP

    Admin only access required
    """
    # In production, query from middleware/service
    # For now, return mock data
    # TODO: Implement actual usage tracking

    return {
        "react_sessions": {
            "active": 0,
            "max": load_resource_limits().max_react_sessions
        },
        "agent_workflows": {
            "active": 0,
            "max": load_resource_limits().max_agent_workflows
        },
        "rate_limit": {
            "requests_this_minute": 0,
            "max_per_minute": load_resource_limits().rate_limit_per_minute
        }
    }
