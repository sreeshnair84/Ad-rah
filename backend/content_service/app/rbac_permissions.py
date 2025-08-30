"""
RBAC Permission Management Module
Handles default role permissions creation and management
"""

from app.models import RolePermission, Screen, Permission
from app.repo import repo


async def create_default_role_permissions(admin_role_id: str, host_role_id: str, advertiser_role_id: str):
    """Create default permissions for each role and screen combination"""
    try:
        # Clear existing permissions first
        await clear_role_permissions(admin_role_id, host_role_id, advertiser_role_id)
        
        # Admin permissions - full access to all screens
        admin_permissions = [
            {"screen": Screen.DASHBOARD, "permissions": [Permission.VIEW, Permission.EDIT, Permission.DELETE, Permission.ACCESS]},
            {"screen": Screen.USERS, "permissions": [Permission.VIEW, Permission.EDIT, Permission.DELETE, Permission.ACCESS]},
            {"screen": Screen.COMPANIES, "permissions": [Permission.VIEW, Permission.EDIT, Permission.DELETE, Permission.ACCESS]},
            {"screen": Screen.CONTENT, "permissions": [Permission.VIEW, Permission.EDIT, Permission.DELETE, Permission.ACCESS]},
            {"screen": Screen.MODERATION, "permissions": [Permission.VIEW, Permission.EDIT, Permission.DELETE, Permission.ACCESS]},
            {"screen": Screen.ANALYTICS, "permissions": [Permission.VIEW, Permission.EDIT, Permission.DELETE, Permission.ACCESS]},
            {"screen": Screen.SETTINGS, "permissions": [Permission.VIEW, Permission.EDIT, Permission.DELETE, Permission.ACCESS]},
            {"screen": Screen.BILLING, "permissions": [Permission.VIEW, Permission.EDIT, Permission.DELETE, Permission.ACCESS]}
        ]
        
        # Host permissions - manage content, screens, analytics for their venues
        host_permissions = [
            {"screen": Screen.DASHBOARD, "permissions": [Permission.VIEW, Permission.ACCESS]},
            {"screen": Screen.CONTENT, "permissions": [Permission.VIEW, Permission.EDIT, Permission.ACCESS]},
            {"screen": Screen.MODERATION, "permissions": [Permission.VIEW, Permission.EDIT, Permission.ACCESS]},
            {"screen": Screen.ANALYTICS, "permissions": [Permission.VIEW, Permission.ACCESS]},
            {"screen": Screen.SETTINGS, "permissions": [Permission.VIEW, Permission.EDIT, Permission.ACCESS]}
        ]
        
        # Advertiser permissions - manage their own content and view analytics
        advertiser_permissions = [
            {"screen": Screen.DASHBOARD, "permissions": [Permission.VIEW, Permission.ACCESS]},
            {"screen": Screen.CONTENT, "permissions": [Permission.VIEW, Permission.EDIT, Permission.ACCESS]},
            {"screen": Screen.ANALYTICS, "permissions": [Permission.VIEW, Permission.ACCESS]},
            {"screen": Screen.SETTINGS, "permissions": [Permission.VIEW, Permission.ACCESS]}
        ]
        
        # Create admin role permissions
        for perm_data in admin_permissions:
            permission = RolePermission(
                role_id=admin_role_id,
                screen=perm_data["screen"].value,  # Convert enum to string
                permissions=[p.value for p in perm_data["permissions"]]  # Convert enum list to strings
            )
            await repo.save_role_permission(permission)
            
        # Create host role permissions
        for perm_data in host_permissions:
            permission = RolePermission(
                role_id=host_role_id,
                screen=perm_data["screen"].value,  # Convert enum to string
                permissions=[p.value for p in perm_data["permissions"]]  # Convert enum list to strings
            )
            await repo.save_role_permission(permission)
            
        # Create advertiser role permissions
        for perm_data in advertiser_permissions:
            permission = RolePermission(
                role_id=advertiser_role_id,
                screen=perm_data["screen"].value,  # Convert enum to string
                permissions=[p.value for p in perm_data["permissions"]]  # Convert enum list to strings
            )
            await repo.save_role_permission(permission)
            
        print("Default role permissions created successfully")
        
    except Exception as e:
        print(f"Error creating default role permissions: {e}")
        raise


async def clear_role_permissions(*role_ids):
    """Clear existing permissions for the given role IDs"""
    try:
        if hasattr(repo, '_store'):
            # InMemoryRepo
            permission_store = repo._store.get("__role_permissions__", {})
            to_delete = [p_id for p_id, perm in permission_store.items() 
                        if perm.get("role_id") in role_ids]
            for p_id in to_delete:
                del permission_store[p_id]
            print(f"Cleared permissions for {len(to_delete)} existing permissions")
        else:
            # MongoRepo
            from app.repo import MongoRepo
            if isinstance(repo, MongoRepo):
                result = await repo._role_permission_col.delete_many({"role_id": {"$in": list(role_ids)}})
                print(f"Cleared permissions for {result.deleted_count} existing permissions")
    except Exception as e:
        print(f"Error clearing role permissions: {e}")