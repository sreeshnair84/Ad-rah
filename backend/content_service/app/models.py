from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Literal
from datetime import datetime
from enum import Enum
import uuid


class Permission(str, Enum):
    VIEW = "view"
    EDIT = "edit"
    DELETE = "delete"
    ACCESS = "access"


class RoleGroup(str, Enum):
    ADMIN = "ADMIN"  # Platform administrators
    HOST = "HOST"    # Host company roles
    ADVERTISER = "ADVERTISER"  # Advertiser company roles


class CompanyRoleType(str, Enum):
    """Specific role types within companies"""
    COMPANY_ADMIN = "COMPANY_ADMIN"      # Full company management
    APPROVER = "APPROVER"                # Content approval/rejection
    EDITOR = "EDITOR"                    # Content upload/editing
    VIEWER = "VIEWER"                    # Read-only access


class Screen(str, Enum):
    DASHBOARD = "dashboard"
    USERS = "users"
    COMPANIES = "companies"
    CONTENT = "content"
    MODERATION = "moderation"
    ANALYTICS = "analytics"
    SETTINGS = "settings"
    BILLING = "billing"


class CompanyCreate(BaseModel):
    name: str
    type: str = Field(..., pattern="^(HOST|ADVERTISER)$")  # HOST or ADVERTISER
    address: str
    city: str
    country: str
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    organization_code: Optional[str] = None
    status: str = "active"  # active or inactive


class CompanyUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    status: Optional[str] = None


