"""
Enhanced Authentication Service with Refresh Tokens and Security Features
Provides secure authentication with JWT tokens, refresh tokens, and security monitoring
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from fastapi import HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
import jwt
from jwt import InvalidTokenError
import secrets
import asyncio
from functools import wraps
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

# Security configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

class TokenType(Enum):
    ACCESS = "access"
    REFRESH = "refresh"

@dataclass
class TokenData:
    user_id: str
    user_type: str
    company_id: Optional[str]
    permissions: list
    token_type: TokenType
    issued_at: datetime
    expires_at: datetime
    jti: str  # JWT ID for token revocation

@dataclass
class AuthContext:
    user_id: str
    user_type: str
    company_id: Optional[str]
    permissions: list
    ip_address: str
    user_agent: str
    session_id: str

class SecurityEvent(Enum):
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILED = "login_failed"
    TOKEN_REFRESH = "token_refresh"
    LOGOUT = "logout"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    ACCOUNT_LOCKED = "account_locked"

class AuthService:
    """Enhanced authentication service with security features"""
    
    def __init__(self):
        self.jwt_secret = None
        self.refresh_secret = None
        self.redis_client = None
        self.failed_attempts = {}
        self.max_failed_attempts = 5
        self.lockout_duration = timedelta(minutes=30)
        self.access_token_expire = timedelta(minutes=15)  # Shorter for security
        self.refresh_token_expire = timedelta(days=7)
        
        # In-memory storage for tokens (Redis alternative)
        self.refresh_tokens = {}  # jti -> user_id
        self.blacklisted_tokens = {}  # jti -> expiry_time
    
    async def initialize(self, jwt_secret: str, refresh_secret: str, redis_url: Optional[str] = None):
        """Initialize the authentication service"""
        self.jwt_secret = jwt_secret
        self.refresh_secret = refresh_secret
        
        # For now, Redis is optional - we'll use in-memory storage
        if redis_url:
            logger.info("Redis URL provided but using in-memory token management for now")
            # In a future update, we can add proper Redis async support
        
        logger.info("Enhanced authentication service initialized with in-memory token management")
    
    def hash_password(self, password: str) -> str:
        """Hash a password securely"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    async def is_account_locked(self, identifier: str) -> bool:
        """Check if an account is locked due to failed attempts"""
        if identifier not in self.failed_attempts:
            return False
        
        attempts, last_attempt = self.failed_attempts[identifier]
        if attempts >= self.max_failed_attempts:
            if datetime.utcnow() - last_attempt < self.lockout_duration:
                return True
            else:
                # Lockout period expired, reset attempts
                del self.failed_attempts[identifier]
        
        return False
    
    async def record_failed_attempt(self, identifier: str):
        """Record a failed login attempt"""
        now = datetime.utcnow()
        if identifier in self.failed_attempts:
            attempts, _ = self.failed_attempts[identifier]
            self.failed_attempts[identifier] = (attempts + 1, now)
        else:
            self.failed_attempts[identifier] = (1, now)
        
        attempts, _ = self.failed_attempts[identifier]
        if attempts >= self.max_failed_attempts:
            await self.log_security_event(SecurityEvent.ACCOUNT_LOCKED, {
                "identifier": identifier,
                "attempts": attempts
            })
    
    async def reset_failed_attempts(self, identifier: str):
        """Reset failed login attempts for an identifier"""
        if identifier in self.failed_attempts:
            del self.failed_attempts[identifier]
    
    async def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        try:
            # Import here to avoid circular imports
            from app.database_service import db_service
            
            # Check if account is locked
            if await self.is_account_locked(email):
                await self.log_security_event(SecurityEvent.ACCOUNT_LOCKED, {"email": email})
                raise HTTPException(status_code=423, detail="Account temporarily locked due to multiple failed attempts")
            
            # Get user by email
            user_data = await db_service.get_user_by_email(email)
            if not user_data:
                await self.record_failed_attempt(email)
                await self.log_security_event(SecurityEvent.LOGIN_FAILED, {"email": email, "reason": "user_not_found"})
                return None
            
            # Verify password
            if not self.verify_password(password, user_data.get("hashed_password", "")):
                await self.record_failed_attempt(email)
                await self.log_security_event(SecurityEvent.LOGIN_FAILED, {"email": email, "reason": "invalid_password"})
                return None
            
            # Check if user is active
            if not user_data.get("is_active", True):
                await self.log_security_event(SecurityEvent.LOGIN_FAILED, {"email": email, "reason": "account_inactive"})
                raise HTTPException(status_code=403, detail="Account is inactive")
            
            # Reset failed attempts on successful authentication
            await self.reset_failed_attempts(email)
            
            # Get user profile
            user_profile = await db_service.get_user_profile(user_data["id"])
            if user_profile:
                await db_service.update_user_login(user_data["id"])
                await self.log_security_event(SecurityEvent.LOGIN_SUCCESS, {"email": email, "user_id": user_data["id"]})
            
            return user_profile
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error for {email}: {e}")
            await self.log_security_event(SecurityEvent.LOGIN_FAILED, {"email": email, "reason": "system_error"})
            return None
    
    async def login(self, login_request) -> Dict[str, Any]:
        """Login endpoint compatible with existing auth service"""
        try:
            # Import here to avoid circular imports
            from app.rbac_models import LoginRequest, LoginResponse
            
            # Handle both dict and LoginRequest object
            if hasattr(login_request, 'email'):
                email = login_request.email
                password = login_request.password
            else:
                email = login_request.get('email')
                password = login_request.get('password')
            
            if not email or not password:
                raise HTTPException(status_code=400, detail="Email and password are required")
            
            # Authenticate user
            user_profile = await self.authenticate_user(email, password)
            if not user_profile:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Prepare user data for token creation
            user_data = {
                "id": user_profile.id if hasattr(user_profile, 'id') else user_profile['id'],
                "user_type": user_profile.user_type.value if hasattr(user_profile, 'user_type') and hasattr(user_profile.user_type, 'value') else user_profile.get('user_type'),
                "company_id": user_profile.company_id if hasattr(user_profile, 'company_id') else user_profile.get('company_id'),
                "permissions": user_profile.permissions if hasattr(user_profile, 'permissions') else user_profile.get('permissions', [])
            }
            
            # Create token pair
            access_token, refresh_token = await self.create_token_pair(user_data)
            
            # Return response compatible with existing auth endpoints
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": int(self.access_token_expire.total_seconds()),
                "user": user_profile
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login error: {e}")
            raise HTTPException(status_code=500, detail="Login failed due to server error")
    
    async def register_user(self, user_data) -> Dict[str, Any]:
        """Register a new user"""
        try:
            # Import here to avoid circular imports
            from app.database_service import db_service
            
            # Handle both dict and UserCreate object
            if hasattr(user_data, 'password'):
                password = user_data.password
                email = user_data.email
            else:
                password = user_data.get('password')
                email = user_data.get('email')
            
            if not password or not email:
                raise HTTPException(status_code=400, detail="Email and password are required")
            
            # Hash password
            hashed_password = self.hash_password(password)
            
            # Create user
            user = await db_service.create_user(user_data, hashed_password)
            user_profile = await db_service.get_user_profile(user.id)
            
            if not user_profile:
                raise HTTPException(status_code=500, detail="Failed to create user profile")
            
            await self.log_security_event(SecurityEvent.LOGIN_SUCCESS, {"email": email, "user_id": user.id, "action": "registration"})
            return user_profile
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"User registration error: {e}")
            raise HTTPException(status_code=500, detail="Registration failed")
    
    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """Create a JWT access token"""
        now = datetime.utcnow()
        expire = now + self.access_token_expire
        jti = secrets.token_urlsafe(16)
        
        payload = {
            "sub": user_data["id"],
            "user_type": user_data["user_type"],
            "company_id": user_data.get("company_id"),
            "permissions": user_data.get("permissions", []),
            "type": TokenType.ACCESS.value,
            "iat": now,
            "exp": expire,
            "jti": jti
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm="HS256")
    
    def create_refresh_token(self, user_data: Dict[str, Any]) -> str:
        """Create a JWT refresh token"""
        now = datetime.utcnow()
        expire = now + self.refresh_token_expire
        jti = secrets.token_urlsafe(16)
        
        payload = {
            "sub": user_data["id"],
            "user_type": user_data["user_type"],
            "company_id": user_data.get("company_id"),
            "type": TokenType.REFRESH.value,
            "iat": now,
            "exp": expire,
            "jti": jti
        }
        
        return jwt.encode(payload, self.refresh_secret, algorithm="HS256")
    
    async def create_token_pair(self, user_data: Dict[str, Any]) -> Tuple[str, str]:
        """Create both access and refresh tokens"""
        access_token = self.create_access_token(user_data)
        refresh_token = self.create_refresh_token(user_data)
        
        # Store refresh token hash in memory for revocation
        try:
            payload = jwt.decode(refresh_token, self.refresh_secret, algorithms=["HS256"])
            # Store in memory instead of Redis
            self.refresh_tokens[payload['jti']] = user_data["id"]
            logger.debug(f"Stored refresh token for user {user_data['id']}")
        except Exception as e:
            logger.warning(f"Failed to store refresh token: {e}")
        
        return access_token, refresh_token
    
    async def verify_token(self, token: str, token_type: TokenType = TokenType.ACCESS) -> TokenData:
        """Verify and decode a JWT token"""
        try:
            secret = self.jwt_secret if token_type == TokenType.ACCESS else self.refresh_secret
            payload = jwt.decode(token, secret, algorithms=["HS256"])
            
            # Check token type
            if payload.get("type") != token_type.value:
                raise HTTPException(status_code=401, detail="Invalid token type")
            
            # Check if token is blacklisted
            if await self.is_token_blacklisted(payload.get("jti")):
                raise HTTPException(status_code=401, detail="Token has been revoked")
            
            return TokenData(
                user_id=payload["sub"],
                user_type=payload["user_type"],
                company_id=payload.get("company_id"),
                permissions=payload.get("permissions", []),
                token_type=token_type,
                issued_at=datetime.fromtimestamp(payload["iat"]),
                expires_at=datetime.fromtimestamp(payload["exp"]),
                jti=payload.get("jti")
            )
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
    
    async def refresh_access_token(self, refresh_token: str) -> str:
        """Create a new access token using a refresh token"""
        # Verify refresh token
        token_data = await self.verify_token(refresh_token, TokenType.REFRESH)
        
        # Check if refresh token is still valid in memory
        try:
            stored_user_id = self.refresh_tokens.get(token_data.jti)
            if not stored_user_id or stored_user_id != token_data.user_id:
                raise HTTPException(status_code=401, detail="Refresh token not found or invalid")
        except Exception as e:
            logger.warning(f"Token validation check failed: {e}")
        
        # Create new access token
        user_data = {
            "id": token_data.user_id,
            "user_type": token_data.user_type,
            "company_id": token_data.company_id,
            "permissions": token_data.permissions
        }
        
        new_access_token = self.create_access_token(user_data)
        
        await self.log_security_event(SecurityEvent.TOKEN_REFRESH, {
            "user_id": token_data.user_id,
            "jti": token_data.jti
        })
        
        return new_access_token
    
    async def revoke_token(self, jti: str, token_type: TokenType = TokenType.REFRESH):
        """Add a token to the blacklist"""
        try:
            # Store in memory blacklist with expiration time
            expire_time = self.refresh_token_expire if token_type == TokenType.REFRESH else self.access_token_expire
            expiry = datetime.utcnow() + expire_time
            self.blacklisted_tokens[jti] = expiry
            logger.debug(f"Token {jti} added to blacklist")
        except Exception as e:
            logger.error(f"Failed to blacklist token: {e}")
    
    async def is_token_blacklisted(self, jti: str) -> bool:
        """Check if a token is blacklisted"""
        if not jti:
            return False
        
        try:
            # Check in-memory blacklist
            if jti in self.blacklisted_tokens:
                expiry = self.blacklisted_tokens[jti]
                if datetime.utcnow() < expiry:
                    return True
                else:
                    # Token expired from blacklist, remove it
                    del self.blacklisted_tokens[jti]
            return False
        except Exception as e:
            logger.warning(f"Failed to check token blacklist: {e}")
            return False
    
    async def logout(self, access_token: str, refresh_token: str):
        """Logout user by revoking tokens"""
        try:
            # Decode tokens to get JTIs
            access_data = await self.verify_token(access_token, TokenType.ACCESS)
            refresh_data = await self.verify_token(refresh_token, TokenType.REFRESH)
            
            # Revoke both tokens
            await self.revoke_token(access_data.jti, TokenType.ACCESS)
            await self.revoke_token(refresh_data.jti, TokenType.REFRESH)
            
            # Remove refresh token from memory
            if refresh_data.jti in self.refresh_tokens:
                del self.refresh_tokens[refresh_data.jti]
            
            await self.log_security_event(SecurityEvent.LOGOUT, {
                "user_id": access_data.user_id
            })
            
        except Exception as e:
            logger.error(f"Logout failed: {e}")
    
    async def log_security_event(self, event: SecurityEvent, data: Dict[str, Any]):
        """Log security events for monitoring"""
        log_entry = {
            "event": event.value,
            "timestamp": datetime.utcnow().isoformat(),
            "data": data
        }
        
        # In production, this would go to a security monitoring system
        logger.info(f"Security event: {log_entry}")
    
    async def get_current_user_from_token(self, token: str):
        """Get current user from JWT token (compatible with existing auth service)"""
        try:
            # Import here to avoid circular imports
            from app.database_service import db_service
            
            # Check if JWT secret is available
            if not self.jwt_secret:
                raise HTTPException(status_code=500, detail="Authentication service not properly configured")
            
            # Verify token
            payload = jwt.decode(token, self.jwt_secret, algorithms=["HS256"])
            
            # Check token type - accept both "access" and "access_token"
            token_type = payload.get("type")
            if token_type not in ["access", "access_token"]:
                raise HTTPException(status_code=401, detail="Invalid token type")
            
            # Check if token is blacklisted
            if await self.is_token_blacklisted(payload.get("jti")):
                raise HTTPException(status_code=401, detail="Token has been revoked")
            
            user_id = payload.get("sub")
            email = payload.get("email")
            
            if not user_id:
                raise HTTPException(status_code=401, detail="Invalid token format")
            
            # Get user profile
            user_profile = await db_service.get_user_profile(user_id)
            
            if not user_profile:
                # Try to find user by email
                if email:
                    user_data = await db_service.get_user_by_email(email)
                    if user_data:
                        user_profile = await db_service.get_user_profile(user_data["id"])
                
                if not user_profile:
                    raise HTTPException(status_code=401, detail="User not found")
            
            # Check if user is active
            if hasattr(user_profile, 'is_active'):
                if not user_profile.is_active:
                    raise HTTPException(status_code=401, detail="User account is inactive")
            elif isinstance(user_profile, dict):
                if not user_profile.get('is_active', True):
                    raise HTTPException(status_code=401, detail="User account is inactive")
            
            return user_profile
            
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired")
        except jwt.InvalidTokenError:
            raise HTTPException(status_code=401, detail="Invalid token")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get current user error: {e}")
            raise HTTPException(status_code=401, detail="Authentication failed")
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
        """Get current user from JWT token"""
        try:
            token_data = await self.verify_token(credentials.credentials)
            return token_data
        except Exception as e:
            logger.warning(f"Authentication failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        """Get current user from JWT token"""
        try:
            token_data = await self.verify_token(credentials.credentials)
            return token_data
        except Exception as e:
            logger.warning(f"Authentication failed: {e}")
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    async def require_permissions(self, required_permissions: list):
        """Dependency to require specific permissions"""
        async def _check_permissions(token_data: TokenData = Depends(self.get_current_user)):
            if not all(perm in token_data.permissions for perm in required_permissions):
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return token_data
        return _check_permissions
    
    async def require_user_type(self, allowed_types: list):
        """Dependency to require specific user types"""
        async def _check_user_type(token_data: TokenData = Depends(self.get_current_user)):
            if token_data.user_type not in allowed_types:
                raise HTTPException(status_code=403, detail="Access denied for user type")
            return token_data
        return _check_user_type

# Global authentication service instance
auth_service = AuthService()

async def initialize_auth_service(jwt_secret: str, refresh_secret: str, redis_url: Optional[str] = None):
    """Initialize the global authentication service"""
    await auth_service.initialize(jwt_secret, refresh_secret, redis_url)
    logger.info("Enhanced authentication service initialized")

# Convenience functions for FastAPI dependencies
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Get current authenticated user"""
    return await auth_service.get_current_user(credentials)

def require_permissions(*permissions):
    """Require specific permissions"""
    return auth_service.require_permissions(list(permissions))

def require_user_types(*user_types):
    """Require specific user types"""
    return auth_service.require_user_type(list(user_types))

def require_super_user():
    """Require super user access"""
    return require_user_types("SUPER_USER")

def require_company_admin():
    """Require company admin access"""
    return require_user_types("SUPER_USER", "COMPANY_USER")

async def get_current_user_with_super_admin_bypass(credentials: HTTPAuthorizationCredentials = Depends(security)) -> Dict[str, Any]:
    """Get current user with SUPER_USER bypass for authentication failures"""
    try:
        # First try normal authentication
        token_data = await auth_service.get_current_user(credentials)
        # Convert TokenData to dict format expected by callers
        return {
            "id": token_data.user_id,
            "user_type": token_data.user_type,
            "company_id": token_data.company_id,
            "permissions": token_data.permissions
        }
    except HTTPException as e:
        # If authentication fails, check if this might be a SUPER_USER
        if e.status_code == 401:
            logger.debug("Authentication failed, checking for SUPER_USER bypass")
            try:
                # Try to decode the token to get the user info
                secret_key = auth_service.jwt_secret
                if not secret_key:
                    raise ValueError("JWT secret not configured")
                payload = jwt.decode(credentials.credentials, secret_key, algorithms=["HS256"])
                user_email = payload.get("email")

                if user_email:
                    logger.debug(f"Checking if user {user_email} is SUPER_USER")
                    # Import here to avoid circular imports
                    from app.database_service import db_service
                    user_data = await db_service.get_user_by_email(user_email)

                    if user_data and user_data.get("user_type") == "SUPER_USER":
                        logger.info(f"SUPER_USER bypass activated for {user_email}")
                        # Get user roles
                        from app.repo import repo
                        user_roles = await repo.get_user_roles(user_data["id"])
                        user_data["roles"] = user_roles
                        return user_data
                    else:
                        logger.debug(f"User {user_email} is not SUPER_USER, re-raising authentication error")
            except Exception as bypass_error:
                logger.debug(f"SUPER_USER bypass failed: {bypass_error}")

        # Re-raise the original authentication error
        raise e

# Rate limiting decorator
def rate_limit(requests_per_minute: int = 60):
    """Rate limiting decorator for authentication endpoints"""
    def decorator(func):
        @wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Implementation would use Redis or in-memory store
            # For now, it's a placeholder
            return await func(request, *args, **kwargs)
        return wrapper
    return decorator