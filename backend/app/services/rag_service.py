"""Notebook QA with exact span provenance and explicit abstention."""
import uuid
from fastapi import HTTPException
from sqlmodel import Session, select
from backend.app.models.models import Document, DocumentChunk, QAHistory, Citation
from backend.app.schemas.schemas import ChatResponse, CitationResponse
from backend.app.services.ai_client import ai_client

class RAGService:
    def answer_notebook_question(self, *, notebook_id, question, model="phobert_qa", session: Session):
        capability = ai_client.capability(model)
        embedding = ai_client.capability("embedding")
        vector = ai_client.embed([question], is_query=True, expected_version=embedding["version"])
        if len(vector) != 1 or len(vector[0]) != 384: raise HTTPException(502, "ERR_AI_SERVICE_ERROR")
        chunks = session.exec(select(DocumentChunk).join(Document).where(Document.notebook_id == notebook_id,
            Document.status == "ready", Document.current_version > 0, DocumentChunk.version == Document.current_version,
            DocumentChunk.embedding_model == embedding["version"],
            DocumentChunk.embedding.is_not(None)).order_by(DocumentChunk.embedding.cosine_distance(vector[0])).limit(20)).all()
        if not chunks: raise HTTPException(409, "ERR_DOCUMENTS_NOT_READY")
        ranking = ai_client.request("/rerank", {"question": question, "passages": [c.content for c in chunks], "top_k": 3})["results"]
        if not isinstance(ranking, list) or any(not isinstance(r.get("index"), int) or not 0 <= r["index"] < len(chunks) for r in ranking):
            raise HTTPException(502, "ERR_AI_SERVICE_ERROR")
        selected = [chunks[r["index"]] for r in ranking[:3]]
        if not selected: raise HTTPException(502, "ERR_AI_SERVICE_ERROR")
        result = ai_client.request("/qa", {"question": question, "model_type": model,
            "passages": [{"chunk_id": str(c.docuchunk_id), "content": c.content} for c in selected]})
        if result.get("model_version") != capability["version"]: raise HTTPException(503, "ERR_MODEL_VERSION_CHANGED")
        citations, sources, matched = [], [], None
        if result.get("status") == "no_answer":
            answer, status = "Không tìm thấy câu trả lời có đủ bằng chứng trong tài liệu.", "no_answer"
        elif result.get("status") == "answered":
            matched = next((c for c in selected if str(c.docuchunk_id) == result.get("chunk_id")), None)
            start, end = result.get("start"), result.get("end")
            if not matched or not isinstance(start, int) or not isinstance(end, int) or not 0 <= start < end <= len(matched.content):
                raise HTTPException(502, "ERR_INVALID_ANSWER_SPAN")
            exact = matched.content[start:end]
            if exact != result.get("answer") or not exact.strip() or matched.start_offset is None:
                raise HTTPException(502, "ERR_INVALID_ANSWER_SPAN")
            answer, status = exact.strip() + " [1]", "answered"
            citation = CitationResponse(id=1, source_title=matched.document.file_name, page_number=matched.page_number,
                page_end=matched.page_end, snippet=matched.content, document_id=matched.document_id, version=matched.version,
                start_offset=matched.start_offset + start, end_offset=matched.start_offset + end, section_path=matched.section_path)
            citations, sources = [citation], [matched.document.file_name]
        else: raise HTTPException(502, "ERR_AI_SERVICE_ERROR")
        from backend.app.services.summary_service import lock_notebook
        lock_notebook(session, notebook_id)
        for selected_chunk in selected:
            current = session.exec(select(Document).where(Document.document_id == selected_chunk.document_id)
                .execution_options(populate_existing=True)).first()
            if not current or current.status != "ready" or current.current_version != selected_chunk.version:
                raise HTTPException(409, "ERR_SOURCE_CHANGED")
        history = QAHistory(notebook_id=notebook_id, question=question, answer=answer, model_name=model, model_version=capability["version"])
        session.add(history); session.flush()
        if matched:
            rank = next(r for r in ranking if chunks[r["index"]].docuchunk_id == matched.docuchunk_id)
            session.add(Citation(qa_id=history.qahistory_id, chunk_id=matched.docuchunk_id,
                relevance_score=rank["score"], start_offset=citations[0].start_offset, end_offset=citations[0].end_offset))
        session.commit()
        return ChatResponse(answer=answer, status=status, citations=citations, sources=sources, model_version=capability["version"])

rag_service = RAGService()
