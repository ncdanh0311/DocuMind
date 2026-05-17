from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
import uuid
from backend.app.core.db import get_session
from backend.app.models.models import Notebook, User
from backend.app.api.deps import get_current_user

router = APIRouter()

@router.get("/", response_model=List[Notebook])
def read_notebooks(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    notebooks = session.exec(
        select(Notebook).where(Notebook.user_id == current_user.user_id)
    ).all()
    return notebooks

@router.post("/", response_model=Notebook)
def create_notebook(
    *,
    session: Session = Depends(get_session),
    notebook_in: Notebook,
    current_user: User = Depends(get_current_user)
):
    notebook_in.user_id = current_user.user_id
    session.add(notebook_in)
    session.commit()
    session.refresh(notebook_in)
    return notebook_in

@router.get("/{notebook_id}", response_model=Notebook)
def read_notebook(notebook_id: uuid.UUID, session: Session = Depends(get_session)):
    notebook = session.get(Notebook, notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="ERR_NOTEBOOK_NOT_FOUND")
    return notebook
