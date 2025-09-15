"""
Unified Content Management API
Consolidates all content-related functionality from multiple duplicate files:
- app/routes/content.py (basic CRUD operations)
- app/api/content_delivery.py (scheduling, distribution, proof-of-play)
- app/api/enhanced_content.py (layouts, campaigns, deployment, analytics)
- app/api/uploads.py (content upload functionality)

This unified API provides:
- Content CRUD operations
- Content scheduling and distribution
- Proof-of-play verification
- Content layouts and campaigns
- File upload and management
- Analytics and reporting
"""

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request, BackgroundTasks, Query, Form
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import uuid
import os
import mimetypes
import logging
from pydantic import BaseModel, Field

from ..models import (
    ContentMeta, ContentOverlay, ContentOverlayCreate, ContentOverlayUpdate,
    ContentLayoutCreate, ContentLayoutUpdate, AdvertiserCampaignCreate,
    ContentDeploymentCreate, DeviceAnalytics, ProximityDetection, AnalyticsQuery, AnalyticsSummary,
    UserProfile, ContentHistoryEventType
)
from ..auth_service import require_roles, get_current_user, get_user_company_context
from ..repo import repo
from ..database_service import db_service
from ..storage import save_media
from ..utils.serialization import safe_json_response
from ..history_service import HistoryService

# Import content delivery services
try:
    from ..content_delivery import (
        content_scheduler, proof_of_play_service, content_distributor,
        PlaybackEvent, DeliveryMode, SchedulePriority
    )
    CONTENT_DELIVERY_AVAILABLE = True
except ImportError:
    CONTENT_DELIVERY_AVAILABLE = False
    logging.warning("Content delivery services not available")

# Import security modules
try:
    from ..security import content_scanner, audit_logger
    SECURITY_SCANNING_ENABLED = True
except ImportError:
    SECURITY_SCANNING_ENABLED = False
    logging.warning("Security scanning not available - uploads will proceed without scanning")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["content"])

# Initialize history service
history_service = HistoryService(db_service)

# ============================================================================
# CONTENT CRUD OPERATIONS (from app/routes/content.py)
# ============================================================================

@router.get("/", response_model=List[Dict])
async def list_content(
    status: Optional[str] = Query(None, description="Filter by status"),
    owner_id: Optional[str] = Query(None, description="Filter by owner"),
    category: Optional[str] = Query(None, description="Filter by category"),
    limit: int = Query(50, description="Limit results"),
    offset: int = Query(0, description="Offset for pagination"),
    current_user: dict = Depends(get_current_user)
):
    """List content with filtering and pagination"""
    try:
        content_list = await repo.list_content(
            status=status,
            owner_id=owner_id,
            category=category,
            limit=limit,
            offset=offset
        )
        # Return the list directly to match the response model
        return safe_json_response(content_list)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list content: {e}")

