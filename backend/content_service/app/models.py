from __future__ import annotations
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
    model_config = {"from_attributes": True}
    
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
    user_type: Optional[str] = "COMPANY_USER"  # SUPER_USER, COMPANY_USER, DEVICE_USER
    company_id: Optional[str] = None  # Company the user belongs to (None for SUPER_USER)
    roles: List[UserRole] = []
    oauth_provider: Optional[str] = None  # For OAuth support
    oauth_id: Optional[str] = None
    is_active: bool = True
    is_deleted: bool = False  # Soft delete flag
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
    model_config = {"from_attributes": True}
    
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
    company: Optional[Dict] = None  # Primary company information
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

    # AI Moderation fields
    ai_moderation_status: Optional[str] = None  # pending, approved, rejected, needs_review
    ai_confidence_score: Optional[float] = None
    ai_analysis: Optional[Dict] = None
    ai_processed_at: Optional[datetime] = None

    # Review workflow fields
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    approval_status: Optional[str] = None  # pending, approved, rejected

    # Content metadata enhancements
    production_notes: Optional[str] = None  # Notes for editors during overlay creation
    usage_guidelines: Optional[str] = None  # Guidelines for content usage
    priority_level: str = "medium"  # low, medium, high, urgent

    # File metadata
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    preview_url: Optional[str] = None

    # Compliance and legal
    copyright_info: Optional[str] = None
    license_type: Optional[str] = None  # commercial, creative_commons, proprietary
    usage_rights: Optional[str] = None

    # Performance tracking
    download_count: int = 0
    share_count: int = 0
    error_count: int = 0


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


class ContentUploadRequest(BaseModel):
    # Basic content information
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)

    # Categorization
    categories: List[str] = Field(default_factory=list, max_items=5)
    tags: List[str] = Field(default_factory=list, max_items=20)
    content_rating: Optional[str] = Field(None, pattern="^(G|PG|PG-13|R|NC-17)$")

    # Targeting and scheduling
    target_age_min: Optional[int] = Field(None, ge=0, le=100)
    target_age_max: Optional[int] = Field(None, ge=0, le=100)
    target_gender: Optional[str] = Field(None, pattern="^(male|female|all)$")
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

    # Production information
    production_notes: Optional[str] = Field(None, max_length=500)
    usage_guidelines: Optional[str] = Field(None, max_length=500)
    priority_level: str = Field("medium", pattern="^(low|medium|high|urgent)$")

    # Legal and compliance
    copyright_info: Optional[str] = Field(None, max_length=300)
    license_type: Optional[str] = Field(None, pattern="^(commercial|creative_commons|proprietary)$")
    usage_rights: Optional[str] = Field(None, max_length=300)

    # File metadata (set during upload)
    duration_seconds: Optional[int] = Field(None, ge=0)


class UploadResponse(BaseModel):
    filename: str
    status: str
    message: Optional[str] = None
    content_id: Optional[str] = None
    ai_moderation_required: bool = False
    estimated_review_time: Optional[str] = None


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
    
    # Additional fields for enhanced registration
    device_type: Optional[str] = None  # e.g., "KIOSK", "DISPLAY", "TABLET"
    capabilities: Optional["DeviceCapabilities"] = None  # Forward reference
    fingerprint: Optional["DeviceFingerprint"] = None    # Forward reference
    location_description: Optional[str] = None


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
    # Resolution capabilities
    max_resolution_width: int = 1920
    max_resolution_height: int = 1080
    
    # Content support capabilities (Flutter format)
    supports_video: Optional[bool] = True
    supports_images: Optional[bool] = True
    supports_web_content: Optional[bool] = True
    
    # Legacy format support
    supported_formats: List[str] = ["mp4", "jpg", "png", "webp"]
    
    # Hardware capabilities
    has_touch: bool = False
    has_audio: bool = True
    has_camera: bool = False
    
    # System resources (Flutter format)
    storage_capacity_gb: Optional[int] = None  # Flutter sends this
    storage_gb: Optional[int] = None  # Legacy field
    ram_gb: Optional[int] = None
    cpu_info: Optional[str] = None
    os_version: Optional[str] = None
    
    # Network and interaction (Flutter format)
    network_interfaces: Optional[List[str]] = None
    interactive_features: Optional[List[str]] = None


