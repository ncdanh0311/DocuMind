from concurrent.futures import ThreadPoolExecutor
from fastapi import HTTPException
from sqlmodel import Session, select
from backend.app.core.config import settings
from backend.app.models.models import User, UploadReservation
from backend.app.services.storage_quota import reserve


def test_concurrent_reservations_cannot_exceed_global_quota(client, db_engine, account, monkeypatch):
    monkeypatch.setattr(settings, "MAX_TOTAL_STORAGE_BYTES", 10)
    import uuid
    user_id = uuid.UUID(account["user_id"])
    def upload(index):
        with Session(db_engine) as session:
            try:
                reserve(session, user_id, f"pending/{index}.txt", "local", 6)
                return 201
            except HTTPException as exc: return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(upload, range(2)))
    assert sorted(results) == [201, 413]
    with Session(db_engine) as session:
        assert len(session.exec(select(UploadReservation)).all()) == 1
