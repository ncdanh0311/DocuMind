from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import hashlib
import uuid
import pytest
from fastapi import HTTPException
from sqlmodel import Session, select
from backend.app.core.security import utc_now
from backend.app.models.models import Document, DocumentChunk, DocumentVersion, Job, Summary
from backend.app.services.job_service import JobService, LeaseLost, PipelineError
from backend.app.services.document_service import DocumentService
from backend.app.services.summary_worker import SummaryWorker
from backend.app.services import summary_service
from backend.processor.canonical import PIPELINE_VERSION
from tests.helpers import headers

API = "/api/v1"

class FakeAI:
    def __init__(self): self.seen = []; self.fail = False
    def capability(self, model): return {"id": model, "ready": True, "version": "test-model-v1", "max_input_tokens": 128}
    def split(self, text, model, overlap=0):
        from ai.runtime.text import split_to_budget
        return split_to_budget(text, len, 100, min(overlap, 20))
    def embed(self, texts, is_query=False, expected_version=None):
        assert len(texts) <= 16
        if self.fail: raise HTTPException(504, "ERR_AI_TIMEOUT")
        return [[1.0] + [0.0] * 383 for _ in texts]
    def request(self, path, payload):
        assert path == "/summarize"
        self.seen.append(payload["text"])
        return {"summary": payload["text"][:20], "model_version": "test-model-v1"}


def upload(client, account, content="Tiếng Việt 🐈\n" * 90):
    auth = headers(account)
    notebook = client.post(API + "/notebooks/", headers=auth, json={"title": "Pipeline"}).json()
    response = client.post(f"{API}/notebooks/{notebook['notebook_id']}/documents/text", headers=auth,
        json={"title": "Source", "content": content})
    assert response.status_code == 201, response.text
    return notebook["notebook_id"], response.json()


def test_claim_concurrency_and_fencing_after_expired_lease(client, account, db_engine):
    _, doc = upload(client, account)
    queue = JobService()
    def claim():
        with Session(db_engine) as session: return queue.claim(session)
    with ThreadPoolExecutor(max_workers=2) as pool: claims = list(pool.map(lambda _: claim(), range(2)))
    assert sum(c is not None for c in claims) == 1
    old = next(c for c in claims if c)
    with Session(db_engine) as session:
        job = session.get(Job, old.job_id); job.lease_until = utc_now() - timedelta(seconds=1)
        session.add(job); session.commit()
    new = claim()
    assert new.attempt == 2 and new.lease_token != old.lease_token
    with Session(db_engine) as session:
        assert not queue.heartbeat(session, old)
        with pytest.raises(LeaseLost): queue.fenced(session, old)
    with Session(db_engine) as session:
        assert queue.heartbeat(session, new)


def test_retry_backoff_and_exhaustion(client, account, db_engine):
    upload(client, account)
    queue = JobService()
    for attempt in range(1, 4):
        with Session(db_engine) as session: claim = queue.claim(session)
        assert claim.attempt == attempt
        with Session(db_engine) as session:
            queue.fail(session, claim, PipelineError("ERR_AI_TIMEOUT", retryable=True))
        with Session(db_engine) as session:
            job = session.get(Job, claim.job_id)
            assert job.status == ("failed" if attempt == 3 else "queued")
            if attempt < 3:
                assert job.available_at > utc_now() + timedelta(seconds=8 if attempt == 1 else 28)
                job.available_at = utc_now() - timedelta(seconds=1); session.add(job); session.commit()