class DeviceFingerprint(BaseModel):
    """Unique device identification"""
    hardware_id: str  # CPU ID, motherboard serial, etc.
    mac_addresses: List[str] = []  # All network interfaces
    
    # Flutter format fields
    platform: Optional[str] = None  # Flutter sends this
    device_model: Optional[str] = None  # Flutter sends this
    os_version: Optional[str] = None  # Flutter sends this
    
    # Legacy fields
    device_serial: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None  # Same as device_model
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


class ContentLayoutCreate(BaseModel):
    name: str
    description: Optional[str] = None
    company_id: str
    zones: List[Dict]  # List of zone configurations
    layout_type: str = "grid"  # grid, custom, template
    is_template: bool = False
    tags: List[str] = []


class ContentLayoutUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    zones: Optional[List[Dict]] = None
    layout_type: Optional[str] = None
    is_template: Optional[bool] = None
    tags: Optional[List[str]] = None


class AdvertiserCampaignCreate(BaseModel):
    name: str
    description: Optional[str] = None
    advertiser_company_id: str
    content_ids: List[str]
    target_screens: List[str] = []
    budget: Optional[float] = None
    start_date: datetime
    end_date: datetime
    targeting_rules: Optional[Dict] = None
    status: str = "draft"


class ContentDeploymentCreate(BaseModel):
    content_id: str
    device_ids: List[str]
    layout_id: Optional[str] = None
    deployment_type: str = "immediate"  # immediate, scheduled
    scheduled_time: Optional[datetime] = None
    priority: int = 1
    auto_retry: bool = True
    max_retries: int = 3


class DeviceAnalytics(BaseModel):
    device_id: str
    content_id: Optional[str] = None
    event_type: str  # impression, interaction, completion, error
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_seconds: Optional[float] = None
    estimated_revenue: float = 0.0
    user_interactions: int = 0
    technical_issues: List[str] = []
    location_data: Optional[Dict] = None
    device_info: Optional[Dict] = None


class ProximityDetection(BaseModel):
    device_id: str
    content_id: str
    user_distance: float  # meters
    detection_method: str  # bluetooth, wifi, camera, motion
    confidence_score: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    user_demographics: Optional[Dict] = None


class AnalyticsQuery(BaseModel):
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    device_ids: Optional[List[str]] = None
    content_ids: Optional[List[str]] = None
    event_types: Optional[List[str]] = None
    group_by: Optional[str] = None  # device, content, date, hour


class AnalyticsSummary(BaseModel):
    total_impressions: int = 0
    total_revenue: float = 0.0
    total_interactions: int = 0
    unique_devices: int = 0
    avg_engagement_time: float = 0.0
    top_performing_content: List[Dict] = []
    revenue_by_category: Dict[str, float] = {}
    hourly_breakdown: List[Dict] = []


# Content History and Audit Tracking Models
class ContentDeleteType(str, Enum):
    """Types of content deletion"""
    SOFT_DELETE = "soft_delete"  # Mark as deleted but keep data
    HARD_DELETE = "hard_delete"  # Permanently remove data


class ContentHistoryEventType(str, Enum):
    """Types of events in content lifecycle"""
    UPLOADED = "uploaded"
    AI_MODERATION_STARTED = "ai_moderation_started"
    AI_MODERATION_COMPLETED = "ai_moderation_completed"
    MANUAL_REVIEW_ASSIGNED = "manual_review_assigned"
    APPROVED = "approved"
    REJECTED = "rejected"
    UPDATED = "updated"
    SCHEDULED = "scheduled"
    DEPLOYED = "deployed"
    DISPLAYED = "displayed"
    ERROR = "error"
    DELETED = "deleted"
    SHARED = "shared"
    OVERLAY_CREATED = "overlay_created"
    OVERLAY_UPDATED = "overlay_updated"
    ANALYTICS_RECORDED = "analytics_recorded"


