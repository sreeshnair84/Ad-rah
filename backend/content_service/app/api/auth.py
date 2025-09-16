# Unified Authentication API - Consolidated from enhanced_auth.py
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer, HTTPAuthorizationCredentials
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime
import logging

from app.auth_service import (
    auth_service, get_current_user, require_permissions,
    TokenData, SecurityEvent
)
from app.database_service import db_service
from app.rbac_models import LoginRequest, LoginResponse, UserCreate, UserProfile
from app.models import User
from app.repo import repo
from app.config import enhanced_config

# Initialize logger
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Enhanced request/response models
class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class LogoutRequest(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

# HTTP Bearer scheme for token extraction
oauth2_scheme = HTTPBearer()

# Simplified dependency functions
async def get_current_user(credentials = Depends(oauth2_scheme)):
    """Get current authenticated user using enhanced auth service"""
    try:
        if not credentials or not credentials.credentials:
            raise HTTPException(status_code=401, detail="No authorization token provided")
        
        user_profile = await auth_service.get_current_user_from_token(credentials.credentials)
        return user_profile
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=401, detail="Authentication failed")

async def get_current_active_user(current_user = Depends(get_current_user)):
    """Get current active user"""
    is_active = True
    if hasattr(current_user, 'is_active'):
        is_active = current_user.is_active
    elif isinstance(current_user, dict):
        is_active = current_user.get('is_active', True)
    
    if not is_active:
        raise HTTPException(status_code=403, detail="Inactive user account")
    return current_user

def require_permission(permission: str):
    """Require specific permission"""
    async def permission_dependency(current_user = Depends(get_current_active_user)):
        # Get user type
        user_type = None
        if hasattr(current_user, 'user_type'):
            user_type = current_user.user_type.value if hasattr(current_user.user_type, 'value') else str(current_user.user_type)
        elif isinstance(current_user, dict):
            user_type = current_user.get('user_type')
        
        # Super users bypass permission checks
        if user_type == "SUPER_USER":
            return current_user
        
        # Check permissions
        user_permissions = []
        if isinstance(current_user, dict):
            user_permissions = current_user.get('permissions', [])
        elif hasattr(current_user, 'permissions'):
            permissions = getattr(current_user, 'permissions', None)
            user_permissions = permissions if permissions is not None else []
        
        if permission not in user_permissions:
            raise HTTPException(status_code=403, detail=f"Permission required: {permission}")
        return current_user
    return permission_dependency

def require_roles(*allowed_roles):
    """Require specific user roles"""
    async def role_checker(user=Depends(get_current_user)):
        # Get user roles
        user_roles = []
        if isinstance(user, dict):
            user_roles = user.get("roles", [])
        elif hasattr(user, 'roles'):
            user_roles = getattr(user, 'roles', [])
        
        # Get user type for super user bypass
        user_type = None
        if isinstance(user, dict):
            user_type = user.get('user_type')
        elif hasattr(user, 'user_type'):
            user_type = getattr(user, 'user_type')
            if hasattr(user_type, 'value'):
                user_type = user_type.value
        
        # Super users bypass role checks
        if user_type == "SUPER_USER":
            return user

        # Check role groups
        for user_role in user_roles:
            role_group = None
            if isinstance(user_role, dict):
                role_group = user_role.get("role_group")
            elif hasattr(user_role, 'role_group'):
                role_group = getattr(user_role, 'role_group')
            
            if role_group in allowed_roles:
                return user

        raise HTTPException(status_code=403, detail=f"Role required: {list(allowed_roles)}")
    return role_checker

