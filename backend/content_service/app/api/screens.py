from fastapi import APIRouter, Depends, HTTPException, Form
from typing import List, Dict, Optional
from datetime import datetime
import uuid

from app.models import (
    DigitalScreen, ScreenCreate, ScreenUpdate, ScreenStatus,
    ContentOverlay, ContentOverlayCreate, ContentOverlayUpdate,
    DigitalTwin, DigitalTwinCreate, DigitalTwinUpdate,
    LayoutTemplate, LayoutTemplateCreate, LayoutTemplateUpdate
)
from app.auth import get_current_user, get_user_company_context, get_current_user_with_super_admin_bypass
from app.repo import repo
from app.utils.serialization import safe_json_response

router = APIRouter(tags=["screens"])


# Mock data initialization is handled by startup lifecycle in main.py


# Layout Template endpoints
@router.get("/templates", response_model=List[dict])
async def get_layout_templates(
    is_public: Optional[bool] = None,
    current_user: dict = Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Get layout templates with company-scoped access"""
    is_platform_admin = company_context["is_platform_admin"]
    accessible_companies = company_context["accessible_companies"]
    accessible_company_ids = {c.get("id") for c in accessible_companies}
    
    # If platform admin, get all templates, otherwise filter by company access
    if is_platform_admin:
        templates = await repo.list_layout_templates(is_public=is_public)
    else:
        # Get templates for user's companies plus public templates
        all_templates = []
        for company_id in accessible_company_ids:
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
    current_user: dict = Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Create a new layout template"""
    # Validate user has access to the specified company
    is_platform_admin = company_context["is_platform_admin"]
    accessible_companies = company_context["accessible_companies"]
    accessible_company_ids = {c.get("id") for c in accessible_companies}
    
    if not is_platform_admin and template_data.company_id not in accessible_company_ids:
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
    current_user: dict = Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Get a specific layout template"""
    template = await repo.get_layout_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Layout template not found")
    
    # Check access permissions
    is_platform_admin = company_context["is_platform_admin"]
    accessible_companies = company_context["accessible_companies"]
    accessible_company_ids = {c.get("id") for c in accessible_companies}
    
    if not is_platform_admin:
        if not template.get("is_public") and template.get("company_id") not in accessible_company_ids:
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
    current_user: dict = Depends(get_current_user_with_super_admin_bypass),
    company_context=Depends(get_user_company_context)
):
    """Get all digital screens with company-scoped filtering"""
    # SUPER_USER bypass
    if current_user.get("user_type") == "SUPER_USER":
        screens = await repo.list_digital_screens(company_id)
        if status:
            screens = [s for s in screens if s.get("status") == status.value]
        return screens
    
    is_platform_admin = company_context["is_platform_admin"]
    accessible_companies = company_context["accessible_companies"]
    accessible_company_ids = {c.get("id") for c in accessible_companies}
    
    # Get screens with optional company filtering
    screens = await repo.list_digital_screens(company_id)
    
    # Filter by status if specified  
    if status:
        screens = [s for s in screens if s.get("status") == status.value]
    
    # Company-based filtering - non-platform admins only see their company's screens
    if not is_platform_admin:
        screens = [s for s in screens if s.get("company_id") in accessible_company_ids]
    
    return screens


@router.post("", response_model=dict)
async def create_screen(
    screen_data: ScreenCreate,
    current_user: dict = Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Create a new digital screen"""
    
    # Check if user can create screens for this company
    is_platform_admin = company_context["is_platform_admin"]
    accessible_companies = company_context["accessible_companies"]
    accessible_company_ids = {c.get("id") for c in accessible_companies}
    
    if not is_platform_admin and screen_data.company_id not in accessible_company_ids:
        raise HTTPException(status_code=403, detail="Access denied to create screens for this company")
    
    # Check if user has admin or editor role in the company
    current_user_id = current_user.get("id")
    user_can_create = is_platform_admin
    
    if not is_platform_admin:
        user_role = await repo.get_user_role_in_company(current_user_id, screen_data.company_id)
        if user_role:
            role_details = user_role.get("role_details", {})
            company_role_type = role_details.get("company_role_type")
            if company_role_type in ["COMPANY_ADMIN", "EDITOR"]:
                user_can_create = True
    
    if not user_can_create:
        raise HTTPException(
            status_code=403,
            detail="Access denied: Only company admins and editors can create screens"
        )
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
    current_user: dict = Depends(get_current_user_with_super_admin_bypass),
    company_context=Depends(get_user_company_context)
):
    """Get a specific digital screen"""
    # SUPER_USER bypass
    if current_user.get("user_type") == "SUPER_USER":
        screen = await repo.get_digital_screen(screen_id)
        if not screen:
            raise HTTPException(status_code=404, detail="Screen not found")
        return screen
    
    screen = await repo.get_digital_screen(screen_id)
    if not screen:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    # Company-based access check
    is_platform_admin = company_context["is_platform_admin"]
    accessible_companies = company_context["accessible_companies"]
    accessible_company_ids = {c.get("id") for c in accessible_companies}
    
    if not is_platform_admin:
        if screen.get("company_id") not in accessible_company_ids:
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
    """Get content overlays for a specific screen"""
    try:
        # Check if screen exists and user has access
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
        
        # Get all overlays for this screen
        overlays = await repo.list_content_overlays(screen_id=screen_id)
        
        # Enhance with content information
        enhanced_overlays = []
        for overlay in overlays:
            content_id = overlay.get("content_id")
            content = None
            if content_id:
                content = await repo.get_content_meta(content_id)
                if not content:
                    # Try regular content collection
                    content = await repo.get(content_id)
            
            enhanced_overlay = {
                **overlay,
                "content": content
            }
            enhanced_overlays.append(enhanced_overlay)
        
        return safe_json_response(enhanced_overlays)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get screen overlays: {e}")


