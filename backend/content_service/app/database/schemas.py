# Database Schema Definitions
# Clean, normalized schema design for the digital signage platform

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime

class FieldType(str, Enum):
    """Database field types"""
    STRING = "string"
    TEXT = "text"  # Large text
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    JSON = "json"
    UUID = "uuid"
    EMAIL = "email"
    URL = "url"
    ENUM = "enum"

class ConstraintType(str, Enum):
    """Database constraint types"""
    PRIMARY_KEY = "primary_key"
    FOREIGN_KEY = "foreign_key"
    UNIQUE = "unique"
    NOT_NULL = "not_null"
    CHECK = "check"
    INDEX = "index"

class FieldDefinition:
    """Database field definition"""
    def __init__(
        self,
        name: str,
        field_type: FieldType,
        required: bool = False,
        unique: bool = False,
        indexed: bool = False,
        default_value: Any = None,
        max_length: Optional[int] = None,
        enum_values: Optional[List[str]] = None,
        foreign_key: Optional[str] = None,  # Format: "table.field"
        description: Optional[str] = None
    ):
        self.name = name
        self.field_type = field_type
        self.required = required
        self.unique = unique
        self.indexed = indexed
        self.default_value = default_value
        self.max_length = max_length
        self.enum_values = enum_values
        self.foreign_key = foreign_key
        self.description = description

class TableSchema:
    """Database table schema definition"""
    def __init__(
        self,
        name: str,
        fields: List[FieldDefinition],
        indexes: Optional[List[Dict[str, Any]]] = None,
        description: Optional[str] = None
    ):
        self.name = name
        self.fields = fields
        self.indexes = indexes or []
        self.description = description

    def get_field(self, name: str) -> Optional[FieldDefinition]:
        """Get field definition by name"""
        return next((f for f in self.fields if f.name == name), None)

# Standard fields for all entities
def standard_fields() -> List[FieldDefinition]:
    """Standard fields that all entities should have"""
    return [
        FieldDefinition("id", FieldType.UUID, required=True, unique=True, description="Primary key"),
        FieldDefinition("created_at", FieldType.DATETIME, required=True, default_value="NOW()", description="Creation timestamp"),
        FieldDefinition("updated_at", FieldType.DATETIME, required=True, default_value="NOW()", description="Last update timestamp"),
        FieldDefinition("created_by", FieldType.UUID, required=False, foreign_key="users.id", description="User who created this record"),
        FieldDefinition("updated_by", FieldType.UUID, required=False, foreign_key="users.id", description="User who last updated this record"),
        FieldDefinition("is_deleted", FieldType.BOOLEAN, required=True, default_value=False, description="Soft delete flag"),
        FieldDefinition("deleted_at", FieldType.DATETIME, required=False, description="Soft delete timestamp"),
        FieldDefinition("deleted_by", FieldType.UUID, required=False, foreign_key="users.id", description="User who deleted this record")
    ]

# Core Platform Schemas

def companies_schema() -> TableSchema:
    """Company entity schema"""
    fields = [
        FieldDefinition("name", FieldType.STRING, required=True, max_length=200, description="Company name"),
        FieldDefinition("company_type", FieldType.ENUM, required=True, enum_values=["HOST", "ADVERTISER"], description="Company type"),
        FieldDefinition("organization_code", FieldType.STRING, required=True, unique=True, max_length=50, indexed=True, description="Unique organization code for device registration"),
        FieldDefinition("business_license", FieldType.STRING, required=True, max_length=100, description="Business license number"),
        FieldDefinition("email", FieldType.EMAIL, required=True, indexed=True, description="Primary contact email"),
        FieldDefinition("phone", FieldType.STRING, required=False, max_length=20, description="Primary contact phone"),
        FieldDefinition("address", FieldType.TEXT, required=True, description="Full address"),
        FieldDefinition("city", FieldType.STRING, required=True, max_length=100, description="City"),
        FieldDefinition("country", FieldType.STRING, required=True, max_length=100, description="Country"),
        FieldDefinition("website", FieldType.URL, required=False, description="Company website"),
        FieldDefinition("description", FieldType.TEXT, required=False, description="Company description"),
        FieldDefinition("status", FieldType.ENUM, required=True, default_value="active", enum_values=["active", "inactive", "suspended"], description="Company status"),
        FieldDefinition("settings", FieldType.JSON, required=False, description="Company-specific settings"),
        FieldDefinition("limits", FieldType.JSON, required=False, description="Company resource limits")
    ] + standard_fields()
    
    indexes = [
        {"fields": ["organization_code"], "unique": True},
        {"fields": ["email"], "unique": False},
        {"fields": ["company_type", "status"], "unique": False},
        {"fields": ["created_at"], "unique": False}
    ]
    
    return TableSchema("companies", fields, indexes, "Company master data")

