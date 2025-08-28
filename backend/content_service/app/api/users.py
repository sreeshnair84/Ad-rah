from fastapi import APIRouter, Depends, HTTPException
from typing import List
from app.models import User, UserCreate, UserUpdate, UserRole, UserProfile, Role, RoleCreate, RoleUpdate, PermissionCheck
from app.repo import repo
from app.auth import require_roles, get_password_hash

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/", response_model=List[User])
async def list_users(user=Depends(require_roles("ADMIN"))):
    """List all users (Admin only)"""
    users = await repo.list_users()
    return [User(**user) for user in users]


@router.get("/{user_id}", response_model=User)
async def get_user(user_id: str, current_user=Depends(require_roles("ADMIN"))):
    """Get a specific user by ID (Admin only)"""
    user = await repo.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Get user roles
    roles = await repo.get_user_roles(user_id)
    user["roles"] = roles

    return User(**user)


@router.get("/{user_id}/profile", response_model=UserProfile)
async def get_user_profile(user_id: str, current_user=Depends(require_roles("ADMIN"))):
    """Get user profile with expanded role and company information"""
    profile = await repo.get_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User not found")
    return profile


@router.post("/", response_model=User)
async def create_user(user_data: UserCreate, current_user=Depends(require_roles("ADMIN"))):
    """Create a new user (Admin only)"""
    # Check if user already exists
    existing_user = await repo.get_user_by_email(user_data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists")

    # Create user
    user_obj = User(
        name=user_data.name,
        email=user_data.email,
        phone=user_data.phone,
        hashed_password=get_password_hash(user_data.password),
        status="active"
    )

    saved_user = await repo.save_user(user_obj)
    user_id = saved_user["id"]

    # Create user roles
    for role_data in user_data.roles:
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
