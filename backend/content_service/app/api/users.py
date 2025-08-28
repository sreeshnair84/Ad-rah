from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict
from datetime import datetime
import uuid
from app.models import User, UserCreate, UserUpdate, UserRole, UserProfile, Role, RoleCreate, RoleUpdate, PermissionCheck
from app.repo import repo
from app.auth import require_roles, get_password_hash, get_current_user
from app.api.init_data import initialize_mock_data

router = APIRouter(prefix="/users", tags=["users"])

# Initialize mock data when module loads
@router.on_event("startup")
async def startup_event():
    await initialize_mock_data()


@router.get("/", response_model=List[Dict])
async def list_users(current_user: dict = Depends(get_current_user)):
    """List all users with expanded information"""
    try:
        # Ensure mock data is loaded
        await initialize_mock_data()
        
        # Check permissions
        if not any(role.get("role") == "ADMIN" for role in current_user.get("roles", [])):
            raise HTTPException(status_code=403, detail="Only admins can list users")
        
        users = []
        user_store = repo._store.get("__users__", {})
        role_store = repo._store.get("__roles__", {})
        user_role_store = repo._store.get("__user_roles__", {})
        company_store = repo._store.get("__companies__", {})
        
        for user_id, user_data in user_store.items():
            # Get user roles
            user_roles = []
            for ur_id, ur_data in user_role_store.items():
                if ur_data.get("user_id") == user_id and ur_data.get("status") == "active":
                    # Get role details
                    role = role_store.get(ur_data.get("role_id"), {})
                    company = company_store.get(ur_data.get("company_id"), {})
                    
                    role_info = {
                        "id": ur_id,
                        "user_id": user_id,
                        "company_id": ur_data.get("company_id"),
                        "role_id": ur_data.get("role_id"),
                        "role": role.get("role_group", ""),
                        "role_name": role.get("name", ""),
                        "company_name": company.get("name", "Unknown"),
                        "is_default": ur_data.get("is_default", False),
                        "status": ur_data.get("status", "active"),
                        "created_at": ur_data.get("created_at", ""),
                        "updated_at": ur_data.get("updated_at", "")
                    }
                    user_roles.append(role_info)
            
            # Get companies
            user_companies = []
            company_ids = list(set(ur.get("company_id") for ur in user_roles))
            for comp_id in company_ids:
                if comp_id and comp_id != "global":
                    company = company_store.get(comp_id, {})
                    if company:
                        user_companies.append(company)
            
            user_info = {
                **user_data,
                "id": user_id,
                "roles": user_roles,
                "companies": user_companies,
                "active_company": user_companies[0].get("id") if user_companies else None,
                "active_role": next((ur.get("role") for ur in user_roles if ur.get("is_default")), 
                                  user_roles[0].get("role") if user_roles else None)
            }
            users.append(user_info)
        
        return users
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")


