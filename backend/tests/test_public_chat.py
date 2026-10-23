from io import BytesIO

from reportlab.pdfgen import canvas

from app.public_assistant import _rate_store
from app.public_chat import _uploads, cleanup_uploads


def pdf(text):
    stream = BytesIO()
    page = canvas.Canvas(stream)
    page.drawString(20, 700, text)
    page.save()
    return stream.getvalue()


def test_guarded_sse_and_language(fixture_client):
    client, _, _ = fixture_client
    _rate_store.clear()
    response = client.post('/api/public/assistant/stream', json={"message": "What is an excess?"})
    assert response.status_code == 200
    assert response.headers['content-type'].startswith('text/event-stream')
    assert 'event: token' in response.text
    assert 'event: done' in response.text
    assert 'reviewed-knowledge' in response.text
    assert client.post('/api/public/assistant/stream', json={"message": " "}).status_code == 422
    response = client.post('/api/public/assistant/stream', json={"message": "excess", "language": "ar"})
    assert 'مبلغ' in response.text


def test_upload_validation_consumption_and_deletion(fixture_client):
    client, _, _ = fixture_client
    _rate_store.clear()
    assert client.post('/api/public/assistant/upload', files={"file": ('sample.pdf', pdf('Excess definition'), 'application/pdf')}).status_code == 422
    bad = client.post('/api/public/assistant/upload', data={"consent": 'true'}, files={"file": ('sample.pdf', b'fake', 'application/pdf')})
    assert bad.status_code == 422
    mismatch = client.post('/api/public/assistant/upload', data={"consent": 'true'}, files={"file": ('sample.png', pdf('Excess definition'), 'image/png')})
    assert mismatch.status_code == 415
    sensitive = client.post('/api/public/assistant/upload', data={"consent": 'true'}, files={"file": ('sample.pdf', pdf('Passport 123456'), 'application/pdf')})
    assert sensitive.status_code == 422
    response = client.post('/api/public/assistant/upload', data={"consent": 'true'}, files={"file": ('sample.pdf', pdf('Excess is a contribution'), 'application/pdf')})
    assert response.status_code == 200, response.text
    key = response.json()['attachment_id']
    assert key in _uploads
    response = client.post('/api/public/assistant/stream', json={"message": 'Explain excess', "attachments": [key]})
    assert response.status_code == 200
    assert key not in _uploads
    assert client.post('/api/public/assistant/stream', json={"message": 'Explain excess', "attachments": [key]}).status_code == 410
    assert client.delete(f'/api/public/assistant/upload/{key}').status_code == 200
    _uploads['expired'] = {"text": "sample", "expires": 0}
    cleanup_uploads()
    assert 'expired' not in _uploads


def test_voice_requires_consent_and_configuration(fixture_client, monkeypatch):
    client, _, _ = fixture_client
    _rate_store.clear()
    monkeypatch.setenv('GROQ_API_KEY', '')
    assert client.post('/api/public/assistant/transcribe', files={"file": ('voice.webm', b'fake', 'audio/webm')}).status_code == 422
    assert client.post('/api/public/assistant/transcribe', data={"consent": 'true'}, files={"file": ('voice.webm', b'fake', 'audio/webm')}).status_code == 503


def test_handoff_is_demo_not_delivery(fixture_client):
    client, _, _ = fixture_client
    _rate_store.clear()
    response = client.post('/api/public/assistant/handoff', json={"topic": "Complaint"})
    assert response.status_code == 200
    assert response.json()['ticket_ref']
    assert 'demo' in response.json()['reply'].lower()
