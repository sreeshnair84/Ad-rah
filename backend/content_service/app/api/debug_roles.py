"""
Debug Roles API Router
=====================

This router provides debugging endpoints for roles and permissions.
It helps with troubleshooting RBAC issues during development.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Dict, Any
import logging

router = APIRouter(prefix="/debug", tags=["Debug - Roles"])
logger = logging.getLogger(__name__)


@router.get("/system/health")
async def rbac_system_health():
    """Check RBAC system health (debug only)"""
    try:
        return {
            "system_status": "healthy",
            "debug_info": "RBAC system operational",
            "note": "Full debug endpoints will be implemented after database integration is complete"
        }
        
    except Exception as e:
        logger.error(f"RBAC health check failed: {e}")
        return {
            "system_status": "unhealthy", 
            "error": str(e)
        }


@router.get("/users/list")
async def debug_list_users():
    """List all users for debugging (no auth required)"""
    try:
        # Try both old repo and new database service
        debug_info = {
            "old_repo_users": [],
            "new_db_users": [],
            "method_used": "unknown"
        }
        
        # Try old repo first
        try:
            from app.repo import repo
            old_users = await repo.list_users()
            debug_info["old_repo_users"] = [
                {
                    "email": user.get("email", "N/A"),
                    "user_type": user.get("user_type", "N/A"),
                    "status": user.get("status", "N/A"),
                    "has_password": bool(user.get("hashed_password"))
                }
                for user in old_users
            ]
            debug_info["method_used"] = "old_repo"
        except Exception as e:
            debug_info["old_repo_error"] = str(e)
        
        # Try new database service
        try:
            from app.database import get_db_service
            db = get_db_service()
            users_result = await db.list_records("users")
            if users_result.success:
                debug_info["new_db_users"] = [
                    {
                        "email": user.get("email", "N/A"),
                        "user_type": user.get("user_type", "N/A"),
                        "status": user.get("status", "N/A"),
                        "has_password": bool(user.get("hashed_password"))
                    }
                    for user in users_result.data
                ]
                debug_info["method_used"] = "new_db"
        except Exception as e:
            debug_info["new_db_error"] = str(e)
        
        return debug_info
        
    except Exception as e:
        logger.error(f"Debug users list failed: {e}")
        return {"error": str(e)}


@router.post("/auth/test-login")
async def debug_test_login():
    """Test login with common credentials (no auth required)"""
    try:
        from app.services.auth_service import AuthService
        auth_service = AuthService()
        
        # Test common admin credentials
        test_credentials = [
            {"email": "admin@adara.com", "password": "admin123"},
            {"email": "admin@adara.com", "password": "password"},
            {"email": "admin@adara.com", "password": "admin"},
            {"email": "admin@example.com", "password": "admin123"},
            {"email": "super@adara.com", "password": "admin123"},
        ]
        
        results = []
        for creds in test_credentials:
            try:
                result = await auth_service.login(creds["email"], creds["password"])
                if result.success:
                    user_data = result.data
                    results.append({
                        "credentials": creds,
                        "status": "SUCCESS",
                        "user_type": user_data.get("user", {}).get("user_type"),
                        "email": user_data.get("user", {}).get("email")
                    })
                    break  # Stop on first success
                else:
                    results.append({
                        "credentials": creds,
                        "status": "FAILED",
                        "error": result.error
                    })
            except Exception as e:
                results.append({
                    "credentials": creds,
                    "status": "ERROR",
                    "error": str(e)
                })
        
        return {
            "test_results": results,
            "note": "This endpoint tests common admin credentials"
        }
        
    except Exception as e:
        logger.error(f"Debug test login failed: {e}")
        return {"error": str(e)}