# Enhanced RBAC System for Digital Signage Platform

## Overview

This document describes the comprehensive Role-Based Access Control (RBAC) system implemented for the digital signage platform. The system provides fine-grained access control, company isolation, content sharing, and proper audit logging.

## System Architecture

### User Types

1. **Super User (Platform Administrator)**
   - Global access to all platform features
   - Not linked to any specific company
   - Can create and manage Host and Advertiser companies
   - Can see all devices, content, and analytics across the platform
   - Only user type that can perform hard deletes

2. **Company User**
   - Belongs to a specific company (Host or Advertiser)
   - Access is restricted to their company's resources
   - Has one of four company roles: Admin, Reviewer, Editor, or Viewer

3. **Device User**
   - Represents registered devices
   - Used for device authentication and content pulling
   - Each device belongs to a specific company

### Company Types

1. **HOST**
   - Manages physical displays/screens
   - Can share content with other Host companies
   - Receives advertising content from Advertisers
   - Controls content moderation and approval

2. **ADVERTISER**
   - Creates and manages advertising content
   - Cannot share content with other companies
   - Content must be approved by Host companies before display

### Company Roles

Each company (Host or Advertiser) has four distinct roles:

#### 1. Admin
- **Full company management capabilities**
- Can create, edit, and delete other users within the company
- Can share content (if Host company)
- Has all permissions of other roles
- Can perform soft deletes on content
- Can manage device registrations

#### 2. Reviewer
- **Content review and approval focus**
- Can review and approve/reject content
- Can push approved content to devices
- Has Viewer access to all other screens
- Cannot create or manage users
- Cannot share content

#### 3. Editor
- **Content creation and editing**
- Can upload and edit content
- Can push approved content to devices
- Cannot approve content (only create/edit)
- Has basic analytics access
- Cannot manage users or devices

#### 4. Viewer
- **Read-only access with upload capability**
- Can view all pages and search content
- Can upload content (but cannot approve)
- Has basic analytics access
- Cannot edit, delete, or manage anything

## Permission System

### Core Permissions

The system uses granular permissions mapped to specific actions:

```python
# Content permissions
CONTENT_VIEW = "content_view"
CONTENT_CREATE = "content_create"
CONTENT_EDIT = "content_edit"
CONTENT_DELETE = "content_delete"
CONTENT_APPROVE = "content_approve"
CONTENT_SHARE = "content_share"

# User management
USER_VIEW = "user_view"
USER_CREATE = "user_create"
USER_EDIT = "user_edit"
USER_DELETE = "user_delete"

# Device management
DEVICE_VIEW = "device_view"
DEVICE_CREATE = "device_create"
DEVICE_EDIT = "device_edit"
DEVICE_DELETE = "device_delete"
DEVICE_CONTROL = "device_control"

# Analytics and monitoring
ANALYTICS_VIEW = "analytics_view"
ANALYTICS_EXPORT = "analytics_export"
MODERATION_VIEW = "moderation_view"
MODERATION_ACTION = "moderation_action"

# System administration
SYSTEM_SETTINGS = "system_settings"
PLATFORM_ADMIN = "platform_admin"
```

### Permission Matrix

| Role | Content | Users | Devices | Analytics | Moderation | System |
|------|---------|-------|---------|-----------|------------|--------|
| **Super User** | Full | Full | Full | Full | Full | Full |
| **Company Admin** | Full | Company Only | Company Only | Company Only | Company Only | None |
| **Reviewer** | Approve/View | View Only | View/Control | View Only | Full | None |
| **Editor** | Create/Edit | View Only | View Only | View Only | None | None |
| **Viewer** | View/Upload | View Only | View Only | View Only | None | None |
| **Device** | Pull Only | None | None | Report Only | None | None |

## Content Management

### Content Visibility Levels

1. **Private**: Only visible to owner company
2. **Shared**: Shared with specific companies (Host to Host only)
3. **Public**: Visible to all (rarely used, admin only)

### Content Sharing (Host Companies Only)

- Only Host companies can share content with other Host companies
- Advertiser companies cannot share content
- Shared content permissions can be configured:
  - `can_edit`: Allow recipient to edit shared content
  - `can_reshare`: Allow recipient to share with other companies
  - `can_download`: Allow recipient to download content
  - `expires_at`: Optional expiration date for sharing

### Content Deletion

1. **Soft Delete** (Default)
   - Content is marked as deleted but remains in database
   - Can be restored if needed
   - Available to Admin and Super User

2. **Hard Delete** (Compliance)
   - Content is permanently removed from database and storage
   - Cannot be restored
   - Only available to Super User and Company Admin for compliance reasons

## Device Management

### Device Registration

- Each device must be registered to a specific company
- Only users with `DEVICE_CREATE` permission can register devices
- Companies have device limits (configurable)
- Each device receives a unique API key for authentication

### Device Authentication

