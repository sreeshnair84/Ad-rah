# Clean Authentication Service for Adārah Digital Signage Platform
# Simplified, secure authentication with clear RBAC integration

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import hashlib

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

# Import password hashing
try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    BCRYPT_AVAILABLE = True
except ImportError:
    pwd_context = None
    BCRYPT_AVAILABLE = False

from app.config import settings
from app.database_service import db_service
from app.rbac_models_new import (
    LoginRequest, LoginResponse, UserProfile, UserCreate,
    UserType, CompanyType, CompanyRole
)

logger = logging.getLogger(__name__)

# OAuth2 scheme for token extraction
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# JWT Configuration
SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES


class AuthService:
    """Clean authentication service with RBAC integration"""
    
    def __init__(self):
        if not BCRYPT_AVAILABLE:
            logger.warning("⚠️ BCRYPT not available - using fallback password hashing")
    
    # ================================
    # PASSWORD MANAGEMENT
    # ================================
    
    def hash_password(self, password: str) -> str:
        """Hash a password securely"""
        if not password:
            raise ValueError("Password cannot be empty")
        
        if BCRYPT_AVAILABLE and pwd_context:
            return pwd_context.hash(password)
        else:
            # Fallback: SHA256 with salt (NOT recommended for production)
            salt = settings.SECRET_KEY
            return hashlib.sha256((salt + password).encode()).hexdigest()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        if not plain_password or not hashed_password:
            return False
        
        if BCRYPT_AVAILABLE and pwd_context:
            try:
                return pwd_context.verify(plain_password, hashed_password)
            except Exception as e:
                logger.error(f"Bcrypt verification failed: {e}")
                return False
        else:
            # Fallback verification
            salt = settings.SECRET_KEY
            expected_hash = hashlib.sha256((salt + plain_password).encode()).hexdigest()
            return expected_hash == hashed_password
    
    # ================================
    # JWT TOKEN MANAGEMENT
    # ================================
    
    def create_access_token(self, user_profile: UserProfile) -> str:
        """Create JWT access token for user"""
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + expires_delta
        
        # Create token payload with essential user data
        token_data = {
            "sub": user_profile.id,  # Subject (user ID)
            "email": user_profile.email,
            "user_type": user_profile.user_type.value,
            "company_id": user_profile.company_id,
            "company_role": user_profile.company_role.value if user_profile.company_role else None,
            "permissions": user_profile.permissions,
            "exp": expire,
            "iat": datetime.utcnow(),
            "type": "access_token"
        }
        
        return jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            # Verify token type
            if payload.get("type") != "access_token":
                raise JWTError("Invalid token type")
            
            # Verify required fields
            user_id = payload.get("sub")
            email = payload.get("email")
            
            if not user_id or not email:
                raise JWTError("Invalid token format")
            
            return payload
            
        except JWTError as e:
            logger.debug(f"Token verification failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    # ================================
    # AUTHENTICATION OPERATIONS
    # ================================
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserProfile]:
        """Authenticate user by email and password"""
        try:
            # Get user by email
            user_data = await db_service.get_user_by_email(email)
            if not user_data:
                logger.info(f"Authentication failed: User not found - {email}")
                return None
            
            # Verify password
            if not self.verify_password(password, user_data.get("hashed_password", "")):
                logger.info(f"Authentication failed: Invalid password - {email}")
                return None
            
            # Check if user is active
            if not user_data.get("is_active", True):
                logger.info(f"Authentication failed: User inactive - {email}")
                return None
            
            # Get full user profile
            user_profile = await db_service.get_user_profile(user_data["id"])
            if not user_profile:
                logger.error(f"Failed to get user profile - {email}")
                return None
            
            # Update last login
            await db_service.update_user_login(user_data["id"])
            
            logger.info(f"✅ Authentication successful - {email}")
            return user_profile
            
        except Exception as e:
            logger.error(f"Authentication error for {email}: {e}")
            return None
    
    async def login(self, login_request: LoginRequest) -> LoginResponse:
        """Process user login"""
        user_profile = await self.authenticate_user(
            login_request.email,
            login_request.password
        )
        
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Create access token
        access_token = self.create_access_token(user_profile)
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert to seconds
            user=user_profile
        )
    
    async def get_current_user(self, token: str) -> UserProfile:
        """Get current user from JWT token"""
        # Verify and decode token
        payload = self.verify_token(token)
        user_id = payload["sub"]
        
        # Get fresh user profile from database
        user_profile = await db_service.get_user_profile(user_id)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if not user_profile.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User account is inactive",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        return user_profile
    
    # ================================
    # DEVICE AUTHENTICATION
    # ================================
    
    async def authenticate_device(self, api_key: str) -> Optional[Dict]:
        """Authenticate device by API key"""
        try:
            device = await db_service.get_device_by_api_key(api_key)
            if not device or device.status != "active":
                return None
            
            # Update device last seen
            await db_service.update_device_last_seen(api_key)
            
            # Get company info
            company = await db_service.get_company(device.company_id)
            
            return {
                "device_id": device.device_id,
                "device_name": device.device_name,
                "company_id": device.company_id,
                "company": company.model_dump() if company else None,
                "device_type": device.device_type,
                "location": device.location
            }
            
        except Exception as e:
            logger.error(f"Device authentication error: {e}")
            return None
    
    # ================================
    # PERMISSION CHECKING
    # ================================
    
    async def check_permission(self, user: UserProfile, permission: str) -> bool:
        """Check if user has a specific permission"""
        # Super users have all permissions
        if user.user_type == UserType.SUPER_USER:
            return True
        
        return permission in user.permissions
    
    async def check_company_access(self, user: UserProfile, company_id: str) -> bool:
        """Check if user has access to a company"""
        # Super users can access all companies
        if user.user_type == UserType.SUPER_USER:
            return True
        
        # Company users can only access their own company
        return user.company_id == company_id
    
    # ================================
    # USER REGISTRATION
    # ================================
    
    async def register_user(self, user_data: UserCreate) -> UserProfile:
        """Register a new user"""
        # Hash password
        hashed_password = self.hash_password(user_data.password)
        
        # Create user
        user = await db_service.create_user(user_data, hashed_password)
        
        # Get full profile
        user_profile = await db_service.get_user_profile(user.id)
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user profile"
            )
        
        logger.info(f"👤 User registered: {user_data.email}")
        return user_profile


