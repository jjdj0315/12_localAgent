"""
Tool Execution Model

Represents a single execution of a tool by the ReAct agent.
Logs tool invocations for audit trail and debugging.
"""
from sqlalchemy import Column, String, Boolean, DateTime, Text, JSON, Integer, Float, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.core.database import Base


class ToolExecution(Base):
    """
    Tool execution log

    Records each tool execution for audit trail, debugging, and analytics.
    Per FR-066: Logs timestamp, user_id, tool_name, sanitized params, result.
    Does NOT store sensitive user data.
    """
    __tablename__ = "tool_executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # References
    tool_id = Column(UUID(as_uuid=True), ForeignKey("tools.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True, index=True)

    # Execution context
    agent_iteration = Column(Integer, nullable=True)  # Which ReAct iteration (1-5)
    thought = Column(Text, nullable=True)  # Agent's thought before executing tool

    # Input parameters (sanitized - no PII)
    parameters = Column(JSON, nullable=False)
    """
    Sanitized input parameters. PII should be masked or removed.
    Example: {"query": "예산 계산", "amount": 1000000}
    """

    # Execution results
    success = Column(Boolean, nullable=False, index=True)
    result = Column(Text, nullable=True)  # Tool result (truncated if too long)
    error_message = Column(Text, nullable=True)  # Error message if failed

    # Performance metrics
    execution_time_ms = Column(Integer, nullable=False)
    timeout_occurred = Column(Boolean, default=False, nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

    # Relationships
    tool = relationship("Tool", back_populates="executions")
    user = relationship("User")
    conversation = relationship("Conversation")

    def __repr__(self):
        return f"<ToolExecution {self.tool_id} success={self.success} time={self.execution_time_ms}ms>"

    def to_dict(self, include_details=False):
        """Convert to dictionary for API responses"""
        base_dict = {
            "id": str(self.id),
            "tool_id": str(self.tool_id),
            "user_id": str(self.user_id),
            "conversation_id": str(self.conversation_id) if self.conversation_id else None,
            "success": self.success,
            "execution_time_ms": self.execution_time_ms,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

        if include_details:
            base_dict.update({
                "agent_iteration": self.agent_iteration,
                "thought": self.thought,
                "parameters": self.parameters,
                "result": self.result[:500] if self.result else None,  # Truncate for API
                "error_message": self.error_message,
                "timeout_occurred": self.timeout_occurred,
                "retry_count": self.retry_count,
            })

        return base_dict

    @staticmethod
    def sanitize_parameters(params: dict) -> dict:
        """
        Sanitize parameters to remove or mask PII before logging

        Args:
            params: Raw input parameters

        Returns:
            Sanitized parameters safe for logging
        """
        import re

        sanitized = params.copy()

        # Patterns to detect and mask
        pii_patterns = {
            "korean_id": r'\b\d{6}[-\s]?\d{7}\b',
            "phone": r'\b0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}\b',
            "email": r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        }

        def mask_value(value):
            """Mask PII in a string value"""
            if not isinstance(value, str):
                return value

            masked = value
            for pattern_name, pattern in pii_patterns.items():
                masked = re.sub(pattern, f"[{pattern_name}_masked]", masked)
            return masked

        # Recursively sanitize all string values
        def sanitize_recursive(obj):
            if isinstance(obj, dict):
                return {k: sanitize_recursive(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [sanitize_recursive(item) for item in obj]
            elif isinstance(obj, str):
                return mask_value(obj)
            else:
                return obj

        return sanitize_recursive(sanitized)
