"""
Enhanced Authentication Service with Refresh Tokens and Security Features
Provides secure authentication with JWT tokens, refresh tokens, and security monitoring
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple
from fastapi import HTTPException, Depends, Request
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

class EnhancedAuthService:
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
    
    async def get_current_user(self, credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
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
auth_service = EnhancedAuthService()

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