from sqlalchemy.orm import Session

from app.public_assistant import _rate_store
from app.research.generator import CONFIG, generate
from app.research.models import ResearchRecord


def seed_research(engine):
    data = generate({**CONFIG, "profiles": 0, "histories": 0})
    with Session(engine) as db:
        for kind in ("variants", "clauses"):
            db.add_all([ResearchRecord(id=item["id"], kind=kind, version=CONFIG["version"], data=item) for item in data[kind]])
        db.commit()


def test_research_confirm_undo_whatif_memory_and_delete(fixture_client, monkeypatch):
    from cryptography.fernet import Fernet
    monkeypatch.setenv("RESEARCH_STATE_KEY", Fernet.generate_key().decode())
    client, _, engine = fixture_client
    _rate_store.clear()
    seed_research(engine)
    response = client.post("/api/v1/research/sessions", json={"preferred": ["physio"]})
    assert response.status_code == 200, response.text
    data = response.json()
    headers = {"X-Research-Session": data["session_token"]}
    assert client.get("/api/v1/profile/history").status_code == 404
    proposed = client.post("/api/v1/conversation/message", json={"message": "Mental health is essential"}, headers=headers).json()
    assert proposed["proposed"]["required"] == ["mental_health"]
    assert client.get("/api/v1/profile/history", headers=headers).json()["version"] == 1
    changed = client.post("/api/v1/conversation/message", json={"message": "Mental health is essential", "confirm": True}, headers=headers).json()
    assert changed["diff"]["required"]["after"] == ["mental_health"]
    assert all(i["plan"]["limits"]["mental_health"] for i in changed["result"]["items"])
    run = changed["result"]["run_id"]
    hypothetical = client.post(f"/api/v1/recommendations/{run}/what-if", json={"required": ["maternity"]}, headers=headers)
    assert hypothetical.json()["result"]["no_fit"]
    assert client.get("/api/v1/profile/history", headers=headers).json()["profile"]["required"] == ["mental_health"]
    result = client.patch("/api/v1/consent", json={"durable_memory": True, "personalization": True}, headers=headers)
    assert result.status_code == 200
    assert client.get("/api/v1/memory", headers=headers).json()[0]["field"] == "preferred"
    assert client.post("/api/v1/profile/undo", headers=headers).json()["profile"]["required"] == []
    assert client.delete("/api/v1/memory/preferred", headers=headers).status_code == 200
    assert client.get("/api/v1/memory", headers=headers).json() == []
    assert client.patch("/api/v1/consent", json={"training": True}, headers=headers).status_code == 422
    assert client.delete("/api/v1/me", headers=headers).status_code == 200
    assert client.get("/api/v1/me", headers=headers).status_code == 404


def test_session_isolation_and_server_trust(fixture_client):
    client, _, engine = fixture_client
    _rate_store.clear()
    seed_research(engine)
    a = client.post("/api/v1/research/sessions", json={}).json()
    b = client.post("/api/v1/research/sessions", json={}).json()
    headers = {"X-Research-Session": b["session_token"]}
    assert client.get(f"/api/v1/recommendations/{a['result']['run_id']}", headers=headers).status_code == 404
    assert client.patch("/api/v1/profile", json={"fusion": 100}, headers=headers).status_code == 422


def test_state_encrypted_admin_guard_and_exact_confirmation(fixture_client, monkeypatch):
    from sqlalchemy import text
    client, _, engine = fixture_client
    _rate_store.clear()
    monkeypatch.setenv("SYNTHETIC_ADMIN_TOKEN", "")
    monkeypatch.setenv("RESEARCH_STATE_KEY", "")
    seed_research(engine)
    response = client.post("/api/v1/research/sessions", json={"required": ["mental_health"]})
    assert response.status_code == 200
    headers = {"X-Research-Session": response.json()["session_token"]}
    with engine.connect() as connection:
        raw = str(connection.execute(text("SELECT data FROM research_session")).scalar())
        assert 'ciphertext' in raw
        assert 'mental_health' not in raw
    assert client.patch("/api/v1/consent", json={"durable_memory": True}, headers=headers).status_code == 503
    assert client.post("/api/v1/synthetic/generate", json={}).status_code == 403
    assert client.post("/api/v1/conversation/message", json={"message": "physio", "confirm": True}, headers=headers).status_code == 409
    client.post("/api/v1/conversation/message", json={"message": "physio"}, headers=headers)
    assert client.post("/api/v1/conversation/message", json={"message": "dental", "confirm": True}, headers=headers).status_code == 409
    confirmed = client.post("/api/v1/conversation/message", json={"message": "physio", "confirm": True}, headers=headers)
    assert confirmed.status_code == 200
    assert confirmed.json()["profile"]["required"] == ['mental_health']
    result = confirmed.json()['result']
    assert client.get(f"/api/v1/recommendations/{result['run_id']}/why-not/nonexistent", headers=headers).status_code == 404
