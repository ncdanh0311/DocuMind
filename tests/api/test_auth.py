from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
import uuid
from sqlalchemy import update
from sqlmodel import Session, select
from backend.app.core.security import create_token, credential_hash, utc_now
from backend.app.models.models import AuthSession, PasswordResetChallenge, User
from backend.app.api import auth
from tests.helpers import headers

BASE = "/api/v1/auth"

def login(client):
    result = client.post(BASE + "/login", json={"email": "alice@example.com", "password": "correct-password"})
    assert result.status_code == 200, result.text
    return result.json()

def reset_token(client, monkeypatch, email="alice@example.com"):
    sent = []
    async def send(address, code): sent.append((address, code))
    monkeypatch.setattr(auth, "send_reset_otp_email", send)
    response = client.post(BASE + "/forgot-password", json={"email": email})
    assert response.status_code == 200
    assert len(sent) == 1
    response = client.post(BASE + "/verify-otp", json={"email": email, "otp_code": sent[0][1]})
    assert response.status_code == 200, response.text
    return response.json()["reset_token"], sent[0][1]

def test_sessions_rotation_and_logout(client, account, db_engine):
    second = login(client)
    assert client.get(BASE + "/me", headers=headers(account)).status_code == 200
    assert client.get(BASE + "/me", headers=headers(second)).status_code == 200
    refreshed = client.post(BASE + "/refresh-token", json={"refresh_token": account["refresh_token"]})
    assert refreshed.status_code == 200
    assert refreshed.json()["refresh_token"] != account["refresh_token"]
    assert client.post(BASE + "/refresh-token", json={"refresh_token": account["refresh_token"]}).status_code == 401
    assert client.post(BASE + "/logout", headers=headers(refreshed.json())).status_code == 200
    assert client.get(BASE + "/me", headers=headers(account)).status_code == 401
    assert client.post(BASE + "/refresh-token", json={"refresh_token": refreshed.json()["refresh_token"]}).status_code == 401
    assert client.get(BASE + "/me", headers=headers(second)).status_code == 200
    with Session(db_engine) as session:
        hashes = [row.refresh_hash for row in session.exec(select(AuthSession)).all()]
        assert all(len(value) == 64 for value in hashes)
        assert account["refresh_token"] not in hashes

def test_refresh_is_atomic(client, account):
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: client.post(BASE + "/refresh-token", json={"refresh_token": account["refresh_token"]}).status_code, range(2)))
    assert sorted(results) == [200, 401]

def test_token_purpose_expiry_and_invalid_claims(client, account, monkeypatch):
    token, _ = reset_token(client, monkeypatch)
    for value in [account["refresh_token"], token, "bad-token"]:
        assert client.get(BASE + "/me", headers={"Authorization": "Bearer " + value}).status_code == 401
    for value in [account["access_token"], account["refresh_token"]]:
        assert client.post(BASE + "/reset-password", json={"token": value, "new_password": "new-password"}).status_code == 401
    assert client.post(BASE + "/refresh-token", json={"refresh_token": token}).status_code == 401
    from backend.app.core.security import decode_token
    payload = decode_token(account["access_token"], "access")
    expired = create_token(uuid.UUID(payload["sub"]), "access", uuid.UUID(payload["sid"]), timedelta(seconds=-1))
    assert client.get(BASE + "/me", headers={"Authorization": "Bearer " + expired}).status_code == 401
    assert client.get(BASE + "/me").status_code == 401

def test_reset_is_one_use_and_revokes_all_sessions(client, account, monkeypatch, db_engine):
    second = login(client)
    token, code = reset_token(client, monkeypatch)
    assert client.post(BASE + "/verify-otp", json={"email": "alice@example.com", "otp_code": code}).status_code == 400
    result = client.post(BASE + "/reset-password", json={"token": token, "new_password": "new-password"})
    assert result.status_code == 200, result.text
    for old in [account, second]:
        assert client.get(BASE + "/me", headers=headers(old)).status_code == 401
        assert client.post(BASE + "/refresh-token", json={"refresh_token": old["refresh_token"]}).status_code == 401
    assert client.get(BASE + "/me", headers=headers(result.json())).status_code == 200
    assert client.post(BASE + "/reset-password", json={"token": token, "new_password": "other-password"}).status_code == 401
    assert client.post(BASE + "/login", json={"email": "alice@example.com", "password": "new-password"}).status_code == 200
    with Session(db_engine) as session:
        challenge = session.exec(select(PasswordResetChallenge)).one()
        assert challenge.otp_hash != code
        assert challenge.reset_hash == credential_hash(token)
        assert challenge.used_at is not None

