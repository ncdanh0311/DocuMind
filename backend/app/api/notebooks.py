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

import os
import shutil

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.uploads"))

@router.delete("/{notebook_id}", status_code=204)
def delete_notebook(
    notebook_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Xóa sổ tay cùng toàn bộ tài liệu vật lý và các bản ghi liên quan trong DB.
    """
    notebook = session.get(Notebook, notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="ERR_NOTEBOOK_NOT_FOUND")
    if notebook.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="ERR_NOTEBOOK_FORBIDDEN")

    # Xóa file vật lý trong .uploads/{notebook_id}
    notebook_upload_dir = os.path.join(UPLOAD_DIR, str(notebook_id))
    if os.path.exists(notebook_upload_dir):
        try:
            shutil.rmtree(notebook_upload_dir, ignore_errors=True)
        except Exception as e:
            print(f"Lỗi khi xóa thư mục tài liệu {notebook_upload_dir}: {e}")

    session.delete(notebook)
    session.commit()
    return None

from pydantic import BaseModel
from typing import Optional

class NotebookUpdate(BaseModel):
    title: Optional[str] = None
    is_private: Optional[bool] = None
    show_on_home: Optional[bool] = None
    icon_path: Optional[str] = None

@router.put("/{notebook_id}", response_model=Notebook)
def update_notebook(
    notebook_id: uuid.UUID,
    notebook_in: NotebookUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    notebook = session.get(Notebook, notebook_id)
    if not notebook:
        raise HTTPException(status_code=404, detail="ERR_NOTEBOOK_NOT_FOUND")
    if notebook.user_id != current_user.user_id:
        raise HTTPException(status_code=403, detail="ERR_NOTEBOOK_FORBIDDEN")

    if notebook_in.title is not None:
        notebook.title = notebook_in.title
    if notebook_in.is_private is not None:
        notebook.is_private = notebook_in.is_private
    if notebook_in.show_on_home is not None:
        notebook.show_on_home = notebook_in.show_on_home
    if notebook_in.icon_path is not None:
        notebook.icon_path = notebook_in.icon_path

    session.add(notebook)
    session.commit()
    session.refresh(notebook)
    return notebook


from backend.app.schemas.schemas import ChatRequest, ChatResponse, NotebookSummarizeRequest
from backend.app.services import rag_service

@router.post("/{notebook_id}/chat", response_model=ChatResponse)
def chat_with_notebook(
    *,
    notebook_id: uuid.UUID,
    request: ChatRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Hỏi đáp (QA) sử dụng mô hình PhoBERT kết hợp tìm kiếm ngữ nghĩa trên các tài liệu của sổ tay.
    """
    # 1. Kiểm tra quyền sở hữu sổ tay
    notebook = session.get(Notebook, notebook_id)
    if not notebook or notebook.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="ERR_NOTEBOOK_NOT_FOUND")

    # 2. Thực hiện toàn bộ logic RAG thông qua rag_service
    return rag_service.answer_notebook_question(
        notebook_id=notebook_id,
        question=request.question,
        model=request.model or "phobert_qa",
        session=session
    )


@router.post("/{notebook_id}/summarize")
def summarize_notebook_endpoint(
    *,
    notebook_id: uuid.UUID,
    request: NotebookSummarizeRequest = NotebookSummarizeRequest(model="vit5"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Tóm tắt nội dung chính của sổ tay sử dụng mô hình ViT5 hoặc BARTpho.
    """
    # 1. Kiểm tra quyền sở hữu sổ tay
    notebook = session.get(Notebook, notebook_id)
    if not notebook or notebook.user_id != current_user.user_id:
        raise HTTPException(status_code=404, detail="ERR_NOTEBOOK_NOT_FOUND")

    # 2. Thực hiện tóm tắt sổ tay qua rag_service
    summary = rag_service.summarize_notebook(
        notebook_id=notebook_id,
        model=request.model or "vit5",
        session=session
    )
    return {"summary": summary}


