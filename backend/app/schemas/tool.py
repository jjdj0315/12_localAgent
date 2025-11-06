"""
Tool Schemas

Pydantic schemas for Tool and ToolExecution models.
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, Dict, Any, List
from datetime import datetime
from uuid import UUID


# =====================
# Tool Schemas
# =====================

class ToolBase(BaseModel):
    """Base tool schema"""
    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1)
    category: str
    is_active: bool = True
    parameter_schema: Dict[str, Any]
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    max_retries: int = Field(default=0, ge=0, le=3)
    priority: int = Field(default=0, ge=0, le=100)


class ToolCreate(ToolBase):
    """Schema for creating a new tool"""
    pass


class ToolUpdate(BaseModel):
    """Schema for updating a tool"""
    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1)
    is_active: Optional[bool] = None
    parameter_schema: Optional[Dict[str, Any]] = None
    timeout_seconds: Optional[int] = Field(None, ge=1, le=300)
    max_retries: Optional[int] = Field(None, ge=0, le=3)
    priority: Optional[int] = Field(None, ge=0, le=100)


class ToolResponse(ToolBase):
    """Schema for tool in API responses"""
    id: UUID
    is_system_tool: bool
    usage_count: int
    success_count: int
    error_count: int
    avg_execution_time_ms: int
    success_rate: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ToolListResponse(BaseModel):
    """Schema for list of tools"""
    tools: List[ToolResponse]
    total: int


# =====================
# Tool Execution Schemas
# =====================

class ToolExecutionBase(BaseModel):
    """Base tool execution schema"""
    tool_id: UUID
    parameters: Dict[str, Any]


class ToolExecutionCreate(ToolExecutionBase):
    """Schema for creating a tool execution log"""
    user_id: UUID
    conversation_id: Optional[UUID] = None
    agent_iteration: Optional[int] = None
    thought: Optional[str] = None
    success: bool
    result: Optional[str] = None
    error_message: Optional[str] = None
    execution_time_ms: int
    timeout_occurred: bool = False
    retry_count: int = 0


class ToolExecutionResponse(BaseModel):
    """Schema for tool execution in API responses"""
    id: UUID
    tool_id: UUID
    user_id: UUID
    conversation_id: Optional[UUID]
    success: bool
    execution_time_ms: int
    created_at: datetime

    class Config:
        from_attributes = True


class ToolExecutionDetailResponse(ToolExecutionResponse):
    """Schema for detailed tool execution"""
    agent_iteration: Optional[int]
    thought: Optional[str]
    parameters: Dict[str, Any]
    result: Optional[str]
    error_message: Optional[str]
    timeout_occurred: bool
    retry_count: int

    class Config:
        from_attributes = True


class ToolExecutionListResponse(BaseModel):
    """Schema for list of tool executions"""
    executions: List[ToolExecutionResponse]
    total: int


# =====================
# Tool Invocation Schemas (for ReAct agent)
# =====================

class ToolInvocationRequest(BaseModel):
    """Request to invoke a tool"""
    tool_name: str
    parameters: Dict[str, Any]
    conversation_id: Optional[UUID] = None
    agent_iteration: Optional[int] = None
    thought: Optional[str] = None


class ToolInvocationResponse(BaseModel):
    """Response from tool invocation"""
    success: bool
    result: Optional[str] = None
    error_message: Optional[str] = None
    execution_time_ms: int
    tool_name: str


# =====================
# Tool Statistics Schemas
# =====================

class ToolStatistics(BaseModel):
    """Statistics for a single tool"""
    tool_id: UUID
    tool_name: str
    display_name: str
    category: str
    is_active: bool
    usage_count: int
    success_count: int
    error_count: int
    success_rate: float
    avg_execution_time_ms: int
    last_used_at: Optional[datetime]


class ToolStatisticsResponse(BaseModel):
    """Response for tool statistics endpoint"""
    statistics: List[ToolStatistics]
    total_executions: int
    total_tools: int
    overall_success_rate: float
    time_period_days: int


class ToolUsageTrend(BaseModel):
    """Tool usage trend over time"""
    date: str  # YYYY-MM-DD
    usage_count: int
    success_count: int
    error_count: int
    avg_execution_time_ms: int


class ToolUsageTrendResponse(BaseModel):
    """Response for tool usage trends"""
    tool_id: UUID
    tool_name: str
    trends: List[ToolUsageTrend]
    period_days: int


# =====================
# ReAct Display Schemas
# =====================

class ReActStep(BaseModel):
    """A single step in the ReAct loop"""
    iteration: int
    thought: str
    action: Optional[str] = None  # Tool name
    action_input: Optional[Dict[str, Any]] = None  # Tool parameters
    observation: Optional[str] = None  # Tool result or error
    timestamp: datetime


class ReActResponse(BaseModel):
    """Complete ReAct execution result"""
    steps: List[ReActStep]
    final_answer: str
    total_iterations: int
    success: bool
    tools_used: List[str]
    total_execution_time_ms: int


# =====================
# Validators
# =====================

class ToolExecutionFilter(BaseModel):
    """Filters for querying tool executions"""
    tool_id: Optional[UUID] = None
    user_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None
    success: Optional[bool] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class ToolFilter(BaseModel):
    """Filters for querying tools"""
    category: Optional[str] = None
    is_active: Optional[bool] = None
    search: Optional[str] = None  # Search in name or description


# =====================
# Admin Configuration Schemas
# =====================

class ToolConfigUpdate(BaseModel):
    """Update tool configuration"""
    timeout_seconds: Optional[int] = Field(None, ge=1, le=300)
    max_retries: Optional[int] = Field(None, ge=0, le=3)
    priority: Optional[int] = Field(None, ge=0, le=100)


class BulkToolUpdate(BaseModel):
    """Bulk update tools"""
    tool_ids: List[UUID]
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0, le=100)
