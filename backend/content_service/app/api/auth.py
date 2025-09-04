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
    current_user: UserProfile = Depends(require_permission(Permission.USER_READ.value))
):
    # Only SUPER_USER and company ADMIN can access user listing
    if current_user.user_type != UserType.SUPER_USER and current_user.company_role != CompanyRole.ADMIN:
        raise HTTPException(status_code=403, detail="Only administrators can manage users")
    
    # Super users can see all users, company admins see only their company's users
    if current_user.user_type == UserType.SUPER_USER:
        return await db_service.list_all_users()
    else:
        # Company admins can only see users from their own company
        if current_user.company_id:
            return await db_service.list_users_by_company(current_user.company_id)
        else:
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
        return {"status": "healthy", "database": "connected", "auth_service": "operational"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")
