"""
RBAC Permission Mappings for Digital Signage Ad Slot Management System
=====================================================================

This module defines the permission mappings for different user roles in the
ad slot management system. It maps company role types to their specific
permissions across different screens and functionalities.
"""

from typing import Dict, List, Set
from app.models import Permission, CompanyRoleType, Screen, RoleGroup


# ==================== PERMISSION SETS ====================

class PermissionSets:
    """Pre-defined permission sets for common operations"""

    # Basic operation sets
    BASIC_VIEW = {Permission.VIEW}
    BASIC_CRUD = {Permission.VIEW, Permission.CREATE, Permission.EDIT, Permission.DELETE}
    ADMIN_FULL = {Permission.VIEW, Permission.CREATE, Permission.EDIT, Permission.DELETE, Permission.APPROVE, Permission.SYSTEM_ADMIN}

    # Content management sets
    CONTENT_UPLOADER = {Permission.CONTENT_UPLOAD, Permission.VIEW, Permission.EDIT}
    CONTENT_REVIEWER = {Permission.CONTENT_REVIEW, Permission.CONTENT_APPROVE, Permission.CONTENT_REJECT, Permission.VIEW}
    CONTENT_MODERATOR = {Permission.CONTENT_MODERATE, Permission.CONTENT_REVIEW, Permission.CONTENT_APPROVE, Permission.CONTENT_REJECT, Permission.VIEW}

    # Ad slot management sets
    SLOT_MANAGER = {Permission.SLOT_VIEW, Permission.SLOT_CREATE, Permission.SLOT_EDIT, Permission.SLOT_PRICING}
    SLOT_VIEWER = {Permission.SLOT_VIEW}

    # Booking management sets
    BOOKING_CREATOR = {Permission.BOOKING_CREATE, Permission.BOOKING_VIEW, Permission.BOOKING_EDIT}
    BOOKING_APPROVER = {Permission.BOOKING_VIEW, Permission.BOOKING_APPROVE, Permission.BOOKING_REJECT}
    BOOKING_MANAGER = {Permission.BOOKING_VIEW, Permission.BOOKING_CREATE, Permission.BOOKING_EDIT, Permission.BOOKING_CANCEL, Permission.BOOKING_APPROVE, Permission.BOOKING_REJECT}

    # Device and location sets
    DEVICE_MANAGER = {Permission.DEVICE_REGISTER, Permission.DEVICE_MANAGE, Permission.DEVICE_MONITOR, Permission.VIEW}
    LOCATION_MANAGER = {Permission.LOCATION_CREATE, Permission.LOCATION_MANAGE, Permission.VIEW}

    # Financial sets
    BILLING_VIEWER = {Permission.BILLING_VIEW, Permission.PAYOUT_VIEW, Permission.VIEW}
    BILLING_MANAGER = {Permission.BILLING_VIEW, Permission.BILLING_MANAGE, Permission.INVOICE_CREATE, Permission.INVOICE_SEND, Permission.PAYMENT_PROCESS}
    PAYOUT_PROCESSOR = {Permission.PAYOUT_VIEW, Permission.PAYOUT_PROCESS, Permission.BILLING_VIEW}

    # Analytics sets
    ANALYTICS_VIEWER = {Permission.ANALYTICS_VIEW, Permission.PERFORMANCE_VIEW, Permission.PROOF_OF_PLAY}
    ANALYTICS_EXPORTER = {Permission.ANALYTICS_VIEW, Permission.ANALYTICS_EXPORT, Permission.PERFORMANCE_VIEW, Permission.PROOF_OF_PLAY}


# ==================== ROLE-BASED PERMISSION MAPPINGS ====================

