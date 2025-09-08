"""
Unified Overlay Management API
Consolidates overlay functionality from:
- app/routes/overlay.py (basic overlay CRUD)
- app/api/overlays.py (enhanced overlay management)

This unified API provides:
- Overlay CRUD operations
- Screen assignment and scheduling
- Content overlay management
- Z-index and positioning control
"""

from typing import List, Dict, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from datetime import datetime

from ..models import ContentOverlay, ContentOverlayCreate, ContentOverlayUpdate
from ..api.auth import get_current_user
from ..repo import repo
from ..utils.serialization import safe_json_response

router = APIRouter(prefix="/overlays", tags=["overlays"])
security = HTTPBearer()

class OverlayResponse(BaseModel):
    id: str
    content_id: str
    screen_id: str
    position: Dict[str, int] = Field(..., description="Position and size {x, y, width, height}")
    z_index: int = Field(default=1, description="Layer order")
    opacity: float = Field(default=1.0, description="Opacity 0.0-1.0")
    is_active: bool = Field(default=True)
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    created_at: str
    created_by: str
    content_title: Optional[str] = None

class OverlayCreateRequest(BaseModel):
    content_id: str
    screen_id: str
    position: Dict[str, int] = Field(..., description="Position and size {x, y, width, height}")
    z_index: int = Field(default=1, description="Layer order")
    opacity: float = Field(default=1.0, description="Opacity 0.0-1.0")
    is_active: bool = Field(default=True)
    start_time: Optional[str] = None
    end_time: Optional[str] = None

class OverlayUpdateRequest(BaseModel):
    content_id: Optional[str] = None
    screen_id: Optional[str] = None
    position: Optional[Dict[str, int]] = None
    z_index: Optional[int] = None
    opacity: Optional[float] = None
    is_active: Optional[bool] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None

