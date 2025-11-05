"""MetricSnapshot model for storing historical metric data

This module defines the database model for metric snapshots collected at
hourly and daily granularity (Feature 002: FR-089~FR-109).

Supports admin metrics history dashboard with time-series graphs.
"""
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, SmallInteger, CheckConstraint, UniqueConstraint, Index
from sqlalchemy.sql import func
from app.core.database import Base


class MetricSnapshot(Base):
    """Stores point-in-time metric values at hourly and daily granularity.

    Retention: 30 days (hourly), 90 days (daily) per FR-091.
    """
    __tablename__ = "metric_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(String(50), nullable=False, comment="active_users, storage_bytes, active_sessions, conversation_count, document_count, tag_count")
    value = Column(BigInteger, nullable=False, comment="Numeric metric value (BIGINT supports large storage byte counts)")
    granularity = Column(String(10), nullable=False, comment="'hourly' or 'daily' for different retention periods")
    collected_at = Column(DateTime(timezone=True), nullable=False, comment="When metric was captured (UTC per FR-105)")
    retry_count = Column(SmallInteger, default=0, comment="Number of retry attempts before successful collection (FR-107)")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="Database insertion timestamp")

    __table_args__ = (
        UniqueConstraint('metric_type', 'granularity', 'collected_at', name='unique_metric_snapshot'),
        CheckConstraint("granularity IN ('hourly', 'daily')", name='check_granularity'),
        # Performance indexes for time-series queries (per data-model.md)
        Index('idx_metric_type_time', 'metric_type', 'granularity', 'collected_at'),
        # Cleanup indexes for automatic data retention (FR-104)
        Index('idx_cleanup_hourly', 'collected_at', postgresql_where="granularity = 'hourly'"),
        Index('idx_cleanup_daily', 'collected_at', postgresql_where="granularity = 'daily'"),
    )

    def to_dict(self):
        """Convert to API response format"""
        return {
            "metric_type": self.metric_type,
            "value": self.value,
            "granularity": self.granularity,
            "timestamp": self.collected_at.isoformat(),
        }
