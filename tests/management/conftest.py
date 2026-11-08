"""Lightweight resource tests: SQLite, no Docker, network or model inference."""
import os
os.environ.setdefault("SECRET_KEY", "management-test-0c4edc97d6ef483ca292d019f0da7b65")
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import event
from sqlalchemy.pool import StaticPool
from sqlmodel import Session, SQLModel, create_engine
from backend.main import app
from backend.app.api.deps import get_current_user
from backend.app.core.db import get_session
from backend.app.core.config import settings
from backend.app.models.models import User
from backend.app.services.ai_client import ai_client

@pytest.fixture
def resources(monkeypatch, tmp_path):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    @event.listens_for(engine, "connect")
    def foreign_keys(connection, _): connection.execute("PRAGMA foreign_keys=ON")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        alice = User(email="alice@example.com", hashed_password="test-only")
        bob = User(email="bob@example.com", hashed_password="test-only")
        session.add_all([alice, bob]); session.commit(); session.refresh(alice); session.refresh(bob)
        session.expunge(alice); session.expunge(bob)
    identity = {"user": alice}
    def sessions():
        with Session(engine) as session: yield session
    app.dependency_overrides[get_session] = sessions
    app.dependency_overrides[get_current_user] = lambda: identity["user"]
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    monkeypatch.setattr(settings, "AI_ENABLED", False)
    def forbidden(*args, **kwargs): raise AssertionError("AI must not be called in storage-only mode")
    monkeypatch.setattr(ai_client, "request", forbidden)
    with TestClient(app) as client:
        yield client, engine, identity, alice, bob
    app.dependency_overrides.clear(); engine.dispose()