async def get_user_company_context(user=Depends(get_current_user)) -> dict:
    """Get user's company context for filtering data"""
    # Handle both UserProfile objects and dictionaries
    if hasattr(user, 'user_type'):
        # This is a UserProfile object
        user_type = user.user_type.value if hasattr(user.user_type, 'value') else str(user.user_type)
        user_email = user.email.lower() if hasattr(user, 'email') else ""
        user_id = user.id if hasattr(user, 'id') else None
        user_company_id = user.company_id if hasattr(user, 'company_id') else None
    else:
        # This is a dictionary
        user_id = user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        user_type = user.get("user_type", "")
        user_email = user.get("email", "").lower()
        user_company_id = user.get("company_id")
    
    # Build company context
    context = {
        "user_id": user_id,
        "user_type": user_type,
        "user_email": user_email,
        "company_id": user_company_id,
        "is_super_user": user_type == "SUPER_USER"
    }
    
    return context

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, http_request: Request):
    """Enhanced login with refresh tokens and security monitoring"""

    # Check if account is locked
    if await auth_service.is_account_locked(request.email):
        await auth_service.log_security_event(SecurityEvent.LOGIN_FAILED, {
            "username": request.email,
            "reason": "account_locked",
            "ip_address": http_request.client.host if http_request.client else "unknown"
        })
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to multiple failed login attempts"
        )

    try:
        # Find user
        user = await db_service.get_user_by_email(request.email)
        if not user:
            await auth_service.record_failed_attempt(request.email)
            await auth_service.log_security_event(SecurityEvent.LOGIN_FAILED, {
                "username": request.email,
                "reason": "user_not_found"
            })
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Verify password
        if not auth_service.verify_password(request.password, user.get("hashed_password", "")):
            await auth_service.record_failed_attempt(request.email)
            await auth_service.log_security_event(SecurityEvent.LOGIN_FAILED, {
                "username": request.email,
                "reason": "invalid_password"
            })
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )

        # Check if user is active
        if not user.get("is_active", False):
            await auth_service.log_security_event(SecurityEvent.LOGIN_FAILED, {
                "username": request.email,
                "reason": "user_inactive"
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not active"
            )

        # Reset failed attempts on successful login
        await auth_service.reset_failed_attempts(request.email)

        # Create user data for token
        user_data = {
            "id": str(user.get("id", "")),
            "user_type": str(user.get("user_type", "")),
            "company_id": str(user.get("company_id", "")),
            "permissions": user.get("permissions", [])
        }

        # Create token pair
        access_token, refresh_token = await auth_service.create_token_pair(user_data)

        # Log successful login
        await auth_service.log_security_event(SecurityEvent.LOGIN_SUCCESS, {
            "user_id": str(user.get("id", "")),
            "username": request.email,
            "ip_address": http_request.client.host if http_request.client else "unknown"
        })

        # Return enhanced response
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=enhanced_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": str(user.get("id", "")),
                "username": user.get("username", "") or user.get("email", ""),
                "email": user.get("email", ""),
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "user_type": user.get("user_type", ""),
                "company_id": user.get("company_id", ""),
                "permissions": user.get("permissions", [])
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {request.email}: {e}")
        await auth_service.log_security_event(SecurityEvent.LOGIN_FAILED, {
            "username": request.email,
            "reason": "system_error",
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to system error"
        )

@router.post("/login/form", response_model=LoginResponse)
async def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
    login_request = LoginRequest(email=form_data.username, password=form_data.password)
    return await auth_service.login(login_request)

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: UserProfile = Depends(get_current_active_user)):
    return current_user

@router.post("/logout")
async def logout(
    request: LogoutRequest,
    current_user: TokenData = Depends(get_current_user),
    credentials: HTTPAuthorizationCredentials = Depends(oauth2_scheme)
):
    """Enhanced logout with token revocation"""

    try:
        # Revoke both tokens
        await auth_service.logout(credentials.credentials, request.refresh_token)

        await auth_service.log_security_event(SecurityEvent.LOGOUT, {
            "user_id": current_user.user_id
        })

        return {"message": "Successfully logged out"}

    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.post("/users", response_model=User)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_permission("user_create"))
):
    # Only SUPER_ADMIN and company roles can create users
    if current_user.role not in ["super_admin", "admin"]:
        raise HTTPException(status_code=403, detail="Only administrators can create users")
    
    # Company admin can only create users for their own company
    if current_user.role != "super_admin":
        if not current_user.company_id:
            raise HTTPException(status_code=400, detail="Company admin must have a company")
        if user_data.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Company admin can only create users for their own company")
    
    return await auth_service.register_user(user_data)

@router.get("/users", response_model=List[User])
async def list_users(
    company_id: Optional[str] = None,
    current_user: User = Depends(get_current_active_user)
):
    import logging
    logger = logging.getLogger(__name__)
    
    print(f"DEBUG: list_users endpoint called by {current_user.email}")
    logger.info(f"list_users called by user: {current_user.email} (role: {current_user.role})")
    
    # Only SUPER_ADMIN and company roles can access user listing
    if current_user.role not in ["super_admin", "admin"]:
        logger.warning(f"Access denied - user {current_user.email} is not admin")
        raise HTTPException(status_code=403, detail="Only administrators can manage users")
    
    # Super users can see all users, company admins see only their company's users
    if current_user.role == "super_admin":
        logger.info("Getting all users for super user")
        users = await db_service.list_all_users()
        logger.info(f"Retrieved {len(users)} users")
        return users
    else:
        logger.info(f"Getting company users for company_id: {current_user.company_id}")
        # Company admins can only see users from their own company
        if current_user.company_id:
            users = await db_service.list_users_by_company(current_user.company_id)
            logger.info(f"Retrieved {len(users)} company users")
            return users
        else:
            logger.warning("Company admin has no company_id")
            return []

@router.get("/companies")
async def list_companies(current_user: User = Depends(get_current_active_user)):
    if current_user.role == "super_admin":
        return await db_service.list_companies()
    else:
        if current_user.company_id:
            company = await db_service.get_company(current_user.company_id)
            return [company] if company else []
        return []

@router.get("/navigation", response_model=List[str])
async def get_accessible_navigation(current_user: User = Depends(get_current_active_user)):
    # Get accessible navigation for the current user based on role
    if current_user.role == "super_admin":
        accessible_nav = ["admin", "host", "advertiser", "content"]
    elif current_user.role == "admin":
        accessible_nav = ["admin", "host", "advertiser"]
    elif current_user.role == "host":
        accessible_nav = ["host", "content"]
    elif current_user.role == "advertiser":
        accessible_nav = ["advertiser", "content"]
    elif current_user.role == "reviewer":
        accessible_nav = ["content", "moderation"]
    else:
        accessible_nav = []
    
    return accessible_nav

@router.get("/health")
async def health_check():
    try:
        if not db_service.connected:
            raise HTTPException(status_code=503, detail="Database not connected")
        return {"status": "healthy", "database": "connected", "auth_service": "operational", "debug": "code_updated"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")

@router.get("/debug-test")
async def debug_test():
    print("DEBUG: debug_test endpoint called")
    users = await db_service.list_all_users()
    print(f"DEBUG: Found {len(users)} users")
    return {"user_count": len(users), "debug": "endpoint_working"}
