"""Fresh-database baseline. Existing development databases must use a new volume.

Revision ID: phase1_baseline
"""
from alembic import op
import sqlalchemy as sa
import sqlmodel
import pgvector.sqlalchemy

revision = "phase1_baseline"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table('auth_rate_limits',
    sa.Column('key', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('count', sa.Integer(), nullable=False),
    sa.Column('window_started_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('last_requested_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('key')
    )
    op.create_table('users',
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('email', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('full_name', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('hashed_password', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('avatar_id', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.PrimaryKeyConstraint('user_id')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_table('auth_sessions',
    sa.Column('session_id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('refresh_hash', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('revoked_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('session_id')
    )
    op.create_index(op.f('ix_auth_sessions_user_id'), 'auth_sessions', ['user_id'], unique=False)
    op.create_table('notebooks',
    sa.Column('notebook_id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('is_private', sa.Boolean(), nullable=False),
    sa.Column('show_on_home', sa.Boolean(), nullable=False),
    sa.Column('icon_path', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('notebook_id')
    )
    op.create_index(op.f('ix_notebooks_user_id'), 'notebooks', ['user_id'], unique=False)
    op.create_table('notifications',
    sa.Column('notification_id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('title', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('body', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('is_read', sa.Boolean(), nullable=False),
    sa.Column('type', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('notification_id')
    )
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)
    op.create_table('password_reset_challenges',
    sa.Column('challenge_id', sa.Uuid(), nullable=False),
    sa.Column('user_id', sa.Uuid(), nullable=False),
    sa.Column('otp_hash', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('otp_expires_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('attempts', sa.Integer(), nullable=False),
    sa.Column('otp_consumed_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('reset_hash', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('reset_expires_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('challenge_id')
    )
    op.create_index(op.f('ix_password_reset_challenges_user_id'), 'password_reset_challenges', ['user_id'], unique=False)
    op.create_table('documents',
    sa.Column('document_id', sa.Uuid(), nullable=False),
    sa.Column('notebook_id', sa.Uuid(), nullable=False),
    sa.Column('file_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('status', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('uploaded_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['notebook_id'], ['notebooks.notebook_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('document_id')
    )
    op.create_index(op.f('ix_documents_notebook_id'), 'documents', ['notebook_id'], unique=False)
    op.create_table('qa_history',
    sa.Column('qahistory_id', sa.Uuid(), nullable=False),
    sa.Column('notebook_id', sa.Uuid(), nullable=False),
    sa.Column('question', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('answer', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('model_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['notebook_id'], ['notebooks.notebook_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('qahistory_id')
    )
    op.create_index(op.f('ix_qa_history_notebook_id'), 'qa_history', ['notebook_id'], unique=False)
    op.create_table('document_chunks',
    sa.Column('docuchunk_id', sa.Uuid(), nullable=False),
    sa.Column('document_id', sa.Uuid(), nullable=False),
    sa.Column('content', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('embedding', pgvector.sqlalchemy.vector.VECTOR(dim=384), nullable=True),
    sa.Column('embedding_model', sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    sa.Column('page_number', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['document_id'], ['documents.document_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('docuchunk_id')
    )
    op.create_index(op.f('ix_document_chunks_document_id'), 'document_chunks', ['document_id'], unique=False)
    op.create_table('summaries',
    sa.Column('summary_id', sa.Uuid(), nullable=False),
    sa.Column('document_id', sa.Uuid(), nullable=False),
    sa.Column('content', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('model_name', sqlmodel.sql.sqltypes.AutoString(), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.ForeignKeyConstraint(['document_id'], ['documents.document_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('summary_id')
    )
    op.create_index(op.f('ix_summaries_document_id'), 'summaries', ['document_id'], unique=False)
    op.create_table('citations',
    sa.Column('citation_id', sa.Uuid(), nullable=False),
    sa.Column('qa_id', sa.Uuid(), nullable=False),
    sa.Column('chunk_id', sa.Uuid(), nullable=False),
    sa.Column('relevance_score', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['chunk_id'], ['document_chunks.docuchunk_id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['qa_id'], ['qa_history.qahistory_id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('citation_id')
    )
    op.create_index(op.f('ix_citations_chunk_id'), 'citations', ['chunk_id'], unique=False)
    op.create_index(op.f('ix_citations_qa_id'), 'citations', ['qa_id'], unique=False)

def downgrade():
    op.drop_table('citations')
    op.drop_table('summaries')
    op.drop_table('document_chunks')
    op.drop_table('qa_history')
    op.drop_table('documents')
    op.drop_table('password_reset_challenges')
    op.drop_table('notifications')
    op.drop_table('notebooks')
    op.drop_table('auth_sessions')
    op.drop_table('users')
    op.drop_table('auth_rate_limits')
