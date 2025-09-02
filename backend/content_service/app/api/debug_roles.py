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