"""Stable newest-first keyset cursors, scoped by the calling endpoint."""
import base64
import json
import uuid
from datetime import datetime
from fastapi import HTTPException
from sqlalchemy import and_, or_


def encode_cursor(created_at, identifier):
    return base64.urlsafe_b64encode(json.dumps([created_at.isoformat(), str(identifier)]).encode()).decode()


def decode_cursor(value):
    try:
        if len(value) > 300: raise ValueError()
        created, identifier = json.loads(base64.b64decode(value, altchars=b"-_", validate=True))
        return datetime.fromisoformat(created), uuid.UUID(identifier)
    except Exception: raise HTTPException(422, "ERR_INVALID_CURSOR") from None


def after_cursor(created_column, id_column, value):
    created, identifier = decode_cursor(value)
    return or_(created_column < created, and_(created_column == created, id_column < identifier))
