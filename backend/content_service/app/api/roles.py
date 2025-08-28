from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Dict, Optional
from datetime import datetime

from app.models import Role, RolePermission, User
from app.repo import repo
from app.auth import get_current_user

router = APIRouter(prefix="/roles", tags=["roles"])


@router.get("/", response_model=List[Dict])
async def list_roles(
    company_id: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):
    """List all roles, optionally filtered by company"""
    try:
        # Check if user has permission to view roles
        if not await repo.check_user_permission(
            current_user["id"], 
            current_user.get("active_company", ""), 
            "users", 
            "view"
        ):
            # If not admin of current company, only allow viewing global roles
            if current_user.get("active_role") != "ADMIN":
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Insufficient permissions to view roles"
                )
        
        # Get all roles from repository
        all_roles = []
        role_store = repo._store.get("__roles__", {})
        
        for role_id, role_data in role_store.items():
            # Filter by company if specified
            if company_id and role_data.get("company_id") != company_id:
                continue
                
            # Get company name
            company_name = "System"
            if role_data.get("company_id") and role_data["company_id"] != "global":
                company = await repo.get_company(role_data["company_id"])
                if company:
                    company_name = company.get("name", "Unknown Company")
            
            # Count users with this role
            user_roles = repo._store.get("__user_roles__", {})
            user_count = sum(1 for ur in user_roles.values() 
                           if ur.get("role_id") == role_id and ur.get("status") == "active")
            
            # Get permissions for this role
            permissions = await get_role_permissions(role_id)
            
            role_info = {
                **role_data,
                "id": role_id,
                "company_name": company_name,
                "user_count": user_count,
                "permissions": permissions
            }
            all_roles.append(role_info)
            
        return all_roles
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch roles: {str(e)}"
        )


@router.post("/", response_model=Dict)
async def create_role(
    role_data: Dict,
    current_user: dict = Depends(get_current_user)
):
    """Create a new role"""
    try:
        # Check permissions
        if current_user.get("active_role") != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can create roles"
            )
        
        # Validate required fields
        required_fields = ["name", "role_group", "company_id"]
        for field in required_fields:
            if field not in role_data:
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
        
        return {
            "message": "Role created successfully",
            "role": saved_role
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create role: {str(e)}"
        )


@router.get("/{role_id}", response_model=Dict)
async def get_role(
    role_id: str,
    current_user: dict = Depends(get_current_user)
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
        permissions = await get_role_permissions(role_id)
        role["permissions"] = permissions
        
        return role
        
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
    current_user: dict = Depends(get_current_user)
):
    """Update an existing role"""
    try:
        # Check permissions
        if current_user.get("active_role") != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can update roles"
            )
        
        # Check if role exists
        existing_role = await repo.get_role(role_id)
        if not existing_role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        # Update role data
        updated_data = {**existing_role, **role_data}
        updated_data["updated_at"] = datetime.utcnow()
        
        # Save to repository  
        repo._store.setdefault("__roles__", {})[role_id] = updated_data
        
        return {
            "message": "Role updated successfully",
            "role": updated_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update role: {str(e)}"
        )


@router.delete("/{role_id}")
async def delete_role(
    role_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a role"""
    try:
        # Check permissions
        if current_user.get("active_role") != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can delete roles"
            )
        
        # Check if role exists
        role = await repo.get_role(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        # Check if role is default
        if role.get("is_default"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete default role"
            )
        
        # Check if role is assigned to users
        user_roles = repo._store.get("__user_roles__", {})
        assigned_count = sum(1 for ur in user_roles.values() 
                           if ur.get("role_id") == role_id and ur.get("status") == "active")
        
        if assigned_count > 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot delete role assigned to {assigned_count} user(s)"
            )
        
        # Delete role
        if role_id in repo._store.get("__roles__", {}):
            del repo._store["__roles__"][role_id]
            
        # Delete associated permissions
        permissions = repo._store.get("__role_permissions__", {})
        to_delete = [p_id for p_id, perm in permissions.items() 
                    if perm.get("role_id") == role_id]
        for p_id in to_delete:
            del permissions[p_id]
        
        return {"message": "Role deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete role: {str(e)}"
        )


@router.get("/{role_id}/permissions", response_model=List[Dict])
async def get_role_permissions(role_id: str):
    """Get permissions for a specific role"""
    try:
        permissions = []
        permission_store = repo._store.get("__role_permissions__", {})
        
        for perm_id, perm_data in permission_store.items():
            if perm_data.get("role_id") == role_id:
                permissions.append({
                    "id": perm_id,
                    "screen": perm_data.get("screen"),
                    "permissions": perm_data.get("permissions", [])
                })
        
        return permissions
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch role permissions: {str(e)}"
        )


@router.post("/{role_id}/permissions", response_model=Dict)
async def set_role_permissions(
    role_id: str,
    permissions_data: List[Dict],
    current_user: dict = Depends(get_current_user)
):
    """Set permissions for a role"""
    try:
        # Check permissions
        if current_user.get("active_role") != "ADMIN":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only administrators can manage role permissions"
            )
        
        # Check if role exists
        role = await repo.get_role(role_id)
        if not role:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Role not found"
            )
        
        # Clear existing permissions for this role
        permission_store = repo._store.setdefault("__role_permissions__", {})
        to_delete = [p_id for p_id, perm in permission_store.items() 
                    if perm.get("role_id") == role_id]
        for p_id in to_delete:
            del permission_store[p_id]
        
        # Add new permissions
        created_permissions = []
        for perm_data in permissions_data:
            if perm_data.get("permissions"):  # Only create if permissions exist
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
        
        return {
            "message": "Role permissions updated successfully",
            "permissions": created_permissions
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to set role permissions: {str(e)}"
        )


# Helper function to add role management to repository
async def init_default_roles():
    """Initialize default roles in the repository"""
    try:
        # Check if default roles already exist
        roles_store = repo._store.setdefault("__roles__", {})
        
        if not roles_store:
            # Create default admin role
            admin_role = Role(
                name="System Administrator",
                role_group="ADMIN", 
                company_id="global",
                is_default=True,
                status="active"
            )
            await repo.save_role(admin_role)
            
            # Create default host role
            host_role = Role(
                name="Host Manager",
                role_group="HOST",
                company_id="1",  # Default company
                is_default=True,
                status="active"
            )
            await repo.save_role(host_role)
            
            # Create default advertiser role
            advertiser_role = Role(
                name="Advertiser User",
                role_group="ADVERTISER",
                company_id="2",  # Default company
                is_default=True,
                status="active"
            )
            await repo.save_role(advertiser_role)
            
    except Exception as e:
        print(f"Failed to initialize default roles: {e}")