#!/usr/bin/env python3
"""Test seed endpoint without authentication"""
from fastapi import APIRouter, HTTPException
from app.repo import repo
from app.models import User
from app.auth_service import auth_service
import uuid
from datetime import datetime

router = APIRouter(prefix="/test-seed", tags=["test-seed"])

@router.post("/recreate-admin")
async def recreate_admin_user_for_testing():
    """Recreate admin user for testing (deletes existing first)"""
    try:
        # First, try to delete existing admin if any
        existing_admin = await repo.get_user_by_email("admin@adara.com")
        if existing_admin:
            # Clear the user from repo (if using in-memory)
            # This is a hack but necessary for testing
            if hasattr(repo, '_users'):
                users_to_remove = []
                for user_id, user_data in repo._users.items():
                    if user_data.get("email") == "admin@adara.com":
                        users_to_remove.append(user_id)
                for user_id in users_to_remove:
                    del repo._users[user_id]
        
        # Hash password
        hashed_password = auth_service.hash_password("admin")
        
        # Create admin user
        admin_user = User(
            id=str(uuid.uuid4()),
            email="admin@adara.com",
            first_name="Admin",
            last_name="User",
            hashed_password=hashed_password,
            user_type="SUPER_USER",
            is_active=True,
            email_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save user
        saved_user = await repo.save_user(admin_user)
        
        # Verify password immediately
        password_match = auth_service.verify_password("admin", hashed_password)
        
        return {
            "message": "Admin user recreated successfully",
            "email": "admin@adara.com", 
            "password": "admin",
            "user_type": "SUPER_USER",
            "id": saved_user.get("id"),
            "password_verification": password_match
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to recreate admin user: {str(e)}")

@router.post("/create-admin")
async def create_admin_user_for_testing():
    """Create admin user for testing (bypasses authentication)"""
    try:
        # Check if admin already exists
        existing_admin = await repo.get_user_by_email("admin@adara.com")
        if existing_admin:
            # Try to debug the existing admin user
            hashed_password = auth_service.hash_password("admin")
            existing_hash = existing_admin.get("hashed_password", "")
            password_match = auth_service.verify_password("admin", existing_hash)
            
            return {
                "message": "Admin user already exists", 
                "email": "admin@adara.com",
                "debug_info": {
                    "existing_user_type": existing_admin.get("user_type"),
                    "existing_is_active": existing_admin.get("is_active"),
                    "password_verification": password_match,
                    "new_hash_matches": existing_hash == hashed_password,
                    "existing_id": existing_admin.get("id")
                }
            }
        
        # Hash password
        hashed_password = auth_service.hash_password("admin")
        
        # Create admin user
        admin_user = User(
            id=str(uuid.uuid4()),
            email="admin@adara.com",
            first_name="Admin",
            last_name="User",
            hashed_password=hashed_password,
            user_type="SUPER_USER",
            is_active=True,
            email_verified=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        # Save user
        saved_user = await repo.save_user(admin_user)
        
        return {
            "message": "Admin user created successfully",
            "email": "admin@adara.com", 
            "password": "admin",
            "user_type": "SUPER_USER",
            "id": saved_user.get("id")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create admin user: {str(e)}")

@router.get("/test-login")
async def test_login_endpoint():
    """Test login without creating user first"""
    try:
        # Try to authenticate the admin user
        from app.rbac_models import LoginRequest
        
        login_request = LoginRequest(email="admin@adara.com", password="admin")
        
        # Try login
        response = await auth_service.login(login_request)
        
        return {
            "message": "Login successful",
            "access_token": response.access_token[:20] + "...",  # Only show first 20 chars
            "user_type": response.user.user_type,
            "email": response.user.email
        }
    except Exception as e:
        return {
            "message": "Login failed",
            "error": str(e),
            "suggestion": "Try POST /api/test-seed/create-admin first"
        }