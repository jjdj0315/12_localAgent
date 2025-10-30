"""AgentWorkflowStep model for individual agent executions within workflows"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, JSON, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def get_current_utc():
    """Get current UTC time with timezone"""
    return datetime.now(timezone.utc)


class AgentWorkflowStep(Base):
    """
    AgentWorkflowStep model tracks individual agent execution within workflows

    Per FR-072: Sequential workflows with context sharing
    Per FR-074: Agent attribution in responses
    Per FR-075: Detailed execution logging
    Per FR-078: Parallel execution support
    """

    __tablename__ = "agent_workflow_steps"

    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)

    # Relationships
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("agent_workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_id = Column(UUID(as_uuid=True), ForeignKey("agents.id", ondelete="CASCADE"), nullable=False, index=True)

    # Step metadata
    step_order = Column(Integer, nullable=False)  # 0-indexed order in workflow
    execution_mode = Column(String(50), nullable=False, default="sequential")  # sequential, parallel

    # Input/Output
    input_query = Column(Text, nullable=False)  # Query sent to this agent
    input_context = Column(JSON, nullable=True)  # Context from previous agents (FR-072)
    agent_response = Column(Text, nullable=True)  # Agent's response
    output_context = Column(JSON, nullable=True)  # Context passed to next agents

    # Execution tracking
    status = Column(String(50), nullable=False, default="pending")  # pending, running, completed, failed
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    execution_time_ms = Column(Integer, nullable=True)

    # LoRA adapter info (FR-071A)
    lora_adapter_used = Column(String(500), nullable=True)
    lora_loading_time_ms = Column(Integer, nullable=True)

    # Error handling
    success = Column(Boolean, nullable=False, default=False)
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)

    # Performance metrics
    token_count = Column(Integer, nullable=True)
    temperature = Column(Integer, nullable=True)  # Temperature * 100

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=get_current_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_current_utc, onupdate=get_current_utc, nullable=False)

    # Relationships
    workflow = relationship("AgentWorkflow", back_populates="steps")
    agent = relationship("Agent", back_populates="workflow_steps")

    def __repr__(self) -> str:
        return f"<AgentWorkflowStep workflow={self.workflow_id} agent={self.agent_id} order={self.step_order}>"

    def start_execution(self):
        """Mark step as started"""
        self.status = "running"
        self.started_at = get_current_utc()

    def complete_execution(self, response: str, output_context: dict = None):
        """Mark step as completed successfully"""
        self.status = "completed"
        self.completed_at = get_current_utc()
        self.agent_response = response
        self.success = True

        if output_context:
            self.output_context = output_context

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.execution_time_ms = int(delta.total_seconds() * 1000)

    def fail_execution(self, error_message: str):
        """Mark step as failed"""
        self.status = "failed"
        self.completed_at = get_current_utc()
        self.error_message = error_message
        self.success = False

        if self.started_at:
            delta = self.completed_at - self.started_at
            self.execution_time_ms = int(delta.total_seconds() * 1000)

    def set_lora_info(self, adapter_path: str, loading_time_ms: int):
        """Record LoRA adapter usage"""
        self.lora_adapter_used = adapter_path
        self.lora_loading_time_ms = loading_time_ms

    @property
    def temperature_float(self) -> float:
        """Get temperature as float (0.0 - 1.0)"""
        if self.temperature is None:
            return 0.7  # Default
        return self.temperature / 100.0