# Global auth service instance
auth_service = AuthService()


# ================================
# FASTAPI DEPENDENCIES
# ================================

async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserProfile:
    """FastAPI dependency to get current user"""
    return await auth_service.get_current_user(token)


async def get_current_active_user(
    current_user: UserProfile = Depends(get_current_user)
) -> UserProfile:
    """FastAPI dependency to get current active user"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user account"
        )
    return current_user


def require_permission(permission: str):
    """Decorator factory to require specific permission"""
    async def permission_dependency(
        current_user: UserProfile = Depends(get_current_active_user)
    ) -> UserProfile:
        if not await auth_service.check_permission(current_user, permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission required: {permission}"
            )
        return current_user
    
    return permission_dependency


def require_company_access(company_id_param: str = "company_id"):
    """Decorator factory to require company access"""
    async def company_access_dependency(
        company_id: str,
        current_user: UserProfile = Depends(get_current_active_user)
    ) -> UserProfile:
        if not await auth_service.check_company_access(current_user, company_id):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You don't have access to this company"
            )
        return current_user
    
    return company_access_dependency


def require_user_type(*allowed_types: UserType):
    """Decorator factory to require specific user types"""
    async def user_type_dependency(
        current_user: UserProfile = Depends(get_current_active_user)
    ) -> UserProfile:
        if current_user.user_type not in allowed_types:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"User type required: {[t.value for t in allowed_types]}"
            )
        return current_user
    
    return user_type_dependency


def require_company_role(*allowed_roles: CompanyRole):
    """Decorator factory to require specific company roles"""
    async def company_role_dependency(
        current_user: UserProfile = Depends(get_current_active_user)
    ) -> UserProfile:
        if not current_user.company_role or current_user.company_role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Company role required: {[r.value for r in allowed_roles]}"
            )
        return current_user
    
    return company_role_dependency


def require_company_type(*allowed_types: CompanyType):
    """Decorator factory to require specific company types"""
    async def company_type_dependency(
        current_user: UserProfile = Depends(get_current_active_user)
    ) -> UserProfile:
        if (not current_user.company or 
            CompanyType(current_user.company.company_type) not in allowed_types):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Company type required: {[t.value for t in allowed_types]}"
            )
        return current_user
    
    return company_type_dependency