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

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request, BackgroundTasks, Query
from fastapi.responses import FileResponse, StreamingResponse, JSONResponse
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import uuid
import os
import mimetypes
import logging
from pydantic import BaseModel

from ..models import (
    ContentMeta, ContentOverlay, ContentOverlayCreate, ContentOverlayUpdate,
    ContentLayoutCreate, ContentLayoutUpdate, AdvertiserCampaignCreate,
    ContentDeploymentCreate, DeviceAnalytics, ProximityDetection, AnalyticsQuery, AnalyticsSummary
)
from ..auth_service import require_roles, get_current_user, get_user_company_context
from ..repo import repo
from ..database_service import db_service
from ..storage import save_media
from ..utils.serialization import safe_json_response

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
# CONTENT UPLOAD MANAGEMENT (from app/api/uploads.py)
# ============================================================================

@router.post("/upload")
async def upload_content_files(
    request: Request,
    owner_id: str,
    files: List[UploadFile] = File(...),
    current_user: dict = Depends(get_current_user),
    company_context: dict = Depends(get_user_company_context)
):
    """Upload content files with security scanning"""
    try:
        # Validate company access
        if owner_id != current_user.get("id"):
            can_access = await repo.check_content_access_permission(
                current_user.get("id"), owner_id, "edit"
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
                        user_id=current_user.get('id', owner_id),
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
                content_status = "approved" if SECURITY_SCANNING_ENABLED and scan_result.security_level == "safe" else "pending"

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

        return safe_json_response(response)

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
            **layout.dict(),
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
            **campaign.dict(),
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
            **deployment.dict(),
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
            **analytics.dict(),
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