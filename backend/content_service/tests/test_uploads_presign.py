from starlette.testclient import TestClient
from app.main import app
import os


def test_presign_finalize_local(tmp_path):
    # ensure local media dir is the tmp_path for test isolation
    from app.config import settings

    settings.LOCAL_MEDIA_DIR = str(tmp_path)

    with TestClient(app) as client:
        filename = "test.jpg"
        owner_id = "owner-x"
        content = b"hello-image-bytes"
        # request presign
        r = client.post("/api/uploads/presign", json={"owner_id": owner_id, "filename": filename, "content_type": "image/jpeg"})
        assert r.status_code == 200
        body = r.json()
        upload_id = body["upload_id"]

        # upload bytes via local_upload helper
        r2 = client.post("/api/uploads/local_upload", json={"upload_id": upload_id, "file": content.decode('latin1')})
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
        })
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
        # presign
        r = client.post(
            "/api/uploads/presign",
            json={"owner_id": "owner-x", "filename": "ad.jpg", "content_type": "image/jpeg"},
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
                "owner_id": "owner-x",
                "title": "Test Ad",
                "description": "desc",
                "filename": "ad.jpg",
                "content_type": "image/jpeg",
                "size": len(content),
            },
        )
        assert r3.status_code == 200, r3.text
        data = r3.json()
        assert data["status"] == "finalized"
        assert data["meta"]["owner_id"] == "owner-x"
        assert data["meta"]["filename"] == "ad.jpg"
        assert os.path.exists(data["path"])