@router.post("/", response_model=Dict)
async def create_content(
    content_data: Dict,
    current_user: dict = Depends(get_current_user)
):
    """Create new content"""
    try:
        content_data["created_by"] = current_user.get("id")
        content_data["created_at"] = datetime.utcnow().isoformat()

        saved_content = await repo.save_content_meta(content_data)
        return safe_json_response(saved_content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create content: {e}")

@router.get("/{content_id}", response_model=Dict)
async def get_content(
    content_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get content by ID"""
    try:
        content = await repo.get_content_meta(content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        return safe_json_response(content)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get content: {e}")

@router.put("/{content_id}", response_model=Dict)
async def update_content(
    content_id: str,
    content_data: Dict,
    current_user: dict = Depends(get_current_user)
):
    """Update existing content"""
    try:
        existing_content = await repo.get_content_meta(content_id)
        if not existing_content:
            raise HTTPException(status_code=404, detail="Content not found")

        content_data["updated_at"] = datetime.utcnow().isoformat()
        content_data["updated_by"] = current_user.get("id")

        updated_content = await repo.update_content_meta(content_id, content_data)
        return safe_json_response(updated_content)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update content: {e}")

@router.delete("/{content_id}")
async def delete_content(
    content_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete content"""
    try:
        existing_content = await repo.get_content_meta(content_id)
        if not existing_content:
            raise HTTPException(status_code=404, detail="Content not found")

        await repo.delete_content_meta(content_id)
        return {"message": "Content deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete content: {e}")

@router.post("/{content_id}/approve")
async def approve_content(
    content_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Approve content for distribution"""
    try:
        existing_content = await repo.get_content_meta(content_id)
        if not existing_content:
            raise HTTPException(status_code=404, detail="Content not found")

        await repo.update_content_status(content_id, "approved", current_user.get("id"))
        return {"message": "Content approved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve content: {e}")

@router.post("/{content_id}/reject")
async def reject_content(
    content_id: str,
    reason: str = Query(..., description="Rejection reason"),
    current_user: dict = Depends(get_current_user)
):
    """Reject content"""
    try:
        existing_content = await repo.get_content_meta(content_id)
        if not existing_content:
            raise HTTPException(status_code=404, detail="Content not found")

        await repo.update_content_status(content_id, "rejected", current_user.get("id"), reason)
        return {"message": "Content rejected successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject content: {e}")

# ============================================================================
# CONTENT ADMIN/MODERATION ENDPOINTS
# ============================================================================

@router.get("/admin/pending")
async def get_pending_content(
    current_user: UserProfile = Depends(get_current_user),
    company_context: dict = Depends(get_user_company_context)
):
    """Get all pending content for admin review"""
    try:
        # Only SUPER_USER or users with content_moderate permission can access
        if (current_user.user_type != "SUPER_USER" and 
            "content_moderate" not in current_user.permissions):
            raise HTTPException(status_code=403, detail="Access denied")

        # Get all content with status="pending"
        pending_content = await repo.list_content(status="pending")
        
        return safe_json_response({
            "pending_content": pending_content,
            "total": len(pending_content)
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pending content: {e}")

class ContentApprovalRequest(BaseModel):
    action: str = Field(..., pattern="^(approve|reject)$")
    reviewer_notes: Optional[str] = Field(None, max_length=1000)

    # For approvals - optional modifications
    final_categories: Optional[List[str]] = None
    final_tags: Optional[List[str]] = None
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None

    # For rejections - required reason
    rejection_reason: Optional[str] = Field(None, max_length=500)


@router.post("/admin/review/{content_id}")
async def review_content(
    content_id: str,
    review_data: ContentApprovalRequest,
    current_user: UserProfile = Depends(get_current_user),
    company_context: dict = Depends(get_user_company_context)
):
    """Comprehensive content review endpoint for reviewers"""
    try:
        # Check permissions
        if (current_user.user_type != "SUPER_USER" and
            "content_approve" not in current_user.permissions):
            raise HTTPException(status_code=403, detail="Access denied")

        # Get existing content
        existing_content = await repo.get_content_meta(content_id)
        if not existing_content:
            raise HTTPException(status_code=404, detail="Content not found")

        # Validate content is in reviewable state
        if existing_content.get("status") not in ["pending", "quarantine"]:
            raise HTTPException(status_code=400, detail=f"Content status '{existing_content.get('status')}' cannot be reviewed")

        # Validate rejection reason if rejecting
        if review_data.action == "reject" and not review_data.rejection_reason:
            raise HTTPException(status_code=400, detail="Rejection reason is required when rejecting content")

        # Prepare update data
        update_data = {
            "reviewer_id": current_user.id,
            "reviewer_notes": review_data.reviewer_notes,
            "reviewed_at": datetime.utcnow().isoformat(),
            "approval_status": review_data.action + "d",  # approved or rejected
            "updated_at": datetime.utcnow().isoformat()
        }

        if review_data.action == "approve":
            update_data["status"] = "approved"

            # Apply any final modifications from reviewer
            if review_data.final_categories is not None:
                update_data["categories"] = review_data.final_categories
            if review_data.final_tags is not None:
                update_data["tags"] = review_data.final_tags
            if review_data.scheduled_start:
                update_data["start_time"] = review_data.scheduled_start.isoformat()
            if review_data.scheduled_end:
                update_data["end_time"] = review_data.scheduled_end.isoformat()

        else:  # reject
            update_data["status"] = "rejected"
            update_data["rejection_reason"] = review_data.rejection_reason

        # Update content
        await repo.update_content_meta(content_id, update_data)

        # Track review event
        event_type = ContentHistoryEventType.APPROVED if review_data.action == "approve" else ContentHistoryEventType.REJECTED

        await history_service.track_content_event(
            content_id=content_id,
            event_type=event_type,
            company_id=current_user.company_id,
            user_id=current_user.id,
            event_details={
                "action": review_data.action,
                "reviewer_notes": review_data.reviewer_notes,
                "rejection_reason": review_data.rejection_reason if review_data.action == "reject" else None,
                "final_categories": review_data.final_categories,
                "final_tags": review_data.final_tags,
                "ai_moderation_status": existing_content.get("ai_moderation_status"),
                "ai_confidence_score": existing_content.get("ai_confidence_score")
            },
            previous_state={
                "status": existing_content.get("status"),
                "approval_status": existing_content.get("approval_status")
            },
            new_state={
                "status": update_data["status"],
                "approval_status": update_data["approval_status"]
            }
        )

        # Create review history record
        await _create_review_history(content_id, current_user.id, review_data, existing_content)

        # Send notification to content owner
        await _notify_content_decision(content_id, existing_content, review_data, current_user)

        action_message = "approved" if review_data.action == "approve" else "rejected"
        return safe_json_response({
            "message": f"Content {action_message} successfully",
            "content_id": content_id,
            "action": review_data.action,
            "reviewer": current_user.email,
            "reviewed_at": datetime.utcnow().isoformat()
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to review content {content_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to review content: {e}")


@router.post("/admin/approve/{content_id}")
async def admin_approve_content(
    content_id: str,
    current_user: UserProfile = Depends(get_current_user),
    company_context: dict = Depends(get_user_company_context)
):
    """Quick approve endpoint (legacy compatibility)"""
    try:
        # Use the comprehensive review endpoint
        review_request = ContentApprovalRequest(
            action="approve",
            reviewer_notes="Quick approval by admin"
        )
        return await review_content(content_id, review_request, current_user, company_context)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to approve content: {e}")

@router.post("/admin/reject/{content_id}")
async def admin_reject_content(
    content_id: str,
    current_user: UserProfile = Depends(get_current_user),
    company_context: dict = Depends(get_user_company_context)
):
    """Admin reject content with reviewer tracking"""
    try:
        # Only SUPER_USER or users with content_approve permission can access
        if (current_user.user_type != "SUPER_USER" and 
            "content_approve" not in current_user.permissions):
            raise HTTPException(status_code=403, detail="Access denied")

        existing_content = await repo.get_content_meta(content_id)
        if not existing_content:
            raise HTTPException(status_code=404, detail="Content not found")

        # Update content status and add reviewer info
        await repo.update_content_status(
            content_id, 
            "rejected", 
            current_user.id,
            notes="Rejected by admin"
        )

        return safe_json_response({"message": "Content rejected successfully"})

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reject content: {e}")

# ============================================================================
# CONTENT UPLOAD MANAGEMENT (from app/api/uploads.py)
# ============================================================================

async def _process_upload_files(
    request: Request,
    owner_id: str,
    files: List[UploadFile],
    current_user: UserProfile,
    company_context: dict
):
    """Common upload processing logic"""
    # Validate company access
    # SUPER_USER can upload for any company, others need permission check
    if current_user.user_type != "SUPER_USER" and owner_id != current_user.id:
        can_access = await repo.check_content_access_permission(
            current_user.id, owner_id, "edit"
        )
        if not can_access:
            raise HTTPException(status_code=403, detail="Access denied")

    saved = []
    rejected = []
    client_ip = request.client.host if request.client else "unknown"

    for f in files:
        try:
            filename = f.filename or "upload.bin"
            ctype = f.content_type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
            content = await f.read()
            file_size = len(content)

            # Security scanning
            if SECURITY_SCANNING_ENABLED:
                audit_logger.log_content_upload(
                    user_id=current_user.id or owner_id,
                    filename=filename,
                    content_type=ctype,
                    size=file_size,
                    ip_address=client_ip
                )

                scan_result = await content_scanner.scan_content(content, filename, ctype)
                if scan_result.security_level == "blocked":
                    rejected.append({
                        "filename": filename,
                        "reason": "security_blocked",
                        "details": scan_result.content_warnings
                    })
                    continue

            # Save file
            path = save_media(filename, content, content_type=ctype)

            # Create metadata
            content_status = "approved" if SECURITY_SCANNING_ENABLED and 'scan_result' in locals() and scan_result.security_level == "safe" else "pending"

            meta = ContentMeta(
                id=None,
                owner_id=owner_id,
                filename=filename,
                content_type=ctype,
                size=file_size,
                status=content_status
            )

            saved_meta = await repo.save_content_meta(meta)
            saved.append({"meta": saved_meta, "path": path})

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

@router.post("/upload-file")
async def upload_content_file(
    request: Request,
    file: UploadFile = File(...),
    # Basic information
    title: str = Form(...),
    description: Optional[str] = Form(None),

    # Categorization
    categories: Optional[str] = Form(None),  # JSON string of category IDs
    tags: Optional[str] = Form(None),  # JSON string of tag names
    content_rating: Optional[str] = Form(None),

    # Targeting
    target_age_min: Optional[int] = Form(None),
    target_age_max: Optional[int] = Form(None),
    target_gender: Optional[str] = Form(None),

    # Scheduling
    start_time: Optional[str] = Form(None),  # ISO format datetime
    end_time: Optional[str] = Form(None),    # ISO format datetime

    # Production notes
    production_notes: Optional[str] = Form(None),
    usage_guidelines: Optional[str] = Form(None),
    priority_level: str = Form("medium"),

    # Legal and compliance
    copyright_info: Optional[str] = Form(None),
    license_type: Optional[str] = Form(None),
    usage_rights: Optional[str] = Form(None),

    current_user: UserProfile = Depends(get_current_user),
    company_context: dict = Depends(get_user_company_context)
):
    """Upload a single content file with comprehensive metadata"""
    try:
        # Parse categories and tags from JSON strings
        import json
        parsed_categories = []
        parsed_tags = []

        if categories:
            try:
                parsed_categories = json.loads(categories) if isinstance(categories, str) else categories
            except json.JSONDecodeError:
                parsed_categories = [cat.strip() for cat in categories.split(',') if cat.strip()]

        if tags:
            try:
                parsed_tags = json.loads(tags) if isinstance(tags, str) else tags
            except json.JSONDecodeError:
                parsed_tags = [tag.strip() for tag in tags.split(',') if tag.strip()]

        # Parse datetime strings
        parsed_start_time = None
        parsed_end_time = None
        if start_time:
            try:
                from datetime import datetime
                parsed_start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            except ValueError:
                pass
        if end_time:
            try:
                parsed_end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
            except ValueError:
                pass

        # Validate company access
        if current_user.user_type != "SUPER_USER" and current_user.company_id is None:
            raise HTTPException(status_code=403, detail="User must belong to a company")

        # Process file upload
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")

        filename = file.filename
        content = await file.read()
        file_size = len(content)
        content_type = file.content_type or "application/octet-stream"

        # Security scanning
        if SECURITY_SCANNING_ENABLED:
            client_ip = request.client.host if request.client else "unknown"
            audit_logger.log_content_upload(
                user_id=current_user.id,
                filename=filename,
                content_type=content_type,
                size=file_size,
                ip_address=client_ip
            )

            scan_result = await content_scanner.scan_content(content, filename, content_type)
            if scan_result.security_level == "blocked":
                return safe_json_response({
                    "status": "rejected",
                    "message": "Content blocked by security scanner",
                    "details": scan_result.content_warnings
                })

        # Save file
        file_path = save_media(filename, content, content_type=content_type)

        # Detect content duration for videos
        detected_duration = None
        if content_type.startswith('video/'):
            try:
                # You would implement actual video duration detection here
                # For now, we'll use a placeholder
                detected_duration = 30  # seconds
            except Exception:
                pass

        # Create enhanced content metadata
        content_id = str(uuid.uuid4())
        content_meta = {
            "id": content_id,
            "owner_id": current_user.id,
            "filename": filename,
            "content_type": content_type,
            "size": file_size,
            "title": title,
            "description": description,
            "categories": parsed_categories,
            "tags": parsed_tags,
            "content_rating": content_rating,
            "target_age_min": target_age_min,
            "target_age_max": target_age_max,
            "target_gender": target_gender,
            "start_time": parsed_start_time.isoformat() if parsed_start_time else None,
            "end_time": parsed_end_time.isoformat() if parsed_end_time else None,
            "production_notes": production_notes,
            "usage_guidelines": usage_guidelines,
            "priority_level": priority_level,
            "copyright_info": copyright_info,
            "license_type": license_type,
            "usage_rights": usage_rights,
            "duration_seconds": detected_duration,
            "file_url": file_path,
            "status": "quarantine",
            "ai_moderation_status": "pending",
            "uploaded_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        # Save content metadata
        saved_content = await repo.save_content_meta(content_meta)

        # Track content upload event
        await history_service.track_content_event(
            content_id=content_id,
            event_type=ContentHistoryEventType.UPLOADED,
            company_id=current_user.company_id,
            user_id=current_user.id,
            event_details={
                "filename": filename,
                "content_type": content_type,
                "file_size": file_size,
                "title": title,
                "categories": parsed_categories,
                "tags": parsed_tags,
                "priority_level": priority_level
            },
            new_state={"status": "quarantine", "ai_moderation_status": "pending"},
            request=request
        )

        # Trigger AI moderation in background
        from fastapi import BackgroundTasks
        background_tasks = BackgroundTasks()
        background_tasks.add_task(_trigger_ai_moderation, content_id, file_path, content_meta)

        return safe_json_response({
            "status": "success",
            "message": "Content uploaded successfully and sent for AI moderation",
            "content_id": content_id,
            "filename": filename,
            "ai_moderation_required": True,
            "estimated_review_time": "2-5 minutes for AI review, then human review if needed"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

@router.post("/upload")
async def upload_content_files(
    request: Request,
    owner_id: str,
    files: List[UploadFile] = File(...),
    current_user: UserProfile = Depends(get_current_user),
    company_context: dict = Depends(get_user_company_context)
):
    """Upload content files with security scanning"""
    try:
        result = await _process_upload_files(
            request, owner_id, files, current_user, company_context
        )
        return safe_json_response(result)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")

@router.get("/files/{filename}")
async def serve_content_file(filename: str):
    """Serve content files"""
    try:
        from ..config import settings
        local_dir = settings.LOCAL_MEDIA_DIR
        file_path = os.path.join(local_dir, filename)

        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")

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

# ============================================================================
# CONTENT SCHEDULING AND DELIVERY (from app/api/content_delivery.py)
# ============================================================================

class ScheduleCreateRequest(BaseModel):
    content_id: str
    campaign_id: Optional[str] = None
    device_ids: List[str]
    start_date: str
    end_date: str
    delivery_mode: str = "scheduled"
    priority: int = 2
    target_audience: Optional[Dict[str, Any]] = {}
    location_targeting: Optional[Dict[str, Any]] = {}
    frequency_cap: Optional[int] = None
    rotation_weight: float = 1.0
    minimum_gap_minutes: int = 30

class PlaybackEventRequest(BaseModel):
    device_id: str
    content_id: str
    event_type: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: Optional[float] = None
    actual_duration: Optional[float] = None
    completion_percentage: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    audience_count: Optional[int] = None
    resolution: Optional[str] = None
    interaction_count: int = 0
    error_count: int = 0
    network_quality: str = "good"

@router.post("/schedules")
async def create_content_schedule(
    request: ScheduleCreateRequest,
    current_user: dict = Depends(require_roles("ADVERTISER", "HOST", "ADMIN"))
):
    """Create a new content schedule"""
    if not CONTENT_DELIVERY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Content delivery service not available")

    try:
        schedule_data = {
            "content_id": request.content_id,
            "campaign_id": request.campaign_id,
            "device_ids": request.device_ids,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "delivery_mode": request.delivery_mode,
            "priority": request.priority,
            "target_audience": request.target_audience,
            "location_targeting": request.location_targeting,
            "frequency_cap": request.frequency_cap,
            "rotation_weight": request.rotation_weight,
            "minimum_gap_minutes": request.minimum_gap_minutes,
            "created_by": current_user.get("id", "unknown")
        }

        result = await content_scheduler.create_schedule(schedule_data)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return JSONResponse(content={
            "success": True,
            "schedule_id": result["schedule_id"],
            "status": result["status"],
            "estimated_impressions": result.get("estimated_impressions", 0),
            "message": "Schedule created successfully"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create schedule: {e}")
        raise HTTPException(status_code=500, detail="Failed to create schedule")

@router.get("/schedules/device/{device_id}/playlist")
async def get_device_playlist(
    device_id: str,
    target_time: Optional[str] = Query(None, description="ISO format datetime"),
    current_user: dict = Depends(require_roles("HOST", "ADMIN"))
):
    """Get optimized playlist for a device"""
    if not CONTENT_DELIVERY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Content delivery service not available")

    try:
        if target_time:
            target_datetime = datetime.fromisoformat(target_time.replace('Z', '+00:00'))
        else:
            target_datetime = datetime.utcnow()

        result = await content_scheduler.get_device_playlist(device_id, target_datetime)

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return JSONResponse(content=result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get playlist for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get playlist")

@router.post("/proof-of-play/record")
async def record_playback_event(
    request: PlaybackEventRequest,
    current_user: dict = Depends(require_roles("DEVICE", "HOST", "ADMIN"))
):
    """Record a playback event for proof-of-play verification"""
    if not CONTENT_DELIVERY_AVAILABLE:
        raise HTTPException(status_code=503, detail="Content delivery service not available")

    try:
        try:
            event_type = PlaybackEvent(request.event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {request.event_type}")

        event_data = {
            "start_time": datetime.fromisoformat(request.start_time) if request.start_time else datetime.utcnow(),
            "end_time": datetime.fromisoformat(request.end_time) if request.end_time else None,
            "duration_seconds": request.duration_seconds,
            "actual_duration": request.actual_duration,
            "completion_percentage": request.completion_percentage,
            "latitude": request.latitude,
            "longitude": request.longitude,
            "audience_count": request.audience_count,
            "resolution": request.resolution,
            "interaction_count": request.interaction_count,
            "error_count": request.error_count,
            "network_quality": request.network_quality
        }

        result = await proof_of_play_service.record_playback_event(
            device_id=request.device_id,
            content_id=request.content_id,
            event_type=event_type,
            **event_data
        )

        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))

        return JSONResponse(content={
            "success": True,
            "record_id": result["record_id"],
            "verification_level": result["verification_level"],
            "quality_score": result["quality_score"],
            "billing_amount": result["billing_amount"],
            "message": "Playback event recorded"
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to record playback event: {e}")
        raise HTTPException(status_code=500, detail="Failed to record playback event")

# ============================================================================
# ENHANCED CONTENT FEATURES (from app/api/enhanced_content.py)
# ============================================================================

@router.post("/layouts", response_model=Dict)
async def create_content_layout(
    layout: ContentLayoutCreate,
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Create a new multi-zone content layout"""
    try:
        if not company_context["accessible_companies"]:
            raise HTTPException(status_code=403, detail="No accessible companies")

        layout_doc = {
            **layout.model_dump(),
            "id": str(uuid.uuid4()),
            "created_by": current_user["id"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        result = await db_service.db.content_layouts.insert_one(layout_doc)
        layout_doc["_id"] = str(result.inserted_id)

        return {
            "success": True,
            "layout_id": layout_doc["id"],
            "message": "Content layout created successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create layout: {str(e)}")

@router.get("/layouts", response_model=List[Dict])
async def list_content_layouts(
    company_id: Optional[str] = None,
    layout_type: Optional[str] = None,
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """List content layouts with filtering"""
    try:
        query = {}

        accessible_company_ids = [c["id"] for c in company_context["accessible_companies"]]
        if company_id and company_id in accessible_company_ids:
            query["company_id"] = company_id
        else:
            query["$or"] = [
                {"company_id": {"$in": accessible_company_ids}},
                {"is_template": True}
            ]

        if layout_type:
            query["layout_type"] = layout_type

        cursor = db_service.db.content_layouts.find(query)
        layouts = await cursor.to_list(length=None)

        for layout in layouts:
            layout["_id"] = str(layout["_id"])

        return layouts

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch layouts: {str(e)}")

@router.post("/campaigns", response_model=Dict)
async def create_advertiser_campaign(
    campaign: AdvertiserCampaignCreate,
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Create a new advertiser campaign"""
    try:
        user_companies = [c["id"] for c in company_context["accessible_companies"]]
        if campaign.advertiser_company_id not in user_companies:
            raise HTTPException(status_code=403, detail="Can only create campaigns for your company")

        content_filter = {
            "id": {"$in": campaign.content_ids},
            "status": "approved"
        }

        content_count = await db_service.db.content_metadata.count_documents(content_filter)
        if content_count != len(campaign.content_ids):
            raise HTTPException(status_code=400, detail="Some content not found or not approved")

        campaign_doc = {
            **campaign.model_dump(),
            "id": str(uuid.uuid4()),
            "status": "draft",
            "total_impressions": 0,
            "total_clicks": 0,
            "total_spend": 0.0,
            "created_by": current_user["id"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

        result = await db_service.db.advertiser_campaigns.insert_one(campaign_doc)
        campaign_doc["_id"] = str(result.inserted_id)

        return {
            "success": True,
            "campaign_id": campaign_doc["id"],
            "message": "Campaign created successfully"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create campaign: {str(e)}")

class ContentScheduleRequest(BaseModel):
    content_id: str
    overlay_id: Optional[str] = None
    device_ids: List[str]

    # Scheduling options
    deployment_type: str = Field(..., pattern="^(immediate|scheduled|recurring)$")
    scheduled_start: Optional[datetime] = None
    scheduled_end: Optional[datetime] = None

    # Recurring schedule options
    recurrence_pattern: Optional[str] = Field(None, pattern="^(daily|weekly|monthly)$")
    recurrence_days: Optional[List[str]] = None  # For weekly: ["monday", "tuesday"]
    recurrence_end_date: Optional[datetime] = None

    # Display settings
    display_duration: Optional[int] = Field(None, ge=1, le=86400)  # seconds
    priority_level: str = Field("medium", pattern="^(low|medium|high|urgent)$")

    # Targeting (optional)
    target_audience: Optional[Dict] = None
    content_rotation_weight: Optional[float] = Field(1.0, ge=0.1, le=10.0)

    # Notes and tracking
    deployment_notes: Optional[str] = Field(None, max_length=500)


@router.post("/schedule")
async def schedule_content_to_devices(
    schedule_request: ContentScheduleRequest,
    current_user: UserProfile = Depends(get_current_user),
    company_context: dict = Depends(get_user_company_context)
):
    """Schedule content deployment to specific devices with timing controls"""
    try:
        # Check permissions
        if (current_user.user_type != "SUPER_USER" and
            "content_deploy" not in current_user.permissions):
            raise HTTPException(status_code=403, detail="Access denied")

        # Validate content exists and is approved
        content = await repo.get_content_meta(schedule_request.content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")

        if content.get("status") != "approved":
            raise HTTPException(status_code=400, detail="Only approved content can be scheduled")

        # Validate overlay if specified
        overlay_data = None
        if schedule_request.overlay_id:
            overlay_data = await repo.get_content_overlay(schedule_request.overlay_id)
            if not overlay_data:
                raise HTTPException(status_code=404, detail="Overlay not found")

        # Validate devices exist and user has access
        accessible_company_ids = [c["id"] for c in company_context["accessible_companies"]]
        device_query = {
            "id": {"$in": schedule_request.device_ids},
            "company_id": {"$in": accessible_company_ids}
        }

        devices_cursor = db_service.db.digital_screens.find(device_query)
        accessible_devices = await devices_cursor.to_list(length=None)
        accessible_device_ids = [d["id"] for d in accessible_devices]

        if len(accessible_device_ids) != len(schedule_request.device_ids):
            inaccessible = set(schedule_request.device_ids) - set(accessible_device_ids)
            raise HTTPException(status_code=403, detail=f"Cannot access devices: {', '.join(inaccessible)}")

        # Validate scheduling parameters
        now = datetime.utcnow()
        if schedule_request.deployment_type == "scheduled":
            if not schedule_request.scheduled_start:
                raise HTTPException(status_code=400, detail="Scheduled start time required for scheduled deployment")
            if schedule_request.scheduled_start <= now:
                raise HTTPException(status_code=400, detail="Scheduled start time must be in the future")

        # Create content schedule
        schedule_id = str(uuid.uuid4())
        schedule_data = {
            "id": schedule_id,
            "content_id": schedule_request.content_id,
            "overlay_id": schedule_request.overlay_id,
            "device_ids": schedule_request.device_ids,
            "deployment_type": schedule_request.deployment_type,
            "scheduled_start": schedule_request.scheduled_start.isoformat() if schedule_request.scheduled_start else None,
            "scheduled_end": schedule_request.scheduled_end.isoformat() if schedule_request.scheduled_end else None,
            "recurrence_pattern": schedule_request.recurrence_pattern,
            "recurrence_days": schedule_request.recurrence_days,
            "recurrence_end_date": schedule_request.recurrence_end_date.isoformat() if schedule_request.recurrence_end_date else None,
            "display_duration": schedule_request.display_duration,
            "priority_level": schedule_request.priority_level,
            "target_audience": schedule_request.target_audience,
            "content_rotation_weight": schedule_request.content_rotation_weight,
            "deployment_notes": schedule_request.deployment_notes,
            "created_by": current_user.id,
            "created_at": now.isoformat(),
            "status": "pending" if schedule_request.deployment_type == "scheduled" else "active",
            "deployment_history": []
        }

        # Save schedule to database
        await db_service.db.content_schedules.insert_one(schedule_data)

        # If immediate deployment, trigger distribution now
        if schedule_request.deployment_type == "immediate":
            await _trigger_content_distribution(schedule_id, schedule_data)

        # Create deployment notifications for device owners
        await _notify_device_owners(schedule_request.device_ids, content, schedule_data, current_user)

        return safe_json_response({
            "success": True,
            "schedule_id": schedule_id,
            "message": f"Content {'deployed immediately' if schedule_request.deployment_type == 'immediate' else 'scheduled'} to {len(schedule_request.device_ids)} device(s)",
            "deployment_type": schedule_request.deployment_type,
            "scheduled_start": schedule_data["scheduled_start"],
            "devices_count": len(schedule_request.device_ids)
        })

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to schedule content: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to schedule content: {e}")


@router.get("/schedules")
async def list_content_schedules(
    device_id: Optional[str] = Query(None),
    content_id: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    current_user: UserProfile = Depends(get_current_user),
    company_context: dict = Depends(get_user_company_context)
):
    """List content schedules with filtering"""
    try:
        # Build query
        query = {}

        # Filter by device access if not super user
        if current_user.user_type != "SUPER_USER":
            accessible_company_ids = [c["id"] for c in company_context["accessible_companies"]]
            # Get devices user has access to
            devices_cursor = db_service.db.digital_screens.find({"company_id": {"$in": accessible_company_ids}})
            accessible_devices = await devices_cursor.to_list(length=None)
            accessible_device_ids = [d["id"] for d in accessible_devices]

            query["device_ids"] = {"$in": accessible_device_ids}

        # Apply filters
        if device_id:
            query["device_ids"] = device_id
        if content_id:
            query["content_id"] = content_id
        if status:
            query["status"] = status

        # Execute query
        cursor = db_service.db.content_schedules.find(query).skip(offset).limit(limit)
        schedules = await cursor.to_list(length=limit)

        # Enhance with content and device information
        enhanced_schedules = []
        for schedule in schedules:
            # Get content info
            content_info = await repo.get_content_meta(schedule["content_id"])

            # Get device info
            device_infos = []
            if schedule.get("device_ids"):
                devices_cursor = db_service.db.digital_screens.find({"id": {"$in": schedule["device_ids"]}})
                devices = await devices_cursor.to_list(length=None)
                device_infos = [{"id": d["id"], "name": d["name"], "location": d.get("location")} for d in devices]

            schedule["_id"] = str(schedule["_id"])
            schedule["content_info"] = {
                "title": content_info.get("title") if content_info else "Unknown",
                "type": content_info.get("content_type") if content_info else "Unknown"
            }
            schedule["device_infos"] = device_infos

            enhanced_schedules.append(schedule)

        return safe_json_response({
            "schedules": enhanced_schedules,
            "total": len(enhanced_schedules),
            "limit": limit,
            "offset": offset
        })

    except Exception as e:
        logger.error(f"Failed to list schedules: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list schedules: {e}")


@router.post("/deploy", response_model=Dict)
async def deploy_content_to_devices(
    deployment: ContentDeploymentCreate,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Deploy content to specific devices"""
    try:
        content = await db_service.db.content_metadata.find_one({
            "id": deployment.content_id,
            "status": "approved"
        })
        if not content:
            raise HTTPException(status_code=404, detail="Content not found or not approved")

        layout = await db_service.db.content_layouts.find_one({"id": deployment.layout_id})
        if not layout:
            raise HTTPException(status_code=404, detail="Layout not found")

        accessible_company_ids = [c["id"] for c in company_context["accessible_companies"]]
        device_query = {
            "id": {"$in": deployment.device_ids},
            "company_id": {"$in": accessible_company_ids}
        }

        devices_cursor = db_service.db.digital_screens.find(device_query)
        accessible_devices = await devices_cursor.to_list(length=None)
        accessible_device_ids = [d["id"] for d in accessible_devices]

        if len(accessible_device_ids) != len(deployment.device_ids):
            raise HTTPException(status_code=403, detail="Some devices not accessible")

        deployment_doc = {
            **deployment.model_dump(),
            "id": str(uuid.uuid4()),
            "status": "pending",
            "deployment_progress": {device_id: "pending" for device_id in deployment.device_ids},
            "error_logs": [],
            "deployed_by": current_user["id"],
            "created_at": datetime.utcnow().isoformat()
        }

        if deployment.deployment_type == "immediate":
            deployment_doc["scheduled_time"] = datetime.utcnow().isoformat()

        result = await db_service.db.content_deployments.insert_one(deployment_doc)
        deployment_doc["_id"] = str(result.inserted_id)

        background_tasks.add_task(
            process_content_deployment,
            deployment_doc["id"],
            deployment.device_ids,
            deployment.content_id,
            deployment.layout_id
        )

        return {
            "success": True,
            "deployment_id": deployment_doc["id"],
            "message": "Content deployment initiated"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to deploy content: {str(e)}")

async def process_content_deployment(deployment_id: str, device_ids: List[str], content_id: str, layout_id: str):
    """Background task to process content deployment"""
    try:
        await db_service.db.content_deployments.update_one(
            {"id": deployment_id},
            {"$set": {"status": "deploying"}}
        )

        for device_id in device_ids:
            try:
                await update_device_content_config(device_id, content_id, layout_id)
                await db_service.db.content_deployments.update_one(
                    {"id": deployment_id},
                    {"$set": {f"deployment_progress.{device_id}": "deployed"}}
                )
            except Exception as device_error:
                await db_service.db.content_deployments.update_one(
                    {"id": deployment_id},
                    {
                        "$set": {f"deployment_progress.{device_id}": "failed"},
                        "$push": {"error_logs": {
                            "device_id": device_id,
                            "error": str(device_error),
                            "timestamp": datetime.utcnow().isoformat()
                        }}
                    }
                )

        deployment = await db_service.db.content_deployments.find_one({"id": deployment_id})
        progress = deployment.get("deployment_progress", {})

        if all(status == "deployed" for status in progress.values()):
            final_status = "deployed"
        elif any(status == "failed" for status in progress.values()):
            final_status = "partial"
        else:
            final_status = "failed"

        await db_service.db.content_deployments.update_one(
            {"id": deployment_id},
            {
                "$set": {
                    "status": final_status,
                    "deployed_at": datetime.utcnow().isoformat()
                }
            }
        )

    except Exception as e:
        await db_service.db.content_deployments.update_one(
            {"id": deployment_id},
            {"$set": {"status": "failed"}}
        )

async def update_device_content_config(device_id: str, content_id: str, layout_id: str):
    """Update device content configuration"""
    config_update = {
        "current_content_id": content_id,
        "current_layout_id": layout_id,
        "last_updated": datetime.utcnow().isoformat(),
        "sync_required": True
    }

    await db_service.db.digital_screens.update_one(
        {"id": device_id},
        {"$set": config_update}
    )

# ============================================================================
# CONTENT ANALYTICS (from app/api/enhanced_content.py)
# ============================================================================

@router.post("/analytics/record", response_model=Dict)
async def record_device_analytics(
    analytics: DeviceAnalytics,
    current_user=Depends(get_current_user)
):
    """Record analytics data from devices"""
    try:
        device = await db_service.db.digital_screens.find_one({"id": analytics.device_id})
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")

        analytics_doc = {
            **analytics.model_dump(),
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat()
        }

        await db_service.db.device_analytics.insert_one(analytics_doc)
        await update_aggregated_metrics(analytics_doc)

        return {"success": True, "message": "Analytics recorded"}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record analytics: {str(e)}")

@router.get("/analytics/summary", response_model=AnalyticsSummary)
async def get_analytics_summary(
    query: AnalyticsQuery,
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Get analytics summary with filtering"""
    try:
        match_stage = {}

        if query.start_date:
            match_stage["timestamp"] = {"$gte": query.start_date.isoformat()}
        if query.end_date:
            if "timestamp" not in match_stage:
                match_stage["timestamp"] = {}
            match_stage["timestamp"]["$lte"] = query.end_date.isoformat()

        accessible_company_ids = [c["id"] for c in company_context["accessible_companies"]]
        if query.device_ids:
            device_query = {
                "id": {"$in": query.device_ids},
                "company_id": {"$in": accessible_company_ids}
            }
            devices_cursor = db_service.db.digital_screens.find(device_query)
            accessible_devices = await devices_cursor.to_list(length=None)
            accessible_device_ids = [d["id"] for d in accessible_devices]
            match_stage["device_id"] = {"$in": accessible_device_ids}
        else:
            devices_cursor = db_service.db.digital_screens.find({"company_id": {"$in": accessible_company_ids}})
            accessible_devices = await devices_cursor.to_list(length=None)
            accessible_device_ids = [d["id"] for d in accessible_devices]
            match_stage["device_id"] = {"$in": accessible_device_ids}

        if query.content_ids:
            match_stage["content_id"] = {"$in": query.content_ids}

        if query.event_types:
            match_stage["event_type"] = {"$in": query.event_types}

        pipeline = [
            {"$match": match_stage},
            {
                "$group": {
                    "_id": None,
                    "total_impressions": {
                        "$sum": {"$cond": [{"$eq": ["$event_type", "impression"]}, 1, 0]}
                    },
                    "total_revenue": {"$sum": "$estimated_revenue"},
                    "total_interactions": {
                        "$sum": {"$cond": [{"$eq": ["$event_type", "interaction"]}, 1, 0]}
                    },
                    "unique_devices": {"$addToSet": "$device_id"},
                    "avg_engagement_time": {"$avg": "$duration_seconds"}
                }
            }
        ]

        cursor = db_service.db.device_analytics.aggregate(pipeline)
        result = await cursor.to_list(length=1)

        if result:
            summary_data = result[0]
            summary_data["unique_devices"] = len(summary_data.get("unique_devices", []))
        else:
            summary_data = {
                "total_impressions": 0,
                "total_revenue": 0.0,
                "total_interactions": 0,
                "unique_devices": 0,
                "avg_engagement_time": 0.0
            }

        top_content_pipeline = [
            {"$match": match_stage},
            {"$group": {
                "_id": "$content_id",
                "impressions": {"$sum": {"$cond": [{"$eq": ["$event_type", "impression"]}, 1, 0]}}}},
            {"$sort": {"impressions": -1}},
            {"$limit": 5}
        ]

        top_content_cursor = db_service.db.device_analytics.aggregate(top_content_pipeline)
        top_content = await top_content_cursor.to_list(length=5)

        return AnalyticsSummary(
            **summary_data,
            top_performing_content=top_content,
            revenue_by_category={},
            hourly_breakdown=[]
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get analytics summary: {str(e)}")

async def update_aggregated_metrics(analytics_doc: Dict):
    """Update aggregated metrics for faster querying"""
    try:
        timestamp = datetime.fromisoformat(analytics_doc["timestamp"].replace("Z", "+00:00"))
        date_key = timestamp.date().isoformat()
        hour_key = timestamp.hour

        daily_key = f"{analytics_doc['device_id']}_{analytics_doc['content_id']}_{date_key}"

        update_data = {
            "device_id": analytics_doc["device_id"],
            "content_id": analytics_doc["content_id"],
            "date": date_key,
            "last_updated": datetime.utcnow().isoformat()
        }

        if analytics_doc["event_type"] == "impression":
            update_data["$inc"] = {"impressions": 1}
        elif analytics_doc["event_type"] == "interaction":
            update_data["$inc"] = {"interactions": 1}
        elif analytics_doc["event_type"] == "completion":
            update_data["$inc"] = {"completions": 1}

        if analytics_doc.get("estimated_revenue", 0) > 0:
            if "$inc" not in update_data:
                update_data["$inc"] = {}
            update_data["$inc"]["revenue"] = analytics_doc["estimated_revenue"]

        await db_service.db.daily_metrics.update_one(
            {"id": daily_key},
            {"$set": update_data, "$inc": update_data.get("$inc", {})},
            upsert=True
        )

    except Exception as e:
        # Log error for debugging
        print(f"Failed to update aggregated metrics: {e}")


# ============================================================================
# AI MODERATION SYSTEM
# ============================================================================

async def _trigger_ai_moderation(content_id: str, file_path: str, content_meta: Dict):
    """Background task to trigger AI moderation for uploaded content"""
    try:
        # Import AI services
        try:
            from ..services import ai_service_manager
            AI_AVAILABLE = True
        except ImportError:
            AI_AVAILABLE = False
            logger.warning("AI services not available - content will need manual review")

        if not AI_AVAILABLE:
            # If AI not available, mark for manual review
            await repo.update_content_meta(content_id, {
                "ai_moderation_status": "needs_review",
                "status": "pending",
                "ai_processed_at": datetime.utcnow().isoformat()
            })
            return

        # Prepare content for AI analysis
        ai_analysis_data = {
            "title": content_meta.get("title", ""),
            "description": content_meta.get("description", ""),
            "categories": content_meta.get("categories", []),
            "tags": content_meta.get("tags", []),
            "content_type": content_meta.get("content_type", ""),
            "filename": content_meta.get("filename", ""),
            "file_path": file_path
        }

        # Run AI moderation
        moderation_result = await ai_service_manager.moderate_content(ai_analysis_data)

        # Parse AI results
        confidence_score = moderation_result.get("confidence", 0.0)
        ai_decision = moderation_result.get("decision", "needs_review")  # approved, rejected, needs_review
        ai_analysis = moderation_result.get("analysis", {})
        warnings = moderation_result.get("warnings", [])

        # Determine status based on AI confidence
        if confidence_score >= 0.9 and ai_decision == "approved":
            new_status = "pending"  # Still needs human review, but AI approved
            ai_status = "approved"
        elif confidence_score >= 0.9 and ai_decision == "rejected":
            new_status = "rejected"
            ai_status = "rejected"
        else:
            new_status = "pending"
            ai_status = "needs_review"

        # Update content with AI results
        update_data = {
            "ai_moderation_status": ai_status,
            "ai_confidence_score": confidence_score,
            "ai_analysis": ai_analysis,
            "ai_processed_at": datetime.utcnow().isoformat(),
            "status": new_status,
            "updated_at": datetime.utcnow().isoformat()
        }

        if warnings:
            update_data["ai_warnings"] = warnings

        await repo.update_content_meta(content_id, update_data)

        # Track AI moderation completion event
        company_id = content_meta.get("company_id") or content_meta.get("owner_company_id")
        await history_service.track_content_event(
            content_id=content_id,
            event_type=ContentHistoryEventType.AI_MODERATION_COMPLETED,
            company_id=company_id,
            triggered_by_system="AI_MODERATION",
            event_details={
                "ai_decision": ai_decision,
                "confidence_score": confidence_score,
                "warnings": warnings,
                "analysis_summary": ai_analysis.get("summary", ""),
                "processing_time": ai_analysis.get("processing_time_ms")
            },
            previous_state={"status": "quarantine", "ai_moderation_status": "pending"},
            new_state={"status": new_status, "ai_moderation_status": ai_status},
            processing_time_ms=ai_analysis.get("processing_time_ms")
        )

        # Log moderation result
        logger.info(f"AI moderation completed for content {content_id}: {ai_decision} (confidence: {confidence_score})")

        # If high confidence rejection, notify the uploader
        if new_status == "rejected":
            await _notify_content_rejection(content_id, content_meta, ai_analysis)

    except Exception as e:
        logger.error(f"AI moderation failed for content {content_id}: {e}")
        # Mark as needing manual review if AI fails
        await repo.update_content_meta(content_id, {
            "ai_moderation_status": "error",
            "status": "pending",
            "ai_processed_at": datetime.utcnow().isoformat(),
            "ai_error": str(e)
        })


async def _create_review_history(content_id: str, reviewer_id: str, review_data: ContentApprovalRequest, original_content: Dict):
    """Create a detailed review history record"""
    try:
        review_history = {
            "id": str(uuid.uuid4()),
            "content_id": content_id,
            "reviewer_id": reviewer_id,
            "action": review_data.action,
            "reviewer_notes": review_data.reviewer_notes,
            "rejection_reason": review_data.rejection_reason,
            "changes_made": {},
            "original_data": {
                "categories": original_content.get("categories", []),
                "tags": original_content.get("tags", []),
                "status": original_content.get("status")
            },
            "reviewed_at": datetime.utcnow().isoformat(),
            "ai_data": {
                "ai_moderation_status": original_content.get("ai_moderation_status"),
                "ai_confidence_score": original_content.get("ai_confidence_score"),
                "ai_analysis": original_content.get("ai_analysis")
            }
        }

        # Track what changes were made during approval
        if review_data.action == "approve":
            if review_data.final_categories is not None:
                review_history["changes_made"]["categories"] = {
                    "from": original_content.get("categories", []),
                    "to": review_data.final_categories
                }
            if review_data.final_tags is not None:
                review_history["changes_made"]["tags"] = {
                    "from": original_content.get("tags", []),
                    "to": review_data.final_tags
                }

        # Save to database
        await db_service.db.content_review_history.insert_one(review_history)
        logger.info(f"Review history created for content {content_id} by reviewer {reviewer_id}")

    except Exception as e:
        logger.error(f"Failed to create review history: {e}")


async def _notify_content_decision(content_id: str, content_meta: Dict, review_data: ContentApprovalRequest, reviewer: UserProfile):
    """Notify content owner of approval/rejection decision"""
    try:
        owner_id = content_meta.get("owner_id")
        content_title = content_meta.get("title", "Untitled Content")

        notification_data = {
            "id": str(uuid.uuid4()),
            "user_id": owner_id,
            "content_id": content_id,
            "type": "content_decision",
            "action": review_data.action,
            "title": f"Content {review_data.action}d: {content_title}",
            "message": f"Your content '{content_title}' has been {review_data.action}d by {reviewer.email}",
            "reviewer_notes": review_data.reviewer_notes,
            "rejection_reason": review_data.rejection_reason if review_data.action == "reject" else None,
            "created_at": datetime.utcnow().isoformat(),
            "read": False
        }

        # Save notification
        await db_service.db.notifications.insert_one(notification_data)

        # You could also send email here
        logger.info(f"Notification sent to user {owner_id} for content {content_id} decision: {review_data.action}")

    except Exception as e:
        logger.error(f"Failed to send content decision notification: {e}")


async def _trigger_content_distribution(schedule_id: str, schedule_data: Dict):
    """Trigger immediate content distribution to devices"""
    try:
        content_id = schedule_data["content_id"]
        device_ids = schedule_data["device_ids"]
        overlay_id = schedule_data.get("overlay_id")

        # Update device content configurations
        update_data = {
            "current_content_id": content_id,
            "current_overlay_id": overlay_id,
            "schedule_id": schedule_id,
            "last_updated": datetime.utcnow().isoformat(),
            "sync_required": True,
            "content_priority": schedule_data.get("priority_level", "medium"),
            "display_duration": schedule_data.get("display_duration"),
            "rotation_weight": schedule_data.get("content_rotation_weight", 1.0)
        }

        # Update all targeted devices
        result = await db_service.db.digital_screens.update_many(
            {"id": {"$in": device_ids}},
            {"$set": update_data}
        )

        # Record distribution in schedule history
        distribution_record = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": "distributed",
            "device_count": result.modified_count,
            "details": f"Content distributed to {result.modified_count} devices"
        }

        await db_service.db.content_schedules.update_one(
            {"id": schedule_id},
            {"$push": {"deployment_history": distribution_record}}
        )

        logger.info(f"Content {content_id} distributed to {result.modified_count} devices via schedule {schedule_id}")

    except Exception as e:
        logger.error(f"Failed to distribute content for schedule {schedule_id}: {e}")


async def _notify_device_owners(device_ids: List[str], content: Dict, schedule_data: Dict, deployer: UserProfile):
    """Notify device owners about new content deployment"""
    try:
        # Get device owners (companies that own these devices)
        devices_cursor = db_service.db.digital_screens.find({"id": {"$in": device_ids}})
        devices = await devices_cursor.to_list(length=None)

        # Group devices by company
        company_devices = {}
        for device in devices:
            company_id = device.get("company_id")
            if company_id:
                if company_id not in company_devices:
                    company_devices[company_id] = []
                company_devices[company_id].append(device)

        # Create notifications for each company
        for company_id, devices_list in company_devices.items():
            # Get company admins to notify
            users_cursor = db_service.db.users.find({
                "company_id": company_id,
                "user_type": "COMPANY_USER",
                "permissions": {"$in": ["device_manage", "content_receive"]}
            })
            company_users = await users_cursor.to_list(length=None)

            device_names = [d["name"] for d in devices_list]
            notification_data = {
                "id": str(uuid.uuid4()),
                "company_id": company_id,
                "type": "content_deployment",
                "title": f"New content scheduled: {content.get('title', 'Unknown')}",
                "message": f"Content has been scheduled for deployment to {len(device_names)} device(s): {', '.join(device_names[:3])}{'...' if len(device_names) > 3 else ''}",
                "content_id": schedule_data["content_id"],
                "schedule_id": schedule_data["id"],
                "deployed_by": deployer.email,
                "deployment_type": schedule_data["deployment_type"],
                "scheduled_start": schedule_data.get("scheduled_start"),
                "device_count": len(device_names),
                "created_at": datetime.utcnow().isoformat(),
                "read": False
            }

            # Send to each company user
            for user in company_users:
                user_notification = {**notification_data, "user_id": user["id"]}
                await db_service.db.notifications.insert_one(user_notification)

        logger.info(f"Deployment notifications sent for schedule {schedule_data['id']}")

    except Exception as e:
        logger.error(f"Failed to notify device owners: {e}")


async def _notify_content_rejection(content_id: str, content_meta: Dict, ai_analysis: Dict):
    """Notify content uploader of AI rejection"""
    try:
        # You would implement email notification here
        logger.info(f"Content {content_id} rejected by AI - notification would be sent to user {content_meta.get('owner_id')}")

        # Could integrate with email service
        # await email_service.send_rejection_notification(
        #     user_id=content_meta.get('owner_id'),
        #     content_title=content_meta.get('title'),
        #     rejection_reason=ai_analysis.get('rejection_reason', 'Content policy violation')
        # )
    except Exception as e:
        logger.error(f"Failed to send rejection notification: {e}")