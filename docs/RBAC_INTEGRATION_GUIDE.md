# RBAC System Integration Guide

## Overview

This guide helps you integrate the new enhanced RBAC system into your existing digital signage platform. The new system replaces the basic role structure with a comprehensive permission-based system.

## Prerequisites

1. **Install Missing Dependencies**
   ```bash
   # Install the missing authentication libraries
   pip install python-jose[cryptography] passlib[bcrypt]
   
   # Or add to requirements.txt
   echo "python-jose[cryptography]" >> requirements.txt
   echo "passlib[bcrypt]" >> requirements.txt
   ```

2. **Update Repository Interface**
   
   Add the missing `update_user` method to your repository. In your existing repo class, add:
   
   ```python
   async def update_user(self, user_id: str, user_data: dict) -> dict:
       """Update user data in the repository"""
       if user_id in self.users:
           self.users[user_id].update(user_data)
           return self.users[user_id]
       raise ValueError(f"User {user_id} not found")
   ```

## Integration Steps

### Step 1: Fix Authentication Dependencies

Replace the simplified authentication in `enhanced_auth.py` with proper JWT handling:

```python
# At the top of enhanced_auth.py, replace the imports:
from jose import JWTError, jwt
from passlib.context import CryptContext

# Replace the simple password context with:
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Replace the simple token functions with proper JWT:
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise JWTError("Invalid token")
        return {"email": email}
    except JWTError:
        raise JWTError("Invalid token")
```

### Step 2: Initialize the RBAC System

Create a startup script to initialize your database with RBAC data:

```python
# Create: backend/content_service/init_rbac.py
import asyncio
from rbac_service import RBACService
from app.repository import InMemoryRepo

async def initialize_rbac():
    """Initialize the RBAC system with default data"""
    repo = InMemoryRepo()
    rbac_service = RBACService(repo)
    
    # Create Super User
    super_user = await rbac_service.create_super_user({
        "email": "admin@openkiosk.com",
        "password": "SecurePassword123!",
        "first_name": "Super",
        "last_name": "Admin"
    })
    print(f"Created Super User: {super_user['email']}")
    
    # Create sample Host company
    host_company = await rbac_service.create_company({
        "name": "Sample Host Company",
        "company_type": "HOST",
        "contact_email": "host@example.com"
    }, super_user["id"])
    
    # Create sample Advertiser company
    advertiser_company = await rbac_service.create_company({
        "name": "Sample Advertiser Company", 
        "company_type": "ADVERTISER",
        "contact_email": "advertiser@example.com"
    }, super_user["id"])
    
    # Create company users
    host_admin = await rbac_service.create_company_user({
        "email": "host.admin@example.com",
        "password": "Password123!",
        "first_name": "Host",
        "last_name": "Admin"
    }, host_company["id"], "ADMIN", super_user["id"])
    
    advertiser_admin = await rbac_service.create_company_user({
        "email": "advertiser.admin@example.com", 
        "password": "Password123!",
        "first_name": "Advertiser",
        "last_name": "Admin"
    }, advertiser_company["id"], "ADMIN", super_user["id"])
    
    print("RBAC system initialized successfully!")
    return {
        "super_user": super_user,
        "host_company": host_company,
        "advertiser_company": advertiser_company,
        "host_admin": host_admin,
        "advertiser_admin": advertiser_admin
    }

if __name__ == "__main__":
    asyncio.run(initialize_rbac())
```

### Step 3: Update Your Main Application

Update your `main.py` to use the new authentication system:

