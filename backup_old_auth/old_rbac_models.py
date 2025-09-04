"""
Enhanced RBAC Models for Digital Signage Platform
==================================================

This module defines the Role-Based Access Control models that match the specific
requirements for the digital signage platform:

1. Super User (Platform Admin) - Global access, not linked to companies
2. Company Roles: Admin, Reviewer, Editor, Viewer
3. Device Roles for content pulling
4. Content sharing and visibility controls
5. Soft/hard delete mechanisms
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal, Any
from datetime import datetime
from enum import Enum
import uuid


class UserType(str, Enum):
    """Core user types in the system"""
    SUPER_USER = "SUPER_USER"      # Platform administrator
    COMPANY_USER = "COMPANY_USER"   # Belongs to a company
    DEVICE_USER = "DEVICE_USER"     # Device authentication


class CompanyType(str, Enum):
    """Types of companies in the system"""
    HOST = "HOST"                   # Manages physical displays/screens
    ADVERTISER = "ADVERTISER"       # Creates and manages ad content


class CompanyRole(str, Enum):
    """Roles within a company (HOST or ADVERTISER)"""
    ADMIN = "ADMIN"                 # Full company management
    REVIEWER = "REVIEWER"           # Content review and approval
    EDITOR = "EDITOR"              # Content creation and editing
    VIEWER = "VIEWER"              # Read-only access with upload capability


class Permission(str, Enum):
    """Granular permissions for different actions"""
    # Content permissions
    CONTENT_VIEW = "content_view"
    CONTENT_CREATE = "content_create"
    CONTENT_EDIT = "content_edit"
    CONTENT_DELETE = "content_delete"
    CONTENT_APPROVE = "content_approve"
    CONTENT_SHARE = "content_share"
    
    # User management
    USER_VIEW = "user_view"
    USER_CREATE = "user_create"
    USER_EDIT = "user_edit"
    USER_DELETE = "user_delete"
    
    # Company management
    COMPANY_VIEW = "company_view"
    COMPANY_CREATE = "company_create"
    COMPANY_EDIT = "company_edit"
    COMPANY_DELETE = "company_delete"
    
    # Device management
    DEVICE_VIEW = "device_view"
    DEVICE_CREATE = "device_create"
    DEVICE_EDIT = "device_edit"
    DEVICE_DELETE = "device_delete"
    DEVICE_CONTROL = "device_control"
    
    # Analytics and monitoring
    ANALYTICS_VIEW = "analytics_view"
    ANALYTICS_EXPORT = "analytics_export"
    MODERATION_VIEW = "moderation_view"
    MODERATION_ACTION = "moderation_action"
    
    # System administration
    SYSTEM_SETTINGS = "system_settings"
    PLATFORM_ADMIN = "platform_admin"


class ContentDeleteType(str, Enum):
    """Types of content deletion"""
    SOFT_DELETE = "soft_delete"     # Mark as deleted but keep in database
    HARD_DELETE = "hard_delete"     # Permanently remove from database


class ContentVisibility(str, Enum):
    """Content visibility levels"""
    PRIVATE = "private"             # Only visible to owner company
    SHARED = "shared"               # Shared with specific companies
    PUBLIC = "public"               # Visible to all (rare, admin only)


# Enhanced User Model
class EnhancedUser(BaseModel):
    """Enhanced user model with proper RBAC support"""
    id: Optional[str] = None
    name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    user_type: UserType = UserType.COMPANY_USER
    status: str = "active"
    hashed_password: Optional[str] = None
    
    # Company association (None for SUPER_USER)
    primary_company_id: Optional[str] = None
    
    # Authentication metadata
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None
    email_verified: bool = False
    last_login: Optional[datetime] = None
    login_attempts: int = 0
    locked_until: Optional[datetime] = None
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None  # Who created this user


# Enhanced Company Model
class EnhancedCompany(BaseModel):
    """Enhanced company model with RBAC metadata"""
    id: Optional[str] = None
    name: str
    type: CompanyType
    address: str
    city: str
    country: str
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    
    # Registration and identification
    organization_code: str = Field(default_factory=lambda: f"ORG-{uuid.uuid4().hex[:8].upper()}")
    business_license: Optional[str] = None
    
    # Status and settings
    status: str = "active"
    max_users: int = 50  # User limit for the company
    max_devices: int = 100  # Device limit for the company
    
    # Content sharing settings (for HOST companies)
    allow_content_sharing: bool = True
    shared_with_companies: List[str] = Field(default_factory=list)
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None  # Super user who created this company


# Enhanced Role Model
class EnhancedRole(BaseModel):
    """Enhanced role model with detailed permissions"""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    
    # Role classification
    user_type: UserType  # What type of user this role is for
    company_role: Optional[CompanyRole] = None  # For company users
    company_id: Optional[str] = None  # None for SUPER_USER roles
    
    # Permission set
    permissions: List[Permission] = Field(default_factory=list)
    
    # Role metadata
    is_default: bool = False  # Default role for new users in company
    is_system_role: bool = False  # System-defined role (cannot be deleted)
    max_users: Optional[int] = None  # Maximum users with this role
    
    # Status and audit
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None


# Device Model for authentication
class Device(BaseModel):
    """Device model for digital signage display units"""
    id: Optional[str] = None
    name: str
    company_id: str  # Must belong to a company
    api_key: str  # For device authentication
    
    # Device properties
    device_type: str = "display"  # display, kiosk, etc.
    location: Optional[str] = None
    screen_resolution: Optional[str] = None
    hardware_info: Optional[str] = None
    
    # Status and connectivity
    status: str = "inactive"  # active, inactive, maintenance
    last_heartbeat: Optional[datetime] = None
    online: bool = False
    
    # Configuration
    auto_content_refresh: bool = True
    refresh_interval: int = 300  # seconds
    allowed_content_types: List[str] = Field(default_factory=lambda: ["image", "video", "html"])
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None  # User who registered this device


# User Role Assignment
class EnhancedUserRole(BaseModel):
    """Enhanced user role assignment with context"""
    id: Optional[str] = None
    user_id: str
    role_id: str
    company_id: Optional[str] = None  # None for super user roles
    
    # Assignment metadata
    is_primary: bool = False  # Primary role for the user
    assigned_by: str  # Who assigned this role
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Optional restrictions
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    
    # Status
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Content Sharing Model
class ContentShare(BaseModel):
    """Model for content sharing between companies"""
    id: Optional[str] = None
    content_id: str
    owner_company_id: str  # Company that owns the content
    shared_with_company_id: str  # Company receiving access
    
    # Sharing metadata
    shared_by: str  # User who shared the content
    shared_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    
    # Permissions for shared content
    can_edit: bool = False
    can_reshare: bool = False
    can_download: bool = True
    
    # Status
    status: str = "active"  # active, revoked, expired
    revoked_by: Optional[str] = None
    revoked_at: Optional[datetime] = None


# Enhanced Content Model with RBAC
class EnhancedContent(BaseModel):
    """Enhanced content model with RBAC and sharing support"""
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    filename: str
    content_type: str
    size: int
    
    # Ownership and access
    owner_company_id: str
    created_by: str  # User who uploaded
    visibility: ContentVisibility = ContentVisibility.PRIVATE
    
    # Content metadata
    duration_seconds: Optional[int] = None
    categories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    content_rating: Optional[str] = None
    
    # Moderation and approval
    moderation_status: str = "pending"  # pending, approved, rejected, quarantine
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    moderation_notes: Optional[str] = None
    
    # Scheduling
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # Analytics
    view_count: int = 0
    impression_count: int = 0
    
    # Deletion tracking
    deleted: bool = False
    deleted_type: Optional[ContentDeleteType] = None
    deleted_by: Optional[str] = None
    deleted_at: Optional[datetime] = None
    deletion_reason: Optional[str] = None
    
    # Audit fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Device Authentication Model
class DeviceRole(BaseModel):
    """Device role for content pulling"""
    id: Optional[str] = None
    device_id: str
    company_id: str  # Company the device belongs to
    
    # Device metadata
    device_name: str
    device_type: str = "display"
    location: Optional[str] = None
    
    # Permissions
    can_pull_content: bool = True
    can_report_analytics: bool = True
    allowed_content_types: List[str] = Field(default_factory=list)
    
    # Authentication
    api_key: str
    last_authenticated: Optional[datetime] = None
    
    # Status
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    registered_by: str  # User who registered the device


# Permission Check Models
class PermissionContext(BaseModel):
    """Context for permission checking"""
    user_id: str
    company_id: Optional[str] = None
    target_company_id: Optional[str] = None  # For cross-company operations
    resource_type: str  # content, user, device, etc.
    resource_id: Optional[str] = None
    action: str  # view, create, edit, delete, etc.


class PermissionResult(BaseModel):
    """Result of permission check"""
    allowed: bool
    reason: Optional[str] = None
    required_permissions: List[Permission] = Field(default_factory=list)
    user_permissions: List[Permission] = Field(default_factory=list)


# Audit Log Model
class AuditLog(BaseModel):
    """Audit log for tracking user actions"""
    id: Optional[str] = None
    user_id: str
    company_id: Optional[str] = None
    action: str
    resource_type: str
    resource_id: Optional[str] = None
    
    # Action details
    details: Dict = Field(default_factory=dict)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Result
    success: bool = True
    error_message: Optional[str] = None
    
    # Timestamp
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Request/Response Models for API
class CreateCompanyUserRequest(BaseModel):
    """Request to create a user within a company"""
    name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    company_role: CompanyRole
    send_invitation: bool = True


class ShareContentRequest(BaseModel):
    """Request to share content with another company"""
    content_id: str
    target_company_id: str
    can_edit: bool = False
    can_reshare: bool = False
    can_download: bool = True
    expires_at: Optional[datetime] = None


class DeleteContentRequest(BaseModel):
    """Request to delete content"""
    content_id: str
    delete_type: ContentDeleteType = ContentDeleteType.SOFT_DELETE
    reason: Optional[str] = None


class RolePermissionUpdate(BaseModel):
    """Update role permissions"""
    role_id: str
    permissions: List[Permission]
    reason: Optional[str] = None


# Default Permission Sets
class DefaultPermissions:
    """Default permission sets for different roles"""
    
    SUPER_USER = [
        Permission.PLATFORM_ADMIN,
        Permission.COMPANY_CREATE,
        Permission.COMPANY_VIEW,
        Permission.COMPANY_EDIT,
        Permission.COMPANY_DELETE,
        Permission.USER_VIEW,
        Permission.USER_CREATE,
        Permission.USER_EDIT,
        Permission.USER_DELETE,
        Permission.CONTENT_VIEW,
        Permission.CONTENT_DELETE,
        Permission.DEVICE_VIEW,
        Permission.DEVICE_DELETE,
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_EXPORT,
        Permission.MODERATION_VIEW,
        Permission.MODERATION_ACTION,
        Permission.SYSTEM_SETTINGS
    ]
    
    COMPANY_ADMIN = [
        Permission.USER_VIEW,
        Permission.USER_CREATE,
        Permission.USER_EDIT,
        Permission.USER_DELETE,
        Permission.CONTENT_VIEW,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_EDIT,
        Permission.CONTENT_DELETE,
        Permission.CONTENT_APPROVE,
        Permission.CONTENT_SHARE,
        Permission.DEVICE_VIEW,
        Permission.DEVICE_CREATE,
        Permission.DEVICE_EDIT,
        Permission.DEVICE_CONTROL,
        Permission.ANALYTICS_VIEW,
        Permission.ANALYTICS_EXPORT,
        Permission.MODERATION_VIEW,
        Permission.MODERATION_ACTION
    ]
    
    REVIEWER = [
        Permission.CONTENT_VIEW,
        Permission.CONTENT_APPROVE,
        Permission.DEVICE_VIEW,
        Permission.DEVICE_CONTROL,
        Permission.ANALYTICS_VIEW,
        Permission.MODERATION_VIEW,
        Permission.MODERATION_ACTION,
        Permission.USER_VIEW
    ]
    
    EDITOR = [
        Permission.CONTENT_VIEW,
        Permission.CONTENT_CREATE,
        Permission.CONTENT_EDIT,
        Permission.DEVICE_VIEW,
        Permission.ANALYTICS_VIEW,
        Permission.USER_VIEW
    ]
    
    VIEWER = [
        Permission.CONTENT_VIEW,
        Permission.CONTENT_CREATE,  # Can upload
        Permission.DEVICE_VIEW,
        Permission.ANALYTICS_VIEW,
        Permission.USER_VIEW
    ]
    
    DEVICE = [
        Permission.CONTENT_VIEW,  # Can pull content
        Permission.ANALYTICS_VIEW  # Can report analytics
    ]


# Utility functions for permission checking
def get_default_permissions(user_type: UserType, company_role: Optional[CompanyRole] = None) -> List[Permission]:
    """Get default permissions for a user type and role"""
    if user_type == UserType.SUPER_USER:
        return DefaultPermissions.SUPER_USER
    elif user_type == UserType.DEVICE_USER:
        return DefaultPermissions.DEVICE
    elif user_type == UserType.COMPANY_USER and company_role:
        if company_role == CompanyRole.ADMIN:
            return DefaultPermissions.COMPANY_ADMIN
        elif company_role == CompanyRole.REVIEWER:
            return DefaultPermissions.REVIEWER
        elif company_role == CompanyRole.EDITOR:
            return DefaultPermissions.EDITOR
        elif company_role == CompanyRole.VIEWER:
            return DefaultPermissions.VIEWER
    
    return []  # No permissions by default


def check_permission_compatibility(user_permissions: List[Permission], required_permissions: List[Permission]) -> bool:
    """Check if user has all required permissions"""
    user_perms_set = set(user_permissions)
    required_perms_set = set(required_permissions)
    return required_perms_set.issubset(user_perms_set)
