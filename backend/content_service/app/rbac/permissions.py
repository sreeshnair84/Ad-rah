# Enhanced RBAC System with Page-Level Permissions
# Clean, enterprise-grade role-based access control

from enum import Enum
from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
import json

class UserType(str, Enum):
    """User types in the system"""
    SUPER_USER = "SUPER_USER"        # Platform administrators
    COMPANY_USER = "COMPANY_USER"    # Company-specific users
    DEVICE_USER = "DEVICE_USER"      # Device authentication only

class Role(str, Enum):
    """Simplified role hierarchy"""
    SUPER_ADMIN = "SUPER_ADMIN"          # Full system access
    COMPANY_ADMIN = "COMPANY_ADMIN"      # Full company management
    CONTENT_MANAGER = "CONTENT_MANAGER"  # Content & device management
    REVIEWER = "REVIEWER"                # Content review & approval
    EDITOR = "EDITOR"                    # Content creation & editing
    VIEWER = "VIEWER"                    # Read-only access
    DEVICE_USER = "DEVICE_USER"          # Device-only access

class Page(str, Enum):
    """System pages/modules"""
    # Core Pages
    DASHBOARD = "dashboard"
    ANALYTICS = "analytics"
    
    # User & Company Management
    USERS = "users"
    COMPANIES = "companies"
    ROLES = "roles"
    
    # Content Management
    CONTENT = "content"
    CONTENT_UPLOAD = "content_upload"
    CONTENT_REVIEW = "content_review"
    CONTENT_APPROVAL = "content_approval"
    
    # Device Management
    DEVICES = "devices"
    DEVICE_REGISTRATION = "device_registration"
    DEVICE_MONITORING = "device_monitoring"
    
    # Advanced Features
    SCHEDULES = "schedules"
    OVERLAYS = "overlays"
    DIGITAL_TWIN = "digital_twin"
    
    # System Administration
    SYSTEM_SETTINGS = "system_settings"
    AUDIT_LOGS = "audit_logs"
    API_KEYS = "api_keys"

class Permission(str, Enum):
    """Permission types for pages"""
    VIEW = "view"           # Can view the page
    CREATE = "create"       # Can create new records
    EDIT = "edit"          # Can edit existing records
    DELETE = "delete"      # Can delete records
    APPROVE = "approve"    # Can approve content/requests
    REJECT = "reject"      # Can reject content/requests
    MANAGE = "manage"      # Full management access
    EXPORT = "export"      # Can export data
    IMPORT = "import"      # Can import data
    
    # Content specific permissions
    READ = "read"          # Can read content
    UPLOAD = "upload"      # Can upload content
    DISTRIBUTE = "distribute"  # Can distribute content to devices
    MODERATE = "moderate"  # Can moderate content

@dataclass
class PagePermissions:
    """Permissions for a specific page"""
    page: Page
    permissions: Set[Permission] = field(default_factory=set)
    
    def has_permission(self, permission: Permission) -> bool:
        """Check if specific permission is granted"""
        return permission in self.permissions
    
    def add_permission(self, permission: Permission) -> None:
        """Add a permission"""
        self.permissions.add(permission)
    
    def remove_permission(self, permission: Permission) -> None:
        """Remove a permission"""
        self.permissions.discard(permission)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "page": self.page.value,
            "permissions": [p.value for p in self.permissions]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PagePermissions':
        """Create from dictionary"""
        page = Page(data["page"])
        permissions = {Permission(p) for p in data["permissions"]}
        return cls(page=page, permissions=permissions)

@dataclass
class RoleTemplate:
    """Role template with default permissions"""
    role: Role
    name: str
    description: str
    user_type: UserType
    page_permissions: List[PagePermissions] = field(default_factory=list)
    is_system: bool = True
    
    def get_page_permissions(self, page: Page) -> Optional[PagePermissions]:
        """Get permissions for a specific page"""
        return next(
            (pp for pp in self.page_permissions if pp.page == page),
            None
        )
    
    def has_page_access(self, page: Page) -> bool:
        """Check if role has any access to a page"""
        page_perms = self.get_page_permissions(page)
        return page_perms is not None and len(page_perms.permissions) > 0
    
    def has_permission(self, page: Page, permission: Permission) -> bool:
        """Check if role has specific permission on a page"""
        page_perms = self.get_page_permissions(page)
        return page_perms is not None and page_perms.has_permission(permission)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "role": self.role.value,
            "name": self.name,
            "description": self.description,
            "user_type": self.user_type.value,
            "page_permissions": [pp.to_dict() for pp in self.page_permissions],
            "is_system": self.is_system
        }

# Default Role Templates

