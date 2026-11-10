"""Ingestion preparation and atomic publication, guarded by a live job lease."""
import hashlib
import math
from pathlib import Path
from sqlmodel import Session, select
from backend.app.models.models import Document, DocumentChunk, DocumentVersion, Job, Notification
from backend.app.services.job_service import PipelineError, job_service
from backend.app.services.storage import materialize
from backend.processor.canonical import PIPELINE_VERSION
from backend.processor.document_processor import DocumentProcessor

class DocumentService:
    def __init__(self, engine, ai, processor_factory=DocumentProcessor):
        self.engine, self.ai, self.processor_factory = engine, ai, processor_factory

    def execute(self, claim: Job, check=lambda: None):
        with Session(self.engine) as session:
            document = session.get(Document, claim.document_id)
            if not document: raise PipelineError("ERR_SOURCE_MISSING")
            key = document.storage_key
            expected_checksum = document.checksum
            storage_backend = document.storage_backend
            suffix = Path(document.file_name).suffix
        if not key: raise PipelineError("ERR_SOURCE_MISSING")
        with materialize(key, storage_backend, suffix) as path:
            if not path.is_file(): raise PipelineError("ERR_SOURCE_MISSING")
            digest = hashlib.sha256()
            with path.open("rb") as stream:
                while data := stream.read(1024 * 1024): digest.update(data)
            if expected_checksum != digest.hexdigest(): raise PipelineError("ERR_SOURCE_CHANGED")
            check()
            canonical = self.processor_factory().extract(str(path))
        capability = self.ai.capability("embedding")
        chunks = canonical.chunks(lambda text: self.ai.split(text, "embedding", overlap=64))
        if not chunks: raise PipelineError("ERR_EMPTY_DOCUMENT")
        vectors = []
        for start in range(0, len(chunks), 16):
            check()
            batch = self.ai.embed([c["content"] for c in chunks[start:start + 16]], expected_version=capability["version"])
            if len(batch) != len(chunks[start:start + 16]) or any(len(v) != 384 or not all(math.isfinite(x) for x in v) for v in batch):
                raise PipelineError("ERR_EMBEDDING_SHAPE")
            vectors.extend(batch)
            with Session(self.engine) as session: job_service.progress(session, claim, 0.1 + 0.8 * len(vectors) / len(chunks))
        check()
        with Session(self.engine) as session:
            job = job_service.fenced(session, claim)
            document = session.exec(select(Document).where(Document.document_id == claim.document_id).with_for_update()).first()
            if not document or document.requested_version != claim.payload["version"] or document.checksum != expected_checksum:
                raise PipelineError("ERR_SOURCE_CHANGED")
            version = DocumentVersion(document_id=document.document_id, version=claim.payload["version"], canonical_text=canonical.text,
                sections=canonical.sections, checksum=canonical.checksum, pipeline_version=PIPELINE_VERSION)
            session.add(version)
            for chunk, vector in zip(chunks, vectors):
                session.add(DocumentChunk(document_id=document.document_id, version=version.version, embedding=vector,
                    embedding_model=capability["version"], **chunk))
            document.current_version, document.status, document.error_code = version.version, "ready", None
            document.text_status, document.text_error_code = "ready", None
            session.add(document)
            session.add(Notification(user_id=job.user_id, title="Tài liệu đã sẵn sàng", body=f"Đã xử lý {document.file_name}.", type="success"))
            job_service.succeed(session, job)
            session.commit()
