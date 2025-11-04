"""MetricCollectionFailure model for tracking failed metric collections

This module defines the database model for tracking failed metric collection
attempts (Feature 002: FR-106, FR-107).

Supports collection status indicator (green/yellow/red) and retry logic.
"""
from sqlalchemy import Column, Integer, String, DateTime, SmallInteger, Text, Index
from sqlalchemy.sql import func
from app.core.database import Base


class MetricCollectionFailure(Base):
    """Tracks failed metric collections for admin status indicator (FR-106).

    Records failures after max 3 retry attempts exhausted (FR-107).
    Used to calculate collection health status (green/yellow/red thresholds).
    """
    __tablename__ = "metric_collection_failures"

    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(String(50), nullable=False, comment="active_users, storage_bytes, active_sessions, conversation_count, document_count, tag_count")
    granularity = Column(String(10), nullable=False, comment="'hourly' or 'daily'")
    attempted_at = Column(DateTime(timezone=True), nullable=False, comment="When collection was attempted (UTC)")
    error_message = Column(Text, comment="Exception or error details for debugging")
    retry_count = Column(SmallInteger, default=0, comment="Number of retry attempts made before final failure (max 3 per FR-107)")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="When failure was recorded")

    __table_args__ = (
        # Performance indexes for status indicator queries (FR-106)
        Index('idx_failures_recent', 'created_at'),
        Index('idx_metric_type_failures', 'metric_type', 'attempted_at'),
    )

    def to_dict(self):
        """Convert to API response format"""
        return {
            "metric_type": self.metric_type,
            "attempted_at": self.attempted_at.isoformat(),
            "error_message": self.error_message,
        }