def super_admin_template() -> RoleTemplate:
    """Super Administrator - Full system access"""
    permissions = []
    
    # Full access to all pages
    all_permissions = {Permission.VIEW, Permission.CREATE, Permission.EDIT, Permission.DELETE, 
                      Permission.APPROVE, Permission.REJECT, Permission.MANAGE, 
                      Permission.EXPORT, Permission.IMPORT}
    
    for page in Page:
        permissions.append(PagePermissions(page=page, permissions=all_permissions.copy()))
    
    return RoleTemplate(
        role=Role.SUPER_ADMIN,
        name="Super Administrator",
        description="Full system access and management",
        user_type=UserType.SUPER_USER,
        page_permissions=permissions
    )

def company_admin_template() -> RoleTemplate:
    """Company Administrator - Full company management"""
    permissions = [
        # Dashboard & Analytics
        PagePermissions(Page.DASHBOARD, {Permission.VIEW}),
        PagePermissions(Page.ANALYTICS, {Permission.VIEW, Permission.EXPORT}),
        
        # User Management (within company)
        PagePermissions(Page.USERS, {Permission.VIEW, Permission.CREATE, Permission.EDIT, Permission.DELETE}),
        PagePermissions(Page.ROLES, {Permission.VIEW, Permission.CREATE, Permission.EDIT, Permission.DELETE}),
        
        # Company Management (own company only)
        PagePermissions(Page.COMPANIES, {Permission.VIEW, Permission.EDIT}),
        
        # Full Content Management
        PagePermissions(Page.CONTENT, {Permission.VIEW, Permission.CREATE, Permission.EDIT, Permission.DELETE, Permission.EXPORT, Permission.READ, Permission.UPLOAD, Permission.DISTRIBUTE}),
        PagePermissions(Page.CONTENT_UPLOAD, {Permission.VIEW, Permission.CREATE}),
        PagePermissions(Page.CONTENT_REVIEW, {Permission.VIEW, Permission.EDIT}),
        PagePermissions(Page.CONTENT_APPROVAL, {Permission.VIEW, Permission.APPROVE, Permission.REJECT}),
        
        # Full Device Management
        PagePermissions(Page.DEVICES, {Permission.VIEW, Permission.CREATE, Permission.EDIT, Permission.DELETE, Permission.MANAGE}),
        PagePermissions(Page.DEVICE_REGISTRATION, {Permission.VIEW, Permission.CREATE, Permission.MANAGE}),
        PagePermissions(Page.DEVICE_MONITORING, {Permission.VIEW, Permission.MANAGE}),
        
        # Advanced Features
        PagePermissions(Page.SCHEDULES, {Permission.VIEW, Permission.CREATE, Permission.EDIT, Permission.DELETE}),
        PagePermissions(Page.OVERLAYS, {Permission.VIEW, Permission.CREATE, Permission.EDIT, Permission.DELETE}),
        PagePermissions(Page.DIGITAL_TWIN, {Permission.VIEW, Permission.CREATE, Permission.EDIT, Permission.DELETE}),
        
        # Limited System Access
        PagePermissions(Page.API_KEYS, {Permission.VIEW, Permission.CREATE, Permission.EDIT})
    ]
    
    return RoleTemplate(
        role=Role.COMPANY_ADMIN,
        name="Company Administrator",
        description="Full management within company scope with access to all features",
        user_type=UserType.COMPANY_USER,
        page_permissions=permissions
    )

def content_manager_template() -> RoleTemplate:
    """Content Manager - Content and device management"""
    permissions = [
        # Dashboard & Analytics
        PagePermissions(Page.DASHBOARD, {Permission.VIEW}),
        PagePermissions(Page.ANALYTICS, {Permission.VIEW, Permission.EXPORT}),
        
        # Limited User Management
        PagePermissions(Page.USERS, {Permission.VIEW}),
        
        # Full Content Management
        PagePermissions(Page.CONTENT, {Permission.VIEW, Permission.CREATE, Permission.EDIT, Permission.DELETE}),
        PagePermissions(Page.CONTENT_UPLOAD, {Permission.VIEW, Permission.CREATE}),
        PagePermissions(Page.CONTENT_REVIEW, {Permission.VIEW, Permission.EDIT}),
        
        # Device Management
        PagePermissions(Page.DEVICES, {Permission.VIEW, Permission.CREATE, Permission.EDIT}),
        PagePermissions(Page.DEVICE_REGISTRATION, {Permission.VIEW, Permission.CREATE}),
        PagePermissions(Page.DEVICE_MONITORING, {Permission.VIEW}),
        
        # Advanced Features
        PagePermissions(Page.SCHEDULES, {Permission.VIEW, Permission.CREATE, Permission.EDIT, Permission.DELETE}),
        PagePermissions(Page.OVERLAYS, {Permission.VIEW, Permission.CREATE, Permission.EDIT, Permission.DELETE}),
        PagePermissions(Page.DIGITAL_TWIN, {Permission.VIEW, Permission.CREATE, Permission.EDIT})
    ]
    
    return RoleTemplate(
        role=Role.CONTENT_MANAGER,
        name="Content Manager",
        description="Content and device management",
        user_type=UserType.COMPANY_USER,
        page_permissions=permissions
    )

