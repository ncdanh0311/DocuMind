import uuid
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from urllib.parse import quote
from sqlalchemy import union_all, literal
from sqlmodel import Session, select
from backend.app.api.deps import get_current_user, get_owned_document, get_owned_notebook
from backend.app.core.db import get_session
from backend.app.models.models import User, Document, DocumentVersion, QAHistory, Summary, Notebook
from backend.app.services.pagination import encode_cursor, after_cursor
from backend.app.services.text_extraction import extract_document
from backend.app.api.documents import document_response
from backend.app.schemas.schemas import DocumentResponse

router = APIRouter()


@router.post("/documents/{document_id}/extract-text", response_model=DocumentResponse)
def extract_text(document_id: uuid.UUID, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    document = get_owned_document(document_id, session, user)
    return document_response(extract_document(session, document), session)


def source_state(session, snapshot):
    result = []
    for saved in snapshot:
        row = dict(saved)
        document = session.get(Document, uuid.UUID(str(row["document_id"]))) if row.get("document_id") else None
        row["source_state"] = "missing" if document is None else "changed" if document.current_version != row.get("version") else "available"
        result.append(row)
    return result


@router.get("/notebooks/{notebook_id}/history")
def history(notebook_id: uuid.UUID, kind: str = Query(default="all", pattern="^(all|qa|summary)$"),
            limit: int = Query(default=20, ge=1, le=100), cursor: str | None = None,
            session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    get_owned_notebook(notebook_id, session, user)
    qa = select(QAHistory.qahistory_id.label("id"), QAHistory.created_at.label("created_at"),
                literal("qa").label("kind"), QAHistory.question.label("title"), QAHistory.model_name.label("model"))
    qa = qa.where(QAHistory.notebook_id == notebook_id)
    summaries = select(Summary.summary_id.label("id"), Summary.created_at.label("created_at"),
                       literal("summary").label("kind"), literal("Bản tóm tắt").label("title"), Summary.model_name.label("model"))
    summaries = summaries.where(Summary.notebook_id == notebook_id)
    table = (union_all(qa, summaries) if kind == "all" else qa if kind == "qa" else summaries).subquery()
    statement = select(table).order_by(table.c.created_at.desc(), table.c.id.desc()).limit(limit + 1)
    if cursor: statement = statement.where(after_cursor(table.c.created_at, table.c.id, cursor))
    rows = session.execute(statement).mappings().all()
    return {"items": [dict(row) for row in rows[:limit]],
            "next_cursor": encode_cursor(rows[limit - 1]["created_at"], rows[limit - 1]["id"]) if len(rows) > limit else None}


@router.get("/qa-history/{history_id}")
def qa_history(history_id: uuid.UUID, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    row = session.exec(select(QAHistory).join(Notebook).where(QAHistory.qahistory_id == history_id,
                                                            Notebook.user_id == user.user_id)).first()
    if not row: raise HTTPException(404, "ERR_HISTORY_NOT_FOUND")
    return {"id": row.qahistory_id, "notebook_id": row.notebook_id, "question": row.question, "answer": row.answer,
            "model": row.model_name, "model_version": row.model_version, "created_at": row.created_at,
            "citations": source_state(session, row.citation_snapshot)}


@router.get("/summary-history/{summary_id}")
def summary_history(summary_id: uuid.UUID, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    row = session.exec(select(Summary).join(Notebook).where(Summary.summary_id == summary_id,
                                                          Notebook.user_id == user.user_id)).first()
    if not row: raise HTTPException(404, "ERR_SUMMARY_NOT_FOUND")
    return {"id": row.summary_id, "notebook_id": row.notebook_id, "content": row.content if row.status == "succeeded" else None,
            "model": row.model_name, "model_version": row.model_version, "created_at": row.created_at,
            "status": row.status, "sources": source_state(session, row.source_snapshot)}


def markdown_response(content, filename):
    return Response(content, media_type="text/markdown; charset=utf-8", headers={
        "Content-Disposition": "attachment; filename*=UTF-8''" + quote(filename, safe=""),
        "Cache-Control": "private, no-store", "X-Content-Type-Options": "nosniff"})


@router.get("/documents/{document_id}/export")
def export_document(document_id: uuid.UUID, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    document = get_owned_document(document_id, session, user)
    version = session.exec(select(DocumentVersion).where(DocumentVersion.document_id == document_id,
                                                        DocumentVersion.version == document.current_version)).first()
    if not version: raise HTTPException(409, "ERR_SOURCE_NOT_READY")
    content = f"# {document.file_name}\n\nNguồn: {document.document_id} · Phiên bản {version.version}\n\n{version.canonical_text}\n"
    return markdown_response(content, document.file_name + ".md")


@router.get("/history/{kind}/{identifier}/export")
def export_history(kind: str, identifier: uuid.UUID, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    if kind == "qa":
        detail = qa_history(identifier, session, user)
        body = "# " + detail["question"] + "\n\n" + detail["answer"]
        sources = detail["citations"]
    elif kind == "summary":
        detail = summary_history(identifier, session, user)
        if detail["status"] != "succeeded": raise HTTPException(409, "ERR_HISTORY_NOT_READY")
        body = "# Bản tóm tắt đã lưu\n\n" + (detail["content"] or "")
        sources = detail["sources"]
    else: raise HTTPException(404, "ERR_HISTORY_NOT_FOUND")
    body += f"\n\nModel: {detail['model']} · {detail['model_version'] or 'legacy'}\nThời điểm: {detail['created_at'].isoformat()}\n"
    for source in sources:
        body += f"\n- Nguồn: {source.get('source_title', source.get('document_id', ''))} · Phiên bản {source.get('version', '?')} · {source['source_state']}\n"
        if source.get("snippet"): body += "\n> " + source["snippet"].replace("\n", "\n> ") + "\n"
    return markdown_response(body, "lich-su.md")
