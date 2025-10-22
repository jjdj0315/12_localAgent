"""
Admin Pydantic schemas for user management and system monitoring.
"""
from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class UserCreate(BaseModel):
    """Schema for creating a new user account."""

    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="Initial password")
    is_admin: bool = Field(False, description="Administrator privileges")


class UserResponse(BaseModel):
    """Schema for user information response."""

    id: UUID
    username: str
    is_admin: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Schema for paginated user list response."""

    users: list[UserResponse]
    total: int
    page: int
    page_size: int


class PasswordResetResponse(BaseModel):
    """Schema for password reset response."""

    username: str
    temporary_password: str
    message: str


class StatsResponse(BaseModel):
    """Schema for usage statistics response."""

    active_users_today: int
    active_users_week: int
    active_users_month: int
    total_queries_today: int
    total_queries_week: int
    total_queries_month: int
    avg_response_time_today: float  # milliseconds
    avg_response_time_week: float
    avg_response_time_month: float


class SystemHealthResponse(BaseModel):
    """Schema for system health metrics response."""

    server_uptime_seconds: int
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    available_storage_gb: float
    total_storage_gb: float
    llm_service_status: str  # "healthy", "degraded", "unavailable"
    database_status: str  # "healthy", "degraded", "unavailable"
    gpu_usage_percent: Optional[float] = None
    gpu_memory_usage_percent: Optional[float] = None


class StorageUsageResponse(BaseModel):
    """Schema for storage usage by user."""

    user_id: UUID
    username: str
    total_storage_bytes: int
    document_count: int
    conversation_count: int


class StorageStatsResponse(BaseModel):
    """Schema for overall storage statistics."""

    total_storage_used_bytes: int
    total_storage_available_bytes: int
    usage_percent: float
    user_storage: list[StorageUsageResponse]
    warning_threshold_exceeded: bool  # True if > 80%
    critical_threshold_exceeded: bool  # True if > 95%
