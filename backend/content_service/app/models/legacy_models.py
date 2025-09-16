"""
Legacy Models from main models.py file
These models are used by various parts of the system and need to be available through the models package
"""

from pydantic import BaseModel, Field
from typing import Optional, Dict, List
from datetime import datetime
from enum import Enum

# Copy the essential models directly to avoid circular imports

class ContentDeleteType(str, Enum):
    """Types of content deletion"""
    SOFT_DELETE = "soft_delete"  # Mark as deleted but keep data
    HARD_DELETE = "hard_delete"  # Permanently remove data


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


class CompanyType(str, Enum):
    HOST = "HOST"
    ADVERTISER = "ADVERTISER"


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
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    website: Optional[str] = None
    organization_code: Optional[str] = None
    status: Optional[str] = None


class RolePermission(BaseModel):
    """Many-to-many relationship between roles and permissions"""
    role_id: str
    permission: Permission
    screen: Screen
    granted: bool = True


class Role(BaseModel):
    id: Optional[str] = None
    name: str
    company_id: Optional[str] = None  # None for system roles
    role_group: RoleGroup
    company_role_type: Optional[CompanyRoleType] = None
    permissions: List[RolePermission] = []
    description: Optional[str] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class UserRole(BaseModel):
    """User role assignment with company context"""
    id: Optional[str] = None
    user_id: str
    role_id: str
    company_id: Optional[str] = None  # Company context for the role
    is_active: bool = True
    assigned_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_by: Optional[str] = None  # User ID who assigned this role


class UserLogin(BaseModel):
    email: str
    password: str


class UserCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None
    password: str
    company_id: Optional[str] = None  # Optional for registration
    role_ids: List[str] = []  # Roles to assign


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    is_active: Optional[bool] = None


class UserProfile(BaseModel):
    """Enhanced user profile with company and role information"""
    id: str
    name: str
    email: str
    phone: Optional[str] = None
    is_active: bool = True
    companies: List[Dict] = []  # Companies the user belongs to
    roles: List[Dict] = []      # Roles assigned to the user
    permissions: List[Dict] = []  # Computed permissions across all roles
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    
    # Additional profile fields
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    notification_preferences: Dict = {}
    
    # Authentication related
    email_verified: bool = False
    two_factor_enabled: bool = False
    password_changed_at: Optional[datetime] = None
    
    # Company context
    current_company_id: Optional[str] = None
    default_company_id: Optional[str] = None
    
    # Activity tracking
    login_count: int = 0
    last_active: Optional[datetime] = None
    
    # Security
    failed_login_attempts: int = 0
    locked_until: Optional[datetime] = None


class RoleCreate(BaseModel):
    name: str
    company_id: Optional[str] = None
    role_group: RoleGroup
    company_role_type: Optional[CompanyRoleType] = None
    description: Optional[str] = None
    permissions: List[RolePermission] = []


class RoleUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    permissions: Optional[List[RolePermission]] = None


class PermissionCheck(BaseModel):
    user_id: str
    permission: Permission
    screen: Screen
    company_id: Optional[str] = None


class OAuthLogin(BaseModel):
    provider: str  # google, microsoft, etc.
    access_token: str
    email: Optional[str] = None


class PasswordResetRequest(BaseModel):
    email: str


