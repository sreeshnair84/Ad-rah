import os
import tempfile
from app import storage


def test_save_local(tmp_path, monkeypatch):
    tmp_dir = tmp_path / "media"
    monkeypatch.setattr(storage.settings, "LOCAL_MEDIA_DIR", str(tmp_dir))
    filename = "test image.jpg"
    content = b"hello world"
    path = storage.save_local(filename, content)
    assert os.path.exists(path)
    with open(path, "rb") as fh:
        assert fh.read() == content


def test_save_media_fallback_to_local(tmp_path, monkeypatch):
    # Ensure Azure not configured
    monkeypatch.setattr(storage.settings, "AZURE_STORAGE_CONNECTION_STRING", None)
    tmp_dir = tmp_path / "media2"
    monkeypatch.setattr(storage.settings, "LOCAL_MEDIA_DIR", str(tmp_dir))
    filename = "video.mp4"
    content = b"binarydata"
    path = storage.save_media(filename, content, content_type="video/mp4")
    assert path.startswith(str(tmp_dir))
    assert os.path.exists(path)
