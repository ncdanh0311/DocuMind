import hashlib
import json
import uuid
from fastapi import HTTPException
from sqlmodel import Session, select
from backend.app.core.security import utc_now
from backend.app.models.models import Document, Job, Notebook, Summary
from backend.app.schemas.schemas import SummaryResponse
from backend.app.services.ai_client import ai_client
from backend.processor.canonical import PIPELINE_VERSION as CANONICAL_VERSION

PIPELINE_VERSION = CANONICAL_VERSION + "/hierarchical-v1"

ACTIVE = ("queued", "running")

def lock_notebook(session: Session, notebook_id: uuid.UUID) -> Notebook:
    notebook = session.exec(select(Notebook).where(Notebook.notebook_id == notebook_id).with_for_update().execution_options(populate_existing=True)).first()
    if not notebook: raise HTTPException(404, "ERR_NOTEBOOK_NOT_FOUND")
    return notebook

def source_snapshot(session: Session, notebook_id: uuid.UUID) -> list[dict]:
    docs = session.exec(select(Document).where(Document.notebook_id == notebook_id).order_by(Document.uploaded_at, Document.document_id)).all()
    if not docs: raise HTTPException(400, "ERR_NO_DOCUMENTS")
    if any(d.status != "ready" or d.current_version < 1 for d in docs): raise HTTPException(409, "ERR_DOCUMENTS_NOT_READY")
    return [{"document_id": str(d.document_id), "version": d.current_version, "checksum": d.checksum} for d in docs]

def snapshot_key(notebook_id, snapshot, model, model_version) -> str:
    payload = [str(notebook_id), snapshot, model, model_version, PIPELINE_VERSION]
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()

def summary_response(summary: Summary, job: Job, stale: bool = False) -> SummaryResponse:
    return SummaryResponse(summary_id=summary.summary_id, job_id=job.job_id, status=summary.status,
        summary=summary.content if summary.status == "succeeded" and not stale else None,
        model=summary.model_name, model_version=summary.model_version,
        coverage=summary.processed_units / summary.total_units if summary.total_units else 0,
        processed_units=summary.processed_units, total_units=summary.total_units,
        error_code="ERR_SOURCE_CHANGED" if stale else summary.error_code, stale=stale)

def enqueue_summary(session: Session, notebook_id: uuid.UUID, model: str) -> tuple[SummaryResponse, int]:
    capability = ai_client.capability(model)
    notebook = lock_notebook(session, notebook_id)
    snapshot = source_snapshot(session, notebook_id)
    key = snapshot_key(notebook_id, snapshot, model, capability["version"])
    summary = session.exec(select(Summary).where(Summary.cache_key == key)).first()
    if summary:
        job = session.exec(select(Job).where(Job.summary_id == summary.summary_id)).one()
        if summary.status in ("failed", "cancelled"):
            from backend.app.services.storage_quota import check_job_quota
            check_job_quota(session, notebook.user_id)
            job.status, job.attempt, job.progress, job.error_code = "queued", 0, 0, None
            job.available_at, job.updated_at = utc_now(), utc_now()
            job.lease_token, job.lease_until = None, None
            summary.content, summary.parts, summary.total_units = None, [], 0
            summary.status, summary.error_code, summary.processed_units = "queued", None, 0
            session.add(job); session.add(summary); session.commit()
        return summary_response(summary, job), 200 if summary.status == "succeeded" else 202
    from backend.app.services.storage_quota import check_job_quota
    check_job_quota(session, notebook.user_id)
    summary = Summary(notebook_id=notebook_id, content=None, model_name=model,
        model_version=capability["version"], pipeline_version=PIPELINE_VERSION, cache_key=key, source_snapshot=snapshot)
    session.add(summary); session.flush()
    job = Job(user_id=notebook.user_id, notebook_id=notebook_id, summary_id=summary.summary_id,
        kind="summarize", dedupe_key="summary:" + key,
        payload={"model": model, "model_version": capability["version"], "snapshot": snapshot})
    session.add(job); session.commit()
    return summary_response(summary, job), 202
