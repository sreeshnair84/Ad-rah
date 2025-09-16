# Copyright (c) 2025 Adara Screen by Hebron
# Owner: Sujesh M S
# All Rights Reserved
#
# This software is proprietary to Adara Screen by Hebron.
# Unauthorized use, reproduction, or distribution is strictly prohibited.

"""
Shared Models and Enums

This module contains all shared enums, constants, and base models
used across different domains in the Adara Digital Signage Platform.

These models are imported by other domain-specific model files.
"""

from enum import Enum


class Permission(str, Enum):
    """System-wide permission definitions"""
    # Basic CRUD permissions
    VIEW = "view"
    EDIT = "edit"
    DELETE = "delete"
    ACCESS = "access"
    CREATE = "create"
    APPROVE = "approve"

    # Ad Slot Management Permissions
    SLOT_CREATE = "slot_create"
    SLOT_VIEW = "slot_view"
    SLOT_EDIT = "slot_edit"
    SLOT_DELETE = "slot_delete"
    SLOT_PRICING = "slot_pricing"

    # Booking Management Permissions
    BOOKING_CREATE = "booking_create"
    BOOKING_VIEW = "booking_view"
    BOOKING_EDIT = "booking_edit"
    BOOKING_CANCEL = "booking_cancel"
    BOOKING_APPROVE = "booking_approve"
    BOOKING_REJECT = "booking_reject"

    # Content & Moderation Permissions
    CONTENT_UPLOAD = "content_upload"
    CONTENT_MODERATE = "content_moderate"
    CONTENT_REVIEW = "content_review"
    CONTENT_APPROVE = "content_approve"
    CONTENT_REJECT = "content_reject"

    # Billing & Finance Permissions
    BILLING_VIEW = "billing_view"
    BILLING_MANAGE = "billing_manage"
    INVOICE_CREATE = "invoice_create"
    INVOICE_SEND = "invoice_send"
    PAYMENT_PROCESS = "payment_process"
    PAYOUT_VIEW = "payout_view"
    PAYOUT_PROCESS = "payout_process"

    # Analytics & Reporting Permissions
    ANALYTICS_VIEW = "analytics_view"
    ANALYTICS_EXPORT = "analytics_export"
    PROOF_OF_PLAY = "proof_of_play"
    PERFORMANCE_VIEW = "performance_view"

    # Device & Location Permissions
    LOCATION_CREATE = "location_create"
    LOCATION_MANAGE = "location_manage"
    DEVICE_REGISTER = "device_register"
    DEVICE_MANAGE = "device_manage"
    DEVICE_MONITOR = "device_monitor"

    # System Administration
    SYSTEM_ADMIN = "system_admin"
    USER_MANAGE = "user_manage"
    COMPANY_MANAGE = "company_manage"
    AUDIT_VIEW = "audit_view"


class RoleGroup(str, Enum):
    """High-level role groupings"""
    ADMIN = "ADMIN"  # Platform administrators
    HOST = "HOST"    # Host company roles
    ADVERTISER = "ADVERTISER"  # Advertiser company roles


class CompanyRoleType(str, Enum):
    """Specific role types within companies"""
    # Core Roles
    COMPANY_ADMIN = "COMPANY_ADMIN"      # Full company management
    MANAGER = "MANAGER"                  # Department management
    EDITOR = "EDITOR"                    # Content/data editing
    VIEWER = "VIEWER"                    # Read-only access

    # Host Company Specific Roles
    HOST_ADMIN = "HOST_ADMIN"            # Host company administration
    LOCATION_MANAGER = "LOCATION_MANAGER" # Manage locations and devices
    SLOT_MANAGER = "SLOT_MANAGER"        # Manage ad slot inventory
    BOOKING_APPROVER = "BOOKING_APPROVER" # Approve/reject bookings
    REVENUE_MANAGER = "REVENUE_MANAGER"   # View financial reports

    # Advertiser Company Specific Roles
    ADVERTISER_ADMIN = "ADVERTISER_ADMIN" # Advertiser company administration
    CAMPAIGN_MANAGER = "CAMPAIGN_MANAGER" # Create and manage campaigns
    CONTENT_CREATOR = "CONTENT_CREATOR"   # Upload and manage content
    BUYER = "BUYER"                      # Book ad slots

    # Reviewer and Moderator Roles
    CONTENT_REVIEWER = "CONTENT_REVIEWER" # Review content for approval
    CONTENT_MODERATOR = "CONTENT_MODERATOR" # Moderate content for compliance

    # Finance and Billing Roles
    FINANCE_MANAGER = "FINANCE_MANAGER"   # Handle billing and payments
    ACCOUNTANT = "ACCOUNTANT"            # View financial reports


