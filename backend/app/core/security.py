"""Purpose-bound credentials. Only hashes of refresh/reset credentials are persisted."""
import hashlib
import hmac
import uuid
from datetime import datetime, timedelta, timezone
from typing import Literal

import bcrypt
from fastapi import HTTPException
from jose import JWTError, jwt
from backend.app.core.config import settings

TokenPurpose = Literal["access", "refresh", "password_reset"]

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

def is_expired(value: datetime | None) -> bool:
    if value is None:
        return True
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value <= utc_now()

def credential_hash(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()

def otp_hash(challenge_id: uuid.UUID, code: str) -> str:
    return hmac.new(settings.SECRET_KEY.encode(), f"otp:{challenge_id}:{code}".encode(), hashlib.sha256).hexdigest()

def create_token(subject: uuid.UUID, purpose: TokenPurpose, binding_id: uuid.UUID, lifetime: timedelta) -> str:
    return jwt.encode({
        "sub": str(subject), "sid": str(binding_id), "jti": str(uuid.uuid4()),
        "type": purpose, "exp": utc_now() + lifetime,
    }, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_access_token(subject: uuid.UUID, session_id: uuid.UUID) -> str:
    return create_token(subject, "access", session_id, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))

def create_refresh_token(subject: uuid.UUID, session_id: uuid.UUID) -> str:
    return create_token(subject, "refresh", session_id, timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS))

def decode_token(token: str, purpose: TokenPurpose) -> dict:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM],
                             options={"require_exp": True, "require_sub": True})
        if payload.get("type") != purpose:
            raise ValueError("Incorrect purpose")
        for key in ("sub", "sid", "jti"):
            uuid.UUID(payload[key])
        return payload
    except (JWTError, ValueError, TypeError, KeyError, AttributeError):
        raise HTTPException(401, "ERR_TOKEN_INVALID", headers={"WWW-Authenticate": "Bearer"}) from None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    password_bytes = plain_password.encode("utf-8")
    if len(password_bytes) > 72:
        return False
    try:
        return bcrypt.checkpw(password_bytes, hashed_password.encode("utf-8"))
    except (ValueError, TypeError):
        return False

def get_password_hash(password: str) -> str:
    password_bytes = password.encode("utf-8")
    if len(password) < 8 or len(password_bytes) > 72:
        raise ValueError("Password must contain at least 8 characters and at most 72 UTF-8 bytes")
    return bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode("utf-8")
