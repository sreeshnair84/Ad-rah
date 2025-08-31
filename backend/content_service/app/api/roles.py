from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Optional
from datetime import datetime
import logging

from app.models import Role, RolePermission, User, RoleGroup
from app.repo import repo
from app.auth import get_current_user_with_roles, get_current_user
from bson import ObjectId

# Configure logger
logger = logging.getLogger(__name__)


def convert_objectid_to_str(data):
    """Recursively convert ObjectId instances to strings in a data structure"""
    if isinstance(data, ObjectId):
        return str(data)
    elif isinstance(data, dict):
        return {key: convert_objectid_to_str(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_objectid_to_str(item) for item in data]
    else:
        return data

router = APIRouter(prefix="/roles", tags=["roles"])




@router.post("/", response_model=Dict)
async def create_role(
    role_data: Dict,
    current_user: dict = Depends(get_current_user_with_roles)
):
    """Create a new role"""
    try:
        logger.info(f"User {current_user.get('email')} attempting to create role: {role_data.get('name')}")
        
        # Check if user has ADMIN role
        user_roles = current_user.get("roles", [])
        is_admin = any(
            role.get("role") == "ADMIN" or 
            role.get("role_group") == "ADMIN" or
            ((role.get("role_details") or {}).get("role_group") == "ADMIN")
            for role in user_roles if role
        )
        
        if not is_admin:
            logger.warning(f"User {current_user.get('email')} denied role creation - insufficient permissions")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can create roles"
            )
        
        # Validate required fields
        required_fields = ["name", "role_group", "company_id"]
        for field in required_fields:
            if field not in role_data:
                logger.error(f"Missing required field in role creation: {field}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Create role object
        role = Role(
            name=role_data["name"],
            role_group=role_data["role_group"],
            company_id=role_data["company_id"],
            is_default=role_data.get("is_default", False),
            status="active"
        )
        
        # Save to repository
        saved_role = await repo.save_role(role)
        logger.info(f"Role '{role_data['name']}' created successfully by user {current_user.get('email')}")
        
        return {
            "message": "Role created successfully",
            "role": convert_objectid_to_str(saved_role)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create role: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create role: {str(e)}"
        )


@router.get("/", response_model=List[Dict])
@router.get("", response_model=List[Dict])  # Add route without trailing slash
async def list_roles(
    company_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user_with_roles)
):
    """List all roles, optionally filtered by company"""
    try:
        print(f"[ROLES] INFO: User {current_user.get('email')} requesting roles list, company_id: {company_id}")
        print(f"[ROLES] DEBUG: Current user roles: {len(current_user.get('roles', []))}")
        
        # Check if user has ADMIN role
        user_roles = current_user.get("roles", [])
        is_admin = any(
            role.get("role") == "ADMIN" or 
            role.get("role_group") == "ADMIN" or
            ((role.get("role_details") or {}).get("role_group") == "ADMIN")
            for role in user_roles if role
        )
        
        print(f"[ROLES] DEBUG: Is admin: {is_admin}")
        print(f"[ROLES] DEBUG: User roles details: {[{'role': r.get('role'), 'role_group': r.get('role_group'), 'role_details': (r.get('role_details') or {}).get('role_group')} for r in user_roles if r]}")
        
        if not is_admin:
            print(f"[ROLES] WARNING: User {current_user.get('email')} denied roles list access - insufficient permissions")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to view roles"
            )
        
        print("[ROLES] INFO: User has admin permissions, proceeding with role listing")
        
        # Fetch actual roles from repository
        roles = []
        if hasattr(repo, '_store'):
            # InMemoryRepo
            print("[ROLES] DEBUG: Using InMemoryRepo")
            roles_store = repo._store.get("__roles__", {})
            companies_store = repo._store.get("__companies__", {})
            user_roles_store = repo._store.get("__user_roles__", {})
            
            print(f"[ROLES] DEBUG: Found {len(roles_store)} roles in store")
            
            for role_id, role_data in roles_store.items():
                # Get company name
                company = companies_store.get(role_data.get("company_id"), {})
                company_name = company.get("name") or None
                
                # Count users with this role
                user_count = sum(1 for ur in user_roles_store.values() 
                               if ur.get("role_id") == role_id and ur.get("status") == "active")
                
                role_info = {
                    "id": role_id,
                    "name": role_data.get("name"),
                    "role_group": role_data.get("role_group"),
                    "company_id": role_data.get("company_id"),
                    "company_name": company_name,
                    "is_default": role_data.get("is_default", False),
                    "status": role_data.get("status", "active"),
                    "user_count": user_count,
                    "created_at": role_data.get("created_at", ""),
                    "updated_at": role_data.get("updated_at", "")
                }
                
                if company_id is None or role_data.get("company_id") == company_id:
                    roles.append(role_info)
        else:
            # MongoRepo
            print("[ROLES] DEBUG: Using MongoRepo")
            from app.repo import MongoRepo
            if isinstance(repo, MongoRepo):
                query = {} if company_id is None else {"company_id": company_id}
                roles_cursor = repo._role_col.find(query)
                
                async for role_data in roles_cursor:
                    # Get company name
                    company = await repo.get_company(role_data.get("company_id"))
                    company_name = company.get("name") if company else None
                    
                    # Count users with this role
                    user_count = await repo._user_role_col.count_documents({
                        "role_id": role_data.get("id"),
                        "status": "active"
                    })
                    
                    roles.append(convert_objectid_to_str({
                        "id": role_data.get("id"),
                        "name": role_data.get("name"),
                        "role_group": role_data.get("role_group"),
                        "company_id": role_data.get("company_id"),
                        "company_name": company_name,
                        "is_default": role_data.get("is_default", False),
                        "status": role_data.get("status", "active"),
                        "user_count": user_count,
                        "created_at": role_data.get("created_at", ""),
                        "updated_at": role_data.get("updated_at", "")
                    }))
        
        print(f"[ROLES] INFO: Retrieved {len(roles)} roles for user {current_user.get('email')}")
        return roles
        
    except HTTPException:
        print(f"[ROLES] ERROR: HTTPException raised")
        raise
    except Exception as e:
        print(f"[ROLES] ERROR: Failed to fetch roles: {str(e)}")
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch roles: {str(e)}"
        )