def test_atomic_ingestion_source_ranges_summary_cache_and_staleness(client, account, db_engine, monkeypatch):
    raw = "Tiếng Việt 🐈\n" * 90 + "PHẦN CUỐI: kết luận độc nhất."
    notebook_id, doc = upload(client, account, raw)
    fake = FakeAI(); monkeypatch.setattr(summary_service, "ai_client", fake)
    with Session(db_engine) as session: claim = JobService().claim(session)
    DocumentService(db_engine, fake).execute(claim)
    response = client.get(f"{API}/documents/{doc['document_id']}/source?start=0&end=12", headers=headers(account))
    assert response.status_code == 200, response.text
    assert response.json()["text"] == raw[:12]
    chunks = client.get(f"{API}/documents/{doc['document_id']}/chunks", headers=headers(account)).json()
    assert len(chunks) > 10
    assert all(raw[c["start_offset"]:c["end_offset"]] == c["content"] and c["page_number"] is None for c in chunks)
    endpoint = f"{API}/notebooks/{notebook_id}/summarize"
    first = client.post(endpoint, headers=headers(account), json={"model": "vit5"})
    assert first.status_code == 202, first.text
    again = client.post(endpoint, headers=headers(account), json={"model": "vit5"})
    assert first.json()["job_id"] == again.json()["job_id"]
    with Session(db_engine) as session: summary_claim = JobService().claim(session)
    SummaryWorker(db_engine, fake).execute(summary_claim)
    completed = client.get(f"{API}/summaries/{first.json()['summary_id']}", headers=headers(account))
    assert completed.json()["coverage"] == 1 and completed.json()["status"] == "succeeded", completed.text
    assert raw in "".join(fake.seen)  # Every character reaches inference, including the unique tail.
    assert client.post(endpoint, headers=headers(account), json={"model": "vit5"}).status_code == 200
    bob = client.post(API + "/auth/register", json={"email": "bob@example.com", "password": "correct-password"}).json()
    for path in (f"/jobs/{summary_claim.job_id}", f"/summaries/{first.json()['summary_id']}", f"/documents/{doc['document_id']}/source"):
        assert client.get(API + path, headers=headers(bob)).status_code == 404
    client.post(f"{API}/documents/{doc['document_id']}/reprocess", headers=headers(account))
    stale = client.get(f"{API}/summaries/{first.json()['summary_id']}", headers=headers(account)).json()
    assert stale["stale"] and stale["summary"] is None
    assert client.post(endpoint, headers=headers(account), json={"model": "vit5"}).status_code == 409


def test_deleted_source_fences_worker_and_rejects_publication(client, account, db_engine):
    _, doc = upload(client, account)
    with Session(db_engine) as session: claim = JobService().claim(session)
    assert client.delete(f"{API}/documents/{doc['document_id']}", headers=headers(account)).status_code == 204
    with Session(db_engine) as session:
        with pytest.raises(LeaseLost): JobService().fenced(session, claim)
        assert session.get(Job, claim.job_id).status == "cancelled"
        assert not session.exec(select(DocumentChunk)).all()


def test_failure_does_not_publish_partial_chunks(client, account, db_engine):
    _, doc = upload(client, account)
    fake = FakeAI(); fake.fail = True
    with Session(db_engine) as session: claim = JobService().claim(session)
    with pytest.raises(HTTPException): DocumentService(db_engine, fake).execute(claim)
    with Session(db_engine) as session:
        assert not session.exec(select(DocumentChunk)).all()
        assert not session.exec(select(DocumentVersion)).all()
        assert session.get(Document, uuid.UUID(doc["document_id"])).current_version == 0


