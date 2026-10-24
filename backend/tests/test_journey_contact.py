from app.public_assistant import _rate_store


def test_fake_contact_verification_is_scoped_bounded_and_single_use(fixture_client):
    client, _, _ = fixture_client
    _rate_store.clear()
    token = client.post('/api/journey/sessions').json()['session_token']
    headers = {'X-Journey-Session': token}
    body = {'channel': 'email', 'destination': 'customer@example.test', 'demo_acknowledged': True}
    contact = client.post('/api/journey/contacts/challenges', headers=headers, json=body).json()
    assert 'code' not in contact
    assert client.get('/api/journey/demo/inbox').status_code == 404
    inbox = client.get('/api/journey/demo/inbox', headers=headers).json()
    code = inbox[0]['content']['code']
    assert client.post('/api/journey/contacts/verify', headers=headers, json={'contact_id': contact['contact_id'], 'code': code}).json()['real_ownership_verified'] is False
    assert client.post('/api/journey/contacts/verify', headers=headers, json={'contact_id': contact['contact_id'], 'code': code}).status_code == 410
    body['destination'] = 'real@example.com'
    assert client.post('/api/journey/contacts/challenges', headers=headers, json=body).status_code == 422
