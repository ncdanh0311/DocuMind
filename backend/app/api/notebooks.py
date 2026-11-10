import os
import logging
import shutil
import uuid
from fastapi import APIRouter, Depends, Response
from sqlalchemy import func
from sqlmodel import Session, select
from backend.app.api.deps import get_current_user, get_owned_notebook
from backend.app.core.db import get_session
from backend.app.models.models import Document, Notebook, User
from backend.app.schemas.schemas import (
    NotebookCreate, NotebookUpdate, NotebookResponse, ChatRequest, ChatResponse,
    NotebookSummarizeRequest, SummaryResponse,
)
from backend.app.services import rag_service
from backend.app.services.features import require_ai

router = APIRouter()
from backend.app.services.storage_quota import queue_cleanup, cleanup_pending

def notebook_response(notebook: Notebook, session: Session) -> NotebookResponse:
    count = session.exec(select(func.count()).select_from(Document).where(Document.notebook_id == notebook.notebook_id)).one()
    return NotebookResponse(**notebook.model_dump(), document_count=count)

@router.get("/", response_model=list[NotebookResponse])
def read_notebooks(session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    rows = session.exec(select(Notebook, func.count(Document.document_id)).outerjoin(Document)
        .where(Notebook.user_id == current_user.user_id).group_by(Notebook.notebook_id).order_by(Notebook.created_at.desc())).all()
    return [NotebookResponse(**notebook.model_dump(), document_count=count) for notebook, count in rows]

@router.post("/", response_model=NotebookResponse, status_code=201)
def create_notebook(notebook_in: NotebookCreate, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    notebook = Notebook(**notebook_in.model_dump(), user_id=current_user.user_id)
    session.add(notebook)
    session.commit()
    session.refresh(notebook)
    return notebook_response(notebook, session)

@router.get("/{notebook_id}", response_model=NotebookResponse)
def read_notebook(notebook: Notebook = Depends(get_owned_notebook), session: Session = Depends(get_session)):
    return notebook_response(notebook, session)

@router.delete("/{notebook_id}", status_code=204)
def delete_notebook(notebook: Notebook = Depends(get_owned_notebook), session: Session = Depends(get_session)):
    from backend.app.services.summary_service import lock_notebook
    from backend.app.services.job_service import job_service
    lock_notebook(session, notebook.notebook_id)
    job_service.cancel(session, notebook.notebook_id)
    for document in session.exec(select(Document).where(Document.notebook_id == notebook.notebook_id)).all():
        if document.storage_key: queue_cleanup(session, document.storage_backend, document.storage_key, document.file_size_bytes or 0)
    session.delete(notebook)
    session.commit()
    cleanup_pending(session)

@router.put("/{notebook_id}", response_model=NotebookResponse)
def update_notebook(notebook_in: NotebookUpdate, notebook: Notebook = Depends(get_owned_notebook), session: Session = Depends(get_session)):
    for key, value in notebook_in.model_dump(exclude_unset=True).items():
        if value is not None:
            setattr(notebook, key, value)
    session.add(notebook)
    session.commit()
    session.refresh(notebook)
    return notebook_response(notebook, session)

@router.post("/{notebook_id}/chat", response_model=ChatResponse)
def chat_with_notebook(request: ChatRequest, notebook: Notebook = Depends(get_owned_notebook), session: Session = Depends(get_session)):
    require_ai()
    return rag_service.answer_notebook_question(notebook_id=notebook.notebook_id, question=request.question, model=request.model, session=session)

@router.post("/{notebook_id}/summarize", response_model=SummaryResponse)
def summarize_notebook_endpoint(request: NotebookSummarizeRequest, response: Response, notebook: Notebook = Depends(get_owned_notebook), session: Session = Depends(get_session)):
    require_ai()
    from backend.app.services.summary_service import enqueue_summary
    result, response.status_code = enqueue_summary(session, notebook.notebook_id, request.model)
    return result