```python
# In your main.py, add the RBAC imports:
from enhanced_auth import (
    authenticate_user, 
    get_current_user, 
    require_permission,
    require_content_access
)
from rbac_service import RBACService

# Initialize RBAC service
rbac_service = RBACService(repo)

# Update your login endpoint:
@app.post("/auth/login")
async def login(credentials: LoginRequest):
    user = await authenticate_user(credentials.email, credentials.password, repo)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": user["email"]})
    return {"access_token": access_token, "token_type": "bearer", "user": user}

# Add logout endpoint:
@app.post("/auth/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    # In a production system, you'd invalidate the token
    return {"message": "Logged out successfully"}

# Update protected endpoints to use new auth:
@app.get("/content")
async def get_content(
    current_user: dict = Depends(require_permission("content", "view"))
):
    # Get content accessible to this user
    return await rbac_service.get_accessible_content(current_user["id"])

@app.post("/content")
async def create_content(
    content_data: ContentCreateRequest,
    current_user: dict = Depends(require_permission("content", "create"))
):
    # Create content with proper ownership
    return await rbac_service.create_content(content_data.dict(), current_user["id"])
```

### Step 4: Update Your Routes

Update your existing routes to use the new permission system:

```python
# Example: Update user management routes
@app.get("/users")
async def get_users(
    current_user: dict = Depends(require_permission("user", "view"))
):
    if current_user["user_type"] == "SUPER_USER":
        # Super user can see all users
        return await repo.get_all_users()
    else:
        # Company users can only see users in their company
        return await rbac_service.get_company_users(current_user["company_id"])

@app.post("/users")
async def create_user(
    user_data: CreateUserRequest,
    current_user: dict = Depends(require_permission("user", "create"))
):
    # Only company admins and super users can create users
    if current_user["user_type"] == "COMPANY_USER":
        # Company user creating another company user
        return await rbac_service.create_company_user(
            user_data.dict(),
            current_user["company_id"],
            user_data.company_role,
            current_user["id"]
        )
    else:
        # Super user can create any type of user
        return await rbac_service.create_user(user_data.dict(), current_user["id"])

# Example: Update device management routes
@app.get("/devices")
async def get_devices(
    current_user: dict = Depends(require_permission("device", "view"))
):
    return await rbac_service.get_accessible_devices(current_user["id"])

@app.post("/devices")
async def register_device(
    device_data: DeviceRegistrationRequest,
    current_user: dict = Depends(require_permission("device", "create"))
):
    return await rbac_service.register_device(
        device_data.dict(),
        current_user["company_id"],
        current_user["id"]
    )
```

### Step 5: Update Frontend Integration

Update your frontend to handle the new user structure and permissions:

```typescript
// Update your user interface
interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  user_type: 'SUPER_USER' | 'COMPANY_USER' | 'DEVICE_USER';
  company_id?: string;
  company_role?: 'ADMIN' | 'REVIEWER' | 'EDITOR' | 'VIEWER';
  permissions: string[];
  is_active: boolean;
}

// Update your auth context
const useAuth = () => {
  const [user, setUser] = useState<User | null>(null);
  
  const hasPermission = (resource: string, action: string): boolean => {
    if (!user) return false;
    if (user.user_type === 'SUPER_USER') return true;
    return user.permissions.includes(`${resource}_${action}`);
  };
  
  const canAccess = (component: string): boolean => {
    switch (component) {
      case 'user_management':
        return hasPermission('user', 'view');
      case 'device_management':
        return hasPermission('device', 'view');
      case 'content_creation':
        return hasPermission('content', 'create');
      case 'content_approval':
        return hasPermission('content', 'approve');
      default:
        return false;
    }
  };
  
  return { user, hasPermission, canAccess };
};
```

### Step 6: Test the Integration

Create a test script to verify the RBAC system works correctly:

