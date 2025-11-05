"""
Tool Management Admin Endpoints

Per FR-067: Enable/disable tools, view tool list
Per FR-069: Tool usage statistics (per-tool usage, avg time, error rate)
"""
from typing import Optional
from uuid import UUID
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_admin
from app.core.database import get_db
from app.models.tool import Tool
from app.models.tool_execution import ToolExecution
from app.models.admin import Admin
from app.schemas.tool import (
    ToolResponse,
    ToolListResponse,
    ToolUpdate,
    ToolStatistics,
    ToolStatisticsResponse,
    BulkToolUpdate
)

router = APIRouter()


@router.get("/list", response_model=ToolListResponse)
async def list_tools(
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List all tools with optional filters

    Args:
        category: Filter by tool category
        is_active: Filter by active status
    """
    query = select(Tool)

    if category:
        query = query.where(Tool.category == category)
    if is_active is not None:
        query = query.where(Tool.is_active == is_active)

    query = query.order_by(Tool.priority.desc(), Tool.name)

    result = await db.execute(query)
    tools = result.scalars().all()

    return ToolListResponse(
        tools=[ToolResponse.from_orm(tool) for tool in tools],
        total=len(tools)
    )


@router.get("/{tool_id}", response_model=ToolResponse)
async def get_tool(
    tool_id: UUID,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get tool by ID"""
    result = await db.execute(select(Tool).where(Tool.id == tool_id))
    tool = result.scalar_one_or_none()

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="도구를 찾을 수 없습니다."
        )

    return ToolResponse.from_orm(tool)


@router.put("/{tool_id}", response_model=ToolResponse)
async def update_tool(
    tool_id: UUID,
    update_data: ToolUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update tool configuration

    Admins can:
    - Enable/disable tools (FR-067)
    - Update display name, description
    - Modify parameters, timeout, priority
    """
    result = await db.execute(select(Tool).where(Tool.id == tool_id))
    tool = result.scalar_one_or_none()

    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="도구를 찾을 수 없습니다."
        )

    # Update fields
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(tool, field, value)

    await db.commit()
    await db.refresh(tool)

    return ToolResponse.from_orm(tool)


@router.post("/bulk-update")
async def bulk_update_tools(
    bulk_update: BulkToolUpdate,
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Bulk update tools

    Args:
        bulk_update: Tool IDs and fields to update
    """
    result = await db.execute(
        select(Tool).where(Tool.id.in_(bulk_update.tool_ids))
    )
    tools = result.scalars().all()

    if not tools:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="도구를 찾을 수 없습니다."
        )

    # Update fields
    for tool in tools:
        if bulk_update.is_active is not None:
            tool.is_active = bulk_update.is_active
        if bulk_update.priority is not None:
            tool.priority = bulk_update.priority

    await db.commit()

    return {"success": True, "updated_count": len(tools)}


@router.get("/stats/overview", response_model=ToolStatisticsResponse)
async def get_tool_statistics(
    days: int = Query(default=7, ge=1, le=90),
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get tool usage statistics

    Per FR-069: Per-tool usage, avg time, error rate

    Args:
        days: Number of days to analyze (default: 7)
    """
    # Calculate time threshold
    time_threshold = datetime.utcnow() - timedelta(days=days)

    # Get all tools
    tools_result = await db.execute(select(Tool))
    tools = tools_result.scalars().all()

    statistics = []

    for tool in tools:
        # Get executions in time period
        executions_result = await db.execute(
            select(ToolExecution)
            .where(
                ToolExecution.tool_id == tool.id,
                ToolExecution.created_at >= time_threshold
            )
        )
        executions = executions_result.scalars().all()

        # Calculate statistics
        total_count = len(executions)
        success_count = sum(1 for e in executions if e.success)
        error_count = total_count - success_count

        success_rate = (success_count / total_count * 100) if total_count > 0 else 0.0

        avg_time = (
            sum(e.execution_time_ms for e in executions) / total_count
            if total_count > 0
            else 0
        )

        last_used = max((e.created_at for e in executions), default=None)

        statistics.append(
            ToolStatistics(
                tool_id=tool.id,
                tool_name=tool.name,
                display_name=tool.display_name,
                category=tool.category,
                is_active=tool.is_active,
                usage_count=total_count,
                success_count=success_count,
                error_count=error_count,
                success_rate=success_rate,
                avg_execution_time_ms=int(avg_time),
                last_used_at=last_used
            )
        )

    # Calculate overall statistics
    total_executions = sum(s.usage_count for s in statistics)
    overall_success = sum(s.success_count for s in statistics)
    overall_success_rate = (
        (overall_success / total_executions * 100) if total_executions > 0 else 0.0
    )

    # Sort by usage count
    statistics.sort(key=lambda s: s.usage_count, reverse=True)

    return ToolStatisticsResponse(
        statistics=statistics,
        total_executions=total_executions,
        total_tools=len(tools),
        overall_success_rate=overall_success_rate,
        time_period_days=days
    )


@router.get("/executions/recent")
async def get_recent_executions(
    tool_id: Optional[UUID] = None,
    limit: int = Query(default=50, ge=1, le=200),
    current_admin: Admin = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get recent tool executions for debugging

    Args:
        tool_id: Filter by tool ID (optional)
        limit: Number of executions to return
    """
    query = select(ToolExecution).order_by(ToolExecution.created_at.desc()).limit(limit)

    if tool_id:
        query = query.where(ToolExecution.tool_id == tool_id)

    result = await db.execute(query)
    executions = result.scalars().all()

    return {
        "executions": [
            {
                "id": str(e.id),
                "tool_id": str(e.tool_id),
                "user_id": str(e.user_id),
                "success": e.success,
                "execution_time_ms": e.execution_time_ms,
                "created_at": e.created_at.isoformat(),
                "error_message": e.error_message if not e.success else None,
            }
            for e in executions
        ],
        "total": len(executions)
    }