- Devices authenticate using Device ID + API key
- API keys are used in request headers: `X-Device-ID` and `X-API-Key`
- Failed authentication attempts are logged
- Device status (active/inactive) controls access

### Device Visibility

- Devices are only visible to users of the owning company
- Super Users can see all devices across all companies
- Shared content can be pulled by devices from companies that have sharing relationships

## Implementation

### Key Files

1. **`rbac_models.py`** - Pydantic models for all RBAC entities
2. **`rbac_service.py`** - Core RBAC business logic and permission checking
3. **`enhanced_auth.py`** - Authentication and authorization decorators
4. **`seed_data.py`** - Database initialization with sample RBAC data

### Database Schema

The RBAC system uses the following key collections/tables:

- `users` - User accounts with type and company association
- `companies` - Company information and sharing settings
- `roles` - Role definitions with permissions
- `user_roles` - User-to-role assignments
- `content_shares` - Content sharing relationships
- `device_roles` - Device authentication and permissions
- `audit_logs` - Complete audit trail of all actions

### API Usage Examples

#### Creating a Company User

```python
@router.post("/companies/{company_id}/users")
async def create_company_user(
    company_id: str,
    user_data: CreateCompanyUserRequest,
    current_user: Dict = Depends(require_permission("user", "create"))
):
    return await rbac_service.create_company_user(
        user_data.dict(), 
        company_id, 
        user_data.company_role, 
        current_user["id"]
    )
```

#### Checking Content Access

```python
@router.get("/content/{content_id}")
async def get_content(
    content_id: str,
    current_user: Dict = Depends(require_content_access("view"))
):
    # User already verified to have access to this content
    return await repo.get_content_meta(content_id)
```

#### Sharing Content

```python
@router.post("/content/{content_id}/share")
async def share_content(
    content_id: str,
    share_request: ShareContentRequest,
    current_user: Dict = Depends(require_permission("content", "share"))
):
    return await rbac_service.share_content(
        content_id,
        share_request.target_company_id,
        current_user["id"],
        share_request.dict()
    )
```

## Security Features

### Authentication
- Secure password hashing
- JWT token-based authentication
- Device API key authentication
- Account lockout after failed attempts

### Authorization
- Fine-grained permission checking
- Company isolation enforcement
- Content access control
- Cross-company operation validation

### Audit Logging
- Complete audit trail of all actions
- User identification and timestamps
- Resource type and action tracking
- Success/failure status

### Data Isolation
- Company-based data segregation
- Shared content visibility controls
- Device access restrictions
- Analytics filtering by company

## Migration from Existing System

If migrating from an existing system:

1. **Backup existing data**
2. **Run the RBAC initialization script**
3. **Map existing users to new role structure**
4. **Update API endpoints to use new auth decorators**
5. **Test permission enforcement**
6. **Verify data isolation**

## Configuration

### Environment Variables

```env
# Super user configuration
SUPER_USER_EMAIL=admin@adara.com
SUPER_USER_PASSWORD=secure_password_here

# Company limits
DEFAULT_MAX_USERS_PER_COMPANY=50
DEFAULT_MAX_DEVICES_PER_COMPANY=100

# Security settings
JWT_SECRET_KEY=your_secret_key_here
TOKEN_EXPIRE_MINUTES=30
FAILED_LOGIN_LOCKOUT_MINUTES=30
MAX_FAILED_LOGIN_ATTEMPTS=5
```

### Company Settings

```python
# Content sharing settings (for Host companies)
company_settings = {
    "allow_content_sharing": True,
    "max_shared_companies": 10,
    "require_approval_for_sharing": False
}
```

## Best Practices

1. **Always use permission decorators** on API endpoints
2. **Check company access** for cross-company operations
3. **Log all significant actions** using the audit system
4. **Validate input data** before permission checks
5. **Use soft deletes** unless hard delete is specifically required
6. **Regular audit log reviews** for security monitoring
7. **Test permission boundaries** during development

## Troubleshooting

### Common Issues

1. **Permission Denied Errors**
   - Check user's role assignments
   - Verify company membership
   - Confirm permission mappings

2. **Content Access Issues**
   - Check content ownership
   - Verify sharing relationships
   - Confirm content visibility settings

3. **Device Authentication Failures**
   - Verify API key validity
   - Check device status
   - Confirm company ownership

### Debug Commands

```python
# Check user permissions
permissions = await rbac_service._get_user_permissions(user_id, company_id)

# Verify content access
has_access = await rbac_service.check_content_access(user_id, content_id, "view")

# Get accessible companies
companies = await rbac_service.get_accessible_companies(user_id)
```

## Future Enhancements

1. **Role Templates** - Predefined role configurations
2. **Time-based Permissions** - Temporary access grants
3. **API Rate Limiting** - Per-user/company rate limits
4. **Advanced Audit Queries** - Complex audit log analysis
5. **Multi-factor Authentication** - Enhanced security
6. **Single Sign-On Integration** - Enterprise authentication
7. **Permission Delegation** - Temporary permission sharing