@pytest.mark.parametrize("mode", ["answered", "no_answer", "forged_span", "changed_source"])
def test_qa_exact_spans_abstention_and_source_changes(client, account, db_engine, monkeypatch, mode):
    from backend.app.services import rag_service
    from backend.app.models.models import QAHistory
    text = "Thủ đô Việt Nam là Hà Nội."
    notebook_id, doc = upload(client, account, text)
    fake = FakeAI()
    with Session(db_engine) as session: claim = JobService().claim(session)
    DocumentService(db_engine, fake).execute(claim)
    def request(path, payload):
        if path == "/rerank": return {"results": [{"index": 0, "score": 7.0}]}
        assert path == "/qa"
        passage = payload["passages"][0]
        if mode == "changed_source":
            with Session(db_engine) as session:
                document = session.get(Document, uuid.UUID(doc["document_id"])); document.status = "processing"
                session.add(document); session.commit()
        start = passage["content"].index("Hà Nội")
        return {"status": "no_answer" if mode == "no_answer" else "answered", "model_version": "test-model-v1",
            "chunk_id": "forged" if mode == "forged_span" else passage["chunk_id"], "start": start, "end": start + 6, "answer": "Hà Nội"}
    fake.request = request
    import importlib
    monkeypatch.setattr(importlib.import_module("backend.app.services.rag_service"), "ai_client", fake)
    response = client.post(f"{API}/notebooks/{notebook_id}/chat", headers=headers(account), json={"question": "Thủ đô ở đâu?", "model": "phobert_qa"})
    if mode == "forged_span": assert response.status_code == 502
    elif mode == "changed_source": assert response.status_code == 409
    else:
        assert response.status_code == 200, response.text
        result = response.json()
        assert result["status"] == mode
        if mode == "no_answer": assert result["citations"] == [] and result["sources"] == []
        else:
            citation = result["citations"][0]
            source = client.get(f"{API}/documents/{citation['document_id']}/source", headers=headers(account),
                params={"version": citation["version"], "start": citation["start_offset"], "end": citation["end_offset"]})
            assert source.json()["text"] == "Hà Nội"
        with Session(db_engine) as session:
            assert session.exec(select(QAHistory)).one().model_version == "test-model-v1"


def test_worker_records_transient_failure_and_timeout(client, account, db_engine, monkeypatch):
    from backend.worker import run_once
    from backend.app.core.config import settings
    _, doc = upload(client, account)
    fake = FakeAI(); fake.fail = True
    assert run_once(db_engine, fake)
    with Session(db_engine) as session:
        job = session.get(Job, uuid.UUID(doc["job_id"]))
        assert job.status == "queued" and job.error_code == "ERR_AI_TIMEOUT"
        job.available_at = utc_now() - timedelta(seconds=1); session.add(job); session.commit()
    monkeypatch.setattr(settings, "JOB_MAX_SECONDS", 0)
    assert run_once(db_engine, fake)
    with Session(db_engine) as session:
        job = session.get(Job, uuid.UUID(doc["job_id"]))
        assert job.status == "failed" and job.error_code == "ERR_JOB_TIMEOUT"


def test_database_transactions_close_during_model_calls(client, account, db_engine, monkeypatch):
    notebook_id, doc = upload(client, account)
    fake = FakeAI()
    original_embed, original_request = fake.embed, fake.request
    def embed(*args, **kwargs):
        assert db_engine.pool.checkedout() == 0
        return original_embed(*args, **kwargs)
    def request(*args, **kwargs):
        assert db_engine.pool.checkedout() == 0
        return original_request(*args, **kwargs)
    fake.embed, fake.request = embed, request
    monkeypatch.setattr(summary_service, "ai_client", fake)
    with Session(db_engine) as session: claim = JobService().claim(session)
    DocumentService(db_engine, fake).execute(claim)
    result = client.post(f"{API}/notebooks/{notebook_id}/summarize", headers=headers(account), json={"model": "vit5"})
    assert result.status_code == 202
    with Session(db_engine) as session: claim = JobService().claim(session)
    SummaryWorker(db_engine, fake).execute(claim)


def test_delete_during_inference_prevents_old_worker_publication(client, account, db_engine):
    _, doc = upload(client, account)
    fake = FakeAI(); original = fake.embed
    def embed(*args, **kwargs):
        result = original(*args, **kwargs)
        assert client.delete(f"{API}/documents/{doc['document_id']}", headers=headers(account)).status_code == 204
        return result
    fake.embed = embed
    with Session(db_engine) as session: claim = JobService().claim(session)
    with pytest.raises(LeaseLost): DocumentService(db_engine, fake).execute(claim)
    with Session(db_engine) as session:
        assert session.get(Job, claim.job_id).status == "cancelled"
        assert not session.exec(select(DocumentChunk)).all()
        assert not session.exec(select(DocumentVersion)).all()
