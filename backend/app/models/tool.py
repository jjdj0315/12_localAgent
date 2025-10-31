"""
Tool Model

Represents a ReAct tool that the AI agent can use to perform actions.
Tools include: document search, calculator, date/schedule, data analysis,
document templates, and legal reference.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from app.core.database import Base


class ToolCategory(str, enum.Enum):
    """Tool categories"""
    DOCUMENT_SEARCH = "document_search"
    CALCULATOR = "calculator"
    DATE_SCHEDULE = "date_schedule"
    DATA_ANALYSIS = "data_analysis"
    DOCUMENT_TEMPLATE = "document_template"
    LEGAL_REFERENCE = "legal_reference"


class Tool(Base):
    """
    Tool model for ReAct agent

    Represents a tool that can be used by the AI agent to perform specific actions.
    Tools are managed by administrators and can be enabled/disabled.
    """
    __tablename__ = "tools"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Basic information
    name = Column(String(100), nullable=False, unique=True, index=True)
    display_name = Column(String(200), nullable=False)  # Korean display name
    description = Column(Text, nullable=False)  # Tool description in Korean
    category = Column(String(50), nullable=False, index=True)

    # Tool configuration
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_system_tool = Column(Boolean, default=True, nullable=False)  # System tools cannot be deleted

    # Tool parameters schema (JSON)
    parameter_schema = Column(JSON, nullable=False)
    """
    Example:
    {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "검색 쿼리"
            }
        },
        "required": ["query"]
    }
    """

    # Tool settings
    timeout_seconds = Column(Integer, default=30, nullable=False)  # Execution timeout
    max_retries = Column(Integer, default=0, nullable=False)  # Number of retries on failure

    # Usage statistics
    usage_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    avg_execution_time_ms = Column(Integer, default=0, nullable=False)

    # Priority (higher values execute first if multiple tools selected)
    priority = Column(Integer, default=0, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    executions = relationship("ToolExecution", back_populates="tool", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Tool {self.name} (active={self.is_active})>"

    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "name": self.name,
            "display_name": self.display_name,
            "description": self.description,
            "category": self.category,
            "is_active": self.is_active,
            "is_system_tool": self.is_system_tool,
            "parameter_schema": self.parameter_schema,
            "timeout_seconds": self.timeout_seconds,
            "usage_count": self.usage_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "avg_execution_time_ms": self.avg_execution_time_ms,
            "success_rate": self.get_success_rate(),
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    def get_success_rate(self) -> float:
        """Calculate success rate"""
        if self.usage_count == 0:
            return 0.0
        return (self.success_count / self.usage_count) * 100

    def increment_usage(self, success: bool, execution_time_ms: int):
        """Update usage statistics"""
        self.usage_count += 1
        if success:
            self.success_count += 1
        else:
            self.error_count += 1

        # Update average execution time (rolling average)
        if self.avg_execution_time_ms == 0:
            self.avg_execution_time_ms = execution_time_ms
        else:
            # Exponential moving average (alpha = 0.2)
            self.avg_execution_time_ms = int(
                0.8 * self.avg_execution_time_ms + 0.2 * execution_time_ms
            )
