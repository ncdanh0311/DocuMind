from fastapi import HTTPException
from sqlalchemy import text
from sqlmodel import Session
from backend.app.models.models import Document, DocumentChunk, Notification
from tests.helpers import headers

API = "/api/v1"

def test_notebook_and_documents_are_owner_scoped(client, account, db_engine):
    notebook = client.post(API + "/notebooks/", headers=headers(account), json={"title": "Study"}).json()
    notebook_id = notebook["notebook_id"]
    with Session(db_engine) as session:
        doc = Document(notebook_id=notebook_id, file_name="source.txt", status="ready", current_version=1)
        session.add(doc); session.flush()
        chunk = DocumentChunk(document_id=doc.document_id, content="An answer", page_number=3, version=1, global_index=0, start_offset=0, end_offset=9)
        session.add(chunk)
        notification = Notification(user_id=account["user_id"], title="Ready", body="Document processed")
        session.add(notification); session.commit()
        doc_id = str(doc.document_id); notification_id = str(notification.notification_id)
    listing = client.get(API + "/notebooks/", headers=headers(account))
    assert listing.json()[0]["document_count"] == 1
    assert client.get(f"{API}/notebooks/{notebook_id}", headers=headers(account)).json()["document_count"] == 1
    assert len(client.get(f"{API}/documents/{doc_id}/chunks", headers=headers(account)).json()) == 1
    assert client.get(API + "/notifications/", headers=headers(account)).json()[0]["body"] == "Document processed"
    bob = client.post(API + "/auth/register", json={"email": "bob@example.com", "password": "correct-password"}).json()
    for operation, path, kwargs in [
        ("get", f"/notebooks/{notebook_id}", {}),
        ("put", f"/notebooks/{notebook_id}", {"json": {"title": "Changed"}}),
        ("delete", f"/notebooks/{notebook_id}", {}),
        ("get", f"/notebooks/{notebook_id}/documents", {}),
        ("post", f"/notebooks/{notebook_id}/documents/text", {"json": {"title": "note", "content": "Text"}}),
        ("post", f"/notebooks/{notebook_id}/documents/upload", {"files": {"file": ("note.txt", b"Text", "text/plain")}}),
        ("get", f"/documents/{doc_id}/chunks", {}),
        ("delete", f"/documents/{doc_id}", {}),
        ("post", f"/notebooks/{notebook_id}/chat", {"json": {"question": "Question?", "model": "phobert_qa"}}),
        ("post", f"/notebooks/{notebook_id}/summarize", {"json": {"model": "vit5"}}),
        ("post", f"/notifications/{notification_id}/read", {}),
    ]:
        response = getattr(client, operation)(API + path, headers=headers(bob), **kwargs)
        assert response.status_code == 404, (operation, path, response.text)
        assert getattr(client, operation)(API + path, **kwargs).status_code == 401
    assert client.get(API + "/documents/recent", headers=headers(bob)).json() == []
    assert client.get(API + "/notifications/", headers=headers(bob)).json() == []
    assert client.delete(f"{API}/notebooks/{notebook_id}", headers=headers(account)).status_code == 204
    with Session(db_engine) as session:
        assert session.get(Document, doc_id) is None

def test_upload_contract_model_validation_and_ai_errors(client, account, monkeypatch):
    notebook_id = client.post(API + "/notebooks/", headers=headers(account), json={"title": "Study"}).json()["notebook_id"]
    result = client.post(f"{API}/notebooks/{notebook_id}/documents/upload", headers=headers(account), files={"file": ("note.txt", b"Some text", "text/plain")})
    assert result.status_code == 201, result.text
    assert result.json()["status"] == "uploaded"
    assert client.post(f"{API}/notebooks/{notebook_id}/chat", headers=headers(account), json={"question": "Question?", "model": "xlm_roberta"}).status_code == 422
    assert client.post(f"{API}/notebooks/{notebook_id}/summarize", headers=headers(account), json={"model": "unknown"}).status_code == 422
    from backend.app.api import notebooks
    def unavailable(**kwargs): raise HTTPException(503, "ERR_AI_SERVICE_UNAVAILABLE")
    monkeypatch.setattr(notebooks.rag_service, "answer_notebook_question", unavailable)
    assert client.post(f"{API}/notebooks/{notebook_id}/chat", headers=headers(account), json={"question": "Question?", "model": "xlmroberta_qa"}).status_code == 503
    assert client.post(API + "/notebooks/", headers=headers(account), json={"title": "Study", "user_id": account["user_id"]}).status_code == 422

def test_health_readiness_and_public_schema_removal(client, db_engine):
    assert client.get("/health").json() == {"status": "online"}
    assert client.get("/ready").status_code == 200
    assert client.get("/init-db").status_code == 404
    assert client.post("/init-db").status_code == 404
    with db_engine.begin() as connection:
        original_revision = connection.execute(text("SELECT version_num FROM alembic_version")).scalar_one()
        connection.execute(text("UPDATE alembic_version SET version_num = 'not_the_head'"))
    try:
        assert client.get("/ready").status_code == 503
        assert client.get("/ready").json() == {"status": "not_ready"}
    finally:
        with db_engine.begin() as connection:
            connection.execute(text("UPDATE alembic_version SET version_num = :revision"), {"revision": original_revision})

