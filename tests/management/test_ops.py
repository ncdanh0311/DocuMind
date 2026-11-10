from datetime import datetime, timezone
import uuid
import sqlalchemy as sa
from sqlmodel import SQLModel, create_engine
from backend.ops import import_legacy


def test_legacy_import_preserves_ids_and_refuses_overwrite(tmp_path):
    source = create_engine("sqlite:///" + str(tmp_path / "old.db"))
    target = create_engine("sqlite:///" + str(tmp_path / "new.db"))
    old = sa.MetaData()
    users = sa.Table("users", old,
        sa.Column("user_id", sa.Uuid(), primary_key=True), sa.Column("email", sa.String()),
        sa.Column("hashed_password", sa.String()), sa.Column("created_at", sa.DateTime(timezone=True)))
    notebooks = sa.Table("notebooks", old,
        sa.Column("notebook_id", sa.Uuid(), primary_key=True), sa.Column("user_id", sa.Uuid()),
        sa.Column("title", sa.String()), sa.Column("is_private", sa.Boolean()),
        sa.Column("show_on_home", sa.Boolean()), sa.Column("created_at", sa.DateTime(timezone=True)))
    documents = sa.Table("documents", old,
        sa.Column("document_id", sa.Uuid(), primary_key=True), sa.Column("notebook_id", sa.Uuid()),
        sa.Column("file_name", sa.String()), sa.Column("status", sa.String()),
        sa.Column("uploaded_at", sa.DateTime(timezone=True)))
    old.create_all(source); SQLModel.metadata.create_all(target)
    user_id, notebook_id, document_id = (uuid.uuid4() for _ in range(3))
    now = datetime.now(timezone.utc)
    with source.begin() as connection:
        connection.execute(users.insert().values(user_id=user_id, email="legacy@example.com", hashed_password="preserve-hash", created_at=now))
        connection.execute(notebooks.insert().values(notebook_id=notebook_id, user_id=user_id, title="Tiếng Việt 🐈", is_private=True, show_on_home=True, created_at=now))
        connection.execute(documents.insert().values(document_id=document_id, notebook_id=notebook_id, file_name="old.txt", status="ready", uploaded_at=now))
    assert import_legacy(source, target) == {"users": 1, "notebooks": 1, "documents": 1}
    assert import_legacy(source, target, True)["documents"] == 1
    with target.connect() as connection:
        row = connection.execute(sa.select(SQLModel.metadata.tables["documents"])).mappings().one()
        assert row["document_id"] == document_id and row["notebook_id"] == notebook_id
        assert row["current_version"] == 0 and row["file_size_bytes"] is None
        assert connection.execute(sa.select(SQLModel.metadata.tables["notebooks"].c.title)).scalar_one() == "Tiếng Việt 🐈"
    import pytest
    with pytest.raises(ValueError, match="empty target"): import_legacy(source, target, True)
    source.dispose(); target.dispose()