def users_schema() -> TableSchema:
    """User entity schema"""
    fields = [
        FieldDefinition("name", FieldType.STRING, required=True, max_length=200, description="Full name"),
        FieldDefinition("email", FieldType.EMAIL, required=True, unique=True, indexed=True, description="Email address"),
        FieldDefinition("phone", FieldType.STRING, required=False, max_length=20, description="Phone number"),
        FieldDefinition("hashed_password", FieldType.STRING, required=True, max_length=255, description="Hashed password"),
        FieldDefinition("user_type", FieldType.ENUM, required=True, enum_values=["SUPER_USER", "COMPANY_USER", "DEVICE_USER"], description="User type"),
        FieldDefinition("status", FieldType.ENUM, required=True, default_value="active", enum_values=["active", "inactive", "suspended"], description="User status"),
        FieldDefinition("email_verified", FieldType.BOOLEAN, required=True, default_value=False, description="Email verification status"),
        FieldDefinition("email_verified_at", FieldType.DATETIME, required=False, description="Email verification timestamp"),
        FieldDefinition("last_login", FieldType.DATETIME, required=False, description="Last login timestamp"),
        FieldDefinition("login_count", FieldType.INTEGER, required=True, default_value=0, description="Total login count"),
        FieldDefinition("profile_image", FieldType.URL, required=False, description="Profile image URL"),
        FieldDefinition("preferences", FieldType.JSON, required=False, description="User preferences"),
        FieldDefinition("oauth_provider", FieldType.STRING, required=False, max_length=50, description="OAuth provider"),
        FieldDefinition("oauth_id", FieldType.STRING, required=False, max_length=255, description="OAuth user ID")
    ] + standard_fields()
    
    indexes = [
        {"fields": ["email"], "unique": True},
        {"fields": ["user_type", "status"], "unique": False},
        {"fields": ["oauth_provider", "oauth_id"], "unique": False},
        {"fields": ["last_login"], "unique": False}
    ]
    
    return TableSchema("users", fields, indexes, "User accounts")

def user_company_roles_schema() -> TableSchema:
    """Simplified user-company-role mapping"""
    fields = [
        FieldDefinition("user_id", FieldType.UUID, required=True, foreign_key="users.id", indexed=True, description="User ID"),
        FieldDefinition("company_id", FieldType.UUID, required=False, foreign_key="companies.id", indexed=True, description="Company ID (null for super users)"),
        FieldDefinition("role", FieldType.ENUM, required=True, 
                       enum_values=["SUPER_ADMIN", "COMPANY_ADMIN", "CONTENT_MANAGER", "REVIEWER", "EDITOR", "VIEWER", "DEVICE_USER"], 
                       description="User role"),
        FieldDefinition("permissions", FieldType.JSON, required=True, description="Page-level permissions as JSON object"),
        FieldDefinition("is_primary", FieldType.BOOLEAN, required=True, default_value=False, description="Primary role for this company"),
        FieldDefinition("status", FieldType.ENUM, required=True, default_value="active", enum_values=["active", "inactive", "expired"], description="Role assignment status"),
        FieldDefinition("expires_at", FieldType.DATETIME, required=False, description="Role expiration date"),
        FieldDefinition("granted_by", FieldType.UUID, required=False, foreign_key="users.id", description="User who granted this role")
    ] + standard_fields()
    
    indexes = [
        {"fields": ["user_id"], "unique": False},
        {"fields": ["company_id"], "unique": False},
        {"fields": ["user_id", "company_id"], "unique": False},
        {"fields": ["role", "status"], "unique": False}
    ]
    
    return TableSchema("user_company_roles", fields, indexes, "User role assignments per company")

