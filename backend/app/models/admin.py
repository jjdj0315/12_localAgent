"""Admin model for privilege escalation prevention (FR-033)"""

from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import Boolean, Column, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.core.database import Base


def get_current_utc():
    """Get current UTC time with timezone"""
    return datetime.now(timezone.utc)


class Admin(Base):
    """
    Admin model - separate table for administrator privileges

    Per FR-033:
    - Separate admins table (no is_admin flag in users table)
    - Admin privileges granted only via direct database modification
    - Admins cannot revoke their own privileges
    """

    __tablename__ = "admins"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)

    # Admin permissions
    can_manage_users = Column(Boolean, default=True, nullable=False)  # User CRUD operations
    can_view_logs = Column(Boolean, default=True, nullable=False)      # Access audit logs
    can_modify_settings = Column(Boolean, default=True, nullable=False)  # System configuration

    created_at = Column(DateTime(timezone=True), default=get_current_utc, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)  # First admin will be NULL

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="admin_profile")

    def __repr__(self) -> str:
        return f"<Admin user_id={self.user_id}>"
