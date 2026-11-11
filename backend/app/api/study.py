import csv
import io
import uuid
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select
from backend.app.api.deps import get_current_user, get_owned_notebook
from backend.app.core.db import get_session
from backend.app.core.security import utc_now
from backend.app.models.models import User, Notebook, Document, DocumentVersion, Flashcard, ReviewState, ReviewEvent
from backend.app.schemas.learning import CardCreate, CardUpdate, ReviewInput, CardResponse, CardPage, ReviewResponse
from backend.app.services.study import (owned_card, verified_source, normalize, card_response, state_response,
                                        replay, next_review, as_utc)
from backend.app.services.summary_service import lock_notebook
from backend.app.services.pagination import after_cursor, encode_cursor

router = APIRouter()


@router.post("/notebooks/{notebook_id}/flashcards", status_code=201, response_model=CardResponse)
def create_card(notebook_id: uuid.UUID, body: CardCreate, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    get_owned_notebook(notebook_id, session, user); lock_notebook(session, notebook_id)
    source = verified_source(session, notebook_id, body.source)
    card = Flashcard(notebook_id=notebook_id, question=body.question, answer=body.answer,
                     search_text=normalize(body.question + "\n" + body.answer),
                     source_document_id=body.source.document_id if body.source else None, source_snapshot=source)
    session.add(card); session.flush()
    session.add(ReviewState(card_id=card.card_id, user_id=user.user_id, due_at=utc_now()))
    session.commit(); session.refresh(card)
    return card_response(session, card)


@router.get("/notebooks/{notebook_id}/flashcards", response_model=CardPage)
def list_cards(notebook_id: uuid.UUID, q: str = Query(default="", max_length=200), cursor: str | None = None,
               limit: int = Query(default=20, ge=1, le=100), session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    get_owned_notebook(notebook_id, session, user)
    statement = select(Flashcard).where(Flashcard.notebook_id == notebook_id)
    if q.strip(): statement = statement.where(Flashcard.search_text.contains(normalize(q.strip()), autoescape=True))
    if cursor: statement = statement.where(after_cursor(Flashcard.created_at, Flashcard.card_id, cursor))
    cards = session.exec(statement.order_by(Flashcard.created_at.desc(), Flashcard.card_id.desc()).limit(limit + 1)).all()
    return {"items": [card_response(session, card) for card in cards[:limit]],
            "next_cursor": encode_cursor(cards[limit - 1].created_at, cards[limit - 1].card_id) if len(cards) > limit else None}


@router.get("/flashcards/due", response_model=CardPage)
def due_cards(notebook_id: uuid.UUID | None = None, limit: int = Query(default=20, ge=1, le=20),
              session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    statement = select(Flashcard).join(Notebook).join(ReviewState, ReviewState.card_id == Flashcard.card_id).where(
        Notebook.user_id == user.user_id, ReviewState.user_id == user.user_id, ReviewState.due_at <= utc_now())
    if notebook_id:
        get_owned_notebook(notebook_id, session, user)
        statement = statement.where(Flashcard.notebook_id == notebook_id)
    cards = session.exec(statement.order_by(ReviewState.due_at, Flashcard.card_id).limit(limit)).all()
    return {"items": [card_response(session, card) for card in cards], "next_cursor": None}


@router.get("/flashcards/{card_id}", response_model=CardResponse)
def read_card(card_id: uuid.UUID, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    return card_response(session, owned_card(session, card_id, user))


@router.patch("/flashcards/{card_id}", response_model=CardResponse)
def edit_card(card_id: uuid.UUID, body: CardUpdate, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    card = owned_card(session, card_id, user); lock_notebook(session, card.notebook_id)
    session.refresh(card)
    if card.revision != body.expected_revision: raise HTTPException(409, "ERR_CARD_CONFLICT")
    if "source" in body.model_fields_set:
        card.source_snapshot = verified_source(session, card.notebook_id, body.source)
        card.source_document_id = body.source.document_id if body.source else None
    card.question, card.answer = body.question, body.answer
    card.search_text = normalize(body.question + "\n" + body.answer)
    card.revision += 1; card.updated_at = utc_now()
    session.add(card); session.commit(); session.refresh(card)
    return card_response(session, card)


@router.delete("/flashcards/{card_id}", status_code=204)
def delete_card(card_id: uuid.UUID, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    card = owned_card(session, card_id, user); lock_notebook(session, card.notebook_id)
    session.delete(card); session.commit()


@router.post("/flashcards/{card_id}/reviews", response_model=ReviewResponse)
def review_card(card_id: uuid.UUID, body: ReviewInput, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    card = owned_card(session, card_id, user)
    existing = session.get(ReviewEvent, body.request_id)
    if existing: return replay(existing, card_id, user.user_id, body)
    lock_notebook(session, card.notebook_id)
    session.refresh(card)
    # Recheck after acquiring the notebook lock; another device may just have committed this UUID.
    existing = session.get(ReviewEvent, body.request_id)
    if existing: return replay(existing, card_id, user.user_id, body)
    state = session.exec(select(ReviewState).where(ReviewState.card_id == card_id).with_for_update()
                         .execution_options(populate_existing=True)).one()
    if card.revision != body.card_revision: raise HTTPException(409, "ERR_CARD_CONFLICT")
    if state.revision != body.expected_revision: raise HTTPException(409, "ERR_REVIEW_CONFLICT")
    now = utc_now()
    if as_utc(state.due_at) > now: raise HTTPException(409, "ERR_CARD_NOT_DUE")
    next_review(state, body.grade, now)
    response = state_response(state)
    session.add(state)
    session.add(ReviewEvent(request_id=body.request_id, card_id=card_id, user_id=user.user_id, grade=body.grade,
        expected_revision=body.expected_revision, card_revision=body.card_revision, reviewed_at=now, response_snapshot=response))
    try: session.commit()
    except IntegrityError:
        session.rollback()
        existing = session.get(ReviewEvent, body.request_id)
        if existing: return replay(existing, card_id, user.user_id, body)
        raise HTTPException(409, "ERR_REVIEW_CONFLICT") from None
    return response


@router.get("/study/stats")
def statistics(notebook_id: uuid.UUID | None = None, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    if notebook_id: get_owned_notebook(notebook_id, session, user)
    cards = select(Flashcard.card_id).join(Notebook).where(Notebook.user_id == user.user_id)
    if notebook_id: cards = cards.where(Flashcard.notebook_id == notebook_id)
    identifiers = cards.subquery()
    total = session.exec(select(func.count()).select_from(identifiers)).one()
    now = utc_now(); zone = ZoneInfo("Asia/Ho_Chi_Minh"); today = now.astimezone(zone).date()
    due = session.exec(select(func.count()).select_from(ReviewState).where(ReviewState.card_id.in_(select(identifiers.c.card_id)),
                                              ReviewState.user_id == user.user_id, ReviewState.due_at <= now)).one()
    events = session.exec(select(ReviewEvent.card_id, ReviewEvent.reviewed_at).where(ReviewEvent.user_id == user.user_id,
                           ReviewEvent.card_id.in_(select(identifiers.c.card_id)))).all()
    dates, today_cards = set(), set()
    for card_id, reviewed_at in events:
        day = as_utc(reviewed_at).astimezone(zone).date(); dates.add(day)
        if day == today: today_cards.add(card_id)
    day = today if today in dates else today - timedelta(days=1)
    streak = 0
    while day in dates: streak += 1; day -= timedelta(days=1)
    return {"total_cards": total, "due_cards": due, "reviewed_today": len(today_cards), "streak_days": streak,
            "timezone": "Asia/Ho_Chi_Minh", "server_now": now}


def safe_csv(value):
    value = str(value or "")
    return "'" + value if value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r")) else value


@router.get("/notebooks/{notebook_id}/flashcards/export")
def export_cards(notebook_id: uuid.UUID, session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    get_owned_notebook(notebook_id, session, user)
    output = io.StringIO(); writer = csv.writer(output)
    writer.writerow(["question", "answer", "source_title", "source_quote", "source_version"])
    for card in session.exec(select(Flashcard).where(Flashcard.notebook_id == notebook_id).order_by(Flashcard.created_at)).all():
        source = card.source_snapshot or {}
        writer.writerow([safe_csv(value) for value in (card.question, card.answer, source.get("source_title"), source.get("snippet"), source.get("version"))])
    return Response("\ufeff" + output.getvalue(), media_type="text/csv; charset=utf-8", headers={
        "Content-Disposition": 'attachment; filename="flashcards.csv"', "Cache-Control": "private, no-store"})


@router.get("/notebooks/{notebook_id}/search")
def search_text(notebook_id: uuid.UUID, q: str = Query(min_length=1, max_length=200), cursor: str | None = None,
                limit: int = Query(default=20, ge=1, le=100), session: Session = Depends(get_session), user: User = Depends(get_current_user)):
    get_owned_notebook(notebook_id, session, user)
    term = normalize(q.strip())
    if not term: raise HTTPException(422, "ERR_INVALID_INPUT")
    statement = select(Document, DocumentVersion).join(DocumentVersion, (DocumentVersion.document_id == Document.document_id) &
        (DocumentVersion.version == Document.current_version)).where(Document.notebook_id == notebook_id)
    if cursor: statement = statement.where(after_cursor(Document.uploaded_at, Document.document_id, cursor))
    statement = statement.order_by(Document.uploaded_at.desc(), Document.document_id.desc()).execution_options(yield_per=10)
    matches = []
    for document, version in session.exec(statement):
        normalized = normalize(version.canonical_text)
        if term not in normalize(document.file_name) and term not in normalized: continue
        position = max(0, normalized.find(term) - 50)
        matches.append((document, version, version.canonical_text[position:position + 240]))
        if len(matches) > limit: break
    return {"items": [{"document_id": doc.document_id, "file_name": doc.file_name, "version": version.version, "snippet": snippet}
                       for doc, version, snippet in matches[:limit]],
            "next_cursor": encode_cursor(matches[limit - 1][0].uploaded_at, matches[limit - 1][0].document_id) if len(matches) > limit else None}
