from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from app.models import ContentMetadata, UploadResponse, ModerationResult
import asyncio
try:
    import aiofiles
    _AIOFILES_AVAILABLE = True
except Exception:
    aiofiles = None
    _AIOFILES_AVAILABLE = False
import uuid
from app.repo import repo
import os
import random
from typing import List

router = APIRouter()

STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "storage")
os.makedirs(STORAGE_DIR, exist_ok=True)


@router.post("/upload-file", response_model=UploadResponse)
async def upload_file(file: UploadFile = File(...), owner_id: str = Form(...)):
    """Accept a file upload and simulate quarantine + AI moderation trigger."""
    file_id = str(uuid.uuid4())
    filename = f"{file_id}_{file.filename}"
    filepath = os.path.join(STORAGE_DIR, filename)

    # save file to local storage (placeholder for Azure Blob upload)
    try:
        if _AIOFILES_AVAILABLE:
            async with aiofiles.open(filepath, "wb") as out_file:
                content = await file.read()
                await out_file.write(content)
        else:
            # fallback: read bytes asynchronously then write on thread executor
            content = await file.read()
            loop = asyncio.get_event_loop()

            def _write_bytes(path, b):
                with open(path, "wb") as fh:
                    fh.write(b)

            await loop.run_in_executor(None, _write_bytes, filepath, content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"failed to save file: {e}")

    # Simulated virus scan -- here just a random pass
    virus_ok = random.random() > 0.01
    if not virus_ok:
        return UploadResponse(filename=filename, status="rejected", message="Virus detected")

    # Simulated AI moderation enqueue (we'll return quarantined until moderation runs)
    return UploadResponse(filename=filename, status="quarantine", message="File saved and queued for moderation")


@router.post("/metadata", response_model=ContentMetadata)
async def post_metadata(metadata: ContentMetadata):
    # persist metadata
    metadata.id = metadata.id or str(uuid.uuid4())
    saved = await repo.save(metadata)
    return saved



@router.get("/{content_id}")
async def get_metadata(content_id: str):
    item = await repo.get(content_id)
    if not item:
        raise HTTPException(status_code=404, detail="not found")
    return item


@router.get("/")
async def list_metadata():
    return await repo.list()


@router.post("/moderation/simulate", response_model=ModerationResult)
async def simulate_moderation(content_id: str = Form(...)):
    # Simulate an AI moderation decision
    confidence = round(random.uniform(0.4, 0.99), 3)
    if confidence > 0.95:
        action = "approved"
    elif confidence >= 0.70:
        action = "needs_review"
    else:
        action = "rejected"

    reason = None
    if action != "approved":
        reason = "simulated policy flag"

    return ModerationResult(content_id=content_id, ai_confidence=confidence, action=action, reason=reason)


@router.get("/ping")
async def ping():
    return JSONResponse({"pong": True})