def reviewer_template() -> RoleTemplate:
    """Reviewer - Content review and approval"""
    permissions = [
        # Dashboard & Analytics
        PagePermissions(Page.DASHBOARD, {Permission.VIEW}),
        PagePermissions(Page.ANALYTICS, {Permission.VIEW}),
        
        # Content Review Focus
        PagePermissions(Page.CONTENT, {Permission.VIEW}),
        PagePermissions(Page.CONTENT_REVIEW, {Permission.VIEW, Permission.EDIT}),
        PagePermissions(Page.CONTENT_APPROVAL, {Permission.VIEW, Permission.APPROVE, Permission.REJECT}),
        
        # Device Monitoring
        PagePermissions(Page.DEVICES, {Permission.VIEW}),
        PagePermissions(Page.DEVICE_MONITORING, {Permission.VIEW})
    ]
    
    return RoleTemplate(
        role=Role.REVIEWER,
        name="Content Reviewer",
        description="Content review and approval",
        user_type=UserType.COMPANY_USER,
        page_permissions=permissions
    )

def editor_template() -> RoleTemplate:
    """Editor - Content creation and editing"""
    permissions = [
        # Dashboard
        PagePermissions(Page.DASHBOARD, {Permission.VIEW}),
        
        # Content Creation Focus
        PagePermissions(Page.CONTENT, {Permission.VIEW, Permission.CREATE, Permission.EDIT, Permission.READ, Permission.UPLOAD, Permission.DISTRIBUTE}),
        PagePermissions(Page.CONTENT_UPLOAD, {Permission.VIEW, Permission.CREATE}),
        
        # Limited Device Access
        PagePermissions(Page.DEVICES, {Permission.VIEW}),
        
        # Scheduling
        PagePermissions(Page.SCHEDULES, {Permission.VIEW, Permission.CREATE, Permission.EDIT}),
        
        # Advanced Features - Added for Host Admin and Editor access
        PagePermissions(Page.OVERLAYS, {Permission.VIEW, Permission.CREATE, Permission.EDIT}),
        PagePermissions(Page.DIGITAL_TWIN, {Permission.VIEW, Permission.CREATE, Permission.EDIT})
    ]
    
    return RoleTemplate(
        role=Role.EDITOR,
        name="Content Editor",
        description="Content creation and editing with advanced features",
        user_type=UserType.COMPANY_USER,
        page_permissions=permissions
    )

def viewer_template() -> RoleTemplate:
    """Viewer - Read-only access"""
    permissions = [
        # Dashboard & Analytics
        PagePermissions(Page.DASHBOARD, {Permission.VIEW}),
        PagePermissions(Page.ANALYTICS, {Permission.VIEW}),
        
        # Read-only Content Access
        PagePermissions(Page.CONTENT, {Permission.VIEW}),
        
        # Read-only Device Access
        PagePermissions(Page.DEVICES, {Permission.VIEW}),
        PagePermissions(Page.DEVICE_MONITORING, {Permission.VIEW}),
        
        # Read-only Schedule Access
        PagePermissions(Page.SCHEDULES, {Permission.VIEW})
    ]
    
    return RoleTemplate(
        role=Role.VIEWER,
        name="Viewer",
        description="Read-only access to company data",
        user_type=UserType.COMPANY_USER,
        page_permissions=permissions
    )

def device_user_template() -> RoleTemplate:
    """Device User - API access only"""
    permissions = [
        # Minimal device access
        PagePermissions(Page.CONTENT, {Permission.VIEW}),
        PagePermissions(Page.SCHEDULES, {Permission.VIEW})
    ]
    
    return RoleTemplate(
        role=Role.DEVICE_USER,
        name="Device User",
        description="Device API access only",
        user_type=UserType.DEVICE_USER,
        page_permissions=permissions
    )

# Role Template Registry
DEFAULT_ROLE_TEMPLATES: Dict[Role, RoleTemplate] = {
    Role.SUPER_ADMIN: super_admin_template(),
    Role.COMPANY_ADMIN: company_admin_template(),
    Role.CONTENT_MANAGER: content_manager_template(),
    Role.REVIEWER: reviewer_template(),
    Role.EDITOR: editor_template(),
    Role.VIEWER: viewer_template(),
    Role.DEVICE_USER: device_user_template()
}

