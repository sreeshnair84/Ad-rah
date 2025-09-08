from starlette.testclient import TestClient
from app.main import app
import os


def get_auth_token(client):
    """Helper function to get authentication token"""
    r = client.post("/api/auth/login", json={
        "email": "admin@adara.com",
        "password": "SuperAdmin123!"
    })
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    return body["access_token"], body["user"]["id"]


def test_presign_finalize_local(tmp_path):
    # ensure local media dir is the tmp_path for test isolation
    from app.config import settings

    settings.LOCAL_MEDIA_DIR = str(tmp_path)

    with TestClient(app) as client:
        # Get authentication token and user ID
        token, user_id = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        filename = "test.jpg"
        owner_id = user_id  # Use actual user ID instead of hardcoded "owner-x"
        content = b"hello-image-bytes"
        # request presign
        r = client.post("/api/uploads/presign", 
                       json={"owner_id": owner_id, "filename": filename, "content_type": "image/jpeg"},
                       headers=headers)
        assert r.status_code == 200
        body = r.json()
        upload_id = body["upload_id"]

        # upload bytes via local_upload helper
        from io import BytesIO
        files = {"file": ("test.jpg", BytesIO(content), "image/jpeg")}
        data = {"upload_id": upload_id}
        r2 = client.post("/api/uploads/local_upload", 
                        files=files, data=data,
                        headers=headers)
        assert r2.status_code == 200

        # finalize
        r3 = client.post("/api/uploads/finalize", json={
            "upload_id": upload_id,
            "owner_id": owner_id,
            "title": "Test",
            "description": "desc",
            "filename": filename,
            "content_type": "image/jpeg",
            "size": len(content),
        }, headers=headers)
        assert r3.status_code == 200, r3.text
        data = r3.json()
        assert data["status"] == "finalized"
        assert data["meta"]["owner_id"] == owner_id
        # file saved
        assert os.path.exists(data["path"])
from starlette.testclient import TestClient
from app.main import app
import os
from app.config import settings


def test_presign_and_finalize_local(tmp_path):
    # ensure local media dir is the tmp_path for test isolation
    settings.LOCAL_MEDIA_DIR = str(tmp_path)
    with TestClient(app) as client:
        # Get authentication token and user ID
        token, user_id = get_auth_token(client)
        headers = {"Authorization": f"Bearer {token}"}
        
        # presign
        r = client.post(
            "/api/uploads/presign",
            json={"owner_id": user_id, "filename": "ad.jpg", "content_type": "image/jpeg"},  # Use actual user ID
            headers=headers
        )
        assert r.status_code == 200
        body = r.json()
        upload_url = body["upload_url"]
        # extract local path from upload_url: local://<path>
        assert upload_url.startswith("local://")
        path = upload_url[len("local://") :]

        # write actual bytes to path (simulate client behavior)
        content = b"\x00\x01\x02TESTBYTES"
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "wb") as fh:
            fh.write(content)

        upload_id = body["upload_id"]

        # finalize
        r3 = client.post(
            "/api/uploads/finalize",
            json={
                "upload_id": upload_id,
                "owner_id": user_id,  # Use actual user ID
                "title": "Test Ad",
                "description": "desc",
                "filename": "ad.jpg",
                "content_type": "image/jpeg",
                "size": len(content),
            },
            headers=headers
        )
        assert r3.status_code == 200, r3.text
        data = r3.json()
        assert data["status"] == "finalized"
        assert data["meta"]["owner_id"] == user_id  # Check against actual user ID
        assert data["meta"]["filename"] == "ad.jpg"
        assert os.path.exists(data["path"])
