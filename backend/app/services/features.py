from fastapi import HTTPException
from backend.app.core.config import settings

def require_ai():
    if not settings.AI_ENABLED:
        raise HTTPException(503, "ERR_AI_DISABLED")
