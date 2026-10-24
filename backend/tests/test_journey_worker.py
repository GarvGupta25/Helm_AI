from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session
from test_journey_compare_api import start
from test_journey_requests import prepare_request
from test_research_api import seed_research

from app.journey.case_models import Quotation, QuoteRequest
from app.journey.worker import process_quotes
from app.models import now


def test_delayed_quotes_timeout_retry_and_idempotency(fixture_client):
    client, _, engine = fixture_client
    seed_research(engine)
    headers, run = start(client)
    body = prepare_request(client, headers, run)
    assert client.post('/api/journey/quote-requests', headers=headers, json=body).status_code == 200
    with Session(engine) as db:
        first = db.scalars(select(QuoteRequest)).first()
        first.data = {**first.data, 'simulation': {'timeout_attempts': 1}}
        db.commit()
        clock = now()+timedelta(seconds=5)
        assert process_quotes(db, clock=clock) == 2
        assert first.status == 'queued' and first.attempts == 1
        assert process_quotes(db, clock=clock+timedelta(seconds=31)) == 1
        quotes = db.scalars(select(Quotation)).all()
        assert len(quotes) == 3
        assert all(q.data['source'] == 'synthetic' for q in quotes)
        assert process_quotes(db, clock=clock+timedelta(minutes=3)) == 0
