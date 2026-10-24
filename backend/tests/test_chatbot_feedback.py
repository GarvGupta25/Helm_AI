from datetime import timedelta
from uuid import uuid4

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.chatbot_feedback import ChatFeedback, FeedbackBase, feedback_db, purge_feedback
from app.main import app
from app.models import Base, now
from app.public_assistant import _rate_store


def test_feedback_is_durable_separate_deduplicated_and_opt_in(fixture_client):
    client, _, main_engine = fixture_client
    _rate_store.clear()
    engine = create_engine('sqlite://', poolclass=StaticPool, connect_args={'check_same_thread': False})
    FeedbackBase.metadata.create_all(engine)

    def database():
        with Session(engine) as db:
            yield db

    app.dependency_overrides[feedback_db] = database
    body = {'session_id': str(uuid4()), 'message_id': str(uuid4()), 'kind': 'feedback', 'rating': 'down', 'category': 'unclear', 'comment': 'Please make the explanation shorter.', 'answer_excerpt': 'Must not persist without permission'}
    response = client.post('/api/public/assistant/feedback', json=body)
    assert response.status_code == 200 and response.json()['recorded'] is True
    reference = response.json()['reference']
    update = {'session_id': body['session_id'], 'message_id': body['message_id'], 'rating': 'up'}
    assert client.post('/api/public/assistant/feedback', json=update).json()['reference'] == reference
    with Session(engine) as db:
        rows = db.scalars(select(ChatFeedback)).all()
        assert len(rows) == 1 and rows[0].rating == 'up'
        assert rows[0].data['answer_excerpt'] == ''
        assert rows[0].data['comment'] == body['comment']
        assert rows[0].session_hash != body['session_id']
        raw = db.scalar(text('select data from chatbot_feedback'))
        assert body['comment'] not in raw
    assert 'chatbot_feedback' not in Base.metadata.tables
    assert client.get('/api/public/assistant/feedback').status_code == 405
    report = {**body, 'kind': 'issue', 'rating': None, 'category': 'technical', 'include_answer': True, 'answer_excerpt': 'Fictional assistant response'}
    assert client.post('/api/public/assistant/feedback', json=report).status_code == 200
    with Session(engine) as db:
        issue = db.scalar(select(ChatFeedback).where(ChatFeedback.kind == 'issue'))
        assert issue.data['answer_shared'] and issue.data['answer_excerpt'] == report['answer_excerpt']
        issue.updated_at = now()-timedelta(days=91)
        db.commit()
        assert purge_feedback(db) == 1
        db.commit()
    assert client.post('/api/public/assistant/feedback', json={**body, 'rating': None}).status_code == 422
    assert client.post('/api/public/assistant/feedback', json={**report, 'comment': ''}).status_code == 422
    engine.dispose()
