import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from fastapi import HTTPException
from sqlmodel import Session, select
from backend.app.core.config import settings
from backend.app.models.models import Document, DocumentVersion, Job
from backend.app.services.storage import materialize
from backend.app.services.summary_service import lock_notebook

PARSER_VERSION = "lightweight-v1"
_slot = threading.BoundedSemaphore(1)


def parse(key, backend, suffix):
    if not _slot.acquire(blocking=False): raise HTTPException(429, "ERR_EXTRACTION_BUSY")
    try:
        with materialize(key, backend, suffix) as path, tempfile.TemporaryDirectory(prefix="documind-text-") as directory:
            if not path.is_file(): raise HTTPException(404, "ERR_SOURCE_MISSING")
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                while block := stream.read(1024 * 1024): digest.update(block)
            output = Path(directory) / "result.json"
            try:
                process = subprocess.run([sys.executable, "-m", "backend.processor.lightweight", str(path), str(output),
                    str(settings.EXTRACT_MAX_PAGES), str(settings.EXTRACT_MAX_CHARACTERS)],
                    cwd=Path(__file__).resolve().parents[3], capture_output=True,
                    timeout=settings.EXTRACT_TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired: raise HTTPException(504, "ERR_EXTRACTION_TIMEOUT") from None
            if process.returncode or not output.is_file(): raise HTTPException(422, "ERR_FILE_FORMAT")
            result = json.loads(output.read_text(encoding="utf-8"))
            if "error" in result: raise HTTPException(422, result["error"])
            return result, digest.hexdigest()
    except HTTPException: raise
    except ValueError as exc:
        if str(exc) == "ERR_FILE_TOO_LARGE": raise HTTPException(413, "ERR_FILE_TOO_LARGE") from None
        raise HTTPException(503, "ERR_STORAGE_UNAVAILABLE") from None
    except FileNotFoundError: raise HTTPException(404, "ERR_SOURCE_MISSING") from None
    except Exception: raise HTTPException(503, "ERR_STORAGE_UNAVAILABLE") from None
    finally: _slot.release()


def extract_document(session: Session, document: Document):
    identifier, notebook_id, expected = document.document_id, document.notebook_id, document.checksum
    if document.current_version:
        current = session.exec(select(DocumentVersion).where(DocumentVersion.document_id == identifier,
                                                            DocumentVersion.version == document.current_version)).first()
        if current:
            document.text_status, document.text_error_code = "ready", None
            session.add(document); session.commit(); session.refresh(document)
            return document
    key, backend, suffix = document.storage_key, document.storage_backend, Path(document.file_name).suffix.lower()
    if not key: raise HTTPException(404, "ERR_SOURCE_MISSING")
    session.rollback()  # No database transaction is held while parsing.
    try: result, actual = parse(key, backend, suffix)
    except HTTPException as exc:
        if exc.status_code != 429:
            lock_notebook(session, notebook_id)
            current = session.get(Document, identifier)
            if current and current.checksum == expected:
                current.text_status, current.text_error_code = "error", str(exc.detail)
                session.add(current); session.commit()
        raise
    lock_notebook(session, notebook_id)
    current = session.exec(select(Document).where(Document.document_id == identifier).with_for_update()
                           .execution_options(populate_existing=True)).first()
    if not current: raise HTTPException(404, "ERR_DOCUMENT_NOT_FOUND")
    if current.checksum != expected or actual != expected: raise HTTPException(409, "ERR_SOURCE_CHANGED")
    if session.exec(select(Job).where(Job.document_id == identifier, Job.status.in_(["queued", "running"]))).first():
        if settings.AI_ENABLED: raise HTTPException(409, "ERR_DOCUMENT_BUSY")
        from backend.app.services.job_service import job_service
        job_service.cancel(session, notebook_id, identifier)
        current.status, current.error_code = "uploaded", None
    if current.current_version:
        cached = session.exec(select(DocumentVersion).where(DocumentVersion.document_id == identifier,
                                                            DocumentVersion.version == current.current_version)).first()
        if cached: return current
    version = max(current.current_version, current.requested_version) + 1
    session.add(DocumentVersion(document_id=identifier, version=version, canonical_text=result["text"],
        sections=result["sections"], checksum=hashlib.sha256(result["text"].encode()).hexdigest(),
        pipeline_version=PARSER_VERSION + ":" + actual))
    current.current_version = current.requested_version = version
    current.text_status, current.text_error_code = "ready", None
    session.add(current); session.commit(); session.refresh(current)
    return current