def get_default_permissions_for_role(role_type: CompanyRoleType, company_type: str = None) -> Dict[Screen, Set[Permission]]:
    """
    Get default permissions for a specific role type.
    Returns a mapping of screens to permissions.
    """

    if role_type == CompanyRoleType.COMPANY_ADMIN:
        return _get_company_admin_permissions(company_type)

    elif role_type == CompanyRoleType.HOST_ADMIN:
        return _get_host_admin_permissions()

    elif role_type == CompanyRoleType.ADVERTISER_ADMIN:
        return _get_advertiser_admin_permissions()

    elif role_type == CompanyRoleType.LOCATION_MANAGER:
        return _get_location_manager_permissions()

    elif role_type == CompanyRoleType.SLOT_MANAGER:
        return _get_slot_manager_permissions()

    elif role_type == CompanyRoleType.BOOKING_APPROVER:
        return _get_booking_approver_permissions()

    elif role_type == CompanyRoleType.REVENUE_MANAGER:
        return _get_revenue_manager_permissions()

    elif role_type == CompanyRoleType.CAMPAIGN_MANAGER:
        return _get_campaign_manager_permissions()

    elif role_type == CompanyRoleType.CONTENT_CREATOR:
        return _get_content_creator_permissions()

    elif role_type == CompanyRoleType.BUYER:
        return _get_buyer_permissions()

    elif role_type == CompanyRoleType.CONTENT_REVIEWER:
        return _get_content_reviewer_permissions()

    elif role_type == CompanyRoleType.CONTENT_MODERATOR:
        return _get_content_moderator_permissions()

    elif role_type == CompanyRoleType.FINANCE_MANAGER:
        return _get_finance_manager_permissions()

    elif role_type == CompanyRoleType.ACCOUNTANT:
        return _get_accountant_permissions()

    elif role_type == CompanyRoleType.MANAGER:
        return _get_manager_permissions(company_type)

    elif role_type == CompanyRoleType.EDITOR:
        return _get_editor_permissions(company_type)

    elif role_type == CompanyRoleType.VIEWER:
        return _get_viewer_permissions()

    else:
        return _get_minimal_permissions()


# ==================== SPECIFIC ROLE PERMISSION DEFINITIONS ====================

def _get_company_admin_permissions(company_type: str = None) -> Dict[Screen, Set[Permission]]:
    """Full company administration permissions"""
    permissions = {
        Screen.DASHBOARD: PermissionSets.BASIC_VIEW,
        Screen.USERS: PermissionSets.BASIC_CRUD | {Permission.USER_MANAGE},
        Screen.SETTINGS: PermissionSets.BASIC_CRUD,
        Screen.ANALYTICS: PermissionSets.ANALYTICS_EXPORTER,
        Screen.PERFORMANCE_ANALYTICS: PermissionSets.ANALYTICS_EXPORTER,
        Screen.BILLING: PermissionSets.BILLING_MANAGER,
        Screen.INVOICING: PermissionSets.BILLING_MANAGER,
        Screen.PAYMENTS: PermissionSets.BILLING_MANAGER,
        Screen.AUDIT_LOGS: {Permission.AUDIT_VIEW, Permission.VIEW},
    }

    if company_type == "HOST":
        permissions.update({
            Screen.LOCATIONS: PermissionSets.BASIC_CRUD | PermissionSets.LOCATION_MANAGER,
            Screen.DEVICES: PermissionSets.BASIC_CRUD | PermissionSets.DEVICE_MANAGER,
            Screen.AD_SLOTS: PermissionSets.BASIC_CRUD | PermissionSets.SLOT_MANAGER,
            Screen.SLOT_INVENTORY: PermissionSets.SLOT_MANAGER,
            Screen.SLOT_PRICING: PermissionSets.SLOT_MANAGER,
            Screen.BOOKING_APPROVAL: PermissionSets.BOOKING_MANAGER,
            Screen.REVENUE_REPORTS: PermissionSets.BILLING_VIEWER,
            Screen.PAYOUTS: PermissionSets.PAYOUT_PROCESSOR,
            Screen.DEVICE_MONITORING: PermissionSets.DEVICE_MANAGER,
            Screen.PLAYBACK_LOGS: {Permission.PROOF_OF_PLAY, Permission.VIEW},
        })
    elif company_type == "ADVERTISER":
        permissions.update({
            Screen.CONTENT: PermissionSets.BASIC_CRUD | PermissionSets.CONTENT_UPLOADER,
            Screen.CONTENT_UPLOAD: PermissionSets.CONTENT_UPLOADER,
            Screen.CONTENT_LIBRARY: PermissionSets.BASIC_VIEW,
            Screen.SLOT_DISCOVERY: {Permission.SLOT_VIEW, Permission.VIEW},
            Screen.BOOKING_MANAGEMENT: PermissionSets.BOOKING_MANAGER,
            Screen.CAMPAIGN_MANAGEMENT: PermissionSets.BOOKING_MANAGER,
        })

    return permissions


