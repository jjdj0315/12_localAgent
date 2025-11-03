"""MetricSnapshot model for storing historical metric data

This module defines the database model for metric snapshots collected at
hourly and daily granularity (Feature 002).
"""
from sqlalchemy import Column, Integer, BigInteger, String, DateTime, SmallInteger, CheckConstraint, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base


class MetricSnapshot(Base):
    """Stores point-in-time metric values at hourly and daily granularity"""
    __tablename__ = "metric_snapshots"

    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(String(50), nullable=False)
    value = Column(BigInteger, nullable=False)
    granularity = Column(String(10), nullable=False)
    collected_at = Column(DateTime(timezone=True), nullable=False)
    retry_count = Column(SmallInteger, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint('metric_type', 'granularity', 'collected_at', name='unique_metric_snapshot'),
        CheckConstraint("granularity IN ('hourly', 'daily')", name='check_granularity'),
    )

    def to_dict(self):
        """Convert to API response format"""
        return {
            "metric_type": self.metric_type,
            "value": self.value,
            "granularity": self.granularity,
            "timestamp": self.collected_at.isoformat(),
        }
