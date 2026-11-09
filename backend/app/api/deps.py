import uuid
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from sqlmodel import Session, select
from backend.app.core.config import settings
from backend.app.core.db import get_session
from backend.app.core.security import decode_token, is_expired
from backend.app.models.models import AuthSession, Document, Notebook, User

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login", auto_error=False)

def get_current_session(session: Session = Depends(get_session), token: str | None = Depends(reusable_oauth2)) -> AuthSession:
    if not token:
        raise HTTPException(401, "ERR_UNAUTHORIZED", headers={"WWW-Authenticate": "Bearer"})
    payload = decode_token(token, "access")
    auth_session = session.get(AuthSession, uuid.UUID(payload["sid"]))
    if (not auth_session or str(auth_session.user_id) != payload["sub"]
            or auth_session.revoked_at is not None or is_expired(auth_session.expires_at)):
        raise HTTPException(401, "ERR_SESSION_EXPIRED", headers={"WWW-Authenticate": "Bearer"})
    return auth_session

def get_current_user(session: Session = Depends(get_session), auth_session: AuthSession = Depends(get_current_session)) -> User:
    user = session.get(User, auth_session.user_id)
    if user is None:
        raise HTTPException(401, "ERR_UNAUTHORIZED")
    return user

def get_owned_notebook(notebook_id: uuid.UUID, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)) -> Notebook:
    notebook = session.exec(select(Notebook).where(Notebook.notebook_id == notebook_id, Notebook.user_id == current_user.user_id)).first()
    if notebook is None:
        raise HTTPException(404, "ERR_NOTEBOOK_NOT_FOUND")
    return notebook

def get_owned_document(document_id: uuid.UUID, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)) -> Document:
    document = session.exec(select(Document).join(Notebook).where(Document.document_id == document_id, Notebook.user_id == current_user.user_id)).first()
    if document is None:
        raise HTTPException(404, "ERR_DOC_NOT_FOUND")
    return document