class ContentHistory(BaseModel):
    """Comprehensive audit log for content lifecycle events"""
    id: Optional[str] = None
    content_id: str
    event_type: ContentHistoryEventType
    event_timestamp: datetime = Field(default_factory=datetime.utcnow)

    # User who triggered the event
    triggered_by_user_id: Optional[str] = None
    triggered_by_user_name: Optional[str] = None
    triggered_by_user_type: Optional[str] = None  # SUPER_USER, COMPANY_USER, DEVICE_USER

    # System information
    triggered_by_system: Optional[str] = None  # AI_MODERATION, SCHEDULER, SYNC_SERVICE
    device_id: Optional[str] = None  # For device-related events
    company_id: str  # Company context

    # Event details
    event_details: Dict = Field(default_factory=dict)  # Flexible JSON for event-specific data
    previous_state: Optional[Dict] = None  # State before the event
    new_state: Optional[Dict] = None  # State after the event

    # Metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None

    # Error tracking
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None

    # Performance metrics
    processing_time_ms: Optional[int] = None
    payload_size_bytes: Optional[int] = None

    # Compliance and legal
    gdpr_compliant: bool = True
    retention_expires_at: Optional[datetime] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)


class ContentHistoryQuery(BaseModel):
    """Query parameters for content history lookup"""
    content_ids: Optional[List[str]] = None
    event_types: Optional[List[ContentHistoryEventType]] = None
    user_ids: Optional[List[str]] = None
    device_ids: Optional[List[str]] = None
    company_id: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_system_events: bool = True
    include_error_events: bool = True
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)
    sort_order: str = Field("desc", pattern="^(asc|desc)$")


class ContentLifecycleSummary(BaseModel):
    """Summary view of content's complete lifecycle"""
    content_id: str
    content_title: str
    current_status: str
    company_id: str
    company_name: str

    # Lifecycle timestamps
    uploaded_at: Optional[datetime] = None
    ai_moderation_completed_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    first_deployed_at: Optional[datetime] = None
    last_displayed_at: Optional[datetime] = None

    # Performance metrics
    total_deployments: int = 0
    total_displays: int = 0
    total_errors: int = 0
    avg_processing_time_ms: Optional[float] = None

    # User involvement
    uploaded_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    last_modified_by: Optional[str] = None

    # Business metrics
    estimated_revenue: float = 0.0
    total_impressions: int = 0
    engagement_score: Optional[float] = None

    # Recent activity
    recent_events: List[Dict] = Field(default_factory=list)
    last_activity_at: Optional[datetime] = None


class ContentAuditReport(BaseModel):
    """Comprehensive audit report for compliance and analysis"""
    report_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    company_id: str
    report_type: str  # daily, weekly, monthly, custom, compliance

    # Report period
    start_date: datetime
    end_date: datetime
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str  # User ID who requested the report

    # Content statistics
    total_content_uploaded: int = 0
    total_content_approved: int = 0
    total_content_rejected: int = 0
    total_content_deployed: int = 0

    # Performance metrics
    avg_approval_time_hours: Optional[float] = None
    avg_deployment_time_hours: Optional[float] = None
    success_rate_percentage: Optional[float] = None

    # User activity
    most_active_uploaders: List[Dict] = Field(default_factory=list)
    most_active_reviewers: List[Dict] = Field(default_factory=list)

    # Error analysis
    common_errors: List[Dict] = Field(default_factory=list)
    error_rate_percentage: Optional[float] = None

    # Compliance information
    gdpr_compliant_events: int = 0
    data_retention_violations: int = 0

    # Detailed breakdown
    events_by_type: Dict[str, int] = Field(default_factory=dict)
    events_by_user_type: Dict[str, int] = Field(default_factory=dict)
    daily_activity: List[Dict] = Field(default_factory=list)

    # File information
    report_file_url: Optional[str] = None
    report_format: str = "json"  # json, csv, pdf


