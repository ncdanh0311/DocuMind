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
from backend.app.core.config import settings
import httpx

class RAGService:
    def answer_notebook_question(
        self,
        *,
        notebook_id: uuid.UUID,
        question: str,
        model: str = "phobert_qa",
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

        # 2. Truy vấn top 20 chunks liên quan nhất bằng pgvector (cosine distance)
        statement = (
            select(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.document_id)
            .where(Document.notebook_id == notebook_id)
            .order_by(DocumentChunk.embedding.cosine_distance(query_vector))
            .limit(20)
        )
        related_chunks = session.exec(statement).all()

        if not related_chunks:
            raise HTTPException(
                status_code=400,
                detail="ERR_NO_DOCUMENTS"
            )

        # 3. Rerank bằng ViRanker qua AI Microservice (chọn top 3 tốt nhất)
        passages = [chunk.content for chunk in related_chunks]
        try:
            response = httpx.post(
                f"{settings.AI_SERVICE_URL}/rerank",
                json={
                    "question": question,
                    "passages": passages,
                    "top_k": 3
                },
                timeout=60.0
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"ERR_AI_SERVICE_ERROR: {response.text}"
                )

            rerank_data = response.json()
            rerank_results = rerank_data["results"]
        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503,
                detail="ERR_AI_SERVICE_UNAVAILABLE"
            )

        # Lấy top 3 chunks sau khi rerank và lưu điểm relevance_score
        reranked_chunks = []
        scores_by_chunk_id = {}
        for item in rerank_results:
            orig_idx = item["index"]
            score = item["score"]
            chunk = related_chunks[orig_idx]
            reranked_chunks.append(chunk)
            scores_by_chunk_id[chunk.docuchunk_id] = score

        # 4. Tạo context từ các chunks đã qua rerank
        context = "\n".join([chunk.content for chunk in reranked_chunks])

        # 5. Chạy mô hình QA được lựa chọn để lấy câu trả lời trích xuất
        answer = qa_service.answer_question(context, question, model_type=model)

        if answer and answer.startswith("ERR_"):
            # Ghi lại lịch sử hỏi đáp vào Database (không trích dẫn)
            qa_id = uuid.uuid4()
            qa_history = QAHistory(
                qahistory_id=qa_id,
                notebook_id=notebook_id,
                question=question,
                answer=answer,
                model_name=model,
                created_at=datetime.utcnow()
            )
            session.add(qa_history)
            session.commit()
            return ChatResponse(
                answer=answer,
                sources=[],
                citations=[]
            )

        # Tự động mở rộng câu trả lời ra toàn bộ câu chứa nó trong context
        if answer:
            # Tách context thành các câu
            sentences = re.split(r'(?<=[.!?])\s+|\n+', context)
            clean_ans = answer.lower().replace(" ", "").replace("_", "").replace(".", "")
            for sentence in sentences:
                clean_sentence = sentence.lower().replace(" ", "").replace("_", "").replace(".", "")
                if clean_ans in clean_sentence and len(clean_ans) > 0:
                    answer = sentence.strip()
                    break

        # 6. Tìm xem answer thuộc về chunk nào để đánh dấu trích dẫn dạng [x]
        matched_chunk_idx = None
        clean_ans = answer.lower().replace(" ", "").replace("_", "")
        
        for idx, chunk in enumerate(reranked_chunks):
            clean_chunk = chunk.content.lower().replace(" ", "").replace("_", "")
            if clean_ans in clean_chunk:
                matched_chunk_idx = idx
                break

        # Nếu không trùng khớp hoàn hảo, lấy chunk đầu tiên có độ tương đồng cao nhất
        if matched_chunk_idx is None and len(reranked_chunks) > 0:
            matched_chunk_idx = 0

        if matched_chunk_idx is not None:
            citation_num = matched_chunk_idx + 1
            if answer.endswith("."):
                answer = f"{answer[:-1].strip()} [{citation_num}]."
            else:
                answer = f"{answer.strip()} [{citation_num}]"

        # 7. Ghi lại lịch sử hỏi đáp vào Database
        qa_id = uuid.uuid4()
        qa_history = QAHistory(
            qahistory_id=qa_id,
            notebook_id=notebook_id,
            question=question,
            answer=answer,
            model_name=model,
            created_at=datetime.utcnow()
        )
        session.add(qa_history)

        # Ghi nhận các trích dẫn nguồn kèm điểm relevance_score từ Rerank
        for chunk in reranked_chunks:
            citation = Citation(
                citation_id=uuid.uuid4(),
                qa_id=qa_id,
                chunk_id=chunk.docuchunk_id,
                relevance_score=scores_by_chunk_id.get(chunk.docuchunk_id)
            )
            session.add(citation)

        session.commit()

        # 8. Tạo danh sách nguồn và trích dẫn chi tiết trả về
        sources = []
        citations_list = []
        for idx, chunk in enumerate(reranked_chunks):
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

    def summarize_notebook(
        self,
        *,
        notebook_id: uuid.UUID,
        session: Session
    ) -> str:
        """
        Tóm tắt nội dung chính của sổ tay:
        1. Lấy tất cả các chunks tài liệu thuộc sổ tay.
        2. Ghép nội dung lại và cắt lấy 800 từ (words) đầu tiên.
        3. Gửi POST request sang AI service endpoint `/summarize` với timeout = 180s.
        4. Trả về nội dung tóm tắt.
        """
        # 1. Lấy danh sách các chunks tài liệu thuộc Sổ tay, sắp xếp theo thứ tự tài liệu và số trang
        statement = (
            select(DocumentChunk)
            .join(Document, DocumentChunk.document_id == Document.document_id)
            .where(Document.notebook_id == notebook_id)
            .order_by(DocumentChunk.document_id, DocumentChunk.page_number, DocumentChunk.docuchunk_id)
        )
        chunks = session.exec(statement).all()

        if not chunks:
            raise HTTPException(
                status_code=400,
                detail="ERR_NO_DOCUMENTS"
            )

        # 2. Ghép nội dung các chunks lại và cắt lấy 800 từ đầu tiên
        full_text = " ".join([chunk.content for chunk in chunks])
        words = full_text.split()
        truncated_text = " ".join(words[:800])

        # 3. Gửi request tóm tắt tới AI Microservice
        try:
            # Sử dụng timeout 180 giây vì model load lần đầu hoặc inference trên CPU có thể chậm
            response = httpx.post(
                f"{settings.AI_SERVICE_URL}/summarize",
                json={"text": truncated_text},
                timeout=180.0
            )

            if response.status_code != 200:
                raise HTTPException(
                    status_code=502,
                    detail=f"ERR_AI_SERVICE_ERROR: {response.text}"
                )

            data = response.json()
            return data["summary"]

        except httpx.RequestError as exc:
            raise HTTPException(
                status_code=503,
                detail="ERR_AI_SERVICE_UNAVAILABLE"
            )

rag_service = RAGService()