def _get_host_admin_permissions() -> Dict[Screen, Set[Permission]]:
    """Host company administrator permissions"""
    return {
        Screen.DASHBOARD: PermissionSets.BASIC_VIEW,
        Screen.USERS: PermissionSets.BASIC_CRUD | {Permission.USER_MANAGE},
        Screen.LOCATIONS: PermissionSets.BASIC_CRUD | PermissionSets.LOCATION_MANAGER,
        Screen.DEVICES: PermissionSets.BASIC_CRUD | PermissionSets.DEVICE_MANAGER,
        Screen.AD_SLOTS: PermissionSets.BASIC_CRUD | PermissionSets.SLOT_MANAGER,
        Screen.SLOT_INVENTORY: PermissionSets.SLOT_MANAGER,
        Screen.SLOT_PRICING: PermissionSets.SLOT_MANAGER,
        Screen.BOOKING_APPROVAL: PermissionSets.BOOKING_MANAGER,
        Screen.ANALYTICS: PermissionSets.ANALYTICS_EXPORTER,
        Screen.PERFORMANCE_ANALYTICS: PermissionSets.ANALYTICS_EXPORTER,
        Screen.BILLING: PermissionSets.BILLING_MANAGER,
        Screen.REVENUE_REPORTS: PermissionSets.BILLING_VIEWER,
        Screen.PAYOUTS: PermissionSets.PAYOUT_PROCESSOR,
        Screen.DEVICE_MONITORING: PermissionSets.DEVICE_MANAGER,
        Screen.PLAYBACK_LOGS: {Permission.PROOF_OF_PLAY, Permission.VIEW},
        Screen.SETTINGS: PermissionSets.BASIC_CRUD,
    }


def _get_advertiser_admin_permissions() -> Dict[Screen, Set[Permission]]:
    """Advertiser company administrator permissions"""
    return {
        Screen.DASHBOARD: PermissionSets.BASIC_VIEW,
        Screen.USERS: PermissionSets.BASIC_CRUD | {Permission.USER_MANAGE},
        Screen.CONTENT: PermissionSets.BASIC_CRUD | PermissionSets.CONTENT_UPLOADER,
        Screen.CONTENT_UPLOAD: PermissionSets.CONTENT_UPLOADER,
        Screen.CONTENT_LIBRARY: PermissionSets.BASIC_VIEW,
        Screen.SLOT_DISCOVERY: {Permission.SLOT_VIEW, Permission.VIEW},
        Screen.BOOKING_MANAGEMENT: PermissionSets.BOOKING_MANAGER,
        Screen.CAMPAIGN_MANAGEMENT: PermissionSets.BOOKING_MANAGER,
        Screen.ANALYTICS: PermissionSets.ANALYTICS_EXPORTER,
        Screen.PERFORMANCE_ANALYTICS: PermissionSets.ANALYTICS_EXPORTER,
        Screen.BILLING: PermissionSets.BILLING_VIEWER,
        Screen.INVOICING: PermissionSets.BILLING_VIEWER,
        Screen.PAYMENTS: {Permission.PAYMENT_PROCESS, Permission.BILLING_VIEW, Permission.VIEW},
        Screen.SETTINGS: PermissionSets.BASIC_CRUD,
    }


