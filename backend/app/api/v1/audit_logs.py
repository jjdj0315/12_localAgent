"""
Audit log endpoints (T208)
Admin-only access
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel
import uuid

from app.core.database import get_db
from app.services.audit_log_service import AuditLogService

router = APIRouter()


class AuditLogResponse(BaseModel):
    id: uuid.UUID
    timestamp: datetime
    user_id: Optional[uuid.UUID]
    action_type: str
    action_name: str
    parameters: Optional[dict]
    result: str
    execution_time_ms: Optional[int]
    error_message: Optional[str]
    
    class Config:
        from_attributes = True


@router.get("/audit-logs", response_model=List[AuditLogResponse])
async def get_audit_logs(
    user_id: Optional[str] = Query(None),
    action_type: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    limit: int = Query(100, le=500),
    db: AsyncSession = Depends(get_db)
):
    """
    Get audit logs with filters
    
    Admin only access required
    """
    user_uuid = uuid.UUID(user_id) if user_id else None
    
    logs = await AuditLogService.query_logs(
        db=db,
        user_id=user_uuid,
        action_type=action_type,
        start_date=start_date,
        end_date=end_date,
        limit=limit
    )
    
    return logs


@router.get("/audit-logs/stats")
async def get_audit_stats(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get audit log statistics
    
    Returns:
    - Total events by type
    - Success/failure rates
    - Average execution times
    """
    from sqlalchemy import select, func
    from app.models.audit_log import AuditLog
    
    # Count by action type
    query = select(
        AuditLog.action_type,
        func.count(AuditLog.id).label("count"),
        func.avg(AuditLog.execution_time_ms).label("avg_time")
    ).group_by(AuditLog.action_type)
    
    if start_date:
        query = query.where(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.where(AuditLog.timestamp <= end_date)
    
    result = await db.execute(query)
    stats = result.all()
    
    return {
        "stats": [
            {
                "action_type": stat.action_type,
                "count": stat.count,
                "avg_execution_time_ms": round(stat.avg_time, 2) if stat.avg_time else None
            }
            for stat in stats
        ]
    }
