"""Add response time tracking to messages

Revision ID: 002
Revises: 001
Create Date: 2025-01-24
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Add processing_time_ms column to messages table
    op.add_column('messages',
        sa.Column('processing_time_ms', sa.Integer(), nullable=True, comment='LLM response generation time in milliseconds')
    )

    # Add index for performance queries
    op.create_index('idx_messages_processing_time', 'messages', ['processing_time_ms'])


def downgrade():
    op.drop_index('idx_messages_processing_time', 'messages')
    op.drop_column('messages', 'processing_time_ms')
