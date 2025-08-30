"""
RBAC Permission Management Module - Version 2
Simplified permissions creation with better debugging
"""

from app.models import RolePermission, Screen, Permission
from app.repo import repo


async def create_default_role_permissions(admin_role_id: str, host_role_id: str, advertiser_role_id: str):
    """Create default permissions for each role and screen combination"""
    try:
        print(f"Creating permissions for roles: {admin_role_id}, {host_role_id}, {advertiser_role_id}")
        
        # Clear existing permissions first
        await clear_role_permissions(admin_role_id, host_role_id, advertiser_role_id)
        
        # Admin permissions - full access to all screens
        admin_screens = [
            Screen.DASHBOARD, Screen.USERS, Screen.COMPANIES, Screen.CONTENT,
            Screen.MODERATION, Screen.ANALYTICS, Screen.SETTINGS, Screen.BILLING
        ]
        
        admin_perms = [Permission.VIEW, Permission.EDIT, Permission.DELETE, Permission.ACCESS]
        
        print(f"Creating {len(admin_screens)} admin permissions...")
        for i, screen in enumerate(admin_screens):
            permission = RolePermission(
                role_id=admin_role_id,
                screen=screen,
                permissions=admin_perms
            )
            result = await repo.save_role_permission(permission)
            print(f"  Admin permission {i+1}: {screen.value} -> {result.get('id')}")
        
        # Host permissions
        host_screens_perms = [
            (Screen.DASHBOARD, [Permission.VIEW, Permission.ACCESS]),
            (Screen.CONTENT, [Permission.VIEW, Permission.EDIT, Permission.ACCESS]),
            (Screen.MODERATION, [Permission.VIEW, Permission.EDIT, Permission.ACCESS]),
            (Screen.ANALYTICS, [Permission.VIEW, Permission.ACCESS]),
            (Screen.SETTINGS, [Permission.VIEW, Permission.EDIT, Permission.ACCESS])
        ]
        
        print(f"Creating {len(host_screens_perms)} host permissions...")
        for i, (screen, perms) in enumerate(host_screens_perms):
            permission = RolePermission(
                role_id=host_role_id,
                screen=screen,
                permissions=perms
            )
            result = await repo.save_role_permission(permission)
            print(f"  Host permission {i+1}: {screen.value} -> {result.get('id')}")
        
        # Advertiser permissions
        advertiser_screens_perms = [
            (Screen.DASHBOARD, [Permission.VIEW, Permission.ACCESS]),
            (Screen.CONTENT, [Permission.VIEW, Permission.EDIT, Permission.ACCESS]),
            (Screen.ANALYTICS, [Permission.VIEW, Permission.ACCESS]),
            (Screen.SETTINGS, [Permission.VIEW, Permission.ACCESS])
        ]
        
        print(f"Creating {len(advertiser_screens_perms)} advertiser permissions...")
        for i, (screen, perms) in enumerate(advertiser_screens_perms):
            permission = RolePermission(
                role_id=advertiser_role_id,
                screen=screen,
                permissions=perms
            )
            result = await repo.save_role_permission(permission)
            print(f"  Advertiser permission {i+1}: {screen.value} -> {result.get('id')}")
        
        print("All default role permissions created successfully")
        
    except Exception as e:
        print(f"Error creating default role permissions: {e}")
        import traceback
        traceback.print_exc()
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
            print(f"Cleared {len(to_delete)} existing permissions")
        else:
            # MongoRepo
            from app.repo import MongoRepo
            if isinstance(repo, MongoRepo):
                result = await repo._role_permission_col.delete_many({"role_id": {"$in": list(role_ids)}})
                print(f"Cleared {result.deleted_count} existing permissions")
    except Exception as e:
        print(f"Error clearing role permissions: {e}")