def _get_location_manager_permissions() -> Dict[Screen, Set[Permission]]:
    """Location manager permissions (HOST company)"""
    return {
        Screen.DASHBOARD: PermissionSets.BASIC_VIEW,
        Screen.LOCATIONS: PermissionSets.BASIC_CRUD | PermissionSets.LOCATION_MANAGER,
        Screen.DEVICES: PermissionSets.BASIC_CRUD | PermissionSets.DEVICE_MANAGER,
        Screen.AD_SLOTS: PermissionSets.SLOT_VIEWER,
        Screen.DEVICE_MONITORING: PermissionSets.DEVICE_MANAGER,
        Screen.ANALYTICS: PermissionSets.ANALYTICS_VIEWER,
        Screen.PLAYBACK_LOGS: {Permission.VIEW},
    }


def _get_slot_manager_permissions() -> Dict[Screen, Set[Permission]]:
    """Ad slot manager permissions (HOST company)"""
    return {
        Screen.DASHBOARD: PermissionSets.BASIC_VIEW,
        Screen.AD_SLOTS: PermissionSets.BASIC_CRUD | PermissionSets.SLOT_MANAGER,
        Screen.SLOT_INVENTORY: PermissionSets.SLOT_MANAGER,
        Screen.SLOT_PRICING: PermissionSets.SLOT_MANAGER,
        Screen.BOOKING_APPROVAL: {Permission.BOOKING_VIEW, Permission.VIEW},
        Screen.ANALYTICS: PermissionSets.ANALYTICS_VIEWER,
        Screen.PERFORMANCE_ANALYTICS: PermissionSets.ANALYTICS_VIEWER,
        Screen.DEVICES: {Permission.DEVICE_MONITOR, Permission.VIEW},
        Screen.LOCATIONS: {Permission.VIEW},
    }


def _get_booking_approver_permissions() -> Dict[Screen, Set[Permission]]:
    """Booking approver permissions (HOST company)"""
    return {
        Screen.DASHBOARD: PermissionSets.BASIC_VIEW,
        Screen.BOOKING_APPROVAL: PermissionSets.BOOKING_APPROVER,
        Screen.AD_SLOTS: PermissionSets.SLOT_VIEWER,
        Screen.CONTENT_REVIEW: PermissionSets.CONTENT_REVIEWER,
        Screen.ANALYTICS: PermissionSets.ANALYTICS_VIEWER,
        Screen.BILLING: {Permission.BILLING_VIEW, Permission.VIEW},
    }


def _get_revenue_manager_permissions() -> Dict[Screen, Set[Permission]]:
    """Revenue manager permissions (HOST company)"""
    return {
        Screen.DASHBOARD: PermissionSets.BASIC_VIEW,
        Screen.ANALYTICS: PermissionSets.ANALYTICS_EXPORTER,
        Screen.PERFORMANCE_ANALYTICS: PermissionSets.ANALYTICS_EXPORTER,
        Screen.BILLING: PermissionSets.BILLING_VIEWER,
        Screen.REVENUE_REPORTS: PermissionSets.BILLING_VIEWER,
        Screen.PAYOUTS: PermissionSets.BILLING_VIEWER,
        Screen.INVOICING: PermissionSets.BILLING_VIEWER,
        Screen.PROOF_OF_PLAY: {Permission.PROOF_OF_PLAY, Permission.ANALYTICS_EXPORT, Permission.VIEW},
        Screen.AD_SLOTS: PermissionSets.SLOT_VIEWER,
        Screen.BOOKING_APPROVAL: {Permission.BOOKING_VIEW, Permission.VIEW},
    }


def _get_campaign_manager_permissions() -> Dict[Screen, Set[Permission]]:
    """Campaign manager permissions (ADVERTISER company)"""
    return {
        Screen.DASHBOARD: PermissionSets.BASIC_VIEW,
        Screen.SLOT_DISCOVERY: {Permission.SLOT_VIEW, Permission.VIEW},
        Screen.BOOKING_MANAGEMENT: PermissionSets.BOOKING_MANAGER,
        Screen.CAMPAIGN_MANAGEMENT: PermissionSets.BOOKING_MANAGER,
        Screen.CONTENT: {Permission.VIEW, Permission.EDIT},
        Screen.CONTENT_LIBRARY: PermissionSets.BASIC_VIEW,
        Screen.ANALYTICS: PermissionSets.ANALYTICS_EXPORTER,
        Screen.PERFORMANCE_ANALYTICS: PermissionSets.ANALYTICS_EXPORTER,
        Screen.BILLING: PermissionSets.BILLING_VIEWER,
    }