def permission_templates_schema() -> TableSchema:
    """Permission templates for roles"""
    fields = [
        FieldDefinition("name", FieldType.STRING, required=True, max_length=100, unique=True, description="Template name"),
        FieldDefinition("role", FieldType.ENUM, required=True, 
                       enum_values=["SUPER_ADMIN", "COMPANY_ADMIN", "CONTENT_MANAGER", "REVIEWER", "EDITOR", "VIEWER", "DEVICE_USER"],
                       description="Associated role"),
        FieldDefinition("permissions", FieldType.JSON, required=True, description="Default permissions for this role"),
        FieldDefinition("description", FieldType.TEXT, required=False, description="Template description"),
        FieldDefinition("is_system", FieldType.BOOLEAN, required=True, default_value=True, description="System template (non-editable)"),
        FieldDefinition("company_id", FieldType.UUID, required=False, foreign_key="companies.id", description="Company-specific template (null for system templates)")
    ] + standard_fields()
    
    indexes = [
        {"fields": ["name"], "unique": True},
        {"fields": ["role"], "unique": False},
        {"fields": ["company_id"], "unique": False}
    ]
    
    return TableSchema("permission_templates", fields, indexes, "Permission templates for roles")

def content_schema() -> TableSchema:
    """Content entity schema"""
    fields = [
        FieldDefinition("title", FieldType.STRING, required=True, max_length=200, description="Content title"),
        FieldDefinition("description", FieldType.TEXT, required=False, description="Content description"),
        FieldDefinition("filename", FieldType.STRING, required=True, max_length=255, description="Original filename"),
        FieldDefinition("file_path", FieldType.STRING, required=True, max_length=500, description="Storage file path"),
        FieldDefinition("file_size", FieldType.INTEGER, required=True, description="File size in bytes"),
        FieldDefinition("content_type", FieldType.STRING, required=True, max_length=100, description="MIME type"),
        FieldDefinition("file_hash", FieldType.STRING, required=True, max_length=64, description="File hash for integrity"),
        FieldDefinition("owner_id", FieldType.UUID, required=True, foreign_key="users.id", indexed=True, description="Content owner"),
        FieldDefinition("company_id", FieldType.UUID, required=True, foreign_key="companies.id", indexed=True, description="Owning company"),
        FieldDefinition("status", FieldType.ENUM, required=True, default_value="pending",
                       enum_values=["pending", "reviewing", "approved", "rejected", "archived"],
                       description="Content status"),
        FieldDefinition("moderation_result", FieldType.JSON, required=False, description="AI moderation results"),
        FieldDefinition("reviewer_id", FieldType.UUID, required=False, foreign_key="users.id", description="Human reviewer"),
        FieldDefinition("reviewed_at", FieldType.DATETIME, required=False, description="Review timestamp"),
        FieldDefinition("review_notes", FieldType.TEXT, required=False, description="Review notes"),
        FieldDefinition("duration_seconds", FieldType.INTEGER, required=False, description="Duration for video content"),
        FieldDefinition("thumbnail_path", FieldType.STRING, required=False, max_length=500, description="Thumbnail file path"),
        FieldDefinition("metadata", FieldType.JSON, required=False, description="Additional content metadata"),
        FieldDefinition("tags", FieldType.JSON, required=False, description="Content tags"),
        FieldDefinition("categories", FieldType.JSON, required=False, description="Content categories"),
        FieldDefinition("target_audience", FieldType.JSON, required=False, description="Target audience settings"),
        FieldDefinition("scheduling", FieldType.JSON, required=False, description="Content scheduling settings"),
        FieldDefinition("analytics", FieldType.JSON, required=False, description="Content analytics data")
    ] + standard_fields()
    
    indexes = [
        {"fields": ["owner_id"], "unique": False},
        {"fields": ["company_id"], "unique": False},
        {"fields": ["status"], "unique": False},
        {"fields": ["content_type"], "unique": False},
        {"fields": ["file_hash"], "unique": False},
        {"fields": ["created_at"], "unique": False}
    ]
    
    return TableSchema("content", fields, indexes, "Digital content management")

