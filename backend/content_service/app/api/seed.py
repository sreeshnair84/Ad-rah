"""
API endpoint for seeding data within the server context
This ensures data persists in the in-memory repository for testing
"""

from fastapi import APIRouter, HTTPException, Depends
from app.api.auth import get_current_user
import sys
import os

router = APIRouter(prefix="/seed", tags=["seed"])

@router.post("/data")
async def seed_data_endpoint(current_user=Depends(get_current_user)):
    """Seed data within the server context for testing"""
    try:
        # Import the seeding functions
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
        from seed_data import (
            seed_sample_categories, seed_sample_tags, seed_companies, 
            seed_roles, seed_role_permissions, seed_users, seed_user_roles,
            seed_devices, seed_registration_keys, seed_default_content
        )
        
        # Run the seeding process
        print("🚀 Starting in-server database seeding...")
        
        # Seed sample categories and tags first
        categories = await seed_sample_categories()
        tags = await seed_sample_tags(categories)
        
        # Seed minimal demo companies (for development only)
        companies = await seed_companies()
        
        # Seed roles for admin and any demo companies
        roles = await seed_roles()
        await seed_role_permissions()
        
        # Seed only essential users
        users = await seed_users()
        await seed_user_roles()
        
        # Seed devices for HOST companies (for authentication testing)
        if companies:
            devices = await seed_devices()
        else:
            devices = []
        
        # Only create registration keys for demo companies
        if companies:
            await seed_registration_keys()

        # Seed default content that ships with the system
        await seed_default_content()
        
        return {
            "status": "success",
            "message": "Database seeded successfully within server context",
            "summary": {
                "categories": len(categories) if categories else 0,
                "tags": len(tags) if tags else 0,
                "companies": len(companies) if companies else 0,
                "roles": len(roles) if roles else 0,
                "users": len(users) if users else 0,
                "devices": len(devices) if devices else 0
            }
        }
        
    except Exception as e:
        print(f"❌ Seeding failed: {e}")
        raise HTTPException(status_code=500, detail=f"Seeding failed: {str(e)}")


@router.get("/status")
async def get_seed_status():
    """Check the current state of seeded data"""
    try:
        from app.repo import repo
        
        # Get counts of different data types
        users = await repo.list_users()
        companies = await repo.list_companies()
        
        # Get roles if method exists
        try:
            roles = await repo.list_roles_by_group("ADMIN")
        except:
            roles = []
        
        return {
            "status": "success",
            "repository_type": type(repo).__name__,
            "data_counts": {
                "users": len(users),
                "companies": len(companies),
                "roles": len(roles)
            },
            "users": [{"email": u.get("email"), "user_type": u.get("user_type")} for u in users[:10]]  # First 10 users
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }
