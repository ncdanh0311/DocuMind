"""Serialized quota reservations; object transfers happen outside DB locks."""
import uuid
from fastapi import HTTPException
from sqlalchemy import func
from sqlmodel import Session, select
from backend.app.core.config import settings
from backend.app.models.models import Document, Notebook, StorageLedger, UploadReservation, StorageCleanupTask


def lock_ledger(session: Session):
    dialect = session.get_bind().dialect.name
    if dialect == "postgresql":
        from sqlalchemy.dialects.postgresql import insert
    elif dialect == "sqlite":
        from sqlalchemy.dialects.sqlite import insert
    else: raise RuntimeError("ERR_DATABASE_BACKEND")
    session.exec(insert(StorageLedger).values(ledger_id=1).on_conflict_do_nothing())
    return session.exec(select(StorageLedger).where(StorageLedger.ledger_id == 1).with_for_update()).one()


def usage(session: Session, user_id=None):
    docs = select(func.coalesce(func.sum(Document.file_size_bytes), 0)).select_from(Document).join(Notebook)
    reservations = select(func.coalesce(func.sum(UploadReservation.size_bytes), 0))
    if user_id:
        docs = docs.where(Notebook.user_id == user_id)
        reservations = reservations.where(UploadReservation.user_id == user_id)
    pending_delete = 0 if user_id else int(session.exec(select(func.coalesce(func.sum(StorageCleanupTask.size_bytes), 0))).one())
    return int(session.exec(docs).one()) + int(session.exec(reservations).one()) + pending_delete


def reserve(session: Session, user_id: uuid.UUID, key: str, backend: str, size: int):
    lock_ledger(session)
    if session.exec(select(Document.document_id).where(Document.file_size_bytes.is_(None)).limit(1)).first():
        raise HTTPException(409, "ERR_STORAGE_RECONCILE_REQUIRED")
    if size > settings.MAX_UPLOAD_BYTES: raise HTTPException(413, "ERR_FILE_TOO_LARGE")
    if usage(session, user_id) + size > settings.MAX_USER_STORAGE_BYTES:
        raise HTTPException(413, "ERR_USER_STORAGE_QUOTA")
    if usage(session) + size > settings.MAX_TOTAL_STORAGE_BYTES:
        raise HTTPException(413, "ERR_TOTAL_STORAGE_QUOTA")
    row = UploadReservation(user_id=user_id, storage_key=key, storage_backend=backend, size_bytes=size)
    session.add(row); session.commit(); session.refresh(row)
    return row.reservation_id


def queue_cleanup(session: Session, backend: str, key: str, size: int = 0):
    found = session.exec(select(StorageCleanupTask).where(StorageCleanupTask.storage_backend == backend,
                                                         StorageCleanupTask.storage_key == key)).first()
    if not found: session.add(StorageCleanupTask(storage_backend=backend, storage_key=key, size_bytes=size))
    elif size > found.size_bytes:
        found.size_bytes = size; session.add(found)


def cleanup_pending(session: Session, limit=100):
    from backend.app.services.storage import get_storage
    succeeded = failed = 0
    for row in session.exec(select(StorageCleanupTask).order_by(StorageCleanupTask.created_at).limit(limit)).all():
        try: get_storage(row.storage_backend).delete(row.storage_key)
        except Exception:
            row.attempts += 1; session.add(row); failed += 1
        else:
            session.delete(row); succeeded += 1
        session.commit()
    return {"deleted": succeeded, "failed": failed}


def check_job_quota(session: Session, user_id):
    from backend.app.models.models import User, Job
    session.exec(select(User).where(User.user_id == user_id).with_for_update()).one()
    count = session.exec(select(func.count()).select_from(Job).where(Job.user_id == user_id,
                            Job.status.in_(["queued", "running"]))).one()
    if count >= settings.MAX_ACTIVE_JOBS_PER_USER: raise HTTPException(429, "ERR_JOB_QUOTA")
