"""add user lockout fields

Revision ID: 004
Revises: 003
Create Date: 2025-11-01

FR-031: Account lockout implementation
Adds fields for account lockout management:
- email: Optional email address
- is_active: Account active/inactive status
- is_locked: Account lockout flag
- locked_until: Lockout expiry timestamp
- failed_login_attempts: Failed login counter

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add user lockout fields to users table."""
    # Add email column
    op.add_column('users', sa.Column('email', sa.String(length=255), nullable=True))

    # Add is_active column (default True)
    op.add_column('users', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))

    # Add is_locked column (default False)
    op.add_column('users', sa.Column('is_locked', sa.Boolean(), nullable=False, server_default='false'))

    # Add locked_until column (nullable)
    op.add_column('users', sa.Column('locked_until', sa.DateTime(timezone=True), nullable=True))

    # Add failed_login_attempts column (default 0)
    op.add_column('users', sa.Column('failed_login_attempts', sa.Integer(), nullable=False, server_default='0'))


def downgrade() -> None:
    """Remove user lockout fields from users table."""
    op.drop_column('users', 'failed_login_attempts')
    op.drop_column('users', 'locked_until')
    op.drop_column('users', 'is_locked')
    op.drop_column('users', 'is_active')
    op.drop_column('users', 'email')