class ContentCategory(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0
    parent_id: Optional[str] = None  # For hierarchical categories
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ContentCategoryCreate(BaseModel):
    name: str
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    parent_id: Optional[str] = None


class ContentCategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None


class ContentTag(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    category_id: Optional[str] = None
    color: Optional[str] = None
    is_active: bool = True
    usage_count: int = 0
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


class HostPreference(BaseModel):
    id: Optional[str] = None
    company_id: str  # Host company ID
    category_preferences: List[str] = []  # Preferred content category IDs
    prohibited_categories: List[str] = []  # Prohibited content category IDs
    content_rating_max: str = "PG-13"  # G, PG, PG-13, R
    auto_approval: bool = False
    approval_required_keywords: List[str] = []
    prohibited_keywords: List[str] = []
    max_content_duration: Optional[int] = None  # seconds
    min_content_duration: Optional[int] = None  # seconds
    allowed_file_types: List[str] = ["jpg", "png", "gif", "mp4", "webm"]
    max_file_size: int = 50 * 1024 * 1024  # 50MB default
    business_hours_only: bool = False
    schedule_restrictions: Dict = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class HostPreferenceCreate(BaseModel):
    company_id: str
    category_preferences: List[str] = []
    prohibited_categories: List[str] = []
    content_rating_max: str = "PG-13"
    auto_approval: bool = False
    approval_required_keywords: List[str] = []
    prohibited_keywords: List[str] = []
    max_content_duration: Optional[int] = None
    min_content_duration: Optional[int] = None


class HostPreferenceUpdate(BaseModel):
    category_preferences: Optional[List[str]] = None
    prohibited_categories: Optional[List[str]] = None
    content_rating_max: Optional[str] = None
    auto_approval: Optional[bool] = None
    approval_required_keywords: Optional[List[str]] = None
    prohibited_keywords: Optional[List[str]] = None
    max_content_duration: Optional[int] = None
    min_content_duration: Optional[int] = None


class PasswordReset(BaseModel):
    token: str
    new_password: str


class ContentMeta(BaseModel):
    """Basic content metadata structure"""
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    file_type: str  # image, video, audio, etc.
    file_size: int
    duration: Optional[float] = None  # For video/audio content
    dimensions: Optional[Dict] = None  # width, height for images/videos
    thumbnail_url: Optional[str] = None
    preview_url: Optional[str] = None
    tags: List[str] = []
    category_id: Optional[str] = None
    content_rating: str = "G"  # G, PG, PG-13, R
    language: str = "en"
    created_by: str
    company_id: str
    is_active: bool = True
    moderation_status: str = "pending"  # pending, approved, rejected
    moderation_notes: Optional[str] = None
    ai_analysis: Optional[Dict] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Usage tracking
    view_count: int = 0
    download_count: int = 0
    share_count: int = 0
    
    # Scheduling
    publish_date: Optional[datetime] = None
    expire_date: Optional[datetime] = None
    
    # Geographic restrictions
    geo_restrictions: List[str] = []  # Country codes
    
    # Device compatibility
    device_compatibility: List[str] = []  # Device types
    
    # Rights and licensing
    license_type: str = "proprietary"
    copyright_info: Optional[str] = None
    usage_rights: Dict = {}
    
    # SEO and discovery
    keywords: List[str] = []
    alt_text: Optional[str] = None
    
    # Technical metadata
    encoding: Optional[str] = None
    bitrate: Optional[int] = None
    frame_rate: Optional[float] = None
    color_space: Optional[str] = None
    
    # Approval workflow
    approval_status: str = "pending"  # pending, approved, rejected, revision_requested
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    revision_notes: Optional[str] = None
    
    # Version control
    version: int = 1
    parent_id: Optional[str] = None  # For versioned content
    
    # Analytics integration
    analytics_id: Optional[str] = None
    tracking_enabled: bool = True
    
    # Content relationships
    related_content: List[str] = []  # Related content IDs
    content_series: Optional[str] = None  # Series or collection ID
    
    # Quality metrics
    quality_score: Optional[float] = None
    engagement_score: Optional[float] = None
    
    # Accessibility
    has_subtitles: bool = False
    has_audio_description: bool = False
    accessibility_features: List[str] = []
    
    # Monetization
    is_monetizable: bool = True
    pricing_tier: Optional[str] = None
    revenue_share: Optional[float] = None
    estimated_review_time: Optional[str] = None


class ContentMetadata(BaseModel):
    """Enhanced content metadata for digital signage"""
    id: Optional[str] = None
    title: str
    description: Optional[str] = None
    file_type: str
    file_size: int
    file_path: str
    file_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration: Optional[float] = None
    dimensions: Optional[Dict] = None
    tags: List[str] = []
    category_id: Optional[str] = None
    created_by: str
    company_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ContentMetadataUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None
    category_id: Optional[str] = None
    thumbnail_url: Optional[str] = None
    file_url: Optional[str] = None
    dimensions: Optional[Dict] = None
    duration: Optional[float] = None
    file_size: Optional[int] = None
    file_type: Optional[str] = None


class UploadResponse(BaseModel):
    id: str
    file_url: str
    thumbnail_url: Optional[str] = None
    file_size: int
    file_type: str
    dimensions: Optional[Dict] = None
    duration: Optional[float] = None
    status: str = "uploaded"


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
    accepted_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class PasswordResetToken(BaseModel):
    id: Optional[str] = None
    user_id: str
    token: str
    expires_at: datetime
    used_at: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ScreenStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    ERROR = "error"


class ScreenOrientation(str, Enum):
    LANDSCAPE = "landscape"
    PORTRAIT = "portrait"


class DigitalScreen(BaseModel):
    id: Optional[str] = None
    name: str
    company_id: str  # Host company
    location: str
    description: Optional[str] = None
    screen_size: str  # e.g., "55 inches"
    resolution: str  # e.g., "1920x1080"
    orientation: ScreenOrientation = ScreenOrientation.LANDSCAPE
    status: ScreenStatus = ScreenStatus.ACTIVE
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None
    last_heartbeat: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ScreenCreate(BaseModel):
    name: str
    company_id: str
    location: str
    description: Optional[str] = None
    screen_size: str
    resolution: str
    orientation: ScreenOrientation = ScreenOrientation.LANDSCAPE
    mac_address: Optional[str] = None


class ScreenUpdate(BaseModel):
    name: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    screen_size: Optional[str] = None
    resolution: Optional[str] = None
    orientation: Optional[ScreenOrientation] = None
    status: Optional[ScreenStatus] = None
    mac_address: Optional[str] = None
    ip_address: Optional[str] = None


class ContentOverlayStatus(str, Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class ContentOverlay(BaseModel):
    id: Optional[str] = None
    screen_id: str
    content_id: str
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    position: Dict = {}  # x, y, width, height
    z_index: int = 1
    opacity: float = 1.0
    status: ContentOverlayStatus = ContentOverlayStatus.DRAFT
    created_by: str
    company_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class ContentOverlayCreate(BaseModel):
    screen_id: str
    content_id: str
    title: str
    description: Optional[str] = None
    start_time: datetime
    end_time: datetime
    position: Dict = {}
    z_index: int = 1
    opacity: float = 1.0


class ContentOverlayUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    position: Optional[Dict] = None
    z_index: Optional[int] = None
    opacity: Optional[float] = None
    status: Optional[ContentOverlayStatus] = None


class DigitalTwinStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    SIMULATION = "simulation"


class DigitalTwin(BaseModel):
    id: Optional[str] = None
    screen_id: str
    name: str
    description: Optional[str] = None
    twin_data: Dict = {}  # Sensor data, status info, etc.
    last_sync: Optional[datetime] = None
    status: DigitalTwinStatus = DigitalTwinStatus.ACTIVE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DigitalTwinCreate(BaseModel):
    screen_id: str
    name: str
    description: Optional[str] = None
    twin_data: Dict = {}


class DigitalTwinUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    twin_data: Optional[Dict] = None
    status: Optional[DigitalTwinStatus] = None


class CompanyApplicationStatus(str, Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    REQUIRES_CHANGES = "requires_changes"


class CompanyApplication(BaseModel):
    id: Optional[str] = None
    applicant_email: str
    applicant_name: str
    company_name: str
    company_type: str  # HOST or ADVERTISER
    business_description: str
    website: Optional[str] = None
    phone: Optional[str] = None
    address: str
    city: str
    country: str
    business_license: Optional[str] = None
    tax_id: Optional[str] = None
    
    # Application specific fields
    status: CompanyApplicationStatus = CompanyApplicationStatus.DRAFT
    submitted_at: Optional[datetime] = None
    
    # Review process
    reviewer_id: Optional[str] = None
    reviewer_notes: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    
    # Supporting documents
    documents: List[Dict] = []  # Document metadata
    
    # For HOST applications
    venue_count: Optional[int] = None
    screen_count: Optional[int] = None
    audience_size: Optional[str] = None
    
    # For ADVERTISER applications
    advertising_budget: Optional[str] = None
    target_audience: Optional[str] = None
    campaign_types: List[str] = []
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CompanyApplicationCreate(BaseModel):
    applicant_email: str
    applicant_name: str
    company_name: str
    company_type: str
    business_description: str
    website: Optional[str] = None
    phone: Optional[str] = None
    address: str
    city: str
    country: str
    business_license: Optional[str] = None
    tax_id: Optional[str] = None
    venue_count: Optional[int] = None
    screen_count: Optional[int] = None
    audience_size: Optional[str] = None
    advertising_budget: Optional[str] = None
    target_audience: Optional[str] = None
    campaign_types: List[str] = []


class CompanyApplicationReview(BaseModel):
    status: CompanyApplicationStatus
    reviewer_notes: Optional[str] = None


class CompanyApplicationUpdate(BaseModel):
    applicant_name: Optional[str] = None
    company_name: Optional[str] = None
    business_description: Optional[str] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    business_license: Optional[str] = None
    tax_id: Optional[str] = None
    venue_count: Optional[int] = None
    screen_count: Optional[int] = None
    audience_size: Optional[str] = None
    advertising_budget: Optional[str] = None
    target_audience: Optional[str] = None
    campaign_types: Optional[List[str]] = None


class DeviceRegistrationKeyCreate(BaseModel):
    company_id: str
    description: Optional[str] = None
    expires_at: Optional[datetime] = None
    max_uses: Optional[int] = None


class DeviceRegistrationKey(BaseModel):
    id: Optional[str] = None
    company_id: str
    key: str
    description: Optional[str] = None
    created_by: str
    expires_at: Optional[datetime] = None
    max_uses: Optional[int] = None
    current_uses: int = 0
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None


class DeviceCapabilities(BaseModel):
    id: Optional[str] = None
    device_id: str
    screen_resolution: str
    supported_formats: List[str] = []
    audio_support: bool = True
    touch_support: bool = False
    camera_support: bool = False
    sensor_support: List[str] = []
    network_interfaces: List[str] = []
    storage_capacity: Optional[int] = None  # GB
    memory_capacity: Optional[int] = None   # GB
    cpu_info: Optional[str] = None
    gpu_info: Optional[str] = None
    os_info: Optional[str] = None
    browser_info: Optional[str] = None
    max_concurrent_media: int = 1
    hardware_acceleration: bool = False
    power_management: Dict = {}
    thermal_limits: Dict = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DeviceFingerprint(BaseModel):
    id: Optional[str] = None
    device_id: str
    fingerprint_hash: str
    hardware_signature: str
    software_signature: str
    network_signature: Optional[str] = None
    user_agent: Optional[str] = None
    screen_fingerprint: Optional[str] = None
    canvas_fingerprint: Optional[str] = None
    webgl_fingerprint: Optional[str] = None
    audio_fingerprint: Optional[str] = None
    timezone: Optional[str] = None
    language: Optional[str] = None
    platform: Optional[str] = None
    confidence_score: float = 0.0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen: datetime = Field(default_factory=datetime.utcnow)


class DeviceCredentials(BaseModel):
    id: Optional[str] = None
    device_id: str
    credential_type: str  # api_key, certificate, token
    credential_data: str  # encrypted
    issued_by: str
    expires_at: Optional[datetime] = None
    revoked_at: Optional[datetime] = None
    is_active: bool = True
    permissions: List[str] = []
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_used: Optional[datetime] = None


class DeviceHeartbeat(BaseModel):
    id: Optional[str] = None
    device_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: str = "online"  # online, offline, error
    system_info: Dict = {}
    performance_metrics: Dict = {}
    error_logs: List[str] = []
    network_info: Dict = {}
    location_info: Optional[Dict] = None
    battery_level: Optional[float] = None
    temperature: Optional[float] = None
    uptime: Optional[int] = None  # seconds
    memory_usage: Optional[float] = None  # percentage
    cpu_usage: Optional[float] = None     # percentage
    disk_usage: Optional[float] = None    # percentage
    active_content: List[str] = []  # Currently playing content IDs


# === DEVICE REGISTRATION AND LAYOUT MODELS ===

class DeviceType(str, Enum):
    KIOSK = "kiosk"
    BILLBOARD = "billboard"
    INDOOR_SCREEN = "indoor_screen"
    OUTDOOR_SCREEN = "outdoor_screen"
    INTERACTIVE_DISPLAY = "interactive_display"


class DeviceRegistrationCreate(BaseModel):
    device_name: str = Field(..., min_length=1, max_length=100)
    organization_code: str = Field(..., min_length=1, max_length=50)
    aspect_ratio: Optional[str] = None  # e.g., "16:9", "4:3"
    registration_key: str = Field(..., min_length=1, max_length=100)
    
    # Additional fields for enhanced registration
    device_type: Optional[str] = None
    capabilities: Optional[Dict] = None
    fingerprint: Optional[Dict] = None
    location_description: Optional[str] = None


class LayoutTemplate(BaseModel):
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    company_id: str
    template_data: Dict
    is_public: bool = False
    usage_count: int = 0
    created_by: str
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


class ContentUploadRequest(BaseModel):
    # Basic content information
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)

    # Categorization
    categories: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
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
    estimated_review_time: Optional[str] = None


# === HISTORY AND AUDIT MODELS ===

class ContentHistoryEventType(str, Enum):
    """Types of content lifecycle events"""
    UPLOADED = "uploaded"
    AI_MODERATION_STARTED = "ai_moderation_started"
    AI_MODERATION_COMPLETED = "ai_moderation_completed"
    APPROVED = "approved"
    REJECTED = "rejected"
    MODIFIED = "modified"
    DEPLOYED = "deployed"
    DISPLAYED = "displayed"
    REMOVED = "removed"
    ARCHIVED = "archived"
    ERROR_OCCURRED = "error_occurred"


class DeviceHistoryEventType(str, Enum):
    """Types of device-related events"""
    REGISTERED = "registered"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    CONTENT_DOWNLOADED = "content_downloaded"
    CONTENT_DISPLAYED = "content_displayed"
    HEARTBEAT = "heartbeat"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    UPDATED = "updated"


class ContentHistory(BaseModel):
    """Content lifecycle event tracking"""
    id: Optional[str] = None
    content_id: str
    event_type: ContentHistoryEventType
    event_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Who/what triggered the event
    triggered_by_user_id: Optional[str] = None
    triggered_by_user_name: Optional[str] = None
    triggered_by_user_type: Optional[str] = None
    triggered_by_system: Optional[str] = None
    
    # Context information
    device_id: Optional[str] = None
    company_id: str
    
    # Event details
    event_details: Dict = Field(default_factory=dict)
    previous_state: Optional[Dict] = None
    new_state: Optional[Dict] = None
    
    # Request metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    
    # Performance tracking
    processing_time_ms: Optional[int] = None
    
    # Error tracking
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    stack_trace: Optional[str] = None


class DeviceHistory(BaseModel):
    """Device event tracking"""
    id: Optional[str] = None
    device_id: str
    event_type: DeviceHistoryEventType
    event_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Related content
    content_id: Optional[str] = None
    company_id: str
    
    # Trigger information
    triggered_by_user_id: Optional[str] = None
    
    # Event data
    event_data: Dict = Field(default_factory=dict)
    system_metrics: Optional[Dict] = None
    
    # Error information
    error_code: Optional[str] = None
    error_message: Optional[str] = None


class SystemAuditLog(BaseModel):
    """System-wide audit logging for compliance"""
    id: Optional[str] = None
    audit_type: str  # "api_access", "data_modification", "user_action", etc.
    resource_type: str  # "content", "user", "company", etc.
    resource_id: str
    action_performed: str
    
    # User context
    performed_by_user_id: Optional[str] = None
    company_id: Optional[str] = None
    
    # Request/response data
    request_data: Optional[Dict] = None
    response_data: Optional[Dict] = None
    
    # Metadata
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    session_id: Optional[str] = None
    
    # Result tracking
    success: bool = True
    error_code: Optional[str] = None
    error_message: Optional[str] = None


# Request/Response Models for History API

class ContentHistoryQuery(BaseModel):
    """Query parameters for content history search"""
    content_ids: Optional[List[str]] = None
    event_types: Optional[List[ContentHistoryEventType]] = None
    user_ids: Optional[List[str]] = None
    device_ids: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    include_system_events: bool = True
    include_error_events: bool = True
    limit: int = Field(default=100, le=1000)
    offset: int = Field(default=0, ge=0)
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$")


class HistoryEventCreate(BaseModel):
    """Create a new history event"""
    content_id: str
    event_type: ContentHistoryEventType
    event_details: Optional[Dict] = None
    previous_state: Optional[Dict] = None
    new_state: Optional[Dict] = None


class ContentTimelineView(BaseModel):
    """Timeline view for a specific content item"""
    content_id: str
    content_title: str
    timeline_events: List[Dict]
    milestones: List[Dict]
    current_phase: str
    performance_score: Optional[float] = None
    bottlenecks: List[Dict] = Field(default_factory=list)


class ContentLifecycleSummary(BaseModel):
    """Comprehensive lifecycle summary for content"""
    content_id: str
    content_title: str
    current_status: str
    company_id: str
    company_name: str
    
    # Key timestamps
    uploaded_at: Optional[datetime] = None
    ai_moderation_completed_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    first_deployed_at: Optional[datetime] = None
    last_displayed_at: Optional[datetime] = None
    
    # Metrics
    total_deployments: int = 0
    total_displays: int = 0
    total_errors: int = 0
    avg_processing_time_ms: Optional[float] = None
    
    # People involved
    uploaded_by: Optional[str] = None
    reviewed_by: Optional[str] = None
    last_modified_by: Optional[str] = None
    
    # Recent activity
    recent_events: List[Dict] = Field(default_factory=list)
    last_activity_at: Optional[datetime] = None


class ContentAuditReport(BaseModel):
    """Comprehensive audit report for content management"""
    company_id: str
    report_type: str
    start_date: datetime
    end_date: datetime
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    generated_by: str
    
    # Summary statistics
    total_content_uploaded: int = 0
    total_content_approved: int = 0
    total_content_rejected: int = 0
    total_content_deployed: int = 0
    
    # Performance metrics
    avg_approval_time_hours: Optional[float] = None
    avg_deployment_time_hours: Optional[float] = None
    success_rate_percentage: Optional[float] = None
    error_rate_percentage: Optional[float] = None
    
    # Activity breakdown
    most_active_uploaders: List[Dict] = Field(default_factory=list)
    most_active_reviewers: List[Dict] = Field(default_factory=list)
    
    # Event analysis
    events_by_type: Dict = Field(default_factory=dict)
    events_by_user_type: Dict = Field(default_factory=dict)


# === ENHANCED CONTENT LAYOUT MODELS (consolidated from main models.py) ===

import uuid

class ContentLayoutType(str, Enum):
    SINGLE_ZONE = "single_zone"
    MULTI_ZONE = "multi_zone"
    DYNAMIC_OVERLAY = "dynamic_overlay"
    INTERACTIVE = "interactive"


class LayoutZone(BaseModel):
    """Individual zones within a layout"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str  # e.g., "Main Content", "Side Banner", "Bottom Ticker"
    zone_type: str  # content, advertisement, text, logo
    position_x: int
    position_y: int
    width: int
    height: int
    z_index: int = 1
    is_interactive: bool = False
    allowed_content_types: List[str] = ["image", "video", "html"]
    max_duration_seconds: Optional[int] = None
    priority: int = 1  # For content selection when multiple items available
    rotation_enabled: bool = False  # Can content rotate in this zone
    rotation_interval_seconds: int = 30


class ContentLayout(BaseModel):
    """Multi-zone content layouts for screens"""
    id: Optional[str] = None
    name: str
    description: Optional[str] = None
    company_id: str
    layout_type: ContentLayoutType
    screen_resolution_width: int = 1920
    screen_resolution_height: int = 1080
    zones: List[LayoutZone] = []
    is_template: bool = False  # Can be used by other companies
    category_preferences: Dict[str, Dict] = {}  # Zone-specific category preferences
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AdCategoryPreference(BaseModel):
    """Host preferences for ad categories in specific zones"""
    id: Optional[str] = None
    host_company_id: str
    layout_id: str
    zone_id: str
    # Category filtering
    preferred_categories: List[str] = []  # Category IDs
    blocked_categories: List[str] = []
    # Content filtering
    max_duration_seconds: Optional[int] = None
    content_rating_limit: str = "PG"  # G, PG, PG-13, R
    # Revenue settings
    min_cpm_rate: Optional[float] = None  # Minimum cost per mille
    revenue_share_percentage: float = 70.0  # Host's share of ad revenue
    # Time restrictions
    restricted_time_slots: List[Dict] = []  # Times when certain categories blocked
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class AdvertiserCampaign(BaseModel):
    """Advertiser campaign management"""
    id: Optional[str] = None
    name: str
    advertiser_company_id: str
    content_ids: List[str] = []
    # Targeting
    target_categories: List[str] = []  # Where ads should appear
    target_zones: List[str] = []  # Specific zones if known
    target_demographics: Dict = {}  # Age, gender, location preferences
    # Budget and bidding
    total_budget: float = 0.0
    daily_budget: float = 0.0
    cpm_bid: float = 0.0  # Cost per mille bid
    max_spend_per_day: float = 0.0
    # Campaign schedule
    campaign_start: datetime
    campaign_end: datetime
    # Performance tracking
    total_impressions: int = 0
    total_clicks: int = 0
    total_spend: float = 0.0
    status: str = "draft"  # draft, active, paused, completed
    created_by: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class DeviceAnalytics(BaseModel):
    """Device-level analytics and statistics"""
    id: Optional[str] = None
    device_id: str
    content_id: str
    layout_id: str
    zone_id: Optional[str] = None
    # Event data
    event_type: str  # impression, interaction, completion, error
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    duration_seconds: Optional[float] = None
    # Audience data (privacy-compliant)
    estimated_audience_count: int = 0
    detected_devices_nearby: int = 0  # Anonymized count
    audience_demographics: Dict = {}  # Aggregated, anonymized data
    # Technical metrics
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    network_quality: Optional[str] = None  # excellent, good, fair, poor
    # Revenue tracking
    estimated_revenue: float = 0.0
    cpm_rate: Optional[float] = None
    # Location context
    ambient_light: Optional[float] = None
    temperature: Optional[float] = None
    noise_level: Optional[float] = None


class ProximityDetection(BaseModel):
    """Privacy-compliant proximity detection"""
    id: Optional[str] = None
    device_id: str
    detection_method: str  # wifi, bluetooth, camera_count
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    # Anonymized data only
    detected_count: int = 0
    avg_dwell_time_seconds: Optional[float] = None
    device_types: Dict[str, int] = {}  # {"mobile": 5, "tablet": 2}
    estimated_demographics: Dict = {}  # Aggregated estimates only
    # Engagement metrics
    interaction_rate: float = 0.0
    attention_duration_seconds: float = 0.0
    # Privacy compliance
    data_anonymized: bool = True
    retention_period_days: int = 7  # How long this data is kept


class MonetizationMetrics(BaseModel):
    """Revenue and monetization tracking"""
    id: Optional[str] = None
    device_id: str
    content_id: str
    advertiser_company_id: str
    host_company_id: str
    # Time period
    date: datetime
    hour: int  # 0-23 for hourly tracking
    # Metrics
    impressions: int = 0
    clicks: int = 0
    completions: int = 0  # Full ad views
    unique_viewers: int = 0  # Estimated unique audience
    total_view_time_seconds: float = 0.0
    # Revenue
    revenue_generated: float = 0.0
    host_revenue_share: float = 0.0
    platform_revenue_share: float = 0.0
    cpm_rate: float = 0.0
    # Quality metrics
    attention_score: float = 0.0  # 0-1 score of audience engagement
    completion_rate: float = 0.0  # Percentage who watched full ad
    interaction_rate: float = 0.0  # Percentage who interacted


class ContentScheduleRule(BaseModel):
    """Advanced scheduling rules for content"""
    id: Optional[str] = None
    content_id: str
    layout_id: str
    zone_id: str
    # Time-based rules
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    days_of_week: List[int] = []  # 0=Monday, 6=Sunday
    time_slots: List[Dict] = []  # [{"start": "09:00", "end": "17:00"}]
    # Frequency rules
    max_plays_per_day: Optional[int] = None
    min_interval_seconds: int = 300  # Minimum time between plays
    priority: int = 1
    # Conditions
    weather_conditions: List[str] = []  # sunny, rainy, etc.
    audience_type: List[str] = []  # families, professionals, etc.
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ContentDeployment(BaseModel):
    """Content deployment to specific devices"""
    id: Optional[str] = None
    content_id: str
    layout_id: str
    device_ids: List[str] = []  # Target devices
    deployment_type: str = "immediate"  # immediate, scheduled
    scheduled_time: Optional[datetime] = None
    # Deployment status
    status: str = "pending"  # pending, deploying, deployed, failed
    deployment_progress: Dict = {}  # Device-specific progress
    error_logs: List[Dict] = []
    # Metadata
    deployed_by: str
    deployed_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


# API Request/Response Models for Enhanced Features

class ContentLayoutCreate(BaseModel):
    name: str
    description: Optional[str] = None
    company_id: str
    layout_type: ContentLayoutType
    screen_resolution_width: int = 1920
    screen_resolution_height: int = 1080
    zones: List[Dict] = []  # Zone configurations
    is_template: bool = False


class ContentLayoutUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    layout_type: Optional[ContentLayoutType] = None
    zones: Optional[List[Dict]] = None
    category_preferences: Optional[Dict] = None


class AdvertiserCampaignCreate(BaseModel):
    name: str
    advertiser_company_id: str
    content_ids: List[str]
    target_categories: List[str] = []
    total_budget: float
    daily_budget: float
    cpm_bid: float
    campaign_start: datetime
    campaign_end: datetime


class ContentDeploymentCreate(BaseModel):
    content_id: str
    layout_id: str
    device_ids: List[str]
    deployment_type: str = "immediate"
    scheduled_time: Optional[datetime] = None


class AnalyticsQuery(BaseModel):
    device_ids: Optional[List[str]] = None
    content_ids: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    event_types: Optional[List[str]] = None
    group_by: str = "hour"  # hour, day, week, month
    metrics: List[str] = ["impressions", "revenue", "engagement"]


class AnalyticsSummary(BaseModel):
    total_impressions: int = 0
    total_revenue: float = 0.0
    total_interactions: int = 0
    unique_devices: int = 0
    avg_engagement_time: float = 0.0
    top_performing_content: List[Dict] = []
    revenue_by_category: Dict[str, float] = {}
    hourly_breakdown: List[Dict] = []