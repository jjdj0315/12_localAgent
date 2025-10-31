"""
Audit Log model (T206)
"""

from sqlalchemy import Column, String, DateTime, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from app.core.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    action_type = Column(String(50), nullable=False, index=True)  # filter, tool, agent
    action_name = Column(String(100), nullable=False)  # specific action
    
    # Sanitized parameters (no PII, no message content)
    parameters = Column(JSON, nullable=True)
    
    result = Column(String(20), nullable=False)  # success, failure
    execution_time_ms = Column(Integer, nullable=True)
    error_message = Column(String(500), nullable=True)
    
    # Context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(500), nullable=True)
