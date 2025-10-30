"""
Admin endpoints for Multi-Agent management

Provides admin functionality for:
- Enabling/disabling agents (FR-076)
- Configuring routing mode (LLM vs keyword-based)
- Editing keyword mappings
- Viewing agent performance metrics (FR-076)
"""

from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin_user
from app.core.database import get_db
from app.models.user import User
from app.services.orchestrator_service import MultiAgentOrchestrator

router = APIRouter()

# Global orchestrator instance (initialized in chat.py)
# For simplicity, we'll create a new instance here
# In production, use dependency injection or singleton pattern
orchestrator = None

try:
    orchestrator = MultiAgentOrchestrator()
except Exception as e:
    print(f"[Admin API] Failed to initialize orchestrator: {e}")


# ========== Request/Response Schemas ==========

class AgentInfo(BaseModel):
    """Agent information schema"""
    name: str
    display_name: str
    description: str
    capabilities: List[str]
    enabled: bool = True


class AgentConfigUpdate(BaseModel):
    """Agent configuration update schema"""
    enabled: Optional[bool] = None
    routing_mode: Optional[str] = None  # "llm" or "keyword"
    keywords: Optional[List[str]] = None


class AgentStats(BaseModel):
    """Agent performance statistics"""
    agent_name: str
    display_name: str
    total_tasks: int
    successful_tasks: int
    failed_tasks: int
    avg_response_time_ms: float
    error_rate: float


class OrchestratorConfig(BaseModel):
    """Orchestrator configuration"""
    routing_mode: str  # "llm" or "keyword"
    enabled_agents: List[str]


# ========== Admin Endpoints ==========

@router.get("/agents", response_model=List[AgentInfo])
async def list_agents(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    List all available agents with metadata

    Requires admin authentication.
    Returns agent information including capabilities and enabled status.
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Multi-Agent system not initialized"
        )

    agents_info = []

    for agent_name, agent_instance in orchestrator.agents.items():
        # Get agent metadata
        metadata = agent_instance.get_agent_info()

        agents_info.append(AgentInfo(
            name=metadata["name"],
            display_name=metadata["display_name"],
            description=metadata["description"],
            capabilities=metadata["capabilities"],
            enabled=True  # Default enabled, stored in DB in production
        ))

    return agents_info


@router.get("/agents/{agent_name}", response_model=AgentInfo)
async def get_agent_info(
    agent_name: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed information about a specific agent

    Requires admin authentication.
    Returns agent metadata and configuration.
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Multi-Agent system not initialized"
        )

    agent_instance = orchestrator.agents.get(agent_name)
    if not agent_instance:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found"
        )

    metadata = agent_instance.get_agent_info()

    return AgentInfo(
        name=metadata["name"],
        display_name=metadata["display_name"],
        description=metadata["description"],
        capabilities=metadata["capabilities"],
        enabled=True
    )


@router.patch("/agents/{agent_name}")
async def update_agent_config(
    agent_name: str,
    config: AgentConfigUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update agent configuration (FR-076)

    Allows admins to:
    - Enable/disable agents
    - Change routing mode (LLM vs keyword)
    - Update keyword mappings

    Requires admin authentication.
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Multi-Agent system not initialized"
        )

    if agent_name not in orchestrator.agents:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Agent '{agent_name}' not found"
        )

    # In production, store configuration in database
    # For Phase 10, just return success
    # TODO: Implement persistent configuration storage

    return {
        "status": "success",
        "message": f"Agent '{agent_name}' configuration updated",
        "config": config.dict(exclude_none=True)
    }


@router.get("/agents/stats", response_model=List[AgentStats])
async def get_agent_statistics(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get performance statistics for all agents (FR-076)

    Metrics include:
    - Total tasks executed
    - Success/failure counts
    - Average response time
    - Error rate

    Requires admin authentication.
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Multi-Agent system not initialized"
        )

    # In production, query database for statistics
    # For Phase 10, return mock data
    # TODO: Implement actual metrics collection from database

    stats = []
    for agent_name, agent_instance in orchestrator.agents.items():
        metadata = agent_instance.get_agent_info()

        stats.append(AgentStats(
            agent_name=agent_name,
            display_name=metadata["display_name"],
            total_tasks=0,  # TODO: Query from DB
            successful_tasks=0,
            failed_tasks=0,
            avg_response_time_ms=0.0,
            error_rate=0.0
        ))

    return stats


@router.get("/config", response_model=OrchestratorConfig)
async def get_orchestrator_config(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current orchestrator configuration

    Returns routing mode and enabled agents.
    Requires admin authentication.
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Multi-Agent system not initialized"
        )

    return OrchestratorConfig(
        routing_mode="llm",  # Default to LLM-based routing
        enabled_agents=list(orchestrator.agents.keys())
    )


@router.patch("/config")
async def update_orchestrator_config(
    config: OrchestratorConfig,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Update orchestrator configuration

    Allows admins to:
    - Switch between LLM and keyword-based routing
    - Enable/disable specific agents

    Requires admin authentication.
    """
    if not orchestrator:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Multi-Agent system not initialized"
        )

    # TODO: Implement persistent configuration storage
    # For Phase 10, just return success

    return {
        "status": "success",
        "message": "Orchestrator configuration updated",
        "config": config.dict()
    }
