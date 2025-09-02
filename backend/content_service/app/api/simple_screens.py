"""
Simple Screens API for frontend consumption
"""
from typing import List
from fastapi import APIRouter, Depends

from ..api.auth import get_current_user
from ..utils.serialization import safe_json_response

router = APIRouter()

@router.get("/", response_model=List[dict])
async def list_screens(
    current_user: dict = Depends(get_current_user)
):
    """List available screens for content display"""
    # Mock screen data for now - in a real app this would come from a database
    screens = [
        {
            "id": "screen-lobby-1",
            "name": "Main Lobby Display",
            "location": "Lobby",
            "resolution": {"width": 1920, "height": 1080},
            "status": "online",
            "company_id": "demo-company",
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": "screen-reception-1", 
            "name": "Reception Display",
            "location": "Reception",
            "resolution": {"width": 1366, "height": 768},
            "status": "online",
            "company_id": "demo-company",
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": "screen-cafeteria-1",
            "name": "Cafeteria Display", 
            "location": "Cafeteria",
            "resolution": {"width": 1920, "height": 1080},
            "status": "online",
            "company_id": "demo-company", 
            "created_at": "2024-01-01T00:00:00Z"
        },
        {
            "id": "screen-mall-entrance",
            "name": "Mall Entrance Display",
            "location": "Main Entrance",
            "resolution": {"width": 2560, "height": 1440},
            "status": "online",
            "company_id": "demo-company",
            "created_at": "2024-01-01T00:00:00Z"
        }
    ]
    
    return safe_json_response(screens)

@router.get("/{screen_id}", response_model=dict)
async def get_screen(
    screen_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get details for a specific screen"""
    # Mock single screen lookup
    screens = {
        "screen-lobby-1": {
            "id": "screen-lobby-1",
            "name": "Main Lobby Display",
            "location": "Lobby",
            "resolution": {"width": 1920, "height": 1080},
            "status": "online",
            "company_id": "demo-company",
            "created_at": "2024-01-01T00:00:00Z"
        },
        "screen-reception-1": {
            "id": "screen-reception-1", 
            "name": "Reception Display",
            "location": "Reception",
            "resolution": {"width": 1366, "height": 768},
            "status": "online",
            "company_id": "demo-company",
            "created_at": "2024-01-01T00:00:00Z"
        },
        "screen-cafeteria-1": {
            "id": "screen-cafeteria-1",
            "name": "Cafeteria Display", 
            "location": "Cafeteria",
            "resolution": {"width": 1920, "height": 1080},
            "status": "online",
            "company_id": "demo-company", 
            "created_at": "2024-01-01T00:00:00Z"
        },
        "screen-mall-entrance": {
            "id": "screen-mall-entrance",
            "name": "Mall Entrance Display",
            "location": "Main Entrance",
            "resolution": {"width": 2560, "height": 1440},
            "status": "online",
            "company_id": "demo-company",
            "created_at": "2024-01-01T00:00:00Z"
        }
    }
    
    screen = screens.get(screen_id)
    if not screen:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Screen not found")
    
    return safe_json_response(screen)
