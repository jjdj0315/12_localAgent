"""
Agent Pydantic schemas for Multi-Agent System
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================================
# Agent Schemas
# ============================================================================

class AgentBase(BaseModel):
    """Base schema for Agent"""
    name: str = Field(..., min_length=1, max_length=100, description="Agent identifier name")
    display_name: str = Field(..., min_length=1, max_length=200, description="Display name in Korean")
    description: str = Field(..., description="Agent purpose and capabilities")
    category: str = Field(..., description="Agent category: citizen_support, document_writing, legal_research, data_analysis, review")


class AgentCreate(AgentBase):
    """Schema for creating a new agent"""
    prompt_template_path: str = Field(..., description="Path to prompt template file")
    is_active: bool = Field(True, description="Whether agent is active")
    priority: int = Field(100, ge=0, le=1000, description="Routing priority (higher = preferred)")

    # LoRA configuration (FR-071A)
    lora_adapter_path: Optional[str] = Field(None, description="Path to LoRA adapter file (optional)")
    lora_adapter_enabled: bool = Field(False, description="Whether LoRA adapter is enabled")

    # Performance configuration
    max_tokens: int = Field(1024, ge=128, le=4096, description="Maximum tokens to generate")
    temperature: int = Field(70, ge=0, le=100, description="Temperature * 100 (e.g., 70 = 0.7)")
    timeout_seconds: int = Field(60, ge=10, le=300, description="Execution timeout in seconds")

    # Few-shot examples (FR-070)
    few_shot_examples: Optional[List[str]] = Field(None, description="Example queries for orchestrator routing")


class AgentUpdate(BaseModel):
    """Schema for updating agent configuration"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0, le=1000)

    lora_adapter_path: Optional[str] = None
    lora_adapter_enabled: Optional[bool] = None

    max_tokens: Optional[int] = Field(None, ge=128, le=4096)
    temperature: Optional[int] = Field(None, ge=0, le=100)
    timeout_seconds: Optional[int] = Field(None, ge=10, le=300)

    few_shot_examples: Optional[List[str]] = None


class AgentResponse(AgentBase):
    """Schema for agent response"""
    id: UUID
    prompt_template_path: str
    is_active: bool
    priority: int

    lora_adapter_path: Optional[str] = None
    lora_adapter_enabled: bool

    max_tokens: int
    temperature: int
    timeout_seconds: int

    few_shot_examples: Optional[List[str]] = None

    # Statistics
    usage_count: int
    success_count: int
    error_count: int
    avg_execution_time_ms: int
    success_rate: float

    # Timestamps
    created_at: datetime
    updated_at: datetime
    last_used_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AgentListResponse(BaseModel):
    """Schema for list of agents"""
    agents: List[AgentResponse]
    total: int


# ============================================================================
# AgentWorkflow Schemas
# ============================================================================

class AgentWorkflowBase(BaseModel):
    """Base schema for AgentWorkflow"""
    workflow_type: str = Field(..., description="Workflow type: single, sequential, parallel")
    query: str = Field(..., description="Original user query")


class AgentWorkflowCreate(AgentWorkflowBase):
    """Schema for creating a new workflow"""
    user_id: UUID
    conversation_id: UUID
    intent: Optional[str] = Field(None, description="Classified intent")


class AgentWorkflowResponse(AgentWorkflowBase):
    """Schema for workflow response"""
    id: UUID
    user_id: UUID
    conversation_id: UUID
    intent: Optional[str] = None

    status: str  # pending, running, completed, failed
    total_steps: int
    completed_steps: int

    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_execution_time_ms: Optional[int] = None

    final_response: Optional[str] = None
    execution_log: Optional[List[Dict[str, Any]]] = None

    error_message: Optional[str] = None
    failed_step_index: Optional[int] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentWorkflowListResponse(BaseModel):
    """Schema for list of workflows"""
    workflows: List[AgentWorkflowResponse]
    total: int


# ============================================================================
# AgentWorkflowStep Schemas
# ============================================================================

class AgentWorkflowStepBase(BaseModel):
    """Base schema for AgentWorkflowStep"""
    step_order: int = Field(..., ge=0, description="Step order in workflow (0-indexed)")
    execution_mode: str = Field("sequential", description="Execution mode: sequential, parallel")
    input_query: str = Field(..., description="Query sent to agent")


class AgentWorkflowStepCreate(AgentWorkflowStepBase):
    """Schema for creating a new workflow step"""
    workflow_id: UUID
    agent_id: UUID
    input_context: Optional[Dict[str, Any]] = Field(None, description="Context from previous agents")


class AgentWorkflowStepResponse(AgentWorkflowStepBase):
    """Schema for workflow step response"""
    id: UUID
    workflow_id: UUID
    agent_id: UUID

    input_context: Optional[Dict[str, Any]] = None
    agent_response: Optional[str] = None
    output_context: Optional[Dict[str, Any]] = None

    status: str  # pending, running, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: Optional[int] = None

    lora_adapter_used: Optional[str] = None
    lora_loading_time_ms: Optional[int] = None

    success: bool
    error_message: Optional[str] = None
    retry_count: int

    token_count: Optional[int] = None
    temperature: Optional[int] = None

    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AgentWorkflowStepListResponse(BaseModel):
    """Schema for list of workflow steps"""
    steps: List[AgentWorkflowStepResponse]
    total: int


# ============================================================================
# Agent Execution Schemas (for API requests)
# ============================================================================

class AgentExecutionRequest(BaseModel):
    """Schema for executing an agent directly"""
    agent_id: UUID
    query: str = Field(..., min_length=1, description="Query to send to agent")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    conversation_id: Optional[UUID] = Field(None, description="Associated conversation ID")


class AgentExecutionResponse(BaseModel):
    """Schema for agent execution response"""
    agent_id: UUID
    agent_name: str
    query: str
    response: str
    execution_time_ms: int
    success: bool
    error_message: Optional[str] = None

    lora_adapter_used: Optional[str] = None
    token_count: Optional[int] = None


# ============================================================================
# Multi-Agent Orchestration Schemas
# ============================================================================

class MultiAgentRequest(BaseModel):
    """Schema for multi-agent orchestration request"""
    query: str = Field(..., min_length=1, description="User query")
    conversation_id: UUID = Field(..., description="Conversation ID")
    force_workflow_type: Optional[str] = Field(None, description="Force specific workflow type (for testing)")


class MultiAgentResponse(BaseModel):
    """Schema for multi-agent orchestration response"""
    workflow_id: UUID
    workflow_type: str
    final_response: str
    agents_used: List[str]
    total_execution_time_ms: int
    success: bool

    # Step details
    steps: List[AgentWorkflowStepResponse]

    # Attribution (FR-074)
    agent_contributions: Dict[str, str]  # agent_name -> contribution


class AgentStatistics(BaseModel):
    """Schema for agent statistics"""
    agent_id: UUID
    agent_name: str
    display_name: str
    category: str
    is_active: bool

    usage_count: int
    success_count: int
    error_count: int
    success_rate: float
    avg_execution_time_ms: int

    last_used_at: Optional[datetime] = None


class AgentStatisticsResponse(BaseModel):
    """Schema for agent statistics overview"""
    statistics: List[AgentStatistics]
    total_agents: int
    total_executions: int
    overall_success_rate: float
    time_period_days: int
