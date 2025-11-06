"""Remove Admin table and consolidate to User.is_admin (FR-118)

Revision ID: 20251105_remove_admin
Revises: 20251102_add_metrics_tables
Create Date: 2025-11-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251105_remove_admin'
down_revision = '20251102_add_metrics_tables'
branch_labels = None
depends_on = None


def upgrade():
    """
    Remove Admin table and consolidate admin privileges to User.is_admin
    
    Steps:
    1. Sync User.is_admin from Admin table (if any admins exist)
    2. DROP admins table
    """
    # Sync User.is_admin flag from Admin table
    # Set is_admin=TRUE for users who have entries in admins table
    op.execute("""
        UPDATE users
        SET is_admin = TRUE
        WHERE id IN (SELECT user_id FROM admins)
    """)
    
    # Drop admins table (no longer needed)
    op.drop_table('admins')


def downgrade():
    """
    Recreate Admin table and populate from User.is_admin
    """
    # Recreate admins table
    op.create_table(
        'admins',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('granted_by', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    
    # Populate admins table from User.is_admin
    op.execute("""
        INSERT INTO admins (user_id, granted_at)
        SELECT id, created_at
        FROM users
        WHERE is_admin = TRUE
    """)