def devices_schema() -> TableSchema:
    """Device/Screen entity schema"""
    fields = [
        FieldDefinition("name", FieldType.STRING, required=True, max_length=200, description="Device name"),
        FieldDefinition("device_type", FieldType.ENUM, required=True,
                       enum_values=["kiosk", "billboard", "indoor_screen", "outdoor_screen", "interactive_display"],
                       description="Device type"),
        FieldDefinition("company_id", FieldType.UUID, required=True, foreign_key="companies.id", indexed=True, description="Owner company"),
        FieldDefinition("location", FieldType.STRING, required=True, max_length=300, description="Physical location"),
        FieldDefinition("api_key", FieldType.STRING, required=True, unique=True, max_length=255, indexed=True, description="Device API key"),
        FieldDefinition("registration_key", FieldType.STRING, required=False, max_length=255, description="Registration key used"),
        FieldDefinition("device_fingerprint", FieldType.JSON, required=False, description="Device hardware fingerprint"),
        FieldDefinition("capabilities", FieldType.JSON, required=False, description="Device capabilities"),
        FieldDefinition("screen_config", FieldType.JSON, required=True, description="Screen configuration (resolution, orientation, etc.)"),
        FieldDefinition("status", FieldType.ENUM, required=True, default_value="active",
                       enum_values=["active", "inactive", "maintenance", "offline", "error"],
                       description="Device status"),
        FieldDefinition("ip_address", FieldType.STRING, required=False, max_length=45, description="Last known IP address"),
        FieldDefinition("mac_address", FieldType.STRING, required=False, max_length=17, description="MAC address"),
        FieldDefinition("last_seen", FieldType.DATETIME, required=False, description="Last communication timestamp"),
        FieldDefinition("last_heartbeat", FieldType.DATETIME, required=False, description="Last heartbeat timestamp"),
        FieldDefinition("firmware_version", FieldType.STRING, required=False, max_length=50, description="Device firmware version"),
        FieldDefinition("settings", FieldType.JSON, required=False, description="Device-specific settings"),
        FieldDefinition("maintenance_schedule", FieldType.JSON, required=False, description="Maintenance schedule")
    ] + standard_fields()
    
    indexes = [
        {"fields": ["api_key"], "unique": True},
        {"fields": ["company_id"], "unique": False},
        {"fields": ["status"], "unique": False},
        {"fields": ["device_type"], "unique": False},
        {"fields": ["last_seen"], "unique": False}
    ]
    
    return TableSchema("devices", fields, indexes, "Digital signage devices")

def content_schedule_schema() -> TableSchema:
    """Content scheduling schema"""
    fields = [
        FieldDefinition("content_id", FieldType.UUID, required=True, foreign_key="content.id", indexed=True, description="Content ID"),
        FieldDefinition("device_id", FieldType.UUID, required=True, foreign_key="devices.id", indexed=True, description="Device ID"),
        FieldDefinition("company_id", FieldType.UUID, required=True, foreign_key="companies.id", indexed=True, description="Company ID"),
        FieldDefinition("schedule_name", FieldType.STRING, required=True, max_length=200, description="Schedule name"),
        FieldDefinition("start_time", FieldType.DATETIME, required=True, description="Start time"),
        FieldDefinition("end_time", FieldType.DATETIME, required=True, description="End time"),
        FieldDefinition("priority", FieldType.INTEGER, required=True, default_value=5, description="Display priority (1-10)"),
        FieldDefinition("duration_seconds", FieldType.INTEGER, required=False, description="Display duration override"),
        FieldDefinition("repeat_config", FieldType.JSON, required=False, description="Repeat configuration"),
        FieldDefinition("display_config", FieldType.JSON, required=False, description="Display configuration (position, size, effects)"),
        FieldDefinition("status", FieldType.ENUM, required=True, default_value="scheduled",
                       enum_values=["scheduled", "active", "completed", "cancelled", "error"],
                       description="Schedule status"),
        FieldDefinition("last_played", FieldType.DATETIME, required=False, description="Last play timestamp"),
        FieldDefinition("play_count", FieldType.INTEGER, required=True, default_value=0, description="Total play count"),
        FieldDefinition("error_log", FieldType.JSON, required=False, description="Error logs")
    ] + standard_fields()
    
    indexes = [
        {"fields": ["content_id"], "unique": False},
        {"fields": ["device_id"], "unique": False},
        {"fields": ["company_id"], "unique": False},
        {"fields": ["start_time", "end_time"], "unique": False},
        {"fields": ["status"], "unique": False}
    ]
    
    return TableSchema("content_schedule", fields, indexes, "Content scheduling")

