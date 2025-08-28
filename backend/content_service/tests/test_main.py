from starlette.testclient import TestClient
from app.main import app


def test_health():
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_metadata_roundtrip():
    payload = {
        "title": "Test Ad",
        "description": "A sample ad",
        "owner_id": "owner-123",
        "categories": ["drinks"],
        "tags": ["promo"]
    }
    client = TestClient(app)
    r = client.post("/api/content/metadata", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["title"] == "Test Ad"
    assert "id" in body

    # fetch it back
    cid = body["id"]
    r2 = client.get(f"/api/content/{cid}")
    assert r2.status_code == 200
    assert r2.json()["title"] == "Test Ad"

    # list
    r3 = client.get("/api/content/")
    assert r3.status_code == 200
    assert any(i["id"] == cid for i in r3.json())
