"""
Enhanced RBAC Service for Digital Signage Platform
==================================================

This service provides comprehensive Role-Based Access Control functionality:

1. Permission checking and enforcement
2. User and role management
3. Content sharing and visibility
4. Company isolation
5. Device authentication
6. Audit logging
"""

from typing import List, Optional, Dict, Tuple, Set
from datetime import datetime, timedelta
import logging

from app.rbac_models import (
    UserType, CompanyType, CompanyRole, Permission,
    User, Company, UserProfile, get_permissions_for_role
)
from app.models import ContentDeleteType, UserRole
from app.database_service import db_service
from app.repo import repo

logger = logging.getLogger(__name__)


class RBACService:
    """Enhanced RBAC Service implementing the complete permission system"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._db = None
    
    @property
    def db(self):
        """Lazy initialization of database service"""
        if self._db is None:
            self._db = db_service
        return self._db
    
    # ==================== USER MANAGEMENT ====================
    
    async def create_super_user(self, user_data: Dict, created_by: Optional[str] = None) -> Dict:
        """Create a super user (platform administrator)"""
        self.logger.info(f"Creating super user: {user_data.get('email')}")
        
        user = User(
            **user_data,
            user_type=UserType.SUPER_USER,
            primary_company_id=None,  # Super users are not linked to companies
            created_by=created_by
        )
        
        user_result = await self.db.create_record("users", user.model_dump())
        if not user_result.success:
            raise ValueError(f"Failed to create super user: {user_result.error}")
        saved_user = user_result.data
        
        # Create super user role
        super_role = await self._get_or_create_super_user_role()
        
        # Assign super user role
        user_role = UserRole(
            user_id=saved_user["id"],
            role_id=super_role["id"],
            company_id=None,
            is_primary=True,
            assigned_by=created_by or saved_user["id"]
        )
        
        user_role_result = await self.db.create_record("user_roles", user_role.model_dump())
        if not user_role_result.success:
            raise ValueError(f"Failed to assign user role: {user_role_result.error}")
        
        await self._log_audit(
            user_id=created_by or saved_user["id"],
            action="create_super_user",
            resource_type="user",
            resource_id=saved_user["id"],
            details={"email": user_data.get("email")}
        )
        
        return saved_user
    
    async def create_company_user(self, user_data: Dict, company_id: str, 
                                 company_role: CompanyRole, created_by: str) -> Dict:
        """Create a user within a company with specific role"""
        self.logger.info(f"Creating company user: {user_data.get('email')} in company {company_id}")
        
        # Verify creator has permission
        if not await self.check_permission(created_by, company_id, "user", "create"):
            raise PermissionError("Insufficient permissions to create users in this company")
        
        # Check company user limits
        company = await repo.get_company(company_id)
        if not company:
            raise ValueError("Company not found")
        
        current_users = await self._get_company_user_count(company_id)
        if current_users >= company.get("max_users", 50):
            raise ValueError("Company user limit reached")
        
        user = User(
            **user_data,
            user_type=UserType.COMPANY_USER,
            primary_company_id=company_id,
            created_by=created_by
        )
        
        saved_user = await repo.save_user(user.model_dump())
        
        # Get or create company role
        role = await self._get_or_create_company_role(company_id, company_role, company.get("type"))
        
        # Assign role
        user_role = UserRole(
            user_id=saved_user["id"],
            role_id=role["id"],
            company_id=company_id,
            is_primary=True,
            assigned_by=created_by
        )
        
        await repo.save_user_role(user_role.model_dump())
        
        await self._log_audit(
            user_id=created_by,
            company_id=company_id,
            action="create_company_user",
            resource_type="user",
            resource_id=saved_user["id"],
            details={
                "email": user_data.get("email"),
                "role": company_role.value
            }
        )
        
        return saved_user
    
    # ==================== PERMISSION CHECKING ====================
    
    async def check_permission(self, user_id: str, company_id: Optional[str], 
                             resource_type: str, action: str, 
                             target_company_id: Optional[str] = None) -> bool:
        """Check if user has permission for a specific action"""
        try:
            user = await repo.get_user(user_id)
            if not user:
                return False
            
            # Super users have all permissions
            if user.get("user_type") == UserType.SUPER_USER.value:
                return True
            
            # Get user permissions
            user_permissions = await self._get_user_permissions(user_id, company_id)
            
            # Map action to required permission
            required_permission = self._map_action_to_permission(resource_type, action)
            if not required_permission:
                return False
            
            # Check if user has required permission
            if required_permission not in user_permissions:
                return False
            
            # Additional checks for cross-company operations
            if target_company_id and target_company_id != company_id:
                return await self._check_cross_company_permission(
                    user_id, company_id, target_company_id, resource_type, action
                )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Permission check failed: {e}")
            return False
    
    async def check_content_access(self, user_id: str, content_id: str, action: str) -> bool:
        """Check if user can access specific content"""
        try:
            content = await repo.get_content_meta(content_id)
            if not content:
                return False
            
            user = await repo.get_user(user_id)
            if not user:
                return False
            
            # Super users can access all content
            if user.get("user_type") == UserType.SUPER_USER.value:
                return True
            
            owner_company_id = content.get("owner_company_id")
            user_company_id = user.get("primary_company_id")
            
            # Owner company can always access their content
            if owner_company_id == user_company_id:
                return await self.check_permission(user_id, user_company_id, "content", action)
            
            # Check if content is shared with user's company
            if await self._is_content_shared(content_id, user_company_id):
                shared_content = await self._get_content_share(content_id, user_company_id)
                
                # Check shared permissions
                if action == "edit" and not shared_content.get("can_edit", False):
                    return False
                if action == "delete":
                    return False  # Cannot delete shared content
                
                return await self.check_permission(user_id, user_company_id, "content", "view")
            
            # Check if content is public (rare case)
            if content.get("visibility") == ContentVisibility.PUBLIC.value:
                return await self.check_permission(user_id, user_company_id, "content", "view")
            
            return False
            
        except Exception as e:
            self.logger.error(f"Content access check failed: {e}")
            return False
    
    async def get_accessible_companies(self, user_id: str) -> List[Dict]:
        """Get list of companies user can access"""
        try:
            user = await repo.get_user(user_id)
            if not user:
                return []
            
            # Super users can access all companies
            if user.get("user_type") == UserType.SUPER_USER.value:
                return await repo.list_companies()
            
            # Regular users can only access their primary company
            primary_company_id = user.get("primary_company_id")
            if primary_company_id:
                company = await repo.get_company(primary_company_id)
                return [company] if company else []
            
            return []
            
        except Exception as e:
            self.logger.error(f"Failed to get accessible companies: {e}")
            return []
    
    # ==================== CONTENT SHARING ====================
    
    async def share_content(self, content_id: str, target_company_id: str, 
                           shared_by: str, permissions: Dict) -> bool:
        """Share content with another company"""
        try:
            # Verify user can share content
            if not await self.check_content_access(shared_by, content_id, "share"):
                raise PermissionError("Insufficient permissions to share content")
            
            content = await repo.get_content_meta(content_id)
            if not content:
                raise ValueError("Content not found")
            
            # Only HOST companies can share content
            owner_company = await repo.get_company(content.get("owner_company_id"))
            if owner_company.get("type") != CompanyType.HOST.value:
                raise ValueError("Only HOST companies can share content")
            
            # Check if target company allows content sharing
            target_company = await repo.get_company(target_company_id)
            if not target_company.get("allow_content_sharing", True):
                raise ValueError("Target company does not allow content sharing")
            
            # Create content share record
            content_share = ContentShare(
                content_id=content_id,
                owner_company_id=content.get("owner_company_id"),
                shared_with_company_id=target_company_id,
                shared_by=shared_by,
                **permissions
            )
            
            await repo.save_content_share(content_share.model_dump())
            
            # Update company shared_with list
            await self._update_company_sharing_list(
                content.get("owner_company_id"), 
                target_company_id
            )
            
            await self._log_audit(
                user_id=shared_by,
                company_id=content.get("owner_company_id"),
                action="share_content",
                resource_type="content",
                resource_id=content_id,
                details={
                    "target_company_id": target_company_id,
                    "permissions": permissions
                }
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Content sharing failed: {e}")
            return False
    
    async def revoke_content_sharing(self, content_id: str, target_company_id: str, 
                                   revoked_by: str) -> bool:
        """Revoke content sharing"""
        try:
            if not await self.check_content_access(revoked_by, content_id, "share"):
                raise PermissionError("Insufficient permissions to revoke content sharing")
            
            # Update share record
            share_record = await self._get_content_share(content_id, target_company_id)
            if share_record:
                share_record["status"] = "revoked"
                share_record["revoked_by"] = revoked_by
                share_record["revoked_at"] = datetime.utcnow()
                await repo.update_content_share(share_record["id"], share_record)
            
            await self._log_audit(
                user_id=revoked_by,
                action="revoke_content_sharing",
                resource_type="content",
                resource_id=content_id,
                details={"target_company_id": target_company_id}
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Content sharing revocation failed: {e}")
            return False
    
    # ==================== CONTENT MANAGEMENT ====================
    
    async def delete_content(self, content_id: str, deleted_by: str, 
                           delete_type: ContentDeleteType = ContentDeleteType.SOFT_DELETE,
                           reason: Optional[str] = None) -> bool:
        """Delete content (soft or hard delete)"""
        try:
            if not await self.check_content_access(deleted_by, content_id, "delete"):
                raise PermissionError("Insufficient permissions to delete content")
            
            content = await repo.get_content_meta(content_id)
            if not content:
                raise ValueError("Content not found")
            
            if delete_type == ContentDeleteType.SOFT_DELETE:
                # Soft delete - mark as deleted
                content["deleted"] = True
                content["deleted_type"] = delete_type.value
                content["deleted_by"] = deleted_by
                content["deleted_at"] = datetime.utcnow()
                content["deletion_reason"] = reason
                
                await repo.update_content_meta(content_id, content)
                
            else:  # Hard delete
                # Only super users and admins can hard delete
                user = await repo.get_user(deleted_by)
                if (user.get("user_type") != UserType.SUPER_USER.value and
                    not await self._has_admin_role(deleted_by, content.get("owner_company_id"))):
                    raise PermissionError("Only administrators can perform hard delete")
                
                # Actually remove from storage and database
                await repo.delete_content_meta(content_id)
                # TODO: Delete actual file from storage
            
            await self._log_audit(
                user_id=deleted_by,
                action=f"{delete_type.value}_content",
                resource_type="content",
                resource_id=content_id,
                details={"reason": reason}
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Content deletion failed: {e}")
            return False
    
    # ==================== DEVICE MANAGEMENT ====================
    
    async def register_device(self, device_data: Dict, company_id: str, 
                            registered_by: str) -> Dict:
        """Register a new device with proper RBAC"""
        try:
            if not await self.check_permission(registered_by, company_id, "device", "create"):
                raise PermissionError("Insufficient permissions to register devices")
            
            # Check device limits
            company = await repo.get_company(company_id)
            current_devices = await self._get_company_device_count(company_id)
            if current_devices >= company.get("max_devices", 100):
                raise ValueError("Company device limit reached")
            
            # Generate API key for device
            import secrets
            api_key = secrets.token_urlsafe(32)
            
            device_role = DeviceRole(
                device_id=device_data.get("device_id"),
                company_id=company_id,
                device_name=device_data.get("device_name"),
                device_type=device_data.get("device_type", "display"),
                location=device_data.get("location"),
                api_key=api_key,
                registered_by=registered_by
            )
            
            saved_device = await repo.save_device_role(device_role.model_dump())
            
            await self._log_audit(
                user_id=registered_by,
                company_id=company_id,
                action="register_device",
                resource_type="device",
                resource_id=saved_device["id"],
                details=device_data
            )
            
            return saved_device
            
        except Exception as e:
            self.logger.error(f"Device registration failed: {e}")
            raise
    
    async def authenticate_device(self, device_id: str, api_key: str) -> Optional[Dict]:
        """Authenticate device for content pulling"""
        try:
            device = await repo.get_device_by_id(device_id)
            if not device:
                return None
            
            if device.get("api_key") != api_key:
                return None
            
            if device.get("status") != "active":
                return None
            
            # Update last authenticated
            device["last_authenticated"] = datetime.utcnow()
            await repo.update_device_role(device["id"], device)
            
            return device
            
        except Exception as e:
            self.logger.error(f"Device authentication failed: {e}")
            return None
    
    # ==================== HELPER METHODS ====================
    
    async def _get_user_permissions(self, user_id: str, company_id: Optional[str]) -> Set[Permission]:
        """Get all permissions for a user"""
        try:
            user_roles = await repo.get_user_roles(user_id)
            permissions = set()
            
            for user_role in user_roles:
                if company_id and user_role.get("company_id") != company_id:
                    continue
                
                role = await repo.get_role(user_role.get("role_id"))
                if role and role.get("status") == "active":
                    role_permissions = role.get("permissions", [])
                    permissions.update(Permission(p) for p in role_permissions)
            
            return permissions
            
        except Exception as e:
            self.logger.error(f"Failed to get user permissions: {e}")
            return set()
    
    def _map_action_to_permission(self, resource_type: str, action: str) -> Optional[Permission]:
        """Map resource type and action to required permission"""
        mapping = {
            ("content", "view"): Permission.CONTENT_VIEW,
            ("content", "create"): Permission.CONTENT_CREATE,
            ("content", "edit"): Permission.CONTENT_EDIT,
            ("content", "delete"): Permission.CONTENT_DELETE,
            ("content", "approve"): Permission.CONTENT_APPROVE,
            ("content", "share"): Permission.CONTENT_SHARE,
            
            ("user", "view"): Permission.USER_VIEW,
            ("user", "create"): Permission.USER_CREATE,
            ("user", "edit"): Permission.USER_EDIT,
            ("user", "delete"): Permission.USER_DELETE,
            
            ("company", "view"): Permission.COMPANY_VIEW,
            ("company", "create"): Permission.COMPANY_CREATE,
            ("company", "edit"): Permission.COMPANY_EDIT,
            ("company", "delete"): Permission.COMPANY_DELETE,
            
            ("device", "view"): Permission.DEVICE_VIEW,
            ("device", "create"): Permission.DEVICE_CREATE,
            ("device", "edit"): Permission.DEVICE_EDIT,
            ("device", "delete"): Permission.DEVICE_DELETE,
            ("device", "control"): Permission.DEVICE_CONTROL,
            
            ("analytics", "view"): Permission.ANALYTICS_VIEW,
            ("analytics", "export"): Permission.ANALYTICS_EXPORT,
            
            ("moderation", "view"): Permission.MODERATION_VIEW,
            ("moderation", "action"): Permission.MODERATION_ACTION,
        }
        
        return mapping.get((resource_type, action))
    
    async def _get_or_create_super_user_role(self) -> Dict:
        """Get or create the super user role"""
        # Try to find existing super user role
        roles = await repo.list_roles_by_group("ADMIN")
        for role in roles:
            if (role.get("user_type") == UserType.SUPER_USER.value and
                role.get("company_id") is None):
                return role
        
        # Create new super user role
        super_role = EnhancedRole(
            name="Platform Administrator",
            description="Full platform administration access",
            user_type=UserType.SUPER_USER,
            company_role=None,
            company_id=None,
            permissions=get_default_permissions(UserType.SUPER_USER),
            is_default=True,
            is_system_role=True
        )
        
        return await repo.save_role(super_role.model_dump())
    
    async def _get_or_create_company_role(self, company_id: str, company_role: CompanyRole, 
                                        company_type: str) -> Dict:
        """Get or create a role for a company"""
        # Try to find existing role
        company_roles = await repo.get_roles_by_company(company_id)
        for role in company_roles:
            if role.get("company_role") == company_role.value:
                return role
        
        # Create new company role
        role_name = f"{company_type} {company_role.value}"
        new_role = EnhancedRole(
            name=role_name,
            description=f"{company_role.value} role for {company_type} company",
            user_type=UserType.COMPANY_USER,
            company_role=company_role,
            company_id=company_id,
            permissions=get_default_permissions(UserType.COMPANY_USER, company_role),
            is_default=(company_role == CompanyRole.ADMIN),
            is_system_role=True
        )
        
        return await repo.save_role(new_role.model_dump())
    
    async def _check_cross_company_permission(self, user_id: str, user_company_id: str,
                                            target_company_id: str, resource_type: str, 
                                            action: str) -> bool:
        """Check permissions for cross-company operations"""
        # Only super users and specific scenarios allow cross-company access
        user = await repo.get_user(user_id)
        if user.get("user_type") == UserType.SUPER_USER.value:
            return True
        
        # Check if companies have sharing relationship
        user_company = await repo.get_company(user_company_id)
        target_company = await repo.get_company(target_company_id)
        
        if (user_company.get("type") == CompanyType.HOST.value and
            target_company_id in user_company.get("shared_with_companies", [])):
            return True
        
        return False
    
    async def _is_content_shared(self, content_id: str, company_id: str) -> bool:
        """Check if content is shared with a company"""
        try:
            share = await repo.get_content_share_by_content_and_company(content_id, company_id)
            return share and share.get("status") == "active"
        except:
            return False
    
    async def _get_content_share(self, content_id: str, company_id: str) -> Optional[Dict]:
        """Get content share record"""
        try:
            return await repo.get_content_share_by_content_and_company(content_id, company_id)
        except:
            return None
    
    async def _has_admin_role(self, user_id: str, company_id: str) -> bool:
        """Check if user has admin role in company"""
        user_roles = await repo.get_user_roles(user_id)
        for user_role in user_roles:
            if user_role.get("company_id") == company_id:
                role = await repo.get_role(user_role.get("role_id"))
                if role and role.get("company_role") == CompanyRole.ADMIN.value:
                    return True
        return False
    
    async def _get_company_user_count(self, company_id: str) -> int:
        """Get current user count for a company"""
        try:
            users = await repo.get_users_by_company(company_id)
            return len(users)
        except:
            return 0
    
    async def _get_company_device_count(self, company_id: str) -> int:
        """Get current device count for a company"""
        try:
            devices = await repo.get_devices_by_company(company_id)
            return len(devices)
        except:
            return 0
    
    async def _update_company_sharing_list(self, owner_company_id: str, target_company_id: str):
        """Update company's shared_with list"""
        try:
            company = await repo.get_company(owner_company_id)
            if company:
                shared_with = company.get("shared_with_companies", [])
                if target_company_id not in shared_with:
                    shared_with.append(target_company_id)
                    company["shared_with_companies"] = shared_with
                    await repo.update_company(owner_company_id, company)
        except Exception as e:
            self.logger.error(f"Failed to update company sharing list: {e}")
    
    async def _log_audit(self, user_id: str, action: str, resource_type: str,
                        resource_id: Optional[str] = None, company_id: Optional[str] = None,
                        details: Optional[Dict] = None, success: bool = True,
                        error_message: Optional[str] = None):
        """Log audit event"""
        try:
            audit_log = AuditLog(
                user_id=user_id,
                company_id=company_id,
                action=action,
                resource_type=resource_type,
                resource_id=resource_id,
                details=details or {},
                success=success,
                error_message=error_message
            )
            
            await repo.save_audit_log(audit_log.model_dump())
            
        except Exception as e:
            self.logger.error(f"Failed to log audit event: {e}")


# Global RBAC service instance
rbac_service = RBACService()
