"""Run separately: python -m backend.worker [--once]. No API BackgroundTasks."""
import argparse
import logging
import threading
import time
from fastapi import HTTPException
from sqlmodel import Session
from backend.app.core.config import settings
from backend.app.core.db import engine
from backend.app.services.ai_client import ai_client
from backend.app.services.document_service import DocumentService
from backend.app.services.summary_worker import SummaryWorker
from backend.app.services.job_service import LeaseLost, PipelineError, job_service

logger = logging.getLogger(__name__)

def run_once(db_engine=engine, ai=ai_client):
    if not settings.AI_ENABLED: return False
    with Session(db_engine) as session: claim = job_service.claim(session)
    if claim is None: return False
    stop, lost = threading.Event(), threading.Event()
    deadline = time.monotonic() + settings.JOB_MAX_SECONDS
    def check():
        if lost.is_set(): raise LeaseLost()
        if time.monotonic() >= deadline: raise PipelineError("ERR_JOB_TIMEOUT")
    def heartbeat():
        while not stop.wait(settings.JOB_HEARTBEAT_SECONDS):
            try:
                with Session(db_engine) as session:
                    if time.monotonic() >= deadline:
                        job_service.fail(session, claim, PipelineError("ERR_JOB_TIMEOUT"))
                        lost.set(); return
                    if not job_service.heartbeat(session, claim): lost.set(); return
            except Exception: lost.set(); return
    thread = threading.Thread(target=heartbeat, name="job-heartbeat", daemon=True)
    thread.start()
    try:
        runner = DocumentService(db_engine, ai) if claim.kind == "ingest" else SummaryWorker(db_engine, ai)
        runner.execute(claim, check)
    except LeaseLost: pass
    except Exception as exc:
        if isinstance(exc, PipelineError): error = exc
        elif isinstance(exc, HTTPException): error = PipelineError(str(exc.detail), exc.status_code in (502, 504) or exc.detail == "ERR_AI_SERVICE_UNAVAILABLE")
        elif isinstance(exc, (ValueError, FileNotFoundError)) and str(exc).startswith("ERR_"): error = PipelineError(str(exc))
        else:
            logger.warning("Job failed (%s)", type(exc).__name__)
            error = PipelineError("ERR_JOB_FAILED")
        try:
            with Session(db_engine) as session: job_service.fail(session, claim, error)
        except LeaseLost: pass
    finally:
        stop.set(); thread.join(timeout=2)
    return True

def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--once", action="store_true"); args = parser.parse_args()
    if not settings.AI_ENABLED:
        print("AI đang tạm hoãn; worker không nhận job.")
        return
    try:
        while True:
            worked = run_once()
            if args.once: break
            if not worked: time.sleep(1)
    except KeyboardInterrupt: pass

if __name__ == "__main__": main()
