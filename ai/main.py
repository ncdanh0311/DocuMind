import sys
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

# Đảm bảo import được các module từ thư mục root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ai.services.embedding_service import embedding_service
from ai.services.qa_service import qa_service
from ai.services.summarization_service import summarization_service

app = FastAPI(
    title="DocuMind AI Service",
    description="Microservice cho các mô hình Embedding và QA",
    version="1.0.0"
)

# Models cho API Request/Response
class EmbedRequest(BaseModel):
    texts: List[str]
    is_query: bool = False

class EmbedResponse(BaseModel):
    embeddings: List[List[float]]

class QARequest(BaseModel):
    context: str
    question: str

class QAResponse(BaseModel):
    answer: str

class SummarizeRequest(BaseModel):
    text: str

class SummarizeResponse(BaseModel):
    summary: str

@app.get("/health")
async def health():
    qa_loaded = qa_service.model is not None
    summarization_loaded = summarization_service.model is not None
    return {
        "status": "healthy",
        "embedding_model": embedding_service.model_name,
        "qa_model_path": qa_service.model_path,
        "qa_model_loaded": qa_loaded,
        "summarization_model_path": summarization_service.model_path,
        "summarization_model_loaded": summarization_loaded
    }

@app.post("/embed", response_model=EmbedResponse)
async def embed(request: EmbedRequest):
    try:
        embeddings = embedding_service.embed_text(request.texts, is_query=request.is_query)
        return EmbedResponse(embeddings=embeddings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi tạo embedding: {str(e)}")

@app.post("/qa", response_model=QAResponse)
async def qa(request: QARequest):
    try:
        answer = qa_service.answer_question(request.context, request.question)
        return QAResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi chạy QA inference: {str(e)}")

@app.post("/summarize", response_model=SummarizeResponse)
async def summarize(request: SummarizeRequest):
    try:
        summary = summarization_service.summarize(request.text)
        return SummarizeResponse(summary=summary)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi khi chạy summarization inference: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    # Chạy trên cổng 8001 để tránh xung đột với backend (port 8000)
    uvicorn.run("ai.main:app", host="0.0.0.0", port=8001, reload=True)
