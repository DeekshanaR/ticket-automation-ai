from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_create_ticket_is_classified_and_assigned():
    r = client.post("/tickets", json={
        "title": "VPN not connecting",
        "description": "VPN client shows timeout error when connecting from home",
    })
    assert r.status_code == 201
    body = r.json()
    assert body["category"] == "Network"
    assert body["status"] == "ASSIGNED"
    assert body["assignee"] == "network-team"
    assert body["ai_suggestion"]


def test_full_lifecycle_and_history():
    t = client.post("/tickets", json={"title": "Mailbox full", "description": "quota exceeded warning in outlook"}).json()
    for status in ("IN_PROGRESS", "RESOLVED", "CLOSED"):
        assert client.post(f"/tickets/{t['id']}/transition", json={"status": status}).status_code == 200
    history = client.get(f"/tickets/{t['id']}/history").json()
    assert [h["to_status"] for h in history] == ["NEW", "TRIAGED", "ASSIGNED", "IN_PROGRESS", "RESOLVED", "CLOSED"]


def test_invalid_transition_returns_409():
    t = client.post("/tickets", json={"title": "Printer offline", "description": "printer jobs stuck in queue"}).json()
    r = client.post(f"/tickets/{t['id']}/transition", json={"status": "CLOSED"})
    assert r.status_code == 409


def test_not_found_and_validation():
    assert client.get("/tickets/9999").status_code == 404
    assert client.post("/tickets", json={"title": "x", "description": "y"}).status_code == 422


def test_stats_and_filters():
    client.post("/tickets", json={"title": "VPN down", "description": "vpn timeout cannot connect"})
    assert client.get("/stats").json()["by_status"]
    assert all(t["category"] == "Network" for t in client.get("/tickets?category=Network").json())
