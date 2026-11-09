"""PostgreSQL lease queue with fencing. Claim/heartbeat never hold inference transactions."""
from datetime import timedelta
import uuid
from sqlalchemy import and_, or_, update
from sqlmodel import Session, select
from backend.app.core.config import settings
from backend.app.core.security import utc_now, is_expired
from backend.app.models.models import Job, Document, Notebook, Summary

class LeaseLost(RuntimeError): pass

class PipelineError(RuntimeError):
    def __init__(self, code: str, retryable: bool = False):
        self.code, self.retryable = code, retryable
        super().__init__(code)

class JobService:
    def claim(self, session: Session) -> Job | None:
        now = utc_now()
        job = session.exec(select(Job).where(or_(
            and_(Job.status == "queued", Job.available_at <= now),
            and_(Job.status == "running", Job.lease_until <= now),
        )).order_by(Job.available_at, Job.created_at).with_for_update(skip_locked=True).limit(1)).first()
        if job is None: return None
        if job.attempt >= job.max_attempts:
            job.status, job.error_code = "failed", "ERR_JOB_ATTEMPTS_EXHAUSTED"
            job.lease_token, job.lease_until = None, None
            self._target_state(session, job, "failed")
            session.add(job); session.commit()
            return None
        job.status, job.attempt = "running", job.attempt + 1
        job.lease_token = uuid.uuid4()
        job.lease_until = now + timedelta(seconds=settings.JOB_LEASE_SECONDS)
        job.updated_at = now
        self._target_state(session, job, "running")
        session.add(job); session.commit(); session.refresh(job)
        # Detach claim identity before closing the short-lived session.
        session.expunge(job)
        return job

    def heartbeat(self, session: Session, claim: Job) -> bool:
        now = utc_now()
        result = session.exec(update(Job).where(Job.job_id == claim.job_id, Job.status == "running",
            Job.lease_token == claim.lease_token, Job.lease_until > now).values(
                lease_until=now + timedelta(seconds=settings.JOB_LEASE_SECONDS), updated_at=now))
        session.commit()
        return result.rowcount == 1

    def fenced(self, session: Session, claim: Job) -> Job:
        # Match the API's lock order: notebook -> job -> document.
        if claim.notebook_id:
            notebook = session.exec(select(Notebook).where(Notebook.notebook_id == claim.notebook_id).with_for_update()).first()
            if notebook is None: raise LeaseLost()
        job = session.exec(select(Job).where(Job.job_id == claim.job_id, Job.status == "running",
            Job.lease_token == claim.lease_token).with_for_update().execution_options(populate_existing=True)).first()
        if job is None or is_expired(job.lease_until): raise LeaseLost()
        return job

    def progress(self, session: Session, claim: Job, value: float) -> None:
        job = self.fenced(session, claim)
        job.progress, job.updated_at = min(0.99, max(0, value)), utc_now()
        session.add(job); session.commit()

    def fail(self, session: Session, claim: Job, error: PipelineError) -> None:
        job = self.fenced(session, claim)
        retry = error.retryable and job.attempt < job.max_attempts
        job.status = "queued" if retry else "failed"
        job.error_code, job.updated_at = error.code, utc_now()
        job.available_at = utc_now() + timedelta(seconds=10 if job.attempt == 1 else 30)
        job.lease_token, job.lease_until = None, None
        self._target_state(session, job, job.status)
        session.add(job); session.commit()

    def succeed(self, session: Session, job: Job) -> None:
        job.status, job.progress, job.error_code = "succeeded", 1, None
        job.lease_token, job.lease_until, job.updated_at = None, None, utc_now()
        session.add(job)

    def cancel(self, session: Session, notebook_id: uuid.UUID, document_id: uuid.UUID | None = None) -> None:
        statement = select(Job).where(Job.notebook_id == notebook_id, Job.status.in_(["queued", "running"]))
        if document_id: statement = statement.where(Job.document_id == document_id)
        for job in session.exec(statement.with_for_update()).all():
            job.status, job.error_code = "cancelled", "ERR_SOURCE_CHANGED"
            job.lease_token, job.lease_until, job.updated_at = None, None, utc_now()
            self._target_state(session, job, "cancelled")
            session.add(job)

    def _target_state(self, session: Session, job: Job, state: str) -> None:
        if job.kind == "ingest" and job.document_id:
            document = session.get(Document, job.document_id)
            if document and document.requested_version == job.payload.get("version"):
                document.status = {"queued": "uploaded", "running": "processing"}.get(state, "error")
                document.error_code = job.error_code
                session.add(document)
        if job.summary_id:
            summary = session.get(Summary, job.summary_id)
            if summary:
                summary.status, summary.error_code = state, job.error_code
                session.add(summary)

job_service = JobService()
