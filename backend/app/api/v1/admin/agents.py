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
import json
from pathlib import Path

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


# ========== Keyword Configuration (T210, FR-084) ==========

# Agent keyword configuration file
AGENT_CONFIG_FILE = Path("backend/config/agent_keywords.json")
AGENT_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)

# Default keywords (FR-073)
DEFAULT_KEYWORDS = {
    "research_agent": [
        "조사", "연구", "분석", "데이터", "통계", "정보 수집"
    ],
    "document_agent": [
        "문서 작성", "초안", "공문", "보고서", "양식", "템플릿"
    ],
    "code_agent": [
        "코드", "프로그래밍", "스크립트", "SQL", "쿼리", "개발"
    ],
    "policy_agent": [
        "정책", "법령", "규정", "조례", "규칙", "지침"
    ],
    "general_agent": [
        # General agent is fallback, no specific keywords
    ]
}


def load_agent_keywords() -> Dict[str, List[str]]:
    """Load agent keywords from config file"""
    if not AGENT_CONFIG_FILE.exists():
        # Create default config
        save_agent_keywords(DEFAULT_KEYWORDS)
        return DEFAULT_KEYWORDS

    with open(AGENT_CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_agent_keywords(keywords: Dict[str, List[str]]):
    """Save agent keywords to config file"""
    with open(AGENT_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(keywords, f, ensure_ascii=False, indent=2)


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


class AgentKeywordConfig(BaseModel):
    """Agent keyword configuration (T210)"""
    agent_name: str
    keywords: List[str]


class AgentKeywordBulkUpdate(BaseModel):
    """Bulk update for agent keywords (T210)"""
    configs: Dict[str, List[str]]


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


# ========== Keyword Management Endpoints (T210, FR-084) ==========

@router.get("/keywords")
async def get_agent_keywords(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current agent routing keywords (FR-084)

    Admin only access required
    """
    keywords = load_agent_keywords()

    return {
        "keywords": keywords,
        "available_agents": list(DEFAULT_KEYWORDS.keys())
    }


@router.put("/keywords/{agent_name}")
async def update_agent_keywords(
    agent_name: str,
    config: AgentKeywordConfig,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update keywords for specific agent (FR-084)

    Admin only access required
    Changes take effect within 5 seconds (in-memory cache)
    """
    if agent_name not in DEFAULT_KEYWORDS:
        raise HTTPException(
            status_code=404,
            detail=f"알 수 없는 에이전트입니다: {agent_name}"
        )

    # Load current keywords
    all_keywords = load_agent_keywords()

    # Update specific agent
    all_keywords[agent_name] = config.keywords

    # Save
    save_agent_keywords(all_keywords)

    return {
        "message": f"'{agent_name}' 키워드가 업데이트되었습니다.",
        "keywords": config.keywords,
        "effect_time": "5초 이내 (메모리 캐시)"
    }


@router.post("/keywords/bulk")
async def bulk_update_keywords(
    update: AgentKeywordBulkUpdate,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Bulk update all agent keywords (FR-084)

    Admin only access required
    Changes take effect within 5 seconds
    """
    # Validate all agent names
    for agent_name in update.configs.keys():
        if agent_name not in DEFAULT_KEYWORDS:
            raise HTTPException(
                status_code=400,
                detail=f"알 수 없는 에이전트입니다: {agent_name}"
            )

    # Save all configs
    save_agent_keywords(update.configs)

    return {
        "message": "모든 에이전트 키워드가 업데이트되었습니다.",
        "updated_agents": list(update.configs.keys()),
        "effect_time": "5초 이내 (메모리 캐시)"
    }


@router.post("/keywords/reset")
async def reset_keywords_to_default(
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Reset all keywords to default values (FR-084)

    Admin only access required
    """
    save_agent_keywords(DEFAULT_KEYWORDS)

    return {
        "message": "모든 키워드가 기본값으로 초기화되었습니다.",
        "keywords": DEFAULT_KEYWORDS
    }


@router.get("/test-routing")
async def test_agent_routing(
    query: str,
    current_admin: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Test which agent would be selected for a query (FR-084)

    Admin only - for testing keyword configuration
    """
    keywords = load_agent_keywords()

    # Simple keyword matching (same logic as orchestrator)
    query_lower = query.lower()
    matched_agents = []

    for agent_name, agent_keywords in keywords.items():
        for keyword in agent_keywords:
            if keyword in query_lower:
                matched_agents.append({
                    "agent": agent_name,
                    "matched_keyword": keyword
                })
                break

    if not matched_agents:
        selected_agent = "general_agent"
        reason = "키워드 매칭 없음 (기본값)"
    else:
        # First match wins (can be customized)
        selected_agent = matched_agents[0]["agent"]
        reason = f"키워드 '{matched_agents[0]['matched_keyword']}' 매칭"

    return {
        "query": query,
        "selected_agent": selected_agent,
        "reason": reason,
        "all_matches": matched_agents
    }
