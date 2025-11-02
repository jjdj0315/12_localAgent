"""Authentication schemas (T231: Enhanced validation)"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field, field_validator
from app.core.validators import InputValidator


class LoginRequest(BaseModel):
    """Login request schema with enhanced validation (T231)"""
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=8)

    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format (T231)"""
        return InputValidator.validate_username(v)

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password format (T231)"""
        return InputValidator.validate_password(v)


class LoginResponse(BaseModel):
    """Login response schema"""
    user_id: UUID
    username: str
    is_admin: bool
    session_token: str
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
