from starlette.testclient import TestClient
from app.main import app
import time


def test_worker_job():
    with TestClient(app) as client:
        # create content
        payload = {"title": "WorkerAd", "owner_id": "owner-y", "description": "for worker"}
        r = client.post("/api/content/metadata", json=payload)
        assert r.status_code == 200
        cid = r.json()["id"]

        r2 = client.post("/api/moderation/job/enqueue", data={"content_id": cid})
        assert r2.status_code == 200
        jid = r2.json()["job_id"]

    # wait for completion using the wait endpoint
    r3 = client.post(f"/api/moderation/job/{jid}/wait", json={"timeout": 5.0})
    assert r3.status_code == 200, r3.text
    status = r3.json().get("status")
    assert status == "done"
    assert "review_id" in r3.json()
