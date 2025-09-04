# Clean RBAC Models
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal
from datetime import datetime
from enum import Enum

class UserType(str, Enum):
    SUPER_USER = "SUPER_USER"
    COMPANY_USER = "COMPANY_USER" 
    DEVICE_USER = "DEVICE_USER"

class CompanyType(str, Enum):
    HOST = "HOST"
    ADVERTISER = "ADVERTISER"

class CompanyRole(str, Enum):
    ADMIN = "ADMIN"
    REVIEWER = "REVIEWER"
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"

class Permission(str, Enum):
    # User Management
    USER_CREATE = "user_create"
    USER_READ = "user_read"
    USER_UPDATE = "user_update"
    USER_DELETE = "user_delete"
    
    # Content Management
    CONTENT_CREATE = "content_create"
    CONTENT_READ = "content_read"
    CONTENT_UPDATE = "content_update"
    CONTENT_DELETE = "content_delete"
    CONTENT_UPLOAD = "content_upload"
    CONTENT_APPROVE = "content_approve"
    CONTENT_REJECT = "content_reject"
    CONTENT_SHARE = "content_share"
    CONTENT_MODERATE = "content_moderate"
    
    # Device Management
    DEVICE_CREATE = "device_create"
    DEVICE_READ = "device_read"
    DEVICE_UPDATE = "device_update" 
    DEVICE_DELETE = "device_delete"
    DEVICE_REGISTER = "device_register"
    DEVICE_CONTROL = "device_control"
    DEVICE_MONITOR = "device_monitor"
    
    # Analytics & Settings
    ANALYTICS_READ = "analytics_read"
    ANALYTICS_EXPORT = "analytics_export"
    ANALYTICS_REPORTS = "analytics_reports"
    SETTINGS_READ = "settings_read"
    SETTINGS_UPDATE = "settings_update"
    SETTINGS_MANAGE = "settings_manage"
    DASHBOARD_VIEW = "dashboard_view"

# Permission matrix for roles
ROLE_PERMISSIONS = {
    "SUPER_USER": list(Permission),
    "HOST": {
        CompanyRole.ADMIN: [
            Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE, Permission.USER_DELETE,
            Permission.CONTENT_CREATE, Permission.CONTENT_READ, Permission.CONTENT_UPDATE, Permission.CONTENT_DELETE,
            Permission.CONTENT_UPLOAD, Permission.CONTENT_APPROVE, Permission.CONTENT_REJECT, Permission.CONTENT_SHARE,
            Permission.CONTENT_MODERATE, Permission.DEVICE_CREATE, Permission.DEVICE_READ, Permission.DEVICE_UPDATE,
            Permission.DEVICE_DELETE, Permission.DEVICE_REGISTER, Permission.DEVICE_CONTROL, Permission.DEVICE_MONITOR,
            Permission.ANALYTICS_READ, Permission.ANALYTICS_EXPORT, Permission.ANALYTICS_REPORTS,
            Permission.SETTINGS_READ, Permission.SETTINGS_UPDATE, Permission.SETTINGS_MANAGE, Permission.DASHBOARD_VIEW
        ],
        CompanyRole.REVIEWER: [
            Permission.USER_READ, Permission.CONTENT_READ, Permission.CONTENT_APPROVE, Permission.CONTENT_REJECT,
            Permission.CONTENT_MODERATE, Permission.DEVICE_READ, Permission.DEVICE_CONTROL, Permission.DEVICE_MONITOR,
            Permission.ANALYTICS_READ, Permission.ANALYTICS_REPORTS, Permission.DASHBOARD_VIEW
        ],
        CompanyRole.EDITOR: [
            Permission.CONTENT_CREATE, Permission.CONTENT_READ, Permission.CONTENT_UPDATE, Permission.CONTENT_UPLOAD,
            Permission.ANALYTICS_READ, Permission.ANALYTICS_REPORTS, Permission.DASHBOARD_VIEW
        ],
        CompanyRole.VIEWER: [
            Permission.CONTENT_READ, Permission.CONTENT_UPLOAD, Permission.ANALYTICS_READ,
            Permission.ANALYTICS_REPORTS, Permission.DASHBOARD_VIEW
        ]
    },
    "ADVERTISER": {
        CompanyRole.ADMIN: [
            Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE, Permission.USER_DELETE,
            Permission.CONTENT_CREATE, Permission.CONTENT_READ, Permission.CONTENT_UPDATE, Permission.CONTENT_DELETE,
            Permission.CONTENT_UPLOAD, Permission.CONTENT_APPROVE, Permission.CONTENT_REJECT, Permission.CONTENT_MODERATE,
            Permission.ANALYTICS_READ, Permission.ANALYTICS_EXPORT, Permission.ANALYTICS_REPORTS,
            Permission.SETTINGS_READ, Permission.SETTINGS_UPDATE, Permission.SETTINGS_MANAGE, Permission.DASHBOARD_VIEW
        ],
        CompanyRole.REVIEWER: [
            Permission.USER_READ, Permission.CONTENT_READ, Permission.CONTENT_APPROVE, Permission.CONTENT_REJECT,
            Permission.CONTENT_MODERATE, Permission.ANALYTICS_READ, Permission.ANALYTICS_REPORTS, Permission.DASHBOARD_VIEW
        ],
        CompanyRole.EDITOR: [
            Permission.CONTENT_CREATE, Permission.CONTENT_READ, Permission.CONTENT_UPDATE, Permission.CONTENT_UPLOAD,
            Permission.ANALYTICS_READ, Permission.ANALYTICS_REPORTS, Permission.DASHBOARD_VIEW
        ],
        CompanyRole.VIEWER: [
            Permission.CONTENT_READ, Permission.CONTENT_UPLOAD, Permission.ANALYTICS_READ,
            Permission.ANALYTICS_REPORTS, Permission.DASHBOARD_VIEW
        ]
    }
}

def get_permissions_for_role(user_type: UserType, company_type: Optional[CompanyType], company_role: Optional[CompanyRole]) -> List[Permission]:
    """Get permissions for user role combination"""
    if user_type == UserType.SUPER_USER:
        return list(Permission)
    
    if user_type == UserType.DEVICE_USER:
        return []
    
    if not company_type or not company_role:
        return []
    
    return ROLE_PERMISSIONS.get(company_type.value, {}).get(company_role, [])

# Pydantic Models
class Company(BaseModel):
    id: str
    name: str
    company_type: CompanyType
    organization_code: str
    registration_key: str
    address: str
    city: str
    country: str
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    status: Literal["active", "inactive"] = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class User(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    user_type: UserType
    company_id: Optional[str] = None
    company_role: Optional[CompanyRole] = None
    permissions: List[str] = Field(default_factory=list)
    is_active: bool = True
    email_verified: bool = False
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    company: Optional[Company] = None

class UserProfile(BaseModel):
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    user_type: UserType
    company_id: Optional[str] = None
    company_role: Optional[CompanyRole] = None
    permissions: List[str] = Field(default_factory=list)
    is_active: bool = True
    email_verified: bool = False
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    company: Optional[Company] = None
    accessible_navigation: List[str] = Field(default_factory=list)
    display_name: str = ""
    role_display: str = ""

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserProfile

class UserCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    user_type: UserType = UserType.COMPANY_USER
    company_id: Optional[str] = None
    company_role: Optional[CompanyRole] = None

# Utility functions
def generate_organization_code() -> str:
    import random, string
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
    return f"ORG-{code}"

def generate_registration_key() -> str:
    import secrets, string
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(16))

def generate_api_key() -> str:
    import secrets
    return secrets.token_urlsafe(32)
