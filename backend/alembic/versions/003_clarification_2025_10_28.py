"""Clarification 2025-10-28: Document scope and storage management

Revision ID: 003
Revises: 002
Create Date: 2025-10-28

Changes:
- Add conversation_id FK to documents (documents are conversation-scoped)
- Add last_accessed_at to documents (for auto-cleanup)
- Add extracted_text to documents (for Q&A)
- Add last_accessed_at to conversations (for auto-cleanup)
- Add storage_size_bytes to conversations (for quota enforcement)
- Migrate existing data from conversation_documents to documents.conversation_id
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to sessions table (for session limit enforcement)
    op.add_column('sessions', sa.Column(
        'last_activity',
        sa.DateTime(timezone=True),
        server_default=sa.text('now()'),
        nullable=False,
        comment='Last activity timestamp (updated on every request)'
    ))
    op.create_index(op.f('ix_sessions_last_activity'), 'sessions', ['last_activity'], unique=False)

    # Add new columns to conversations table
    op.add_column('conversations', sa.Column(
        'last_accessed_at',
        sa.DateTime(timezone=True),
        server_default=sa.text('now()'),
        nullable=False,
        comment='Last access timestamp for auto-cleanup (Clarification 2025-10-28)'
    ))
    op.add_column('conversations', sa.Column(
        'storage_size_bytes',
        sa.BigInteger(),
        server_default='0',
        nullable=False,
        comment='Total storage used by conversation + documents for quota enforcement (Clarification 2025-10-28)'
    ))
    op.create_index(op.f('ix_conversations_last_accessed_at'), 'conversations', ['last_accessed_at'], unique=False)

    # Add new columns to documents table
    op.add_column('documents', sa.Column(
        'conversation_id',
        postgresql.UUID(as_uuid=True),
        nullable=True,  # Nullable temporarily for migration
        comment='Parent conversation (documents belong to one conversation per Clarification 2025-10-28)'
    ))
    op.add_column('documents', sa.Column(
        'last_accessed_at',
        sa.DateTime(timezone=True),
        server_default=sa.text('now()'),
        nullable=False,
        comment='Last access timestamp for auto-cleanup (Clarification 2025-10-28)'
    ))
    op.add_column('documents', sa.Column(
        'extracted_text',
        sa.Text(),
        nullable=True,
        comment='Extracted text content for search/Q&A'
    ))

    # Migrate existing data: Copy conversation_id from conversation_documents to documents
    # For documents with multiple conversations (M:N), keep the first one
    op.execute("""
        UPDATE documents d
        SET conversation_id = (
            SELECT cd.conversation_id
            FROM conversation_documents cd
            WHERE cd.document_id = d.id
            ORDER BY cd.added_at ASC
            LIMIT 1
        )
        WHERE EXISTS (
            SELECT 1 FROM conversation_documents cd WHERE cd.document_id = d.id
        )
    """)

    # Make conversation_id NOT NULL and add foreign key
    op.alter_column('documents', 'conversation_id', nullable=False)
    op.create_foreign_key(
        'fk_documents_conversation_id',
        'documents', 'conversations',
        ['conversation_id'], ['id'],
        ondelete='CASCADE'
    )
    op.create_index(op.f('ix_documents_conversation_id'), 'documents', ['conversation_id'], unique=False)
    op.create_index(op.f('ix_documents_last_accessed_at'), 'documents', ['last_accessed_at'], unique=False)

    # Make file_path unique (should already be, but enforce at DB level)
    op.create_unique_constraint('uq_documents_file_path', 'documents', ['file_path'])


def downgrade() -> None:
    # Remove unique constraint
    op.drop_constraint('uq_documents_file_path', 'documents', type_='unique')

    # Remove indexes
    op.drop_index(op.f('ix_documents_last_accessed_at'), table_name='documents')
    op.drop_index(op.f('ix_documents_conversation_id'), table_name='documents')
    op.drop_index(op.f('ix_conversations_last_accessed_at'), table_name='conversations')
    op.drop_index(op.f('ix_sessions_last_activity'), table_name='sessions')

    # Remove foreign key and columns from documents
    op.drop_constraint('fk_documents_conversation_id', 'documents', type_='foreignkey')
    op.drop_column('documents', 'extracted_text')
    op.drop_column('documents', 'last_accessed_at')
    op.drop_column('documents', 'conversation_id')

    # Remove columns from conversations
    op.drop_column('conversations', 'storage_size_bytes')
    op.drop_column('conversations', 'last_accessed_at')

    # Remove columns from sessions
    op.drop_column('sessions', 'last_activity')
