"""Durable object storage metadata, quota reservations and historical citations."""
from alembic import op
import sqlalchemy as sa

revision = "phase3_operations"
down_revision = "phase3_management"
branch_labels = depends_on = None


def upgrade():
    op.add_column("documents", sa.Column("storage_backend", sa.String(), nullable=False, server_default="local"))
    op.add_column("documents", sa.Column("file_size_bytes", sa.BigInteger(), nullable=True))
    op.add_column("documents", sa.Column("text_status", sa.String(), nullable=False, server_default="not_started"))
    op.add_column("documents", sa.Column("text_error_code", sa.String(), nullable=True))
    op.add_column("qa_history", sa.Column("citation_snapshot", sa.JSON(), nullable=False, server_default=sa.text("'[]'")))
    op.execute("""UPDATE documents SET text_status = 'ready'
        WHERE EXISTS (SELECT 1 FROM document_versions v WHERE v.document_id = documents.document_id
        AND v.version = documents.current_version)""")
    op.execute("""UPDATE qa_history q SET citation_snapshot = saved.value FROM (
        SELECT c.qa_id, json_agg(json_build_object(
            'document_id', d.document_id, 'source_title', d.file_name, 'version', ch.version,
            'start_offset', c.start_offset, 'end_offset', c.end_offset,
            'page_number', ch.page_number, 'page_end', ch.page_end, 'section_path', ch.section_path,
            'snippet', COALESCE(substring(v.canonical_text FROM c.start_offset + 1
                FOR c.end_offset - c.start_offset), ch.content))) AS value
        FROM citations c JOIN document_chunks ch ON ch.docuchunk_id = c.chunk_id
        JOIN documents d ON d.document_id = ch.document_id
        LEFT JOIN document_versions v ON v.document_id = ch.document_id AND v.version = ch.version
        GROUP BY c.qa_id) saved WHERE saved.qa_id = q.qahistory_id""")
    op.create_table("storage_ledger", sa.Column("ledger_id", sa.Integer(), primary_key=True))
    op.execute("INSERT INTO storage_ledger (ledger_id) VALUES (1)")
    op.create_table("upload_reservations",
        sa.Column("reservation_id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False),
        sa.Column("storage_key", sa.String(), nullable=False, unique=True),
        sa.Column("storage_backend", sa.String(), nullable=False),
        sa.Column("size_bytes", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False))
    op.create_index("ix_upload_reservations_user_id", "upload_reservations", ["user_id"])
    op.create_table("storage_cleanup_tasks",
        sa.Column("task_id", sa.Uuid(), primary_key=True),
        sa.Column("storage_backend", sa.String(), nullable=False),
        sa.Column("storage_key", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.UniqueConstraint("storage_backend", "storage_key", name="uq_cleanup_object"))
    for name in ("storage_backend", "text_status"):
        op.alter_column("documents", name, server_default=None)
    op.alter_column("qa_history", "citation_snapshot", server_default=None)


def downgrade():
    op.drop_table("storage_cleanup_tasks")
    op.drop_index("ix_upload_reservations_user_id", table_name="upload_reservations")
    op.drop_table("upload_reservations")
    op.drop_table("storage_ledger")
    op.drop_column("qa_history", "citation_snapshot")
    for name in ("text_error_code", "text_status", "file_size_bytes", "storage_backend"):
        op.drop_column("documents", name)