class HistoryEventCreate(BaseModel):
    """Model for creating history events"""
    content_id: str
    event_type: ContentHistoryEventType
    event_details: Dict = Field(default_factory=dict)
    previous_state: Optional[Dict] = None
    new_state: Optional[Dict] = None
    device_id: Optional[str] = None
    triggered_by_system: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    processing_time_ms: Optional[int] = None
    payload_size_bytes: Optional[int] = None


class ContentTimelineView(BaseModel):
    """Timeline view for content history UI"""
    content_id: str
    content_title: str
    timeline_events: List[Dict] = Field(default_factory=list)
    milestones: List[Dict] = Field(default_factory=list)  # Key lifecycle points
    current_phase: str  # upload, moderation, review, approved, deployed, active
    next_expected_action: Optional[str] = None
    estimated_completion: Optional[datetime] = None
    bottlenecks: List[Dict] = Field(default_factory=list)  # Identified delays
    performance_score: Optional[float] = None  # Overall efficiency score


# Device History and Monitoring Models
class DeviceHistoryEventType(str, Enum):
    """Types of device-related events"""
    REGISTERED = "registered"
    AUTHENTICATED = "authenticated"
    HEARTBEAT = "heartbeat"
    CONTENT_SYNCED = "content_synced"
    CONTENT_DISPLAYED = "content_displayed"
    ERROR_OCCURRED = "error_occurred"
    OFFLINE = "offline"
    ONLINE = "online"
    MAINTENANCE_START = "maintenance_start"
    MAINTENANCE_END = "maintenance_end"
    CONFIGURATION_UPDATED = "configuration_updated"
    PERFORMANCE_ALERT = "performance_alert"


class DeviceHistory(BaseModel):
    """Device activity and status history"""
    id: Optional[str] = None
    device_id: str
    event_type: DeviceHistoryEventType
    event_timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Event context
    content_id: Optional[str] = None
    company_id: str
    triggered_by_user_id: Optional[str] = None

    # Device state
    device_status: Optional[str] = None
    device_location: Optional[str] = None

    # Technical details
    event_data: Dict = Field(default_factory=dict)
    system_metrics: Optional[Dict] = None  # CPU, memory, etc.
    network_info: Optional[Dict] = None

    # Error information
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    # Performance
    response_time_ms: Optional[int] = None
    bandwidth_usage_mb: Optional[float] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)


class SystemAuditLog(BaseModel):
    """System-wide audit logging for compliance"""
    id: Optional[str] = None
    audit_type: str  # USER_ACTION, SYSTEM_EVENT, SECURITY_EVENT, DATA_ACCESS
    resource_type: str  # CONTENT, USER, COMPANY, DEVICE, SYSTEM
    resource_id: str
    action_performed: str

    # Actor information
    performed_by_user_id: Optional[str] = None
    performed_by_system: Optional[str] = None
    user_role: Optional[str] = None
    company_id: Optional[str] = None

    # Technical details
    request_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None

    # Event payload
    request_data: Optional[Dict] = None
    response_data: Optional[Dict] = None
    before_state: Optional[Dict] = None
    after_state: Optional[Dict] = None

    # Security and compliance
    security_level: str = "normal"  # low, normal, high, critical
    contains_pii: bool = False
    gdpr_category: Optional[str] = None
    retention_policy: str = "standard"  # standard, extended, permanent

    # Status and outcome
    success: bool = True
    error_code: Optional[str] = None
    error_message: Optional[str] = None

    # Timing
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_ms: Optional[int] = None

    created_at: datetime = Field(default_factory=datetime.utcnow)