def analytics_events_schema() -> TableSchema:
    """Analytics events schema"""
    fields = [
        FieldDefinition("event_type", FieldType.STRING, required=True, max_length=50, indexed=True, description="Event type"),
        FieldDefinition("device_id", FieldType.UUID, required=False, foreign_key="devices.id", indexed=True, description="Device ID"),
        FieldDefinition("content_id", FieldType.UUID, required=False, foreign_key="content.id", indexed=True, description="Content ID"),
        FieldDefinition("company_id", FieldType.UUID, required=False, foreign_key="companies.id", indexed=True, description="Company ID"),
        FieldDefinition("user_id", FieldType.UUID, required=False, foreign_key="users.id", description="User ID"),
        FieldDefinition("session_id", FieldType.STRING, required=False, max_length=100, description="Session ID"),
        FieldDefinition("event_data", FieldType.JSON, required=False, description="Event-specific data"),
        FieldDefinition("timestamp", FieldType.DATETIME, required=True, default_value="NOW()", description="Event timestamp"),
        FieldDefinition("ip_address", FieldType.STRING, required=False, max_length=45, description="Source IP address"),
        FieldDefinition("user_agent", FieldType.STRING, required=False, max_length=500, description="User agent string"),
        FieldDefinition("location", FieldType.JSON, required=False, description="Geographic location data"),
        FieldDefinition("processed", FieldType.BOOLEAN, required=True, default_value=False, description="Processing status")
    ] + [
        # Minimal standard fields for analytics (no soft delete needed)
        FieldDefinition("id", FieldType.UUID, required=True, unique=True, description="Primary key"),
        FieldDefinition("created_at", FieldType.DATETIME, required=True, default_value="NOW()", description="Creation timestamp")
    ]
    
    indexes = [
        {"fields": ["event_type"], "unique": False},
        {"fields": ["device_id"], "unique": False},
        {"fields": ["content_id"], "unique": False},
        {"fields": ["company_id"], "unique": False},
        {"fields": ["timestamp"], "unique": False},
        {"fields": ["processed"], "unique": False}
    ]
    
    return TableSchema("analytics_events", fields, indexes, "Analytics events")

def audit_log_schema() -> TableSchema:
    """Audit log schema"""
    fields = [
        FieldDefinition("entity_type", FieldType.STRING, required=True, max_length=50, indexed=True, description="Entity type"),
        FieldDefinition("entity_id", FieldType.UUID, required=True, indexed=True, description="Entity ID"),
        FieldDefinition("action", FieldType.ENUM, required=True,
                       enum_values=["CREATE", "UPDATE", "DELETE", "LOGIN", "LOGOUT", "ACCESS_DENIED", "PERMISSION_CHANGE"],
                       description="Action performed"),
        FieldDefinition("user_id", FieldType.UUID, required=False, foreign_key="users.id", indexed=True, description="User who performed action"),
        FieldDefinition("company_id", FieldType.UUID, required=False, foreign_key="companies.id", indexed=True, description="Company context"),
        FieldDefinition("old_values", FieldType.JSON, required=False, description="Previous values"),
        FieldDefinition("new_values", FieldType.JSON, required=False, description="New values"),
        FieldDefinition("ip_address", FieldType.STRING, required=False, max_length=45, description="Source IP address"),
        FieldDefinition("user_agent", FieldType.STRING, required=False, max_length=500, description="User agent string"),
        FieldDefinition("timestamp", FieldType.DATETIME, required=True, default_value="NOW()", description="Action timestamp")
    ] + [
        # Minimal standard fields for audit log
        FieldDefinition("id", FieldType.UUID, required=True, unique=True, description="Primary key")
    ]
    
    indexes = [
        {"fields": ["entity_type"], "unique": False},
        {"fields": ["entity_id"], "unique": False},
        {"fields": ["user_id"], "unique": False},
        {"fields": ["company_id"], "unique": False},
        {"fields": ["action"], "unique": False},
        {"fields": ["timestamp"], "unique": False}
    ]
    
    return TableSchema("audit_log", fields, indexes, "System audit log")

# All schemas registry
ALL_SCHEMAS = [
    companies_schema(),
    users_schema(),
    user_company_roles_schema(),
    permission_templates_schema(),
    content_schema(),
    devices_schema(),
    content_schedule_schema(),
    analytics_events_schema(),
    audit_log_schema()
]

def get_schema(table_name: str) -> Optional[TableSchema]:
    """Get schema by table name"""
    return next((schema for schema in ALL_SCHEMAS if schema.name == table_name), None)

def get_all_table_names() -> List[str]:
    """Get all table names"""
    return [schema.name for schema in ALL_SCHEMAS]