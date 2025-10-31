"""
Audit logging service (T207, FR-083)

Logs:
- Safety filter events
- ReAct tool executions
- Multi-agent workflows
"""

from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime
from typing import Optional, Dict, Any
import uuid

from app.models.audit_log import AuditLog


class AuditLogService:
    """Service for creating audit logs"""
    
    @staticmethod
    async def log_filter_event(
        db: AsyncSession,
        user_id: uuid.UUID,
        filter_type: str,  # rule_based, ml_based, pii
        category: str,
        result: str,  # blocked, passed
        execution_time_ms: float = None,
        ip_address: str = None
    ) -> AuditLog:
        """
        Log safety filter event
        
        NOTE: Message content is NOT logged (FR-056)
        """
        audit_log = AuditLog(
            user_id=user_id,
            action_type="filter",
            action_name=filter_type,
            parameters={"category": category},
            result=result,
            execution_time_ms=int(execution_time_ms) if execution_time_ms else None,
            ip_address=ip_address
        )
        
        db.add(audit_log)
        await db.commit()
        return audit_log
    
    @staticmethod
    async def log_tool_execution(
        db: AsyncSession,
        user_id: uuid.UUID,
        tool_name: str,
        sanitized_params: Dict[str, Any],
        result: str,  # success, failure
        execution_time_ms: float = None,
        error_message: str = None,
        ip_address: str = None
    ) -> AuditLog:
        """
        Log ReAct tool execution
        
        Parameters are sanitized to remove PII (FR-066)
        """
        audit_log = AuditLog(
            user_id=user_id,
            action_type="tool",
            action_name=tool_name,
            parameters=sanitized_params,
            result=result,
            execution_time_ms=int(execution_time_ms) if execution_time_ms else None,
            error_message=error_message[:500] if error_message else None,
            ip_address=ip_address
        )
        
        db.add(audit_log)
        await db.commit()
        return audit_log
    
    @staticmethod
    async def log_agent_workflow(
        db: AsyncSession,
        user_id: uuid.UUID,
        workflow_type: str,  # single, sequential, parallel
        agents_used: list,
        result: str,
        execution_time_ms: float = None,
        error_message: str = None,
        ip_address: str = None
    ) -> AuditLog:
        """
        Log multi-agent workflow execution
        
        FR-075: Track agent invocations with sanitized summaries
        """
        audit_log = AuditLog(
            user_id=user_id,
            action_type="agent",
            action_name=workflow_type,
            parameters={
                "agents": agents_used,
                "agent_count": len(agents_used)
            },
            result=result,
            execution_time_ms=int(execution_time_ms) if execution_time_ms else None,
            error_message=error_message[:500] if error_message else None,
            ip_address=ip_address
        )
        
        db.add(audit_log)
        await db.commit()
        return audit_log
    
    @staticmethod
    async def query_logs(
        db: AsyncSession,
        user_id: Optional[uuid.UUID] = None,
        action_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list:
        """Query audit logs with filters"""
        from sqlalchemy import select
        
        query = select(AuditLog)
        
        if user_id:
            query = query.where(AuditLog.user_id == user_id)
        
        if action_type:
            query = query.where(AuditLog.action_type == action_type)
        
        if start_date:
            query = query.where(AuditLog.timestamp >= start_date)
        
        if end_date:
            query = query.where(AuditLog.timestamp <= end_date)
        
        query = query.order_by(AuditLog.timestamp.desc()).limit(limit)
        
        result = await db.execute(query)
        return result.scalars().all()


def sanitize_tool_params(params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove PII from tool parameters
    
    FR-066: Log sanitized parameters only
    """
    sanitized = {}
    
    for key, value in params.items():
        if isinstance(value, str):
            # Truncate long strings
            if len(value) > 200:
                sanitized[key] = value[:200] + "..."
            else:
                sanitized[key] = value
        elif isinstance(value, (int, float, bool)):
            sanitized[key] = value
        elif isinstance(value, list):
            sanitized[key] = f"[list with {len(value)} items]"
        elif isinstance(value, dict):
            sanitized[key] = f"[dict with {len(value)} keys]"
        else:
            sanitized[key] = str(type(value))
    
    return sanitized
