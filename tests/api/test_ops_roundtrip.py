"""Real pg_dump/restore roundtrip on disposable CI databases only."""
import shutil
import uuid
import pytest
from sqlalchemy import text
from sqlmodel import Session, create_engine, select
from backend.app.core.config import settings
from backend.app.models.models import Document, User
from backend.ops import backup, restore, verify_backup
from tests.helpers import headers


def test_old_schema_backup_restore_then_upgrade(db_engine, monkeypatch, tmp_path):
    """Exercise a real pre-storage schema, not metadata.create_all() of the new ORM."""
    if not all(shutil.which(name) for name in ("pg_dump", "pg_restore")):
        pytest.skip("PostgreSQL client tools required")
    from alembic import command
    from alembic.config import Config
    from datetime import datetime, timezone
    from sqlalchemy import MetaData, Table
    from backend.ops import preflight
    from backend.app.services.storage import source_path
    names = ["documind_old_" + uuid.uuid4().hex[:12] + "_test" for _ in range(2)]
    admin = create_engine(db_engine.url, isolation_level="AUTOCOMMIT")
    engines = []
    try:
        for name in names:
            with admin.connect() as connection: connection.execute(text(f'CREATE DATABASE "{name}"'))
            engines.append(create_engine(db_engine.url.set(database=name), hide_parameters=True))
        source, target = engines
        config = Config("alembic.ini")
        with source.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "phase1_baseline")
        monkeypatch.setattr(settings, "STORAGE_BACKEND", "local")
        monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "old-files"))
        monkeypatch.setattr(settings, "DATABASE_DIRECT_URL", source.url.render_as_string(hide_password=False))
        user_id, notebook_id, document_id = (uuid.uuid4() for _ in range(3))
        now = datetime.now(timezone.utc)
        with source.begin() as connection:
            users = Table("users", MetaData(), autoload_with=connection)
            notebooks = Table("notebooks", MetaData(), autoload_with=connection)
            documents = Table("documents", MetaData(), autoload_with=connection)
            connection.execute(users.insert().values(user_id=user_id, email="legacy@example.com", hashed_password="retain", created_at=now))
            connection.execute(notebooks.insert().values(notebook_id=notebook_id, user_id=user_id, title="Nguồn cũ", is_private=True, show_on_home=True, created_at=now))
            connection.execute(documents.insert().values(document_id=document_id, notebook_id=notebook_id, file_name="old.txt", status="uploaded", uploaded_at=now))
        assert not preflight(source)["database"]["schema_current"]
        with pytest.raises(ValueError, match="current Alembic"):
            preflight(source, require_current_schema=True)
        path = source_path(f"{notebook_id}/{document_id}.txt")
        path.parent.mkdir(parents=True); path.write_bytes("Tài liệu trước migration 🐈".encode())
        directory = tmp_path / "before-upgrade"
        assert backup(source, directory)["revision"] == "phase1_baseline"
        monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "restored-old-files"))
        monkeypatch.setattr(settings, "DATABASE_DIRECT_URL", target.url.render_as_string(hide_password=False))
        assert restore(target, directory)["restored_objects"] == 1
        assert source_path(f"{notebook_id}/{document_id}.txt").read_bytes() == path.read_bytes()
        with target.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        assert preflight(target, require_current_schema=True)["database"]["schema_current"]
        with Session(target) as session:
            assert session.get(Document, document_id).notebook_id == notebook_id
            assert session.get(User, user_id).hashed_password == "retain"
    finally:
        for engine in engines: engine.dispose()
        with admin.connect() as connection:
            for name in names: connection.execute(text(f'DROP DATABASE IF EXISTS "{name}"'))
        admin.dispose()


def test_backup_restore_preserves_database_and_original_files(client, db_engine, account, monkeypatch, tmp_path):
    if not all(shutil.which(name) for name in ("pg_dump", "pg_restore")):
        pytest.skip("PostgreSQL client tools required; installed on the CI runner")
    monkeypatch.setattr(settings, "AI_ENABLED", False)
    notebook = client.post("/api/v1/notebooks/", headers=headers(account), json={"title": "Backup 🐈"}).json()
    response = client.post(f"/api/v1/notebooks/{notebook['notebook_id']}/documents/text", headers=headers(account),
                           json={"title": "Nguồn", "content": "Nội dung khôi phục 🐈"})
    assert response.status_code == 201, response.text
    card = client.post(f"/api/v1/notebooks/{notebook['notebook_id']}/flashcards", headers=headers(account),
                       json={"question": "Backup thẻ?", "answer": "Giữ cả tiến độ"}).json()
    import uuid as uuid_module
    graded = client.post(f"/api/v1/flashcards/{card['card_id']}/reviews", headers=headers(account),
        json={"request_id": str(uuid_module.uuid4()), "grade": "remembered", "expected_revision": 0, "card_revision": 1})
    assert graded.status_code == 200, graded.text
    backup_dir = tmp_path / "archive"
    assert backup(db_engine, backup_dir)["objects"] == 1
    manifest = verify_backup(backup_dir)
    database = "documind_restore_" + uuid.uuid4().hex[:12] + "_test"
    target_url = db_engine.url.set(database=database)
    admin = create_engine(db_engine.url, isolation_level="AUTOCOMMIT")
    target = None
    try:
        with admin.connect() as connection: connection.execute(text(f'CREATE DATABASE "{database}"'))
        target = create_engine(target_url, hide_parameters=True)
        monkeypatch.setattr(settings, "DATABASE_DIRECT_URL", target_url.render_as_string(hide_password=False))
        monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "restored-files"))
        result = restore(target, backup_dir)
        assert result["restored_objects"] == 1 and result["revision"] == manifest["revision"]
        with Session(target) as session:
            assert session.exec(select(User)).one().email == "alice@example.com"
            document = session.exec(select(Document)).one()
            from backend.app.services.storage import source_path
            assert source_path(document.storage_key).read_text(encoding="utf-8") == "Nội dung khôi phục 🐈"
            from backend.app.models.models import Flashcard, ReviewState, ReviewEvent
            assert session.exec(select(Flashcard)).one().question == "Backup thẻ?"
            assert session.exec(select(ReviewState)).one().revision == 1
            assert session.exec(select(ReviewEvent)).one().grade == "remembered"
        with pytest.raises(ValueError, match="empty target database"): restore(target, backup_dir)
    finally:
        if target: target.dispose()
        with admin.connect() as connection: connection.execute(text(f'DROP DATABASE IF EXISTS "{database}"'))
        admin.dispose()
