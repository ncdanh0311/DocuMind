import json
from pathlib import Path
import uuid
from datetime import datetime, timedelta, timezone
import pytest
from sqlmodel import Session, select
from backend.app.models.models import Flashcard, ReviewState, ReviewEvent
from backend.app.api import study

API = "/api/v1"


def test_shared_card_wire_contract():
    from backend.app.schemas.learning import CardResponse
    fixture = json.loads((Path(__file__).resolve().parents[2] / "contracts/learning.json").read_text(encoding="utf-8"))["card"]
    assert CardResponse.model_validate(fixture).model_dump(mode="json") == fixture


def setup_card(client, source=None, question="Câu hỏi thật", answer="Câu trả lời thật", notebook=None):
    notebook = notebook or client.post(API + "/notebooks/", json={"title": "Học tập"}).json()["notebook_id"]
    response = client.post(f"{API}/notebooks/{notebook}/flashcards", json={"question": question, "answer": answer, "source": source})
    assert response.status_code == 201, response.text
    return notebook, response.json()


def review_body(card, grade="remembered", identifier=None):
    return {"request_id": identifier or str(uuid.uuid4()), "grade": grade,
            "expected_revision": card["review"]["revision"], "card_revision": card["revision"]}


def test_manual_cards_are_persistent_searchable_and_owner_scoped(resources):
    client, _, identity, alice, bob = resources
    notebook, card = setup_card(client, question="Định nghĩa trí nhớ")
    path = f"{API}/notebooks/{notebook}/flashcards"
    assert client.get(path + "?q=tri+nho").json()["items"][0]["card_id"] == card["card_id"]
    assert client.get(f"{API}/flashcards/{card['card_id']}").json()["answer"] == "Câu trả lời thật"
    assert client.get(f"{API}/flashcards/due?notebook_id={notebook}").json()["items"][0]["card_id"] == card["card_id"]
    identity["user"] = bob
    for method, suffix, body in [("get", "", None), ("delete", "", None), ("post", "/reviews", review_body(card)),
                                 ("patch", "", {"question": "Attack", "answer": "Attack", "expected_revision": 1})]:
        kwargs = {"json": body} if body else {}
        assert getattr(client, method)(f"{API}/flashcards/{card['card_id']}{suffix}", **kwargs).status_code == 404
    assert client.get(path).status_code == 404
    assert client.get(f"{API}/study/stats?notebook_id={notebook}").status_code == 404
    assert client.get(f"{API}/notebooks/{notebook}/flashcards/export").status_code == 404
    identity["user"] = alice
    assert client.delete(f"{API}/flashcards/{card['card_id']}").status_code == 204
    assert client.get(path).json() == {"items": [], "next_cursor": None}


def test_source_quote_is_verified_and_survives_document_deletion(resources):
    client, *_ = resources
    notebook = client.post(API + "/notebooks/", json={"title": "Nguồn"}).json()["notebook_id"]
    document = client.post(f"{API}/notebooks/{notebook}/documents/text", json={"title": "Nguồn thật", "content": "Đầu 🐈 cuối"}).json()
    identifier = document["document_id"]
    assert client.post(f"{API}/documents/{identifier}/extract-text").status_code == 200
    source = {"document_id": identifier, "version": 1, "start_offset": 4, "end_offset": 5, "snippet": "🐈", "source_title": "FORGED TITLE"}
    _, card = setup_card(client, source, notebook=notebook)
    assert card["source"]["snippet"] == "🐈" and card["source"]["source_title"] == "Nguồn thật.txt"
    forged = client.post(f"{API}/notebooks/{notebook}/flashcards", json={"question": "Question", "answer": "Answer", "source": {**source, "snippet": "fake"}})
    assert forged.status_code == 422
    other = client.post(API + "/notebooks/", json={"title": "Khác"}).json()["notebook_id"]
    assert client.post(f"{API}/notebooks/{other}/flashcards", json={"question": "Question", "answer": "Answer", "source": source}).status_code == 404
    assert client.delete(f"{API}/documents/{identifier}").status_code == 204
    read = client.get(f"{API}/flashcards/{card['card_id']}").json()
    assert read["source"]["source_state"] == "missing" and read["source"]["snippet"] == "🐈"


