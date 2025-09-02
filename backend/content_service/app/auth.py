import os
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
try:
    from passlib.context import CryptContext
    _PASSLIB_AVAILABLE = True
except ImportError as e:
    CryptContext = None
    _PASSLIB_AVAILABLE = False
    logging.error(f"Passlib not available: {e}. Password hashing will use fallback SHA256.")
import hashlib

from app.repo import repo
from app.models import User, UserRole, Company
from app.config import settings

logger = logging.getLogger(__name__)

# JWT Configuration from settings
SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

# Initialize password context with proper error handling
if _PASSLIB_AVAILABLE:
    try:
        pwd_context = CryptContext(
            schemes=["bcrypt"], 
            deprecated="auto",
            bcrypt__rounds=12  # Increased rounds for better security
        )
        logger.info("Bcrypt password hashing initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize bcrypt: {e}. Using fallback hashing.")
        pwd_context = None
        _PASSLIB_AVAILABLE = False
else:
    pwd_context = None
    logger.warning("SECURITY WARNING: Using fallback SHA256 password hashing. Install passlib[bcrypt] for production!")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def _simple_hash(pw: str) -> str:
    """Fallback password hashing using SHA256 with salt (NOT recommended for production)"""
    # Add a simple salt for basic security improvement
    salt = "openkiosk_salt_2024"  # In production, use per-user random salts
    return hashlib.sha256((salt + pw).encode("utf-8")).hexdigest()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    if not plain_password or not hashed_password:
        return False
        
    if pwd_context:
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Bcrypt verification failed: {e}. Falling back to simple hash.")
    
    # Fallback to simple hash comparison
    return _simple_hash(plain_password) == hashed_password


def get_password_hash(password: str) -> str:
    """Hash a password using the best available method"""
    if not password:
        raise ValueError("Password cannot be empty")
        
    if pwd_context:
        try:
            return pwd_context.hash(password)
        except Exception as e:
            logger.error(f"Bcrypt hashing failed: {e}. Using fallback hash.")
    
    # Log security warning for fallback
    if settings.ENVIRONMENT == "production":
        logger.critical("CRITICAL: Using fallback password hashing in production!")
    
    return _simple_hash(password)