def _get_content_creator_permissions() -> Dict[Screen, Set[Permission]]:
    """Content creator permissions (ADVERTISER company)"""
    return {
        Screen.DASHBOARD: PermissionSets.BASIC_VIEW,
        Screen.CONTENT: PermissionSets.BASIC_CRUD | PermissionSets.CONTENT_UPLOADER,
        Screen.CONTENT_UPLOAD: PermissionSets.CONTENT_UPLOADER,
        Screen.CONTENT_LIBRARY: PermissionSets.BASIC_VIEW,
        Screen.ANALYTICS: {Permission.PERFORMANCE_VIEW, Permission.VIEW},
    }


def _get_buyer_permissions() -> Dict[Screen, Set[Permission]]:
    """Buyer permissions (ADVERTISER company)"""
    return {
        Screen.DASHBOARD: PermissionSets.BASIC_VIEW,
        Screen.SLOT_DISCOVERY: {Permission.SLOT_VIEW, Permission.VIEW},
        Screen.BOOKING_MANAGEMENT: PermissionSets.BOOKING_CREATOR,
        Screen.CAMPAIGN_MANAGEMENT: {Permission.BOOKING_VIEW, Permission.VIEW},
        Screen.CONTENT_LIBRARY: PermissionSets.BASIC_VIEW,
        Screen.ANALYTICS: PermissionSets.ANALYTICS_VIEWER,
        Screen.BILLING: PermissionSets.BILLING_VIEWER,
        Screen.PAYMENTS: {Permission.PAYMENT_PROCESS, Permission.BILLING_VIEW, Permission.VIEW},
    }


def _get_content_reviewer_permissions() -> Dict[Screen, Set[Permission]]:
    """Content reviewer permissions (platform-wide)"""
    return {
        Screen.DASHBOARD: PermissionSets.BASIC_VIEW,
        Screen.CONTENT_REVIEW: PermissionSets.CONTENT_REVIEWER,
        Screen.MODERATION: PermissionSets.CONTENT_REVIEWER,
        Screen.CONTENT: {Permission.VIEW},
        Screen.ANALYTICS: {Permission.VIEW},
    }


def _get_content_moderator_permissions() -> Dict[Screen, Set[Permission]]:
    """Content moderator permissions (platform-wide)"""
    return {
        Screen.DASHBOARD: PermissionSets.BASIC_VIEW,
        Screen.CONTENT_REVIEW: PermissionSets.CONTENT_MODERATOR,
        Screen.MODERATION: PermissionSets.CONTENT_MODERATOR,
        Screen.CONTENT: {Permission.VIEW, Permission.CONTENT_MODERATE},
        Screen.ANALYTICS: PermissionSets.ANALYTICS_VIEWER,
        Screen.AUDIT_LOGS: {Permission.AUDIT_VIEW, Permission.VIEW},
    }


def _get_finance_manager_permissions() -> Dict[Screen, Set[Permission]]:
    """Finance manager permissions"""
    return {
        Screen.DASHBOARD: PermissionSets.BASIC_VIEW,
        Screen.BILLING: PermissionSets.BILLING_MANAGER,
        Screen.INVOICING: PermissionSets.BILLING_MANAGER,
        Screen.PAYMENTS: PermissionSets.BILLING_MANAGER,
        Screen.PAYOUTS: PermissionSets.PAYOUT_PROCESSOR,
        Screen.REVENUE_REPORTS: PermissionSets.BILLING_VIEWER,
        Screen.ANALYTICS: PermissionSets.ANALYTICS_VIEWER,
        Screen.AUDIT_LOGS: {Permission.AUDIT_VIEW, Permission.VIEW},
    }


