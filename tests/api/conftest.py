import os
from pathlib import Path
import pytest
from sqlalchemy.engine import make_url

# Never import application settings using a developer's real database/secret.
os.environ["SECRET_KEY"] = "phase1-test-0c4edc97d6ef483ca292d019f0da7b65"
os.environ["DATABASE_URL_OVERRIDE"] = os.environ.get("TEST_DATABASE_URL", "postgresql://postgres:phase1-test@127.0.0.1:55432/documind_phase1_test")
os.environ["DATABASE_DIRECT_URL"] = os.environ["DATABASE_URL_OVERRIDE"]
os.environ["STORAGE_BACKEND"] = "local"
os.environ["EMAIL_PROVIDER"] = "smtp"

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlmodel import Session, create_engine
from backend.app.core.db import get_session
from backend.app.models.models import SQLModel
from backend.main import app
import backend.main as main

@pytest.fixture(scope="session")
def db_engine():
    url = os.environ.get("TEST_DATABASE_URL")
    if not url:
        pytest.skip("Set TEST_DATABASE_URL to an isolated PostgreSQL/pgvector database ending in _test")
    parsed = make_url(url)
    if parsed.get_backend_name() != "postgresql" or not (parsed.database or "").endswith("_test"):
        pytest.fail("Refusing to modify a database not explicitly named *_test")
    engine = create_engine(url, pool_pre_ping=True, hide_parameters=True)
    config = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
    with engine.begin() as connection:
        config.attributes["connection"] = connection
        command.upgrade(config, "head")
        command.upgrade(config, "head")
    yield engine
    engine.dispose()

@pytest.fixture
def client(db_engine, monkeypatch, tmp_path):
    with db_engine.begin() as connection:
        names = ", ".join('"'+name+'"' for name in SQLModel.metadata.tables)
        connection.execute(text(f"TRUNCATE {names} CASCADE"))
    def get_test_session():
        with Session(db_engine) as session:
            yield session
    app.dependency_overrides[get_session] = get_test_session
    monkeypatch.setattr(main, "engine", db_engine)
    from backend.app.core.config import settings
    # Existing pipeline regression uses mock AI, never real models.
    monkeypatch.setattr(settings, "AI_ENABLED", True)
    monkeypatch.setattr(settings, "UPLOAD_DIR", str(tmp_path / "uploads"))
    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def account(client):
    response = client.post("/api/v1/auth/register", json={"email": "alice@example.com", "password": "correct-password", "full_name": "Alice"})
    assert response.status_code == 200, response.text
    return response.json()

def headers(tokens):
    return {"Authorization": "Bearer " + tokens["access_token"]}
