from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from typing import List
from app.storage import save_media
from app.models import ContentMeta
from app.auth import require_roles
from fastapi import Body
import uuid
import os
from app.config import settings
from app.repo import repo

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/media")
async def upload_media(owner_id: str, files: List[UploadFile] = File(...), user=Depends(require_roles("partner", "admin"))):
    """Upload media files. Uses Azure Blob when AZURE_STORAGE_CONNECTION_STRING is set, otherwise saves locally.

    owner_id: required query parameter identifying the uploading user/partner.
    """
    saved = []
    for f in files:
        ctype = f.content_type or ""
        top = ctype.split("/")[0] if ctype else ""
        if top not in ("image", "video", "text"):
            raise HTTPException(status_code=400, detail=f"Unsupported media type: {ctype}")
        content = await f.read()
        filename = f.filename or "upload.bin"
        path = save_media(filename, content)
        meta = ContentMeta(id=None, owner_id=owner_id, filename=filename, content_type=ctype, size=len(content))
        saved_meta = await repo.save_content_meta(meta)
        saved.append({"meta": saved_meta, "path": path})
    return {"uploaded": saved}


@router.post("/presign")
async def presign_upload(owner_id: str = Body(...), filename: str = Body(...), content_type: str = Body(None)):
    """Return an upload_id and a local upload URL for tests/dev when Azure is not configured."""
    upload_id = str(uuid.uuid4())
    # local upload path (client can PUT bytes here in local/dev mode)
    local_dir = settings.LOCAL_MEDIA_DIR
    os.makedirs(local_dir, exist_ok=True)
    upload_path = os.path.join(local_dir, f"{upload_id}.upload")
    return {"upload_id": upload_id, "upload_url": f"local://{upload_path}", "filename": filename, "content_type": content_type}


@router.post("/local_upload")
async def local_upload(upload_id: str = Body(...), file: bytes = Body(...)):
    """Test-only endpoint: accept raw bytes and write to local upload path matching presign."""
    local_dir = settings.LOCAL_MEDIA_DIR
    path = os.path.join(local_dir, f"{upload_id}.upload")
    with open(path, "wb") as fh:
        fh.write(file)
    return {"status": "ok", "path": path}


@router.post("/finalize")
async def finalize_upload(upload_id: str = Body(...), owner_id: str = Body(...), title: str = Body(None), description: str = Body(None), filename: str = Body(...), content_type: str = Body(None), size: int = Body(...)):
    """Finalize an upload: validate local file exists and create ContentMeta entry.

    In Azure-enabled mode this function would move/copy the blob to final container and record metadata.
    """
    local_dir = settings.LOCAL_MEDIA_DIR
    path = os.path.join(local_dir, f"{upload_id}.upload")
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="uploaded file not found")
    actual_size = os.path.getsize(path)
    if actual_size != int(size):
        raise HTTPException(status_code=400, detail=f"size mismatch: expected {size}, got {actual_size}")
    # read bytes and save via save_media to choose backend
    with open(path, "rb") as fh:
        content = fh.read()
    saved_path = save_media(filename, content, content_type=content_type)
    meta = ContentMeta(id=None, owner_id=owner_id, filename=filename, content_type=content_type or "application/octet-stream", size=len(content))
    saved_meta = await repo.save_content_meta(meta)
    return {"status": "finalized", "meta": saved_meta, "path": saved_path}