def _get_accountant_permissions() -> Dict[Screen, Set[Permission]]:
    """Accountant permissions (read-only financial access)"""
    return {
        Screen.DASHBOARD: PermissionSets.BASIC_VIEW,
        Screen.BILLING: PermissionSets.BILLING_VIEWER,
        Screen.INVOICING: PermissionSets.BILLING_VIEWER,
        Screen.PAYMENTS: PermissionSets.BILLING_VIEWER,
        Screen.PAYOUTS: PermissionSets.BILLING_VIEWER,
        Screen.REVENUE_REPORTS: PermissionSets.BILLING_VIEWER,
        Screen.ANALYTICS: PermissionSets.ANALYTICS_VIEWER,
        Screen.PROOF_OF_PLAY: {Permission.PROOF_OF_PLAY, Permission.VIEW},
    }


def _get_manager_permissions(company_type: str = None) -> Dict[Screen, Set[Permission]]:
    """General manager permissions"""
    base_permissions = {
        Screen.DASHBOARD: PermissionSets.BASIC_VIEW,
        Screen.USERS: {Permission.VIEW, Permission.USER_MANAGE},
        Screen.ANALYTICS: PermissionSets.ANALYTICS_VIEWER,
        Screen.SETTINGS: {Permission.VIEW, Permission.EDIT},
    }

    if company_type == "HOST":
        base_permissions.update({
            Screen.LOCATIONS: {Permission.VIEW, Permission.EDIT},
            Screen.DEVICES: {Permission.VIEW, Permission.DEVICE_MANAGE},
            Screen.AD_SLOTS: PermissionSets.SLOT_VIEWER,
            Screen.BOOKING_APPROVAL: {Permission.BOOKING_VIEW, Permission.VIEW},
        })
    elif company_type == "ADVERTISER":
        base_permissions.update({
            Screen.CONTENT: {Permission.VIEW, Permission.EDIT},
            Screen.SLOT_DISCOVERY: {Permission.SLOT_VIEW, Permission.VIEW},
            Screen.BOOKING_MANAGEMENT: {Permission.BOOKING_VIEW, Permission.VIEW},
        })

    return base_permissions


def _get_editor_permissions(company_type: str = None) -> Dict[Screen, Set[Permission]]:
    """General editor permissions"""
    base_permissions = {
        Screen.DASHBOARD: PermissionSets.BASIC_VIEW,
    }

    if company_type == "HOST":
        base_permissions.update({
            Screen.LOCATIONS: {Permission.VIEW, Permission.EDIT},
            Screen.DEVICES: {Permission.VIEW, Permission.EDIT},
            Screen.AD_SLOTS: {Permission.SLOT_VIEW, Permission.SLOT_EDIT},
        })
    elif company_type == "ADVERTISER":
        base_permissions.update({
            Screen.CONTENT: PermissionSets.CONTENT_UPLOADER,
            Screen.CONTENT_UPLOAD: PermissionSets.CONTENT_UPLOADER,
            Screen.CONTENT_LIBRARY: PermissionSets.BASIC_VIEW,
            Screen.SLOT_DISCOVERY: {Permission.SLOT_VIEW, Permission.VIEW},
        })

    return base_permissions


def _get_viewer_permissions() -> Dict[Screen, Set[Permission]]:
    """Read-only viewer permissions"""
    return {
        Screen.DASHBOARD: PermissionSets.BASIC_VIEW,
        Screen.ANALYTICS: {Permission.VIEW},
        Screen.CONTENT: {Permission.VIEW},
        Screen.AD_SLOTS: {Permission.VIEW},
        Screen.BOOKING_MANAGEMENT: {Permission.VIEW},
        Screen.BILLING: {Permission.VIEW},
    }


def _get_minimal_permissions() -> Dict[Screen, Set[Permission]]:
    """Minimal permissions for unknown roles"""
    return {
        Screen.DASHBOARD: {Permission.VIEW},
    }


# ==================== SUPER USER PERMISSIONS ====================

