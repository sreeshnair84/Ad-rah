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


# Layout Template endpoints
@router.get("/templates", response_model=List[dict])
async def get_layout_templates(
    is_public: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get layout templates"""
    # Get user company IDs for filtering
    user_roles = current_user.get("roles", [])
    user_company_ids = [role.get("company_id") for role in user_roles]
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    
    # If admin, get all templates, otherwise filter by company access
    if user_is_admin:
        templates = await repo.list_layout_templates(is_public=is_public)
    else:
        # Get templates for user's companies plus public templates
        all_templates = []
        for company_id in user_company_ids:
            company_templates = await repo.list_layout_templates(company_id=company_id, is_public=is_public)
            all_templates.extend(company_templates)
        
        # Remove duplicates
        seen_ids = set()
        templates = []
        for template in all_templates:
            if template.get("id") not in seen_ids:
                seen_ids.add(template.get("id"))
                templates.append(template)
    
    return templates


@router.post("/templates", response_model=dict)
async def create_layout_template(
    template_data: LayoutTemplateCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new layout template"""
    # Validate user has access to the specified company
    user_roles = current_user.get("roles", [])
    user_company_ids = [role.get("company_id") for role in user_roles]
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    
    if not user_is_admin and template_data.company_id not in user_company_ids:
        raise HTTPException(status_code=403, detail="Access denied to create templates for this company")
    
    # Create template data
    template_dict = template_data.dict()
    template_dict.update({
        "id": str(uuid.uuid4()),
        "created_by": current_user.get("id"),
        "usage_count": 0,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    })
    
    # Save to repository
    result = await repo.save_layout_template(template_dict)
    return result


@router.get("/templates/{template_id}", response_model=dict)
async def get_layout_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific layout template"""
    template = await repo.get_layout_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Layout template not found")
    
    # Check access permissions
    user_roles = current_user.get("roles", [])
    user_company_ids = [role.get("company_id") for role in user_roles]
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    
    if not user_is_admin:
        if not template.get("is_public") and template.get("company_id") not in user_company_ids:
            raise HTTPException(status_code=403, detail="Access denied to this template")
    
    return template


@router.put("/templates/{template_id}", response_model=dict)
async def update_layout_template(
    template_id: str,
    template_data: LayoutTemplateUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a layout template"""
    template = await repo.get_layout_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Layout template not found")
    
    # Check access permissions
    user_roles = current_user.get("roles", [])
    user_company_ids = [role.get("company_id") for role in user_roles]
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    
    if not user_is_admin and template.get("company_id") not in user_company_ids:
        raise HTTPException(status_code=403, detail="Access denied to modify this template")
    
    # Update template
    update_data = template_data.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    success = await repo.update_layout_template(template_id, update_data)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update template")
    
    # Return updated template
    updated_template = await repo.get_layout_template(template_id)
    return updated_template


@router.delete("/templates/{template_id}")
async def delete_layout_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a layout template"""
    template = await repo.get_layout_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Layout template not found")
    
    # Check access permissions
    user_roles = current_user.get("roles", [])
    user_company_ids = [role.get("company_id") for role in user_roles]
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    
    if not user_is_admin and template.get("company_id") not in user_company_ids:
        raise HTTPException(status_code=403, detail="Access denied to delete this template")
    
    success = await repo.delete_layout_template(template_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to delete template")
    
    return {"message": "Layout template deleted successfully"}


@router.post("/templates/{template_id}/use")
async def use_layout_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Increment usage count when template is used"""
    template = await repo.get_layout_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Layout template not found")
    
    # Check access permissions
    user_roles = current_user.get("roles", [])
    user_company_ids = [role.get("company_id") for role in user_roles]
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    
    if not user_is_admin:
        if not template.get("is_public") and template.get("company_id") not in user_company_ids:
            raise HTTPException(status_code=403, detail="Access denied to use this template")
    
    # Increment usage count
    success = await repo.increment_template_usage(template_id)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update template usage")
    
    return {"message": "Template usage recorded"}


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