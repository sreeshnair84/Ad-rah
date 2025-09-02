"""
Content Delivery API Endpoints
Provides comprehensive API for content scheduling, distribution, and proof-of-play verification.
Essential for legal compliance and operational management.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, Body, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pydantic import BaseModel, Field
import logging

from app.auth import require_roles
from app.models import User

# Import content delivery services
try:
    from app.content_delivery import (
        content_scheduler, proof_of_play_service, content_distributor,
        PlaybackEvent, DeliveryMode, SchedulePriority
    )
    CONTENT_DELIVERY_AVAILABLE = True
except ImportError:
    CONTENT_DELIVERY_AVAILABLE = False
    logging.warning("Content delivery services not available")

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content-delivery", tags=["content-delivery"])

# Pydantic models for API requests
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

class EmergencyOverrideRequest(BaseModel):
    device_ids: List[str]
    emergency_content_id: str
    duration_minutes: int
    message: Optional[str] = None

# Content Scheduling Endpoints
@router.post("/schedules")
async def create_schedule(
    request: ScheduleCreateRequest,
    user: User = Depends(require_roles("ADVERTISER", "HOST", "ADMIN"))
):
    """Create a new content schedule"""
    if not CONTENT_DELIVERY_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Content delivery service not available"
        )
    
    try:
        # Prepare schedule data
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
            "created_by": user.get("id", "unknown")
        }
        
        # Create schedule
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
    user: User = Depends(require_roles("HOST", "ADMIN"))
):
    """Get optimized playlist for a device"""
    if not CONTENT_DELIVERY_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Content delivery service not available"
        )
    
    try:
        # Parse target time
        if target_time:
            target_datetime = datetime.fromisoformat(target_time.replace('Z', '+00:00'))
        else:
            target_datetime = datetime.utcnow()
        
        # Get playlist
        result = await content_scheduler.get_device_playlist(device_id, target_datetime)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get playlist for device {device_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to get playlist")

@router.post("/schedules/emergency-override")
async def emergency_override(
    request: EmergencyOverrideRequest,
    user: User = Depends(require_roles("ADMIN"))
):
    """Handle emergency content override"""
    if not CONTENT_DELIVERY_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Content delivery service not available"
        )
    
    try:
        result = await content_scheduler.handle_emergency_override(
            device_ids=request.device_ids,
            emergency_content_id=request.emergency_content_id,
            duration_minutes=request.duration_minutes,
            authorized_by=user.get("id", "admin")
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return JSONResponse(content={
            "success": True,
            "emergency_schedule_id": result["emergency_schedule_id"],
            "active_until": result["active_until"],
            "affected_devices": result["affected_devices"],
            "message": "Emergency override activated"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to handle emergency override: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate emergency override")

# Proof-of-Play Endpoints
@router.post("/proof-of-play/record")
async def record_playback_event(
    request: PlaybackEventRequest,
    user: User = Depends(require_roles("DEVICE", "HOST", "ADMIN"))
):
    """Record a playback event for proof-of-play verification"""
    if not CONTENT_DELIVERY_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Content delivery service not available"
        )
    
    try:
        # Validate event type
        try:
            event_type = PlaybackEvent(request.event_type)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid event type: {request.event_type}")
        
        # Prepare event data
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
        
        # Record event
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

@router.post("/proof-of-play/verify/{record_id}")
async def verify_playback_record(
    record_id: str,
    user: User = Depends(require_roles("ADVERTISER", "HOST", "ADMIN"))
):
    """Verify the authenticity of a playback record"""
    if not CONTENT_DELIVERY_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Content delivery service not available"
        )
    
    try:
        result = await proof_of_play_service.verify_playback_record(record_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to verify playback record: {e}")
        raise HTTPException(status_code=500, detail="Failed to verify playback record")

@router.get("/proof-of-play/campaign/{campaign_id}/report")
async def get_campaign_proof_report(
    campaign_id: str,
    start_date: str = Query(..., description="ISO format start date"),
    end_date: str = Query(..., description="ISO format end date"),
    user: User = Depends(require_roles("ADVERTISER", "HOST", "ADMIN"))
):
    """Generate comprehensive proof-of-play report for a campaign"""
    if not CONTENT_DELIVERY_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Content delivery service not available"
        )
    
    try:
        # Parse dates
        start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Generate report
        result = await proof_of_play_service.get_campaign_proof_report(
            campaign_id, start_datetime, end_datetime
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {e}")
    except Exception as e:
        logger.error(f"Failed to generate campaign report: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate campaign report")

# Content Distribution Endpoints
@router.post("/distribution/prepare")
async def prepare_content_package(
    content_id: str = Body(...),
    schedule_id: str = Body(...),
    device_id: str = Body(...),
    priority: int = Body(5),
    deadline_hours: int = Body(24),
    user: User = Depends(require_roles("HOST", "ADMIN"))
):
    """Prepare optimized content package for delivery"""
    if not CONTENT_DELIVERY_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Content delivery service not available"
        )
    
    try:
        # Prepare package
        result = await content_distributor.prepare_content_package(
            content_id=content_id,
            schedule_id=schedule_id,
            device_id=device_id,
            priority=priority,
            deadline=datetime.utcnow() + timedelta(hours=deadline_hours)
        )
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to prepare content package: {e}")
        raise HTTPException(status_code=500, detail="Failed to prepare content package")

@router.post("/distribution/queue/{package_id}")
async def queue_content_delivery(
    package_id: str,
    user: User = Depends(require_roles("HOST", "ADMIN"))
):
    """Queue content package for delivery"""
    if not CONTENT_DELIVERY_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Content delivery service not available"
        )
    
    try:
        result = await content_distributor.queue_delivery(package_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to queue delivery: {e}")
        raise HTTPException(status_code=500, detail="Failed to queue delivery")

@router.get("/distribution/status/{package_id}")
async def get_delivery_status(
    package_id: str,
    user: User = Depends(require_roles("HOST", "ADMIN"))
):
    """Get current delivery status and progress"""
    if not CONTENT_DELIVERY_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Content delivery service not available"
        )
    
    try:
        result = await content_distributor.get_delivery_status(package_id)
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get delivery status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get delivery status")

@router.get("/distribution/metrics")
async def get_delivery_metrics(
    user: User = Depends(require_roles("ADMIN"))
):
    """Get comprehensive delivery performance metrics"""
    if not CONTENT_DELIVERY_AVAILABLE:
        raise HTTPException(
            status_code=503, 
            detail="Content delivery service not available"
        )
    
    try:
        result = await content_distributor.get_delivery_metrics()
        
        if not result.get("success"):
            raise HTTPException(status_code=400, detail=result.get("error"))
        
        return JSONResponse(content=result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get delivery metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get delivery metrics")

# Health and Status Endpoints
@router.get("/health")
async def get_content_delivery_health():
    """Get health status of content delivery services"""
    try:
        health_status = {
            "content_delivery_available": CONTENT_DELIVERY_AVAILABLE,
            "timestamp": datetime.utcnow().isoformat(),
            "services": {}
        }
        
        if CONTENT_DELIVERY_AVAILABLE:
            # Check individual service health
            health_status["services"] = {
                "scheduler": "healthy",
                "proof_of_play": "healthy", 
                "distributor": "healthy"
            }
        
        return JSONResponse(content=health_status)
        
    except Exception as e:
        logger.error(f"Failed to get health status: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to get health status"}
        )