@router.get("/{role_id}", response_model=Dict)
async def get_role(
    role_id: str,
    current_user: dict = Depends(get_current_user_with_roles)
):
    """Get a specific role by ID"""
    try:
        role = await repo.get_role(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
            
        # Get permissions
        permissions = await _get_role_permissions_helper(role_id)
        role["permissions"] = permissions
        
        return convert_objectid_to_str(role)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch role: {str(e)}"
        )


@router.put("/{role_id}", response_model=Dict)
async def update_role(
    role_id: str,
    role_data: Dict,
    current_user: dict = Depends(get_current_user_with_roles)
):
    """Update an existing role"""
    try:
        logger.info(f"User {current_user.get('email')} attempting to update role {role_id}")
        
        # Check if user has ADMIN role
        user_roles = current_user.get("roles", [])
        is_admin = any(
            role.get("role") == "ADMIN" or 
            role.get("role_group") == "ADMIN" or
            ((role.get("role_details") or {}).get("role_group") == "ADMIN")
            for role in user_roles if role
        )
        
        if not is_admin:
            logger.warning(f"User {current_user.get('email')} denied role update - insufficient permissions")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can update roles"
            )
        
        # Check if role exists
        existing_role = await repo.get_role(role_id)
        if not existing_role:
            logger.warning(f"Role {role_id} not found for update attempt by user {current_user.get('email')}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        # Update role data
        updated_data = {**existing_role, **role_data}
        updated_data["updated_at"] = datetime.utcnow()
        
        # Save to repository
        if hasattr(repo, '_store'):
            # InMemoryRepo
            repo._store.setdefault("__roles__", {})[role_id] = updated_data
        else:
            # MongoRepo
            from app.repo import MongoRepo
            if isinstance(repo, MongoRepo):
                await repo._role_col.update_one(
                    {"id": role_id},
                    {"$set": updated_data}
                )
        
        logger.info(f"Role {role_id} updated successfully by user {current_user.get('email')}")
        return {
            "message": "Role updated successfully",
            "role": convert_objectid_to_str(updated_data)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update role {role_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update role: {str(e)}"
        )


@router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    current_user: dict = Depends(get_current_user_with_roles)
):
    """Delete a role"""
    try:
        logger.info(f"User {current_user.get('email')} attempting to delete role {role_id}")
        
        # Check if user has ADMIN role
        user_roles = current_user.get("roles", [])
        is_admin = any(
            role.get("role") == "ADMIN" or 
            role.get("role_group") == "ADMIN" or
            ((role.get("role_details") or {}).get("role_group") == "ADMIN")
            for role in user_roles if role
        )
        
        if not is_admin:
            logger.warning(f"User {current_user.get('email')} denied role deletion - insufficient permissions")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can delete roles"
            )
        
        # Check if role exists
        role = await repo.get_role(role_id)
        if not role:
            logger.warning(f"Role {role_id} not found for deletion attempt by user {current_user.get('email')}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        # Check if role is default
        if role.get("is_default"):
            logger.warning(f"User {current_user.get('email')} attempted to delete default role {role_id}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete default role"
            )
        
        # Check if role is assigned to users
        if hasattr(repo, '_store'):
            # InMemoryRepo
            user_roles = repo._store.get("__user_roles__", {})
            assigned_count = sum(1 for ur in user_roles.values() 
                               if ur.get("role_id") == role_id and ur.get("status") == "active")
        else:
            # MongoRepo
            from app.repo import MongoRepo
            if isinstance(repo, MongoRepo):
                assigned_count = await repo._user_role_col.count_documents({
                    "role_id": role_id, 
                    "status": "active"
                })
            else:
                assigned_count = 0
        
        if assigned_count > 0:
            logger.warning(f"User {current_user.get('email')} attempted to delete role {role_id} assigned to {assigned_count} users")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete role assigned to {assigned_count} user(s)"
            )
        
        # Delete role
        if hasattr(repo, '_store'):
            # InMemoryRepo
            if role_id in repo._store.get("__roles__", {}):
                del repo._store["__roles__"][role_id]
                
            # Delete associated permissions
            permissions = repo._store.get("__role_permissions__", {})
            to_delete = [p_id for p_id, perm in permissions.items() 
                        if perm.get("role_id") == role_id]
            for p_id in to_delete:
                del permissions[p_id]
        else:
            # MongoRepo
            from app.repo import MongoRepo
            if isinstance(repo, MongoRepo):
                await repo._role_col.delete_one({"id": role_id})
                # Delete associated permissions
                await repo._role_permission_col.delete_many({"role_id": role_id})
        
        logger.info(f"Role {role_id} deleted successfully by user {current_user.get('email')}")
        return {"message": "Role deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete role {role_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete role: {str(e)}"
        )


