from pathlib import Path
import hashlib
import tempfile
import uuid
from urllib.parse import quote
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from pydantic import BaseModel, Field
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from backend.app.api.deps import get_current_user, get_owned_document, get_owned_notebook
from backend.app.core.config import settings
from backend.app.core.db import get_session
from backend.app.models.models import Document, DocumentChunk, DocumentVersion, Job, Notebook, User
from backend.app.schemas.schemas import DocumentChunkResponse, DocumentResponse, SourceResponse, DocumentRenameRequest
from backend.app.services.job_service import job_service
from backend.app.services.storage import get_storage
from backend.app.services.storage_quota import reserve, lock_ledger, queue_cleanup, cleanup_pending, usage, check_job_quota
from backend.app.models.models import UploadReservation
from backend.app.services.summary_service import lock_notebook
from backend.app.services.features import require_ai

router = APIRouter()

def document_response(document: Document, session: Session) -> DocumentResponse:
    job = session.exec(select(Job).where(Job.document_id == document.document_id, Job.kind == "ingest").order_by(Job.created_at.desc()).limit(1)).first()
    return DocumentResponse(**document.model_dump(), job_id=job.job_id if job else None)

def invalidate_summary_jobs(session, notebook_id):
    for job in session.exec(select(Job).where(Job.notebook_id == notebook_id, Job.kind == "summarize", Job.status.in_(["queued", "running"])).with_for_update()).all():
        job.status, job.error_code, job.lease_token, job.lease_until = "cancelled", "ERR_SOURCE_CHANGED", None, None
        if job.summary_id:
            from backend.app.models.models import Summary
            summary = session.get(Summary, job.summary_id)
            if summary: summary.status, summary.error_code = "cancelled", "ERR_SOURCE_CHANGED"; session.add(summary)
        session.add(job)

def enqueue_ingest(document: Document, notebook: Notebook, session: Session) -> Job | None:
    if not settings.AI_ENABLED:
        document.status, document.error_code = "uploaded", None
        invalidate_summary_jobs(session, notebook.notebook_id)
        session.add(document)
        return None
    document.requested_version += 1
    check_job_quota(session, notebook.user_id)
    document.status, document.error_code = "uploaded", None
    invalidate_summary_jobs(session, notebook.notebook_id)
    job = Job(user_id=notebook.user_id, notebook_id=notebook.notebook_id, document_id=document.document_id,
        kind="ingest", dedupe_key=f"ingest:{document.document_id}:{document.requested_version}", payload={"version": document.requested_version})
    session.add(document); session.add(job)
    return job


def save_upload(notebook_id, name, path, size, checksum, session, current_user):
    document = Document(notebook_id=notebook_id, file_name=name, file_size_bytes=size,
                        storage_backend=settings.STORAGE_BACKEND, checksum=checksum)
    key = f"{notebook_id}/{document.document_id}{Path(name).suffix.lower()}"
    document.storage_key = key
    reservation_id = reserve(session, current_user.user_id, key, document.storage_backend, size)
    try:
        get_storage(document.storage_backend).put_file(key, path)
        lock_ledger(session)
        notebook = lock_notebook(session, notebook_id)
        if notebook.user_id != current_user.user_id: raise HTTPException(404, "ERR_NOTEBOOK_NOT_FOUND")
        session.add(document); session.flush()
        enqueue_ingest(document, notebook, session)
        session.delete(session.get(UploadReservation, reservation_id))
        session.commit(); session.refresh(document)
        return document_response(document, session)
    except Exception as exc:
        session.rollback()
        # Persist cleanup before releasing quota. A dead process leaves a reservation for the ops sweep.
        queue_cleanup(session, document.storage_backend, key)
        reservation = session.get(UploadReservation, reservation_id)
        if reservation: session.delete(reservation)
        session.commit()
        cleanup_pending(session)
        if isinstance(exc, HTTPException): raise
        raise HTTPException(503, "ERR_STORAGE_UNAVAILABLE") from None

@router.post("/notebooks/{notebook_id}/documents/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(notebook_id: uuid.UUID, file: UploadFile = File(...), session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    get_owned_notebook(notebook_id, session, current_user)
    name = Path((file.filename or "").replace("\\", "/")).name
    extension = Path(name).suffix.lower()
    if extension not in (".pdf", ".docx", ".txt"): raise HTTPException(422, "ERR_FILE_FORMAT")
    size, digest = 0, hashlib.sha256()
    try:
        with tempfile.TemporaryDirectory(prefix="documind-upload-") as directory:
            path = Path(directory) / ("upload" + extension)
            with path.open("wb") as stream:
                while data := await file.read(1024 * 1024):
                    size += len(data)
                    if size > settings.MAX_UPLOAD_BYTES: raise HTTPException(413, "ERR_FILE_TOO_LARGE")
                    stream.write(data); digest.update(data)
            if size == 0: raise HTTPException(422, "ERR_EMPTY_DOCUMENT")
            with path.open("rb") as stream: signature = stream.read(5)
            if (extension == ".pdf" and signature != b"%PDF-") or (extension == ".docx" and not signature.startswith(b"PK")):
                raise HTTPException(422, "ERR_FILE_FORMAT")
            return save_upload(notebook_id, name, path, size, digest.hexdigest(), session, current_user)
    finally:
        await file.close()

class TextDocumentCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1, max_length=1000000)

