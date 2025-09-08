# User Service Layer
# Enterprise-grade user management with enhanced RBAC

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import hashlib
import secrets

from app.database import get_db_service, QueryFilter, FilterOperation, QueryOptions, DatabaseResult
from app.rbac.permissions import (
    Role, UserType, PermissionManager, DEFAULT_ROLE_TEMPLATES,
    PagePermissions, is_super_admin, Page, Permission
)
from app.models import User, UserCreate, UserUpdate, UserProfile
from app.auth_service import auth_service  # Use consolidated auth service

logger = logging.getLogger(__name__)

class UserService:
    """Enhanced user management service with RBAC integration"""
    
    def __init__(self):
        self._db = None
    
    @property
    def db(self):
        """Lazy initialization of database service with error handling"""
        if self._db is None:
            try:
                self._db = get_db_service()
            except Exception as e:
                logger.error(f"Failed to get database service: {e}")
                raise RuntimeError("Database service not available. Please ensure the database is initialized.")
        return self._db
    
    async def create_user(
        self, 
        user_data: UserCreate,
        created_by: Optional[str] = None
    ) -> DatabaseResult:
        """Create a new user with role assignments"""
        try:
            # Hash password
            hashed_password = auth_service.hash_password(user_data.password)
            
            # Prepare user record
            user_record = {
                "name": user_data.name,
                "email": user_data.email.lower(),
                "phone": user_data.phone,
                "hashed_password": hashed_password,
                "user_type": UserType.COMPANY_USER.value,  # Default
                "status": "active",
                "email_verified": False,
                "login_count": 0,
                "created_by": created_by
            }
            
            # Create user
            result = await self.db.create_record("users", user_record)
            if not result.success:
                return result
            
            user_id = result.data["id"]
            
            # Create role assignments if provided
            if user_data.roles:
                for role_assignment in user_data.roles:
                    await self._assign_user_role(
                        user_id=user_id,
                        company_id=role_assignment.get("company_id"),
                        role=Role(role_assignment.get("role", Role.VIEWER.value)),
                        is_primary=role_assignment.get("is_primary", False),
                        created_by=created_by
                    )
            
            # Return user profile
            return await self.get_user_profile(user_id)
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def get_user_profile(self, user_id: str) -> DatabaseResult:
        """Get enhanced user profile with roles and permissions"""
        try:
            # Get user record - try new DB first, then fallback
            user_result = None
            try:
                user_result = await self.db.get_record("users", user_id)
            except Exception as db_error:
                logger.warning(f"New database service failed for get_user_profile, trying fallback: {db_error}")
                try:
                    from app.repo import repo
                    user_data = await repo.get_user(user_id)
                    if user_data:
                        user_result = DatabaseResult(success=True, data=user_data)
                    else:
                        user_result = DatabaseResult(success=False, error="User not found")
                except Exception as repo_error:
                    logger.error(f"Fallback repo also failed: {repo_error}")
                    return DatabaseResult(success=False, error="User lookup failed")
            
            if not user_result or not user_result.success:
                return DatabaseResult(success=False, error="User not found")
            
            user_data = user_result.data
            
            # Get user roles
            roles_result = await self._get_user_roles_with_details(user_id)
            if not roles_result.success:
                return roles_result
            
            user_roles = roles_result.data
            
            # Get accessible companies
            companies = []
            company_ids = set()
            
            for role in user_roles:
                if role.get("company_id") and role["company_id"] != "global":
                    company_ids.add(role["company_id"])
            
            for company_id in company_ids:
                try:
                    company_result = await self.db.get_record("companies", company_id)
                    if company_result.success:
                        companies.append(company_result.data)
                except Exception as company_error:
                    logger.warning(f"Failed to get company {company_id} from database: {company_error}")
                    # Try fallback to repo
                    try:
                        from app.repo import repo
                        company_data = await repo.get_company(company_id)
                        if company_data:
                            companies.append(company_data)
                    except Exception as repo_error:
                        logger.warning(f"Failed to get company {company_id} from repo: {repo_error}")
            
            # Build profile
            full_name = user_data.get("name", "")
            name_parts = full_name.split() if full_name else []
            first_name = name_parts[0] if name_parts else None
            last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else None
            
            # Determine user type
            user_type = "COMPANY_USER"  # Default
            if user_data.get("email") == "admin@adara.com":
                user_type = "SUPER_USER"
            elif any(role.get("role") == "DEVICE" for role in user_roles):
                user_type = "DEVICE_USER"
            
            # Get permissions from roles
            permissions = []
            company_role = None
            company_id = None
            
            # For SUPER_USER, use permissions from user record directly
            if user_type == "SUPER_USER":
                user_permissions = user_data.get("permissions", [])
                permissions = list(set(str(p) for p in user_permissions if p))
            else:
                # For other users, get permissions from roles
                for role in user_roles:
                    role_permissions = role.get("permissions", [])
                    if isinstance(role_permissions, list):
                        for perm in role_permissions:
                            if isinstance(perm, dict) and "permissions" in perm:
                                permissions.extend(perm["permissions"])
                            elif isinstance(perm, str):
                                permissions.append(perm)
                    
                    # Set company role and ID from first company role
                    if not company_role and role.get("company_id") != "global":
                        company_role = role.get("role")
                        company_id = role.get("company_id")
                
                # Remove duplicates and ensure all permissions are strings
                permissions = list(set(str(p) for p in permissions if p))
            
            profile = UserProfile(
                id=user_data.get("id") or str(user_data.get("_id")),
                email=user_data["email"],
                first_name=first_name,
                last_name=last_name,
                name=user_data.get("name"),
                phone=user_data.get("phone"),
                user_type=user_type,
                company_id=company_id,
                company_role=company_role,
                permissions=permissions,
                is_active=user_data.get("status") == "active",
                status=user_data.get("status", "active"),
                roles=user_roles,
                companies=companies,
                active_company=None,
                active_role=None,
                email_verified=user_data.get("email_verified", False),
                last_login=user_data.get("last_login"),
                failed_login_attempts=user_data.get("failed_login_attempts", 0),
                locked_until=user_data.get("locked_until"),
                created_at=user_data.get("created_at"),
                updated_at=user_data.get("updated_at"),
                created_by=user_data.get("created_by")
            )
            
            # Set active company and role (primary role or first role)
            for role in user_roles:
                if role.get("is_primary"):
                    profile.active_company = role.get("company_id")
                    profile.active_role = role.get("role")
                    break
            
            if not profile.active_company and user_roles:
                profile.active_company = user_roles[0].get("company_id")
                profile.active_role = user_roles[0].get("role")
            
            return DatabaseResult(success=True, data=profile.model_dump())
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def update_user(
        self,
        user_id: str,
        update_data: UserUpdate,
        updated_by: Optional[str] = None
    ) -> DatabaseResult:
        """Update user information"""
        try:
            # Prepare update data
            update_record = {}
            
            if update_data.name is not None:
                update_record["name"] = update_data.name
            
            if update_data.email is not None:
                update_record["email"] = update_data.email.lower()
                update_record["email_verified"] = False  # Re-verify email
            
            if update_data.phone is not None:
                update_record["phone"] = update_data.phone
            
            if update_data.status is not None:
                update_record["status"] = update_data.status
            
            if updated_by:
                update_record["updated_by"] = updated_by
            
            # Update user record
            result = await self.db.update_record("users", user_id, update_record)
            if not result.success:
                return result
            
            # Update roles if provided
            if update_data.roles is not None:
                # Remove existing roles
                await self._remove_all_user_roles(user_id)
                
                # Add new roles
                for role_assignment in update_data.roles:
                    await self._assign_user_role(
                        user_id=user_id,
                        company_id=role_assignment.get("company_id"),
                        role=Role(role_assignment.get("role", Role.VIEWER.value)),
                        is_primary=role_assignment.get("is_primary", False),
                        created_by=updated_by
                    )
            
            # Return updated profile
            return await self.get_user_profile(user_id)
            
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def delete_user(self, user_id: str, deleted_by: Optional[str] = None) -> DatabaseResult:
        """Soft delete user and remove role assignments"""
        try:
            # Soft delete user
            result = await self.db.soft_delete_record("users", user_id)
            if not result.success:
                return result
            
            # Remove all role assignments
            await self._remove_all_user_roles(user_id)
            
            return DatabaseResult(success=True, data={"deleted": True})
            
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def list_users(
        self,
        company_id: Optional[str] = None,
        role: Optional[Role] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        offset: Optional[int] = None
    ) -> DatabaseResult:
        """List users with filtering and pagination"""
        try:
            filters = []
            
            # Exclude soft-deleted users
            filters.append(QueryFilter("is_deleted", FilterOperation.EQUALS, False))
            
            if status:
                filters.append(QueryFilter("status", FilterOperation.EQUALS, status))
            
            # If filtering by company or role, we need to join with user_company_roles
            if company_id or role:
                # Get user IDs from role assignments first
                role_filters = []
                if company_id:
                    role_filters.append(QueryFilter("company_id", FilterOperation.EQUALS, company_id))
                if role:
                    role_filters.append(QueryFilter("role", FilterOperation.EQUALS, role.value))
                
                role_result = await self.db.find_records("user_company_roles", role_filters)
                if not role_result.success:
                    return role_result
                
                user_ids = [r["user_id"] for r in role_result.data]
                if user_ids:
                    filters.append(QueryFilter("id", FilterOperation.IN, user_ids))
                else:
                    # No users match the role filter
                    return DatabaseResult(success=True, data=[], count=0)
            
            options = QueryOptions(
                filters=filters,
                limit=limit,
                offset=offset,
                sort_by="created_at",
                sort_desc=True
            )
            
            return await self.db.list_records("users", options)
            
        except Exception as e:
            logger.error(f"Error listing users: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def get_user_by_email(self, email: str) -> DatabaseResult:
        """Get user by email address"""
        try:
            # Try new database service first
            try:
                filters = [
                    QueryFilter("email", FilterOperation.EQUALS, email.lower()),
                    QueryFilter("is_deleted", FilterOperation.EQUALS, False)
                ]
                
                result = await self.db.find_one_record("users", filters)
                if result.success:
                    return result
            except Exception as db_error:
                logger.warning(f"New database service failed, trying fallback: {db_error}")
            
            # Fallback to old repo system
            try:
                from app.repo import repo
                user_data = await repo.get_user_by_email(email.lower())
                if user_data:
                    return DatabaseResult(success=True, data=user_data)
                else:
                    return DatabaseResult(success=False, error="User not found")
            except Exception as repo_error:
                logger.error(f"Fallback repo also failed: {repo_error}")
                return DatabaseResult(success=False, error="User lookup failed")
            
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def authenticate_user(self, email: str, password: str) -> DatabaseResult:
        """Authenticate user with email and password"""
        try:
            # Get user by email (includes fallback logic)
            user_result = await self.get_user_by_email(email)
            if not user_result.success:
                logger.warning(f"User not found: {email}")
                return DatabaseResult(success=False, error="Invalid credentials")
            
            user_data = user_result.data
            
            # Check if user is active
            if user_data.get("status") != "active":
                logger.warning(f"User account not active: {email}")
                return DatabaseResult(success=False, error="Account is not active")
            
            # Verify password
            if not auth_service.verify_password(password, user_data.get("hashed_password")):
                logger.warning(f"Invalid password for user: {email}")
                return DatabaseResult(success=False, error="Invalid credentials")
            
            # Update last login - try both database systems
            user_id = user_data.get("id") or str(user_data.get("_id"))
            try:
                login_update = {
                    "last_login": datetime.utcnow(),
                    "login_count": user_data.get("login_count", 0) + 1
                }
                await self.db.update_record("users", user_id, login_update)
            except Exception as update_error:
                # Login time update is not critical, just log and continue
                logger.warning(f"Failed to update login time: {update_error}")
            
            # Return user profile
            # For now, always use basic profile since database service is not working properly
            logger.info("Using basic profile to avoid database service issues")
            from app.models import UserProfile
            return DatabaseResult(
                success=True,
                data=UserProfile(
                    id=user_id,
                    email=user_data["email"],
                    first_name=user_data.get("first_name"),
                    last_name=user_data.get("last_name"),
                    name=user_data.get("name"),
                    phone=user_data.get("phone"),
                    user_type="SUPER_USER" if user_data.get("email") == "admin@adara.com" else "COMPANY_USER",
                    company_id=None,
                    company_role="ADMIN" if user_data.get("email") == "admin@adara.com" else "VIEWER",
                    permissions=["*"] if user_data.get("email") == "admin@adara.com" else [],
                    is_active=user_data.get("status") == "active",
                    status=user_data.get("status", "active"),
                    roles=[],
                    companies=[]
                )
            )
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return DatabaseResult(success=False, error="Authentication failed")
    
    async def assign_user_role(
        self,
        user_id: str,
        company_id: Optional[str],
        role: Role,
        is_primary: bool = False,
        assigned_by: Optional[str] = None
    ) -> DatabaseResult:
        """Assign role to user in a company"""
        try:
            return await self._assign_user_role(user_id, company_id, role, is_primary, assigned_by)
            
        except Exception as e:
            logger.error(f"Error assigning user role: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def remove_user_role(
        self,
        user_id: str,
        company_id: Optional[str],
        role: Role
    ) -> DatabaseResult:
        """Remove role from user in a company"""
        try:
            filters = [
                QueryFilter("user_id", FilterOperation.EQUALS, user_id),
                QueryFilter("role", FilterOperation.EQUALS, role.value)
            ]
            
            if company_id:
                filters.append(QueryFilter("company_id", FilterOperation.EQUALS, company_id))
            else:
                filters.append(QueryFilter("company_id", FilterOperation.IS_NULL))
            
            # Find existing role assignment
            role_result = await self.db.find_one_record("user_company_roles", filters)
            if not role_result.success:
                return DatabaseResult(success=False, error="Role assignment not found")
            
            # Delete role assignment
            return await self.db.delete_record("user_company_roles", role_result.data["id"])
            
        except Exception as e:
            logger.error(f"Error removing user role: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def get_user_permissions(
        self,
        user_id: str,
        company_id: Optional[str] = None
    ) -> DatabaseResult:
        """Get user's effective permissions"""
        try:
            # First get the user to check if they are SUPER_USER
            user_result = await self.get_user_profile(user_id)
            if not user_result.success:
                return user_result
            
            user_data = user_result.data
            is_super_user = user_data.get("user_type") == "SUPER_USER"
            
            # If it's a super user, grant all permissions
            if is_super_user:
                # Super admin gets all permissions on all pages
                all_permissions = []
                for page in Page:
                    page_permissions = PagePermissions(page=page, permissions={Permission.VIEW, Permission.EDIT, Permission.DELETE, Permission.MANAGE})
                    all_permissions.append(page_permissions)
                
                permissions_data = [p.to_dict() for p in all_permissions]
                return DatabaseResult(success=True, data={
                    "permissions": permissions_data,
                    "is_super_admin": True
                })
            
            # Get user roles for regular users
            roles_result = await self._get_user_roles_with_details(user_id)
            if not roles_result.success:
                return roles_result
            
            user_roles = roles_result.data
            
            # Filter by company if specified
            if company_id:
                user_roles = [r for r in user_roles if r.get("company_id") == company_id or r.get("company_id") == "global"]
            
            # Collect all permissions
            all_permissions = []
            for role_data in user_roles:
                role = Role(role_data["role"])
                permissions_json = role_data.get("permissions")
                
                if permissions_json:
                    try:
                        permissions = PermissionManager.deserialize_permissions(permissions_json)
                        all_permissions.append(permissions)
                    except:
                        # Fallback to role template
                        template = PermissionManager.get_role_template(role)
                        if template:
                            all_permissions.append(template.page_permissions)
                else:
                    # Use role template
                    template = PermissionManager.get_role_template(role)
                    if template:
                        all_permissions.append(template.page_permissions)
            
            # Merge all permissions (union)
            if all_permissions:
                merged_permissions = PermissionManager.merge_permissions(all_permissions)
            else:
                merged_permissions = []
            
            # Convert to serializable format
            permissions_data = [p.to_dict() for p in merged_permissions]
            
            return DatabaseResult(success=True, data={
                "permissions": permissions_data,
                "is_super_admin": is_super_admin(merged_permissions)
            })
            
        except Exception as e:
            logger.error(f"Error getting user permissions: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str
    ) -> DatabaseResult:
        """Change user password"""
        try:
            # Get user
            user_result = await self.db.get_record("users", user_id)
            if not user_result.success:
                return user_result
            
            user_data = user_result.data
            
            # Verify old password
            if not auth_service.verify_password(old_password, user_data.get("hashed_password")):
                return DatabaseResult(success=False, error="Invalid current password")
            
            # Hash new password
            new_hashed_password = auth_service.hash_password(new_password)
            
            # Update password
            result = await self.db.update_record("users", user_id, {
                "hashed_password": new_hashed_password
            })
            
            if result.success:
                return DatabaseResult(success=True, data={"password_changed": True})
            else:
                return result
            
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    # Private helper methods
    
    async def _assign_user_role(
        self,
        user_id: str,
        company_id: Optional[str],
        role: Role,
        is_primary: bool = False,
        created_by: Optional[str] = None
    ) -> DatabaseResult:
        """Internal method to assign role to user"""
        # Check if role assignment already exists
        filters = [
            QueryFilter("user_id", FilterOperation.EQUALS, user_id),
            QueryFilter("role", FilterOperation.EQUALS, role.value)
        ]
        
        if company_id:
            filters.append(QueryFilter("company_id", FilterOperation.EQUALS, company_id))
        else:
            filters.append(QueryFilter("company_id", FilterOperation.IS_NULL))
        
        existing_result = await self.db.find_one_record("user_company_roles", filters)
        if existing_result.success:
            return DatabaseResult(success=False, error="Role already assigned")
        
        # Get permissions for the role
        template = PermissionManager.get_role_template(role)
        permissions_json = ""
        
        if template:
            permissions_json = PermissionManager.serialize_permissions(template.page_permissions)
        
        # Create role assignment
        role_assignment = {
            "user_id": user_id,
            "company_id": company_id,
            "role": role.value,
            "permissions": permissions_json,
            "is_primary": is_primary,
            "status": "active",
            "granted_by": created_by
        }
        
        return await self.db.create_record("user_company_roles", role_assignment)
    
    async def _remove_all_user_roles(self, user_id: str) -> None:
        """Remove all role assignments for a user"""
        filters = [QueryFilter("user_id", FilterOperation.EQUALS, user_id)]
        roles_result = await self.db.find_records("user_company_roles", filters)
        
        if roles_result.success:
            for role in roles_result.data:
                await self.db.delete_record("user_company_roles", role["id"])
    
    async def _get_user_roles_with_details(self, user_id: str) -> DatabaseResult:
        """Get user roles with company details"""
        filters = [
            QueryFilter("user_id", FilterOperation.EQUALS, user_id),
            QueryFilter("status", FilterOperation.EQUALS, "active")
        ]
        
        roles_result = await self.db.find_records("user_company_roles", filters)
        if not roles_result.success:
            return roles_result
        
        # Enrich with company data
        enriched_roles = []
        for role in roles_result.data:
            enriched_role = role.copy()
            
            if role.get("company_id"):
                company_result = await self.db.get_record("companies", role["company_id"])
                if company_result.success:
                    enriched_role["company_name"] = company_result.data.get("name")
                    enriched_role["company_type"] = company_result.data.get("company_type")
            
            enriched_roles.append(enriched_role)
        
        return DatabaseResult(success=True, data=enriched_roles)