def test_review_idempotency_conflict_and_edits_do_not_reset_schedule(resources):
    client, engine, *_ = resources
    _, card = setup_card(client)
    path = f"{API}/flashcards/{card['card_id']}"
    body = review_body(card)
    first = client.post(path + "/reviews", json=body)
    assert first.status_code == 200, first.text
    assert client.post(path + "/reviews", json=body).json() == first.json()
    assert client.post(path + "/reviews", json={**body, "request_id": str(uuid.uuid4())}).status_code == 409
    assert client.post(path + "/reviews", json={**body, "grade": "again"}).json()["detail"] == "ERR_REQUEST_ID_REUSED"
    edited = client.patch(path, json={"question": "Sửa câu hỏi", "answer": "Sửa đáp án", "expected_revision": card["revision"]})
    assert edited.status_code == 200 and edited.json()["review"] == first.json()
    assert client.patch(path, json={"question": "Old", "answer": "Old", "expected_revision": 1}).status_code == 409
    with Session(engine) as session: assert len(session.exec(select(ReviewEvent)).all()) == 1


def test_review_intervals_again_and_cap_match_shared_contract(resources, monkeypatch):
    client, _, *_ = resources
    fixture = json.loads((Path(__file__).resolve().parents[2] / "contracts/learning.json").read_text(encoding="utf-8"))
    clock = {"now": datetime(2030, 1, 1, tzinfo=timezone.utc)}
    monkeypatch.setattr(study, "utc_now", lambda: clock["now"])
    _, card = setup_card(client)
    path = f"{API}/flashcards/{card['card_id']}"
    for days in fixture["review_intervals_days"] + [30]:
        result = client.post(path + "/reviews", json=review_body(card))
        assert result.status_code == 200, result.text
        state = result.json()
        due = datetime.fromisoformat(state["due_at"])
        assert due == clock["now"] + timedelta(days=days)
        card["review"] = state
        assert not client.get(API + "/flashcards/due").json()["items"]
        clock["now"] = due
    result = client.post(path + "/reviews", json=review_body(card, "again")).json()
    assert result["stage"] == 0 and datetime.fromisoformat(result["due_at"]) == clock["now"] + timedelta(minutes=fixture["review_again_minutes"])


def test_stats_use_vietnam_day_and_distinct_cards(resources, monkeypatch):
    client, *_ = resources
    clock = {"now": datetime(2030, 1, 1, 16, 59, tzinfo=timezone.utc)}  # 23:59 VN
    monkeypatch.setattr(study, "utc_now", lambda: clock["now"])
    notebook, card = setup_card(client)
    client.post(f"{API}/flashcards/{card['card_id']}/reviews", json=review_body(card, "again"))
    path = f"{API}/study/stats?notebook_id={notebook}"
    assert client.get(path).json()["reviewed_today"] == 1
    clock["now"] += timedelta(minutes=2)
    stats = client.get(path).json()
    assert stats["reviewed_today"] == 0 and stats["streak_days"] == 1 and stats["total_cards"] == 1
    clock["now"] += timedelta(days=2)
    assert client.get(path).json()["streak_days"] == 0


def test_csv_export_and_text_search_do_not_use_ai(resources):
    client, *_ = resources
    notebook, card = setup_card(client, question="=1+1", answer="Tiếng Việt 🐈")
    exported = client.get(f"{API}/notebooks/{notebook}/flashcards/export")
    assert exported.status_code == 200 and exported.content.startswith(b"\xef\xbb\xbf")
    assert "'=1+1" in exported.text and "Tiếng Việt 🐈" in exported.text
    document = client.post(f"{API}/notebooks/{notebook}/documents/text", json={"title": "Ghi chú", "content": "Định nghĩa trí nhớ ở phần cuối"}).json()
    identifier = document["document_id"]
    assert client.get(f"{API}/notebooks/{notebook}/search?q=tri+nho").json()["items"] == []
    client.post(f"{API}/documents/{identifier}/extract-text")
    found = client.get(f"{API}/notebooks/{notebook}/search?q=tri+nho").json()
    assert found["items"][0]["document_id"] == identifier
    assert "Định nghĩa" in client.get(f"{API}/documents/{identifier}/export").text


def test_delete_notebook_cascades_cards_and_review_events(resources):
    client, engine, *_ = resources
    notebook, card = setup_card(client)
    assert client.post(f"{API}/flashcards/{card['card_id']}/reviews", json=review_body(card)).status_code == 200
    assert client.delete(f"{API}/notebooks/{notebook}").status_code == 204
    with Session(engine) as session:
        assert not session.exec(select(Flashcard)).all()
        assert not session.exec(select(ReviewState)).all()
        assert not session.exec(select(ReviewEvent)).all()
