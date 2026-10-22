"""Public endpoint contract checks for the reviewed UK knowledge mode."""
import pytest

from app.public_assistant import _rate_store


@pytest.fixture(autouse=True)
def clear_rate_store():
    _rate_store.clear()
    yield
    _rate_store.clear()


def test_general_answer_without_inference_or_api_key(fixture_client):
    client, _, _ = fixture_client
    response = client.post('/api/public/assistant/messages', json={'message': 'How does private health cover work?'})
    assert response.status_code == 200
    assert 'NHS' in response.json()['reply']
    assert len(response.json()['reply'].split()) < 100


def test_price_request_cannot_invent_premium(fixture_client):
    client, _, _ = fixture_client
    response = client.post('/api/public/assistant/messages', json={'message': 'Give me a quote for a 35-year-old.'})
    assert response.status_code == 200
    assert 'comparison' in response.json()['reply']
    assert '£' not in response.json()['reply']


@pytest.mark.parametrize('message', ['', '   ', 'x' * 501])
def test_message_boundaries(fixture_client, message):
    client, _, _ = fixture_client
    assert client.post('/api/public/assistant/messages', json={'message': message}).status_code == 422


def test_unknown_question_has_useful_fallback(fixture_client):
    client, _, _ = fixture_client
    response = client.post('/api/public/assistant/messages', json={'message': 'Tell me about quantum gravity'})
    assert response.status_code == 200
    assert 'FAQs' in response.json()['reply']
