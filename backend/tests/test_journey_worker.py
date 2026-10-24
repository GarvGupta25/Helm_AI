from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session
from test_journey_compare_api import start
from test_journey_requests import prepare_request
from test_research_api import seed_research

from app.journey.case_models import Quotation, QuoteRequest
from app.journey.worker import process_quotes
from app.models import now


def test_partial_response_and_timeout_exhaustion_are_explicit(fixture_client):
    from copy import deepcopy
    client, _, engine = fixture_client
    seed_research(engine)
    headers, run = start(client)
    body = prepare_request(client, headers, run)
    client.post('/api/journey/quote-requests', headers=headers, json=body)
    with Session(engine) as db:
        requests = db.scalars(select(QuoteRequest)).all()
        first, second = requests[:2]
        payload = deepcopy(first.data)
        other = deepcopy(payload['items'][0])
        other['id'] += ':partial-fixture'
        payload['items'].append(other)
        payload['simulation'] = {'partial': True}
        first.data = payload
        second.data = {**second.data, 'simulation': {'timeout_attempts': 3}}
        db.commit()
        clock = now()+timedelta(seconds=5)
        process_quotes(db, clock=clock)
        assert first.status == 'partial'
        assert len(db.scalars(select(Quotation).where(Quotation.request_id == first.id)).all()) == 1
        process_quotes(db, clock=clock+timedelta(seconds=31))
        process_quotes(db, clock=clock+timedelta(seconds=100))
        assert second.status == 'failed' and second.attempts == 3
        assert not db.scalars(select(Quotation).where(Quotation.request_id == second.id)).all()


def test_swapped_adapter_cannot_change_server_prices(fixture_client):
    from copy import deepcopy
    client, _, engine = fixture_client
    seed_research(engine)
    headers, run = start(client)
    body = prepare_request(client, headers, run)
    client.post('/api/journey/quote-requests', headers=headers, json=body)

    class InvalidAdapter:
        def request(self, payload, attempt):
            items = deepcopy(payload['items'])
            items[0]['quote']['monthly_pence'] += 1
            return items

    with Session(engine) as db:
        assert process_quotes(db, clock=now()+timedelta(seconds=5), adapter=InvalidAdapter()) == 0
        assert not db.scalars(select(Quotation)).all()
        assert all(r.status == 'failed' for r in db.scalars(select(QuoteRequest)))


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
