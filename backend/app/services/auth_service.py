"""Database-backed sessions and reset challenges; callers own transaction boundaries."""
import hmac
import uuid
from datetime import timedelta
from fastapi import HTTPException
from sqlalchemy import update
from sqlalchemy.dialects.postgresql import insert
from sqlmodel import Session, select

from backend.app.core.config import settings
from backend.app.core.security import credential_hash, create_access_token, create_refresh_token, utc_now
from backend.app.models.models import AuthRateLimit, AuthSession, PasswordResetChallenge, User
from backend.app.schemas.schemas import Token

def lock_user(session: Session, user_id: uuid.UUID) -> User:
    user = session.exec(select(User).where(User.user_id == user_id).with_for_update().execution_options(populate_existing=True)).first()
    if user is None:
        raise HTTPException(401, "ERR_UNAUTHORIZED")
    return user

def issue_tokens(session: Session, user: User, auth_session: AuthSession | None = None) -> Token:
    now = utc_now()
    if auth_session is None:
        auth_session = AuthSession(user_id=user.user_id, refresh_hash="", expires_at=now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))
    refresh = create_refresh_token(user.user_id, auth_session.session_id)
    access = create_access_token(user.user_id, auth_session.session_id)
    auth_session.refresh_hash = credential_hash(refresh)
    auth_session.expires_at = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    session.add(auth_session)
    session.flush()
    return Token(user_id=str(user.user_id), access_token=access, refresh_token=refresh,
                 token_type="bearer", full_name=user.full_name, avatar_id=user.avatar_id)

def revoke_user_credentials(session: Session, user: User) -> None:
    now = utc_now()
    session.exec(update(AuthSession).where(AuthSession.user_id == user.user_id, AuthSession.revoked_at.is_(None)).values(revoked_at=now))
    session.exec(update(PasswordResetChallenge).where(PasswordResetChallenge.user_id == user.user_id, PasswordResetChallenge.used_at.is_(None)).values(used_at=now))

def same_hash(stored: str | None, value: str) -> bool:
    return bool(stored) and hmac.compare_digest(stored, credential_hash(value))

def consume_reset_rate_limit(session: Session, email: str, ip: str) -> bool:
    # Lock both buckets in deterministic order. Insert-on-conflict handles first-request races.
    now = utc_now()
    keys = sorted(credential_hash(f"reset-send:{kind}:{value}") for kind, value in (("email", email), ("ip", ip)))
    allowed = True
    for key in keys:
        session.exec(insert(AuthRateLimit).values(key=key, count=0, window_started_at=now, last_requested_at=now - timedelta(days=1)).on_conflict_do_nothing())
        bucket = session.exec(select(AuthRateLimit).where(AuthRateLimit.key == key).with_for_update()).one()
        if bucket.window_started_at <= now - timedelta(hours=1):
            bucket.window_started_at = now
            bucket.count = 0
        if bucket.last_requested_at > now - timedelta(seconds=settings.OTP_SEND_COOLDOWN_SECONDS) or bucket.count >= settings.OTP_SEND_HOURLY_LIMIT:
            allowed = False
    if allowed:
        for key in keys:
            bucket = session.get(AuthRateLimit, key)
            bucket.count += 1
            bucket.last_requested_at = now
            session.add(bucket)
    return allowed
