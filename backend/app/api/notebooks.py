from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
import uuid
from backend.app.core.db import get_session
from backend.app.models.models import Notebook

router = APIRouter()

@router.get("/", response_model=List[Notebook])
def read_notebooks(session: Session = Depends(get_session)):
    notebooks = session.exec(select(Notebook)).all()
    return notebooks

@router.post("/", response_model=Notebook)
def create_notebook(notebook: Notebook, session: Session = Depends(get_session)):
    session.add(notebook)
    session.commit()
    session.refresh(notebook)
    return notebook

@router.get("/{notebook_id}", response_model=Notebook)
def read_notebook(notebook_id: uuid.UUID, session: Session = Depends(get_session)):
    notebook = session.get(Notebook, notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="Notebook not found")
    return notebook
