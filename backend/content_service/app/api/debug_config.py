#!/usr/bin/env python3
"""
Debug endpoint to check environment configuration
"""

from fastapi import APIRouter
from app.config import settings
import os

router = APIRouter()

@router.get("/debug/config")
async def debug_config():
    """Debug endpoint to check configuration"""
    
    # Check environment variables
    env_secret = os.getenv("SECRET_KEY", "NOT_SET")
    env_jwt_secret = os.getenv("JWT_SECRET_KEY", "NOT_SET")
    
    # Check settings object
    settings_secret = getattr(settings, "SECRET_KEY", "NOT_SET")
    settings_jwt_secret = getattr(settings, "JWT_SECRET_KEY", "NOT_SET")
    
    return {
        "environment_variables": {
            "SECRET_KEY": env_secret[:10] + "..." if len(env_secret) > 10 else env_secret,
            "JWT_SECRET_KEY": env_jwt_secret[:10] + "..." if len(env_jwt_secret) > 10 else env_jwt_secret,
        },
        "settings_object": {
            "SECRET_KEY": settings_secret[:10] + "..." if len(settings_secret) > 10 else settings_secret,
            "JWT_SECRET_KEY": settings_jwt_secret[:10] + "..." if len(settings_jwt_secret) > 10 else settings_jwt_secret,
        },
        "expected_jwt_secret": "XvY2nR8dF3..." # First 10 chars from .env
    }