class Screen(str, Enum):
    """Screen/page identifiers for navigation and access control"""
    # Core Platform Screens
    DASHBOARD = "dashboard"
    USERS = "users"
    COMPANIES = "companies"
    SETTINGS = "settings"

    # Content Management Screens
    CONTENT = "content"
    CONTENT_UPLOAD = "content_upload"
    CONTENT_LIBRARY = "content_library"
    MODERATION = "moderation"
    CONTENT_REVIEW = "content_review"

    # Ad Slot Management Screens
    LOCATIONS = "locations"
    DEVICES = "devices"
    AD_SLOTS = "ad_slots"
    SLOT_INVENTORY = "slot_inventory"
    SLOT_PRICING = "slot_pricing"

    # Booking Management Screens
    SLOT_DISCOVERY = "slot_discovery"
    BOOKING_MANAGEMENT = "booking_management"
    BOOKING_APPROVAL = "booking_approval"
    CAMPAIGN_MANAGEMENT = "campaign_management"

    # Financial Screens
    BILLING = "billing"
    INVOICING = "invoicing"
    PAYMENTS = "payments"
    REVENUE_REPORTS = "revenue_reports"
    PAYOUTS = "payouts"

    # Analytics and Reporting Screens
    ANALYTICS = "analytics"
    PERFORMANCE_ANALYTICS = "performance_analytics"
    PROOF_OF_PLAY = "proof_of_play"
    AUDIENCE_ANALYTICS = "audience_analytics"

    # Device and Monitoring Screens
    DEVICE_MONITORING = "device_monitoring"
    PLAYBACK_LOGS = "playback_logs"
    SYSTEM_HEALTH = "system_health"

    # Administration Screens
    AUDIT_LOGS = "audit_logs"
    SYSTEM_ADMIN = "system_admin"


class CompanyType(str, Enum):
    """Company types in the multi-tenant system"""
    HOST = "HOST"
    ADVERTISER = "ADVERTISER"


class UserType(str, Enum):
    """User types for authentication and authorization"""
    SUPER_USER = "SUPER_USER"        # Platform administrators
    COMPANY_USER = "COMPANY_USER"    # Company-specific users
    DEVICE_USER = "DEVICE_USER"      # Device authentication


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


class ContentDeleteType(str, Enum):
    """Types of content deletion"""
    SOFT_DELETE = "soft_delete"  # Mark as deleted but keep data
    HARD_DELETE = "hard_delete"  # Permanently remove data


class ScreenStatus(str, Enum):
    """Device/screen status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class ScreenOrientation(str, Enum):
    """Screen orientation settings"""
    LANDSCAPE = "landscape"
    PORTRAIT = "portrait"


class DeviceType(str, Enum):
    """Types of devices supported"""
    KIOSK = "kiosk"
    BILLBOARD = "billboard"
    INDOOR_SCREEN = "indoor_screen"
    OUTDOOR_SCREEN = "outdoor_screen"
    INTERACTIVE_DISPLAY = "interactive_display"


class ContentLayoutType(str, Enum):
    """Types of content layouts"""
    SINGLE_ZONE = "single_zone"
    MULTI_ZONE = "multi_zone"
    DYNAMIC_OVERLAY = "dynamic_overlay"
    INTERACTIVE = "interactive"


class ContentOverlayStatus(str, Enum):
    """Status of content overlays"""
    DRAFT = "draft"
    ACTIVE = "active"
    SCHEDULED = "scheduled"
    EXPIRED = "expired"
    PAUSED = "paused"


class DigitalTwinStatus(str, Enum):
    """Digital twin status"""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"


class CompanyApplicationStatus(str, Enum):
    """Status of company registration applications"""
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"