@router.post("/notebooks/{notebook_id}/documents/text", response_model=DocumentResponse, status_code=201)
def create_document_from_text(notebook_id: uuid.UUID, request: TextDocumentCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    get_owned_notebook(notebook_id, session, current_user)
    if not request.title.strip() or not request.content.strip(): raise HTTPException(422, "ERR_EMPTY_DOCUMENT")
    title = request.title.strip()
    if not title.lower().endswith(".txt"): title += ".txt"
    with tempfile.TemporaryDirectory(prefix="documind-note-") as directory:
        path = Path(directory) / "note.txt"
        path.write_bytes(request.content.encode("utf-8"))
        return save_upload(notebook_id, title, path, path.stat().st_size,
                           hashlib.sha256(request.content.encode()).hexdigest(), session, current_user)

@router.post("/documents/{document_id}/reprocess", response_model=DocumentResponse, status_code=202)
def reprocess_document(document_id: uuid.UUID, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    document = get_owned_document(document_id, session, current_user)
    require_ai()
    notebook = lock_notebook(session, document.notebook_id)
    session.refresh(document)
    active = session.exec(select(Job).where(Job.document_id == document_id, Job.kind == "ingest", Job.status.in_(["queued", "running"]))).first()
    if not active:
        if not document.storage_key: document.storage_key = f"{document.notebook_id}/{document.document_id}{Path(document.file_name).suffix.lower()}"
        storage = get_storage(document.storage_backend)
        if not storage.exists(document.storage_key): raise HTTPException(404, "ERR_SOURCE_MISSING")
        digest = hashlib.sha256()
        with storage.open(document.storage_key) as stream:
            while block := stream.read(1024 * 1024): digest.update(block)
        document.checksum = digest.hexdigest()
        enqueue_ingest(document, notebook, session); session.commit(); session.refresh(document)
    return document_response(document, session)

@router.patch("/documents/{document_id}", response_model=DocumentResponse)
def rename_document(document_id: uuid.UUID, request: DocumentRenameRequest, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    document = get_owned_document(document_id, session, current_user)
    lock_notebook(session, document.notebook_id)
    session.refresh(document)
    document.file_name = request.title + Path(document.file_name).suffix
    session.add(document); session.commit(); session.refresh(document)
    return document_response(document, session)

@router.get("/notebooks/{notebook_id}/documents", response_model=list[DocumentResponse])
def list_documents(notebook_id: uuid.UUID, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    get_owned_notebook(notebook_id, session, current_user)
    return [document_response(d, session) for d in session.exec(select(Document).where(Document.notebook_id == notebook_id).order_by(Document.uploaded_at.desc())).all()]

@router.get("/documents/recent", response_model=list[DocumentResponse])
def get_recent_documents(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    return [document_response(d, session) for d in session.exec(select(Document).join(Notebook).where(Notebook.user_id == current_user.user_id).order_by(Document.uploaded_at.desc()).limit(5)).all()]

@router.delete("/documents/{document_id}", status_code=204)
def delete_document(document_id: uuid.UUID, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    document = get_owned_document(document_id, session, current_user)
    lock_notebook(session, document.notebook_id)
    job_service.cancel(session, document.notebook_id, document_id)
    invalidate_summary_jobs(session, document.notebook_id)
    key = document.storage_key or f"{document.notebook_id}/{document.document_id}{Path(document.file_name).suffix.lower()}"
    queue_cleanup(session, document.storage_backend, key)
    session.delete(document); session.commit()
    cleanup_pending(session)


@router.get("/storage/usage")
def storage_usage(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    used = usage(session, current_user.user_id)
    return {"used_bytes": used, "limit_bytes": settings.MAX_USER_STORAGE_BYTES,
            "max_file_bytes": settings.MAX_UPLOAD_BYTES}


@router.get("/documents/{document_id}/download")
def download_document(document_id: uuid.UUID, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    document = get_owned_document(document_id, session, current_user)
    if not document.storage_key: raise HTTPException(404, "ERR_SOURCE_MISSING")
    try:
        storage = get_storage(document.storage_backend)
        if not storage.exists(document.storage_key): raise HTTPException(404, "ERR_SOURCE_MISSING")
        body = storage.open(document.storage_key)
    except HTTPException: raise
    except Exception: raise HTTPException(503, "ERR_STORAGE_UNAVAILABLE") from None
    def content():
        try:
            while block := body.read(64 * 1024): yield block
        finally: body.close()
    return StreamingResponse(content(), media_type="application/octet-stream", headers={
        "Content-Disposition": "attachment; filename*=UTF-8''" + quote(document.file_name, safe=""),
        "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})

@router.get("/documents/{document_id}/chunks", response_model=list[DocumentChunkResponse])
def get_document_chunks(document_id: uuid.UUID, version: int | None = Query(default=None, ge=1), session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    document = get_owned_document(document_id, session, current_user)
    if (version or document.current_version) < 1: return []
    return session.exec(select(DocumentChunk).where(DocumentChunk.document_id == document_id, DocumentChunk.version == (version or document.current_version)).order_by(DocumentChunk.global_index)).all()

@router.get("/documents/{document_id}/source", response_model=SourceResponse)
def get_document_source(document_id: uuid.UUID, version: int | None = Query(default=None, ge=1), start: int = Query(default=0, ge=0), end: int | None = Query(default=None, ge=0), session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    document = get_owned_document(document_id, session, current_user)
    source = session.exec(select(DocumentVersion).where(DocumentVersion.document_id == document_id, DocumentVersion.version == (version or document.current_version))).first()
    if source is None: raise HTTPException(404, "ERR_SOURCE_NOT_READY")
    end = len(source.canonical_text) if end is None else end
    if not 0 <= start <= end <= len(source.canonical_text): raise HTTPException(422, "ERR_INVALID_SOURCE_RANGE")
    return SourceResponse(document_id=document_id, version=source.version, start_offset=start, end_offset=end,
        text=source.canonical_text[start:end], sections=[s for s in source.sections if s["start"] < end and s["end"] > start])
