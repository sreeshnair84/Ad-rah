"""
Upload Management API
Implements presign/finalize upload flow for secure file uploads
"""
import os
import uuid
import logging
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel

from app.api.auth import get_current_user, get_user_company_context
from app.models import ContentMeta, UserProfile
from app.repo import repo
from app.storage import save_media, presign_local
from app.config import settings
from app.security.audit_logger import audit_logger
from app.utils.serialization import safe_json_response

logger = logging.getLogger(__name__)

# Security scanning configuration
try:
    SECURITY_SCANNING_ENABLED = True
    # Test if content scanner is available
    from app.security.content_scanner import content_scanner
except ImportError:
    SECURITY_SCANNING_ENABLED = False
    logger.warning("Security scanning not available - uploads will proceed without scanning")

router = APIRouter(prefix="/uploads", tags=["uploads"])


class PresignRequest(BaseModel):
    owner_id: str
    filename: str
    content_type: str
    size: Optional[int] = None


class FinalizeRequest(BaseModel):
    upload_id: str
    owner_id: str
    title: str
    description: Optional[str] = None
    filename: str
    content_type: str
    size: int
    category: Optional[str] = None
    tags: Optional[list] = None


@router.post("/presign")
async def presign_upload(
    request: PresignRequest,
    current_user: UserProfile = Depends(get_current_user),
    company_context: dict = Depends(get_user_company_context)
):
    """Generate presigned upload URL for secure file upload"""
    try:
        # Validate user permissions
        if request.owner_id != current_user.id:
            can_access = await repo.check_content_access_permission(
                current_user.id, request.owner_id, "edit"
            )
            if not can_access:
                raise HTTPException(status_code=403, detail="Access denied")

        # Generate upload ID
        upload_id = str(uuid.uuid4())

        # Create presigned URL based on storage type
        azure_conn_str = getattr(settings, 'AZURE_STORAGE_CONNECTION_STRING', None)
        logger.info(f"DEBUG: azure_conn_str = {repr(azure_conn_str)}")
        logger.info(f"DEBUG: isinstance(azure_conn_str, str) = {isinstance(azure_conn_str, str)}")
        if azure_conn_str is not None:
            logger.info(f"DEBUG: azure_conn_str.strip() = {repr(azure_conn_str.strip())}")
        logger.info(f"DEBUG: Final condition = {(azure_conn_str is not None and isinstance(azure_conn_str, str) and azure_conn_str.strip())}")
        logger.info(f"DEBUG: ENVIRONMENT = {getattr(settings, 'ENVIRONMENT', 'unknown')}")
        
        # In development, always use local storage for testing compatibility
        if (getattr(settings, 'ENVIRONMENT', 'production').lower() == 'development' or
            not (azure_conn_str is not None and 
                 isinstance(azure_conn_str, str) and 
                 azure_conn_str.strip())):
            # Local storage presign
            local_path = presign_local(request.filename)
            upload_url = f"local://{local_path}"
            logger.info(f"DEBUG: Using local URL: {upload_url}")
        else:
            # Azure storage presign (would need azure implementation)
            upload_url = f"azure://{upload_id}"
            local_path = None
            logger.info(f"DEBUG: Using Azure URL: {upload_url}")

        # Store upload metadata temporarily (in production, use Redis/cache)
        upload_meta = {
            "upload_id": upload_id,
            "owner_id": request.owner_id,
            "filename": request.filename,
            "content_type": request.content_type,
            "size": request.size,
            "upload_url": upload_url,
            "path": local_path,  # Store the local path for finalize
            "created_at": datetime.utcnow().isoformat(),
            "status": "pending"
        }

        # For now, store in memory (production should use proper cache)
        if not hasattr(router, '_pending_uploads'):
            router._pending_uploads = {}
        router._pending_uploads[upload_id] = upload_meta

        logger.info(f"Presigned upload for {request.filename} by user {current_user.id}")

        return {
            "upload_id": upload_id,
            "upload_url": upload_url,
            "expires_in": 3600  # 1 hour
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Presign failed: {e}")
        raise HTTPException(status_code=500, detail=f"Presign failed: {e}")


@router.post("/local_upload")
async def local_upload(
    upload_id: str = Form(...),
    file: UploadFile = File(...),
    current_user: UserProfile = Depends(get_current_user)
):
    """Handle local file upload (helper for testing)"""
    try:
        # Get upload metadata
        if not hasattr(router, '_pending_uploads'):
            raise HTTPException(status_code=404, detail="Upload not found")

        upload_meta = router._pending_uploads.get(upload_id)
        if not upload_meta:
            raise HTTPException(status_code=404, detail="Upload not found")

        # Validate ownership
        if upload_meta["owner_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Read file content
        content = await file.read()

        # Save file
        path = save_media(upload_meta["filename"], content, upload_meta["content_type"])
        logger.info(f"save_media returned path: {path}")

        # Update metadata
        upload_meta["status"] = "uploaded"
        upload_meta["path"] = path
        upload_meta["actual_size"] = len(content)
        logger.info(f"Stored path in upload_meta: {upload_meta.get('path')}")

        logger.info(f"Local upload completed for {upload_meta['filename']}")

        return {"status": "uploaded", "path": path}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Local upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


@router.post("/finalize")
async def finalize_upload(
    request: FinalizeRequest,
    current_user: UserProfile = Depends(get_current_user),
    company_context: dict = Depends(get_user_company_context)
):
    """Finalize upload and create content metadata"""
    try:
        # Validate user permissions
        if request.owner_id != current_user.id:
            can_access = await repo.check_content_access_permission(
                current_user.id, request.owner_id, "edit"
            )
            if not can_access:
                raise HTTPException(status_code=403, detail="Access denied")

        # Get upload metadata
        if not hasattr(router, '_pending_uploads'):
            raise HTTPException(status_code=404, detail="Upload not found")

        upload_meta = router._pending_uploads.get(request.upload_id)
        if not upload_meta:
            raise HTTPException(status_code=404, detail="Upload not found")

        # Validate metadata matches
        if (upload_meta["filename"] != request.filename or
            upload_meta["content_type"] != request.content_type):
            raise HTTPException(status_code=400, detail="Metadata mismatch")

        # Get file path
        logger.info(f"AZURE_STORAGE_CONNECTION_STRING: {repr(getattr(settings, 'AZURE_STORAGE_CONNECTION_STRING', None))}")
        logger.info(f"hasattr check: {hasattr(settings, 'AZURE_STORAGE_CONNECTION_STRING')}")
        logger.info(f"value check: {bool(settings.AZURE_STORAGE_CONNECTION_STRING)}")
        logger.info(f"strip check: {bool(str(settings.AZURE_STORAGE_CONNECTION_STRING).strip())}")

        azure_conn_str = getattr(settings, 'AZURE_STORAGE_CONNECTION_STRING', None)
        # In development, always use local storage for testing compatibility
        if (getattr(settings, 'ENVIRONMENT', 'production').lower() == 'development' or
            not (azure_conn_str is not None and 
                 isinstance(azure_conn_str, str) and 
                 azure_conn_str.strip())):
            # Local storage
            file_path = upload_meta.get("path")
            logger.info(f"Using local path: {file_path}")
            if not file_path or not os.path.exists(file_path):
                raise HTTPException(status_code=404, detail="File not found")
        else:
            # Azure/Azurite storage - get the actual URL from upload_meta
            file_path = upload_meta.get("path")
            if not file_path:
                # Fallback to azure:// URL if path not stored
                file_path = f"azure://{request.upload_id}"
            logger.info(f"Using Azure/Azurite path: {file_path}")

        # Security scanning
        content_status = "pending"
        if SECURITY_SCANNING_ENABLED and file_path.startswith(settings.LOCAL_MEDIA_DIR):
            try:
                with open(file_path, "rb") as f:
                    content = f.read()

                audit_logger.log_content_upload(
                    user_id=current_user.id,
                    filename=request.filename,
                    content_type=request.content_type,
                    size=request.size,
                    ip_address="unknown"  # Would need to get from request
                )

                scan_result = await content_scanner.scan_content(content, request.filename, request.content_type)
                if scan_result.security_level == "blocked":
                    # Clean up file if blocked
                    try:
                        os.unlink(file_path)
                    except:
                        pass
                    raise HTTPException(status_code=400, detail="Content blocked by security scan")

                content_status = "approved" if scan_result.security_level == "safe" else "pending"

            except Exception as scan_error:
                logger.warning(f"Security scan failed: {scan_error}")
                content_status = "pending"

        # Create content metadata
        meta = ContentMeta(
            id=None,
            owner_id=request.owner_id,
            filename=request.filename,
            content_type=request.content_type,
            size=request.size,
            status=content_status,
            title=request.title,
            description=request.description,
            category=request.category,
            tags=request.tags or []
        )

        saved_meta = await repo.save_content_meta(meta)

        # Clean up pending upload
        if request.upload_id in router._pending_uploads:
            del router._pending_uploads[request.upload_id]

        logger.info(f"Upload finalized: {request.filename} by user {current_user.id}")

        return safe_json_response({
            "status": "finalized",
            "meta": saved_meta,
            "path": file_path
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Finalize failed: {e}")
        raise HTTPException(status_code=500, detail=f"Finalize failed: {e}")


@router.get("/status/{upload_id}")
async def get_upload_status(
    upload_id: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """Get upload status"""
    try:
        if not hasattr(router, '_pending_uploads'):
            raise HTTPException(status_code=404, detail="Upload not found")

        upload_meta = router._pending_uploads.get(upload_id)
        if not upload_meta:
            raise HTTPException(status_code=404, detail="Upload not found")

        # Validate ownership
        if upload_meta["owner_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        return upload_meta

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status check failed: {e}")
        raise HTTPException(status_code=500, detail=f"Status check failed: {e}")


@router.delete("/cancel/{upload_id}")
async def cancel_upload(
    upload_id: str,
    current_user: UserProfile = Depends(get_current_user)
):
    """Cancel pending upload"""
    try:
        if not hasattr(router, '_pending_uploads'):
            raise HTTPException(status_code=404, detail="Upload not found")

        upload_meta = router._pending_uploads.get(upload_id)
        if not upload_meta:
            raise HTTPException(status_code=404, detail="Upload not found")

        # Validate ownership
        if upload_meta["owner_id"] != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")

        # Clean up file if it exists
        file_path = upload_meta.get("path")
        if file_path and os.path.exists(file_path):
            try:
                os.unlink(file_path)
            except:
                pass

        # Remove from pending uploads
        del router._pending_uploads[upload_id]

        logger.info(f"Upload cancelled: {upload_id}")

        return {"status": "cancelled"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Cancel failed: {e}")
        raise HTTPException(status_code=500, detail=f"Cancel failed: {e}")
