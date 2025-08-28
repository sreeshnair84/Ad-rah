from starlette.testclient import TestClient
from app.main import app


def test_token_and_me():
    client = TestClient(app)
    # Obtain token
    r = client.post("/api/auth/token", data={"username": "partner1", "password": "password1"})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    token = body["access_token"]

    # Use token to call /me
    r2 = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    assert r2.json()["user"]["username"] == "partner1"
