from starlette.testclient import TestClient
from app.main import app


def test_moderation_flow():
    client = TestClient(app)
    # create metadata first
    payload = {"title": "ModAd", "owner_id": "owner-x", "description": "for mod"}
    r = client.post("/api/content/metadata", json=payload)
    assert r.status_code == 200
    cid = r.json()["id"]

    # enqueue
    r2 = client.post("/api/moderation/enqueue", data={"content_id": cid})
    assert r2.status_code == 200
    review = r2.json()
    assert review.get("content_id") == cid
    rid = review.get("id")

    # list queue
    r3 = client.get("/api/moderation/queue")
    assert r3.status_code == 200
    assert any(r.get("id") == rid for r in r3.json())

    # post decision
    r4 = client.post(f"/api/moderation/{rid}/decision", data={"decision": "approve", "reviewer_id": "sup-1"})
    assert r4.status_code == 200
    assert r4.json()["action"].startswith("manual_")
