from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from datetime import datetime
import uuid
try:
    from bson import ObjectId
except ImportError:
    try:
        from pymongo import ObjectId
    except ImportError:
        ObjectId = None
from app.models import User, UserCreate, UserUpdate, UserRole, UserProfile, Role, RoleCreate, RoleUpdate, PermissionCheck
from app.repo import repo
from app.api.auth import require_roles, get_user_company_context
from app.auth_service import get_current_user_with_super_admin_bypass
from app.auth_service import get_current_user
# Data initialization is handled at server startup

def convert_objectid_to_str(data: Any) -> Any:
    """Recursively convert ObjectId to string in nested data structures"""
    if ObjectId and isinstance(data, ObjectId):
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
async def list_users(
    current_user: UserProfile = Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """List users with company-scoped access control"""
    try:
        # Initialize variables
        current_user_id = current_user.id
        is_platform_admin = False
        accessible_companies = []
        can_manage_users = False
        
        # SUPER_USER bypass
        if current_user.user_type == "SUPER_USER":
            print(f"[USERS] SUPER_USER detected, granting full access")
            is_platform_admin = True  # SUPER_USER has platform admin privileges
            accessible_companies = []  # Will be populated with all companies later
            can_manage_users = True
        else:
            # Company admins can list users in their company, platform admins see all users
            is_platform_admin = company_context["is_platform_admin"]
            accessible_companies = company_context["accessible_companies"]
            
            print(f"[USERS] DEBUG: User {current_user_id} requesting user list")
            print(f"[USERS] DEBUG: is_platform_admin: {is_platform_admin}")
            print(f"[USERS] DEBUG: accessible_companies count: {len(accessible_companies)}")
            
            # Check if user has admin role (platform or company level)
            user_roles = current_user.roles or []
            can_manage_users = is_platform_admin
            
            # Also check if the user has an ADMIN role directly (fallback for platform admin detection)
            if not can_manage_users:
                for role in user_roles:
                    if role.get("role") == "ADMIN":
                        can_manage_users = True
                        print(f"[USERS] DEBUG: Found ADMIN role directly in user roles")
                        break
            
            if not is_platform_admin and not can_manage_users:
                # Check if user is company admin in any of their companies
                for company in accessible_companies:
                    company_id = company.get("id")
                    if company_id:
                        user_role = await repo.get_user_role_in_company(current_user_id, company_id)
                        if user_role:
                            role_details = user_role.get("role_details", {})
                            if role_details.get("company_role_type") == "COMPANY_ADMIN":
                                can_manage_users = True
                                print(f"[USERS] DEBUG: Found COMPANY_ADMIN role")
                                break
            
            print(f"[USERS] DEBUG: can_manage_users: {can_manage_users}")
            
            if not can_manage_users:
                raise HTTPException(status_code=403, detail="Only admins can list users")
        
        # Check if repo has _store (InMemoryRepo) or use MongoDB methods
        if hasattr(repo, '_store'):
            # InMemoryRepo
            users = []
            user_store = repo._store.get("__users__", {})
            role_store = repo._store.get("__roles__", {})
            user_role_store = repo._store.get("__user_roles__", {})
            company_store = repo._store.get("__companies__", {})
            
            # Get accessible company IDs for filtering
            accessible_company_ids = {c.get("id") for c in accessible_companies} if not is_platform_admin else None
            
            for user_id, user_data in user_store.items():
                # Get user roles
                user_roles_info = []
                user_has_accessible_role = False
                
                for ur_id, ur_data in user_role_store.items():
                    if ur_data.get("user_id") == user_id and ur_data.get("status") == "active":
                        company_id = ur_data.get("company_id")
                        
                        # For platform admins, show all roles
                        # For non-platform admins, filter by company access
                        if not is_platform_admin and accessible_company_ids:
                            if company_id not in accessible_company_ids and company_id not in ["global", "1-c"]:
                                continue
                        
                        user_has_accessible_role = True
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
                            "role_name": role.get("name", "") if role else "",
                            "company_name": company.get("name") if company else None,
                            "is_default": ur_data.get("is_default", False),
                            "status": ur_data.get("status", "active"),
                            "created_at": str(ur_data.get("created_at", "")),
                            "updated_at": str(ur_data.get("updated_at", ""))
                        }
                        user_roles_info.append(role_info)
                
                # For platform admins, show all users even if they don't have accessible roles
                # For non-platform admins, skip users who don't have any accessible roles  
                if not is_platform_admin and not user_has_accessible_role:
                    continue
                
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
                    # Use the UUID id field, not the MongoDB _id
                    user_id = user_data.get("id")
                    if not user_id:
                        # Fallback to _id if no id field exists
                        user_id = str(user_data["_id"])
                    
                    # Get user roles with company filtering
                    user_roles_info = []
                    all_user_roles = await repo.get_user_roles(user_id)
                    user_has_accessible_role = False
                    
                    for role in all_user_roles:
                        company_id = role.get("company_id")
                        # For platform admins, show all roles
                        # For non-platform admins, filter by company access
                        if not is_platform_admin and accessible_companies:
                            accessible_company_ids = {c.get("id") for c in accessible_companies}
                            if company_id not in accessible_company_ids and company_id not in ["global", "1-c"]:
                                continue
                        
                        user_has_accessible_role = True
                        user_roles_info.append(role)
                    
                    # For platform admins, show all users even if they don't have accessible roles
                    # For non-platform admins, skip users who don't have any accessible roles
                    if not is_platform_admin and not user_has_accessible_role:
                        continue
                    
                    # Get companies
                    user_companies = []
                    company_ids = list(set(ur.get("company_id") for ur in user_roles_info if ur.get("company_id")))
                    for comp_id in company_ids:
                        if comp_id and comp_id not in ["global", "1-c"]:
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
async def get_user(user_id: str, current_user: UserProfile = Depends(get_current_user)):
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
                        "company_name": company.get("name") or None,
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
async def get_roles_dropdown(
    current_user: UserProfile = Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Get roles for dropdown selection with company filtering"""
    try:
        print(f"[ROLES] DEBUG: Getting roles dropdown for user {current_user.id}")
        
        is_platform_admin = company_context["is_platform_admin"]
        accessible_companies = company_context["accessible_companies"]
        accessible_company_ids = {c.get("id") for c in accessible_companies}
        
        print(f"[ROLES] DEBUG: is_platform_admin: {is_platform_admin}")
        print(f"[ROLES] DEBUG: accessible_company_ids: {accessible_company_ids}")
        
        # Check if repo has _store (InMemoryRepo) or use MongoDB methods
        if hasattr(repo, '_store'):
            # InMemoryRepo
            role_store = repo._store.get("__roles__", {})
            company_store = repo._store.get("__companies__", {})
            
            print(f"[ROLES] DEBUG: Found {len(role_store)} roles in store")
            
            roles_data = []
            for role_id, role_data in role_store.items():
                role_company_id = role_data.get("company_id")
                
                # Filter roles by company access
                if not is_platform_admin:
                    # Non-platform admins only see roles from their accessible companies
                    if role_company_id not in accessible_company_ids and role_company_id not in ["global", "1-c"]:
                        continue
                
                company = company_store.get(role_company_id, {})
                company_name = "System" if role_company_id in ["global", "1-c"] else company.get("name") or None
                
                role_item = {
                    "id": role_id,
                    "name": role_data.get("name", ""),
                    "role_group": role_data.get("role_group", ""),
                    "company_id": role_company_id or "",
                    "company_name": company_name,
                    "is_default": role_data.get("is_default", False)
                }
                roles_data.append(role_item)
                print(f"[ROLES] DEBUG: Added role: {role_item['name']} (company: {company_name})")
        else:
            # MongoRepo - use proper async methods
            from app.repo import MongoRepo
            if isinstance(repo, MongoRepo):
                roles_cursor = repo._role_col.find({})
                roles_data = []
                async for role_data in roles_cursor:
                    role_id = str(role_data["_id"])
                    role_company_id = role_data.get("company_id", "")
                    
                    # Filter roles by company access
                    if not is_platform_admin:
                        # Non-platform admins only see roles from their accessible companies
                        if role_company_id not in accessible_company_ids and role_company_id not in ["global", "1-c"]:
                            continue
                    
                    company_name = "System"
                    if role_company_id and role_company_id not in ["global", "1-c"]:
                        company = await repo.get_company(role_company_id)
                        if company:
                            company_name = company.get("name") or None
                    
                    role_item = {
                        "id": role_id,
                        "name": role_data.get("name", ""),
                        "role_group": role_data.get("role_group", ""),
                        "company_id": role_company_id,
                        "company_name": company_name,
                        "is_default": role_data.get("is_default", False)
                    }
                    # Convert ObjectIds to strings recursively
                    role_item = convert_objectid_to_str(role_item)
                    roles_data.append(role_item)
                    print(f"[ROLES] DEBUG: Added MongoDB role: {role_item['name']} (company: {company_name})")
            else:
                roles_data = []
        
        print(f"[ROLES] DEBUG: Returning {len(roles_data)} roles")
        return roles_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch roles: {str(e)}")


@router.get("/companies/dropdown", response_model=List[Dict])
async def get_companies_dropdown(
    current_user: UserProfile = Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Get companies for dropdown selection with company filtering"""
    try:
        print(f"[COMPANIES] DEBUG: Getting companies dropdown for user {current_user.id}")
        
        is_platform_admin = company_context["is_platform_admin"]
        accessible_companies = company_context["accessible_companies"]
        
        print(f"[COMPANIES] DEBUG: is_platform_admin: {is_platform_admin}")
        print(f"[COMPANIES] DEBUG: accessible_companies count: {len(accessible_companies)}")
        
        # For companies dropdown, we just return the accessible companies
        companies_data = []
        for company in accessible_companies:
            companies_data.append({
                "id": company.get("id", ""),
                "name": company.get("name", ""),
                "type": company.get("type", ""),
                "status": company.get("status", "")
            })
        
        print(f"[COMPANIES] DEBUG: Returning {len(companies_data)} companies")
        return companies_data
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch companies: {str(e)}")


@router.post("/", response_model=Dict)
async def create_user(
    user_data: Dict, 
    current_user: UserProfile = Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Create a new user"""
    try:
# Mock data initialization is handled at server startup
        
        # Check permissions - Platform admins and Company admins can create users
        current_user_id = current_user.id
        is_platform_admin = company_context["is_platform_admin"]
        accessible_companies = company_context["accessible_companies"]
        
        user_can_create = is_platform_admin
        
        if not is_platform_admin:
            # Check if user is company admin in any of their companies
            for company in accessible_companies:
                company_id = company.get("id")
                if company_id:
                    user_role = await repo.get_user_role_in_company(current_user_id, company_id)
                    if user_role:
                        role_details = user_role.get("role_details", {})
                        if role_details.get("company_role_type") == "COMPANY_ADMIN":
                            user_can_create = True
                            break
        
        if not user_can_create:
            raise HTTPException(status_code=403, detail="Only platform admins and company admins can create users")
        
        # Validate that non-platform admins can only create users for their accessible companies
        if not is_platform_admin:
            user_roles_data = user_data.get("roles", [])
            accessible_company_ids = {c.get("id") for c in accessible_companies}
            
            for role_data in user_roles_data:
                role_company_id = role_data.get("company_id")
                if role_company_id not in accessible_company_ids:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Cannot assign user to company {role_company_id} - access denied"
                    )
        
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
                "hashed_password": auth_service.hash_password(user_data.get("password", "defaultpass")),
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
                    "hashed_password": auth_service.hash_password(user_data.get("password", "defaultpass")),
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
    current_user: UserProfile = Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Update a user (Platform admins and Company admins only)"""
    try:
        # Check permissions - Platform admins and Company admins can update users
        current_user_id = current_user.id
        is_platform_admin = company_context["is_platform_admin"]
        accessible_companies = company_context["accessible_companies"]
        
        user_can_update = is_platform_admin
        
        if not is_platform_admin:
            # Check if user is company admin in any of their companies
            for company in accessible_companies:
                company_id = company.get("id")
                if company_id:
                    user_role = await repo.get_user_role_in_company(current_user_id, company_id)
                    if user_role:
                        role_details = user_role.get("role_details", {})
                        if role_details.get("company_role_type") == "COMPANY_ADMIN":
                            user_can_update = True
                            break
        
        if not user_can_update:
            raise HTTPException(status_code=403, detail="Only platform admins and company admins can update users")
        
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
                update_data["hashed_password"] = auth_service.hash_password(update_data.pop("password"))
            
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
                    update_data["hashed_password"] = auth_service.hash_password(update_data.pop("password"))
                
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
async def delete_user(
    user_id: str, 
    current_user: UserProfile = Depends(get_current_user),
    company_context=Depends(get_user_company_context)
):
    """Delete a user (Platform admins and Company admins only)"""
    try:
        # Check permissions - Platform admins and Company admins can delete users
        current_user_id = current_user.id
        is_platform_admin = company_context["is_platform_admin"]
        accessible_companies = company_context["accessible_companies"]
        
        user_can_delete = is_platform_admin
        
        if not is_platform_admin:
            # Check if user is HOST company admin
            for company in accessible_companies:
                company_id = company.get("id")
                if company_id:
                    user_role = await repo.get_user_role_in_company(current_user_id, company_id)
                    if user_role:
                        role_details = user_role.get("role_details", {})
                        company_type = company.get("company_type", "").upper()
                        if role_details.get("company_role_type") == "COMPANY_ADMIN" and company_type == "HOST":
                            user_can_delete = True
                            break
        
        if not user_can_delete:
            raise HTTPException(status_code=403, detail="Only platform admins and HOST company admins can delete users")
        
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
