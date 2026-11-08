"""Persist notebook categories and descriptions without altering stored files."""
from alembic import op
import sqlalchemy as sa

revision = "phase3_management"
down_revision = "phase2_pipeline"
branch_labels = None
depends_on = None

def upgrade():
    op.add_column("notebooks", sa.Column("category", sa.String(), nullable=False, server_default="personal"))
    op.add_column("notebooks", sa.Column("description", sa.String(), nullable=False, server_default=""))
    # Match only known category icon basenames; never infer a category from a title.
    notebooks = sa.table("notebooks", sa.column("icon_path", sa.String()), sa.column("category", sa.String()))
    for category in ("study", "project", "research", "personal"):
        filename = f"icon-category-{category}.png"
        path = sa.func.replace(notebooks.c.icon_path, sa.func.chr(92), "/")
        op.execute(notebooks.update().where(sa.or_(notebooks.c.icon_path == filename, path.like("%/" + filename))).values(category=category))
    op.alter_column("notebooks", "category", server_default=None)
    op.alter_column("notebooks", "description", server_default=None)

def downgrade():
    op.drop_column("notebooks", "description")
    op.drop_column("notebooks", "category")