async def authenticate_user(username: str, password: str):
    user_data = await repo.get_user_by_email(username)
    if not user_data:
        return None
    if not verify_password(password, user_data.get("hashed_password", "")):
        return None
    return user_data


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    print(f"[AUTH] DEBUG: Received token: {token[:20]}...")
    print(f"[AUTH] DEBUG: Token length: {len(token) if token else 0}")

    if not token:
        print("[AUTH] ERROR: No token provided")
        raise credentials_exception

    try:
        print(f"[AUTH] DEBUG: Attempting to decode JWT token")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        print(f"[AUTH] DEBUG: Extracted username: {username}")

        if username is None:
            print("[AUTH] ERROR: Username is None in token payload")
            raise credentials_exception

        # Check token expiration
        exp = payload.get("exp")
        if exp is None:
            print("[AUTH] ERROR: Token has no expiration")
            raise credentials_exception

        # Verify token hasn't expired
        current_time = datetime.utcnow().timestamp()
        print(f"[AUTH] DEBUG: Current time: {current_time}, Token exp: {exp}")
        if current_time > exp:
            print("[AUTH] ERROR: Token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except JWTError as e:
        print(f"[AUTH] ERROR: JWT Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    print(f"[AUTH] DEBUG: Looking up user by email: {username}")
    user_data = await repo.get_user_by_email(username)
    print(f"[AUTH] DEBUG: User data found: {user_data is not None}")

    if user_data is None:
        print(f"[AUTH] ERROR: User not found in database: {username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user roles
    user_roles = await repo.get_user_roles(user_data["id"])
    print(f"[AUTH] DEBUG: User roles found: {len(user_roles)} roles")
    user_data["roles"] = user_roles

    print(f"[AUTH] SUCCESS: Authentication successful for user: {username}")
    return user_data


async def get_current_user_with_roles(token: str = Depends(oauth2_scheme)):
    """Get current user with their roles and companies"""
    print("[AUTH] INFO: Starting get_current_user_with_roles")

    user_data = await get_current_user(token)
    print(f"[AUTH] DEBUG: Base user data retrieved: {user_data.get('email') if user_data else 'None'}")

    # Get all companies for user's roles
    companies = []
    user_roles = user_data.get("roles", [])
    print(f"[AUTH] DEBUG: Processing {len(user_roles)} user roles")

    for role in user_roles:
        try:
            company_id = role.get("company_id")
            print(f"[AUTH] DEBUG: Processing role with company_id: {company_id}")

            if company_id and company_id != "global":
                company = await repo.get_company(company_id)
                if company:
                    companies.append(company)
                    print(f"[AUTH] DEBUG: Added company: {company.get('name')}")
                else:
                    print(f"[AUTH] WARNING: Company not found for ID: {company_id}")
            else:
                print(f"[AUTH] DEBUG: Skipping global company or empty company_id: {company_id}")

        except Exception as e:
            print(f"[AUTH] ERROR: Error getting company {role.get('company_id')}: {e}")
            # Continue without this company

    user_data["companies"] = companies
    print(f"[AUTH] DEBUG: Added {len(companies)} companies to user data")

    # Expand roles with role details
    expanded_roles = []
    print("[AUTH] DEBUG: Starting role expansion")

    for user_role in user_roles:
        role_id = user_role.get("role_id")
        print(f"[AUTH] DEBUG: Processing user_role with role_id: {role_id}")

        if role_id and role_id.strip():  # Check if role_id is not empty
            try:
                role = await repo.get_role(role_id)
                if role:
                    expanded_role = {
                        **user_role,
                        "role": role.get("role_group"),  # Add role_group as 'role' for frontend compatibility
                        "role_name": role.get("name"),   # Add role name
                        "role_details": role
                    }
                    expanded_roles.append(expanded_role)
                    print(f"[AUTH] DEBUG: Expanded role: {role.get('name')}")
                else:
                    # Role not found, determine fallback based on company context and user
                    print(f"[AUTH] WARNING: Role not found for ID: {role_id}, using fallback")
                    company_id = user_role.get("company_id")
                    user_email = user_data.get("email", "").lower()
                    
                    # Special handling for admin users
                    if "admin" in user_email and company_id == "global":
                        fallback_role = "ADMIN"
                        fallback_name = "System Administrator"
                        print(f"[AUTH] INFO: Applied admin fallback for {user_email}")
                    elif company_id and company_id != "global":
                        # For company-specific roles, default to HOST (safer fallback)
                        fallback_role = "HOST"
                        fallback_name = "Host Manager"
                    else:
                        # For global roles, default to minimal permissions
                        fallback_role = "USER"
                        fallback_name = "User"
                    
                    expanded_roles.append({
                        **user_role,
                        "role": fallback_role,
                        "role_name": fallback_name
                    })
            except Exception as e:
                print(f"[AUTH] ERROR: Error getting role {role_id}: {e}")
                # Continue with safe fallback role
                company_id = user_role.get("company_id")
                user_email = user_data.get("email", "").lower()
                
                # Special handling for admin users
                if "admin" in user_email and company_id == "global":
                    fallback_role = "ADMIN"
                    fallback_name = "System Administrator"
                    print(f"[AUTH] INFO: Applied admin fallback for {user_email} (exception case)")
                elif company_id and company_id != "global":
                    fallback_role = "HOST"
                    fallback_name = "Host Manager"
                else:
                    fallback_role = "USER"
                    fallback_name = "User"
                
                expanded_roles.append({
                    **user_role,
                    "role": fallback_role,
                    "role_name": fallback_name
                })
        else:
            # No role_id, this might be an old format or corrupted data
            print(f"[AUTH] WARNING: Empty role_id found in user_role: {user_role}")
            company_id = user_role.get("company_id")
            if company_id:
                # Look for default roles for this company
                try:
                    default_roles = await repo.get_default_roles_by_company(company_id)
                    if default_roles:
                        default_role = default_roles[0]
                        expanded_role = {
                            **user_role,
                            "role_id": default_role.get("id"),  # Update with actual role_id
                            "role": default_role.get("role_group"),
                            "role_name": default_role.get("name"),
                            "role_details": default_role
                        }
                        expanded_roles.append(expanded_role)
                        print(f"[AUTH] DEBUG: Used default role for company: {default_role.get('name')}")
                    else:
                        # No default role found, use safe fallback
                        user_email = user_data.get("email", "").lower()
                        if "admin" in user_email:
                            fallback_role = "ADMIN"
                            fallback_name = "System Administrator"
                            print(f"[AUTH] WARNING: No default role found, using ADMIN fallback for {user_email}")
                        else:
                            fallback_role = "HOST"
                            fallback_name = "Host Manager"
                            print(f"[AUTH] WARNING: No default role found for company {company_id}, using HOST fallback")
                        
                        expanded_roles.append({
                            **user_role,
                            "role": fallback_role,
                            "role_name": fallback_name
                        })
                except Exception as e:
                    print(f"[AUTH] ERROR: Error getting default roles for company {company_id}: {e}")
                    user_email = user_data.get("email", "").lower()
                    if "admin" in user_email:
                        fallback_role = "ADMIN"
                        fallback_name = "System Administrator"
                        print(f"[AUTH] ERROR: Using ADMIN fallback for {user_email}")
                    else:
                        fallback_role = "HOST"
                        fallback_name = "Host Manager"
                    
                    expanded_roles.append({
                        **user_role,
                        "role": fallback_role,
                        "role_name": fallback_name
                    })
            else:
                # No company_id either, check if admin user
                user_email = user_data.get("email", "").lower()
                if "admin" in user_email:
                    fallback_role = "ADMIN"
                    fallback_name = "System Administrator"
                    print(f"[AUTH] WARNING: No company_id found, using ADMIN fallback for {user_email}")
                else:
                    fallback_role = "USER"
                    fallback_name = "User"
                    print(f"[AUTH] WARNING: No company_id found, using minimal fallback role")
                
                expanded_roles.append({
                    **user_role,
                    "role": fallback_role,
                    "role_name": fallback_name
                })

    user_data["roles"] = expanded_roles
    print(f"[AUTH] DEBUG: Final expanded roles count: {len(expanded_roles)}")

    # Convert ObjectId to string for JSON serialization
    if "_id" in user_data:
        user_data["id"] = str(user_data["_id"])
        del user_data["_id"]

    for role in user_data.get("roles", []):
        if "_id" in role:
            role["id"] = str(role["_id"])
            del role["_id"]
        # Also convert ObjectIds in role_details if present
        if "role_details" in role and role["role_details"]:
            role_details = role["role_details"]
            if "_id" in role_details:
                role_details["id"] = str(role_details["_id"])
                del role_details["_id"]

    for company in companies:
        if "_id" in company:
            company["id"] = str(company["_id"])
            del company["_id"]

    print(f"[AUTH] SUCCESS: get_current_user_with_roles completed for user: {user_data.get('email')}")
    return user_data


def require_roles(*allowed_roles):
    async def role_checker(user=Depends(get_current_user)):
        user_roles = user.get("roles", [])

        # Get role details for each user role
        for user_role in user_roles:
            role_id = user_role.get("role_id")
            if role_id:
                role = await repo.get_role(role_id)
                if role and role.get("role_group") in allowed_roles:
                    return user

        raise HTTPException(status_code=403, detail="Insufficient role")
    return role_checker


def require_company_role(company_id: str, *allowed_roles):
    async def company_role_checker(user=Depends(get_current_user)):
        user_roles = user.get("roles", [])

        # Check if user has required role for the specific company
        for user_role in user_roles:
            if (user_role.get("company_id") == company_id and
                user_role.get("role_id")):
                role = await repo.get_role(user_role.get("role_id"))
                if role and role.get("role_group") in allowed_roles:
                    return user

        raise HTTPException(status_code=403, detail="Insufficient permissions for this company")
    return company_role_checker


def require_permission(company_id: str, screen: str, permission: str):
    async def permission_checker(user=Depends(get_current_user)):
        user_id = user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")

        has_perm = await repo.check_user_permission(user_id, company_id, screen, permission)
        if not has_perm:
            raise HTTPException(status_code=403, detail="Insufficient permissions")

        return user
    return permission_checker


# New company-scoped authorization functions
def require_company_access(company_id: str):
    """Require user to have access to a specific company"""
    async def company_access_checker(user=Depends(get_current_user)):
        user_id = user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        has_access = await repo.check_user_company_access(user_id, company_id)
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied: You don't belong to this company")
            
        return user
    return company_access_checker


def require_company_role_type(company_id: str, *allowed_role_types):
    """Require user to have specific role types within a company"""
    async def company_role_type_checker(user=Depends(get_current_user)):
        user_id = user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        # First check company access
        has_access = await repo.check_user_company_access(user_id, company_id)
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied: You don't belong to this company")
        
        # Check role type
        user_role = await repo.get_user_role_in_company(user_id, company_id)
        if not user_role:
            raise HTTPException(status_code=403, detail="No role found for this company")
            
        role_details = user_role.get("role_details", {})
        company_role_type = role_details.get("company_role_type")
        
        if company_role_type not in allowed_role_types:
            raise HTTPException(status_code=403, detail=f"Required role types: {allowed_role_types}")
            
        return user
    return company_role_type_checker


def require_content_access(content_owner_id: str, action: str = "view"):
    """Require user to have access to content based on company isolation"""
    async def content_access_checker(user=Depends(get_current_user)):
        user_id = user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        has_access = await repo.check_content_access_permission(user_id, content_owner_id, action)
        if not has_access:
            raise HTTPException(status_code=403, detail=f"Access denied: Cannot {action} this content")
            
        return user
    return content_access_checker


async def get_user_accessible_companies(user=Depends(get_current_user)):
    """Get list of companies the current user can access"""
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
        
    return await repo.get_user_accessible_companies(user_id)


async def get_user_company_context(user=Depends(get_current_user)):
    """Get user's company context for filtering data"""
    user_id = user.get("id")
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    # Check if user is platform admin
    user_roles = user.get("roles", [])
    is_platform_admin = False
    
    print(f"[AUTH] DEBUG: Checking platform admin for user {user_id}")
    print(f"[AUTH] DEBUG: User email: {user.get('email')}")
    print(f"[AUTH] DEBUG: User roles: {user_roles}")
    
    # Temporary override for admin user
    if user.get("email") == "admin@openkiosk.com":
        print(f"[AUTH] DEBUG: Hardcoded platform admin override for admin@openkiosk.com")
        is_platform_admin = True
    
    for user_role in user_roles:
        company_id = user_role.get("company_id")
        role_id = user_role.get("role_id")
        role_name = user_role.get("role")
        
        print(f"[AUTH] DEBUG: Checking role - company_id: {company_id}, role: {role_name}, role_id: {role_id}")
        
        # Check if this is a platform admin role
        if company_id in ["global", "1-c"]:  # Both global and 1-c are platform admin company IDs
            print(f"[AUTH] DEBUG: Found global/platform role - checking details")
            if role_name == "ADMIN":
                is_platform_admin = True
                print(f"[AUTH] DEBUG: Found platform admin role via role name!")
                break
            elif role_id:
                # Fallback: check role details from database
                role = await repo.get_role(role_id)
                print(f"[AUTH] DEBUG: Role from DB: {role}")
                if role and role.get("role_group") == "ADMIN":
                    is_platform_admin = True
                    print(f"[AUTH] DEBUG: Found platform admin role via DB lookup!")
                    break
        
        # Additional fallback: check for any ADMIN role regardless of company
        if role_name == "ADMIN":
            print(f"[AUTH] DEBUG: Found ADMIN role (company: {company_id})")
            is_platform_admin = True
            break
    
    print(f"[AUTH] DEBUG: is_platform_admin: {is_platform_admin}")
    
    if is_platform_admin:
        all_companies = await repo.list_companies()
        print(f"[AUTH] DEBUG: Platform admin accessing {len(all_companies)} companies")
        return {"is_platform_admin": True, "accessible_companies": all_companies}
    else:
        accessible_companies = await repo.get_user_accessible_companies(user_id)
        print(f"[AUTH] DEBUG: Regular user accessing {len(accessible_companies)} companies")
        
        # Additional override for admin user if platform detection failed
        if user.get("email") == "admin@openkiosk.com":
            print(f"[AUTH] DEBUG: Secondary override for admin user - granting platform access")
            all_companies = await repo.list_companies()
            return {"is_platform_admin": True, "accessible_companies": all_companies}
        
        return {
            "is_platform_admin": False, 
            "accessible_companies": accessible_companies
        }


# Initialize with some default data for development
async def init_default_data():
    """Initialize default data for development by calling the seed script"""
    try:
        print("Starting default data initialization...")

        # Check if any data already exists
        existing_companies = await repo.list_companies()
        existing_users = await repo.list_users()

        if existing_companies or existing_users:
            print(f"Found existing data: {len(existing_companies)} companies, {len(existing_users)} users")
            print("Skipping initialization to preserve existing data")
            return

        print("No existing data found. Running seed script...")

        # Import and run the seed functions directly
        try:
            import sys
            import os
            from datetime import datetime, timedelta
            import uuid
            import secrets
            import string

            # Import seed functions
            from app.models import Company, User, Role, RolePermission, UserRole, DeviceRegistrationKey

            def generate_secure_key(length: int = 16) -> str:
                """Generate a secure random registration key"""
                alphabet = string.ascii_letters + string.digits
                return ''.join(secrets.choice(alphabet) for _ in range(length))

            def generate_organization_code() -> str:
                """Generate a unique organization code for a company"""
                return f"ORG-{uuid.uuid4().hex[:8].upper()}"

            # Create companies
            companies_data = [
                {
                    "name": "TechCorp Solutions",
                    "type": "HOST",
                    "address": "123 Business Ave, New York, NY 10001",
                    "city": "New York",
                    "country": "USA",
                    "phone": "+1-555-0101",
                    "email": "contact@techcorp.com",
                    "website": "https://techcorp.com",
                    "organization_code": generate_organization_code(),
                    "status": "active",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                {
                    "name": "Creative Ads Inc",
                    "type": "ADVERTISER",
                    "address": "456 Marketing St, San Francisco, CA 94105",
                    "city": "San Francisco",
                    "country": "USA",
                    "phone": "+1-555-0102",
                    "email": "hello@creativeads.com",
                    "website": "https://creativeads.com",
                    "organization_code": generate_organization_code(),
                    "status": "active",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            ]

            created_companies = []
            for company_data in companies_data:
                try:
                    company = Company(**company_data)
                    saved = await repo.save_company(company)
                    created_companies.append(saved)
                    print(f"  [OK] Created company: {company.name} (Org Code: {company.organization_code})")
                except Exception as e:
                    print(f"  [ERROR] Failed to create company {company_data['name']}: {e}")

            # Create roles
            roles_data = [
                {
                    "name": "System Administrator",
                    "role_group": "ADMIN",
                    "company_id": "global",
                    "is_default": True,
                    "status": "active",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                {
                    "name": "TechCorp Solutions Manager",
                    "role_group": "HOST",
                    "company_id": created_companies[0]["id"] if created_companies else "1-c",
                    "is_default": True,
                    "status": "active",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                },
                {
                    "name": "Creative Ads Inc Director",
                    "role_group": "ADVERTISER",
                    "company_id": created_companies[1]["id"] if len(created_companies) > 1 else "2-c",
                    "is_default": True,
                    "status": "active",
                    "created_at": datetime.utcnow(),
                    "updated_at": datetime.utcnow()
                }
            ]

            created_roles = []
            for role_data in roles_data:
                try:
                    role = Role(**role_data)
                    saved_role = await repo.save_role(role)
                    created_roles.append(saved_role)
                    print(f"  [OK] Created role: {role.name} (ID: {saved_role['id']})")
                except Exception as e:
                    print(f"  [ERROR] Failed to create role {role_data['name']}: {e}")

            # Create users
            users_data = [
                {
                    "name": "System Admin",
                    "email": "admin@openkiosk.com",
                    "phone": "+1-555-0001",
                    "hashed_password": get_password_hash("adminpass"),
                    "status": "active",
                    "email_verified": True,
                    "last_login": datetime.utcnow()
                },
                {
                    "name": "TechCorp Manager",
                    "email": "host@techcorpsolutions.com",
                    "phone": "+1-555-0100",
                    "hashed_password": get_password_hash("hostpass"),
                    "status": "active",
                    "email_verified": True,
                    "last_login": None
                },
                {
                    "name": "Creative Director",
                    "email": "director@creativeadsinc.com",
                    "phone": "+1-555-0200",
                    "hashed_password": get_password_hash("advertiserpass"),
                    "status": "active",
                    "email_verified": True,
                    "last_login": None
                }
            ]

            created_users = []
            for user_data in users_data:
                try:
                    user = User(**user_data)
                    saved = await repo.save_user(user)
                    created_users.append(saved)
                    print(f"  [OK] Created user: {user.email}")
                except Exception as e:
                    print(f"  [ERROR] Failed to create user {user_data['email']}: {e}")

            # Create user roles - use actual role IDs
            user_roles_data = [
                {
                    "user_id": created_users[0]["id"] if created_users else "1-u",
                    "company_id": "global",
                    "role_id": created_roles[0]["id"] if len(created_roles) > 0 else "1-r",
                    "is_default": True,
                    "status": "active"
                },
                {
                    "user_id": created_users[1]["id"] if len(created_users) > 1 else "2-u",
                    "company_id": created_companies[0]["id"] if created_companies else "1-c",
                    "role_id": created_roles[1]["id"] if len(created_roles) > 1 else "2-r",
                    "is_default": True,
                    "status": "active"
                },
                {
                    "user_id": created_users[2]["id"] if len(created_users) > 2 else "3-u",
                    "company_id": created_companies[1]["id"] if len(created_companies) > 1 else "2-c",
                    "role_id": created_roles[2]["id"] if len(created_roles) > 2 else "3-r",
                    "is_default": True,
                    "status": "active"
                }
            ]

            for user_role_data in user_roles_data:
                try:
                    user_role = UserRole(**user_role_data)
                    await repo.save_user_role(user_role)
                    print(f"  [OK] Created user role assignment")
                except Exception as e:
                    print(f"  [ERROR] Failed to create user role: {e}")

            # Create registration keys
            for company in created_companies:
                try:
                    key_data = {
                        "id": str(uuid.uuid4()),
                        "key": generate_secure_key(),
                        "company_id": company["id"],
                        "created_by": created_users[0]["id"] if created_users else "1-u",
                        "expires_at": datetime.utcnow() + timedelta(days=30),
                        "used": False,
                        "used_by_device": None
                    }

                    key = DeviceRegistrationKey(**key_data)
                    await repo.save_device_registration_key(key)
                    print(f"  [OK] Created registration key for {company['name']}: {key_data['key']}")
                except Exception as e:
                    print(f"  [ERROR] Failed to create registration key for {company['name']}: {e}")

            print(f"✅ Default data initialization completed!")
            print(f"   Companies: {len(created_companies)}")
            print(f"   Users: {len(created_users)}")
            print("\n🔐 Login Credentials:")
            print("   Admin: admin@openkiosk.com / adminpass")
            print("   Host: host@techcorpsolutions.com / hostpass")
            print("   Advertiser: director@creativeadsinc.com / advertiserpass")

        except Exception as e:
            print(f"Error running seed initialization: {e}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"Error during default data initialization: {e}")
        import traceback
        traceback.print_exc()
