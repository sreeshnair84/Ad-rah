from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Request
from fastapi.responses import FileResponse, StreamingResponse
from typing import List
import mimetypes
from app.storage import save_media
from app.models import ContentMeta
from app.auth import require_roles, get_current_user, get_user_company_context
from fastapi import Body
import uuid
import os
from app.config import settings
from app.repo import repo

# Import security modules
try:
    from app.security import content_scanner, audit_logger
    SECURITY_SCANNING_ENABLED = True
except ImportError:
    SECURITY_SCANNING_ENABLED = False
    import logging
    logging.warning("Security scanning not available - uploads will proceed without scanning")

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/media")
async def upload_media(
    request: Request, 
    owner_id: str, 
    files: List[UploadFile] = File(...),
    user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """
    Upload media files with comprehensive security scanning and company isolation.
    
    Features:
    - Company-scoped content isolation
    - Content security scanning
    - Copyright protection checks
    - Malware detection
    - File type validation
    - Size limits enforcement
    
    Users can only upload content for their own company.
    """
    
    # Validate company access for content ownership
    current_user_id = user.get("id")
    
    # If owner_id is different from current user, verify they belong to same company
    if owner_id != current_user_id:
        can_access_content = await repo.check_content_access_permission(
            current_user_id, owner_id, "edit"
        )
        if not can_access_content:
            raise HTTPException(
                status_code=403, 
                detail="Access denied: Cannot upload content for users outside your company"
            )
    
    saved = []
    rejected = []
    
    # Get client IP for audit logging
    client_ip = request.client.host if request.client else "unknown"
    
    for f in files:
        try:
            filename = f.filename or "upload.bin"
            ctype = f.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
            content = await f.read()
            file_size = len(content)
            
            # Log upload attempt
            if SECURITY_SCANNING_ENABLED:
                audit_logger.log_content_upload(
                    user_id=user.get('id', owner_id),
                    filename=filename,
                    content_type=ctype,
                    size=file_size,
                    ip_address=client_ip
                )
            
            # Security scanning if enabled
            if SECURITY_SCANNING_ENABLED:
                scan_result = await content_scanner.scan_content(content, filename, ctype)
                
                if scan_result.security_level == "blocked":
                    rejected.append({
                        "filename": filename,
                        "reason": "security_blocked",
                        "details": scan_result.content_warnings,
                        "scan_id": scan_result.scan_id
                    })
                    continue
                elif scan_result.security_level == "suspicious":
                    # Content needs manual review - save with pending status
                    pass
            else:
                # Basic validation without security module
                top = ctype.split("/")[0] if ctype else ""
                if top not in ("image", "video", "text"):
                    rejected.append({
                        "filename": filename,
                        "reason": "unsupported_type",
                        "details": f"Unsupported media type: {ctype}"
                    })
                    continue
                
                # Basic size check
                max_size = getattr(settings, 'CONTENT_MAX_SIZE_MB', 100) * 1024 * 1024
                if file_size > max_size:
                    rejected.append({
                        "filename": filename,
                        "reason": "file_too_large",
                        "details": f"File size ({file_size} bytes) exceeds limit"
                    })
                    continue
            
            # Save the file
            path = save_media(filename, content, content_type=ctype)
            
            # Create content metadata
            content_status = "pending"  # Default to pending for manual review
            if SECURITY_SCANNING_ENABLED and hasattr(scan_result, 'security_level'):
                if scan_result.security_level == "safe":
                    content_status = "approved"
                elif scan_result.security_level == "suspicious":
                    content_status = "pending"
            
            meta = ContentMeta(
                id=None,
                owner_id=owner_id,
                filename=filename,
                content_type=ctype,
                size=file_size,
                status=content_status
            )
            
            saved_meta = await repo.save_content_meta(meta)
            
            # Add security scan information to response
            saved_item = {"meta": saved_meta, "path": path}
            if SECURITY_SCANNING_ENABLED and 'scan_result' in locals():
                saved_item.update({
                    "security_scan": {
                        "scan_id": scan_result.scan_id,
                        "security_level": scan_result.security_level,
                        "recommendation": scan_result.recommendation,
                        "warnings": scan_result.content_warnings
                    }
                })
            
            saved.append(saved_item)
            
        except Exception as e:
            rejected.append({
                "filename": filename,
                "reason": "processing_error",
                "details": str(e)
            })
    
    response = {"uploaded": saved}
    if rejected:
        response["rejected"] = rejected
    
    return response


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


@router.get("/files/{filename}")
async def serve_file(filename: str):
    """Serve uploaded media files"""
    try:
        # Check local media directory for the file
        local_dir = settings.LOCAL_MEDIA_DIR
        file_path = os.path.join(local_dir, filename)
        
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        
        # Determine content type
        content_type, _ = mimetypes.guess_type(filename)
        if not content_type:
            content_type = "application/octet-stream"
        
        return FileResponse(
            path=file_path,
            media_type=content_type,
            filename=filename
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error serving file: {e}")
