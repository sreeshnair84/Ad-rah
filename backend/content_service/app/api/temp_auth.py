"""
Temporary Auth Router for Debugging
===================================

This router provides a simple auth endpoint for debugging login issues.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import logging

router = APIRouter(tags=["Temporary Auth"])
logger = logging.getLogger(__name__)


class TempLoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
async def temp_login(request: TempLoginRequest):
    """Temporary login endpoint for debugging"""
    try:
        from app.repo import repo
        from app.auth import verify_password, create_access_token
        
        # Get user by email from repo
        user_data = await repo.get_user_by_email(request.email.lower())
        if not user_data:
            logger.warning(f"User not found: {request.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check password
        if not verify_password(request.password, user_data.get("hashed_password", "")):
            logger.warning(f"Invalid password for user: {request.email}")
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Check if user is active
        if user_data.get("status") != "active":
            logger.warning(f"User account not active: {request.email}")
            raise HTTPException(status_code=401, detail="Account is not active")
        
        # Get user roles
        user_roles = await repo.get_user_roles(user_data.get("id") or str(user_data.get("_id")))
        
        # Create token data
        token_data = {
            "sub": user_data.get("id") or str(user_data.get("_id")),
            "email": user_data.get("email"),
            "user_type": user_data.get("user_type", "COMPANY_USER")
        }
        
        access_token = create_access_token(token_data)
        
        # Prepare user data for response
        user_response = {
            "id": user_data.get("id") or str(user_data.get("_id")),
            "email": user_data.get("email"),
            "name": user_data.get("name"),
            "user_type": user_data.get("user_type", "COMPANY_USER"),
            "status": user_data.get("status"),
            "roles": user_roles,
            "permissions": [],  # Will be populated by frontend
            "company_role": None,  # Will be determined from roles
        }
        
        # Determine company role from user roles
        if user_roles:
            for role in user_roles:
                role_id = role.get("role_id")
                if role_id:
                    try:
                        role_data = await repo.get_role(str(role_id))
                        if role_data:
                            if role_data.get("name") == "Super Administrator":
                                user_response["company_role"] = "ADMIN"
                                user_response["user_type"] = "SUPER_USER"
                            elif role_data.get("name") == "Administrator":
                                user_response["company_role"] = "ADMIN"
                            elif role_data.get("name") == "Editor":
                                user_response["company_role"] = "EDITOR"
                            elif role_data.get("name") == "Viewer":
                                user_response["company_role"] = "VIEWER"
                            break
                    except Exception as e:
                        logger.warning(f"Failed to get role data: {e}")
        
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": user_response
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Temp login failed: {e}")
        raise HTTPException(status_code=500, detail="Login failed")


@router.get("/test-repo")
async def test_repo():
    """Test repo access"""
    try:
        from app.repo import repo
        
        # Test user access
        users = await repo.list_users()
        user_count = len(users) if users else 0
        
        # Test specific user lookup
        admin_user = await repo.get_user_by_email("admin@adara.com")
        admin_found = admin_user is not None
        
        return {
            "repo_type": type(repo).__name__,
            "user_count": user_count,
            "admin_found": admin_found,
            "admin_email": admin_user.get("email") if admin_user else None,
            "admin_status": admin_user.get("status") if admin_user else None,
            "admin_user_type": admin_user.get("user_type") if admin_user else None,
            "has_password": bool(admin_user.get("hashed_password")) if admin_user else False
        }
        
    except Exception as e:
        logger.error(f"Repo test failed: {e}")
        return {"error": str(e)}
