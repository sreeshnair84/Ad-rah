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

### Planned Security Features
1. **Machine Learning**: Behavioral analysis for anomaly detection
2. **Geographic Restrictions**: Location-based registration controls
3. **Certificate Pinning**: Enhanced device certificate validation
4. **Biometric Verification**: Hardware-based device attestation
5. **Zero Trust**: Continuous device verification

### Integration Opportunities
1. **SIEM Integration**: Export security events to SIEM systems
2. **Threat Intelligence**: Integration with IP reputation services
3. **Analytics Platform**: Advanced security analytics dashboard
4. **Mobile Device Management**: Integration with MDM solutions

---

## 🔄 Advanced Permission Features

### Dynamic Permission Evaluation

The RBAC system supports dynamic permission evaluation based on runtime context:

```python
class DynamicPermissionEvaluator:
    async def evaluate_permission(
        self,
        user_id: str,
        permission: str,
        resource_type: str,
        resource_id: str,
        context: dict = None
    ) -> PermissionResult:
        """
        Evaluate permission with contextual information
        """
        # Get base user permissions
        base_permissions = await self._get_user_permissions(user_id)

        # Apply contextual rules
        if resource_type == "content":
            return await self._evaluate_content_permission(
                user_id, permission, resource_id, context
            )
        elif resource_type == "device":
            return await self._evaluate_device_permission(
                user_id, permission, resource_id, context
            )

        return PermissionResult(
            granted=permission in base_permissions,
            reason="Base permission check"
        )
```

### Time-Based Permissions

Implement time-based access controls for temporary permissions:

```python
class TimeBasedPermission:
    def __init__(self, permission: str, start_time: datetime, end_time: datetime):
        self.permission = permission
        self.start_time = start_time
        self.end_time = end_time

    def is_active(self, current_time: datetime = None) -> bool:
        if current_time is None:
            current_time = datetime.utcnow()
        return self.start_time <= current_time <= self.end_time

# Usage in permission checking
async def check_time_based_permission(
    user_id: str,
    permission: str,
    current_time: datetime = None
) -> bool:
    time_permissions = await get_user_time_permissions(user_id)

    for tp in time_permissions:
        if tp.permission == permission and tp.is_active(current_time):
            return True

    return False
```

### Hierarchical Permission Inheritance

Support for hierarchical permission structures:

```python
PERMISSION_HIERARCHY = {
    "content_admin": ["content_create", "content_edit", "content_delete", "content_approve"],
    "device_admin": ["device_create", "device_edit", "device_delete", "device_control"],
    "user_admin": ["user_create", "user_edit", "user_delete", "user_view"],
    "super_admin": ["content_admin", "device_admin", "user_admin", "system_settings"]
}

def expand_permissions(assigned_permissions: List[str]) -> Set[str]:
    """
    Expand hierarchical permissions to individual permissions
    """
    expanded = set(assigned_permissions)

    for permission in assigned_permissions:
        if permission in PERMISSION_HIERARCHY:
            expanded.update(PERMISSION_HIERARCHY[permission])

    return expanded
```

## 🏢 Multi-Tenant Architecture Extensions

### Cross-Company Content Sharing

Advanced content sharing with granular permissions:

```python
class ContentSharingManager:
    async def share_content(
        self,
        content_id: str,
        from_company_id: str,
        to_company_id: str,
        permissions: List[str],
        expires_at: datetime = None
    ) -> str:
        """
        Share content between companies with specific permissions
        """
        share_id = str(uuid4())

        share_record = {
            "_id": share_id,
            "content_id": content_id,
            "from_company_id": from_company_id,
            "to_company_id": to_company_id,
            "permissions": permissions,
            "expires_at": expires_at,
            "created_at": datetime.utcnow(),
            "status": "ACTIVE"
        }

        await self.db.content_shares.insert_one(share_record)
        return share_id

    async def check_shared_access(
        self,
        user_id: str,
        content_id: str,
        required_permission: str
    ) -> bool:
        """
        Check if user has access to shared content
        """
        user_company = await self.get_user_company(user_id)

        share = await self.db.content_shares.find_one({
            "content_id": content_id,
            "to_company_id": user_company,
            "status": "ACTIVE",
            "$or": [
                {"expires_at": {"$exists": False}},
                {"expires_at": {"$gt": datetime.utcnow()}}
            ]
        })

        if not share:
            return False

        return required_permission in share.get("permissions", [])
```

### Company-Based Resource Quotas

Implement resource quotas per company:

```python
class CompanyQuotaManager:
    async def check_quota(
        self,
        company_id: str,
        resource_type: str,
        requested_amount: int = 1
    ) -> QuotaCheckResult:
        """
        Check if company has quota for resource usage
        """
        quota = await self.get_company_quota(company_id, resource_type)
        current_usage = await self.get_current_usage(company_id, resource_type)

        available = quota - current_usage

        return QuotaCheckResult(
            allowed=available >= requested_amount,
            available=available,
            requested=requested_amount,
            quota=quota
        )

    async def allocate_resource(
        self,
        company_id: str,
        resource_type: str,
        amount: int = 1
    ) -> bool:
        """
        Allocate resource quota for company
        """
        quota_check = await self.check_quota(company_id, resource_type, amount)

        if not quota_check.allowed:
            return False

        # Allocate the resource
        await self.increment_usage(company_id, resource_type, amount)
        return True
```

## 🔐 Advanced Security Features

### Session Management

Enhanced session tracking and management:

```python
class SessionManager:
    async def create_session(
        self,
        user_id: str,
        device_info: dict,
        ip_address: str
    ) -> str:
        """
        Create a new user session with tracking
        """
        session_id = str(uuid4())

        session_data = {
            "_id": session_id,
            "user_id": user_id,
            "device_info": device_info,
            "ip_address": ip_address,
            "created_at": datetime.utcnow(),
            "last_activity": datetime.utcnow(),
            "status": "ACTIVE",
            "token_hash": None  # Will be set when token is issued
        }

        await self.db.sessions.insert_one(session_data)
        return session_id

    async def validate_session(
        self,
        session_id: str,
        token_hash: str = None
    ) -> SessionValidationResult:
        """
        Validate session and update activity
        """
        session = await self.db.sessions.find_one({"_id": session_id})

        if not session or session["status"] != "ACTIVE":
            return SessionValidationResult(valid=False, reason="Invalid session")

        # Check session expiry (24 hours default)
        if datetime.utcnow() - session["created_at"] > timedelta(hours=24):
            await self.invalidate_session(session_id)
            return SessionValidationResult(valid=False, reason="Session expired")

        # Update last activity
        await self.db.sessions.update_one(
            {"_id": session_id},
            {"$set": {"last_activity": datetime.utcnow()}}
        )

        return SessionValidationResult(valid=True)
```

### Audit Trail Enhancements

Comprehensive audit logging with advanced features:

```python
class AdvancedAuditLogger:
    async def log_action(
        self,
        user_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        details: dict = None,
        severity: str = "INFO"
    ) -> str:
        """
        Log user action with enhanced details
        """
        audit_entry = {
            "_id": str(uuid4()),
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "company_id": await self.get_user_company(user_id),
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "details": details or {},
            "severity": severity,
            "ip_address": await self.get_client_ip(),
            "user_agent": await self.get_user_agent(),
            "session_id": await self.get_current_session_id(),
            "location": await self.get_geolocation()
        }

        await self.db.audit_logs.insert_one(audit_entry)

        # Check for suspicious activity
        if await self.detect_suspicious_activity(audit_entry):
            await self.trigger_security_alert(audit_entry)

        return audit_entry["_id"]

    async def detect_suspicious_activity(self, audit_entry: dict) -> bool:
        """
        Detect potentially suspicious user activity
        """
        # Check for rapid successive actions
        recent_actions = await self.get_recent_user_actions(
            audit_entry["user_id"], minutes=5
        )

        if len(recent_actions) > 10:  # More than 10 actions in 5 minutes
            return True

        # Check for actions on unusual hours
        if await self.is_unusual_hour(audit_entry["timestamp"]):
            return True

        # Check for actions from unusual locations
        if await self.is_unusual_location(audit_entry["location"]):
            return True

        return False
```

## 📊 Analytics and Reporting

### Permission Usage Analytics

Track permission usage patterns:

