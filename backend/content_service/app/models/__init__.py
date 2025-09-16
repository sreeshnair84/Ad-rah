"""
Digital Signage Ad Slot Management System - Models Package
Clean, unified model imports for the complete platform
"""

# Core Ad Slot Management Models
from .ad_slot_models import (
    # Enums
    UserRole,
    AdSlotStatus,
    BookingStatus,
    ContentStatus,
    PaymentStatus,
    InvoiceStatus,
    
    # Primary Models
    User,
    Company,
    Location,
    Device,
    AdSlot,
    RecurringSlotRule,
    Booking,
    Campaign,
    Content,
    ModerationLog,
    PlaybackEvent,
    AnalyticsAggregation,
    Invoice,
    PaymentTransaction,
    RevenueShare,
    
    # Request/Response Models
    SlotSearchQuery,
    BookingRequest,
    ContentUploadRequest,
    AnalyticsRequest,
    SlotAvailability,
    BookingConfirmation,
    AnalyticsResponse
)

# Content Moderation
from .moderation_models import (
    ModerationResult,
    Review
)

# System Management Models
from .legacy_models import (
    # Content Types
    ContentDeleteType,

    # User & Authentication
    UserProfile,
    UserLogin,
    UserCreate,
    UserUpdate,
    UserRegistration,
    UserInvitation,
    PasswordResetToken,
    PasswordReset,
    PasswordResetRequest,
    OAuthLogin,
    
    # Roles & Permissions
    Permission,
    RoleGroup,
    CompanyRoleType,
    Role,
    RolePermission,
    RoleCreate,
    RoleUpdate,
    PermissionCheck,
    
    # Company Management
    CompanyCreate,
    CompanyUpdate,
    CompanyApplication,
    CompanyApplicationStatus,
    CompanyApplicationCreate,
    CompanyApplicationReview,
    CompanyType,
    
    # Content Management
    ContentMetadata,
    ContentMeta,
    ContentCategory,
    ContentTag,
    ContentCategoryCreate,
    ContentCategoryUpdate,
    ContentTagCreate,
    ContentTagUpdate,
    UploadResponse,
    
    # Host Preferences
    HostPreference,
    HostPreferenceCreate,
    HostPreferenceUpdate,
    
    # Digital Screens & Devices
    DigitalScreen,
    DigitalTwin,
    DigitalTwinCreate,
    DigitalTwinUpdate,
    ScreenStatus,
    ScreenOrientation,
    ScreenCreate,
    ScreenUpdate,
    DeviceRegistrationKey,
    DeviceRegistrationKeyCreate,
    DeviceCredentials,
    DeviceHeartbeat,
    DeviceFingerprint,
    DeviceCapabilities,
    DeviceType,
    DeviceRegistrationCreate,
    
    # Layout Templates
    LayoutTemplate,
    LayoutTemplateCreate,
    LayoutTemplateUpdate,
    
    # Content Overlays
    ContentOverlay,
    ContentOverlayStatus,
    ContentOverlayCreate,
    ContentOverlayUpdate,
    
    # History & Audit Models
    ContentHistory,
    ContentHistoryEventType,
    ContentHistoryQuery,
    ContentLifecycleSummary,
    ContentAuditReport,
    HistoryEventCreate,
    ContentTimelineView,
    DeviceHistory,
    DeviceHistoryEventType,
    SystemAuditLog,
    
    # System Enums
    Screen,
    DigitalTwinStatus,

    # Enhanced Content Layout Models
    ContentLayoutType,
    LayoutZone,
    ContentLayout,
    AdCategoryPreference,
    AdvertiserCampaign,
    DeviceAnalytics,
    ProximityDetection,
    MonetizationMetrics,
    ContentScheduleRule,
    ContentDeployment,
    ContentLayoutCreate,
    ContentLayoutUpdate,
    AdvertiserCampaignCreate,
    ContentDeploymentCreate,
    AnalyticsQuery,
    AnalyticsSummary
)

__all__ = [
    # Core Enums
    "UserRole", "AdSlotStatus", "BookingStatus", "ContentStatus", 
    "PaymentStatus", "InvoiceStatus",
    
    # Primary Models
    "User", "Company", "Location", "Device", "AdSlot", "RecurringSlotRule",
    "Booking", "Campaign", "Content", "ModerationLog", "PlaybackEvent",
    "AnalyticsAggregation", "Invoice", "PaymentTransaction", "RevenueShare",
    
    # Request/Response Models
    "SlotSearchQuery", "BookingRequest", "ContentUploadRequest", "AnalyticsRequest",
    "SlotAvailability", "BookingConfirmation", "AnalyticsResponse",
    
    # Moderation Models
    "ModerationResult", "Review",
    
    # User & Authentication
    "UserProfile", "UserLogin", "UserCreate", "UserUpdate", "UserRegistration",
    "UserInvitation", "PasswordResetToken", "PasswordReset", "PasswordResetRequest",
    "OAuthLogin",
    
    # Roles & Permissions
    "Permission", "RoleGroup", "CompanyRoleType", "Role", "RolePermission",
    "RoleCreate", "RoleUpdate", "PermissionCheck",
    
    # Company Management
    "CompanyCreate", "CompanyUpdate", "CompanyApplication", "CompanyApplicationStatus",
    "CompanyApplicationCreate", "CompanyApplicationReview", "CompanyType",
    
    # Content Management
    "ContentMetadata", "ContentMeta", "ContentCategory", "ContentTag",
    "ContentCategoryCreate", "ContentCategoryUpdate", "ContentTagCreate",
    "ContentTagUpdate", "UploadResponse",
    
    # Host Preferences
    "HostPreference", "HostPreferenceCreate", "HostPreferenceUpdate",
    
    # Digital Screens & Devices
    "DigitalScreen", "DigitalTwin", "DigitalTwinCreate", "DigitalTwinUpdate", "ScreenStatus", "ScreenOrientation",
    "ScreenCreate", "ScreenUpdate", "DeviceRegistrationKey", "DeviceRegistrationKeyCreate",
    "DeviceCredentials", "DeviceHeartbeat", "DeviceFingerprint", "DeviceCapabilities",
    "DeviceType", "DeviceRegistrationCreate",
    
    # Layout Templates
    "LayoutTemplate", "LayoutTemplateCreate", "LayoutTemplateUpdate",
    
    # Content Overlays
    "ContentOverlay", "ContentOverlayStatus", "ContentOverlayCreate",
    "ContentOverlayUpdate",
    
    # History & Audit Models
    "ContentHistory", "ContentHistoryEventType", "ContentHistoryQuery",
    "ContentLifecycleSummary", "ContentAuditReport", "HistoryEventCreate",
    "ContentTimelineView", "DeviceHistory", "DeviceHistoryEventType",
    "SystemAuditLog",
    
    # Content Types
    "ContentDeleteType",

    # System Enums
    "Screen", "DigitalTwinStatus",

    # Enhanced Content Layout Models
    "ContentLayoutType", "LayoutZone", "ContentLayout", "AdCategoryPreference",
    "AdvertiserCampaign", "DeviceAnalytics", "ProximityDetection", "MonetizationMetrics",
    "ContentScheduleRule", "ContentDeployment", "ContentLayoutCreate", "ContentLayoutUpdate",
    "AdvertiserCampaignCreate", "ContentDeploymentCreate", "AnalyticsQuery", "AnalyticsSummary"
]