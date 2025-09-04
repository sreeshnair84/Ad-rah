# Clean Authentication API
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from typing import List
from app.auth_service import auth_service, get_current_user, get_current_active_user, require_permission, require_user_type
from app.database_service import db_service
from app.rbac_models import *

router = APIRouter(prefix="/auth", tags=["Authentication"])

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
    current_user: UserProfile = Depends(require_permission(Permission.USER_CREATE.value))
):
    # Only SUPER_USER and company ADMIN can create users
    if current_user.user_type != UserType.SUPER_USER and current_user.company_role != CompanyRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only administrators can create users")
    
    # Company admin can only create users for their own company
    if current_user.user_type != UserType.SUPER_USER:
        if not current_user.company_id:
            raise HTTPException(status_code=400, detail="Company admin must have a company")
        if user_data.company_id != current_user.company_id:
            raise HTTPException(status_code=403, detail="Company admin can only create users for their own company")
    
    return await auth_service.register_user(user_data)

@router.get("/users", response_model=List[UserProfile])
async def list_users(
    company_id: str = None,
    current_user: UserProfile = Depends(get_current_active_user)
):
    import logging
    logger = logging.getLogger(__name__)
    
    print(f"DEBUG: list_users endpoint called by {current_user.email}")
    logger.info(f"list_users called by user: {current_user.email} (type: {current_user.user_type})")
    
    # Only SUPER_USER and company ADMIN can access user listing
    if current_user.user_type != UserType.SUPER_USER and current_user.company_role != CompanyRole.ADMIN:
        logger.warning(f"Access denied - user {current_user.email} is not admin")
        raise HTTPException(status_code=403, detail="Only administrators can manage users")
    
    # Super users can see all users, company admins see only their company's users
    if current_user.user_type == UserType.SUPER_USER:
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

@router.get("/companies", response_model=List[Company])
async def list_companies(current_user: UserProfile = Depends(get_current_active_user)):
    if current_user.user_type == UserType.SUPER_USER:
        return await db_service.list_companies()
    else:
        if current_user.company_id:
            company = await db_service.get_company(current_user.company_id)
            return [company] if company else []
        return []

@router.get("/navigation", response_model=List[str])
async def get_accessible_navigation(current_user: UserProfile = Depends(get_current_active_user)):
    return current_user.accessible_navigation

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
