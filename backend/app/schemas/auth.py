"""Authentication schemas"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Login request schema"""
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)


class LoginResponse(BaseModel):
    """Login response schema"""
    user_id: UUID
    username: str
    is_admin: bool
    message: str = "Login successful"


class UserProfile(BaseModel):
    """User profile schema"""
    id: UUID
    username: str
    is_admin: bool
    created_at: datetime
    last_login_at: Optional[datetime] = None

    class Config:
        from_attributes = True