async def _get_role_permissions_helper(role_id: str):
    """Internal helper function to get permissions for a specific role"""
    if hasattr(repo, '_store'):
        # InMemoryRepo
        permissions = []
        permission_store = repo._store.get("__role_permissions__", {})
        
        for perm_id, perm_data in permission_store.items():
            if perm_data.get("role_id") == role_id:
                permissions.append({
                    "id": perm_id,
                    "screen": perm_data.get("screen"),
                    "permissions": perm_data.get("permissions", [])
                })
    else:
        # MongoRepo
        from app.repo import MongoRepo
        if isinstance(repo, MongoRepo):
            permissions_cursor = repo._role_permission_col.find({"role_id": role_id})
            permissions = []
            async for perm_data in permissions_cursor:
                permissions.append(convert_objectid_to_str({
                    "id": perm_data.get("id"),
                    "screen": perm_data.get("screen"),
                    "permissions": perm_data.get("permissions", [])
                }))
        else:
            permissions = []
    
    return permissions


@router.get("/{role_id}/permissions", response_model=List[Dict])
async def get_role_permissions(role_id: str):
    """Get permissions for a specific role"""
    try:
        return await _get_role_permissions_helper(role_id)
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch role permissions: {str(e)}"
        )


@router.post("/{role_id}/permissions", response_model=Dict)
async def set_role_permissions(
    role_id: str,
    permissions_data: List[Dict],
    current_user: dict = Depends(get_current_user_with_roles)
):
    """Set permissions for a role"""
    try:
        logger.info(f"User {current_user.get('email')} attempting to set permissions for role {role_id}")
        
        # Check if user has ADMIN role
        user_roles = current_user.get("roles", [])
        is_admin = any(
            role.get("role") == "ADMIN" or 
            role.get("role_group") == "ADMIN" or
            ((role.get("role_details") or {}).get("role_group") == "ADMIN")
            for role in user_roles if role
        )
        
        if not is_admin:
            logger.warning(f"User {current_user.get('email')} denied permission management - insufficient permissions")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can manage role permissions"
            )
        
        # Check if role exists
        role = await repo.get_role(role_id)
        if not role:
            logger.warning(f"Role {role_id} not found for permission update by user {current_user.get('email')}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        # Clear existing permissions for this role
        if hasattr(repo, '_store'):
            # InMemoryRepo
            permission_store = repo._store.setdefault("__role_permissions__", {})
            to_delete = [p_id for p_id, perm in permission_store.items() 
                        if perm.get("role_id") == role_id]
            for p_id in to_delete:
                del permission_store[p_id]
        else:
            # MongoRepo
            from app.repo import MongoRepo
            if isinstance(repo, MongoRepo):
                await repo._role_permission_col.delete_many({"role_id": role_id})
        
        # Add new permissions
        created_permissions = []
        for perm_data in permissions_data:
            if perm_data.get("permissions"):  # Only create if permissions exist
                if hasattr(repo, '_store'):
                    # InMemoryRepo
                    permission_store = repo._store.setdefault("__role_permissions__", {})
                    perm_id = f"{role_id}_{perm_data['screen']}_{len(permission_store)}"
                    permission = {
                        "id": perm_id,
                        "role_id": role_id,
                        "screen": perm_data["screen"],
                        "permissions": perm_data["permissions"],
                        "created_at": datetime.utcnow().isoformat()
                    }
                    permission_store[perm_id] = permission
                    created_permissions.append(permission)
                else:
                    # MongoRepo
                    from app.repo import MongoRepo
                    if isinstance(repo, MongoRepo):
                        import uuid
                        perm_id = str(uuid.uuid4())
                        permission = {
                            "id": perm_id,
                            "role_id": role_id,
                            "screen": perm_data["screen"],
                            "permissions": perm_data["permissions"],
                            "created_at": datetime.utcnow().isoformat()
                        }
                        await repo._role_permission_col.insert_one(permission)
                        created_permissions.append(permission)
        
        logger.info(f"Permissions updated for role {role_id} by user {current_user.get('email')}, {len(created_permissions)} permissions set")
        return {
            "message": "Role permissions updated successfully",
            "permissions": created_permissions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to set permissions for role {role_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set role permissions: {str(e)}"
        )


# Helper function to add role management to repository
async def init_default_roles():
    """Initialize default roles in the repository"""
    try:
        # Check if repo has _store (InMemoryRepo) or use MongoDB methods
        if hasattr(repo, '_store'):
            # InMemoryRepo
            roles_store = repo._store.setdefault("__roles__", {})
            
            if not roles_store:
                # Create default admin role
                admin_role = Role(
                    name="System Administrator",
                    role_group=RoleGroup.ADMIN, 
                    company_id="global",
                    is_default=True,
                    status="active"
                )
                await repo.save_role(admin_role)
                
                # Create default host role
                host_role = Role(
                    name="Host Manager",
                    role_group=RoleGroup.HOST,
                    company_id="1",  # Default company
                    is_default=True,
                    status="active"
                )
                await repo.save_role(host_role)
                
                # Create default advertiser role
                advertiser_role = Role(
                    name="Advertiser User",
                    role_group=RoleGroup.ADVERTISER,
                    company_id="2",  # Default company
                    is_default=True,
                    status="active"
                )
                await repo.save_role(advertiser_role)
        else:
            # MongoRepo - check if roles already exist
            from app.repo import MongoRepo
            if isinstance(repo, MongoRepo):
                count = await repo._role_col.count_documents({})
                if count == 0:
                    # Create default admin role
                    admin_role = Role(
                        name="System Administrator",
                        role_group=RoleGroup.ADMIN, 
                        company_id="global",
                        is_default=True,
                        status="active"
                    )
                    await repo.save_role(admin_role)
                    
                    # Create default host role
                    host_role = Role(
                        name="Host Manager",
                        role_group=RoleGroup.HOST,
                        company_id="1",  # Default company
                        is_default=True,
                        status="active"
                    )
                    await repo.save_role(host_role)
                    
                    # Create default advertiser role
                    advertiser_role = Role(
                        name="Advertiser User",
                        role_group=RoleGroup.ADVERTISER,
                        company_id="2",  # Default company
                        is_default=True,
                        status="active"
                    )
                    await repo.save_role(advertiser_role)
            
    except Exception as e:
        logger.error(f"Failed to initialize default roles: {e}", exc_info=True)