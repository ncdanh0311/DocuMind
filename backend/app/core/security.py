import bcrypt
import sys
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Union
from jose import jwt
from backend.app.core.config import settings

def create_access_token(subject: Union[str, Any], expires_delta: timedelta = None) -> str:
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"exp": expire, "sub": str(subject), "type": "access"}
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def create_refresh_token(subject: Union[str, Any]) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode = {"exp": expire, "sub": str(subject), "type": "refresh"}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        # bcrypt yêu cầu dữ liệu dạng bytes
        password_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        # bcrypt.checkpw tự động xử lý salt từ hashed_bytes
        return bcrypt.checkpw(password_bytes[:72], hashed_bytes)
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    # bcrypt yêu cầu dữ liệu dạng bytes
    password_bytes = password.encode('utf-8')
    # Tạo salt và băm mật khẩu
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes[:72], salt)
    return hashed.decode('utf-8')