@router.post("/{screen_id}/overlays", response_model=dict)
async def create_screen_overlay(
    screen_id: str,
    overlay_data: ContentOverlayCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new content overlay for a screen"""
    try:
        # Check if screen exists and user has access
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
        
        # Verify content exists
        content = await repo.get_content_meta(overlay_data.content_id)
        if not content:
            content = await repo.get(overlay_data.content_id)
        if not content:
            raise HTTPException(status_code=404, detail="Content not found")
        
        # Create overlay
        overlay_id = str(uuid.uuid4())
        overlay_dict = overlay_data.dict()
        overlay_dict.update({
            "id": overlay_id,
            "screen_id": screen_id,
            "created_by": current_user.get("id"),
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        })
        
        # Save overlay
        result = await repo.save_content_overlay(overlay_dict)
        
        return safe_json_response(result)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create screen overlay: {e}")


@router.put("/{screen_id}/overlays/{overlay_id}", response_model=dict)
async def update_screen_overlay(
    screen_id: str,
    overlay_id: str,
    overlay_data: ContentOverlayUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update an existing content overlay"""
    try:
        # Check if screen exists
        screen = await repo.get_digital_screen(screen_id)
        if not screen:
            raise HTTPException(status_code=404, detail="Screen not found")
        
        # Check if overlay exists
        overlay = await repo.get_content_overlay(overlay_id)
        if not overlay:
            raise HTTPException(status_code=404, detail="Overlay not found")
        
        if overlay.get("screen_id") != screen_id:
            raise HTTPException(status_code=400, detail="Overlay does not belong to this screen")
        
        # Role-based access check
        user_roles = current_user.get("roles", [])
        user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
        user_has_global_access = any(role.get("company_id") == "global" for role in user_roles)
        
        if not user_is_admin and not user_has_global_access:
            user_company_ids = [role.get("company_id") for role in user_roles]
            if overlay.get("company_id") not in user_company_ids:
                raise HTTPException(status_code=403, detail="Access denied to this overlay")
        
        # Update overlay
        update_data = overlay_data.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.utcnow()
        
        success = await repo.update_content_overlay(overlay_id, update_data)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update overlay")
        
        # Return updated overlay
        updated_overlay = await repo.get_content_overlay(overlay_id)
        return safe_json_response(updated_overlay)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update screen overlay: {e}")


@router.delete("/{screen_id}/overlays/{overlay_id}")
async def delete_screen_overlay(
    screen_id: str,
    overlay_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a content overlay"""
    try:
        # Check if screen exists
        screen = await repo.get_digital_screen(screen_id)
        if not screen:
            raise HTTPException(status_code=404, detail="Screen not found")
        
        # Check if overlay exists
        overlay = await repo.get_content_overlay(overlay_id)
        if not overlay:
            raise HTTPException(status_code=404, detail="Overlay not found")
        
        if overlay.get("screen_id") != screen_id:
            raise HTTPException(status_code=400, detail="Overlay does not belong to this screen")
        
        # Role-based access check
        user_roles = current_user.get("roles", [])
        user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
        user_has_global_access = any(role.get("company_id") == "global" for role in user_roles)
        
        if not user_is_admin and not user_has_global_access:
            user_company_ids = [role.get("company_id") for role in user_roles]
            if overlay.get("company_id") not in user_company_ids:
                raise HTTPException(status_code=403, detail="Access denied to this overlay")
        
        # Delete overlay
        success = await repo.delete_content_overlay(overlay_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete overlay")
        
        return {"message": "Overlay deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete screen overlay: {e}")