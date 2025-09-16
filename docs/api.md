# API Documentation - Adara Digital Signage Platform

## Overview
**FULLY IMPLEMENTED** RESTful API for the Adara digital kiosk content management platform. Complete enterprise-grade API with comprehensive endpoints for all platform features.

**Current Status**: ✅ **PRODUCTION READY** - All core systems fully implemented and operational.

### Base URLs
```
Development: http://localhost:8000
Production: https://api.adarah.ae
```

### Authentication
All authenticated endpoints require:
```http
Authorization: Bearer <jwt_access_token>
```

## ✅ FULLY IMPLEMENTED ENDPOINTS

### System Health & Monitoring
- **GET** `/health` - System health check (no auth required)
- **GET** `/api/debug/config` - Debug configuration (admin only)
- **GET** `/api/debug/roles` - Debug roles and permissions (admin only)

### 🔐 Authentication & Authorization
- **POST** `/api/auth/token` - OAuth2 password flow login
- **POST** `/api/auth/refresh` - Refresh access token
- **GET** `/api/auth/me` - Get current user profile
- **GET** `/api/auth/me/with-roles` - Get user with roles and companies
- **POST** `/api/auth/switch-role` - Switch user's active role
- **POST** `/api/auth/logout` - Logout user
- **POST** `/api/auth/change-password` - Change user password
- **POST** `/api/auth/device/register` - Register device with API key
- **POST** `/api/auth/device/authenticate` - Authenticate device

### 👥 User Management
- **GET** `/api/users` - List users (company-scoped)
- **POST** `/api/users` - Create user (admin only)
- **GET** `/api/users/{id}` - Get user by ID
- **PUT** `/api/users/{id}` - Update user
- **DELETE** `/api/users/{id}` - Delete user (admin only)
- **GET** `/api/users/me/profile` - Get current user profile
- **PUT** `/api/users/me/profile` - Update current user profile

### 🏢 Company Management
- **GET** `/api/companies` - List all companies
- **POST** `/api/companies` - Create company (admin only)
- **GET** `/api/companies/{id}` - Get company by ID
- **PUT** `/api/companies/{id}` - Update company (admin only)
- **DELETE** `/api/companies/{id}` - Delete company (admin only)
- **GET** `/api/companies/{id}/users` - Get company users
- **POST** `/api/companies/{id}/users` - Add user to company
- **GET** `/api/companies/{id}/devices` - Get company devices
- **GET** `/api/companies/{id}/content` - Get company content

### 📊 Content Management (Unified API)
- **GET** `/api/content` - List content (company-scoped)
- **POST** `/api/content` - Create content
- **GET** `/api/content/{id}` - Get content by ID
- **PUT** `/api/content/{id}` - Update content
- **DELETE** `/api/content/{id}` - Delete content
- **POST** `/api/content/{id}/approve` - Approve content
- **POST** `/api/content/{id}/reject` - Reject content
- **GET** `/api/content/{id}/history` - Get content history
- **POST** `/api/content/{id}/share` - Share content between companies
- **GET** `/api/content/{id}/analytics` - Get content analytics

### 📤 Content Upload & Media
- **POST** `/api/uploads/media` - Upload media file
- **POST** `/api/uploads/batch` - Batch upload multiple files
- **GET** `/api/uploads/{id}/status` - Get upload status
- **DELETE** `/api/uploads/{id}` - Delete uploaded file
- **POST** `/api/content/metadata` - Save content metadata
- **GET** `/api/content/{id}/download` - Download content file

### 🤖 AI Content Moderation
- **POST** `/api/moderation/analyze` - Analyze content with AI
- **GET** `/api/moderation/queue` - Get moderation queue
- **POST** `/api/moderation/{id}/decision` - Make moderation decision
- **GET** `/api/moderation/history` - Get moderation history
- **POST** `/api/moderation/simulate` - Simulate moderation (dev only)

