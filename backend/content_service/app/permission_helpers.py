"""
Permission Helper Functions
Provides utility functions for checking user permissions and roles
"""

from typing import List, Dict, Optional
from app.repo import repo


async def user_has_role(user: Dict, role_name: str, company_id: Optional[str] = None) -> bool:
    """Check if user has a specific role, optionally within a company"""
    user_roles = user.get("roles", [])
    
    for role in user_roles:
        if role.get("role") == role_name:
            if company_id is None or role.get("company_id") == company_id:
                return True
    return False


async def user_has_any_role(user: Dict, role_names: List[str], company_id: Optional[str] = None) -> bool:
    """Check if user has any of the specified roles"""
    for role_name in role_names:
        if await user_has_role(user, role_name, company_id):
            return True
    return False


async def user_has_permission(user: Dict, screen: str, permission: str, company_id: Optional[str] = None) -> bool:
    """Check if user has specific permission for a screen"""
    user_id = user.get("id")
    if not user_id:
        return False
    
    # If company_id not specified, check all user's companies
    if company_id is None:
        user_roles = user.get("roles", [])
        for role in user_roles:
            role_company_id = role.get("company_id", "")
            if await repo.check_user_permission(user_id, role_company_id, screen, permission):
                return True
        return False
    else:
        return await repo.check_user_permission(user_id, company_id, screen, permission)


async def get_user_companies(user: Dict) -> List[str]:
    """Get list of company IDs that the user belongs to"""
    user_roles = user.get("roles", [])
    return list(set(role.get("company_id") for role in user_roles if role.get("company_id")))


async def is_admin_user(user: Dict) -> bool:
    """Check if user has admin privileges"""
    return await user_has_role(user, "ADMIN")


async def is_host_user(user: Dict, company_id: Optional[str] = None) -> bool:
    """Check if user is a host"""
    return await user_has_role(user, "HOST", company_id)


async def is_advertiser_user(user: Dict, company_id: Optional[str] = None) -> bool:
    """Check if user is an advertiser"""
    return await user_has_role(user, "ADVERTISER", company_id)