class Company(BaseModel):
    id: Optional[str] = None
    name: str
    type: str
    address: str
    city: str
    country: str
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    organization_code: Optional[str] = None  # Unique code for device registration
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class RolePermission(BaseModel):
    id: Optional[str] = None
    role_id: str  # Reference to the role this permission belongs to
    screen: Screen
    permissions: List[Permission] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Role(BaseModel):
    id: Optional[str] = None
    name: str
    role_group: RoleGroup
    company_role_type: Optional[CompanyRoleType] = None  # Specific role type within company
    company_id: str  # Role belongs to a company  
    is_default: bool = False
    status: str = "active"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserRole(BaseModel):
    id: Optional[str] = None
    user_id: str
    company_id: str
    role_id: str  # Reference to Role instead of just role name
    is_default: bool = False
    status: str = "active"  # active or inactive
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class User(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    status: str = "active"  # active or inactive
    hashed_password: Optional[str] = None
    roles: List[UserRole] = []
    oauth_provider: Optional[str] = None  # For OAuth support
    oauth_id: Optional[str] = None
    email_verified: bool = False
    last_login: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserLogin(BaseModel):
    username: str  # This will be the email
    password: str


class UserCreate(BaseModel):
    name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    password: str
    roles: List[dict] = []  # List of {company_id: str, role_id: str, is_default: bool}
    oauth_provider: Optional[str] = None
    oauth_id: Optional[str] = None


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: Optional[str] = None
    roles: Optional[List[dict]] = None


class UserProfile(BaseModel):
    id: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    name: Optional[str] = None  # Keep for backward compatibility
    phone: Optional[str] = None
    user_type: str = "COMPANY_USER"  # SUPER_USER, COMPANY_USER, DEVICE_USER
    company_id: Optional[str] = None
    company_role: Optional[str] = None  # ADMIN, REVIEWER, EDITOR, VIEWER
    permissions: List[str] = []  # List of permission strings like "content_create"
    is_active: bool = True
    status: str = "active"  # Keep for backward compatibility
    roles: List[Dict] = []  # Expanded role information
    companies: List[Dict] = []  # Company information
    active_company: Optional[str] = None
    active_role: Optional[str] = None
    email_verified: bool = False
    last_login: Optional[datetime] = None
    failed_login_attempts: Optional[int] = 0
    locked_until: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    created_by: Optional[str] = None


class RoleCreate(BaseModel):
    name: str
    role_group: RoleGroup
    company_role_type: Optional[CompanyRoleType] = None
    company_id: str
    permissions: List[Dict] = []  # List of {screen: str, permissions: List[str]}
    is_default: bool = False


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    company_role_type: Optional[CompanyRoleType] = None
    permissions: Optional[List[Dict]] = None
    is_default: Optional[bool] = None
    status: Optional[str] = None


class PermissionCheck(BaseModel):
    user_id: str
    company_id: str
    screen: Screen
    permission: Permission


class OAuthLogin(BaseModel):
    provider: str  # google, microsoft, etc.
    code: str
    redirect_uri: str


class PasswordResetRequest(BaseModel):
    email: str


# Content Category and Tag Management Models
class ContentCategory(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None  # For hierarchical categories (e.g., Food > Fast Food)
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ContentCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[str] = None


class ContentCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[str] = None
    is_active: Optional[bool] = None


class ContentTag(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    category_id: Optional[str] = None  # Link to category
    color: Optional[str] = None  # Hex color for UI display
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ContentTagCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: Optional[str] = None
    color: Optional[str] = None


class ContentTagUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None


# Host Preference System for Ad Display
class HostPreference(BaseModel):
    id: Optional[str] = None
    company_id: str  # Host company
    screen_id: Optional[str] = None  # Specific screen, null = all screens
    allowed_categories: List[str] = []  # Category IDs
    allowed_tags: List[str] = []  # Tag IDs
    blocked_categories: List[str] = []  # Blocked category IDs
    blocked_tags: List[str] = []  # Blocked tag IDs
    max_duration_seconds: Optional[int] = None  # Max ad duration
    content_rating: Optional[str] = None  # G, PG, PG-13, R ratings
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class HostPreferenceCreate(BaseModel):
    company_id: str
    screen_id: Optional[str] = None
    allowed_categories: List[str] = []
    allowed_tags: List[str] = []
    blocked_categories: List[str] = []
    blocked_tags: List[str] = []
    max_duration_seconds: Optional[int] = None
    content_rating: Optional[str] = None


class HostPreferenceUpdate(BaseModel):
    allowed_categories: Optional[List[str]] = None
    allowed_tags: Optional[List[str]] = None
    blocked_categories: Optional[List[str]] = None
    blocked_tags: Optional[List[str]] = None
    max_duration_seconds: Optional[int] = None
    content_rating: Optional[str] = None


class PasswordReset(BaseModel):
    token: str
    new_password: str


class ContentMeta(BaseModel):
    id: Optional[str] = None
    owner_id: str
    filename: str
    content_type: str
    size: int
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "quarantine"  # quarantine -> pending -> approved -> rejected
    # Enhanced fields for categorization
    title: Optional[str] = None
    description: Optional[str] = None
    duration_seconds: Optional[int] = None  # For video content
    categories: List[str] = []  # Category IDs
    tags: List[str] = []  # Tag IDs
    content_rating: Optional[str] = None  # G, PG, PG-13, R
    # Scheduling
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    # Targeting
    target_age_min: Optional[int] = None
    target_age_max: Optional[int] = None
    target_gender: Optional[str] = None  # male, female, all
    # Analytics
    view_count: int = 0
    impression_count: int = 0
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ContentMetadata(BaseModel):
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    owner_id: str
    categories: List[str] = []  # Category IDs
    tags: List[str] = []  # Tag IDs
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    content_rating: Optional[str] = None
    target_age_min: Optional[int] = None
    target_age_max: Optional[int] = None
    target_gender: Optional[str] = None


class ContentMetadataUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    content_rating: Optional[str] = None
    target_age_min: Optional[int] = None
    target_age_max: Optional[int] = None
    target_gender: Optional[str] = None


class UploadResponse(BaseModel):
    filename: str
    status: str
    message: Optional[str] = None


class ModerationResult(BaseModel):
    content_id: str
    ai_confidence: float = Field(..., ge=0.0, le=1.0)
    action: str  # approved / quarantine / reject
    reason: Optional[str] = None


class Review(BaseModel):
    id: Optional[str] = None
    content_id: str
    ai_confidence: Optional[float] = None
    action: str  # approved | needs_review | rejected | manual_approve | manual_reject
    reviewer_id: Optional[str] = None
    notes: Optional[str] = None
    ai_analysis: Optional[Dict] = None  # AI analysis details
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UserRegistration(BaseModel):
    name: Optional[str] = None
    email: str
    phone: Optional[str] = None
    password: str


class UserInvitation(BaseModel):
    id: Optional[str] = None
    email: str
    invited_by: str  # User ID of the inviter
    company_id: str
    role_id: str
    invitation_token: str
    expires_at: datetime
    status: str = "pending"  # pending, accepted, expired, cancelled
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PasswordResetToken(BaseModel):
    id: Optional[str] = None
    user_id: str
    reset_token: str
    expires_at: datetime
    used: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Screen/Kiosk Management Models
class ScreenStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class ScreenOrientation(str, Enum):
    LANDSCAPE = "landscape"
    PORTRAIT = "portrait"


class DigitalScreen(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    company_id: str  # Owner company
    location: str  # Physical location description
    resolution_width: int = 1920
    resolution_height: int = 1080
    orientation: ScreenOrientation = ScreenOrientation.LANDSCAPE
    aspect_ratio: Optional[str] = None  # e.g., "16:9", "4:3"
    registration_key: Optional[str] = None  # Key used for registration
    status: ScreenStatus = ScreenStatus.ACTIVE
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    last_seen: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ScreenCreate(BaseModel):
    name: str
    description: Optional[str] = None
    company_id: str
    location: str
    resolution_width: int = 1920
    resolution_height: int = 1080
    orientation: ScreenOrientation = ScreenOrientation.LANDSCAPE
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None


class ScreenUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None
    resolution_width: Optional[int] = None
    resolution_height: Optional[int] = None
    orientation: Optional[ScreenOrientation] = None
    status: Optional[ScreenStatus] = None
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None


# Content Overlay Models
class ContentOverlayStatus(str, Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    SCHEDULED = "scheduled"
    EXPIRED = "expired"
    PAUSED = "paused"


class ContentOverlay(BaseModel):
    id: Optional[str] = None
    content_id: str  # Reference to uploaded content
    screen_id: str   # Reference to digital screen
    company_id: str  # Owner company
    name: str        # Layout name
    position_x: int = 0      # X position in pixels
    position_y: int = 0      # Y position in pixels
    width: int = 100         # Width in pixels
    height: int = 100        # Height in pixels
    z_index: int = 1         # Layer order (higher = front)
    opacity: float = 1.0     # 0.0 to 1.0
    rotation: float = 0.0    # Rotation in degrees
    start_time: Optional[datetime] = None  # When to start showing
    end_time: Optional[datetime] = None    # When to stop showing
    status: ContentOverlayStatus = ContentOverlayStatus.DRAFT
    created_by: str          # User who created this overlay
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ContentOverlayCreate(BaseModel):
    content_id: str
    screen_id: str
    company_id: str
    name: str
    position_x: int = 0
    position_y: int = 0
    width: int = 100
    height: int = 100
    z_index: int = 1
    opacity: float = 1.0
    rotation: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: ContentOverlayStatus = ContentOverlayStatus.DRAFT


class ContentOverlayUpdate(BaseModel):
    name: Optional[str] = None
    position_x: Optional[int] = None
    position_y: Optional[int] = None
    width: Optional[int] = None
    height: Optional[int] = None
    z_index: Optional[int] = None
    opacity: Optional[float] = None
    rotation: Optional[float] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: Optional[ContentOverlayStatus] = None


# Digital Twin Models
class DigitalTwinStatus(str, Enum):
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class DigitalTwin(BaseModel):
    id: Optional[str] = None
    name: str
    screen_id: str           # Associated physical screen
    company_id: str          # Owner company
    description: Optional[str] = None
    is_live_mirror: bool = False  # Mirror real screen content
    test_content_ids: List[str] = []  # Content being tested
    overlay_configs: List[str] = []   # Overlay configurations
    status: DigitalTwinStatus = DigitalTwinStatus.STOPPED
    created_by: str          # User who created this twin
    last_accessed: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DigitalTwinCreate(BaseModel):
    name: str
    screen_id: str
    company_id: str
    description: Optional[str] = None
    is_live_mirror: bool = False


class DigitalTwinUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_live_mirror: Optional[bool] = None
    test_content_ids: Optional[List[str]] = None
    overlay_configs: Optional[List[str]] = None
    status: Optional[DigitalTwinStatus] = None


# Screen Layout Template Models
class LayoutTemplate(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    company_id: str          # Owner company
    template_data: Dict      # JSON configuration for layout
    is_public: bool = False  # Available to all companies
    usage_count: int = 0     # How many times used
    created_by: str          # User who created template
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class LayoutTemplateCreate(BaseModel):
    name: str
    description: Optional[str] = None
    company_id: str
    template_data: Dict
    is_public: bool = False


class LayoutTemplateUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    template_data: Optional[Dict] = None
    is_public: Optional[bool] = None


# Company Registration Application Models
class CompanyApplicationStatus(str, Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"


class CompanyType(str, Enum):
    HOST = "HOST"
    ADVERTISER = "ADVERTISER"


class CompanyApplication(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    
    # Company Information
    company_name: str
    company_type: CompanyType
    business_license: str
    address: str
    city: str
    country: str
    website: Optional[str] = None
    description: str
    
    # Applicant Information  
    applicant_name: str
    applicant_email: str
    applicant_phone: str
    
    # Process Tracking
    status: CompanyApplicationStatus = CompanyApplicationStatus.PENDING
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    reviewed_at: Optional[datetime] = None
    reviewer_id: Optional[str] = None  # Track approving admin
    reviewer_notes: Optional[str] = None
    
    # Document Management
    documents: Dict[str, str] = Field(default_factory=dict)  # document_type -> file_url/path
    
    # Post-Approval Linking
    created_company_id: Optional[str] = None
    created_user_id: Optional[str] = None
    
    # Audit Fields
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CompanyApplicationCreate(BaseModel):
    company_name: str
    company_type: CompanyType
    business_license: str
    address: str
    city: str
    country: str
    website: Optional[str] = None
    description: str
    applicant_name: str
    applicant_email: str
    applicant_phone: str
    documents: Dict[str, str] = Field(default_factory=dict)


class CompanyApplicationReview(BaseModel):
    decision: Literal["approved", "rejected"]
    notes: Optional[str] = None


class CompanyApplicationUpdate(BaseModel):
    status: Optional[CompanyApplicationStatus] = None
    reviewed_at: Optional[datetime] = None
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    created_company_id: Optional[str] = None
    created_user_id: Optional[str] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


# Device Registration Models
class DeviceRegistrationCreate(BaseModel):
    device_name: str = Field(..., min_length=1, max_length=100)
    organization_code: str = Field(..., min_length=1, max_length=50)
    aspect_ratio: Optional[str] = None  # e.g., "16:9", "4:3"
    registration_key: str = Field(..., min_length=1, max_length=100)  # Secure key for registration


class DeviceRegistrationKeyCreate(BaseModel):
    company_id: str
    expires_at: Optional[datetime] = None  # Optional expiration date


class DeviceRegistrationKey(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    key: str  # The actual registration key
    company_id: str
    created_by: str  # User who generated the key
    expires_at: datetime
    used: bool = False
    used_at: Optional[datetime] = None
    used_by_device: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# Enhanced Device Authentication Models
class DeviceType(str, Enum):
    KIOSK = "kiosk"
    BILLBOARD = "billboard"
    INDOOR_SCREEN = "indoor_screen"
    OUTDOOR_SCREEN = "outdoor_screen"
    INTERACTIVE_DISPLAY = "interactive_display"


class DeviceCapabilities(BaseModel):
    """Device hardware and software capabilities"""
    max_resolution_width: int = 1920
    max_resolution_height: int = 1080
    supported_formats: List[str] = ["mp4", "jpg", "png", "webp"]
    has_touch: bool = False
    has_audio: bool = True
    has_camera: bool = False
    storage_gb: Optional[int] = None
    ram_gb: Optional[int] = None
    cpu_info: Optional[str] = None
    os_version: Optional[str] = None


class DeviceFingerprint(BaseModel):
    """Unique device identification"""
    hardware_id: str  # CPU ID, motherboard serial, etc.
    mac_addresses: List[str] = []  # All network interfaces
    device_serial: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    timezone: Optional[str] = None
    locale: Optional[str] = None


class DeviceCredentials(BaseModel):
    """Device authentication credentials"""
    id: Optional[str] = None
    device_id: str
    certificate_pem: Optional[str] = None  # Device certificate
    private_key_hash: Optional[str] = None  # Hashed private key
    jwt_token: Optional[str] = None  # Current JWT token
    jwt_expires_at: Optional[datetime] = None
    refresh_token: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_refreshed: Optional[datetime] = None
    revoked: bool = False
    revoked_at: Optional[datetime] = None


class DeviceHeartbeat(BaseModel):
    """Device health and status reporting"""
    id: Optional[str] = None
    device_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: ScreenStatus
    # System metrics
    cpu_usage: Optional[float] = None  # Percentage
    memory_usage: Optional[float] = None  # Percentage
    storage_usage: Optional[float] = None  # Percentage
    temperature: Optional[float] = None  # Celsius
    # Network metrics
    network_strength: Optional[int] = None  # Signal strength %
    bandwidth_mbps: Optional[float] = None
    # Content metrics
    current_content_id: Optional[str] = None
    content_errors: int = 0
    # Location (if available)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    # Additional data
    error_logs: List[str] = []
    performance_score: Optional[float] = None  # Overall health score


class DeviceRegistration(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    device_name: str
    organization_code: str
    registration_key: str
    device_type: DeviceType = DeviceType.KIOSK
    aspect_ratio: Optional[str] = None
    # Enhanced device information
    fingerprint: Optional[DeviceFingerprint] = None
    capabilities: Optional[DeviceCapabilities] = None
    location_description: Optional[str] = None
    # Status and tracking
    status: str = "active"
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    mac_address: Optional[str] = None
    # Security
    is_trusted: bool = False
    security_level: str = "standard"  # standard, high, maximum
    # Configuration
    auto_update: bool = True
    maintenance_window: Optional[str] = None  # "02:00-04:00"
