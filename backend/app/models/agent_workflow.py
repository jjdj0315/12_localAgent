"""AgentWorkflow model for tracking multi-agent execution workflows"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def get_current_utc():
    """Get current UTC time with timezone"""
    return datetime.now(timezone.utc)


class AgentWorkflow(Base):
    """
    AgentWorkflow model tracks multi-agent system executions

    Per FR-070: Orchestrator routes queries to single/sequential/parallel workflows
    Per FR-075: Logs execution history for auditing
    Per FR-072: Sequential workflows with context sharing
    Per FR-078: Parallel workflows (max 3 agents)
    """

    __tablename__ = "agent_workflows"

    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Ownership
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False, index=True)

    # Workflow metadata
    workflow_type = Column(String(50), nullable=False)  # single, sequential, parallel
    query = Column(Text, nullable=False)  # Original user query
    intent = Column(String(100), nullable=True)  # Classified intent from orchestrator

    # Execution tracking
    status = Column(String(50), nullable=False, default="pending")  # pending, running, completed, failed
    total_steps = Column(Integer, nullable=False, default=0)  # Number of agent steps in workflow
    completed_steps = Column(Integer, nullable=False, default=0)

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    total_execution_time_ms = Column(Integer, nullable=True)

    # Results
    final_response = Column(Text, nullable=True)  # Aggregated response from all agents
    execution_log = Column(JSON, nullable=True)  # List of execution events per FR-075

    # Error handling
    error_message = Column(Text, nullable=True)
    failed_step_index = Column(Integer, nullable=True)  # Which step failed

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=get_current_utc, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=get_current_utc, onupdate=get_current_utc, nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])
    conversation = relationship("Conversation", foreign_keys=[conversation_id])
    steps = relationship("AgentWorkflowStep", back_populates="workflow", cascade="all, delete-orphan", order_by="AgentWorkflowStep.step_order")

    def __repr__(self) -> str:
        return f"<AgentWorkflow {self.id} type={self.workflow_type} status={self.status}>"

    @property
    def is_completed(self) -> bool:
        """Check if workflow is completed (success or failure)"""
        return self.status in ("completed", "failed")

    @property
    def success(self) -> bool:
        """Check if workflow completed successfully"""
        return self.status == "completed" and self.error_message is None

    def start_execution(self):
        """Mark workflow as started"""
        self.status = "running"
        self.started_at = get_current_utc()

    def complete_execution(self, final_response: str):
        """Mark workflow as completed successfully"""
        self.status = "completed"
        self.completed_at = get_current_utc()
        self.final_response = final_response

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.total_execution_time_ms = int(delta.total_seconds() * 1000)

    def fail_execution(self, error_message: str, failed_step_index: int = None):
        """Mark workflow as failed"""
        self.status = "failed"
        self.completed_at = get_current_utc()
        self.error_message = error_message
        self.failed_step_index = failed_step_index

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.total_execution_time_ms = int(delta.total_seconds() * 1000)

    def increment_completed_steps(self):
        """Increment completed steps counter"""
        self.completed_steps += 1
