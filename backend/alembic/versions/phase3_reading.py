"""Retain saved summaries when their source document is deleted."""
from alembic import op

revision = "phase3_reading"
down_revision = "phase3_operations"
branch_labels = depends_on = None


def upgrade():
    op.drop_constraint("summaries_document_id_fkey", "summaries", type_="foreignkey")
    op.create_foreign_key("summaries_document_id_fkey", "summaries", "documents", ["document_id"], ["document_id"], ondelete="SET NULL")


def downgrade():
    op.drop_constraint("summaries_document_id_fkey", "summaries", type_="foreignkey")
    op.create_foreign_key("summaries_document_id_fkey", "summaries", "documents", ["document_id"], ["document_id"], ondelete="CASCADE")
