from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import uuid
from bson import ObjectId
from app.models import User, UserCreate, UserUpdate, UserRole, UserProfile, Role, RoleCreate, RoleUpdate, PermissionCheck
from app.repo import repo
from app.auth import require_roles, get_password_hash, get_current_user, get_current_user_with_roles
# Data initialization is handled at server startup

def convert_objectid_to_str(data: Any) -> Any:
    """Recursively convert ObjectId to string in nested data structures"""
    if isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, dict):
        return {key: convert_objectid_to_str(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_objectid_to_str(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data

# Users API endpoints

router = APIRouter(prefix="/users", tags=["users"])

# Data initialization is handled by the main application at server startup




@router.get("/", response_model=List[Dict])
@router.get("", response_model=List[Dict])  # Add route without trailing slash
async def list_users(current_user: dict = Depends(get_current_user_with_roles)):
    """List all users with expanded information"""
    try:
        # Mock data initialization is handled at server startup
        
        # Check if user has ADMIN role
        user_roles = current_user.get("roles", [])
        has_admin = any(
            role.get("role") == "ADMIN" or 
            role.get("role_group") == "ADMIN" or
            (role.get("role_details", {}).get("role_group") == "ADMIN")
            for role in user_roles
        )
        if not has_admin:
            role_list = [role.get("role") for role in user_roles]
            role_group_list = [role.get("role_group") for role in user_roles] 
            role_details_list = [role.get("role_details", {}).get("role_group") for role in user_roles]
            raise HTTPException(status_code=403, detail="Only admins can list users")
        
        # Check if repo has _store (InMemoryRepo) or use MongoDB methods
        if hasattr(repo, '_store'):
            # InMemoryRepo
            users = []
            user_store = repo._store.get("__users__", {})
            role_store = repo._store.get("__roles__", {})
            user_role_store = repo._store.get("__user_roles__", {})
            company_store = repo._store.get("__companies__", {})
            
            for user_id, user_data in user_store.items():
                # Get user roles
                user_roles_info = []
                for ur_id, ur_data in user_role_store.items():
                    if ur_data.get("user_id") == user_id and ur_data.get("status") == "active":
                        # Get role details - handle empty role_id and company_id
                        role_id = ur_data.get("role_id")
                        company_id = ur_data.get("company_id")
                        
                        role = role_store.get(role_id, {}) if role_id else {}
                        company = company_store.get(company_id, {}) if company_id else {}
                        
                        role_info = {
                            "id": ur_id,
                            "user_id": user_id,
                            "company_id": company_id or "",
                            "role_id": role_id or "",
                            "role": role.get("role_group", "") if role else "",
                            "role_name": role.get("name", "") if role else "Unknown Role",
                            "company_name": company.get("name", "Unknown") if company else "Unknown Company",
                            "is_default": ur_data.get("is_default", False),
                            "status": ur_data.get("status", "active"),
                            "created_at": str(ur_data.get("created_at", "")),
                            "updated_at": str(ur_data.get("updated_at", ""))
                        }
                        user_roles_info.append(role_info)
                
                # Get companies
                user_companies = []
                company_ids = list(set(ur.get("company_id", "") for ur in user_roles_info if ur.get("company_id")))
                for comp_id in company_ids:
                    if comp_id and comp_id != "global" and comp_id.strip():
                        company = company_store.get(comp_id, {})
                        if company:
                            user_companies.append(company)
                
                user_info = {
                    **user_data,
                    "id": user_id,
                    "roles": user_roles_info,
                    "companies": user_companies,
                    "active_company": user_companies[0].get("id") if user_companies else None,
                    "active_role": next((ur.get("role") for ur in user_roles_info if ur.get("is_default")), 
                                      user_roles_info[0].get("role") if user_roles_info else None)
                }
                users.append(user_info)
        else:
            # MongoRepo - use proper async methods
            users = []
            from app.repo import MongoRepo
            if isinstance(repo, MongoRepo):
                # Get all users
                user_cursor = repo._user_col.find({})
                async for user_data in user_cursor:
                    user_id = str(user_data["_id"])
                    
                    # Get user roles
                    user_roles_info = await repo.get_user_roles(user_id)
                    
                    # Get companies
                    user_companies = []
                    company_ids = list(set(ur.get("company_id") for ur in user_roles_info if ur.get("company_id")))
                    for comp_id in company_ids:
                        if comp_id and comp_id != "global":
                            company = await repo.get_company(comp_id)
                            if company:
                                user_companies.append(company)
                    
                    user_info = {
                        **user_data,
                        "id": user_id,
                        "roles": user_roles_info,
                        "companies": user_companies,
                        "active_company": user_companies[0].get("id") if user_companies else None,
                        "active_role": next((ur.get("role") for ur in user_roles_info if ur.get("is_default")), 
                                          user_roles_info[0].get("role") if user_roles_info else None)
                    }
                    # Convert ObjectIds to strings recursively
                    user_info = convert_objectid_to_str(user_info)
                    users.append(user_info)
            else:
                # Fallback for other repo types
                users = []
        
        return users
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch users: {str(e)}")


@router.get("/{user_id}", response_model=Dict)
async def get_user(user_id: str, current_user: dict = Depends(get_current_user_with_roles)):
    """Get a specific user by ID"""
    try:
# Mock data initialization is handled at server startup
        
        # Check if repo has _store (InMemoryRepo) or use MongoDB methods
        if hasattr(repo, '_store'):
            # InMemoryRepo
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
        else:
            # MongoRepo - use proper async methods
            from app.repo import MongoRepo
            if isinstance(repo, MongoRepo):
                user_data = await repo.get_user(user_id)
                if not user_data:
                    raise HTTPException(status_code=404, detail="User not found")

                # Get user roles with expanded information
                user_roles = await repo.get_user_roles(user_id)

                return {
                    **user_data,
                    "id": user_id,
                    "roles": user_roles
                }
            else:
                raise HTTPException(status_code=404, detail="User not found")
        
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
async def get_roles_dropdown(current_user: dict = Depends(get_current_user_with_roles)):
    """Get roles for dropdown selection"""
    try:
# Mock data initialization is handled at server startup
        
        # Check if repo has _store (InMemoryRepo) or use MongoDB methods
        if hasattr(repo, '_store'):
            # InMemoryRepo
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
        else:
            # MongoRepo - use proper async methods
            from app.repo import MongoRepo
            if isinstance(repo, MongoRepo):
                roles_cursor = repo._role_col.find({})
                roles_data = []
                async for role_data in roles_cursor:
                    role_id = str(role_data["_id"])
                    company_id = role_data.get("company_id", "")
                    
                    company_name = "System"
                    if company_id and company_id != "global":
                        company = await repo.get_company(company_id)
                        if company:
                            company_name = company.get("name", "Unknown")
                    
                    role_item = {
                        "id": role_id,
                        "name": role_data.get("name", ""),
                        "role_group": role_data.get("role_group", ""),
                        "company_id": company_id,
                        "company_name": company_name,
                        "is_default": role_data.get("is_default", False)
                    }
                    # Convert ObjectIds to strings recursively
                    role_item = convert_objectid_to_str(role_item)
                    roles_data.append(role_item)
            else:
                roles_data = []
        
        return roles_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch roles: {str(e)}")


@router.get("/companies/dropdown", response_model=List[Dict])
async def get_companies_dropdown(current_user: dict = Depends(get_current_user_with_roles)):
    """Get companies for dropdown selection"""
    try:
# Mock data initialization is handled at server startup
        
        # Check if repo has _store (InMemoryRepo) or use MongoDB methods
        if hasattr(repo, '_store'):
            # InMemoryRepo
            company_store = repo._store.get("__companies__", {})
            
            companies_data = []
            for company_id, company_data in company_store.items():
                companies_data.append({
                    "id": company_id,
                    "name": company_data.get("name", ""),
                    "type": company_data.get("type", ""),
                    "status": company_data.get("status", "")
                })
        else:
            # MongoRepo - use proper async methods
            from app.repo import MongoRepo
            if isinstance(repo, MongoRepo):
                companies_cursor = repo._company_col.find({})
                companies_data = []
                async for company_data in companies_cursor:
                    company_id = str(company_data["_id"])
                    company_item = {
                        "id": company_id,
                        "name": company_data.get("name", ""),
                        "type": company_data.get("type", ""),
                        "status": company_data.get("status", "")
                    }
                    # Convert ObjectIds to strings recursively
                    company_item = convert_objectid_to_str(company_item)
                    companies_data.append(company_item)
            else:
                companies_data = []
        
        return companies_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch companies: {str(e)}")


@router.post("/", response_model=Dict)
async def create_user(user_data: Dict, current_user: dict = Depends(get_current_user_with_roles)):
    """Create a new user"""
    try:
# Mock data initialization is handled at server startup
        
        # Check permissions
        if not any(role.get("role") == "ADMIN" for role in current_user.get("roles", [])):
            raise HTTPException(status_code=403, detail="Only admins can create users")
        
        # Check if repo has _store (InMemoryRepo) or use MongoDB methods
        if hasattr(repo, '_store'):
            # InMemoryRepo
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
        else:
            # MongoRepo - use proper async methods
            from app.repo import MongoRepo
            if isinstance(repo, MongoRepo):
                # Check if user already exists
                existing_user = await repo._user_col.find_one({"email": user_data.get("email")})
                if existing_user:
                    raise HTTPException(status_code=400, detail="User with this email already exists")
                
                user_doc = {
                    "name": user_data.get("name", ""),
                    "email": user_data.get("email", ""),
                    "phone": user_data.get("phone", ""),
                    "status": user_data.get("status", "active"),
                    "hashed_password": get_password_hash(user_data.get("password", "defaultpass")),
                    "oauth_provider": None,
                    "oauth_id": None,
                    "email_verified": True,
                    "last_login": None,
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
                
                result = await repo._user_col.insert_one(user_doc)
                user_id = str(result.inserted_id)
                
                # Create user roles
                roles_data = user_data.get("roles", [])
                for role_data in roles_data:
                    role_doc = {
                        "user_id": user_id,
                        "company_id": role_data.get("company_id", ""),
                        "role_id": role_data.get("role_id", ""),
                        "is_default": role_data.get("is_default", False),
                        "status": "active",
                        "created_at": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                    await repo._user_role_col.insert_one(role_doc)
                
                return {"message": "User created successfully", "user_id": user_id}
            else:
                raise HTTPException(status_code=500, detail="Unsupported repository type")
        
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
    try:
# Mock data initialization is handled at server startup
        
        # Check if repo has _store (InMemoryRepo) or use MongoDB methods
        if hasattr(repo, '_store'):
            # InMemoryRepo
            user_store = repo._store.get("__users__", {})
            user_role_store = repo._store.get("__user_roles__", {})
            
            if user_id not in user_store:
                raise HTTPException(status_code=404, detail="User not found")
            
            existing_user = user_store[user_id]
            
            # Update user fields
            update_data = user_update.model_dump(exclude_unset=True)
            if "password" in update_data:
                update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
            
            updated_user = {**existing_user, **update_data}
            updated_user["updated_at"] = datetime.utcnow().isoformat()
            user_store[user_id] = updated_user
            
            # Handle role updates
            if user_update.roles is not None:
                # Delete existing roles for this user
                roles_to_delete = [role_id for role_id, role_data in user_role_store.items() 
                                 if role_data.get("user_id") == user_id]
                for role_id in roles_to_delete:
                    del user_role_store[role_id]
                
                # Create new roles
                for role_data in user_update.roles:
                    role_id = str(uuid.uuid4())
                    user_role = {
                        "id": role_id,
                        "user_id": user_id,
                        "company_id": role_data["company_id"],
                        "role_id": role_data["role_id"],
                        "is_default": role_data.get("is_default", False),
                        "status": "active",
                        "created_at": datetime.utcnow().isoformat(),
                        "updated_at": datetime.utcnow().isoformat()
                    }
                    user_role_store[role_id] = user_role
            
            # Return user with roles
            user_with_roles = updated_user.copy()
            user_roles = [role_data for role_data in user_role_store.values() 
                         if role_data.get("user_id") == user_id]
            user_with_roles["roles"] = user_roles
            
            return User(**user_with_roles)
        else:
            # MongoRepo - use proper async methods
            from app.repo import MongoRepo
            if isinstance(repo, MongoRepo):
                existing_user = await repo._user_col.find_one({"id": user_id})
                if not existing_user:
                    raise HTTPException(status_code=404, detail="User not found")
                
                # Update user fields
                update_data = user_update.model_dump(exclude_unset=True)
                if "password" in update_data:
                    update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
                
                update_data["updated_at"] = datetime.utcnow()
                
                await repo._user_col.update_one(
                    {"id": user_id},
                    {"$set": update_data}
                )
                
                # Handle role updates
                if user_update.roles is not None:
                    # Delete existing roles
                    await repo._user_role_col.delete_many({"user_id": user_id})
                    
                    # Create new roles
                    for role_data in user_update.roles:
                        role_doc = {
                            "user_id": user_id,
                            "company_id": role_data["company_id"],
                            "role_id": role_data["role_id"],
                            "is_default": role_data.get("is_default", False),
                            "status": "active",
                            "created_at": datetime.utcnow(),
                            "updated_at": datetime.utcnow()
                        }
                        await repo._user_role_col.insert_one(role_doc)
                
                # Return user with roles
                updated_user = await repo._user_col.find_one({"id": user_id})
                if updated_user:
                    updated_user["id"] = user_id
                    user_roles = await repo._user_role_col.find({"user_id": user_id}).to_list(None)
                    updated_user["roles"] = user_roles
                    return User(**updated_user)
                else:
                    raise HTTPException(status_code=404, detail="User not found")
            else:
                raise HTTPException(status_code=500, detail="Unsupported repository type")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update user: {str(e)}")


@router.delete("/{user_id}")
async def delete_user(user_id: str, current_user=Depends(require_roles("ADMIN"))):
    """Delete a user (Admin only)"""
    try:
# Mock data initialization is handled at server startup
        
        # Check if repo has _store (InMemoryRepo) or use MongoDB methods
        if hasattr(repo, '_store'):
            # InMemoryRepo
            user_store = repo._store.get("__users__", {})
            user_role_store = repo._store.get("__user_roles__", {})
            
            if user_id not in user_store:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Delete user
            del user_store[user_id]
            
            # Delete user roles
            roles_to_delete = [role_id for role_id, role_data in user_role_store.items() 
                             if role_data.get("user_id") == user_id]
            for role_id in roles_to_delete:
                del user_role_store[role_id]
            
            return {"message": "User deleted successfully"}
        else:
            # MongoRepo - use proper async methods
            from app.repo import MongoRepo
            if isinstance(repo, MongoRepo):
                # Delete user roles first
                await repo._user_role_col.delete_many({"user_id": user_id})
                
                # Delete user
                result = await repo._user_col.delete_one({"id": user_id})
                if result.deleted_count == 0:
                    raise HTTPException(status_code=404, detail="User not found")
                
                return {"message": "User deleted successfully"}
            else:
                raise HTTPException(status_code=500, detail="Unsupported repository type")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete user: {str(e)}")


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
