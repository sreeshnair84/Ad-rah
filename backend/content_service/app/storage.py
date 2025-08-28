import os
import logging
import re
from typing import Optional
from app.config import settings

logger = logging.getLogger(__name__)


def ensure_local_dir():
    os.makedirs(settings.LOCAL_MEDIA_DIR, exist_ok=True)


def _safe_filename(filename: str) -> str:
    # Remove path separators and unsafe chars
    name = os.path.basename(filename or "upload.bin")
    # keep ascii letters, numbers, dot, dash, underscore
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", name)
    return safe


def save_local(filename: str, content: bytes) -> str:
    ensure_local_dir()
    safe_name = _safe_filename(filename)
    path = os.path.join(settings.LOCAL_MEDIA_DIR, safe_name)
    with open(path, "wb") as fh:
        fh.write(content)
    logger.info("Saved media locally: %s", path)
    return path


def presign_local(filename: str) -> str:
    """Return a local filesystem path where a client may upload a file.

    This is a simple 'presign' for local development: the client should write
    the bytes to the returned path (atomic behavior is the caller's responsibility).
    """
    ensure_local_dir()
    safe_name = _safe_filename(filename)
    # include a random suffix to avoid collisions
    import uuid

    upload_id = str(uuid.uuid4())
    path = os.path.join(settings.LOCAL_MEDIA_DIR, f"{upload_id}--{safe_name}")
    return path


# Try to import Azure SDK; if not available, we gracefully fall back to local.
try:
    from azure.storage.blob import BlobServiceClient, ContentSettings

    def _ensure_container(client: BlobServiceClient, container_name: str):
        try:
            container_client = client.get_container_client(container_name)
            if not container_client.exists():
                container_client.create_container()
            return container_client
        except Exception:
            # In some older SDK versions exists() may not be available or permissions may differ.
            try:
                client.create_container(container_name)
                return client.get_container_client(container_name)
            except Exception as exc:
                logger.exception("Failed to ensure azure container %s: %s", container_name, exc)
                raise

    def save_azure(filename: str, content: bytes, content_type: Optional[str] = None) -> str:
        conn = settings.AZURE_STORAGE_CONNECTION_STRING
        if not conn:
            raise RuntimeError("Azure connection string not configured")
        client = BlobServiceClient.from_connection_string(conn)
        container = settings.AZURE_CONTAINER_NAME
        # ensure container exists
        _ensure_container(client, container)
        blob_name = _safe_filename(filename)
        blob_client = client.get_blob_client(container=container, blob=blob_name)
        kwargs = {}
        if content_type:
            kwargs["content_settings"] = ContentSettings(content_type=content_type)
        blob_client.upload_blob(content, overwrite=True, **kwargs)
        url = f"azure://{container}/{blob_name}"
        logger.info("Uploaded media to Azure: %s", url)
        return url

except Exception:
    BlobServiceClient = None
    ContentSettings = None


def save_media(filename: str, content: bytes, content_type: Optional[str] = None) -> str:
    """Save media to Azure if configured, otherwise save locally.

    Returns a path or an Azure pseudo-URL (azure://container/blob).
    """
    # Prefer Azure if configured and SDK available
    if getattr(settings, "AZURE_STORAGE_CONNECTION_STRING", None) and BlobServiceClient is not None:
        try:
            return save_azure(filename, content, content_type=content_type)
        except Exception as exc:
            logger.warning("Azure upload failed, falling back to local storage: %s", exc)
    return save_local(filename, content)
