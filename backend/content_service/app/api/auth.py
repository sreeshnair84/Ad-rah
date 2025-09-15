# Clean Authentication API
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm, HTTPBearer
from typing import List, Optional

# Use the enhanced auth service instead of the old one
from app.auth_service import auth_service
from app.database_service import db_service
from app.rbac_models import LoginRequest, LoginResponse, UserCreate
from app.models import UserProfile

router = APIRouter(prefix="/auth", tags=["Authentication"])

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
async def login(login_request: LoginRequest):
    return await auth_service.login(login_request)

@router.post("/login/form", response_model=LoginResponse)
async def login_form(form_data: OAuth2PasswordRequestForm = Depends()):
    login_request = LoginRequest(email=form_data.username, password=form_data.password)
    return await auth_service.login(login_request)

@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(current_user: UserProfile = Depends(get_current_active_user)):
    return current_user

@router.post("/logout")
async def logout():
    return {"message": "Successfully logged out"}

@router.post("/users", response_model=UserProfile)
async def create_user(
    user_data: UserCreate,
    current_user: UserProfile = Depends(require_permission("user_create"))
):
    # Only SUPER_USER and company ADMIN can create users
    if current_user.user_type != "SUPER_USER" and current_user.company_role != "ADMIN":
        raise HTTPException(status_code=403, detail="Only administrators can create users")
    
    # Company admin can only create users for their own company
    if current_user.user_type != "SUPER_USER":
        if not current_user.company_id:
            raise HTTPException(status_code=400, detail="Company admin must have a company")
        if user_data.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Company admin can only create users for their own company")
    
    return await auth_service.register_user(user_data)

@router.get("/users", response_model=List[UserProfile])
async def list_users(
    company_id: Optional[str] = None,
    current_user: UserProfile = Depends(get_current_active_user)
):
    import logging
    logger = logging.getLogger(__name__)
    
    print(f"DEBUG: list_users endpoint called by {current_user.email}")
    logger.info(f"list_users called by user: {current_user.email} (type: {current_user.user_type})")
    
    # Only SUPER_USER and company ADMIN can access user listing
    if current_user.user_type != "SUPER_USER" and current_user.company_role != "ADMIN":
        logger.warning(f"Access denied - user {current_user.email} is not admin")
        raise HTTPException(status_code=403, detail="Only administrators can manage users")
    
    # Super users can see all users, company admins see only their company's users
    if current_user.user_type == "SUPER_USER":
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
async def list_companies(current_user: UserProfile = Depends(get_current_active_user)):
    if current_user.user_type == "SUPER_USER":
        return await db_service.list_companies()
    else:
        if current_user.company_id:
            company = await db_service.get_company(current_user.company_id)
            return [company] if company else []
        return []

@router.get("/navigation", response_model=List[str])
async def get_accessible_navigation(current_user: UserProfile = Depends(get_current_active_user)):
    # Get accessible navigation for the current user
    if isinstance(current_user, dict):
        accessible_nav = current_user.get('accessible_navigation', [])
    elif hasattr(current_user, 'accessible_navigation'):
        accessible_nav = getattr(current_user, 'accessible_navigation', [])
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
