from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Optional
from datetime import datetime
import uuid

from app.models import (
    DigitalScreen, ScreenCreate, ScreenUpdate, ScreenStatus,
    ContentOverlay, ContentOverlayCreate, ContentOverlayUpdate,
    DigitalTwin, DigitalTwinCreate, DigitalTwinUpdate,
    LayoutTemplate, LayoutTemplateCreate, LayoutTemplateUpdate
)
from app.api.auth import get_current_user
from app.repo import repo

router = APIRouter(prefix="/screens", tags=["screens"])


# Mock data initialization is handled by startup lifecycle in main.py


# Digital Screen endpoints
@router.get("", response_model=List[dict])
async def get_screens(
    company_id: Optional[str] = None,
    status: Optional[ScreenStatus] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all digital screens with optional filtering"""
    screens = await repo.list_digital_screens(company_id)
    
    # Filter by status if specified  
    if status:
        screens = [s for s in screens if s.get("status") == status.value]
    
    # Role-based filtering - non-admins only see their company's screens
    user_roles = current_user.get("roles", [])
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    user_has_global_access = any(role.get("company_id") == "global" for role in user_roles)
    
    if not user_is_admin and not user_has_global_access:
        user_company_ids = [role.get("company_id") for role in user_roles]
        screens = [s for s in screens if s.get("company_id") in user_company_ids]
    
    return screens
@router.post("", response_model=dict)
async def create_screen(
    screen_data: ScreenCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new digital screen"""
    screen_id = str(uuid.uuid4())
    screen = screen_data.dict()
    screen.update({
        "id": screen_id,
        "status": ScreenStatus.ACTIVE,  # Use enum instead of string
        "last_seen": None,
        "created_at": datetime.utcnow(),  # Use datetime object instead of ISO string
        "updated_at": datetime.utcnow(),  # Use datetime object instead of ISO string
    })
    
    # Create DigitalScreen model instance
    from app.models import DigitalScreen
    screen_model = DigitalScreen(**screen)
    result = await repo.save_digital_screen(screen_model)
    return result


@router.get("/{screen_id}", response_model=dict)
async def get_screen(
    screen_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific digital screen"""
    screen = await repo.get_digital_screen(screen_id)
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    # Role-based access check
    user_roles = current_user.get("roles", [])
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    user_has_global_access = any(role.get("company_id") == "global" for role in user_roles)
    
    if not user_is_admin and not user_has_global_access:
        user_company_ids = [role.get("company_id") for role in user_roles] 
        if screen.get("company_id") not in user_company_ids:
            raise HTTPException(status_code=403, detail="Access denied to this screen")
    
    return screen


@router.put("/{screen_id}", response_model=dict)
async def update_screen(
    screen_id: str,
    screen_data: ScreenUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a digital screen"""
    screen = await repo.get_digital_screen(screen_id)
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    # Role-based access check
    user_roles = current_user.get("roles", [])
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    user_has_global_access = any(role.get("company_id") == "global" for role in user_roles)
    
    if not user_is_admin and not user_has_global_access:
        user_company_ids = [role.get("company_id") for role in user_roles]
        if screen.get("company_id") not in user_company_ids:
            raise HTTPException(status_code=403, detail="Access denied to this screen")
    
    # Update fields
    update_data = screen_data.dict(exclude_unset=True)
    success = await repo.update_digital_screen(screen_id, update_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update screen")
    
    # Return updated screen
    updated_screen = await repo.get_digital_screen(screen_id)
    return updated_screen


@router.delete("/{screen_id}")
async def delete_screen(
    screen_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a digital screen"""
    screen = await repo.get_digital_screen(screen_id)
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    # Role-based access check
    user_roles = current_user.get("roles", [])
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    user_has_global_access = any(role.get("company_id") == "global" for role in user_roles)
    
    if not user_is_admin and not user_has_global_access:
        user_company_ids = [role.get("company_id") for role in user_roles]
        if screen.get("company_id") not in user_company_ids:
            raise HTTPException(status_code=403, detail="Access denied to this screen")
    
    success = await repo.delete_digital_screen(screen_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete screen")
    
    return {"message": "Screen deleted successfully"}


# Content Overlay endpoints
@router.get("/{screen_id}/overlays", response_model=List[dict])
async def get_screen_overlays(
    screen_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all content overlays for a specific screen"""
    screen = await repo.get_digital_screen(screen_id)
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    # For now, return empty list as overlays are not implemented in repository
    # TODO: Implement overlay operations in repository
    overlays = []
    
    # Role-based filtering
    user_roles = current_user.get("roles", [])
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    
    if not user_is_admin:
        user_company_ids = [role.get("company_id") for role in user_roles]
        overlays = [o for o in overlays if o.get("company_id") in user_company_ids]
    
    return overlays


@router.post("/{screen_id}/overlays", response_model=dict)
async def create_overlay(
    screen_id: str,
    overlay_data: ContentOverlayCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new content overlay for a screen"""
    screen = await repo.get_digital_screen(screen_id)
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    # TODO: Implement overlay creation in repository
    raise HTTPException(status_code=501, detail="Overlay operations not yet implemented")


# Digital Twin endpoints
@router.get("/{screen_id}/digital-twin", response_model=dict)
async def get_digital_twin(
    screen_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get digital twin for a screen"""
    screen = await repo.get_digital_screen(screen_id)
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    # TODO: Implement digital twin operations in repository
    raise HTTPException(status_code=501, detail="Digital twin operations not yet implemented")


@router.post("/{screen_id}/digital-twin", response_model=dict)
async def create_digital_twin(
    screen_id: str,
    twin_data: DigitalTwinCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a digital twin for a screen"""
    screen = await repo.get_digital_screen(screen_id)
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    # TODO: Implement digital twin creation in repository
    raise HTTPException(status_code=501, detail="Digital twin operations not yet implemented")


# Layout Template endpoints
@router.get("/templates", response_model=List[dict])
async def get_layout_templates(
    is_public: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get layout templates"""
    # TODO: Implement layout template operations in repository
    templates = []
    
    # Filter by public/private
    if is_public is not None:
        templates = [t for t in templates if t.get("is_public") == is_public]
    
    # Role-based filtering - show public templates and own company templates
    user_roles = current_user.get("roles", [])
    user_company_ids = [role.get("company_id") for role in user_roles]
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    
    if not user_is_admin:
        templates = [
            t for t in templates 
            if t.get("is_public") or t.get("company_id") in user_company_ids
        ]
    
    return templates


@router.post("/templates", response_model=dict)
async def create_layout_template(
    template_data: LayoutTemplateCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new layout template"""
    # TODO: Implement layout template creation in repository
    raise HTTPException(status_code=501, detail="Layout template operations not yet implemented")