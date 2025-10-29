"""
Safety Filter Schemas

Pydantic schemas for safety filter API requests and responses.
"""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, validator
from uuid import UUID


# ============================================================================
# Safety Filter Rule Schemas
# ============================================================================

class SafetyFilterRuleBase(BaseModel):
    """Base schema for safety filter rules"""
    name: str = Field(..., min_length=1, max_length=100, description="Rule name")
    description: Optional[str] = Field(None, max_length=500, description="Rule description")
    category: str = Field(..., description="Filter category: violence, sexual, dangerous, hate, pii")
    keywords: List[str] = Field(default_factory=list, description="List of keywords to match")
    regex_patterns: List[str] = Field(default_factory=list, description="List of regex patterns")
    replacement_text: Optional[str] = Field(None, max_length=100, description="Text to replace matched content (for PII)")
    is_active: bool = Field(True, description="Whether rule is active")
    priority: int = Field(0, ge=0, le=100, description="Priority (0-100, higher = checked first)")

    @validator('category')
    def validate_category(cls, v):
        valid_categories = ['violence', 'sexual', 'dangerous', 'hate', 'pii']
        if v not in valid_categories:
            raise ValueError(f'Category must be one of: {valid_categories}')
        return v

    @validator('keywords')
    def validate_keywords(cls, v):
        if not v and not cls.regex_patterns:
            raise ValueError('At least one keyword or regex pattern is required')
        return v


class SafetyFilterRuleCreate(SafetyFilterRuleBase):
    """Schema for creating a new safety filter rule"""
    pass


class SafetyFilterRuleUpdate(BaseModel):
    """Schema for updating an existing safety filter rule"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    keywords: Optional[List[str]] = None
    regex_patterns: Optional[List[str]] = None
    replacement_text: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    priority: Optional[int] = Field(None, ge=0, le=100)


class SafetyFilterRuleResponse(SafetyFilterRuleBase):
    """Schema for safety filter rule responses"""
    id: UUID
    is_system_rule: bool
    match_count: int
    created_at: datetime
    updated_at: datetime
    created_by_admin_id: Optional[UUID]

    class Config:
        from_attributes = True


# ============================================================================
# Filter Event Schemas
# ============================================================================

class FilterEventBase(BaseModel):
    """Base schema for filter events"""
    category: str
    filter_type: str  # "rule_based" or "ml_based"
    filter_phase: str  # "input" or "output"
    action: str  # "blocked", "masked", "warned"


class FilterEventResponse(FilterEventBase):
    """Schema for filter event responses"""
    id: UUID
    user_id: UUID
    conversation_id: Optional[UUID]
    rule_id: Optional[UUID]
    rule_name: Optional[str]
    matched_keyword: Optional[str]
    confidence_score: Optional[float]
    bypass_attempted: bool
    bypass_succeeded: bool
    processing_time_ms: Optional[int]
    created_at: datetime
    message_length: Optional[int]

    class Config:
        from_attributes = True


# ============================================================================
# Filter Check Request/Response
# ============================================================================

class FilterCheckRequest(BaseModel):
    """Request schema for checking content against filters"""
    content: str = Field(..., min_length=1, description="Content to check")
    phase: str = Field("input", description="Filter phase: input or output")
    conversation_id: Optional[UUID] = Field(None, description="Associated conversation ID")
    bypass_rule_based: bool = Field(False, description="Bypass rule-based filter (retry scenario)")


class FilterCheckResponse(BaseModel):
    """Response schema for filter check results"""
    is_safe: bool = Field(..., description="Whether content passed filters")
    filtered_content: str = Field(..., description="Content after PII masking (if any)")
    categories: List[str] = Field(default_factory=list, description="Detected violation categories")
    confidence: Optional[float] = Field(None, description="ML filter confidence score")
    matched_patterns: List[str] = Field(default_factory=list, description="Matched keywords/patterns")
    processing_time_ms: int = Field(..., description="Total filter processing time")
    action_taken: str = Field(..., description="Action: pass, blocked, masked, warned")
    can_retry: bool = Field(False, description="Whether user can retry with bypass")
    safe_message: Optional[str] = Field(None, description="Safe replacement message if blocked")


# ============================================================================
# Filter Statistics Schemas
# ============================================================================

class FilterStatsByCategory(BaseModel):
    """Statistics grouped by category"""
    category: str
    total_count: int
    blocked_count: int
    masked_count: int
    warned_count: int


class FilterStatsResponse(BaseModel):
    """Response schema for filter statistics"""
    total_events: int
    events_today: int
    events_this_week: int
    by_category: List[FilterStatsByCategory]
    top_triggered_rules: List[dict]  # [{rule_id, rule_name, count}, ...]
    avg_processing_time_ms: float
    bypass_attempt_rate: float  # Percentage of events where bypass was attempted


# ============================================================================
# Filter Configuration Schemas
# ============================================================================

class FilterConfigUpdate(BaseModel):
    """Schema for updating global filter configuration"""
    enable_rule_based: Optional[bool] = Field(None, description="Enable/disable rule-based filter")
    enable_ml_based: Optional[bool] = Field(None, description="Enable/disable ML-based filter")
    ml_confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="ML confidence threshold")
    max_processing_time_ms: Optional[int] = Field(None, ge=100, le=10000, description="Max filter processing time")


class FilterConfigResponse(BaseModel):
    """Response schema for filter configuration"""
    enable_rule_based: bool
    enable_ml_based: bool
    ml_confidence_threshold: float
    max_processing_time_ms: int
    rule_count: int
    active_rule_count: int
    ml_model_loaded: bool
