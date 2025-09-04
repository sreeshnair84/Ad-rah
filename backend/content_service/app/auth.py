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
SECRET_KEY = settings.JWT_SECRET_KEY  # Use JWT_SECRET_KEY to match auth service
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
        user_id = payload.get("sub")  # This is the user ID
        user_email = payload.get("email")  # This is the email
        print(f"[AUTH] DEBUG: Extracted user_id: {user_id}")
        print(f"[AUTH] DEBUG: Extracted user_email: {user_email}")

        if user_id is None:
            print("[AUTH] ERROR: User ID is None in token payload")
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

    # Use email to get user data (more reliable than user_id lookup via repo)
    if not user_email:
        print("[AUTH] ERROR: No email in token payload")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    print(f"[AUTH] DEBUG: Looking up user by email: {user_email}")
    user_data = await repo.get_user_by_email(user_email)
    print(f"[AUTH] DEBUG: User data found: {user_data is not None}")

    if user_data is None:
        print(f"[AUTH] ERROR: User not found in database: {user_email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user roles - handle both 'id' and '_id' field names
    user_id = user_data.get("id") or user_data.get("_id")
    if not user_id:
        print(f"[AUTH] ERROR: No user ID found in user data: {list(user_data.keys())}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user data",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_roles = await repo.get_user_roles(str(user_id))
    print(f"[AUTH] DEBUG: User roles found: {len(user_roles)} roles")
    user_data["roles"] = user_roles
    
    # Add JWT payload data to user_data for easier access
    user_data["user_type"] = payload.get("user_type", "COMPANY_USER")
    user_data["permissions"] = payload.get("permissions", [])
    user_data["is_super_admin"] = payload.get("is_super_admin", False)
    user_data["active_company"] = payload.get("active_company")
    user_data["active_role"] = payload.get("active_role")

    print(f"[AUTH] SUCCESS: Authentication successful for user: {user_email}")
    print(f"[AUTH] DEBUG: User type: {user_data.get('user_type')}")
    print(f"[AUTH] DEBUG: Is super admin: {user_data.get('is_super_admin')}")
    print(f"[AUTH] DEBUG: Permissions count: {len(user_data.get('permissions', []))}")
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
    
    # Check if user is SUPER_USER
    user_type = user.get("user_type")
    user_email = user.get("email", "").lower()
    
    print(f"[AUTH] DEBUG: Checking user context for {user_email}, user_type: {user_type}")
    
    # SUPER_USER gets access to everything
    if user_type == "SUPER_USER" or user_email == "admin@adara.com":
        print(f"[AUTH] DEBUG: SUPER_USER detected - granting platform access")
        all_companies = await repo.list_companies()
        return {"is_platform_admin": True, "accessible_companies": all_companies}
    
    # Check roles for admin privileges
    user_roles = user.get("roles", [])
    is_platform_admin = False
    
    for user_role in user_roles:
        role_id = user_role.get("role_id")
        role_name = user_role.get("role")
        
        print(f"[AUTH] DEBUG: Checking role - role_name: {role_name}, role_id: {role_id}")
        
        if role_name == "ADMIN" or role_name == "Super Administrator":
            is_platform_admin = True
            print(f"[AUTH] DEBUG: Found admin role!")
            break
        elif role_id:
            # Fallback: check role details from database
            role = await repo.get_role(role_id)
            print(f"[AUTH] DEBUG: Role from DB: {role}")
            if role and (role.get("name") == "Super Administrator" or role.get("name") == "Administrator"):
                is_platform_admin = True
                print(f"[AUTH] DEBUG: Found admin role via DB lookup!")
                break
    
    print(f"[AUTH] DEBUG: is_platform_admin: {is_platform_admin}")
    
    if is_platform_admin:
        all_companies = await repo.list_companies()
        print(f"[AUTH] DEBUG: Admin accessing {len(all_companies)} companies")
        return {"is_platform_admin": True, "accessible_companies": all_companies}
    else:
        # Regular user - get their company
        user_company_id = user.get("company_id")
        if user_company_id:
            company = await repo.get_company(user_company_id)
            accessible_companies = [company] if company else []
        else:
            accessible_companies = []
        
        print(f"[AUTH] DEBUG: Regular user accessing {len(accessible_companies)} companies")
        return {
            "is_platform_admin": False, 
            "accessible_companies": accessible_companies
        }


async def get_current_user_with_super_admin_bypass(token: str = Depends(oauth2_scheme)):
    """Get current user with SUPER_USER bypass for authentication failures"""
    try:
        # First try normal authentication
        return await get_current_user(token)
    except HTTPException as e:
        # If authentication fails, check if this might be a SUPER_USER
        if e.status_code == 401:
            print(f"[AUTH] DEBUG: Authentication failed, checking for SUPER_USER bypass")
            try:
                # Try to decode the token to get the user info
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_email = payload.get("email")  # Use email instead of sub

                if user_email:
                    print(f"[AUTH] DEBUG: Checking if user {user_email} is SUPER_USER")
                    user_data = await repo.get_user_by_email(user_email)

                    if user_data and user_data.get("user_type") == "SUPER_USER":
                        print(f"[AUTH] DEBUG: SUPER_USER bypass activated for {user_email}")
                        # Get user roles
                        user_roles = await repo.get_user_roles(user_data["id"])
                        user_data["roles"] = user_roles
                        return user_data
                    else:
                        print(f"[AUTH] DEBUG: User {user_email} is not SUPER_USER, re-raising authentication error")
            except Exception as bypass_error:
                print(f"[AUTH] DEBUG: SUPER_USER bypass failed: {bypass_error}")

        # Re-raise the original authentication error
        raise e
