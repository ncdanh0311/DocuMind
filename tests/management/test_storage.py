import hashlib
import io
import json
import uuid
from pathlib import Path
import pytest
from sqlmodel import Session, select
from backend.app.core.config import settings
from backend.app.models.models import Document, UploadReservation, StorageCleanupTask
from backend.app.services import storage
from backend.app.services.storage_quota import reserve

API = "/api/v1"


def notebook(client): return client.post(API + "/notebooks/", json={"title": "Storage"}).json()["notebook_id"]


def test_download_quota_and_ownership(resources, monkeypatch):
    client, engine, identity, _, bob = resources
    identifier = notebook(client)
    monkeypatch.setattr(settings, "MAX_USER_STORAGE_BYTES", 12)
    content = "Việt 🐈".encode()
    response = client.post(f"{API}/notebooks/{identifier}/documents/upload", files={"file": ("file.txt", content)})
    assert response.status_code == 201, response.text
    document = response.json()
    assert document["file_size_bytes"] == len(content)
    assert client.get(API + "/storage/usage").json()["used_bytes"] == len(content)
    download = client.get(f"{API}/documents/{document['document_id']}/download")
    assert download.content == content and download.headers["cache-control"] == "private, no-store"
    second = client.post(f"{API}/notebooks/{identifier}/documents/text", json={"title": "Too much", "content": "extra"})
    assert second.status_code == 413 and second.json()["detail"] == "ERR_USER_STORAGE_QUOTA"
    with Session(engine) as session: assert not session.exec(select(UploadReservation)).all()
    identity["user"] = bob
    assert client.get(f"{API}/documents/{document['document_id']}/download").status_code == 404


def test_reservations_charge_unfinished_uploads(resources, monkeypatch):
    _, engine, _, alice, _ = resources
    monkeypatch.setattr(settings, "MAX_TOTAL_STORAGE_BYTES", 10)
    with Session(engine) as session:
        reserve(session, alice.user_id, "pending/file.txt", "local", 8)
    from fastapi import HTTPException
    with Session(engine) as session, pytest.raises(HTTPException) as caught:
        reserve(session, alice.user_id, "pending/next.txt", "local", 3)
    assert caught.value.detail == "ERR_TOTAL_STORAGE_QUOTA"


def test_cloud_upload_survives_new_storage_instance_and_failed_delete(resources, monkeypatch):
    import backend.app.api.documents as documents
    objects = {}
    state = {"delete_fails": False}
    class FakeCloud:
        def put_file(self, key, path): objects[key] = Path(path).read_bytes()
        def open(self, key): return io.BytesIO(objects[key])
        def exists(self, key): return key in objects
        def delete(self, key):
            if state["delete_fails"]: raise OSError("provider unavailable")
            objects.pop(key, None)
    original = storage.get_storage
    factory = lambda backend=None: FakeCloud() if backend == "neon_s3" else original(backend)
    monkeypatch.setattr(storage, "get_storage", factory)
    monkeypatch.setattr(documents, "get_storage", factory)
    monkeypatch.setattr(settings, "STORAGE_BACKEND", "neon_s3")
    client, engine, *_ = resources
    identifier = notebook(client)
    response = client.post(f"{API}/notebooks/{identifier}/documents/text", json={"title": "Cloud", "content": "Persistent"})
    assert response.status_code == 201, response.text
    document_id = response.json()["document_id"]
    assert client.get(f"{API}/documents/{document_id}/download").content == b"Persistent"
    state["delete_fails"] = True
    assert client.delete(f"{API}/documents/{document_id}").status_code == 204
    with Session(engine) as session:
        assert session.exec(select(StorageCleanupTask)).one().attempts == 1
        assert not session.exec(select(Document)).all()
        state["delete_fails"] = False
        from backend.app.services.storage_quota import cleanup_pending
        assert cleanup_pending(session) == {"deleted": 1, "failed": 0}
    assert not objects


def test_failed_upload_releases_reservation(resources, monkeypatch):
    import backend.app.api.documents as documents
    class FailingStorage:
        def put_file(self, *_): raise RuntimeError("secret provider message must not escape")
    monkeypatch.setattr(documents, "get_storage", lambda *_: FailingStorage())
    client, engine, *_ = resources
    identifier = notebook(client)
    response = client.post(f"{API}/notebooks/{identifier}/documents/text", json={"title": "File", "content": "Data"})
    assert response.status_code == 503 and response.json()["detail"] == "ERR_STORAGE_UNAVAILABLE"
    with Session(engine) as session:
        assert not session.exec(select(UploadReservation)).all()
        assert not session.exec(select(Document)).all()


@pytest.mark.parametrize("key", ["../escape", "/absolute", "a/../b", "a\\b", "", "a//b", "a/./b"])
def test_storage_rejects_unsafe_keys(key):
    with pytest.raises(ValueError): storage.validate_key(key)


def test_neon_sdk_uses_supported_private_operations(monkeypatch, tmp_path):
    from botocore.stub import Stubber, ANY
    for key, value in {"AWS_ENDPOINT_URL_S3": "https://test.storage.neon.tech", "AWS_ACCESS_KEY_ID": "test-key",
                       "AWS_SECRET_ACCESS_KEY": "test-secret", "AWS_REGION": "us-east-1"}.items():
        monkeypatch.setattr(settings, key, value)
    client = storage.NeonStorage()
    path = tmp_path / "source.txt"; path.write_bytes(b"data")
    with Stubber(client.client) as stub:
        stub.add_response("put_object", {}, {"Bucket": settings.STORAGE_BUCKET, "Key": "a/source.txt",
            "Body": ANY, "ContentLength": 4, "ContentType": "application/octet-stream"})
        client.put_file("a/source.txt", path)
        stub.assert_no_pending_responses()


def test_backup_manifest_detects_corruption_and_path_traversal(tmp_path):
    from backend.ops import verify_backup
    (tmp_path / "objects").mkdir()
    (tmp_path / "database.dump").write_bytes(b"dump")
    (tmp_path / "objects/file.bin").write_bytes(b"data")
    manifest = {"format": 1, "database_sha256": hashlib.sha256(b"dump").hexdigest(), "objects": [
        {"key": "a/file.txt", "file": "file.bin", "sha256": hashlib.sha256(b"data").hexdigest(), "size": 4}]}
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    assert len(verify_backup(tmp_path)["objects"]) == 1
    (tmp_path / "objects/file.bin").write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="checksum"): verify_backup(tmp_path)
    manifest["objects"][0]["file"] = "../escape"
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="filename"): verify_backup(tmp_path)
