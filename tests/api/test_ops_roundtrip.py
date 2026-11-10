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


def test_backup_restore_preserves_database_and_original_files(client, db_engine, account, monkeypatch, tmp_path):
    if not all(shutil.which(name) for name in ("pg_dump", "pg_restore")):
        pytest.skip("PostgreSQL client tools required; installed on the CI runner")
    monkeypatch.setattr(settings, "AI_ENABLED", False)
    notebook = client.post("/api/v1/notebooks/", headers=headers(account), json={"title": "Backup 🐈"}).json()
    response = client.post(f"/api/v1/notebooks/{notebook['notebook_id']}/documents/text", headers=headers(account),
                           json={"title": "Nguồn", "content": "Nội dung khôi phục 🐈"})
    assert response.status_code == 201, response.text
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
        with pytest.raises(ValueError, match="empty target database"): restore(target, backup_dir)
    finally:
        if target: target.dispose()
        with admin.connect() as connection: connection.execute(text(f'DROP DATABASE IF EXISTS "{database}"'))
        admin.dispose()
