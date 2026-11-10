from concurrent.futures import ThreadPoolExecutor
import uuid
from sqlmodel import Session, select
from backend.app.api.study import review_card
from backend.app.models.models import User, ReviewEvent
from backend.app.schemas.learning import ReviewInput
from fastapi import HTTPException
from tests.helpers import headers


def test_two_devices_cannot_grade_the_same_revision_twice(client, db_engine, account):
    notebook = client.post('/api/v1/notebooks/', headers=headers(account), json={'title': 'Concurrent review'}).json()['notebook_id']
    card = client.post(f'/api/v1/notebooks/{notebook}/flashcards', headers=headers(account), json={'question': 'Q', 'answer': 'A'}).json()
    identifier = uuid.UUID(card['card_id'])
    def submit(_):
        with Session(db_engine) as session:
            user = session.get(User, uuid.UUID(account['user_id']))
            body = ReviewInput(request_id=uuid.uuid4(), grade='remembered', expected_revision=0, card_revision=1)
            try: review_card(identifier, body, session, user); return 200
            except HTTPException as exc: return exc.status_code
    with ThreadPoolExecutor(max_workers=2) as pool: results = list(pool.map(submit, range(2)))
    assert sorted(results) == [200, 409]
    with Session(db_engine) as session: assert len(session.exec(select(ReviewEvent)).all()) == 1
