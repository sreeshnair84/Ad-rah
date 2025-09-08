from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from app.models import (
    ContentCategory, ContentCategoryCreate, ContentCategoryUpdate,
    ContentTag, ContentTagCreate, ContentTagUpdate,
    HostPreference, HostPreferenceCreate, HostPreferenceUpdate
)
from app.repo import repo
from app.auth_service import get_current_user, require_roles
import uuid

router = APIRouter(prefix="/categories", tags=["categories"])

# Content Category endpoints
@router.post("/", response_model=dict)
async def create_category(
    category: ContentCategoryCreate,
    current_user = Depends(require_roles("ADMIN"))
):
    """Create a new content category"""
    category_obj = ContentCategory(**category.model_dump())
    category_obj.id = str(uuid.uuid4())
    return await repo.save_content_category(category_obj)

@router.get("/", response_model=List[dict])
async def list_categories(
    active_only: bool = True,
    current_user = Depends(get_current_user)
):
    """List all content categories"""
    return await repo.list_content_categories(active_only=active_only)

@router.get("/{category_id}", response_model=dict)
async def get_category(
    category_id: str,
    current_user = Depends(get_current_user)
):
    """Get a specific category"""
    category = await repo.get_content_category(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

@router.put("/{category_id}", response_model=dict)
async def update_category(
    category_id: str,
    category_update: ContentCategoryUpdate,
    current_user = Depends(require_roles("ADMIN"))
):
    """Update a content category"""
    existing = await repo.get_content_category(category_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Category not found")
    
    updates = category_update.model_dump(exclude_none=True)
    success = await repo.update_content_category(category_id, updates)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update category")
    
    return await repo.get_content_category(category_id)

@router.delete("/{category_id}")
async def delete_category(
    category_id: str,
    current_user = Depends(require_roles("ADMIN"))
):
    """Delete a content category"""
    success = await repo.delete_content_category(category_id)
    if not success:
        raise HTTPException(status_code=404, detail="Category not found")
    return {"message": "Category deleted successfully"}

# Content Tag endpoints
@router.post("/tags", response_model=dict)
async def create_tag(
    tag: ContentTagCreate,
    current_user = Depends(require_roles("ADMIN", "ADVERTISER"))
):
    """Create a new content tag"""
    tag_obj = ContentTag(**tag.model_dump())
    tag_obj.id = str(uuid.uuid4())
    return await repo.save_content_tag(tag_obj)

@router.get("/tags", response_model=List[dict])
async def list_tags(
    active_only: bool = True,
    category_id: Optional[str] = None,
    current_user = Depends(get_current_user)
):
    """List all content tags"""
    return await repo.list_content_tags(active_only=active_only, category_id=category_id)

@router.get("/tags/{tag_id}", response_model=dict)
async def get_tag(
    tag_id: str,
    current_user = Depends(get_current_user)
):
    """Get a specific tag"""
    tag = await repo.get_content_tag(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag

@router.put("/tags/{tag_id}", response_model=dict)
async def update_tag(
    tag_id: str,
    tag_update: ContentTagUpdate,
    current_user = Depends(require_roles("ADMIN", "ADVERTISER"))
):
    """Update a content tag"""
    existing = await repo.get_content_tag(tag_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Tag not found")
    
    updates = tag_update.model_dump(exclude_none=True)
    success = await repo.update_content_tag(tag_id, updates)
    if not success:
        raise HTTPException(status_code=400, detail="Failed to update tag")
    
    return await repo.get_content_tag(tag_id)

@router.delete("/tags/{tag_id}")
async def delete_tag(
    tag_id: str,
    current_user = Depends(require_roles("ADMIN", "ADVERTISER"))
):
    """Delete a content tag"""
    success = await repo.delete_content_tag(tag_id)
    if not success:
        raise HTTPException(status_code=404, detail="Tag not found")
    return {"message": "Tag deleted successfully"}

# Host Preference endpoints
@router.post("/preferences", response_model=dict)
async def create_host_preference(
    preference: HostPreferenceCreate,
    current_user = Depends(require_roles("ADMIN", "HOST"))
):
    """Create host content preferences"""
    preference_obj = HostPreference(**preference.model_dump())
    preference_obj.id = str(uuid.uuid4())
    return await repo.save_host_preference(preference_obj)

@router.get("/preferences/{company_id}", response_model=List[dict])
async def get_host_preferences(
    company_id: str,
    screen_id: Optional[str] = None,
    current_user = Depends(require_roles("ADMIN", "HOST"))
):
    """Get host preferences for a company"""
    return await repo.get_host_preferences(company_id, screen_id)

@router.put("/preferences/{preference_id}", response_model=dict)
async def update_host_preference(
    preference_id: str,
    preference_update: HostPreferenceUpdate,
    current_user = Depends(require_roles("ADMIN", "HOST"))
):
    """Update host preferences"""
    updates = preference_update.model_dump(exclude_none=True)
    success = await repo.update_host_preference(preference_id, updates)
    if not success:
        raise HTTPException(status_code=404, detail="Preference not found")
    
    # Return updated preference (would need to implement get_host_preference by ID)
    return {"message": "Preference updated successfully"}

@router.delete("/preferences/{preference_id}")
async def delete_host_preference(
    preference_id: str,
    current_user = Depends(require_roles("ADMIN", "HOST"))
):
    """Delete host preferences"""
    success = await repo.delete_host_preference(preference_id)
    if not success:
        raise HTTPException(status_code=404, detail="Preference not found")
    return {"message": "Preference deleted successfully"}