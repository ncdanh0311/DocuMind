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


from backend.app.schemas.schemas import ChatRequest, ChatResponse
from backend.app.models.models import Document, DocumentChunk, QAHistory, Citation
from backend.app.services.embedding_service import embedding_service
from backend.app.services.qa_service import qa_service
from datetime import datetime

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

    # 2. Sinh vector embedding cho câu hỏi
    query_vector = embedding_service.embed_text([request.question], is_query=True)[0]

    # 3. Truy vấn các chunks liên quan nhất bằng pgvector (cosine distance)
    # Join qua bảng Document để lọc theo notebook_id
    statement = (
        select(DocumentChunk)
        .join(Document, DocumentChunk.document_id == Document.document_id)
        .where(Document.notebook_id == notebook_id)
        .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
        .limit(3)  # Lấy top 3 chunks liên quan nhất làm context
    )
    related_chunks = session.exec(statement).all()

    if not related_chunks:
        return ChatResponse(
            answer="Sổ tay này chưa có tài liệu nào được phân tích thành công. Bạn vui lòng tải tài liệu lên trước khi đặt câu hỏi nhé!",
            sources=[]
        )

    # 4. Tạo context từ các chunks tìm được
    context = "\n".join([chunk.content for chunk in related_chunks])

    # 5. Chạy mô hình PhoBERT QA để lấy câu trả lời trích xuất
    answer = qa_service.answer_question(context, request.question)

    # 6. Ghi lại lịch sử hỏi đáp vào Database
    qa_id = uuid.uuid4()
    qa_history = QAHistory(
        qahistory_id=qa_id,
        notebook_id=notebook_id,
        question=request.question,
        answer=answer,
        model_name="phobert_qa",
        created_at=datetime.utcnow()
    )
    session.add(qa_history)

    # Ghi nhận các trích dẫn nguồn
    for chunk in related_chunks:
        citation = Citation(
            citation_id=uuid.uuid4(),
            qa_id=qa_id,
            chunk_id=chunk.docuchunk_id,
            relevance_score=None
        )
        session.add(citation)

    session.commit()

    # 7. Tạo danh sách nguồn trích dẫn trả về
    sources = []
    for chunk in related_chunks:
        doc_name = chunk.document.file_name if chunk.document else "Tài liệu không tên"
        page_info = f"Trang {chunk.page_number}" if chunk.page_number else "Không rõ trang"
        sources.append(f"{doc_name} ({page_info})")

    return ChatResponse(answer=answer, sources=list(set(sources)))