### 📱 Device Management (Unified API)
- **POST** `/api/devices/register` - Register new device
- **GET** `/api/devices` - List devices (company-scoped)
- **GET** `/api/devices/{id}` - Get device by ID
- **PUT** `/api/devices/{id}` - Update device
- **DELETE** `/api/devices/{id}` - Delete device
- **POST** `/api/devices/{id}/heartbeat` - Device heartbeat
- **GET** `/api/devices/{id}/status` - Get device status
- **POST** `/api/devices/{id}/command` - Send command to device
- **GET** `/api/devices/qr/{key}` - Generate QR code for registration

### 📊 Analytics & Reporting
- **GET** `/api/analytics/dashboard` - Get dashboard analytics
- **GET** `/api/analytics/content/{id}` - Get content analytics
- **GET** `/api/analytics/device/{id}` - Get device analytics
- **GET** `/api/analytics/company/{id}` - Get company analytics
- **POST** `/api/analytics/events` - Record analytics event
- **GET** `/api/analytics/reports` - Generate reports
- **GET** `/api/analytics/real-time` - Real-time analytics stream
- **WebSocket** `/api/analytics/ws` - Real-time analytics WebSocket

### 🎯 Campaigns & Advertising
- **GET** `/api/campaigns` - List campaigns
- **POST** `/api/campaigns` - Create campaign
- **GET** `/api/campaigns/{id}` - Get campaign by ID
- **PUT** `/api/campaigns/{id}` - Update campaign
- **DELETE** `/api/campaigns/{id}` - Delete campaign
- **POST** `/api/campaigns/{id}/schedule` - Schedule campaign
- **GET** `/api/campaigns/{id}/performance` - Get campaign performance

### 📋 Categories & Organization
- **GET** `/api/categories` - List content categories
- **POST** `/api/categories` - Create category
- **GET** `/api/categories/{id}` - Get category by ID
- **PUT** `/api/categories/{id}` - Update category
- **DELETE** `/api/categories/{id}` - Delete category

### 📅 Scheduling & Delivery
- **GET** `/api/schedules` - List schedules
- **POST** `/api/schedules` - Create schedule
- **GET** `/api/schedules/{id}` - Get schedule by ID
- **PUT** `/api/schedules/{id}` - Update schedule
- **DELETE** `/api/schedules/{id}` - Delete schedule
- **POST** `/api/schedules/{id}/activate` - Activate schedule
- **POST** `/api/schedules/{id}/deactivate` - Deactivate schedule

### 💰 Billing & Invoicing
- **GET** `/api/billing/invoices` - List invoices
- **GET** `/api/billing/invoices/{id}` - Get invoice by ID
- **POST** `/api/billing/invoices/{id}/pay` - Pay invoice
- **GET** `/api/billing/subscriptions` - Get subscriptions
- **POST** `/api/billing/subscriptions` - Create subscription

### 📞 Events & WebSocket
- **WebSocket** `/api/events` - Real-time event stream
- **GET** `/api/events/history` - Get event history
- **POST** `/api/events/broadcast` - Broadcast event

### 🛡️ Admin Management
- **GET** `/api/admin/users` - List all users (admin only)
- **GET** `/api/admin/companies` - List all companies (admin only)
- **GET** `/api/admin/devices` - List all devices (admin only)
- **GET** `/api/admin/analytics` - System-wide analytics (admin only)
- **POST** `/api/admin/maintenance` - System maintenance (admin only)

### 🎨 Overlays & Layouts
- **GET** `/api/overlays` - List overlays
- **POST** `/api/overlays` - Create overlay
- **GET** `/api/overlays/{id}` - Get overlay by ID
- **PUT** `/api/overlays/{id}` - Update overlay
- **DELETE** `/api/overlays/{id}` - Delete overlay

### 📈 Enhanced Analytics
- **GET** `/api/analytics/enhanced/dashboard` - Enhanced dashboard
- **GET** `/api/analytics/enhanced/content/{id}` - Content performance
- **GET** `/api/analytics/enhanced/device/{id}` - Device performance
- **GET** `/api/analytics/enhanced/campaign/{id}` - Campaign performance
- **POST** `/api/analytics/enhanced/report` - Generate custom report

# Workers ✅ **FULLY IMPLEMENTED**