def get_super_user_permissions() -> Dict[Screen, Set[Permission]]:
    """Get super user permissions (platform administrators)"""
    return {
        Screen.DASHBOARD: PermissionSets.ADMIN_FULL,
        Screen.USERS: PermissionSets.ADMIN_FULL,
        Screen.COMPANIES: PermissionSets.ADMIN_FULL,
        Screen.SETTINGS: PermissionSets.ADMIN_FULL,
        Screen.CONTENT: PermissionSets.ADMIN_FULL,
        Screen.CONTENT_UPLOAD: PermissionSets.ADMIN_FULL,
        Screen.CONTENT_LIBRARY: PermissionSets.ADMIN_FULL,
        Screen.MODERATION: PermissionSets.ADMIN_FULL,
        Screen.CONTENT_REVIEW: PermissionSets.ADMIN_FULL,
        Screen.LOCATIONS: PermissionSets.ADMIN_FULL,
        Screen.DEVICES: PermissionSets.ADMIN_FULL,
        Screen.AD_SLOTS: PermissionSets.ADMIN_FULL,
        Screen.SLOT_INVENTORY: PermissionSets.ADMIN_FULL,
        Screen.SLOT_PRICING: PermissionSets.ADMIN_FULL,
        Screen.SLOT_DISCOVERY: PermissionSets.ADMIN_FULL,
        Screen.BOOKING_MANAGEMENT: PermissionSets.ADMIN_FULL,
        Screen.BOOKING_APPROVAL: PermissionSets.ADMIN_FULL,
        Screen.CAMPAIGN_MANAGEMENT: PermissionSets.ADMIN_FULL,
        Screen.BILLING: PermissionSets.ADMIN_FULL,
        Screen.INVOICING: PermissionSets.ADMIN_FULL,
        Screen.PAYMENTS: PermissionSets.ADMIN_FULL,
        Screen.REVENUE_REPORTS: PermissionSets.ADMIN_FULL,
        Screen.PAYOUTS: PermissionSets.ADMIN_FULL,
        Screen.ANALYTICS: PermissionSets.ADMIN_FULL,
        Screen.PERFORMANCE_ANALYTICS: PermissionSets.ADMIN_FULL,
        Screen.PROOF_OF_PLAY: PermissionSets.ADMIN_FULL,
        Screen.AUDIENCE_ANALYTICS: PermissionSets.ADMIN_FULL,
        Screen.DEVICE_MONITORING: PermissionSets.ADMIN_FULL,
        Screen.PLAYBACK_LOGS: PermissionSets.ADMIN_FULL,
        Screen.SYSTEM_HEALTH: PermissionSets.ADMIN_FULL,
        Screen.AUDIT_LOGS: PermissionSets.ADMIN_FULL,
        Screen.SYSTEM_ADMIN: PermissionSets.ADMIN_FULL,
    }


# ==================== UTILITY FUNCTIONS ====================

def flatten_permissions(screen_permissions: Dict[Screen, Set[Permission]]) -> List[str]:
    """Flatten screen-based permissions to a simple list of permission strings"""
    all_permissions = set()
    for screen, permissions in screen_permissions.items():
        all_permissions.update(permissions)
    return [perm.value for perm in all_permissions]


def get_accessible_screens(role_type: CompanyRoleType, company_type: str = None) -> List[str]:
    """Get list of screens accessible to a role"""
    permissions = get_default_permissions_for_role(role_type, company_type)
    return [screen.value for screen in permissions.keys()]


def check_screen_permission(role_type: CompanyRoleType, screen: Screen, permission: Permission, company_type: str = None) -> bool:
    """Check if a role has a specific permission on a specific screen"""
    permissions = get_default_permissions_for_role(role_type, company_type)
    screen_permissions = permissions.get(screen, set())
    return permission in screen_permissions


