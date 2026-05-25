import uuid
import re
from datetime import datetime
from typing import List, Dict, Any
from sqlmodel import Session, select
from fastapi import HTTPException

from backend.app.models.models import Document, DocumentChunk, QAHistory, Citation
from backend.app.services.embedding_service import embedding_service
from backend.app.services.qa_service import qa_service
from backend.app.schemas.schemas import ChatResponse

class RAGService:
    def answer_notebook_question(
        self,
        *,
        notebook_id: uuid.UUID,
        question: str,
        session: Session
    ) -> ChatResponse:
        """
        Thực hiện toàn bộ luồng RAG trên Sổ tay:
        1. Sinh vector embedding cho câu hỏi.
        2. Truy vấn top 3 chunks liên quan nhất từ DB.
        3. Dùng PhoBERT QA để lấy câu trả lời trích xuất.
        4. Tự động mở rộng câu trả lời ra toàn bộ câu (Sentence Expansion).
        5. Đánh dấu nguồn trích dẫn tương ứng dưới dạng [x].
        6. Lưu lịch sử QAHistory và Citations vào Database.
        7. Trả về kết quả dưới dạng ChatResponse.
        """
        # 1. Sinh vector embedding cho câu hỏi
        query_vector = embedding_service.embed_text([question], is_query=True)[0]

        # 2. Truy vấn các chunks liên quan nhất bằng pgvector (cosine distance)
        statement = (
            select(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.document_id)
            .where(Document.notebook_id == notebook_id)
            .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
            .limit(3)
        )
        related_chunks = session.exec(statement).all()

        if not related_chunks:
            raise HTTPException(
                status_code=400,
                detail="ERR_NO_DOCUMENTS"
            )

        # 3. Tạo context từ các chunks tìm được
        context = "\n".join([chunk.content for chunk in related_chunks])

        # 4. Chạy mô hình PhoBERT QA để lấy câu trả lời trích xuất
        answer = qa_service.answer_question(context, question)

        # Tự động mở rộng câu trả lời ra toàn bộ câu chứa nó trong context
        if answer and "Không tìm thấy" not in answer:
            # Tách context thành các câu
            sentences = re.split(r'(?<=[.!?])\s+|\n+', context)
            clean_ans = answer.lower().replace(" ", "").replace("_", "").replace(".", "")
            for sentence in sentences:
                clean_sentence = sentence.lower().replace(" ", "").replace("_", "").replace(".", "")
                if clean_ans in clean_sentence and len(clean_ans) > 0:
                    answer = sentence.strip()
                    break

        # 5. Tìm xem answer thuộc về chunk nào để đánh dấu trích dẫn dạng [x]
        matched_chunk_idx = None
        clean_ans = answer.lower().replace(" ", "").replace("_", "")
        
        for idx, chunk in enumerate(related_chunks):
            clean_chunk = chunk.content.lower().replace(" ", "").replace("_", "")
            if clean_ans in clean_chunk:
                matched_chunk_idx = idx
                break

        # Nếu không trùng khớp hoàn hảo, lấy chunk đầu tiên có độ tương đồng cao nhất
        if matched_chunk_idx is None and len(related_chunks) > 0:
            matched_chunk_idx = 0

        if matched_chunk_idx is not None:
            citation_num = matched_chunk_idx + 1
            if answer.endswith("."):
                answer = f"{answer[:-1].strip()} [{citation_num}]."
            else:
                answer = f"{answer.strip()} [{citation_num}]"

        # 6. Ghi lại lịch sử hỏi đáp vào Database
        qa_id = uuid.uuid4()
        qa_history = QAHistory(
            qahistory_id=qa_id,
            notebook_id=notebook_id,
            question=question,
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

        # 7. Tạo danh sách nguồn và trích dẫn chi tiết trả về
        sources = []
        citations_list = []
        for idx, chunk in enumerate(related_chunks):
            doc_name = chunk.document.file_name if chunk.document else "Tài liệu không tên"
            page_info = f"Trang {chunk.page_number}" if chunk.page_number else "Không rõ trang"
            sources.append(f"{doc_name} ({page_info})")
            
            citations_list.append({
                "id": idx + 1,
                "source_title": doc_name,
                "page_number": chunk.page_number,
                "snippet": chunk.content
            })

        return ChatResponse(
            answer=answer, 
            sources=list(set(sources)), 
            citations=citations_list
        )

rag_service = RAGService()
