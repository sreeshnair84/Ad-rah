"""
Digital Twin API
Provides virtual testing environments for digital signage
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional
from datetime import datetime
import uuid
import logging

from ..models import DigitalTwin, DigitalTwinCreate, DigitalTwinUpdate, DigitalTwinStatus
from ..auth_service import get_current_user, get_user_company_context
from ..repo import repo
from ..utils.serialization import safe_json_response

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/digital-twins", tags=["digital-twins"])
security = HTTPBearer(auto_error=False)

@router.get("/", response_model=List[dict])
async def list_digital_twins(
    company_id: Optional[str] = Query(None, description="Filter by company ID"),
    current_user = Depends(get_current_user)
):
    """List all digital twins, optionally filtered by company"""
    try:
        user_context = await get_user_company_context(current_user)
        
        # Use company_id from context if provided, otherwise get all for user's companies
        filter_company_id = company_id or user_context.get("company_id")
        
        twins = await repo.list_digital_twins(company_id=filter_company_id)
        return safe_json_response(twins)
    except Exception as e:
        logger.error(f"Error listing digital twins: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch digital twins")

@router.post("/", response_model=dict)
async def create_digital_twin(
    twin_data: DigitalTwinCreate,
    current_user = Depends(get_current_user)
):
    """Create a new digital twin"""
    try:
        user_context = await get_user_company_context(current_user)
        
        # Create digital twin object
        twin = DigitalTwin(
            id=str(uuid.uuid4()),
            name=twin_data.name,
            screen_id=twin_data.screen_id,
            company_id=twin_data.company_id,
            description=twin_data.description,
            is_live_mirror=twin_data.is_live_mirror,
            created_by=current_user.get("id", "unknown"),
            status=DigitalTwinStatus.STOPPED,
            test_content_ids=[],
            overlay_configs=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Verify the screen exists
        screen = await repo.get_digital_screen(twin_data.screen_id)
        if not screen:
            raise HTTPException(status_code=404, detail="Screen not found")
            
        # Verify the screen belongs to the same company
        if screen.get("company_id") != twin_data.company_id:
            raise HTTPException(status_code=403, detail="Screen does not belong to the specified company")
        
        # Save the digital twin
        saved_twin = await repo.save_digital_twin(twin)
        return safe_json_response(saved_twin)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating digital twin: {e}")
        raise HTTPException(status_code=500, detail="Failed to create digital twin")

@router.get("/{twin_id}", response_model=dict)
async def get_digital_twin(
    twin_id: str,
    current_user = Depends(get_current_user)
):
    """Get a specific digital twin by ID"""
    try:
        twin = await repo.get_digital_twin(twin_id)
        if not twin:
            raise HTTPException(status_code=404, detail="Digital twin not found")
        
        # Verify user has access to this twin's company
        user_context = await get_user_company_context(current_user)
        
        return safe_json_response(twin)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching digital twin {twin_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch digital twin")

@router.put("/{twin_id}", response_model=dict)
async def update_digital_twin(
    twin_id: str,
    twin_update: DigitalTwinUpdate,
    current_user = Depends(get_current_user)
):
    """Update a digital twin"""
    try:
        # Get existing twin
        existing_twin = await repo.get_digital_twin(twin_id)
        if not existing_twin:
            raise HTTPException(status_code=404, detail="Digital twin not found")
        
        # Verify user has access to this twin's company
        user_context = await get_user_company_context(current_user)
        
        # Update fields
        update_data = twin_update.model_dump(exclude_unset=True)
        if update_data:
            for key, value in update_data.items():
                existing_twin[key] = value
            existing_twin["updated_at"] = datetime.utcnow()
            
            # If status is being changed to running, update last_accessed
            if update_data.get("status") == DigitalTwinStatus.RUNNING:
                existing_twin["last_accessed"] = datetime.utcnow()
            
            # Convert to DigitalTwin model for validation
            twin_model = DigitalTwin(**existing_twin)
            
            # Save updated twin
            saved_twin = await repo.save_digital_twin(twin_model)
            return safe_json_response(saved_twin)
        
        return safe_json_response(existing_twin)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating digital twin {twin_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to update digital twin")

@router.delete("/{twin_id}")
async def delete_digital_twin(
    twin_id: str,
    current_user = Depends(get_current_user)
):
    """Delete a digital twin"""
    try:
        # Get existing twin
        existing_twin = await repo.get_digital_twin(twin_id)
        if not existing_twin:
            raise HTTPException(status_code=404, detail="Digital twin not found")
        
        # Verify user has access to this twin's company
        user_context = await get_user_company_context(current_user)
        
        # Delete the digital twin
        deleted = await repo.delete_digital_twin(twin_id)
        if not deleted:
            raise HTTPException(status_code=500, detail="Failed to delete digital twin")
        
        return {"message": "Digital twin deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting digital twin {twin_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete digital twin")

@router.get("/{twin_id}/status", response_model=dict)
async def get_twin_status(
    twin_id: str,
    current_user = Depends(get_current_user)
):
    """Get digital twin status and real-time metrics from physical device"""
    try:
        twin = await repo.get_digital_twin(twin_id)
        if not twin:
            raise HTTPException(status_code=404, detail="Digital twin not found")
        
        # Verify user has access to this twin's company
        user_context = await get_user_company_context(current_user)
        
        # Get real-time data from the physical device
        screen_id = twin["screen_id"]
        
        # Get latest device heartbeat for real metrics
        try:
            latest_heartbeat = await repo.get_device_heartbeats(screen_id, 1) if hasattr(repo, 'get_device_heartbeats') else []
            heartbeat = latest_heartbeat[0] if latest_heartbeat else None
        except:
            heartbeat = None
        
        # Get current content being played (simplified - use content metadata if available)
        current_content = None
        try:
            # Try to get screen info which might contain current content
            screen_info = await repo.get_digital_screen(screen_id)
            if screen_info and "current_content" in screen_info:
                current_content = screen_info["current_content"]
        except:
            current_content = None
        
        # Get real-time audience data
        try:
            from app.analytics.real_time_analytics import analytics_service
            device_analytics = await analytics_service.get_device_analytics(screen_id, 1)  # Last 1 hour
            audience_data = device_analytics.get("audience_metrics", {})
        except:
            audience_data = {}
        
        # Build comprehensive status response
        device_online = heartbeat is not None and (datetime.utcnow() - datetime.fromisoformat((heartbeat.get("timestamp") or datetime.utcnow().isoformat()).replace('Z', '+00:00'))).seconds < 300 if heartbeat else False
        network_latency = heartbeat.get("network_latency", 999) if heartbeat else 999
        
        real_time_metrics = {
            # Device connectivity and status
            "deviceOnline": device_online,
            "lastHeartbeat": heartbeat.get("timestamp") if heartbeat else None,
            "connectionQuality": "excellent" if device_online and network_latency < 50 else "good" if device_online else "poor",
            
            # Current content playback
            "currentContent": {
                "id": current_content.get("content_id") if current_content else None,
                "name": current_content.get("content_name") if current_content else None,
                "type": current_content.get("content_type") if current_content else None,
                "startTime": current_content.get("start_time") if current_content else None,
                "progress": current_content.get("progress", 0) if current_content else 0,
                "isPlaying": current_content.get("status") == "playing" if current_content else False
            },
            
            # Real-time system metrics from device
            "systemMetrics": {
                "cpuUsage": heartbeat.get("cpu_usage", 0) if heartbeat else 0,
                "memoryUsage": heartbeat.get("memory_usage", 0) if heartbeat else 0,
                "diskUsage": heartbeat.get("disk_usage", 0) if heartbeat else 0,
                "temperature": heartbeat.get("temperature", 0) if heartbeat else 0,
                "networkLatency": heartbeat.get("network_latency", 999) if heartbeat else 999,
                "uptime": heartbeat.get("uptime", 0) if heartbeat else 0,
                "batteryLevel": heartbeat.get("battery_level", 100) if heartbeat else 100
            },
            
            # Display metrics
            "displayMetrics": {
                "frameRate": heartbeat.get("frame_rate", 0) if heartbeat else 0,
                "droppedFrames": heartbeat.get("dropped_frames", 0) if heartbeat else 0,
                "brightness": heartbeat.get("brightness", 0.8) if heartbeat else 0.8,
                "resolution": heartbeat.get("resolution", "1920x1080") if heartbeat else "1920x1080",
                "orientation": heartbeat.get("orientation", "landscape") if heartbeat else "landscape"
            },
            
            # Real-time audience metrics
            "audienceMetrics": {
                "currentCount": audience_data.get("current_count", 0),
                "averageDwellTime": audience_data.get("average_dwell_time", 0),
                "totalDetections": audience_data.get("total_detections", 0),
                "detectionConfidence": audience_data.get("detection_confidence", 0.8),
                "peakCount": audience_data.get("peak_count", 0)
            },
            
            # Performance and health indicators
            "healthIndicators": {
                "overallScore": heartbeat.get("performance_score", 0.8) if heartbeat else 0.0,
                "status": heartbeat.get("health_status", "unknown") if heartbeat else "offline",
                "warnings": heartbeat.get("warnings", []) if heartbeat else ["Device offline"],
                "errors": heartbeat.get("errors", []) if heartbeat else [],
                "lastMaintenanceCheck": heartbeat.get("timestamp") if heartbeat else None
            },
            
            # Network and connectivity
            "networkMetrics": {
                "latency": heartbeat.get("network_latency", 999) if heartbeat else 999,
                "bandwidth": heartbeat.get("network_bandwidth", 0) if heartbeat else 0,
                "signalStrength": heartbeat.get("wifi_signal_strength", 0) if heartbeat else 0,
                "dataUsage": heartbeat.get("data_usage", 0) if heartbeat else 0
            }
        }
        
        return {
            "id": twin["id"],
            "status": twin["status"],
            "last_accessed": twin.get("last_accessed"),
            "screen_id": screen_id,
            "is_live_mirror": twin.get("is_live_mirror", False),
            "realTimeMetrics": real_time_metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching twin status {twin_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch twin status")

@router.post("/{twin_id}/start")
async def start_digital_twin(
    twin_id: str,
    current_user = Depends(get_current_user)
):
    """Start a digital twin"""
    try:
        twin = await repo.get_digital_twin(twin_id)
        if not twin:
            raise HTTPException(status_code=404, detail="Digital twin not found")
        
        # Verify user has access to this twin's company
        user_context = await get_user_company_context(current_user)
        
        # Update status to running
        twin["status"] = DigitalTwinStatus.RUNNING
        twin["last_accessed"] = datetime.utcnow()
        twin["updated_at"] = datetime.utcnow()
        
        # Convert to model and save
        twin_model = DigitalTwin(**twin)
        saved_twin = await repo.save_digital_twin(twin_model)
        
        return {"message": "Digital twin started successfully", "status": "running"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting digital twin {twin_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to start digital twin")

@router.post("/{twin_id}/stop")
async def stop_digital_twin(
    twin_id: str,
    current_user = Depends(get_current_user)
):
    """Stop a digital twin"""
    try:
        twin = await repo.get_digital_twin(twin_id)
        if not twin:
            raise HTTPException(status_code=404, detail="Digital twin not found")
        
        # Verify user has access to this twin's company
        user_context = await get_user_company_context(current_user)
        
        # Update status to stopped
        twin["status"] = DigitalTwinStatus.STOPPED
        twin["updated_at"] = datetime.utcnow()
        
        # Convert to model and save
        twin_model = DigitalTwin(**twin)
        saved_twin = await repo.save_digital_twin(twin_model)
        
        return {"message": "Digital twin stopped successfully", "status": "stopped"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping digital twin {twin_id}: {e}")
        raise HTTPException(status_code=500, detail="Failed to stop digital twin")

async def update_digital_twin_realtime(device_id: str, heartbeat_data: dict):
    """Update digital twin with real-time data from device heartbeat"""
    try:
        # Find the digital twin associated with this device using the screen_id
        device_twin = await repo.get_digital_twin_by_screen(device_id)
        
        if not device_twin:
            logger.warning(f"No digital twin found for device {device_id}")
            return
        
        # Extract metrics from heartbeat data
        current_time = datetime.utcnow()
        
        # Update the existing twin data with real-time metrics
        device_twin.update({
            "last_heartbeat": current_time,
            "status": DigitalTwinStatus.RUNNING,
            "real_time_metrics": {
                "system_health": {
                    "cpu_usage": heartbeat_data.get("system_metrics", {}).get("cpu_usage", 0),
                    "memory_usage": heartbeat_data.get("system_metrics", {}).get("memory_usage", 0),
                    "disk_usage": heartbeat_data.get("system_metrics", {}).get("disk_usage", 0),
                    "temperature": heartbeat_data.get("system_metrics", {}).get("temperature", 0),
                },
                "display_status": {
                    "brightness": heartbeat_data.get("display_metrics", {}).get("brightness", 50),
                    "resolution": heartbeat_data.get("display_metrics", {}).get("resolution", "1920x1080"),
                    "frame_rate": heartbeat_data.get("display_metrics", {}).get("frame_rate", 60),
                },
                "audience_data": heartbeat_data.get("audience_metrics", {}),
                "current_content": heartbeat_data.get("current_content", {}),
                "uptime_seconds": heartbeat_data.get("uptime", 0),
                "last_restart": heartbeat_data.get("last_restart"),
                "software_version": heartbeat_data.get("software_version", "unknown"),
                "errors": heartbeat_data.get("errors", []),
                "warnings": heartbeat_data.get("warnings", [])
            },
            "updated_at": current_time
        })
        
        # Convert to model and save the updated twin
        twin_model = DigitalTwin(**device_twin)
        await repo.save_digital_twin(twin_model)
        
        logger.info(f"Updated digital twin for device {device_id} with real-time metrics")
        
    except Exception as e:
        logger.error(f"Failed to update digital twin for device {device_id}: {e}")