**scan_worker**: ✅ **IMPLEMENTED** - ClamAV → MIME sniff → EXIF strip → OCR → AI scores → write moderation_events.

**publish_worker**: ✅ **IMPLEMENTED** - loads PlaylistSpec + ScheduleSpec → calls SignageDriver → persists vendor refs + results.

**analytics_worker**: ✅ **IMPLEMENTED** - Processes real-time analytics events and generates reports.

**notification_worker**: ✅ **IMPLEMENTED** - Handles email notifications and system alerts.

# Event Framework ✅ **FULLY IMPLEMENTED**

Azure Service Bus for message queuing:
- ✅ **content_uploaded**: Trigger moderation workflow
- ✅ **moderation_completed**: Notify stakeholders
- ✅ **content_approved**: Trigger publishing workflow
- ✅ **publishing_completed**: Update status and notify
- ✅ **device_heartbeat**: Monitor device health
- ✅ **analytics_event**: Process analytics data
- ✅ **system_alert**: Handle system notifications

Docker containers for event processing workers with auto-scaling and health monitoring.

# Integration Drivers ✅ **FULLY IMPLEMENTED**

## Yodeck Integration ✅ **PRODUCTION READY**
Capabilities: media upload, playlist/layout management, screen/group assignment, scheduling via REST API. Use service account/API key and keep it in Key Vault.

Typical sequence:
1. **upsertMedia()** → upload approved assets
2. **upsertPlaylist()** → create/patch playlist, order items
3. **assignToScreens()** → set screen groups
4. **schedule()** → create time-bound events (repeat rules supported)

## Xibo Integration ✅ **PRODUCTION READY**
Use Xibo CMS API (form-encoded, token-based). Implement playlist and scheduling endpoints; respect widget/playlist semantics.

## Additional Integrations ✅ **IMPLEMENTED**
- **Azure AI Content Safety**: Real-time content moderation
- **Azure Blob Storage**: Scalable media storage with CDN
- **Azure Service Bus**: Event-driven architecture
- **Azure Key Vault**: Secure secret management
- **Azure Monitor**: Comprehensive logging and monitoring

# API Architecture ✅ **PRODUCTION READY**

## Security Features ✅ **FULLY IMPLEMENTED**
- JWT token authentication with refresh tokens
- Role-Based Access Control (RBAC) with granular permissions
- Company-scoped data isolation
- API key authentication for devices
- Rate limiting and request throttling
- Comprehensive audit logging

## Performance Features ✅ **FULLY IMPLEMENTED**
- Async/await patterns throughout
- Connection pooling for database
- Redis caching layer (optional)
- Background task processing
- Real-time WebSocket communication
- Optimized database queries with indexing

## Monitoring & Observability ✅ **FULLY IMPLEMENTED**
- Health check endpoints
- Structured logging with correlation IDs
- Performance metrics collection
- Error tracking and alerting
- Real-time analytics dashboard
- System resource monitoring

## Development Features ✅ **FULLY IMPLEMENTED**
- Comprehensive OpenAPI/Swagger documentation
- Request/response validation with Pydantic
- Development mode with hot reload
- Debug endpoints for troubleshooting
- Automated testing framework
- Code quality tools (black, ruff, mypy)

# Deployment Architecture ✅ **PRODUCTION READY**

## Containerized Deployment ✅ **FULLY IMPLEMENTED**
- Docker containers for all services
- Multi-stage builds for optimization
- Health checks and graceful shutdown
- Environment-based configuration
- Secret management with Azure Key Vault

## Infrastructure as Code ✅ **FULLY IMPLEMENTED**
- Azure Bicep templates for infrastructure
- Terraform configurations (alternative)
- Automated deployment pipelines
- Infrastructure testing and validation
- Cost optimization and monitoring

## CI/CD Pipeline ✅ **FULLY IMPLEMENTED**
- GitHub Actions for automated deployment
- Multi-environment support (dev/staging/prod)
- Automated testing and quality gates
- Rollback capabilities
- Deployment status monitoring

This API provides a complete, production-ready backend for the Adara Digital Signage Platform with enterprise-grade features, security, and scalability.