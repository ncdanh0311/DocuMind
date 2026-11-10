from datetime import datetime, timedelta, timezone
import unicodedata
import uuid
from fastapi import HTTPException
from sqlmodel import select
from backend.app.models.models import Flashcard, Notebook, DocumentVersion, Document, ReviewState, ReviewEvent

INTERVAL_DAYS = (1, 3, 7, 14, 30)


def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFD', value.casefold().replace('đ', 'd')) if not unicodedata.combining(c))


def as_utc(value): return value.replace(tzinfo=timezone.utc) if value.tzinfo is None else value.astimezone(timezone.utc)


def owned_card(session, identifier, user):
    card = session.exec(select(Flashcard).join(Notebook).where(Flashcard.card_id == identifier, Notebook.user_id == user.user_id)).first()
    if not card: raise HTTPException(404, "ERR_CARD_NOT_FOUND")
    return card


def verified_source(session, notebook_id, source):
    if source is None: return None
    document = session.get(Document, source.document_id)
    if not document or document.notebook_id != notebook_id: raise HTTPException(404, "ERR_DOC_NOT_FOUND")
    version = session.exec(select(DocumentVersion).where(DocumentVersion.document_id == source.document_id,
                                                        DocumentVersion.version == source.version)).first()
    if not version: raise HTTPException(404, "ERR_SOURCE_NOT_READY")
    start, end = source.start_offset, source.end_offset
    if not 0 <= start < end <= len(version.canonical_text) or end - start > 20000:
        raise HTTPException(422, "ERR_INVALID_SOURCE_RANGE")
    text = version.canonical_text[start:end]
    if not text.strip() or source.snippet is not None and source.snippet != text:
        raise HTTPException(422, "ERR_INVALID_SOURCE_RANGE")
    sections = [s for s in version.sections if s['start'] < end and s['end'] > start]
    return {"document_id": str(document.document_id), "version": version.version, "start_offset": start, "end_offset": end,
            "snippet": text, "source_title": document.file_name,
            "page_number": sections[0].get("page_start") if sections else None,
            "page_end": sections[-1].get("page_end") if sections else None,
            "section_path": sections[0].get("section_path") if sections else None}


def state_response(state):
    return {"card_id": str(state.card_id), "stage": state.stage, "revision": state.revision,
            "due_at": as_utc(state.due_at).isoformat(),
            "last_review_at": as_utc(state.last_review_at).isoformat() if state.last_review_at else None}


def card_response(session, card):
    source = dict(card.source_snapshot) if card.source_snapshot else None
    if source:
        document = session.get(Document, card.source_document_id) if card.source_document_id else None
        source["source_state"] = "missing" if document is None else "changed" if document.current_version != source["version"] else "available"
    return {"card_id": card.card_id, "notebook_id": card.notebook_id, "question": card.question, "answer": card.answer,
            "source": source, "revision": card.revision, "created_at": as_utc(card.created_at), "updated_at": as_utc(card.updated_at),
            "review": state_response(session.get(ReviewState, card.card_id))}


def replay(event, card_id, user_id, request):
    if (event.card_id, event.user_id, event.grade, event.expected_revision, event.card_revision) != (
            card_id, user_id, request.grade, request.expected_revision, request.card_revision):
        raise HTTPException(409, "ERR_REQUEST_ID_REUSED")
    return event.response_snapshot


def next_review(state, grade, now):
    if grade == "again": state.stage, state.due_at = 0, now + timedelta(minutes=10)
    else:
        index = min(state.stage, len(INTERVAL_DAYS) - 1)
        state.due_at = now + timedelta(days=INTERVAL_DAYS[index])
        state.stage = min(state.stage + 1, len(INTERVAL_DAYS))
    state.revision += 1; state.last_review_at = now
