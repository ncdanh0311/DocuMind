import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from backend.app.api.deps import get_current_user
from backend.app.core.db import get_session
from backend.app.models.models import Job, Summary, User
from backend.app.schemas.schemas import JobResponse, SummaryResponse
from backend.app.services.ai_client import ai_client
from backend.app.services.summary_service import source_snapshot, summary_response
from backend.app.core.config import settings

router = APIRouter()

@router.get("/app-config")
def app_config(current_user: User = Depends(get_current_user)):
    return {"ai_enabled": settings.AI_ENABLED}

@router.get("/capabilities")
def capabilities(current_user: User = Depends(get_current_user)):
    if not settings.AI_ENABLED:
        tasks = {"phobert_qa": "qa", "xlmroberta_qa": "qa", "vit5": "summarization", "bartpho": "summarization", "embedding": "embedding", "reranker": "reranker"}
        return {"models": [{"id": name, "task": task, "ready": False, "version": None, "error_code": "ERR_AI_DISABLED"} for name, task in tasks.items()]}
    return ai_client.request("/capabilities")

@router.get("/jobs/{job_id}", response_model=JobResponse)
def get_job(job_id: uuid.UUID, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    job = session.exec(select(Job).where(Job.job_id == job_id, Job.user_id == current_user.user_id)).first()
    if not job: raise HTTPException(404, "ERR_JOB_NOT_FOUND")
    return job

@router.get("/summaries/{summary_id}", response_model=SummaryResponse)
def get_summary(summary_id: uuid.UUID, session: Session = Depends(get_session), current_user: User = Depends(get_current_user)):
    job = session.exec(select(Job).where(Job.summary_id == summary_id, Job.user_id == current_user.user_id)).first()
    if not job: raise HTTPException(404, "ERR_SUMMARY_NOT_FOUND")
    summary = session.get(Summary, summary_id)
    try: stale = source_snapshot(session, summary.notebook_id) != summary.source_snapshot
    except HTTPException: stale = True
    return summary_response(summary, job, stale)
