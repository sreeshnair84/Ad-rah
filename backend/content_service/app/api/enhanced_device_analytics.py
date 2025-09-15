"""
Enhanced Device Heartbeat and Analytics Reporting
Provides comprehensive device health monitoring and statistics collection
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from pydantic import BaseModel, Field

from ..security.device_auth import authenticate_device
from ..repo import repo
from ..analytics.real_time_analytics import analytics_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/device-analytics", tags=["device-analytics"])

class SystemMetrics(BaseModel):
    cpu_usage: float = Field(..., ge=0, le=1, description="CPU usage as percentage (0-1)")
    memory_usage: float = Field(..., ge=0, le=1, description="Memory usage as percentage (0-1)")
    disk_usage: float = Field(..., ge=0, le=1, description="Disk usage as percentage (0-1)")
    temperature: float = Field(..., description="Device temperature in Celsius")
    network_latency: float = Field(..., description="Network latency in milliseconds")
    battery_level: Optional[float] = Field(None, ge=0, le=1, description="Battery level (0-1)")
    available_memory_mb: int = Field(..., description="Available memory in MB")
    total_memory_mb: int = Field(..., description="Total memory in MB")
    available_disk_gb: int = Field(..., description="Available disk space in GB")
    total_disk_gb: int = Field(..., description="Total disk space in GB")

class DisplayMetrics(BaseModel):
    frame_rate: float = Field(..., description="Current frame rate")
    dropped_frames: int = Field(..., description="Dropped frames count")
    render_time: float = Field(..., description="Average render time in ms")
    brightness: float = Field(..., ge=0, le=1, description="Screen brightness (0-1)")
    resolution: str = Field(..., description="Screen resolution (e.g., '1920x1080')")
    orientation: str = Field(..., description="Screen orientation")
    is_fullscreen: bool = Field(..., description="Whether in fullscreen mode")

class ContentMetrics(BaseModel):
    content_id: str = Field(..., description="Currently playing content ID")
    content_name: str = Field(..., description="Content name")
    content_type: str = Field(..., description="Content type (video, image, etc.)")
    playback_duration: int = Field(..., description="Playback duration in milliseconds")
    load_time: float = Field(..., description="Content load time in seconds")
    error_count: int = Field(..., description="Error count during playback")
    completion_status: str = Field(..., description="Completion status")
    progress: float = Field(..., ge=0, le=1, description="Playback progress (0-1)")

class AudienceMetrics(BaseModel):
    current_count: int = Field(..., description="Current audience count")
    detection_method: str = Field(..., description="Detection method used")
    confidence: float = Field(..., ge=0, le=1, description="Detection confidence (0-1)")
    dwell_time: int = Field(..., description="Average dwell time in milliseconds")
    location_zone: str = Field(..., description="Location zone identifier")

class EnhancedHeartbeat(BaseModel):
    device_id: str = Field(..., description="Device identifier")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Heartbeat timestamp")
    system_metrics: SystemMetrics = Field(..., description="System health metrics")
    display_metrics: DisplayMetrics = Field(..., description="Display performance metrics")
    current_content: Optional[ContentMetrics] = Field(None, description="Current content metrics")
    audience_metrics: Optional[AudienceMetrics] = Field(None, description="Audience detection metrics")
    
    # Additional metadata
    uptime: int = Field(..., description="Device uptime in seconds")
    last_restart: Optional[datetime] = Field(None, description="Last restart timestamp")
    software_version: str = Field(..., description="Software version")
    warnings: List[str] = Field(default=[], description="System warnings")
    errors: List[str] = Field(default=[], description="System errors")

@router.post("/heartbeat")
async def enhanced_device_heartbeat(
    heartbeat: EnhancedHeartbeat,
    request: Request,
    device_info: dict = Depends(authenticate_device)
):
    """
    Process enhanced device heartbeat with comprehensive metrics
    This replaces the basic heartbeat with detailed analytics
    """
    try:
        device_id = heartbeat.device_id
        
        # Validate device ID matches authenticated device
        if device_info.get("device_id") != device_id:
            raise HTTPException(status_code=403, detail="Device ID mismatch")
        
        # Calculate performance score
        performance_score = _calculate_device_performance_score(heartbeat.system_metrics, heartbeat.display_metrics)
        
        # Determine health status
        health_status = _determine_health_status(performance_score, heartbeat.warnings, heartbeat.errors)
        
        # Store enhanced heartbeat data
        heartbeat_data = {
            "device_id": device_id,
            "timestamp": heartbeat.timestamp.isoformat(),
            "system_metrics": heartbeat.system_metrics.model_dump(),
            "display_metrics": heartbeat.display_metrics.model_dump(),
            "current_content": heartbeat.current_content.model_dump() if heartbeat.current_content else None,
            "audience_metrics": heartbeat.audience_metrics.model_dump() if heartbeat.audience_metrics else None,
            "uptime": heartbeat.uptime,
            "last_restart": heartbeat.last_restart.isoformat() if heartbeat.last_restart else None,
            "software_version": heartbeat.software_version,
            "warnings": heartbeat.warnings,
            "errors": heartbeat.errors,
            "performance_score": performance_score,
            "health_status": health_status,
            "client_ip": request.client.host if request.client else "unknown"
        }
        
        # Save to database
        try:
            await repo.save_device_heartbeat(device_id, heartbeat_data)
        except Exception as e:
            logger.error(f"Failed to save heartbeat data: {e}")
        
        # Record analytics events
        await _record_analytics_events(heartbeat, performance_score)
        
        # Update device status in real-time
        await _update_device_status(device_id, heartbeat_data)
        
        return {
            "success": True,
            "message": "Enhanced heartbeat processed",
            "performance_score": performance_score,
            "health_status": health_status,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing enhanced heartbeat: {e}")
        raise HTTPException(status_code=500, detail="Failed to process heartbeat")

@router.get("/device-health/{device_id}")
async def get_device_health_report(
    device_id: str,
    hours: int = 24,
    device_info: dict = Depends(authenticate_device)
):
    """Get comprehensive device health report"""
    try:
        # Get recent heartbeats
        heartbeats = await repo.get_device_heartbeats(device_id, limit=hours * 6)  # 6 per hour
        
        if not heartbeats:
            raise HTTPException(status_code=404, detail="No heartbeat data found")
        
        latest_heartbeat = heartbeats[0]
        
        # Calculate health trends
        health_trends = _calculate_health_trends(heartbeats)
        
        # Get performance analytics
        performance_analytics = await analytics_service.get_device_analytics(device_id, hours)
        
        return {
            "device_id": device_id,
            "current_status": {
                "health_status": latest_heartbeat.get("health_status"),
                "performance_score": latest_heartbeat.get("performance_score"),
                "uptime": latest_heartbeat.get("uptime"),
                "last_heartbeat": latest_heartbeat.get("timestamp")
            },
            "system_metrics": latest_heartbeat.get("system_metrics", {}),
            "display_metrics": latest_heartbeat.get("display_metrics", {}),
            "current_content": latest_heartbeat.get("current_content"),
            "audience_metrics": latest_heartbeat.get("audience_metrics"),
            "health_trends": health_trends,
            "performance_analytics": performance_analytics,
            "warnings": latest_heartbeat.get("warnings", []),
            "errors": latest_heartbeat.get("errors", []),
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting device health report: {e}")
        raise HTTPException(status_code=500, detail="Failed to get health report")

@router.get("/fleet-overview")
async def get_fleet_overview(
    company_id: Optional[str] = None,
    device_info: dict = Depends(authenticate_device)
):
    """Get overview of all devices in the fleet"""
    try:
        # Get all devices (filtered by company if specified)
        devices = await repo.list_digital_screens()
        
        if company_id:
            devices = [d for d in devices if d.get("company_id") == company_id]
        
        fleet_overview = []
        
        for device in devices:
            device_id = device.get("id") or device.get("device_id")
            
            # Get latest heartbeat
            try:
                heartbeats = await repo.get_device_heartbeats(device_id, limit=1)
                latest_heartbeat = heartbeats[0] if heartbeats else None
            except:
                latest_heartbeat = None
            
            # Determine if device is online
            is_online = False
            if latest_heartbeat:
                last_seen = datetime.fromisoformat(latest_heartbeat.get("timestamp", "").replace('Z', '+00:00'))
                is_online = (datetime.utcnow() - last_seen).seconds < 300  # 5 minutes
            
            device_overview = {
                "device_id": device_id,
                "device_name": device.get("name", f"Device {device_id[:8]}"),
                "location": device.get("location", "Unknown"),
                "is_online": is_online,
                "health_status": latest_heartbeat.get("health_status", "unknown") if latest_heartbeat else "offline",
                "performance_score": latest_heartbeat.get("performance_score", 0) if latest_heartbeat else 0,
                "last_heartbeat": latest_heartbeat.get("timestamp") if latest_heartbeat else None,
                "current_content": latest_heartbeat.get("current_content") if latest_heartbeat else None,
                "warnings_count": len(latest_heartbeat.get("warnings", [])) if latest_heartbeat else 0,
                "errors_count": len(latest_heartbeat.get("errors", [])) if latest_heartbeat else 0
            }
            
            fleet_overview.append(device_overview)
        
        # Calculate fleet statistics
        total_devices = len(fleet_overview)
        online_devices = len([d for d in fleet_overview if d["is_online"]])
        healthy_devices = len([d for d in fleet_overview if d["health_status"] in ["excellent", "good"]])
        devices_with_warnings = len([d for d in fleet_overview if d["warnings_count"] > 0])
        devices_with_errors = len([d for d in fleet_overview if d["errors_count"] > 0])
        
        fleet_stats = {
            "total_devices": total_devices,
            "online_devices": online_devices,
            "offline_devices": total_devices - online_devices,
            "healthy_devices": healthy_devices,
            "devices_with_warnings": devices_with_warnings,
            "devices_with_errors": devices_with_errors,
            "fleet_health_percentage": (healthy_devices / total_devices * 100) if total_devices > 0 else 0,
            "uptime_percentage": (online_devices / total_devices * 100) if total_devices > 0 else 0
        }
        
        return {
            "fleet_stats": fleet_stats,
            "devices": fleet_overview,
            "generated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting fleet overview: {e}")
        raise HTTPException(status_code=500, detail="Failed to get fleet overview")

def _calculate_device_performance_score(system: SystemMetrics, display: DisplayMetrics) -> float:
    """Calculate overall device performance score (0-1)"""
    
    # System metrics scores (lower is better for usage, higher for frame rate)
    cpu_score = max(0, 1 - system.cpu_usage)
    memory_score = max(0, 1 - system.memory_usage)
    disk_score = max(0, 1 - system.disk_usage)
    
    # Temperature score (optimal range 20-45°C)
    temp_score = 1.0
    if system.temperature > 60:
        temp_score = max(0, 1 - (system.temperature - 60) / 20)
    elif system.temperature < 10:
        temp_score = max(0, 1 - (10 - system.temperature) / 10)
    
    # Network score (lower latency is better)
    network_score = max(0, min(1, (500 - system.network_latency) / 500))
    
    # Display performance score
    frame_rate_score = min(1, display.frame_rate / 60.0)
    dropped_frames_score = max(0, 1 - display.dropped_frames / 100)
    
    # Weighted average
    performance_score = (
        cpu_score * 0.2 +
        memory_score * 0.15 +
        disk_score * 0.1 +
        temp_score * 0.15 +
        network_score * 0.15 +
        frame_rate_score * 0.15 +
        dropped_frames_score * 0.1
    )
    
    return round(performance_score, 3)

def _determine_health_status(performance_score: float, warnings: List[str], errors: List[str]) -> str:
    """Determine device health status based on performance and issues"""
    
    if errors:
        return "critical"
    elif performance_score < 0.4:
        return "critical"
    elif performance_score < 0.6 or len(warnings) > 5:
        return "poor"
    elif performance_score < 0.75 or len(warnings) > 2:
        return "fair"
    elif performance_score < 0.9:
        return "good"
    else:
        return "excellent"

async def _record_analytics_events(heartbeat: EnhancedHeartbeat, performance_score: float):
    """Record analytics events from heartbeat data"""
    try:
        # System metrics event
        await analytics_service.record_metric({
            "metric_type": "device",
            "event_type": "system_metrics",
            "device_id": heartbeat.device_id,
            "value": performance_score,
            "timestamp": heartbeat.timestamp.isoformat(),
            "system_metrics": heartbeat.system_metrics.model_dump(),
            "display_metrics": heartbeat.display_metrics.model_dump()
        })
        
        # Content metrics event
        if heartbeat.current_content:
            await analytics_service.record_metric({
                "metric_type": "content",
                "event_type": "content_playback",
                "device_id": heartbeat.device_id,
                "content_id": heartbeat.current_content.content_id,
                "value": heartbeat.current_content.progress,
                "timestamp": heartbeat.timestamp.isoformat(),
                "content_metadata": heartbeat.current_content.model_dump()
            })
        
        # Audience metrics event
        if heartbeat.audience_metrics:
            await analytics_service.record_metric({
                "metric_type": "audience",
                "event_type": "audience_detection",
                "device_id": heartbeat.device_id,
                "value": heartbeat.audience_metrics.current_count,
                "count": heartbeat.audience_metrics.current_count,
                "timestamp": heartbeat.timestamp.isoformat(),
                "audience_data": heartbeat.audience_metrics.model_dump()
            })
        
    except Exception as e:
        logger.error(f"Error recording analytics events: {e}")

async def _update_device_status(device_id: str, heartbeat_data: Dict[str, Any]):
    """Update device status in real-time for digital twin synchronization"""
    try:
        # Update device record with latest status
        device_update = {
            "last_heartbeat": heartbeat_data["timestamp"],
            "status": "online",
            "health_status": heartbeat_data["health_status"],
            "performance_score": heartbeat_data["performance_score"],
            "current_content": heartbeat_data.get("current_content"),
            "system_metrics": heartbeat_data["system_metrics"],
            "display_metrics": heartbeat_data["display_metrics"]
        }
        
        await repo.update_digital_screen_status(device_id, device_update)
        
        # Update any digital twins associated with this device
        twin = await repo.get_digital_twin_by_screen(device_id)
        if twin and twin.get("is_live_mirror", False):
            twin_update = {
                "last_accessed": heartbeat_data["timestamp"],
                "live_metrics": heartbeat_data,
                "updated_at": datetime.utcnow()
            }
            await repo.update_digital_twin(twin["id"], twin_update)
        
    except Exception as e:
        logger.error(f"Error updating device status: {e}")

def _calculate_health_trends(heartbeats: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate health trends from historical heartbeat data"""
    if len(heartbeats) < 2:
        return {"trend": "stable", "change": 0}
    
    # Calculate trend in performance score
    recent_scores = [h.get("performance_score", 0) for h in heartbeats[:10]]
    older_scores = [h.get("performance_score", 0) for h in heartbeats[-10:]]
    
    recent_avg = sum(recent_scores) / len(recent_scores) if recent_scores else 0
    older_avg = sum(older_scores) / len(older_scores) if older_scores else 0
    
    change = recent_avg - older_avg
    
    if abs(change) < 0.05:
        trend = "stable"
    elif change > 0:
        trend = "improving"
    else:
        trend = "declining"
    
    return {
        "trend": trend,
        "change": round(change, 3),
        "recent_average": round(recent_avg, 3),
        "historical_average": round(older_avg, 3)
    }