@router.get("/", response_model=List[OverlayResponse])
async def list_overlays(
    screen_id: Optional[str] = Query(None, description="Filter by screen ID"),
    content_id: Optional[str] = Query(None, description="Filter by content ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: dict = Depends(get_current_user)
):
    """List all content overlays with optional filtering"""
    try:
        # Get overlays from repository
        overlays = await repo.list_content_overlays(screen_id=screen_id)

        # Apply additional filters
        if content_id:
            overlays = [o for o in overlays if o.get("content_id") == content_id]

        if is_active is not None:
            overlays = [o for o in overlays if o.get("is_active") == is_active]

        # Enhance with content information
        enhanced_overlays = []
        for overlay in overlays:
            try:
                # Get content metadata for title
                content_meta = await repo.get_metadata(overlay.get("content_id", ""))
                overlay["content_title"] = content_meta.get("title", "Unknown") if content_meta else "Unknown"
            except:
                overlay["content_title"] = "Unknown"

            enhanced_overlays.append(overlay)

        return safe_json_response(enhanced_overlays)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list overlays: {e}")

@router.post("/", response_model=OverlayResponse)
async def create_overlay(
    overlay_data: OverlayCreateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Create a new content overlay"""
    try:
        # Validate content exists
        content_meta = await repo.get_metadata(overlay_data.content_id)
        if not content_meta:
            raise HTTPException(status_code=404, detail="Content not found")

        # Create overlay dict
        overlay_dict = {
            "content_id": overlay_data.content_id,
            "screen_id": overlay_data.screen_id,
            "position": overlay_data.position,
            "z_index": overlay_data.z_index,
            "opacity": overlay_data.opacity,
            "is_active": overlay_data.is_active,
            "start_time": overlay_data.start_time,
            "end_time": overlay_data.end_time,
            "created_at": datetime.utcnow().isoformat(),
            "created_by": current_user.get("id", "system")
        }

        # Save overlay
        saved_overlay = await repo.save_content_overlay(overlay_dict)

        # Add content title
        saved_overlay["content_title"] = content_meta.get("title", "Unknown")

        return safe_json_response(saved_overlay)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create overlay: {e}")

@router.get("/{overlay_id}", response_model=OverlayResponse)
async def get_overlay(
    overlay_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific overlay by ID"""
    try:
        overlay = await repo.get_content_overlay(overlay_id)
        if not overlay:
            raise HTTPException(status_code=404, detail="Overlay not found")

        # Add content title
        try:
            content_meta = await repo.get_metadata(overlay.get("content_id", ""))
            overlay["content_title"] = content_meta.get("title", "Unknown") if content_meta else "Unknown"
        except:
            overlay["content_title"] = "Unknown"

        return safe_json_response(overlay)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get overlay: {e}")

@router.put("/{overlay_id}", response_model=OverlayResponse)
async def update_overlay(
    overlay_id: str,
    overlay_data: OverlayUpdateRequest,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing overlay"""
    try:
        # Get existing overlay
        existing_overlay = await repo.get_content_overlay(overlay_id)
        if not existing_overlay:
            raise HTTPException(status_code=404, detail="Overlay not found")

        # Update only provided fields
        updated_overlay = existing_overlay.copy()
        update_data = overlay_data.dict(exclude_unset=True)

        for key, value in update_data.items():
            if value is not None:
                updated_overlay[key] = value

        # Update timestamp
        updated_overlay["updated_at"] = datetime.utcnow().isoformat()
        updated_overlay["updated_by"] = current_user.get("id", "system")

        # Validate content if changed
        if "content_id" in update_data:
            content_meta = await repo.get_metadata(updated_overlay["content_id"])
            if not content_meta:
                raise HTTPException(status_code=404, detail="Content not found")

        # Save updated overlay
        saved_overlay = await repo.save_content_overlay(updated_overlay)

        # Add content title
        try:
            content_meta = await repo.get_metadata(saved_overlay.get("content_id", ""))
            saved_overlay["content_title"] = content_meta.get("title", "Unknown") if content_meta else "Unknown"
        except:
            saved_overlay["content_title"] = "Unknown"

        return safe_json_response(saved_overlay)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update overlay: {e}")

@router.delete("/{overlay_id}")
async def delete_overlay(
    overlay_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete an overlay"""
    try:
        # Check if overlay exists
        existing_overlay = await repo.get_content_overlay(overlay_id)
        if not existing_overlay:
            raise HTTPException(status_code=404, detail="Overlay not found")

        # Delete overlay
        await repo.delete_content_overlay(overlay_id)

        return {"message": "Overlay deleted successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete overlay: {e}")

@router.post("/{overlay_id}/toggle")
async def toggle_overlay_status(
    overlay_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Toggle overlay active status"""
    try:
        # Get existing overlay
        existing_overlay = await repo.get_content_overlay(overlay_id)
        if not existing_overlay:
            raise HTTPException(status_code=404, detail="Overlay not found")

        # Toggle active status
        updated_overlay = existing_overlay.copy()
        updated_overlay["is_active"] = not existing_overlay.get("is_active", True)

        # Update timestamp
        updated_overlay["updated_at"] = datetime.utcnow().isoformat()
        updated_overlay["updated_by"] = current_user.get("id", "system")

        # Save updated overlay
        saved_overlay = await repo.save_content_overlay(updated_overlay)

        return {"message": f"Overlay {'activated' if saved_overlay['is_active'] else 'deactivated'}", "is_active": saved_overlay["is_active"]}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to toggle overlay: {e}")

# ============================================================================
# SCREEN-SPECIFIC OVERLAY ENDPOINTS
# ============================================================================

@router.get("/screen/{screen_id}/active")
async def get_active_overlays_for_screen(
    screen_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all active overlays for a specific screen"""
    try:
        overlays = await repo.list_content_overlays(screen_id=screen_id, is_active=True)

        # Enhance with content information
        enhanced_overlays = []
        for overlay in overlays:
            try:
                content_meta = await repo.get_metadata(overlay.get("content_id", ""))
                overlay["content_title"] = content_meta.get("title", "Unknown") if content_meta else "Unknown"
                overlay["content_url"] = content_meta.get("url") if content_meta else None
            except:
                overlay["content_title"] = "Unknown"
                overlay["content_url"] = None

            enhanced_overlays.append(overlay)

        return safe_json_response({
            "screen_id": screen_id,
            "active_overlays": enhanced_overlays,
            "count": len(enhanced_overlays)
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get active overlays for screen {screen_id}: {e}")

@router.post("/screen/{screen_id}/schedule")
async def schedule_overlay_for_screen(
    screen_id: str,
    overlay_id: str,
    start_time: str,
    end_time: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """Schedule an overlay for display on a specific screen"""
    try:
        # Validate overlay exists
        overlay = await repo.get_content_overlay(overlay_id)
        if not overlay:
            raise HTTPException(status_code=404, detail="Overlay not found")

        # Validate screen exists and user has access
        screen = await repo.get_digital_screen(screen_id)
        if not screen:
            raise HTTPException(status_code=404, detail="Screen not found")

        # Update overlay with scheduling information
        updated_overlay = overlay.copy()
        updated_overlay["screen_id"] = screen_id
        updated_overlay["start_time"] = start_time
        updated_overlay["end_time"] = end_time
        updated_overlay["is_active"] = True
        updated_overlay["updated_at"] = datetime.utcnow().isoformat()
        updated_overlay["updated_by"] = current_user.get("id", "system")

        # Save updated overlay
        saved_overlay = await repo.save_content_overlay(updated_overlay)

        return safe_json_response({
            "message": "Overlay scheduled successfully",
            "overlay_id": overlay_id,
            "screen_id": screen_id,
            "start_time": start_time,
            "end_time": end_time
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to schedule overlay: {e}")

@router.delete("/screen/{screen_id}/overlay/{overlay_id}")
async def remove_overlay_from_screen(
    screen_id: str,
    overlay_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Remove an overlay from a specific screen"""
    try:
        # Get overlay
        overlay = await repo.get_content_overlay(overlay_id)
        if not overlay:
            raise HTTPException(status_code=404, detail="Overlay not found")

        # Check if overlay is assigned to the screen
        if overlay.get("screen_id") != screen_id:
            raise HTTPException(status_code=400, detail="Overlay is not assigned to this screen")

        # Remove screen assignment
        updated_overlay = overlay.copy()
        updated_overlay["screen_id"] = None
        updated_overlay["is_active"] = False
        updated_overlay["updated_at"] = datetime.utcnow().isoformat()
        updated_overlay["updated_by"] = current_user.get("id", "system")

        # Save updated overlay
        await repo.save_content_overlay(updated_overlay)

        return {"message": "Overlay removed from screen successfully"}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove overlay from screen: {e}")
