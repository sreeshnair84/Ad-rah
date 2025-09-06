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

from app.auth_service import get_current_user as get_current_user_service
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

    if not token:
        logger.debug("No token provided")
        raise credentials_exception

    try:
        logger.debug("Decoding JWT token")
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")  # This is the user ID
        user_email = payload.get("email")  # This is the email

        if user_id is None:
            logger.warning("User ID is None in token payload")
            raise credentials_exception

        # Check token expiration
        exp = payload.get("exp")
        if exp is None:
            logger.warning("Token has no expiration")
            raise credentials_exception

        # Verify token hasn't expired
        current_time = datetime.utcnow().timestamp()
        if current_time > exp:
            logger.info("Token has expired")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except JWTError as e:
        logger.warning(f"JWT Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Use email to get user data (more reliable than user_id lookup via repo)
    if not user_email:
        logger.warning("No email in token payload")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    logger.debug(f"Looking up user by email: {user_email}")
    user_data = await repo.get_user_by_email(user_email)

    if user_data is None:
        logger.warning(f"User not found in database: {user_email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user roles - handle both 'id' and '_id' field names
    user_id = user_data.get("id") or user_data.get("_id")
    if not user_id:
        logger.error(f"No user ID found in user data for: {user_email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user data",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_roles = await repo.get_user_roles(str(user_id))
    logger.debug(f"Found {len(user_roles)} roles for user")
    user_data["roles"] = user_roles
    
    # Add JWT payload data to user_data for easier access
    user_data["user_type"] = payload.get("user_type", "COMPANY_USER")
    user_data["permissions"] = payload.get("permissions", [])
    user_data["is_super_admin"] = payload.get("is_super_admin", False)
    
    # Compute is_super_admin based on user_type if not explicitly set in token
    if user_data["user_type"] == "SUPER_USER":
        user_data["is_super_admin"] = True
    
    user_data["active_company"] = payload.get("active_company")
    user_data["active_role"] = payload.get("active_role")

    logger.info(f"Authentication successful for user: {user_email}")
    return user_data


async def get_current_user_with_roles(token: str = Depends(oauth2_scheme)):
    """Get current user with their roles and companies"""
    logger.debug("Starting get_current_user_with_roles")

    user_data = await get_current_user(token)

    # Get all companies for user's roles
    companies = []
    user_roles = user_data.get("roles", [])

    for role in user_roles:
        try:
            company_id = role.get("company_id")

            if company_id and company_id != "global":
                company = await repo.get_company(company_id)
                if company:
                    companies.append(company)
                else:
                    logger.warning(f"Company not found for ID: {company_id}")

        except Exception as e:
            logger.error(f"Error getting company {role.get('company_id')}: {e}")
            # Continue without this company

    user_data["companies"] = companies

    # Expand roles with role details
    expanded_roles = []

    for user_role in user_roles:
        role_id = user_role.get("role_id")

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
                    logger.debug(f"Expanded role: {role.get('name')}")
                else:
                    # Role not found, determine fallback based on company context and user
                    logger.warning(f"Role not found for ID: {role_id}, using fallback")
                    company_id = user_role.get("company_id")
                    user_email = user_data.get("email", "").lower()
                    
                    # Special handling for admin users
                    if "admin" in user_email and company_id == "global":
                        fallback_role = "ADMIN"
                        fallback_name = "System Administrator"
                        logger.debug(f"Applied admin fallback for {user_email}")
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
                logger.error(f"Error getting role {role_id}: {e}")
                # Continue with safe fallback role
                company_id = user_role.get("company_id")
                user_email = user_data.get("email", "").lower()
                
                # Special handling for admin users
                if "admin" in user_email and company_id == "global":
                    fallback_role = "ADMIN"
                    fallback_name = "System Administrator"
                    logger.debug(f"Applied admin fallback for {user_email} (exception case)")
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
            logger.warning(f"Empty role_id found in user_role: {user_role}")
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
                        logger.debug(f"Used default role for company: {default_role.get('name')}")
                    else:
                        # No default role found, use safe fallback
                        user_email = user_data.get("email", "").lower()
                        if "admin" in user_email:
                            fallback_role = "ADMIN"
                            fallback_name = "System Administrator"
                            logger.warning(f"No default role found, using ADMIN fallback for {user_email}")
                        else:
                            fallback_role = "HOST"
                            fallback_name = "Host Manager"
                            logger.warning(f"No default role found for company {company_id}, using HOST fallback")
                        
                        expanded_roles.append({
                            **user_role,
                            "role": fallback_role,
                            "role_name": fallback_name
                        })
                except Exception as e:
                    logger.error(f"Error getting default roles for company {company_id}: {e}")
                    user_email = user_data.get("email", "").lower()
                    if "admin" in user_email:
                        fallback_role = "ADMIN"
                        fallback_name = "System Administrator"
                        logger.debug(f"Using ADMIN fallback for {user_email}")
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
                    logger.warning(f"No company_id found, using ADMIN fallback for {user_email}")
                else:
                    fallback_role = "USER"
                    fallback_name = "User"
                    logger.warning(f"No company_id found, using minimal fallback role")
                
                expanded_roles.append({
                    **user_role,
                    "role": fallback_role,
                    "role_name": fallback_name
                })

    user_data["roles"] = expanded_roles
    logger.debug(f"Final expanded roles count: {len(expanded_roles)}")

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

    logger.debug(f"get_current_user_with_roles completed for user: {user_data.get('email')}")
    return user_data


def require_roles(*allowed_roles):
    async def role_checker(user=Depends(get_current_user_service)):
        user_roles = user.get("roles", []) if isinstance(user, dict) else []

        # Get role details for each user role
        for user_role in user_roles:
            role_id = user_role.get("role_id") if isinstance(user_role, dict) else user_role.role_id
            if role_id:
                role = await repo.get_role(role_id)
                if role and role.get("role_group") in allowed_roles:
                    return user

        raise HTTPException(status_code=403, detail="Insufficient role")
    return role_checker


def require_company_role(company_id: str, *allowed_roles):
    async def company_role_checker(user=Depends(get_current_user_service)):
        user_roles = user.get("roles", []) if isinstance(user, dict) else []

        # Check if user has required role for the specific company
        for user_role in user_roles:
            if isinstance(user_role, dict):
                role_company_id = user_role.get("company_id")
                role_id = user_role.get("role_id")
            else:
                role_company_id = user_role.company_id
                role_id = user_role.role_id
            
            if (role_company_id == company_id and role_id):
                role = await repo.get_role(role_id)
                if role and role.get("role_group") in allowed_roles:
                    return user

        raise HTTPException(status_code=403, detail="Insufficient permissions for this company")
    return company_role_checker


def require_permission(company_id: str, screen: str, permission: str):
    async def permission_checker(user=Depends(get_current_user_service)):
        if isinstance(user, dict):
            user_id = user.get("id")
        else:
            user_id = user.id
            
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
    async def company_access_checker(user=Depends(get_current_user_service)):
        if isinstance(user, dict):
            user_id = user.get("id")
        else:
            user_id = user.id
            
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        has_access = await repo.check_user_company_access(user_id, company_id)
        if not has_access:
            raise HTTPException(status_code=403, detail="Access denied: You don't belong to this company")
            
        return user
    return company_access_checker


def require_company_role_type(company_id: str, *allowed_role_types):
    """Require user to have specific role types within a company"""
    async def company_role_type_checker(user=Depends(get_current_user_service)):
        if isinstance(user, dict):
            user_id = user.get("id")
        else:
            user_id = user.id
            
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
    async def content_access_checker(user=Depends(get_current_user_service)):
        if isinstance(user, dict):
            user_id = user.get("id")
        else:
            user_id = user.id
            
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        has_access = await repo.check_content_access_permission(user_id, content_owner_id, action)
        if not has_access:
            raise HTTPException(status_code=403, detail=f"Access denied: Cannot {action} this content")
            
        return user
    return content_access_checker


async def get_user_accessible_companies(user=Depends(get_current_user_service)):
    """Get list of companies the current user can access"""
    if isinstance(user, dict):
        user_id = user.get("id")
    else:
        user_id = user.id
        
    if not user_id:
        raise HTTPException(status_code=401, detail="User not authenticated")
        
    return await repo.get_user_accessible_companies(user_id)


async def get_user_company_context(user=Depends(get_current_user_service)):
    """Get user's company context for filtering data"""
    # Handle both UserProfile objects and dictionaries
    if hasattr(user, 'user_type'):
        # This is a UserProfile object
        user_type = user.user_type.value
        user_email = user.email.lower()
        user_id = user.id
        user_roles = []  # UserProfile doesn't have roles attribute
        user_company_id = user.company_id
    else:
        # This is a dictionary
        user_id = user.get("id")
        if not user_id:
            raise HTTPException(status_code=401, detail="User not authenticated")
        
        user_type = user.get("user_type")
        user_email = user.get("email", "").lower()
        user_roles = user.get("roles", [])
        user_company_id = user.get("company_id")
    
    logger.debug(f"Checking user context for {user_email}, user_type: {user_type}")
    
    # SUPER_USER gets access to everything
    if user_type == "SUPER_USER" or user_email == "admin@adara.com":
        logger.debug("SUPER_USER detected - granting platform access")
        all_companies = await repo.list_companies()
        return {"is_platform_admin": True, "accessible_companies": all_companies}
    
    # Check roles for admin privileges
    is_platform_admin = False
    
    for user_role in user_roles:
        if hasattr(user_role, 'role'):
            # This is a UserRole object
            role_name = user_role.role.value if hasattr(user_role.role, 'value') else str(user_role.role)
            role_id = user_role.role_id
            company_id = user_role.company_id
        else:
            # This is a dictionary
            role_name = user_role.get("role")
            role_id = user_role.get("role_id")
            company_id = user_role.get("company_id")
        
        logger.debug(f"Checking role - role_name: {role_name}, role_id: {role_id}, company_id: {company_id}")
        
        # Only ADMIN role_group should grant platform admin access
        if role_name == "ADMIN":
            is_platform_admin = True
            logger.debug("Found ADMIN role group - granting platform access")
            break
        elif role_id:
            # Fallback: check role details from database
            role = await repo.get_role(role_id)
            logger.debug(f"Role from DB: {role}")
            if role and role.get("role_group") == "ADMIN":
                is_platform_admin = True
                logger.debug("Found ADMIN role group via DB lookup - granting platform access")
                break
    
    logger.debug(f"is_platform_admin: {is_platform_admin}")
    
    if is_platform_admin:
        all_companies = await repo.list_companies()
        logger.debug(f"Admin accessing {len(all_companies)} companies")
        return {"is_platform_admin": True, "accessible_companies": all_companies}
    else:
        # Regular user - get their company
        if user_company_id:
            company = await repo.get_company(user_company_id)
            accessible_companies = [company] if company else []
        else:
            accessible_companies = []
        
        logger.debug(f"Regular user accessing {len(accessible_companies)} companies")
        return {
            "is_platform_admin": False, 
            "accessible_companies": accessible_companies
        }


async def get_current_user_with_super_admin_bypass(token: str = Depends(oauth2_scheme)):
    """Get current user with SUPER_USER bypass for authentication failures"""
    try:
        # First try normal authentication
        return await get_current_user_service(token)
    except HTTPException as e:
        # If authentication fails, check if this might be a SUPER_USER
        if e.status_code == 401:
            logger.debug("Authentication failed, checking for SUPER_USER bypass")
            try:
                # Try to decode the token to get the user info
                payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
                user_email = payload.get("email")  # Use email instead of sub

                if user_email:
                    logger.debug(f"Checking if user {user_email} is SUPER_USER")
                    user_data = await repo.get_user_by_email(user_email)

                    if user_data and user_data.get("user_type") == "SUPER_USER":
                        logger.info(f"SUPER_USER bypass activated for {user_email}")
                        # Get user roles
                        user_roles = await repo.get_user_roles(user_data["id"])
                        user_data["roles"] = user_roles
                        return user_data
                    else:
                        logger.debug(f"User {user_email} is not SUPER_USER, re-raising authentication error")
            except Exception as bypass_error:
                logger.debug(f"SUPER_USER bypass failed: {bypass_error}")

        # Re-raise the original authentication error
        raise e
