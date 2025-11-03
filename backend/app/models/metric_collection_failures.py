"""MetricCollectionFailure model for tracking failed metric collections

This module defines the database model for tracking failed metric collection
attempts (Feature 002, FR-019).
"""
from sqlalchemy import Column, Integer, String, DateTime, SmallInteger, Text
from sqlalchemy.sql import func
from app.core.database import Base


class MetricCollectionFailure(Base):
    """Tracks failed metric collections for status indicator"""
    __tablename__ = "metric_collection_failures"

    id = Column(Integer, primary_key=True, index=True)
    metric_type = Column(String(50), nullable=False)
    granularity = Column(String(10), nullable=False)
    attempted_at = Column(DateTime(timezone=True), nullable=False)
    error_message = Column(Text)
    retry_count = Column(SmallInteger, default=3)  # Always 3 (max retries exhausted)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def to_dict(self):
        """Convert to API response format"""
        return {
            "metric_type": self.metric_type,
            "attempted_at": self.attempted_at.isoformat(),
            "error_message": self.error_message,
        }
