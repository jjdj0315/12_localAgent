"""Session model"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def get_current_utc():
    """Get current UTC time with timezone"""
    return datetime.now(timezone.utc)


class Session(Base):
    """
    Session model for user authentication.

    Supports concurrent sessions per FR-030: Max 3 sessions per user.
    Clarification 2025-10-28: 4th login auto-terminates oldest session by last_activity.
    """

    __tablename__ = "sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    session_token = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=get_current_utc, nullable=False)
    last_activity = Column(
        DateTime(timezone=True),
        default=get_current_utc,
        onupdate=get_current_utc,
        nullable=False,
        index=True,
        comment="Last activity timestamp (updated on every request)"
    )
    expires_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    user = relationship("User", back_populates="sessions")

    def __repr__(self) -> str:
        return f"<Session {self.session_token[:8]}...>"