def get_role_navigation_items(role_type: CompanyRoleType, company_type: str = None) -> List[Dict]:
    """Get navigation items for a role (used by frontend)"""
    accessible_screens = get_accessible_screens(role_type, company_type)

    # Define navigation structure based on screens
    navigation_mapping = {
        # Core navigation
        Screen.DASHBOARD.value: {"label": "Dashboard", "icon": "dashboard", "category": "core"},
        Screen.USERS.value: {"label": "Users", "icon": "users", "category": "core"},
        Screen.COMPANIES.value: {"label": "Companies", "icon": "building", "category": "core"},
        Screen.SETTINGS.value: {"label": "Settings", "icon": "settings", "category": "core"},

        # Content management
        Screen.CONTENT.value: {"label": "Content", "icon": "file", "category": "content"},
        Screen.CONTENT_UPLOAD.value: {"label": "Upload Content", "icon": "upload", "category": "content"},
        Screen.CONTENT_LIBRARY.value: {"label": "Content Library", "icon": "library", "category": "content"},
        Screen.MODERATION.value: {"label": "Moderation", "icon": "shield", "category": "content"},
        Screen.CONTENT_REVIEW.value: {"label": "Content Review", "icon": "eye", "category": "content"},

        # Ad slot management
        Screen.LOCATIONS.value: {"label": "Locations", "icon": "map-pin", "category": "inventory"},
        Screen.DEVICES.value: {"label": "Devices", "icon": "monitor", "category": "inventory"},
        Screen.AD_SLOTS.value: {"label": "Ad Slots", "icon": "grid", "category": "inventory"},
        Screen.SLOT_INVENTORY.value: {"label": "Slot Inventory", "icon": "package", "category": "inventory"},
        Screen.SLOT_PRICING.value: {"label": "Pricing", "icon": "dollar-sign", "category": "inventory"},

        # Booking management
        Screen.SLOT_DISCOVERY.value: {"label": "Discover Slots", "icon": "search", "category": "booking"},
        Screen.BOOKING_MANAGEMENT.value: {"label": "My Bookings", "icon": "calendar", "category": "booking"},
        Screen.BOOKING_APPROVAL.value: {"label": "Booking Approvals", "icon": "check-circle", "category": "booking"},
        Screen.CAMPAIGN_MANAGEMENT.value: {"label": "Campaigns", "icon": "target", "category": "booking"},

        # Financial
        Screen.BILLING.value: {"label": "Billing", "icon": "credit-card", "category": "finance"},
        Screen.INVOICING.value: {"label": "Invoices", "icon": "file-text", "category": "finance"},
        Screen.PAYMENTS.value: {"label": "Payments", "icon": "credit-card", "category": "finance"},
        Screen.REVENUE_REPORTS.value: {"label": "Revenue", "icon": "trending-up", "category": "finance"},
        Screen.PAYOUTS.value: {"label": "Payouts", "icon": "send", "category": "finance"},

        # Analytics
        Screen.ANALYTICS.value: {"label": "Analytics", "icon": "bar-chart", "category": "analytics"},
        Screen.PERFORMANCE_ANALYTICS.value: {"label": "Performance", "icon": "activity", "category": "analytics"},
        Screen.PROOF_OF_PLAY.value: {"label": "Proof of Play", "icon": "play-circle", "category": "analytics"},
        Screen.AUDIENCE_ANALYTICS.value: {"label": "Audience", "icon": "users", "category": "analytics"},

        # Monitoring
        Screen.DEVICE_MONITORING.value: {"label": "Device Health", "icon": "activity", "category": "monitoring"},
        Screen.PLAYBACK_LOGS.value: {"label": "Playback Logs", "icon": "list", "category": "monitoring"},
        Screen.SYSTEM_HEALTH.value: {"label": "System Health", "icon": "heart", "category": "monitoring"},

        # Administration
        Screen.AUDIT_LOGS.value: {"label": "Audit Logs", "icon": "file-text", "category": "admin"},
        Screen.SYSTEM_ADMIN.value: {"label": "System Admin", "icon": "settings", "category": "admin"},
    }

    navigation_items = []
    for screen in accessible_screens:
        if screen in navigation_mapping:
            item = navigation_mapping[screen].copy()
            item["screen"] = screen
            navigation_items.append(item)

    return navigation_items