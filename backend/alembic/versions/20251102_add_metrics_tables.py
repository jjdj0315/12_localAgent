"""Add metrics tracking tables

Revision ID: 20251102_metrics
Revises: f4412ac279b2
Create Date: 2025-11-02

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251102_metrics'
down_revision = 'f4412ac279b2'
branch_labels = None
depends_on = None


def upgrade():
    # Create metric_snapshots table
    op.create_table(
        'metric_snapshots',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_type', sa.String(length=50), nullable=False),
        sa.Column('value', sa.BigInteger(), nullable=False),
        sa.Column('granularity', sa.String(length=10), nullable=False),
        sa.Column('collected_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('retry_count', sa.SmallInteger(), server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('metric_type', 'granularity', 'collected_at', name='unique_metric_snapshot'),
        sa.CheckConstraint("granularity IN ('hourly', 'daily')", name='check_granularity')
    )

    op.create_index('idx_metric_type_time', 'metric_snapshots', ['metric_type', 'granularity', sa.text('collected_at DESC')])
    op.create_index('idx_cleanup_hourly', 'metric_snapshots', ['collected_at'], postgresql_where=sa.text("granularity = 'hourly'"))
    op.create_index('idx_cleanup_daily', 'metric_snapshots', ['collected_at'], postgresql_where=sa.text("granularity = 'daily'"))

    # Create metric_collection_failures table
    op.create_table(
        'metric_collection_failures',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('metric_type', sa.String(length=50), nullable=False),
        sa.Column('granularity', sa.String(length=10), nullable=False),
        sa.Column('attempted_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('error_message', sa.Text()),
        sa.Column('retry_count', sa.SmallInteger(), server_default='3'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_index('idx_failures_recent', 'metric_collection_failures', [sa.text('created_at DESC')])


def downgrade():
    op.drop_index('idx_failures_recent', table_name='metric_collection_failures')
    op.drop_table('metric_collection_failures')

    op.drop_index('idx_cleanup_daily', table_name='metric_snapshots')
    op.drop_index('idx_cleanup_hourly', table_name='metric_snapshots')
    op.drop_index('idx_metric_type_time', table_name='metric_snapshots')
    op.drop_table('metric_snapshots')
