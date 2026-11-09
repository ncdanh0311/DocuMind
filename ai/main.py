"""Offline AI serving: importing this app never loads a model or accesses Hugging Face."""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Literal
from ai.runtime.registry import registry
from ai.runtime.models import runtime
from ai.services.embedding_service import embedding_service
from ai.services.qa_service import qa_service
from ai.services.summarization_service import summarization_service
from ai.services.reranker_service import reranker_service

app = FastAPI(title="DocuMind AI Service", version="2.0.0")
QAModel = Literal["phobert_qa", "xlmroberta_qa"]
SummaryModel = Literal["vit5", "bartpho"]

class EmbedRequest(BaseModel):
    texts: list[str] = Field(min_length=1, max_length=16)
    is_query: bool = False
    expected_version: str | None = None
class Passage(BaseModel):
    chunk_id: str
    content: str = Field(min_length=1, max_length=50000)
class QARequest(BaseModel):
    passages: list[Passage] = Field(min_length=1, max_length=3)
    question: str = Field(min_length=1, max_length=4000)
    model_type: QAModel = "phobert_qa"
class SummarizeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=1000000)
    model_type: SummaryModel = "vit5"
    expected_version: str | None = None
    max_output_tokens: int = Field(default=128, ge=1, le=256)
class SplitRequest(BaseModel):
    text: str = Field(max_length=1000000)
    model: Literal["embedding", "vit5", "bartpho"]
    overlap: int = Field(default=0, ge=0, le=64)
class RerankRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4000)
    passages: list[str] = Field(min_length=1, max_length=20)
    top_k: int = Field(default=3, ge=1, le=3)

def infer(operation):
    try: return operation()
    except FileNotFoundError as exc: raise HTTPException(503, str(exc) if str(exc).startswith("ERR_") else "ERR_MODEL_UNAVAILABLE") from None
    except ValueError as exc: raise HTTPException(422, str(exc) if str(exc).startswith("ERR_") else "ERR_AI_INPUT") from None
    except Exception: raise HTTPException(500, "ERR_AI_INFERENCE") from None

@app.get("/health")
def health(): return {"status": "online"}
@app.get("/capabilities")
def capabilities(): return registry.capabilities()
@app.post("/embed")
def embed(request: EmbedRequest): return infer(lambda: {"embeddings": embedding_service.embed_text(request.texts, request.is_query, request.expected_version)})
@app.post("/split")
def split(request: SplitRequest): return infer(lambda: {"spans": runtime.split(request.text, request.model, request.overlap)})
@app.post("/qa")
def qa(request: QARequest): return infer(lambda: qa_service.answer([p.model_dump() for p in request.passages], request.question, request.model_type))
@app.post("/summarize")
def summarize(request: SummarizeRequest): return infer(lambda: summarization_service.summarize(request.text, request.model_type, request.expected_version, request.max_output_tokens))
@app.post("/rerank")
def rerank(request: RerankRequest): return infer(lambda: {"results": reranker_service.rerank(request.question, request.passages, request.top_k)})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("ai.main:app", host="127.0.0.1", port=8001)