class PermissionManager:
    """Permission management utilities"""
    
    @staticmethod
    def get_role_template(role: Role) -> Optional[RoleTemplate]:
        """Get default template for a role"""
        return DEFAULT_ROLE_TEMPLATES.get(role)
    
    @staticmethod
    def get_all_role_templates() -> List[RoleTemplate]:
        """Get all default role templates"""
        return list(DEFAULT_ROLE_TEMPLATES.values())
    
    @staticmethod
    def create_custom_permissions(
        base_role: Role,
        custom_permissions: Dict[str, List[str]]
    ) -> List[PagePermissions]:
        """Create custom permissions based on a base role"""
        base_template = DEFAULT_ROLE_TEMPLATES.get(base_role)
        if not base_template:
            return []
        
        # Start with base permissions
        result = []
        for page_perm in base_template.page_permissions:
            new_page_perm = PagePermissions(
                page=page_perm.page,
                permissions=page_perm.permissions.copy()
            )
            result.append(new_page_perm)
        
        # Apply custom permissions
        for page_name, permission_names in custom_permissions.items():
            try:
                page = Page(page_name)
                permissions = {Permission(p) for p in permission_names}
                
                # Find existing page permission or create new one
                page_perm = next(
                    (pp for pp in result if pp.page == page),
                    None
                )
                
                if page_perm:
                    page_perm.permissions = permissions
                else:
                    result.append(PagePermissions(page=page, permissions=permissions))
                    
            except ValueError:
                continue  # Skip invalid page/permission names
        
        return result
    
    @staticmethod
    def serialize_permissions(permissions: List[PagePermissions]) -> str:
        """Serialize permissions to JSON string"""
        data = [pp.to_dict() for pp in permissions]
        return json.dumps(data, sort_keys=True)
    
    @staticmethod
    def deserialize_permissions(permissions_json: str) -> List[PagePermissions]:
        """Deserialize permissions from JSON string"""
        try:
            data = json.loads(permissions_json)
            return [PagePermissions.from_dict(item) for item in data]
        except (json.JSONDecodeError, KeyError, ValueError):
            return []
    
    @staticmethod
    def check_permission(
        user_permissions: List[PagePermissions],
        page: Page,
        permission: Permission
    ) -> bool:
        """Check if user has specific permission on a page"""
        page_perm = next(
            (pp for pp in user_permissions if pp.page == page),
            None
        )
        return page_perm is not None and page_perm.has_permission(permission)
    
    @staticmethod
    def get_accessible_pages(
        user_permissions: List[PagePermissions],
        min_permission: Permission = Permission.VIEW
    ) -> List[Page]:
        """Get list of pages user can access with at least the minimum permission"""
        accessible = []
        for page_perm in user_permissions:
            if min_permission in page_perm.permissions:
                accessible.append(page_perm.page)
        return accessible
    
    @staticmethod
    def merge_permissions(
        permissions_list: List[List[PagePermissions]]
    ) -> List[PagePermissions]:
        """Merge multiple permission sets (union of permissions)"""
        merged: Dict[Page, Set[Permission]] = {}
        
        for permissions in permissions_list:
            for page_perm in permissions:
                if page_perm.page not in merged:
                    merged[page_perm.page] = set()
                merged[page_perm.page].update(page_perm.permissions)
        
        return [
            PagePermissions(page=page, permissions=permissions)
            for page, permissions in merged.items()
        ]

# Convenience functions for common permission checks

def can_view_page(user_permissions: List[PagePermissions], page: Page) -> bool:
    """Check if user can view a page"""
    return PermissionManager.check_permission(user_permissions, page, Permission.VIEW)

def can_create_in_page(user_permissions: List[PagePermissions], page: Page) -> bool:
    """Check if user can create in a page"""
    return PermissionManager.check_permission(user_permissions, page, Permission.CREATE)

def can_edit_in_page(user_permissions: List[PagePermissions], page: Page) -> bool:
    """Check if user can edit in a page"""
    return PermissionManager.check_permission(user_permissions, page, Permission.EDIT)

def can_delete_in_page(user_permissions: List[PagePermissions], page: Page) -> bool:
    """Check if user can delete in a page"""
    return PermissionManager.check_permission(user_permissions, page, Permission.DELETE)

def can_manage_page(user_permissions: List[PagePermissions], page: Page) -> bool:
    """Check if user can fully manage a page"""
    return PermissionManager.check_permission(user_permissions, page, Permission.MANAGE)

def is_super_admin(user_permissions: List[PagePermissions]) -> bool:
    """Check if user has super admin privileges"""
    # Super admin should have MANAGE permission on SYSTEM_SETTINGS
    return PermissionManager.check_permission(user_permissions, Page.SYSTEM_SETTINGS, Permission.MANAGE)