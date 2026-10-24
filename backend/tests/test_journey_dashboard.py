from datetime import timedelta

import fitz
from sqlalchemy.orm import Session
from test_journey_access import link_token, make_case

from app.journey.worker import process_quotes
from app.models import now


def test_dashboard_compares_downloads_and_scopes_frozen_quotes(fixture_client):
    client, _, engine = fixture_client
    headers, _, case = make_case(client, engine)
    assert client.get('/api/journey/dashboard').status_code == 410
    with Session(engine) as db:
        assert process_quotes(db, clock=now()+timedelta(seconds=5)) == 3
    token = link_token(client, headers, case)
    assert client.post('/api/journey/access-links/exchange', json={'token': token}).status_code == 200
    data = client.get('/api/journey/dashboard').json()
    assert len(data['quotations']) == 3
    first = data['quotations'][0]
    pdf = client.get('/api/journey/quotations/'+first['id']+'/document')
    assert pdf.status_code == 200 and pdf.headers['content-type'] == 'application/pdf'
    assert pdf.headers['cache-control'] == 'no-store'
    doc = fitz.open(stream=pdf.content, filetype='pdf')
    assert 'SIMULATION' in ''.join(page.get_text() for page in doc)
    response = client.post('/api/journey/quotations/'+first['id']+'/questions', json={'question': 'Break down my premium'})
    assert response.json()['citations'][0]['value'] == first['item']['quote']['base_pence']
    assert client.get('/api/journey/quotations/not-owned/document').status_code == 404
    assert client.post('/api/journey/dashboard/logout').status_code == 200
    assert client.get('/api/journey/dashboard').status_code == 410