```python
# Create: backend/content_service/test_rbac_integration.py
import asyncio
from enhanced_auth import authenticate_user, verify_token, create_access_token
from rbac_service import RBACService
from app.repository import InMemoryRepo

async def test_rbac_integration():
    """Test the complete RBAC system integration"""
    repo = InMemoryRepo()
    rbac_service = RBACService(repo)
    
    print("Testing RBAC Integration...")
    
    # Test 1: Super User Login
    print("\n1. Testing Super User Authentication")
    super_user = await authenticate_user("admin@openkiosk.com", "SecurePassword123!", repo)
    assert super_user is not None, "Super user authentication failed"
    print("✓ Super user authentication successful")
    
    # Test 2: Permission Checking
    print("\n2. Testing Permission System")
    can_create_company = await rbac_service.check_permission(
        super_user["id"], "company", "create"
    )
    assert can_create_company, "Super user should be able to create companies"
    print("✓ Super user has company creation permission")
    
    # Test 3: Company User Creation
    print("\n3. Testing Company User Creation")
    # First create a company
    company = await rbac_service.create_company({
        "name": "Test Company",
        "company_type": "HOST",
        "contact_email": "test@company.com"
    }, super_user["id"])
    
    # Create a company admin
    company_admin = await rbac_service.create_company_user({
        "email": "admin@testcompany.com",
        "password": "Password123!",
        "first_name": "Test",
        "last_name": "Admin"
    }, company["id"], "ADMIN", super_user["id"])
    
    print("✓ Company and admin user created successfully")
    
    # Test 4: Company User Authentication
    print("\n4. Testing Company User Authentication")
    authenticated_admin = await authenticate_user(
        "admin@testcompany.com", "Password123!", repo
    )
    assert authenticated_admin is not None, "Company admin authentication failed"
    print("✓ Company admin authentication successful")
    
    # Test 5: Permission Isolation
    print("\n5. Testing Permission Isolation")
    can_see_all_companies = await rbac_service.check_permission(
        company_admin["id"], "platform", "admin"
    )
    assert not can_see_all_companies, "Company admin should not have platform admin rights"
    print("✓ Company admin properly isolated from platform admin features")
    
    # Test 6: Token Creation and Verification
    print("\n6. Testing Token System")
    token = create_access_token(data={"sub": super_user["email"]})
    decoded = verify_token(token)
    assert decoded["email"] == super_user["email"], "Token verification failed"
    print("✓ Token creation and verification working")
    
    print("\n🎉 All RBAC integration tests passed!")

if __name__ == "__main__":
    asyncio.run(test_rbac_integration())
```

## Migration Checklist

- [ ] Install missing dependencies (`python-jose`, `passlib`)
- [ ] Add `update_user` method to repository
- [ ] Fix authentication imports in `enhanced_auth.py`
- [ ] Run RBAC initialization script
- [ ] Update main application with new auth endpoints
- [ ] Update existing routes to use new permission decorators
- [ ] Update frontend to handle new user structure
- [ ] Test the integration with test script
- [ ] Update API documentation
- [ ] Train users on new role structure

## Common Issues and Solutions

### Issue 1: Missing Dependencies
**Error**: `ModuleNotFoundError: No module named 'jose'`
**Solution**: Install the missing packages:
```bash
pip install python-jose[cryptography] passlib[bcrypt]
```

### Issue 2: Repository Method Missing
**Error**: `AttributeError: 'InMemoryRepo' object has no attribute 'update_user'`
**Solution**: Add the `update_user` method to your repository class.

### Issue 3: Token Verification Fails
**Error**: `JWTError: Invalid token`
**Solution**: Ensure your `SECRET_KEY` is consistent across restarts. Use environment variables.

### Issue 4: Permission Denied for Valid Users
**Error**: `HTTPException: 403 Forbidden`
**Solution**: Check that users have been assigned proper roles and permissions during creation.

## Performance Considerations

1. **Cache Permissions**: Consider caching user permissions to reduce database calls
2. **Audit Log Management**: Implement log rotation for audit logs
3. **Company Isolation**: Use database indexes on company_id fields
4. **Token Refresh**: Implement token refresh for long-running sessions

## Security Recommendations

1. **Use Strong Secrets**: Generate cryptographically secure JWT secrets
2. **HTTPS Only**: Always use HTTPS in production
3. **Rate Limiting**: Implement rate limiting on authentication endpoints
4. **Audit Monitoring**: Set up alerts for suspicious audit log patterns
5. **Regular Reviews**: Periodically review user permissions and company access

## Next Steps

1. Run the integration steps above
2. Test with your existing frontend
3. Review and adjust permissions as needed
4. Train your team on the new RBAC system
5. Monitor the system in production

The enhanced RBAC system provides a solid foundation for secure, scalable user management in your digital signage platform.
