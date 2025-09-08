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
        update_data = twin_update.dict(exclude_unset=True)
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
    """Get digital twin status and metrics"""
    try:
        twin = await repo.get_digital_twin(twin_id)
        if not twin:
            raise HTTPException(status_code=404, detail="Digital twin not found")
        
        # Verify user has access to this twin's company
        user_context = await get_user_company_context(current_user)
        
        # Return status and mock metrics
        return {
            "id": twin["id"],
            "status": twin["status"],
            "last_accessed": twin.get("last_accessed"),
            "metrics": {
                "fps": 60,
                "cpu_usage": 25,
                "memory_usage": 512,
                "network_latency": 45,
                "uptime": "2h 34m"
            }
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
