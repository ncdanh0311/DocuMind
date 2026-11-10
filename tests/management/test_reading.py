import io
import subprocess
import uuid
import pytest
from sqlmodel import Session, select
from backend.app.models.models import Document, DocumentVersion, QAHistory, Summary
from backend.app.models.models import Job
from backend.app.core.config import settings
from backend.app.services import text_extraction

API = "/api/v1"


def upload(client, name, content):
    notebook = client.post(API + "/notebooks/", json={"title": "Đọc tài liệu"}).json()["notebook_id"]
    response = client.post(f"{API}/notebooks/{notebook}/documents/upload", files={"file": (name, content)})
    assert response.status_code == 201, response.text
    return notebook, response.json()["document_id"]


@pytest.mark.parametrize("extension", ["txt", "pdf", "docx"])
def test_text_only_extraction_and_cache(resources, extension):
    client, engine, *_ = resources
    content = "Tiếng Việt, phần cuối tài liệu."
    if extension == "txt": data = ("Đầu 🐈\n" + content).encode()
    elif extension == "pdf":
        import pymupdf
        with pymupdf.open() as pdf:
            pdf.new_page().insert_text((50, 50), "First page")
            pdf.new_page().insert_text((50, 50), "Last page")
            data = pdf.tobytes()
    else:
        from docx import Document as Docx
        doc = Docx(); doc.add_heading("Chương 1", 1); doc.add_paragraph(content)
        doc.add_table(rows=1, cols=1).cell(0, 0).text = "Nội dung bảng"
        stream = io.BytesIO(); doc.save(stream); data = stream.getvalue()
    _, identifier = upload(client, "source." + extension, data)
    response = client.post(f"{API}/documents/{identifier}/extract-text")
    assert response.status_code == 200, response.text
    assert response.json()["text_status"] == "ready" and response.json()["status"] == "uploaded"
    source = client.get(f"{API}/documents/{identifier}/source").json()
    if extension == "txt":
        assert source["text"] == "Đầu 🐈\n" + content
        selected = client.get(f"{API}/documents/{identifier}/source?start=4&end=5").json()
        assert selected["text"] == "🐈"
    elif extension == "pdf":
        assert "Last page" in source["text"] and source["sections"][-1]["page_start"] == 2
    else: assert content in source["text"] and "Nội dung bảng" in source["text"]
    assert client.post(f"{API}/documents/{identifier}/extract-text").json()["current_version"] == source["version"]
    with Session(engine) as session: assert len(session.exec(select(DocumentVersion)).all()) == 1


def test_scanned_pdf_and_corruption_preserve_original_download(resources):
    client, *_ = resources
    import pymupdf
    with pymupdf.open() as pdf:
        pdf.new_page(); data = pdf.tobytes()
    _, identifier = upload(client, "scan.pdf", data)
    response = client.post(f"{API}/documents/{identifier}/extract-text")
    assert response.status_code == 422 and response.json()["detail"] == "ERR_DOCUMENT_NEEDS_OCR"
    assert client.get(f"{API}/documents/{identifier}/download").content == data
    _, identifier = upload(client, "corrupt.pdf", b"%PDF-corrupted")
    assert client.post(f"{API}/documents/{identifier}/extract-text").json()["detail"] == "ERR_FILE_FORMAT"


def test_extraction_limits_busy_timeout_and_ownership(resources, monkeypatch):
    client, _, identity, alice, bob = resources
    _, identifier = upload(client, "source.txt", "Text 🐈".encode())
    path = f"{API}/documents/{identifier}/extract-text"
    identity["user"] = bob
    assert client.post(path).status_code == 404
    identity["user"] = alice
    text_extraction._slot.acquire()
    try: assert client.post(path).status_code == 429
    finally: text_extraction._slot.release()
    monkeypatch.setattr(settings, "EXTRACT_MAX_CHARACTERS", 3)
    assert client.post(path).json()["detail"] == "ERR_TEXT_TOO_LARGE"
    def timeout(*args, **kwargs): raise subprocess.TimeoutExpired("parser", 15)
    monkeypatch.setattr(text_extraction.subprocess, "run", timeout)
    assert client.post(path).status_code == 504
    assert client.get(f"{API}/documents/{identifier}/download").status_code == 200


def test_history_pagination_and_deleted_source_without_ai(resources):
    client, engine, identity, alice, bob = resources
    notebook, identifier = upload(client, "source.txt", b"Original source")
    client.post(f"{API}/documents/{identifier}/extract-text")
    with Session(engine) as session:
        snapshot = [{"document_id": identifier, "version": 1, "source_title": "source.txt", "snippet": "Original",
                     "start_offset": 0, "end_offset": 8}]
        qa = QAHistory(notebook_id=uuid.UUID(notebook), question="Question?", answer="Saved answer", model_name="xlmroberta_qa", citation_snapshot=snapshot)
        summary = Summary(notebook_id=uuid.UUID(notebook), document_id=uuid.UUID(identifier), content="Saved summary", model_name="vit5",
                          model_version="old", pipeline_version="old", cache_key="test-history", status="succeeded", source_snapshot=snapshot)
        session.add_all([qa, summary]); session.commit(); session.refresh(qa); session.refresh(summary)
        qa_id, summary_id = str(qa.qahistory_id), str(summary.summary_id)
    path = f"{API}/notebooks/{notebook}/history"
    first = client.get(path + "?limit=1").json()
    assert len(first["items"]) == 1 and first["next_cursor"]
    second = client.get(path, params={"limit": 1, "cursor": first["next_cursor"]}).json()
    assert len(second["items"]) == 1 and second["next_cursor"] is None
    assert first["items"][0]["id"] != second["items"][0]["id"]
    assert client.get(path + "?cursor=invalid").status_code == 422
    assert client.get(f"{API}/qa-history/{qa_id}").json()["citations"][0]["source_state"] == "available"
    assert client.delete(f"{API}/documents/{identifier}").status_code == 204
    assert client.get(f"{API}/qa-history/{qa_id}").json()["citations"][0]["source_state"] == "missing"
    assert client.get(f"{API}/summary-history/{summary_id}").json()["content"] == "Saved summary"
    identity["user"] = bob
    assert client.get(path).status_code == 404
    assert client.get(f"{API}/qa-history/{qa_id}").status_code == 404
    assert client.get(f"{API}/summary-history/{summary_id}").status_code == 404


def test_paused_ai_job_does_not_prevent_manual_reading(resources):
    client, engine, _, alice, _ = resources
    notebook, identifier = upload(client, "source.txt", b"Readable without AI")
    with Session(engine) as session:
        document = session.get(Document, uuid.UUID(identifier)); document.requested_version = 1
        session.add(document)
        session.add(Job(user_id=alice.user_id, notebook_id=uuid.UUID(notebook), document_id=document.document_id,
                        kind="ingest", dedupe_key="paused-ingest", payload={"version": 1}))
        session.commit()
    result = client.post(f"{API}/documents/{identifier}/extract-text")
    assert result.status_code == 200 and result.json()["current_version"] == 2
    with Session(engine) as session:
        assert session.exec(select(Job)).one().status == "cancelled"
        assert session.get(Document, uuid.UUID(identifier)).status == "uploaded"
