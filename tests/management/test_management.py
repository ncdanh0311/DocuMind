from pathlib import Path
import uuid
import pytest
from sqlmodel import Session, select
from backend.app.models.models import Document, Job
from backend.app.services.storage import source_path

API = "/api/v1"

def create(client, **fields):
    response = client.post(API + "/notebooks/", json={"title": "Sổ tay", **fields})
    assert response.status_code == 201, response.text
    return response.json()

def test_notebook_metadata_survives_edit_and_reload(resources):
    client, _, _, _, _ = resources
    notebook = create(client, title="Toán học", category="project", description="Mô tả thật")
    assert notebook["category"] == "project"  # Title must not override explicit category.
    path = f"{API}/notebooks/{notebook['notebook_id']}"
    response = client.put(path, json={"title": "Tên mới", "category": "research", "description": "", "show_on_home": False})
    assert response.status_code == 200, response.text
    reloaded = client.get(path).json()
    assert (reloaded["title"], reloaded["category"], reloaded["description"], reloaded["show_on_home"]) == ("Tên mới", "research", "", False)
    assert client.get(API + "/notebooks/").json()[0]["category"] == "research"
    assert client.put(path, json={"category": None}).status_code == 422

@pytest.mark.parametrize("fields", [{"title": "   "}, {"category": "unknown"}, {"description": "x" * 1001}])
def test_invalid_notebook_fields(resources, fields):
    client, *_ = resources
    assert client.post(API + "/notebooks/", json={"title": "Name", **fields}).status_code == 422

def test_storage_only_upload_rename_and_delete_do_not_touch_ai(resources):
    client, engine, *_ = resources
    notebook = create(client)
    path = f"{API}/notebooks/{notebook['notebook_id']}/documents"
    for name, content in [("note.txt", "Nội dung 🐈".encode()), ("source.pdf", b"%PDF-test"), ("source.docx", b"PK-test")]:
        response = client.post(path + "/upload", files={"file": (name, content)})
        assert response.status_code == 201, response.text
        assert response.json()["status"] == "uploaded" and response.json()["job_id"] is None
    response = client.post(path + "/text", json={"title": "Ghi chú", "content": "Đoạn đầu\nĐoạn cuối"})
    assert response.status_code == 201 and response.json()["job_id"] is None
    document_id = response.json()["document_id"]
    with Session(engine) as session:
        before = session.get(Document, uuid.UUID(document_id))
        original = (before.storage_key, before.checksum, before.current_version, before.requested_version)
        content = source_path(before.storage_key).read_bytes()
        assert session.exec(select(Job)).all() == []
    result = client.patch(f"{API}/documents/{document_id}", json={"title": "Tên đã đổi"})
    assert result.status_code == 200 and result.json()["file_name"] == "Tên đã đổi.txt"
    with Session(engine) as session:
        after = session.get(Document, uuid.UUID(document_id))
        assert (after.storage_key, after.checksum, after.current_version, after.requested_version) == original
        assert source_path(after.storage_key).read_bytes() == content
    assert client.get(API + "/app-config").json() == {"ai_enabled": False}
    assert all(not item["ready"] and item["error_code"] == "ERR_AI_DISABLED" for item in client.get(API + "/capabilities").json()["models"])
    for endpoint, body in [(f"/notebooks/{notebook['notebook_id']}/chat", {"question": "Test?"}), (f"/notebooks/{notebook['notebook_id']}/summarize", {"model": "vit5"}), (f"/documents/{document_id}/reprocess", {})]:
        result = client.post(API + endpoint, json=body)
        assert result.status_code == 503 and result.json()["detail"] == "ERR_AI_DISABLED"
    assert client.delete(f"{API}/notebooks/{notebook['notebook_id']}").status_code == 204
    assert not source_path(original[0]).exists()

@pytest.mark.parametrize("title", ["   ", "../outside", "bad\\name", "line\nbreak", "x" * 201])
def test_bad_document_names(resources, title):
    client, *_ = resources
    notebook = create(client)
    document = client.post(f"{API}/notebooks/{notebook['notebook_id']}/documents/text", json={"title": "Note", "content": "Text"}).json()
    assert client.patch(f"{API}/documents/{document['document_id']}", json={"title": title}).status_code == 422

def test_owner_checks_for_metadata_and_rename(resources):
    client, _, identity, alice, bob = resources
    notebook = create(client)
    document = client.post(f"{API}/notebooks/{notebook['notebook_id']}/documents/text", json={"title": "Note", "content": "Text"}).json()
    identity["user"] = bob
    assert client.put(f"{API}/notebooks/{notebook['notebook_id']}", json={"description": "attack"}).status_code == 404
    assert client.patch(f"{API}/documents/{document['document_id']}", json={"title": "attack"}).status_code == 404
    assert client.delete(f"{API}/documents/{document['document_id']}").status_code == 404

def test_worker_exits_before_database_when_ai_disabled(resources):
    from backend.worker import run_once
    class ForbiddenDatabase:
        def connect(self): raise AssertionError("No database connection expected")
    assert run_once(ForbiddenDatabase()) is False


def test_app_config_still_requires_authentication(resources):
    from backend.main import app
    from backend.app.api.deps import get_current_user
    client, *_ = resources
    app.dependency_overrides.pop(get_current_user)
    assert client.get(API + "/app-config").status_code == 401
