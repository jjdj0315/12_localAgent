"""Agent model for Multi-Agent System"""

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def get_current_utc():
    """Get current UTC time with timezone"""
    return datetime.now(timezone.utc)


class Agent(Base):
    """
    Agent model for Multi-Agent System

    Per FR-071: Five specialized agents:
    - Citizen Support Agent (민원 지원 에이전트)
    - Document Writing Agent (문서 작성 에이전트)
    - Legal Research Agent (법규 검색 에이전트)
    - Data Analysis Agent (데이터 분석 에이전트)
    - Review Agent (검토 에이전트)

    Per FR-071A: Each agent can load optional LoRA adapter
    """

    __tablename__ = "agents"

    # Primary fields
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name = Column(String(100), unique=True, nullable=False, index=True)
    display_name = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)

    # Agent configuration
    category = Column(String(50), nullable=False)  # citizen_support, document_writing, legal_research, data_analysis, review
    prompt_template_path = Column(String(500), nullable=False)  # Path to prompt file in backend/prompts/
    is_active = Column(Boolean, default=True, nullable=False)
    priority = Column(Integer, default=100, nullable=False)  # Higher priority = selected first in routing

    # LoRA adapter configuration (FR-071A)
    lora_adapter_path = Column(String(500), nullable=True)  # Path to LoRA adapter (optional)
    lora_adapter_enabled = Column(Boolean, default=False, nullable=False)

    # Performance configuration
    max_tokens = Column(Integer, default=1024, nullable=False)
    temperature = Column(Integer, default=70, nullable=False)  # Temperature * 100 (0.7 = 70)
    timeout_seconds = Column(Integer, default=60, nullable=False)

    # Few-shot examples (FR-070)
    few_shot_examples = Column(JSON, nullable=True)  # List of example queries for orchestrator routing

    # Statistics
    usage_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    avg_execution_time_ms = Column(Integer, default=0, nullable=False)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=get_current_utc, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_current_utc, onupdate=get_current_utc, nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    workflow_steps = relationship("AgentWorkflowStep", back_populates="agent", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Agent {self.name} ({self.category})>"

    @property
    def success_rate(self) -> float:
        """Calculate success rate percentage"""
        if self.usage_count == 0:
            return 0.0
        return (self.success_count / self.usage_count) * 100

    @property
    def temperature_float(self) -> float:
        """Get temperature as float (0.0 - 1.0)"""
        return self.temperature / 100.0

    def increment_usage(self, success: bool, execution_time_ms: int):
        """
        Update agent statistics after execution

        Args:
            success: Whether execution succeeded
            execution_time_ms: Execution time in milliseconds
        """
        self.usage_count += 1
        if success:
            self.success_count += 1
        else:
            self.error_count += 1

        # Update average execution time
        if self.usage_count == 1:
            self.avg_execution_time_ms = execution_time_ms
        else:
            self.avg_execution_time_ms = int(
                (self.avg_execution_time_ms * (self.usage_count - 1) + execution_time_ms) / self.usage_count
            )

        self.last_used_at = get_current_utc()