@router.get("/{user_id}", response_model=Dict)
async def get_user(user_id: str, current_user: dict = Depends(get_current_user)):
    """Get a specific user by ID"""
    try:
        await initialize_mock_data()
        
        user_store = repo._store.get("__users__", {})
        user_data = user_store.get(user_id)
        
        if not user_data:
            raise HTTPException(status_code=404, detail="User not found")

        # Get user roles with expanded information
        user_roles = []
        role_store = repo._store.get("__roles__", {})
        user_role_store = repo._store.get("__user_roles__", {})
        company_store = repo._store.get("__companies__", {})
        
        for ur_id, ur_data in user_role_store.items():
            if ur_data.get("user_id") == user_id and ur_data.get("status") == "active":
                role = role_store.get(ur_data.get("role_id"), {})
                company = company_store.get(ur_data.get("company_id"), {})
                
                role_info = {
                    "id": ur_id,
                    "user_id": user_id,
                    "company_id": ur_data.get("company_id"),
                    "role_id": ur_data.get("role_id"),
                    "role": role.get("role_group", ""),
                    "role_name": role.get("name", ""),
                    "company_name": company.get("name", "Unknown"),
                    "is_default": ur_data.get("is_default", False),
                    "status": ur_data.get("status", "active"),
                    "created_at": ur_data.get("created_at", ""),
                    "updated_at": ur_data.get("updated_at", "")
                }
                user_roles.append(role_info)

        return {
            **user_data,
            "id": user_id,
            "roles": user_roles
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch user: {str(e)}")


@router.get("/{user_id}/profile", response_model=UserProfile)
async def get_user_profile(user_id: str, current_user=Depends(require_roles("ADMIN"))):
    """Get user profile with expanded role and company information"""
    profile = await repo.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile


@router.get("/roles/dropdown", response_model=List[Dict])
async def get_roles_dropdown(current_user: dict = Depends(get_current_user)):
    """Get roles for dropdown selection"""
    try:
        await initialize_mock_data()
        
        role_store = repo._store.get("__roles__", {})
        company_store = repo._store.get("__companies__", {})
        
        roles_data = []
        for role_id, role_data in role_store.items():
            company = company_store.get(role_data.get("company_id"), {})
            company_name = "System" if role_data.get("company_id") == "global" else company.get("name", "Unknown")
            
            roles_data.append({
                "id": role_id,
                "name": role_data.get("name", ""),
                "role_group": role_data.get("role_group", ""),
                "company_id": role_data.get("company_id", ""),
                "company_name": company_name,
                "is_default": role_data.get("is_default", False)
            })
        
        return roles_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch roles: {str(e)}")


@router.get("/companies/dropdown", response_model=List[Dict])
async def get_companies_dropdown(current_user: dict = Depends(get_current_user)):
    """Get companies for dropdown selection"""
    try:
        await initialize_mock_data()
        
        company_store = repo._store.get("__companies__", {})
        
        companies_data = []
        for company_id, company_data in company_store.items():
            companies_data.append({
                "id": company_id,
                "name": company_data.get("name", ""),
                "type": company_data.get("type", ""),
                "status": company_data.get("status", "")
            })
        
        return companies_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch companies: {str(e)}")


@router.post("/", response_model=Dict)
async def create_user(user_data: Dict, current_user: dict = Depends(get_current_user)):
    """Create a new user"""
    try:
        await initialize_mock_data()
        
        # Check permissions
        if not any(role.get("role") == "ADMIN" for role in current_user.get("roles", [])):
            raise HTTPException(status_code=403, detail="Only admins can create users")
        
        user_store = repo._store.setdefault("__users__", {})
        
        # Check if user already exists
        for existing_user in user_store.values():
            if existing_user.get("email") == user_data.get("email"):
                raise HTTPException(status_code=400, detail="User with this email already exists")
        
        # Create new user
        user_id = str(uuid.uuid4())
        new_user = {
            "id": user_id,
            "name": user_data.get("name", ""),
            "email": user_data.get("email", ""),
            "phone": user_data.get("phone", ""),
            "status": user_data.get("status", "active"),
            "hashed_password": get_password_hash(user_data.get("password", "defaultpass")),
            "oauth_provider": None,
            "oauth_id": None,
            "email_verified": True,
            "last_login": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        
        user_store[user_id] = new_user
        
        # Create user roles
        user_role_store = repo._store.setdefault("__user_roles__", {})
        roles_data = user_data.get("roles", [])
        
        for role_data in roles_data:
            user_role_id = str(uuid.uuid4())
            user_role = {
                "id": user_role_id,
                "user_id": user_id,
                "company_id": role_data.get("company_id", ""),
                "role_id": role_data.get("role_id", ""),
                "is_default": role_data.get("is_default", False),
                "status": "active",
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            user_role_store[user_role_id] = user_role
        
        return {"message": "User created successfully", "user_id": user_id}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create user: {str(e)}")


@router.put("/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    user_update: UserUpdate,
    current_user=Depends(require_roles("ADMIN"))
):
    """Update a user (Admin only)"""
    existing_user = await repo.get_user(user_id)
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    # Update user fields
    update_data = user_update.model_dump(exclude_unset=True)
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))

    updated_user = {**existing_user, **update_data}

    # Save updated user
    user_obj = User(**updated_user)
    saved_user = await repo.save_user(user_obj)

    # Handle role updates
    if user_update.roles is not None:
        # Delete existing roles
        existing_roles = await repo.get_user_roles(user_id)
        for role in existing_roles:
            await repo.delete_user_role(role["id"])

        # Create new roles
        for role_data in user_update.roles:
            role_obj = UserRole(
                user_id=user_id,
                company_id=role_data["company_id"],
                role_id=role_data["role_id"],
                is_default=role_data.get("is_default", False),
                status="active"
            )
            await repo.save_user_role(role_obj)

    # Return user with roles
    user_with_roles = await repo.get_user(user_id)
    if not user_with_roles:
        raise HTTPException(status_code=404, detail="User not found")

    roles = await repo.get_user_roles(user_id)
    user_with_roles["roles"] = roles

    return User(**user_with_roles)


@router.delete("/{user_id}")
async def delete_user(user_id: str, current_user=Depends(require_roles("ADMIN"))):
    """Delete a user (Admin only)"""
    # Delete user roles first
    roles = await repo.get_user_roles(user_id)
    for role in roles:
        await repo.delete_user_role(role["id"])

    # Delete user
    success = await repo.delete_user(user_id)
    if not success:
        raise HTTPException(status_code=404, detail="User not found")
    return {"message": "User deleted successfully"}


# Role management endpoints
@router.get("/roles/company/{company_id}", response_model=List[Role])
async def list_roles_by_company(company_id: str, current_user=Depends(require_roles("ADMIN"))):
    """List all roles for a company"""
    roles = await repo.list_roles_by_company(company_id)
    return [Role(**role) for role in roles]


@router.post("/roles", response_model=Role)
async def create_role(role_data: RoleCreate, current_user=Depends(require_roles("ADMIN"))):
    """Create a new role"""
    role_obj = Role(
        name=role_data.name,
        role_group=role_data.role_group,
        company_id=role_data.company_id,
        is_default=role_data.is_default,
        status="active"
    )

    saved_role = await repo.save_role(role_obj)
    role_id = saved_role["id"]

    # Create role permissions
    for perm_data in role_data.permissions:
        from app.models import RolePermission
        perm_obj = RolePermission(
            role_id=role_id,
            screen=perm_data["screen"],
            permissions=perm_data["permissions"]
        )
        await repo.save_role_permission(perm_obj)

    return Role(**saved_role)


@router.put("/roles/{role_id}", response_model=Role)
async def update_role(
    role_id: str,
    role_update: RoleUpdate,
    current_user=Depends(require_roles("ADMIN"))
):
    """Update a role"""
    existing_role = await repo.get_role(role_id)
    if not existing_role:
        raise HTTPException(status_code=404, detail="Role not found")

    update_data = role_update.model_dump(exclude_unset=True)
    updated_role = {**existing_role, **update_data}

    role_obj = Role(**updated_role)
    saved_role = await repo.save_role(role_obj)

    return Role(**saved_role)


@router.delete("/roles/{role_id}")
async def delete_role(role_id: str, current_user=Depends(require_roles("ADMIN"))):
    """Delete a role"""
    success = await repo.delete_role(role_id)
    if not success:
        raise HTTPException(status_code=404, detail="Role not found")
    return {"message": "Role deleted successfully"}


# Permission checking endpoint
@router.post("/check-permission")
async def check_permission(permission_check: PermissionCheck, current_user=Depends(require_roles("ADMIN"))):
    """Check if a user has specific permission for a screen in a company"""
    has_permission = await repo.check_user_permission(
        permission_check.user_id,
        permission_check.company_id,
        permission_check.screen,
        permission_check.permission
    )
    return {"has_permission": has_permission}


@router.post("/invite")
async def invite_user(
    email: str,
    company_id: str,
    role_id: str,
    current_user=Depends(require_roles("ADMIN", "HOST"))
):
    """Invite a user to join the system"""
    from app.api.registration import invite_user
    return await invite_user(email, company_id, role_id, current_user)
