// MongoDB initialization script for OpenKiosk
// This script creates the necessary database and collections with proper indexes

print('🚀 Initializing OpenKiosk MongoDB database...');

// Switch to the openkiosk database
db = db.getSiblingDB('openkiosk');

// Create collections with proper schemas and indexes
print('📋 Creating collections and indexes...');

// Users collection with indexes
db.createCollection('users');
db.users.createIndex({ "email": 1 }, { unique: true });
db.users.createIndex({ "status": 1 });
db.users.createIndex({ "created_at": -1 });

// Companies collection with indexes
db.createCollection('companies');
db.companies.createIndex({ "organization_code": 1 }, { unique: true });
db.companies.createIndex({ "type": 1 });
db.companies.createIndex({ "status": 1 });

// Roles collection with indexes
db.createCollection('roles');
db.roles.createIndex({ "company_id": 1, "role_group": 1 });
db.roles.createIndex({ "is_default": 1 });

// User roles collection with indexes
db.createCollection('user_roles');
db.user_roles.createIndex({ "user_id": 1 });
db.user_roles.createIndex({ "company_id": 1 });
db.user_roles.createIndex({ "role_id": 1 });

// Digital screens (devices) collection with indexes
db.createCollection('digital_screens');
db.digital_screens.createIndex({ "company_id": 1 });
db.digital_screens.createIndex({ "status": 1 });
db.digital_screens.createIndex({ "last_seen": -1 });
db.digital_screens.createIndex({ "mac_address": 1 });

// Device registration keys with indexes
db.createCollection('device_registration_keys');
db.device_registration_keys.createIndex({ "key": 1 }, { unique: true });
db.device_registration_keys.createIndex({ "company_id": 1 });
db.device_registration_keys.createIndex({ "used": 1 });
db.device_registration_keys.createIndex({ "expires_at": 1 });

// Device credentials with indexes
db.createCollection('device_credentials');
db.device_credentials.createIndex({ "device_id": 1 });
db.device_credentials.createIndex({ "jwt_expires_at": 1 });
db.device_credentials.createIndex({ "revoked": 1 });

// Device heartbeats with indexes and TTL
db.createCollection('device_heartbeats');
db.device_heartbeats.createIndex({ "device_id": 1 });
db.device_heartbeats.createIndex({ "timestamp": -1 });
// TTL index to automatically remove old heartbeats (30 days)
db.device_heartbeats.createIndex({ "timestamp": 1 }, { expireAfterSeconds: 2592000 });

// Content metadata with indexes
db.createCollection('content_metadata');
db.content_metadata.createIndex({ "owner_id": 1 });
db.content_metadata.createIndex({ "status": 1 });
db.content_metadata.createIndex({ "created_at": -1 });

// Content meta (uploaded files) with indexes
db.createCollection('content_meta');
db.content_meta.createIndex({ "owner_id": 1 });
db.content_meta.createIndex({ "status": 1 });
db.content_meta.createIndex({ "filename": 1 });
db.content_meta.createIndex({ "created_at": -1 });

// Content distributions with indexes
db.createCollection('content_distributions');
db.content_distributions.createIndex({ "device_id": 1 });
db.content_distributions.createIndex({ "content_id": 1 });
db.content_distributions.createIndex({ "status": 1 });
db.content_distributions.createIndex({ "scheduled_at": 1 });
db.content_distributions.createIndex({ "priority": -1 });

// Reviews collection for moderation
db.createCollection('reviews');
db.reviews.createIndex({ "content_id": 1 });
db.reviews.createIndex({ "action": 1 });

// Role permissions
db.createCollection('role_permissions');
db.role_permissions.createIndex({ "role_id": 1 });

// Layout templates
db.createCollection('layout_templates');
db.layout_templates.createIndex({ "company_id": 1 });
db.layout_templates.createIndex({ "is_public": 1 });

// Content categories and tags
db.createCollection('content_categories');
db.content_categories.createIndex({ "is_active": 1 });

db.createCollection('content_tags');
db.content_tags.createIndex({ "category_id": 1 });
db.content_tags.createIndex({ "is_active": 1 });

// Host preferences
db.createCollection('host_preferences');
db.host_preferences.createIndex({ "company_id": 1 });
db.host_preferences.createIndex({ "screen_id": 1 });

// Company applications
db.createCollection('company_applications');
db.company_applications.createIndex({ "status": 1 });
db.company_applications.createIndex({ "submitted_at": -1 });

// User invitations
db.createCollection('user_invitations');
db.user_invitations.createIndex({ "email": 1 });
db.user_invitations.createIndex({ "invitation_token": 1 }, { unique: true });

// Password reset tokens
db.createCollection('password_reset_tokens');
db.password_reset_tokens.createIndex({ "reset_token": 1 }, { unique: true });
db.password_reset_tokens.createIndex({ "used": 1 });

print('✅ OpenKiosk MongoDB database initialized successfully!');
print('📊 Collections created with proper indexes for optimal performance');
print('🔒 Unique indexes applied for data integrity');
print('⏰ TTL index set for heartbeats (30-day retention)');