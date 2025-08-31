# API Documentation - Adara from Hebron™

## Overview
RESTful API for the Adara digital kiosk content management platform. All endpoints require authentication unless specified otherwise.

**Current Status**: Development phase with core authentication and content management endpoints implemented.

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

## Currently Implemented Endpoints

### System Health
- **GET** `/health` - System health check (no auth required)

### Authentication
- **POST** `/api/auth/token` - OAuth2 password flow login
- **GET** `/api/auth/me` - Get current user info
- **GET** `/api/auth/me/with-roles` - Get user with roles and companies  
- **POST** `/api/auth/switch-role` - Switch user's active role

### Content Management
- **POST** `/api/uploads/media` - Direct media upload (dev mode)
- **POST** `/api/content/metadata` - Save content metadata
- **GET** `/api/content/{id}` - Get content metadata by ID
- **GET** `/api/content/` - List user's content
- **POST** `/api/content/moderation/simulate` - Simulate AI moderation (dev only)

### Company Management  
- **GET** `/api/companies/` - List all companies
- **GET** `/api/companies/{id}` - Get company by ID
- **POST** `/api/companies/` - Create company (admin only)
- **PUT** `/api/companies/{id}` - Update company (admin only)  
- **DELETE** `/api/companies/{id}` - Delete company (admin only)

Planned / Design (to implement):

- POST   /v1/uploads/presign           -> { sasUrl, assetId, maxSize, mimeAllowlist }
- POST   /v1/assets/{id}/finalize      -> enqueue(scan+moderate)
- GET    /v1/moderation/queue          -> [items]
- POST   /v1/moderation/{id}/decision  -> { approved|rejected, notes }
- POST   /v1/playlists                  -> {id}
- POST   /v1/schedules                  -> {id}
- POST   /v1/publish                    -> idempotent publish job
- GET    /v1/publishes/recent          -> status list
- GET    /v1/admin/users               -> list (RLS)
- POST   /v1/admin/users               -> invite
- GET    /v1/audit                     -> filterable audit log

Notes / TODOs:
- Add presigned upload endpoints and server-side finalize flow (replace direct multipart upload in `uploads.media`).
- Implement worker queues for scan_worker and publish_worker and endpoints to query job status.
- Harden auth (Entra ID OIDC + role-based enforcement + token rotation) and document required scopes/claims.
- Add OpenAPI docs examples and request/response schemas for all planned endpoints.
- Implement event-driven architecture with Azure Service Bus.
- Integrate Azure AI Foundry for real AI moderation.

# Workers

scan_worker: ClamAV → MIME sniff → EXIF strip → OCR → AI scores → write moderation_events.

publish_worker: loads PlaylistSpec + ScheduleSpec → calls SignageDriver → persists vendor refs + results.

# Event Framework

Azure Service Bus for message queuing:
- content_uploaded: Trigger moderation workflow
- moderation_completed: Notify stakeholders
- content_approved: Trigger publishing workflow
- publishing_completed: Update status and notify

Docker containers for event processing workers.

# Yodeck integration notes (driver contract)

Capabilities: media upload, playlist/layout management, screen/group assignment, scheduling via REST API. Use service account/API key and keep it in Key Vault. 
Yodeck
+1

Typical sequence:

upsertMedia() → upload approved assets.

upsertPlaylist() → create/patch playlist, order items.

assignToScreens() → set screen groups.

schedule() → create time-bound events (repeat rules supported). 
Yodeck

# Xibo integration notes (optional driver)

Use Xibo CMS API (form-encoded, token-based). Implement playlist and scheduling endpoints; respect widget/playlist semantics