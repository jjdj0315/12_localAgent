"""
Admin API endpoints for user management and system monitoring.
"""
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin, get_db
from app.models.user import User
from app.schemas.admin import (
    PasswordResetResponse,
    StatsResponse,
    StorageStatsResponse,
    SystemHealthResponse,
    UserCreate,
    UserListResponse,
    UserResponse,
)
from app.services.admin_service import admin_service

router = APIRouter()


# User Management Endpoints

@router.get("/users", response_model=UserListResponse)
async def list_users(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List all users with pagination.

    Requires administrator privileges.

    - **page**: Page number (1-indexed)
    - **page_size**: Items per page (1-100)
    """
    users, total = await admin_service.list_users(
        db=db,
        page=page,
        page_size=page_size,
    )

    user_responses = [
        UserResponse(
            id=user.id,
            username=user.username,
            is_admin=user.is_admin,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        )
        for user in users
    ]

    return UserListResponse(
        users=user_responses,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new user account.

    Requires administrator privileges.

    - **username**: Unique username (3-50 characters)
    - **password**: Initial password (minimum 8 characters)
    - **is_admin**: Administrator privileges (default: false)
    """
    try:
        new_user = await admin_service.create_user(
            db=db,
            username=user.username,
            password=user.password,
            is_admin=user.is_admin,
        )

        return UserResponse(
            id=new_user.id,
            username=new_user.username,
            is_admin=new_user.is_admin,
            created_at=new_user.created_at,
            last_login_at=new_user.last_login_at,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a user account and all associated data.

    Requires administrator privileges.

    - **user_id**: UUID of the user to delete
    """
    # Prevent admin from deleting themselves
    if user_id == current_admin.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account",
        )

    deleted = await admin_service.delete_user(db=db, user_id=user_id)

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return None


@router.post("/users/{user_id}/reset-password", response_model=PasswordResetResponse)
async def reset_password(
    user_id: UUID,
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Reset user password and generate temporary password.

    Requires administrator privileges.

    - **user_id**: UUID of the user
    """
    user, temp_password = await admin_service.reset_password(db=db, user_id=user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return PasswordResetResponse(
        username=user.username,
        temporary_password=temp_password,
        message=f"Password for user '{user.username}' has been reset successfully.",
    )


# Statistics and Monitoring Endpoints

@router.get("/stats", response_model=StatsResponse)
async def get_usage_stats(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get usage statistics for the system.

    Requires administrator privileges.

    Returns:
    - Active users (today, week, month)
    - Total queries processed (today, week, month)
    - Average response times (today, week, month)
    """
    stats = await admin_service.get_usage_stats(db=db)

    return StatsResponse(**stats)


@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get system health metrics.

    Requires administrator privileges.

    Returns:
    - Server uptime
    - CPU, memory, disk usage
    - LLM service status
    - Database status
    - GPU metrics (if available)
    """
    # TODO: Implement system health monitoring
    # This will be implemented in Phase 7 (User Story 5)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="System health monitoring not yet implemented",
    )


@router.get("/storage", response_model=StorageStatsResponse)
async def get_storage_stats(
    current_admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get storage usage statistics.

    Requires administrator privileges.

    Returns:
    - Total storage used/available
    - Per-user storage breakdown
    - Warning/critical threshold status
    """
    # TODO: Implement storage statistics
    # This will be implemented in Phase 7 (User Story 5)
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Storage statistics not yet implemented",
    )
