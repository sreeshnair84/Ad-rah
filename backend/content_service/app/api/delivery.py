"""
Content Delivery API for Flutter Application
Provides content with overlay positioning data
"""

from fastapi import APIRouter, HTTPException, Depends
from app.auth import get_current_user
from app.repo import repo
import logging
from typing import List, Dict, Optional
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/content/{device_id}")
async def get_device_content(
    device_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get current content for a device with overlay information"""
    try:
        # Get device info
        device = await repo.get_digital_screen(device_id)
        if not device:
            raise HTTPException(status_code=404, detail="Device not found")
        
        # Get device schedule (use existing schedule method or mock)
        try:
            schedule = await repo.get_device_schedule(device_id)
        except AttributeError:
            # If method doesn't exist, create a basic schedule structure
            schedule = {
                "id": f"schedule_{device_id}",
                "device_id": device_id,
                "content_slots": []
            }
            
            # Get approved content and create basic slots
            all_content = await repo.list_content_meta()
            approved_content = [c for c in all_content if c.get("status") == "approved"]
            
            for i, content in enumerate(approved_content[:5]):  # Limit to 5 items
                schedule["content_slots"].append({
                    "id": f"slot_{i}",
                    "content_id": content["id"],
                    "duration": 10,  # Default 10 seconds
                    "priority": 1
                })
        
        if not schedule:
            return {
                "device_id": device_id,
                "content_items": [],
                "overlays": [],
                "message": "No schedule configured"
            }
        
        content_items = []
        all_overlays = []
        
        # Process scheduled content
        for slot in schedule.get("content_slots", []):
            content_id = slot.get("content_id")
            if not content_id:
                continue
                
            # Get content details
            try:
                content = await repo.get_content_meta(content_id)
            except AttributeError:
                content = await repo.get_content_meta(content_id)
                
            if not content or content.get("status") != "approved":
                continue
            
            # Get overlays for this content
            content_overlays = await repo.get_active_overlays_for_content(content_id, device_id)
            
            content_item = {
                "content": {
                    "id": content["id"],
                    "title": content["title"],
                    "description": content.get("description", ""),
                    "type": content.get("type", "image"),
                    "url": content.get("url"),
                    "duration": slot.get("duration", content.get("duration", 10)),
                    "file_path": content.get("file_path"),
                    "categories": content.get("categories", []),
                    "tags": content.get("tags", [])
                },
                "slot": {
                    "id": slot.get("id"),
                    "start_time": slot.get("start_time"),
                    "end_time": slot.get("end_time"),
                    "duration": slot.get("duration"),
                    "priority": slot.get("priority", 1)
                },
                "overlays": content_overlays
            }
            
            content_items.append(content_item)
            all_overlays.extend(content_overlays)
        
        # Get global overlays (not tied to specific content)
        global_overlays = []
        try:
            # Get all overlays for the screen and filter for global ones
            screen_overlays = await repo.get_content_overlays_by_screen(device_id)
            global_overlays = [o for o in screen_overlays if o.get("content_id") is None and o.get("is_active", True)]
        except Exception as e:
            logger.warning(f"Could not get global overlays: {e}")
            
        all_overlays.extend(global_overlays)
        
        # Remove duplicates
        seen_overlay_ids = set()
        unique_overlays = []
        for overlay in all_overlays:
            if overlay["id"] not in seen_overlay_ids:
                unique_overlays.append(overlay)
                seen_overlay_ids.add(overlay["id"])
        
        return {
            "device_id": device_id,
            "device_info": {
                "name": device.get("name"),
                "resolution_width": device.get("resolution_width"),
                "resolution_height": device.get("resolution_height"),
                "orientation": device.get("orientation")
            },
            "content_items": content_items,
            "global_overlays": global_overlays,
            "all_overlays": unique_overlays,
            "schedule_id": schedule.get("id"),
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting device content: {e}")
        raise HTTPException(status_code=500, detail="Failed to get device content")

@router.get("/content/{device_id}/current")
async def get_current_content_item(
    device_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get the current content item that should be displayed"""
    try:
        content_data = await get_device_content(device_id, current_user)
        
        if not content_data["content_items"]:
            return {
                "current_content": None,
                "next_content": None,
                "overlays": content_data["global_overlays"],
                "message": "No content scheduled"
            }
        
        # For simplicity, use first content item as current
        # In production, this would use time-based scheduling
        current_content = content_data["content_items"][0]
        next_content = None
        
        if len(content_data["content_items"]) > 1:
            next_content = content_data["content_items"][1]
        
        return {
            "current_content": current_content,
            "next_content": next_content,
            "all_content": content_data["content_items"],
            "overlays": content_data["all_overlays"],
            "device_info": content_data["device_info"]
        }
        
    except Exception as e:
        logger.error(f"Error getting current content: {e}")
        raise HTTPException(status_code=500, detail="Failed to get current content")

@router.post("/content/{device_id}/playback-event")
async def log_playback_event(
    device_id: str,
    event_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Log playback events for analytics"""
    try:
        event_data.update({
            "device_id": device_id,
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": current_user.get("id")
        })
        
        # Log the event (implement proper logging here)
        logger.info(f"Playback event: {event_data}")
        
        return {"success": True, "message": "Event logged"}
        
    except Exception as e:
        logger.error(f"Error logging playback event: {e}")
        raise HTTPException(status_code=500, detail="Failed to log event")

@router.get("/overlay-templates")
async def get_overlay_templates(
    current_user: dict = Depends(get_current_user)
):
    """Get available overlay templates for HOST users"""
    try:
        templates = [
            {
                "id": "welcome_banner",
                "name": "Welcome Banner",
                "description": "Top banner for welcome messages",
                "position": {"x": 0, "y": 0},
                "size": {"width": 100, "height": 15},
                "preview_url": "/api/templates/welcome_banner/preview"
            },
            {
                "id": "bottom_ticker",
                "name": "Bottom Ticker",
                "description": "Scrolling text at bottom of screen",
                "position": {"x": 0, "y": 85},
                "size": {"width": 100, "height": 15},
                "preview_url": "/api/templates/bottom_ticker/preview"
            },
            {
                "id": "corner_logo",
                "name": "Corner Logo",
                "description": "Small logo in corner",
                "position": {"x": 75, "y": 5},
                "size": {"width": 20, "height": 20},
                "preview_url": "/api/templates/corner_logo/preview"
            },
            {
                "id": "side_panel",
                "name": "Side Panel",
                "description": "Information panel on the side",
                "position": {"x": 75, "y": 25},
                "size": {"width": 25, "height": 50},
                "preview_url": "/api/templates/side_panel/preview"
            }
        ]
        
        return {"templates": templates}
        
    except Exception as e:
        logger.error(f"Error getting overlay templates: {e}")
        raise HTTPException(status_code=500, detail="Failed to get templates")
