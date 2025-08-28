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

router = APIRouter(prefix="/screens", tags=["screens"])

# In-memory stores (replace with database in production)
screen_store: Dict[str, dict] = {}
overlay_store: Dict[str, dict] = {}
digital_twin_store: Dict[str, dict] = {}
layout_template_store: Dict[str, dict] = {}


# Initialize with mock data
def initialize_mock_data():
    """Initialize mock data for screens and overlays"""
    
    # Mock digital screens
    mock_screens = [
        {
            "id": "screen_001",
            "name": "Main Lobby Display",
            "description": "Primary display in building lobby",
            "company_id": "company_001",
            "location": "Building A - Main Lobby",
            "resolution_width": 1920,
            "resolution_height": 1080,
            "orientation": "landscape",
            "status": "active",
            "ip_address": "192.168.1.101",
            "mac_address": "00:1B:44:11:3A:B7",
            "last_seen": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": "screen_002", 
            "name": "Cafe Menu Board",
            "description": "Digital menu display in cafe area",
            "company_id": "company_001",
            "location": "Building A - Cafe",
            "resolution_width": 1080,
            "resolution_height": 1920,
            "orientation": "portrait",
            "status": "active",
            "ip_address": "192.168.1.102",
            "mac_address": "00:1B:44:11:3A:B8",
            "last_seen": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": "screen_003",
            "name": "Conference Room Display",
            "description": "Meeting room information display",
            "company_id": "company_002", 
            "location": "Building B - Conference Room 1",
            "resolution_width": 1920,
            "resolution_height": 1080,
            "orientation": "landscape",
            "status": "maintenance",
            "ip_address": "192.168.1.103",
            "mac_address": "00:1B:44:11:3A:B9",
            "last_seen": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    ]
    
    for screen in mock_screens:
        screen_store[screen["id"]] = screen
    
    # Mock content overlays
    mock_overlays = [
        {
            "id": "overlay_001",
            "content_id": "content_001",
            "screen_id": "screen_001", 
            "company_id": "company_001",
            "name": "Welcome Banner",
            "position_x": 50,
            "position_y": 50,
            "width": 800,
            "height": 200,
            "z_index": 1,
            "opacity": 1.0,
            "rotation": 0.0,
            "start_time": None,
            "end_time": None,
            "status": "active",
            "created_by": "user_001",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": "overlay_002",
            "content_id": "content_002", 
            "screen_id": "screen_001",
            "company_id": "company_001",
            "name": "Event Announcement",
            "position_x": 100,
            "position_y": 300,
            "width": 600,
            "height": 400,
            "z_index": 2,
            "opacity": 0.9,
            "rotation": 0.0,
            "start_time": datetime.utcnow().isoformat(),
            "end_time": None,
            "status": "scheduled",
            "created_by": "user_001",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    ]
    
    for overlay in mock_overlays:
        overlay_store[overlay["id"]] = overlay
    
    # Mock digital twins
    mock_twins = [
        {
            "id": "twin_001",
            "name": "Lobby Display Twin",
            "screen_id": "screen_001",
            "company_id": "company_001", 
            "description": "Virtual testing environment for lobby display",
            "is_live_mirror": False,
            "test_content_ids": ["content_001", "content_002"],
            "overlay_configs": ["overlay_001", "overlay_002"],
            "status": "stopped",
            "created_by": "user_001",
            "last_accessed": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    ]
    
    for twin in mock_twins:
        digital_twin_store[twin["id"]] = twin
    
    # Mock layout templates
    mock_templates = [
        {
            "id": "template_001",
            "name": "Corporate Welcome Layout",
            "description": "Standard corporate welcome screen layout",
            "company_id": "company_001",
            "template_data": {
                "background_color": "#f8f9fa",
                "zones": [
                    {"type": "header", "height": 200, "background": "#007bff"},
                    {"type": "content", "height": 680, "background": "#ffffff"}, 
                    {"type": "footer", "height": 200, "background": "#6c757d"}
                ]
            },
            "is_public": True,
            "usage_count": 5,
            "created_by": "user_001",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    ]
    
    for template in mock_templates:
        layout_template_store[template["id"]] = template


# Initialize mock data on module load
initialize_mock_data()


# Digital Screen endpoints
@router.get("", response_model=List[dict])
async def get_screens(
    company_id: Optional[str] = None,
    status: Optional[ScreenStatus] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all digital screens with optional filtering"""
    screens = list(screen_store.values())
    
    # Filter by company if specified
    if company_id:
        screens = [s for s in screens if s["company_id"] == company_id]
    
    # Filter by status if specified  
    if status:
        screens = [s for s in screens if s["status"] == status.value]
    
    # Role-based filtering - non-admins only see their company's screens
    user_roles = current_user.get("roles", [])
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    
    if not user_is_admin:
        user_company_ids = [role.get("company_id") for role in user_roles]
        screens = [s for s in screens if s["company_id"] in user_company_ids]
    
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
        "status": "active",
        "last_seen": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    })
    
    screen_store[screen_id] = screen
    return screen


@router.get("/{screen_id}", response_model=dict)
async def get_screen(
    screen_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific digital screen"""
    if screen_id not in screen_store:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    screen = screen_store[screen_id]
    
    # Role-based access check
    user_roles = current_user.get("roles", [])
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    
    if not user_is_admin:
        user_company_ids = [role.get("company_id") for role in user_roles] 
        if screen["company_id"] not in user_company_ids:
            raise HTTPException(status_code=403, detail="Access denied to this screen")
    
    return screen


@router.put("/{screen_id}", response_model=dict)
async def update_screen(
    screen_id: str,
    screen_data: ScreenUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a digital screen"""
    if screen_id not in screen_store:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    screen = screen_store[screen_id]
    
    # Role-based access check
    user_roles = current_user.get("roles", [])
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    
    if not user_is_admin:
        user_company_ids = [role.get("company_id") for role in user_roles]
        if screen["company_id"] not in user_company_ids:
            raise HTTPException(status_code=403, detail="Access denied to this screen")
    
    # Update fields
    update_data = screen_data.dict(exclude_unset=True)
    screen.update(update_data)
    screen["updated_at"] = datetime.utcnow().isoformat()
    
    screen_store[screen_id] = screen
    return screen


@router.delete("/{screen_id}")
async def delete_screen(
    screen_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a digital screen"""
    if screen_id not in screen_store:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    screen = screen_store[screen_id]
    
    # Role-based access check
    user_roles = current_user.get("roles", [])
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    
    if not user_is_admin:
        user_company_ids = [role.get("company_id") for role in user_roles]
        if screen["company_id"] not in user_company_ids:
            raise HTTPException(status_code=403, detail="Access denied to this screen")
    
    del screen_store[screen_id]
    return {"message": "Screen deleted successfully"}


# Content Overlay endpoints
@router.get("/{screen_id}/overlays", response_model=List[dict])
async def get_screen_overlays(
    screen_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all content overlays for a specific screen"""
    if screen_id not in screen_store:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    overlays = [o for o in overlay_store.values() if o["screen_id"] == screen_id]
    
    # Role-based filtering
    user_roles = current_user.get("roles", [])
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    
    if not user_is_admin:
        user_company_ids = [role.get("company_id") for role in user_roles]
        overlays = [o for o in overlays if o["company_id"] in user_company_ids]
    
    return overlays


@router.post("/{screen_id}/overlays", response_model=dict)
async def create_overlay(
    screen_id: str,
    overlay_data: ContentOverlayCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new content overlay for a screen"""
    if screen_id not in screen_store:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    overlay_id = str(uuid.uuid4())
    overlay = overlay_data.dict()
    overlay.update({
        "id": overlay_id,
        "screen_id": screen_id,
        "created_by": current_user["id"],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    })
    
    overlay_store[overlay_id] = overlay
    return overlay


# Digital Twin endpoints
@router.get("/{screen_id}/digital-twin", response_model=dict)
async def get_digital_twin(
    screen_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get digital twin for a screen"""
    twin = next((t for t in digital_twin_store.values() if t["screen_id"] == screen_id), None)
    if not twin:
        raise HTTPException(status_code=404, detail="Digital twin not found")
    
    return twin


@router.post("/{screen_id}/digital-twin", response_model=dict)
async def create_digital_twin(
    screen_id: str,
    twin_data: DigitalTwinCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a digital twin for a screen"""
    if screen_id not in screen_store:
        raise HTTPException(status_code=404, detail="Screen not found")
    
    twin_id = str(uuid.uuid4())
    twin = twin_data.dict()
    twin.update({
        "id": twin_id,
        "screen_id": screen_id,
        "created_by": current_user["id"],
        "last_accessed": None,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    })
    
    digital_twin_store[twin_id] = twin
    return twin


# Layout Template endpoints
@router.get("/templates", response_model=List[dict])
async def get_layout_templates(
    is_public: Optional[bool] = None,
    current_user: dict = Depends(get_current_user)
):
    """Get layout templates"""
    templates = list(layout_template_store.values())
    
    # Filter by public/private
    if is_public is not None:
        templates = [t for t in templates if t["is_public"] == is_public]
    
    # Role-based filtering - show public templates and own company templates
    user_roles = current_user.get("roles", [])
    user_company_ids = [role.get("company_id") for role in user_roles]
    user_is_admin = any(role.get("role") == "ADMIN" for role in user_roles)
    
    if not user_is_admin:
        templates = [
            t for t in templates 
            if t["is_public"] or t["company_id"] in user_company_ids
        ]
    
    return templates


@router.post("/templates", response_model=dict)
async def create_layout_template(
    template_data: LayoutTemplateCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new layout template"""
    template_id = str(uuid.uuid4())
    template = template_data.dict()
    template.update({
        "id": template_id,
        "usage_count": 0,
        "created_by": current_user["id"],
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat()
    })
    
    layout_template_store[template_id] = template
    return template