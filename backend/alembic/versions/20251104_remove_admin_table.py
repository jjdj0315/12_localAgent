"""Remove Admin table - use User.is_admin as single source of truth (FR-118)

Revision ID: 20251104_remove_admin
Revises: 20251102_add_metrics_tables
Create Date: 2025-11-04 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '20251104_remove_admin'
down_revision: Union[str, None] = '20251102_add_metrics_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Remove Admin table and rely solely on User.is_admin flag.

    Steps:
    1. Sync User.is_admin with Admin table records
    2. Drop Admin table

    Rationale (FR-118):
    - Simplifies privilege model
    - User.is_admin is already used in get_current_admin()
    - Eliminates dual source of truth
    """
    # Step 1: Ensure all users with Admin records have is_admin=True
    op.execute("""
        UPDATE users
        SET is_admin = TRUE
        WHERE id IN (SELECT user_id FROM admins)
    """)

    # Step 2: Drop Admin table
    op.drop_table('admins')


def downgrade() -> None:
    """
    Recreate Admin table and populate from User.is_admin flags.

    Note: This restores the Admin table structure but loses original
    permission flags (can_manage_users, can_view_logs, can_modify_settings).
    All restored admins will have full permissions.
    """
    # Recreate Admin table
    op.create_table('admins',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('can_manage_users', sa.Boolean(), nullable=False),
        sa.Column('can_view_logs', sa.Boolean(), nullable=False),
        sa.Column('can_modify_settings', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_by', sa.UUID(), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_admins_user_id'), 'admins', ['user_id'], unique=True)

    # Populate Admin table from User.is_admin flags
    # Note: created_at will be current timestamp, created_by will be NULL
    # All permissions set to TRUE (full admin)
    op.execute("""
        INSERT INTO admins (id, user_id, can_manage_users, can_view_logs, can_modify_settings, created_at, created_by)
        SELECT
            gen_random_uuid(),
            id,
            TRUE,
            TRUE,
            TRUE,
            NOW(),
            NULL
        FROM users
        WHERE is_admin = TRUE
    """)
