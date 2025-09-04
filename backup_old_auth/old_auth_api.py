# Enhanced Authentication API Endpoints
# Clean, enterprise-grade authentication with improved RBAC

from fastapi import APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any, List
import logging

from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.rbac.permissions import Page, Permission

logger = logging.getLogger(__name__)

# Request/Response Models
class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_info: Optional[Dict[str, Any]] = None

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]
    permissions: List[Dict[str, Any]]
    is_super_admin: bool

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    refresh_token: Optional[str] = None

class CompanySwitchRequest(BaseModel):
    company_id: Optional[str] = None

class PermissionCheckRequest(BaseModel):
    page: str
    permission: str
    company_id: Optional[str] = None

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

# Dependencies
security = HTTPBearer()

# Global service instances - singleton pattern
_auth_service_instance: Optional[AuthService] = None
_user_service_instance: Optional[UserService] = None

def get_auth_service() -> AuthService:
    """Get auth service instance - singleton with lazy initialization"""
    global _auth_service_instance
    if _auth_service_instance is None:
        _auth_service_instance = AuthService()
    return _auth_service_instance

def get_user_service() -> UserService:
    """Get user service instance - singleton with lazy initialization"""
    global _user_service_instance
    if _user_service_instance is None:
        _user_service_instance = UserService()
    return _user_service_instance

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    auth_service: AuthService = Depends(get_auth_service)
) -> Dict[str, Any]:
    """Extract and validate current user from JWT token"""
    try:
        token = credentials.credentials
        result = await auth_service.validate_access_token(token)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.error,
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return result.data["user"]
        
    except Exception as e:
        logger.error(f"Authentication failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"}
        )

async def check_permission(
    page: Page,
    permission: Permission,
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """Check if current user has required permission"""
    try:
        result = await auth_service.check_permission(
            user_id=current_user["id"],
            company_id=current_user.get("active_company"),
            page=page,
            permission=permission
        )
        
        if not result.success or not result.data["has_permission"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        
        return current_user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Permission check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Permission check failed"
        )

# Create router
router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Authenticate user and return access token with role information.
    
    Returns JWT access token, refresh token, user profile, and permissions.
    """
    try:
        result = await auth_service.login(
            email=request.email,
            password=request.password,
            device_info=request.device_info
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.error
            )
        
        return LoginResponse(**result.data)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication failed"
        )

@router.post("/refresh")
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token.
    
    Returns new access token with updated user information.
    """
    try:
        result = await auth_service.refresh_access_token(request.refresh_token)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=result.error
            )
        
        return result.data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/logout")
async def logout(
    request: LogoutRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Logout user and revoke tokens.
    
    Revokes refresh token(s) to invalidate future token refreshes.
    """
    try:
        result = await auth_service.logout(
            user_id=current_user["id"],
            refresh_token=request.refresh_token
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error
            )
        
        return {"message": "Successfully logged out"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/me")
async def get_current_user_info(
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Get current user information and permissions.
    
    Returns user profile, active company, role, and permissions.
    """
    try:
        # Get fresh permissions for current context
        permissions_result = await user_service.get_user_permissions(
            user_id=current_user["id"],
            company_id=current_user.get("active_company")
        )
        
        permissions_data = permissions_result.data if permissions_result.success else {
            "permissions": [],
            "is_super_admin": False
        }
        
        return {
            "user": current_user,
            "permissions": permissions_data["permissions"],
            "is_super_admin": permissions_data["is_super_admin"]
        }
        
    except Exception as e:
        logger.error(f"Get current user failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user information"
        )

@router.post("/switch-company")
async def switch_company(
    request: CompanySwitchRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Switch user's active company context.
    
    Returns new access token with updated company context and permissions.
    """
    try:
        result = await auth_service.switch_company_context(
            user_id=current_user["id"],
            company_id=request.company_id
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error
            )
        
        return result.data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Company switch failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Company switch failed"
        )

@router.post("/check-permission")
async def check_user_permission(
    request: PermissionCheckRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Check if current user has specific permission.
    
    Returns permission status for the requested page and action.
    """
    try:
        # Validate page and permission
        try:
            page = Page(request.page)
            permission = Permission(request.permission)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid page or permission"
            )
        
        result = await auth_service.check_permission(
            user_id=current_user["id"],
            company_id=request.company_id or current_user.get("active_company"),
            page=page,
            permission=permission
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error
            )
        
        return result.data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Permission check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Permission check failed"
        )

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    user_service: UserService = Depends(get_user_service)
):
    """
    Change user password.
    
    Requires current password for security verification.
    """
    try:
        result = await user_service.change_password(
            user_id=current_user["id"],
            old_password=request.old_password,
            new_password=request.new_password
        )
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error
            )
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

@router.get("/sessions")
async def get_active_sessions(
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get user's active sessions.
    
    Returns list of active refresh tokens with device information.
    """
    try:
        result = await auth_service.get_active_sessions(current_user["id"])
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.error
            )
        
        return {"sessions": result.data}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get sessions failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get sessions"
        )

@router.delete("/sessions/{session_id}")
async def revoke_session(
    session_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Revoke specific user session.
    
    Revokes the refresh token for the specified session.
    """
    try:
        result = await auth_service.revoke_session(current_user["id"], session_id)
        
        if not result.success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=result.error
            )
        
        return {"message": "Session revoked successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Revoke session failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to revoke session"
        )

# Export dependencies for use in other modules
__all__ = [
    "router",
    "get_current_user",
    "check_permission"
]