def test_migration_matches_metadata(db_engine):
    from alembic.autogenerate import compare_metadata
    from alembic.runtime.migration import MigrationContext
    from backend.app.models.models import SQLModel
    with db_engine.connect() as connection:
        differences = compare_metadata(MigrationContext.configure(connection, opts={"compare_type": True}), SQLModel.metadata)
    assert differences == []


def test_baseline_downgrade_and_rebuild(db_engine):
    from alembic import command
    from alembic.config import Config
    from pathlib import Path
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    with db_engine.begin() as connection:
        config.attributes["connection"] = connection
        command.downgrade(config, "base")
        command.upgrade(config, "head")
    test_migration_matches_metadata(db_engine)


def test_phase2_upgrade_marks_legacy_sources_for_reprocessing(db_engine):
    from alembic import command
    from alembic.config import Config
    from pathlib import Path
    import uuid
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    user, notebook, document, summary = (str(uuid.uuid4()) for _ in range(4))
    with db_engine.begin() as connection:
        config.attributes["connection"] = connection
        command.downgrade(config, "phase1_baseline")
        connection.execute(text("INSERT INTO users (user_id, email, hashed_password, created_at) VALUES (:id, :email, 'test-hash', now())"), {"id": user, "email": user + "@example.com"})
        connection.execute(text("INSERT INTO notebooks (notebook_id, user_id, title, is_private, show_on_home, created_at) VALUES (:id, :user, 'Legacy', true, true, now())"), {"id": notebook, "user": user})
        connection.execute(text("INSERT INTO documents (document_id, notebook_id, file_name, status, uploaded_at) VALUES (:id, :notebook, 'legacy.txt', 'ready', now())"), {"id": document, "notebook": notebook})
        connection.execute(text("INSERT INTO summaries (summary_id, document_id, content, model_name, created_at) VALUES (:id, :document, 'Old content', 'vit5', now())"), {"id": summary, "document": document})
        command.upgrade(config, "head")
        row = connection.execute(text("SELECT current_version, status, error_code FROM documents WHERE document_id = :id"), {"id": document}).one()
        assert tuple(row) == (0, "error", "ERR_REPROCESS_REQUIRED")
        row = connection.execute(text("SELECT notebook_id, status, error_code FROM summaries WHERE summary_id = :id"), {"id": summary}).one()
        assert str(row.notebook_id) == notebook and row.status == "failed" and row.error_code == "ERR_REPROCESS_REQUIRED"
    test_migration_matches_metadata(db_engine)

def test_validation_and_errors_do_not_echo_credentials(client):
    result = client.post(API + "/auth/reset-password", json={"token": "private-token-value", "new_password": "secret"})
    assert result.status_code == 422
    assert "private-token-value" not in result.text
    assert "secret" not in result.text
    assert "input" not in result.json()["detail"][0]

def test_cors_uses_explicit_origins(client):
    allowed = client.options(API + "/auth/me", headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "GET"})
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:3000"
    denied = client.options(API + "/auth/me", headers={"Origin": "https://untrusted.example", "Access-Control-Request-Method": "GET"})
    assert "access-control-allow-origin" not in denied.headers


def test_phase3_upgrade_preserves_notebooks_and_backfills_categories(db_engine):
    from alembic import command
    from alembic.config import Config
    from pathlib import Path
    import uuid
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    user_id = str(uuid.uuid4())
    cases = [("/assets/icons/categories/icon-category-study.png", "study"),
             ("assets\\icons\\categories\\icon-category-project.png", "project"),
             ("icon-category-research.png", "research"),
             ("weirdicon-category-study.png", "personal"), (None, "personal")]
    with db_engine.begin() as connection:
        config.attributes["connection"] = connection
        command.downgrade(config, "phase2_pipeline")
        connection.execute(text("INSERT INTO users (user_id,email,hashed_password,created_at) VALUES (:id,:email,'test-only',now())"), {"id": user_id, "email": user_id + "@example.com"})
        expected = {}
        for icon, category in cases:
            notebook_id = str(uuid.uuid4()); expected[notebook_id] = category
            connection.execute(text("INSERT INTO notebooks (notebook_id,user_id,title,icon_path,is_private,show_on_home,created_at) VALUES (:id,:user,'Học Toán',:icon,true,true,now())"), {"id": notebook_id, "user": user_id, "icon": icon})
        command.upgrade(config, "head")
        rows = connection.execute(text("SELECT notebook_id,title,category,description FROM notebooks WHERE user_id=:id"), {"id": user_id}).all()
        assert len(rows) == len(cases)
        assert all(row.title == "Học Toán" and row.description == "" and row.category == expected[str(row.notebook_id)] for row in rows)
    test_migration_matches_metadata(db_engine)
