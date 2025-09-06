"""
Content Overlay Management API

This module provides endpoints for managing content overlays - the ability to
overlay advertisements and additional content on top of base content in multiple
zones with scheduling and category-based ad selection.
"""

from fastapi import APIRouter, HTTPException, Depends, Form, Query
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
import logging

from app.auth import get_current_user, get_user_company_context
from app.models import (
    ContentOverlay, ContentOverlayCreate, ContentOverlayUpdate,
    ContentOverlayStatus, ContentCategory, ContentTag
)
from app.repo import repo
from app.utils.serialization import safe_json_response, ensure_string_id
from app.websocket_manager import websocket_manager

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/overlays/create")
async def create_content_overlay(
    overlay_data: ContentOverlayCreate,
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Create a new content overlay configuration"""
    try:
        current_user_id = current_user.get("id")
        is_platform_admin = company_context["is_platform_admin"]
        
        # Verify user has permission to create overlays
        if not is_platform_admin:
            # Check if user can access the content and screen
            content_access = await repo.check_content_access_permission(
                current_user_id, overlay_data.content_id, "edit"
            )
            if not content_access:
                raise HTTPException(status_code=403, detail="No access to specified content")
        
        # Verify content exists and is approved
        content = await repo.get_content_meta(overlay_data.content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        if content.get("status") != "approved":
            raise HTTPException(status_code=400, detail="Content must be approved for overlay creation")
        
        # Verify screen exists
        screen = await repo.get_digital_screen(overlay_data.screen_id)
        if not screen:
            raise HTTPException(status_code=404, detail="Screen not found")
        
        # Create overlay
        overlay = ContentOverlay(
            id=str(uuid.uuid4()),
            created_by=current_user_id,
            **overlay_data.model_dump()
        )
        
        # Save overlay
        saved_overlay = await repo.save_content_overlay(overlay.model_dump())
        
        # Notify connected devices about new overlay
        await websocket_manager.notify_overlay_update(
            overlay_data.screen_id, overlay.id, "created"
        )
        
        logger.info(f"Content overlay created: {overlay.id} by user {current_user_id}")
        
        return safe_json_response({
            "status": "created",
            "overlay_id": overlay.id,
            "message": "Content overlay created successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create content overlay: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create overlay: {str(e)}")


@router.get("/overlays/{content_id}")
async def get_content_overlays(
    content_id: str,
    screen_id: Optional[str] = Query(None),
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Get overlay configurations for specific content"""
    try:
        current_user_id = current_user.get("id")
        is_platform_admin = company_context["is_platform_admin"]
        
        # Verify user has access to content
        if not is_platform_admin:
            content_access = await repo.check_content_access_permission(
                current_user_id, content_id, "view"
            )
            if not content_access:
                raise HTTPException(status_code=403, detail="No access to specified content")
        
        # Get overlays for this content
        overlays = await repo.list_content_overlays(content_id=content_id, screen_id=screen_id)
        
        # Enhance with screen information
        enhanced_overlays = []
        for overlay in overlays:
            screen_id = overlay.get("screen_id")
            screen = await repo.get_digital_screen(screen_id) if screen_id else None
            
            enhanced_overlay = {
                **overlay,
                "screen_name": screen.get("name") if screen else "Unknown Screen",
                "screen_location": screen.get("location") if screen else "Unknown Location"
            }
            enhanced_overlays.append(enhanced_overlay)
        
        return safe_json_response({
            "content_id": content_id,
            "overlays": enhanced_overlays,
            "total": len(enhanced_overlays)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get content overlays: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get overlays: {str(e)}")


@router.put("/overlays/{overlay_id}")
async def update_content_overlay(
    overlay_id: str,
    overlay_data: ContentOverlayUpdate,
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Update an existing content overlay"""
    try:
        current_user_id = current_user.get("id")
        is_platform_admin = company_context["is_platform_admin"]
        
        # Get existing overlay
        overlay = await repo.get_content_overlay(overlay_id)
        if not overlay:
            raise HTTPException(status_code=404, detail="Overlay not found")
        
        # Verify user has permission to update this overlay
        if not is_platform_admin:
            if overlay.get("created_by") != current_user_id:
                # Check if user can access the content
                content_id = overlay.get("content_id")
                content_access = await repo.check_content_access_permission(
                    current_user_id, content_id, "edit"
                )
                if not content_access:
                    raise HTTPException(status_code=403, detail="No permission to update this overlay")
        
        # Update overlay fields
        update_data = overlay_data.model_dump(exclude_unset=True)
        if update_data:
            overlay.update(update_data)
            overlay["updated_at"] = datetime.utcnow()
            
            # Save updated overlay
            await repo.update_content_overlay(overlay_id, overlay)
            
            # Notify connected devices about overlay update
            screen_id = overlay.get("screen_id")
            if screen_id:
                await websocket_manager.notify_overlay_update(
                    screen_id, overlay_id, "updated"
                )
            
            logger.info(f"Content overlay updated: {overlay_id} by user {current_user_id}")
        
        return safe_json_response({
            "status": "updated",
            "overlay_id": overlay_id,
            "message": "Content overlay updated successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update content overlay: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to update overlay: {str(e)}")


@router.delete("/overlays/{overlay_id}")
async def delete_content_overlay(
    overlay_id: str,
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Delete a content overlay"""
    try:
        current_user_id = current_user.get("id")
        is_platform_admin = company_context["is_platform_admin"]
        
        # Get existing overlay
        overlay = await repo.get_content_overlay(overlay_id)
        if not overlay:
            raise HTTPException(status_code=404, detail="Overlay not found")
        
        # Verify user has permission to delete this overlay
        if not is_platform_admin:
            if overlay.get("created_by") != current_user_id:
                # Check if user can access the content
                content_id = overlay.get("content_id")
                content_access = await repo.check_content_access_permission(
                    current_user_id, content_id, "edit"
                )
                if not content_access:
                    raise HTTPException(status_code=403, detail="No permission to delete this overlay")
        
        # Delete overlay
        screen_id = overlay.get("screen_id")
        await repo.delete_content_overlay(overlay_id)
        
        # Notify connected devices about overlay deletion
        if screen_id:
            await websocket_manager.notify_overlay_update(
                screen_id, overlay_id, "deleted"
            )
        
        logger.info(f"Content overlay deleted: {overlay_id} by user {current_user_id}")
        
        return safe_json_response({
            "status": "deleted",
            "overlay_id": overlay_id,
            "message": "Content overlay deleted successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete content overlay: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete overlay: {str(e)}")


@router.get("/overlays/categories")
async def get_ad_categories(
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Get available advertisement categories for overlay selection"""
    try:
        # Get all active content categories
        categories = await repo.list_content_categories(is_active=True)
        
        # Add default categories if none exist
        if not categories:
            default_categories = [
                {"id": "electronics", "name": "Electronics", "description": "Electronic devices and gadgets"},
                {"id": "fashion", "name": "Fashion", "description": "Clothing and accessories"},
                {"id": "food", "name": "Food & Beverage", "description": "Restaurants and food products"},
                {"id": "automotive", "name": "Automotive", "description": "Cars and automotive services"},
                {"id": "health", "name": "Health & Beauty", "description": "Healthcare and beauty products"},
                {"id": "entertainment", "name": "Entertainment", "description": "Movies, games, and entertainment"},
                {"id": "travel", "name": "Travel", "description": "Travel and tourism services"},
                {"id": "education", "name": "Education", "description": "Educational services and products"},
                {"id": "real_estate", "name": "Real Estate", "description": "Property and real estate services"},
                {"id": "finance", "name": "Finance", "description": "Banking and financial services"}
            ]
            categories = default_categories
        
        return safe_json_response({
            "categories": categories,
            "total": len(categories)
        })
        
    except Exception as e:
        logger.error(f"Failed to get ad categories: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get categories: {str(e)}")


@router.get("/overlays/screen/{screen_id}")
async def get_screen_overlays(
    screen_id: str,
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Get all active overlays for a specific screen"""
    try:
        current_user_id = current_user.get("id")
        is_platform_admin = company_context["is_platform_admin"]
        
        # Verify screen exists and user has access
        screen = await repo.get_digital_screen(screen_id)
        if not screen:
            raise HTTPException(status_code=404, detail="Screen not found")
        
        if not is_platform_admin:
            # Check if user's company owns this screen
            screen_company_id = screen.get("company_id")
            accessible_companies = company_context["accessible_companies"]
            accessible_company_ids = {c.get("id") for c in accessible_companies}
            
            if screen_company_id not in accessible_company_ids:
                raise HTTPException(status_code=403, detail="No access to this screen")
        
        # Get active overlays for this screen
        overlays = await repo.list_content_overlays(screen_id=screen_id)
        
        # Filter only active overlays and enhance with content information
        active_overlays = []
        current_time = datetime.utcnow()
        
        for overlay in overlays:
            status = overlay.get("status")
            start_time = overlay.get("start_time")
            end_time = overlay.get("end_time")
            
            # Check if overlay is currently active
            is_active = status == ContentOverlayStatus.ACTIVE
            
            if start_time:
                start_time = datetime.fromisoformat(start_time) if isinstance(start_time, str) else start_time
                if current_time < start_time:
                    is_active = False  # Not started yet
            
            if end_time:
                end_time = datetime.fromisoformat(end_time) if isinstance(end_time, str) else end_time
                if current_time > end_time:
                    is_active = False  # Expired
            
            if is_active:
                # Get content information
                content_id = overlay.get("content_id")
                content = await repo.get_content_meta(content_id) if content_id else None
                
                enhanced_overlay = {
                    **overlay,
                    "content": {
                        "id": content.get("id") if content else None,
                        "title": content.get("title") if content else "Unknown Content",
                        "filename": content.get("filename") if content else None,
                        "content_type": content.get("content_type") if content else None
                    } if content else None
                }
                active_overlays.append(enhanced_overlay)
        
        return safe_json_response({
            "screen_id": screen_id,
            "screen_name": screen.get("name"),
            "overlays": active_overlays,
            "total": len(active_overlays)
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get screen overlays: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get screen overlays: {str(e)}")


@router.post("/overlays/bulk-create")
async def bulk_create_overlays(
    base_content_id: str = Form(...),
    screen_ids: List[str] = Form(...),
    overlay_zones: List[Dict[str, Any]] = Form(...),
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Create multiple overlay zones across multiple screens efficiently"""
    try:
        current_user_id = current_user.get("id")
        is_platform_admin = company_context["is_platform_admin"]
        
        # Verify content exists and user has access
        content = await repo.get_content_meta(base_content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Base content not found")
        
        if not is_platform_admin:
            content_access = await repo.check_content_access_permission(
                current_user_id, base_content_id, "edit"
            )
            if not content_access:
                raise HTTPException(status_code=403, detail="No access to specified content")
        
        # Verify all screens exist and are accessible
        valid_screens = []
        for screen_id in screen_ids:
            screen = await repo.get_digital_screen(screen_id)
            if screen:
                valid_screens.append(screen)
            else:
                logger.warning(f"Screen {screen_id} not found, skipping")
        
        if not valid_screens:
            raise HTTPException(status_code=400, detail="No valid screens found")
        
        # Create overlays for each screen-zone combination
        created_overlays = []
        for screen in valid_screens:
            screen_id = screen.get("id")
            
            for zone_config in overlay_zones:
                overlay = ContentOverlay(
                    id=str(uuid.uuid4()),
                    content_id=base_content_id,
                    screen_id=screen_id,
                    company_id=content.get("owner_id"),  # Use content owner's company
                    name=f"{content.get('title', 'Content')} - Zone {zone_config.get('name', 'Unknown')}",
                    position_x=zone_config.get("position_x", 0),
                    position_y=zone_config.get("position_y", 0),
                    width=zone_config.get("width", 100),
                    height=zone_config.get("height", 100),
                    z_index=zone_config.get("z_index", 1),
                    opacity=zone_config.get("opacity", 1.0),
                    rotation=zone_config.get("rotation", 0.0),
                    start_time=zone_config.get("start_time"),
                    end_time=zone_config.get("end_time"),
                    status=ContentOverlayStatus.ACTIVE,
                    created_by=current_user_id
                )
                
                saved_overlay = await repo.save_content_overlay(overlay.model_dump())
                created_overlays.append(saved_overlay)
                
                # Notify device about new overlay
                await websocket_manager.notify_overlay_update(
                    screen_id, overlay.id, "created"
                )
        
        logger.info(f"Bulk created {len(created_overlays)} overlays by user {current_user_id}")
        
        return safe_json_response({
            "status": "bulk_created",
            "total_overlays": len(created_overlays),
            "screens_affected": len(valid_screens),
            "overlay_ids": [o.get("id") for o in created_overlays],
            "message": f"Created {len(created_overlays)} overlay configurations"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to bulk create overlays: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to bulk create overlays: {str(e)}")


@router.get("/overlays/schedule-conflicts/{screen_id}")
async def check_schedule_conflicts(
    screen_id: str,
    start_time: datetime = Query(...),
    end_time: datetime = Query(...),
    exclude_overlay_id: Optional[str] = Query(None),
    current_user=Depends(get_current_user)
):
    """Check for scheduling conflicts on a screen for the given time period"""
    try:
        # Get all overlays for this screen
        overlays = await repo.list_content_overlays(screen_id=screen_id)
        
        conflicts = []
        for overlay in overlays:
            # Skip the overlay being edited
            if exclude_overlay_id and overlay.get("id") == exclude_overlay_id:
                continue
            
            overlay_start = overlay.get("start_time")
            overlay_end = overlay.get("end_time")
            
            # Convert string dates to datetime if needed
            if overlay_start:
                overlay_start = datetime.fromisoformat(overlay_start) if isinstance(overlay_start, str) else overlay_start
            if overlay_end:
                overlay_end = datetime.fromisoformat(overlay_end) if isinstance(overlay_end, str) else overlay_end
            
            # Check for time overlap
            has_conflict = False
            if overlay_start and overlay_end:
                # Both have start and end times
                if not (end_time <= overlay_start or start_time >= overlay_end):
                    has_conflict = True
            elif overlay_start and not overlay_end:
                # Overlay starts but doesn't end
                if start_time < overlay_start or not end_time:
                    has_conflict = True
            elif not overlay_start and overlay_end:
                # Overlay ends but no start time (always active until end)
                if start_time < overlay_end:
                    has_conflict = True
            elif not overlay_start and not overlay_end:
                # Always active overlay
                has_conflict = True
            
            if has_conflict:
                conflicts.append({
                    "overlay_id": overlay.get("id"),
                    "overlay_name": overlay.get("name"),
                    "start_time": overlay_start.isoformat() if overlay_start else None,
                    "end_time": overlay_end.isoformat() if overlay_end else None,
                    "status": overlay.get("status")
                })
        
        return safe_json_response({
            "screen_id": screen_id,
            "requested_period": {
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat()
            },
            "has_conflicts": len(conflicts) > 0,
            "conflicts": conflicts,
            "total_conflicts": len(conflicts)
        })
        
    except Exception as e:
        logger.error(f"Failed to check schedule conflicts: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check conflicts: {str(e)}")


@router.post("/overlays/{overlay_id}/activate")
async def activate_overlay(
    overlay_id: str,
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Manually activate an overlay (useful for testing or immediate deployment)"""
    try:
        current_user_id = current_user.get("id")
        
        # Get overlay
        overlay = await repo.get_content_overlay(overlay_id)
        if not overlay:
            raise HTTPException(status_code=404, detail="Overlay not found")
        
        # Verify permission
        if not company_context["is_platform_admin"]:
            if overlay.get("created_by") != current_user_id:
                content_id = overlay.get("content_id")
                content_access = await repo.check_content_access_permission(
                    current_user_id, content_id, "edit"
                )
                if not content_access:
                    raise HTTPException(status_code=403, detail="No permission to activate this overlay")
        
        # Update status to active
        overlay["status"] = ContentOverlayStatus.ACTIVE
        overlay["updated_at"] = datetime.utcnow()
        
        await repo.update_content_overlay(overlay_id, overlay)
        
        # Notify device
        screen_id = overlay.get("screen_id")
        if screen_id:
            await websocket_manager.notify_overlay_update(
                screen_id, overlay_id, "activated"
            )
        
        logger.info(f"Overlay activated: {overlay_id} by user {current_user_id}")
        
        return safe_json_response({
            "status": "activated",
            "overlay_id": overlay_id,
            "message": "Overlay activated successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to activate overlay: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to activate overlay: {str(e)}")


@router.post("/overlays/{overlay_id}/deactivate")
async def deactivate_overlay(
    overlay_id: str,
    current_user=Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Manually deactivate an overlay (pauses display without deletion)"""
    try:
        current_user_id = current_user.get("id")
        
        # Get overlay
        overlay = await repo.get_content_overlay(overlay_id)
        if not overlay:
            raise HTTPException(status_code=404, detail="Overlay not found")
        
        # Verify permission
        if not company_context["is_platform_admin"]:
            if overlay.get("created_by") != current_user_id:
                content_id = overlay.get("content_id")
                content_access = await repo.check_content_access_permission(
                    current_user_id, content_id, "edit"
                )
                if not content_access:
                    raise HTTPException(status_code=403, detail="No permission to deactivate this overlay")
        
        # Update status to paused
        overlay["status"] = ContentOverlayStatus.PAUSED
        overlay["updated_at"] = datetime.utcnow()
        
        await repo.update_content_overlay(overlay_id, overlay)
        
        # Notify device
        screen_id = overlay.get("screen_id")
        if screen_id:
            await websocket_manager.notify_overlay_update(
                screen_id, overlay_id, "deactivated"
            )
        
        logger.info(f"Overlay deactivated: {overlay_id} by user {current_user_id}")
        
        return safe_json_response({
            "status": "deactivated",
            "overlay_id": overlay_id,
            "message": "Overlay deactivated successfully"
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to deactivate overlay: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to deactivate overlay: {str(e)}")