```python
class PermissionAnalytics:
    async def get_permission_usage_report(
        self,
        company_id: str = None,
        start_date: datetime = None,
        end_date: datetime = None
    ) -> dict:
        """
        Generate permission usage analytics
        """
        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start_date, "$lte": end_date},
                **({"company_id": company_id} if company_id else {})
            }},
            {"$group": {
                "_id": {
                    "action": "$action",
                    "user_id": "$user_id"
                },
                "count": {"$sum": 1},
                "last_used": {"$max": "$timestamp"}
            }},
            {"$group": {
                "_id": "$_id.action",
                "total_uses": {"$sum": "$count"},
                "unique_users": {"$addToSet": "$_id.user_id"},
                "avg_uses_per_user": {"$avg": "$count"}
            }}
        ]

        results = await self.db.audit_logs.aggregate(pipeline).to_list(None)

        return {
            "period": {"start": start_date, "end": end_date},
            "company_id": company_id,
            "permission_usage": results
        }

    async def get_role_effectiveness_report(self, company_id: str) -> dict:
        """
        Analyze role effectiveness and permission utilization
        """
        # Get all users and their roles
        users = await self.db.users.find({"company_id": company_id}).to_list(None)

        role_stats = {}
        for user in users:
            role = user.get("company_role", "UNKNOWN")
            if role not in role_stats:
                role_stats[role] = {
                    "user_count": 0,
                    "total_actions": 0,
                    "avg_actions_per_user": 0
                }

            role_stats[role]["user_count"] += 1

            # Get user's action count
            action_count = await self.db.audit_logs.count_documents({
                "user_id": user["_id"],
                "timestamp": {"$gte": datetime.utcnow() - timedelta(days=30)}
            })

            role_stats[role]["total_actions"] += action_count

        # Calculate averages
        for role, stats in role_stats.items():
            if stats["user_count"] > 0:
                stats["avg_actions_per_user"] = stats["total_actions"] / stats["user_count"]

        return role_stats
```

## 🔧 API Integration Examples

### FastAPI Permission Decorators

Enhanced permission decorators for FastAPI:

```python
from fastapi import Depends, HTTPException
from typing import Callable, Any
import functools

def require_permissions(*required_permissions: str, require_all: bool = True):
    """
    Decorator to require specific permissions
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Extract current user from kwargs (injected by auth middleware)
            current_user = kwargs.get("current_user")
            if not current_user:
                raise HTTPException(status_code=401, detail="Authentication required")

            # Check permissions
            user_permissions = set(current_user.get("permissions", []))
            required_set = set(required_permissions)

            if require_all:
                has_permission = required_set.issubset(user_permissions)
            else:
                has_permission = bool(required_set.intersection(user_permissions))

            if not has_permission:
                raise HTTPException(
                    status_code=403,
                    detail=f"Missing required permissions: {required_permissions}"
                )

            return await func(*args, **kwargs)
        return wrapper
    return decorator

# Usage in API endpoints
@router.post("/content/{content_id}/approve")
@require_permissions("content_approve")
async def approve_content(
    content_id: str,
    approval_data: ApprovalRequest,
    current_user: dict = Depends(get_current_user)
):
    """Approve content with proper permission checking"""
    return await content_service.approve_content(content_id, approval_data, current_user)
```

### Advanced Resource-Based Access Control

Implement attribute-based access control (ABAC):

```python
class AttributeBasedAccessControl:
    async def check_access(
        self,
        user: dict,
        action: str,
        resource: dict,
        context: dict = None
    ) -> AccessDecision:
        """
        Check access based on user attributes, resource attributes, and context
        """
        # User attributes
        user_attrs = {
            "role": user.get("company_role"),
            "department": user.get("department"),
            "clearance_level": user.get("clearance_level", 1),
            "company_id": user.get("company_id")
        }

        # Resource attributes
        resource_attrs = {
            "owner_id": resource.get("owner_id"),
            "sensitivity": resource.get("sensitivity", "normal"),
            "department": resource.get("department"),
            "classification": resource.get("classification", "internal")
        }

        # Context attributes
        context_attrs = context or {}
        context_attrs.update({
            "time_of_day": datetime.utcnow().hour,
            "location": await self.get_request_location(),
            "device_type": await self.get_device_type()
        })

        # Evaluate policies
        policies = await self.get_applicable_policies(action, resource_attrs)

        for policy in policies:
            if await self.evaluate_policy(policy, user_attrs, resource_attrs, context_attrs):
                return AccessDecision(
                    granted=True,
                    policy_id=policy["_id"],
                    reason=f"Granted by policy: {policy['name']}"
                )

        return AccessDecision(
            granted=False,
            reason="No applicable policy grants access"
        )

    async def evaluate_policy(
        self,
        policy: dict,
        user_attrs: dict,
        resource_attrs: dict,
        context_attrs: dict
    ) -> bool:
        """
        Evaluate a single policy against attributes
        """
        conditions = policy.get("conditions", [])

        for condition in conditions:
            if not await self.evaluate_condition(condition, user_attrs, resource_attrs, context_attrs):
                return False

        return True
```

## 📈 Performance Optimization

### Permission Caching Strategy

Implement efficient permission caching:

```python
class PermissionCache:
    def __init__(self, redis_client, ttl_seconds: int = 300):
        self.redis = redis_client
        self.ttl = ttl_seconds

    async def get_user_permissions(self, user_id: str) -> Optional[List[str]]:
        """
        Get cached user permissions
        """
        cache_key = f"user_permissions:{user_id}"
        cached = await self.redis.get(cache_key)

        if cached:
            return json.loads(cached)

        return None

    async def set_user_permissions(self, user_id: str, permissions: List[str]):
        """
        Cache user permissions
        """
        cache_key = f"user_permissions:{user_id}"
        await self.redis.setex(
            cache_key,
            self.ttl,
            json.dumps(permissions)
        )

    async def invalidate_user_permissions(self, user_id: str):
        """
        Invalidate user permission cache
        """
        cache_key = f"user_permissions:{user_id}"
        await self.redis.delete(cache_key)

    async def get_company_permissions(self, company_id: str) -> Optional[dict]:
        """
        Get cached company permission structure
        """
        cache_key = f"company_permissions:{company_id}"
        cached = await self.redis.get(cache_key)

        if cached:
            return json.loads(cached)

        return None
```

### Database Query Optimization

Optimized database queries for permission checking:

```python
class OptimizedPermissionQueries:
    async def get_user_permissions_optimized(self, user_id: str) -> List[str]:
        """
        Optimized query to get user permissions with minimal database calls
        """
        # Use aggregation pipeline for efficient permission resolution
        pipeline = [
            {"$match": {"_id": ObjectId(user_id)}},
            {"$lookup": {
                "from": "user_roles",
                "localField": "_id",
                "foreignField": "user_id",
                "as": "user_roles"
            }},
            {"$unwind": "$user_roles"},
            {"$lookup": {
                "from": "roles",
                "localField": "user_roles.role_id",
                "foreignField": "_id",
                "as": "role_details"
            }},
            {"$unwind": "$role_details"},
            {"$group": {
                "_id": None,
                "permissions": {"$addToSet": "$role_details.permissions"}
            }},
            {"$project": {
                "permissions": {
                    "$reduce": {
                        "input": "$permissions",
                        "initialValue": [],
                        "in": {"$setUnion": ["$$value", "$$this"]}
                    }
                }
            }}
        ]

        result = await self.db.users.aggregate(pipeline).to_list(1)

        if result:
            return result[0].get("permissions", [])

        return []
```

## 🔍 Monitoring and Observability

### Permission Metrics Collection

Collect comprehensive permission usage metrics:

```python
class PermissionMetricsCollector:
    async def record_permission_check(
        self,
        user_id: str,
        permission: str,
        resource_type: str,
        granted: bool,
        response_time_ms: float,
        context: dict = None
    ):
        """
        Record permission check metrics
        """
        metric_data = {
            "timestamp": datetime.utcnow(),
            "user_id": user_id,
            "permission": permission,
            "resource_type": resource_type,
            "granted": granted,
            "response_time_ms": response_time_ms,
            "context": context or {}
        }

        # Store in time-series database or metrics system
        await self.metrics_db.permission_checks.insert_one(metric_data)

        # Update real-time counters
        await self.update_realtime_counters(metric_data)

    async def get_permission_metrics(
        self,
        time_range: str = "1h",
        group_by: str = "permission"
    ) -> dict:
        """
        Get permission usage metrics
        """
        # Calculate time range
        end_time = datetime.utcnow()
        if time_range.endswith("h"):
            start_time = end_time - timedelta(hours=int(time_range[:-1]))
        elif time_range.endswith("d"):
            start_time = end_time - timedelta(days=int(time_range[:-1]))
        else:
            start_time = end_time - timedelta(hours=1)

        pipeline = [
            {"$match": {
                "timestamp": {"$gte": start_time, "$lte": end_time}
            }},
            {"$group": {
                "_id": f"${group_by}",
                "total_checks": {"$sum": 1},
                "granted": {"$sum": {"$cond": ["$granted", 1, 0]}},
                "denied": {"$sum": {"$cond": ["$granted", 0, 1]}},
                "avg_response_time": {"$avg": "$response_time_ms"},
                "max_response_time": {"$max": "$response_time_ms"}
            }}
        ]

        results = await self.metrics_db.permission_checks.aggregate(pipeline).to_list(None)

        return {
            "time_range": {"start": start_time, "end": end_time},
            "group_by": group_by,
            "metrics": results
        }
```

This enhanced RBAC system provides enterprise-grade access control with advanced features like dynamic permissions, time-based access, hierarchical inheritance, comprehensive audit trails, and performance optimizations. The system is designed to scale with growing business needs while maintaining security and compliance requirements.
