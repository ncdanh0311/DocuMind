"""Persist manual flashcards, spaced review states and idempotent review events."""
from alembic import op
import sqlalchemy as sa

revision = "phase4_study"
down_revision = "phase3_reading"
branch_labels = depends_on = None


def upgrade():
    op.add_column("storage_cleanup_tasks", sa.Column("size_bytes", sa.BigInteger(), nullable=False, server_default="0"))
    op.alter_column("storage_cleanup_tasks", "size_bytes", server_default=None)
    op.create_table("flashcards",
        sa.Column("card_id", sa.Uuid(), primary_key=True),
        sa.Column("notebook_id", sa.Uuid(), sa.ForeignKey("notebooks.notebook_id", ondelete="CASCADE"), nullable=False),
        sa.Column("question", sa.Text(), nullable=False), sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("search_text", sa.Text(), nullable=False),
        sa.Column("source_document_id", sa.Uuid(), sa.ForeignKey("documents.document_id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_snapshot", sa.JSON(), nullable=True), sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_flashcards_notebook_id", "flashcards", ["notebook_id"])
    op.create_index("ix_flashcards_source_document_id", "flashcards", ["source_document_id"])
    op.create_table("review_states",
        sa.Column("card_id", sa.Uuid(), sa.ForeignKey("flashcards.card_id", ondelete="CASCADE"), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("stage", sa.Integer(), nullable=False), sa.Column("revision", sa.Integer(), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_review_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_review_states_user_id", "review_states", ["user_id"])
    op.create_index("ix_review_states_due_at", "review_states", ["due_at"])
    op.create_table("review_events",
        sa.Column("request_id", sa.Uuid(), primary_key=True),
        sa.Column("card_id", sa.Uuid(), sa.ForeignKey("flashcards.card_id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("grade", sa.String(), nullable=False), sa.Column("expected_revision", sa.Integer(), nullable=False),
        sa.Column("card_revision", sa.Integer(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("response_snapshot", sa.JSON(), nullable=False))
    op.create_index("ix_review_events_card_id", "review_events", ["card_id"])
    op.create_index("ix_review_events_user_id", "review_events", ["user_id"])


def downgrade():
    op.drop_table("review_events")
    op.drop_table("review_states")
    op.drop_table("flashcards")
    op.drop_column("storage_cleanup_tasks", "size_bytes")
