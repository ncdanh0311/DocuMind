import os
import shutil
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlmodel import Session, select

from backend.app.core.db import get_session
from backend.app.models.models import Document, Notebook, User
from backend.app.api.deps import get_current_user

router = APIRouter()

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.uploads"))

@router.post("/notebooks/{notebook_id}/documents/upload", response_model=Document, status_code=status.HTTP_201_CREATED)
async def upload_document(
    notebook_id: uuid.UUID,
    file: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Tải file (PDF, DOCX, TXT) lên một sổ tay cụ thể.
    """
    # 1. Kiểm tra quyền sở hữu sổ tay
    notebook = session.get(Notebook, notebook_id)
    if not notebook or notebook.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ERR_NOTEBOOK_NOT_FOUND"
        )

    # 2. Tạo bản ghi Document trước để lấy document_id chuẩn xác
    doc_id = uuid.uuid4()
    db_document = Document(
        document_id=doc_id,
        notebook_id=notebook_id,
        file_name=file.filename,
        status="uploaded"
    )

    # 3. Tạo thư mục lưu trữ nếu chưa có: .uploads/{notebook_id}/
    notebook_upload_dir = os.path.join(UPLOAD_DIR, str(notebook_id))
    os.makedirs(notebook_upload_dir, exist_ok=True)

    # 4. Lưu file vật lý với tên chính là document_id (ví dụ: c8b1a...pdf)
    file_ext = os.path.splitext(file.filename)[1].lower()
    physical_file_name = f"{doc_id}{file_ext}"
    file_path = os.path.join(notebook_upload_dir, physical_file_name)

    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Lỗi khi lưu file: {str(e)}"
        )

    # 5. Lưu thông tin vào Database
    session.add(db_document)
    session.commit()
    session.refresh(db_document)

    return db_document


@router.get("/notebooks/{notebook_id}/documents", response_model=List[Document])
def list_documents(
    notebook_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Lấy danh sách các tài liệu trong một sổ tay.
    """
    notebook = session.get(Notebook, notebook_id)
    if not notebook or notebook.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ERR_NOTEBOOK_NOT_FOUND"
        )

    documents = session.exec(
        select(Document)
        .where(Document.notebook_id == notebook_id)
        .order_by(Document.uploaded_at.desc())
    ).all()
    
    return documents


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    document_id: uuid.UUID,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """
    Xóa tài liệu khỏi hệ thống (cả bản ghi DB và file trên ổ cứng).
    """
    document = session.get(Document, document_id)
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="ERR_DOC_NOT_FOUND"
        )

    notebook = session.get(Notebook, document.notebook_id)
    if not notebook or notebook.user_id != current_user.user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ERR_DOC_FORBIDDEN"
        )

    # 1. Xóa file vật lý trên ổ cứng nếu tồn tại
    notebook_upload_dir = os.path.join(UPLOAD_DIR, str(notebook.notebook_id))
    if os.path.exists(notebook_upload_dir):
        file_ext = os.path.splitext(document.file_name)[1].lower()
        physical_file_path = os.path.join(notebook_upload_dir, f"{str(document_id)}{file_ext}")
        if os.path.exists(physical_file_path):
            try:
                os.remove(physical_file_path)
            except Exception as e:
                print(f"Lỗi khi xóa file vật lý {physical_file_path}: {e}")

    # 2. Xóa bản ghi trong DB
    session.delete(document)
    session.commit()

    return None