def test_password_change_requires_old_and_revokes_sessions(client, account):
    second = login(client)
    assert client.put(BASE + "/security", headers=headers(account), json={"new_password": "new-password"}).status_code == 422
    assert client.put(BASE + "/security", headers=headers(account), json={"old_password": "wrong", "new_password": "new-password"}).status_code == 400
    assert client.put(BASE + "/security", headers=headers(account), json={"old_password": "correct-password", "new_password": "new-password"}).status_code == 200
    for old in [account, second]:
        assert client.get(BASE + "/me", headers=headers(old)).status_code == 401

def test_otp_limits_expiry_and_generic_response(client, account, monkeypatch, db_engine):
    sent = []
    async def send(address, code): sent.append(code)
    monkeypatch.setattr(auth, "send_reset_otp_email", send)
    known = client.post(BASE + "/forgot-password", json={"email": "alice@example.com"})
    unknown = client.post(BASE + "/forgot-password", json={"email": "nobody@example.com"})
    again = client.post(BASE + "/forgot-password", json={"email": "alice@example.com"})
    assert known.json() == unknown.json() == again.json()
    assert len(sent) == 1
    wrong = "000000" if sent[0] != "000000" else "111111"
    for _ in range(5):
        assert client.post(BASE + "/verify-otp", json={"email": "alice@example.com", "otp_code": wrong}).status_code == 400
    assert client.post(BASE + "/verify-otp", json={"email": "alice@example.com", "otp_code": sent[0]}).status_code == 400
    with Session(db_engine) as session:
        row = session.exec(select(PasswordResetChallenge)).one()
        assert row.attempts == 5
        row.attempts = 0
        row.otp_expires_at = utc_now() - timedelta(seconds=1)
        session.add(row); session.commit()
    assert client.post(BASE + "/verify-otp", json={"email": "alice@example.com", "otp_code": sent[0]}).status_code == 400

def test_reset_token_database_expiry(client, account, monkeypatch, db_engine):
    token, _ = reset_token(client, monkeypatch)
    with Session(db_engine) as session:
        session.exec(update(PasswordResetChallenge).values(reset_expires_at=utc_now() - timedelta(seconds=1)))
        session.commit()
    assert client.post(BASE + "/reset-password", json={"token": token, "new_password": "new-password"}).status_code == 401

def test_password_validation_and_normalized_email(client):
    for password in ["short", "a"*73, "é"*37]:
        assert client.post(BASE + "/register", json={"email": "alice@example.com", "password": password}).status_code == 422
    data = {"email": "Alice@Example.com", "password": "valid-password"}
    assert client.post(BASE + "/register", json=data).status_code == 200
    data["email"] = "alice@example.com"
    assert client.post(BASE + "/register", json=data).status_code == 400


def test_resend_hourly_limits_are_persistent(client, account, monkeypatch, db_engine):
    from backend.app.services import auth_service
    from backend.app.models.models import AuthRateLimit
    sent = []
    async def send(address, code): sent.append(code)
    monkeypatch.setattr(auth, "send_reset_otp_email", send)
    now = utc_now()
    for attempt in range(6):
        monkeypatch.setattr(auth_service, "utc_now", lambda attempt=attempt: now + timedelta(seconds=61 * attempt))
        assert client.post(BASE + "/forgot-password", json={"email": "alice@example.com"}).status_code == 200
    assert len(sent) == 5
    with Session(db_engine) as session:
        assert all(bucket.count == 5 for bucket in session.exec(select(AuthRateLimit)).all())

def test_concurrent_reset_has_one_winner(client, account, monkeypatch):
    token, _ = reset_token(client, monkeypatch)
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: client.post(BASE + "/reset-password", json={"token": token, "new_password": "new-password"}).status_code, range(2)))
    assert sorted(results) == [200, 401]
