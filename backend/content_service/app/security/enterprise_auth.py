"""
Enterprise Authentication Service
Provides enhanced authentication capabilities including multi-factor authentication,
Azure Entra ID integration, and enterprise-grade security features.
"""

import logging
import asyncio
import json
import secrets
import base64
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum
import jwt
import bcrypt
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.backends import default_backend

logger = logging.getLogger(__name__)

class AuthMethod(Enum):
    """Authentication methods"""
    PASSWORD = "password"
    MFA_TOTP = "mfa_totp"
    MFA_SMS = "mfa_sms"
    MFA_EMAIL = "mfa_email"
    AZURE_AD = "azure_ad"
    SSO = "sso"
    DEVICE_CERTIFICATE = "device_certificate"
    BIOMETRIC = "biometric"

class AuthLevel(Enum):
    """Authentication security levels"""
    BASIC = "basic"           # Password only
    ENHANCED = "enhanced"     # Password + MFA
    ENTERPRISE = "enterprise" # SSO/Azure AD
    ZERO_TRUST = "zero_trust" # Full verification required

class TokenType(Enum):
    """JWT token types"""
    ACCESS = "access"
    REFRESH = "refresh"
    ID = "id"
    DEVICE = "device"
    SESSION = "session"

@dataclass
class AuthenticationResult:
    """Authentication result"""
    success: bool
    user_id: Optional[str]
    device_id: Optional[str]
    access_token: Optional[str]
    refresh_token: Optional[str]
    expires_in: int
    auth_level: AuthLevel
    auth_methods_used: List[AuthMethod]
    mfa_required: bool
    mfa_token: Optional[str]
    error_message: Optional[str]
    additional_data: Optional[Dict[str, Any]]

@dataclass
class MFAChallenge:
    """Multi-factor authentication challenge"""
    challenge_id: str
    user_id: str
    method: AuthMethod
    challenge_data: Dict[str, Any]
    expires_at: datetime
    attempts_remaining: int
    created_at: datetime

@dataclass
class DeviceFingerprint:
    """Device fingerprint for device binding"""
    device_id: str
    hardware_id: str
    software_signature: str
    network_signature: str
    geolocation: Optional[Dict[str, float]]
    trust_score: float
    first_seen: datetime
    last_seen: datetime

class EnterpriseAuthService:
    """Enhanced authentication service with enterprise features"""
    
    def __init__(self):
        # Configuration
        self.jwt_secret_key = self._get_jwt_secret()
        self.jwt_algorithm = "RS256"  # Using RSA for better security
        self.access_token_expire_minutes = 15
        self.refresh_token_expire_days = 30
        self.mfa_challenge_expire_minutes = 5
        self.max_failed_attempts = 5
        self.account_lockout_duration_minutes = 30
        
        # In-memory stores (would use Redis in production)
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.mfa_challenges: Dict[str, MFAChallenge] = {}
        self.failed_attempts: Dict[str, Dict[str, Any]] = {}
        self.device_fingerprints: Dict[str, DeviceFingerprint] = {}
        self.revoked_tokens: set = set()
        
        # Initialize RSA keys for JWT signing
        self.private_key, self.public_key = self._generate_rsa_keys()
        
        # Initialize dependencies
        try:
            from app.repo import repo
            self.repo = repo
        except ImportError:
            self.repo = None
            logger.warning("Repository not available - using in-memory auth")
        
        try:
            from app.security import audit_logger
            self.audit_logger = audit_logger
        except ImportError:
            self.audit_logger = None
            logger.warning("Audit logging not available")

    def _get_jwt_secret(self) -> str:
        """Get JWT secret from secure source"""
        # In production, this would come from Azure Key Vault
        import os
        return os.getenv("JWT_SECRET_KEY", "development-secret-key-change-in-production")
    
    def _generate_rsa_keys(self) -> Tuple[Any, Any]:
        """Generate RSA key pair for JWT signing"""
        try:
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
                backend=default_backend()
            )
            public_key = private_key.public_key()
            return private_key, public_key
        except Exception as e:
            logger.error(f"Failed to generate RSA keys: {e}")
            # Fallback to HMAC
            self.jwt_algorithm = "HS256"
            return None, None

    async def authenticate_user(self, 
                              username: str, 
                              password: str, 
                              device_info: Optional[Dict[str, Any]] = None,
                              require_mfa: bool = True) -> AuthenticationResult:
        """Enhanced user authentication with MFA support"""
        try:
            # Check for account lockout
            if await self._is_account_locked(username):
                await self._log_auth_event(username, "account_locked", device_info)
                return AuthenticationResult(
                    success=False,
                    user_id=None,
                    device_id=None,
                    access_token=None,
                    refresh_token=None,
                    expires_in=0,
                    auth_level=AuthLevel.BASIC,
                    auth_methods_used=[],
                    mfa_required=False,
                    mfa_token=None,
                    error_message="Account locked due to multiple failed attempts",
                    additional_data=None
                )
            
            # Verify password
            user_data = await self._verify_user_password(username, password)
            if not user_data:
                await self._record_failed_attempt(username, "invalid_password", device_info)
                return AuthenticationResult(
                    success=False,
                    user_id=None,
                    device_id=None,
                    access_token=None,
                    refresh_token=None,
                    expires_in=0,
                    auth_level=AuthLevel.BASIC,
                    auth_methods_used=[AuthMethod.PASSWORD],
                    mfa_required=False,
                    mfa_token=None,
                    error_message="Invalid username or password",
                    additional_data=None
                )
            
            user_id = user_data["id"]
            auth_methods = [AuthMethod.PASSWORD]
            
            # Check if MFA is required
            if require_mfa and await self._is_mfa_required(user_id):
                # Generate MFA challenge
                mfa_challenge = await self._create_mfa_challenge(user_id)
                
                return AuthenticationResult(
                    success=False,
                    user_id=user_id,
                    device_id=device_info.get("device_id") if device_info else None,
                    access_token=None,
                    refresh_token=None,
                    expires_in=0,
                    auth_level=AuthLevel.BASIC,
                    auth_methods_used=auth_methods,
                    mfa_required=True,
                    mfa_token=mfa_challenge.challenge_id,
                    error_message="Multi-factor authentication required",
                    additional_data={"mfa_methods": ["totp", "sms", "email"]}
                )
            
            # Generate device fingerprint if device info provided
            device_id = None
            if device_info:
                device_id = await self._process_device_fingerprint(user_id, device_info)
            
            # Generate tokens
            access_token = await self._generate_access_token(user_id, user_data, device_id)
            refresh_token = await self._generate_refresh_token(user_id, device_id)
            
            # Clear failed attempts
            await self._clear_failed_attempts(username)
            
            # Log successful authentication
            await self._log_auth_event(username, "authentication_success", device_info)
            
            return AuthenticationResult(
                success=True,
                user_id=user_id,
                device_id=device_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self.access_token_expire_minutes * 60,
                auth_level=AuthLevel.ENHANCED if require_mfa else AuthLevel.BASIC,
                auth_methods_used=auth_methods,
                mfa_required=False,
                mfa_token=None,
                error_message=None,
                additional_data={"user_data": user_data}
            )
            
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            await self._log_auth_event(username, "authentication_error", device_info, str(e))
            return AuthenticationResult(
                success=False,
                user_id=None,
                device_id=None,
                access_token=None,
                refresh_token=None,
                expires_in=0,
                auth_level=AuthLevel.BASIC,
                auth_methods_used=[],
                mfa_required=False,
                mfa_token=None,
                error_message="Authentication service error",
                additional_data=None
            )

    async def verify_mfa_challenge(self, 
                                 challenge_id: str, 
                                 mfa_code: str,
                                 device_info: Optional[Dict[str, Any]] = None) -> AuthenticationResult:
        """Verify multi-factor authentication challenge"""
        try:
            # Get MFA challenge
            challenge = self.mfa_challenges.get(challenge_id)
            if not challenge:
                return AuthenticationResult(
                    success=False,
                    user_id=None,
                    device_id=None,
                    access_token=None,
                    refresh_token=None,
                    expires_in=0,
                    auth_level=AuthLevel.BASIC,
                    auth_methods_used=[],
                    mfa_required=False,
                    mfa_token=None,
                    error_message="Invalid or expired MFA challenge",
                    additional_data=None
                )
            
            # Check expiration
            if datetime.utcnow() > challenge.expires_at:
                del self.mfa_challenges[challenge_id]
                return AuthenticationResult(
                    success=False,
                    user_id=None,
                    device_id=None,
                    access_token=None,
                    refresh_token=None,
                    expires_in=0,
                    auth_level=AuthLevel.BASIC,
                    auth_methods_used=[],
                    mfa_required=False,
                    mfa_token=None,
                    error_message="MFA challenge expired",
                    additional_data=None
                )
            
            # Verify MFA code
            if not await self._verify_mfa_code(challenge, mfa_code):
                challenge.attempts_remaining -= 1
                
                if challenge.attempts_remaining <= 0:
                    del self.mfa_challenges[challenge_id]
                    await self._log_auth_event(challenge.user_id, "mfa_failed_max_attempts", device_info)
                
                return AuthenticationResult(
                    success=False,
                    user_id=None,
                    device_id=None,
                    access_token=None,
                    refresh_token=None,
                    expires_in=0,
                    auth_level=AuthLevel.BASIC,
                    auth_methods_used=[],
                    mfa_required=False,
                    mfa_token=None,
                    error_message="Invalid MFA code",
                    additional_data={"attempts_remaining": challenge.attempts_remaining}
                )
            
            # MFA successful - get user data
            user_data = await self._get_user_data(challenge.user_id)
            if not user_data:
                return AuthenticationResult(
                    success=False,
                    user_id=None,
                    device_id=None,
                    access_token=None,
                    refresh_token=None,
                    expires_in=0,
                    auth_level=AuthLevel.BASIC,
                    auth_methods_used=[],
                    mfa_required=False,
                    mfa_token=None,
                    error_message="User data not found",
                    additional_data=None
                )
            
            # Generate device fingerprint if device info provided
            device_id = None
            if device_info:
                device_id = await self._process_device_fingerprint(challenge.user_id, device_info)
            
            # Generate tokens
            access_token = await self._generate_access_token(challenge.user_id, user_data, device_id)
            refresh_token = await self._generate_refresh_token(challenge.user_id, device_id)
            
            # Clean up challenge
            del self.mfa_challenges[challenge_id]
            
            # Log successful MFA
            await self._log_auth_event(challenge.user_id, "mfa_success", device_info)
            
            return AuthenticationResult(
                success=True,
                user_id=challenge.user_id,
                device_id=device_id,
                access_token=access_token,
                refresh_token=refresh_token,
                expires_in=self.access_token_expire_minutes * 60,
                auth_level=AuthLevel.ENHANCED,
                auth_methods_used=[AuthMethod.PASSWORD, challenge.method],
                mfa_required=False,
                mfa_token=None,
                error_message=None,
                additional_data={"user_data": user_data}
            )
            
        except Exception as e:
            logger.error(f"MFA verification error: {e}")
            return AuthenticationResult(
                success=False,
                user_id=None,
                device_id=None,
                access_token=None,
                refresh_token=None,
                expires_in=0,
                auth_level=AuthLevel.BASIC,
                auth_methods_used=[],
                mfa_required=False,
                mfa_token=None,
                error_message="MFA verification service error",
                additional_data=None
            )

    async def refresh_access_token(self, refresh_token: str) -> AuthenticationResult:
        """Refresh access token using refresh token"""
        try:
            # Verify refresh token
            payload = await self._verify_jwt_token(refresh_token, TokenType.REFRESH)
            if not payload:
                return AuthenticationResult(
                    success=False,
                    user_id=None,
                    device_id=None,
                    access_token=None,
                    refresh_token=None,
                    expires_in=0,
                    auth_level=AuthLevel.BASIC,
                    auth_methods_used=[],
                    mfa_required=False,
                    mfa_token=None,
                    error_message="Invalid or expired refresh token",
                    additional_data=None
                )
            
            user_id = payload.get("user_id")
            device_id = payload.get("device_id")
            
            # Get user data
            user_data = await self._get_user_data(user_id)
            if not user_data:
                return AuthenticationResult(
                    success=False,
                    user_id=None,
                    device_id=None,
                    access_token=None,
                    refresh_token=None,
                    expires_in=0,
                    auth_level=AuthLevel.BASIC,
                    auth_methods_used=[],
                    mfa_required=False,
                    mfa_token=None,
                    error_message="User not found",
                    additional_data=None
                )
            
            # Generate new access token
            access_token = await self._generate_access_token(user_id, user_data, device_id)
            
            return AuthenticationResult(
                success=True,
                user_id=user_id,
                device_id=device_id,
                access_token=access_token,
                refresh_token=refresh_token,  # Keep the same refresh token
                expires_in=self.access_token_expire_minutes * 60,
                auth_level=AuthLevel.ENHANCED,  # Assume enhanced if using refresh
                auth_methods_used=[],
                mfa_required=False,
                mfa_token=None,
                error_message=None,
                additional_data={"user_data": user_data}
            )
            
        except Exception as e:
            logger.error(f"Token refresh error: {e}")
            return AuthenticationResult(
                success=False,
                user_id=None,
                device_id=None,
                access_token=None,
                refresh_token=None,
                expires_in=0,
                auth_level=AuthLevel.BASIC,
                auth_methods_used=[],
                mfa_required=False,
                mfa_token=None,
                error_message="Token refresh service error",
                additional_data=None
            )

    async def revoke_token(self, token: str) -> bool:
        """Revoke a JWT token"""
        try:
            # Add to revoked tokens set
            self.revoked_tokens.add(token)
            
            # In production, this would be stored in Redis with expiration
            # For now, we'll clean up old tokens periodically
            await self._cleanup_revoked_tokens()
            
            return True
            
        except Exception as e:
            logger.error(f"Token revocation error: {e}")
            return False

    async def verify_access_token(self, access_token: str) -> Optional[Dict[str, Any]]:
        """Verify access token and return payload"""
        try:
            # Check if token is revoked
            if access_token in self.revoked_tokens:
                return None
            
            # Verify JWT token
            payload = await self._verify_jwt_token(access_token, TokenType.ACCESS)
            return payload
            
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None

    # Private helper methods

    async def _is_account_locked(self, username: str) -> bool:
        """Check if account is locked"""
        attempts_data = self.failed_attempts.get(username)
        if not attempts_data:
            return False
        
        if attempts_data["count"] >= self.max_failed_attempts:
            lockout_until = attempts_data["locked_until"]
            if datetime.utcnow() < lockout_until:
                return True
            else:
                # Lockout period expired, clear attempts
                del self.failed_attempts[username]
                return False
        
        return False

    async def _verify_user_password(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Verify user password"""
        try:
            if self.repo:
                # Use repository to get user data
                user = await self.repo.get_user_by_email(username)
                if user and bcrypt.checkpw(password.encode('utf-8'), user.password_hash.encode('utf-8')):
                    return {
                        "id": user.id,
                        "email": user.email,
                        "name": user.name,
                        "company_roles": user.company_roles
                    }
            else:
                # Fallback for development
                test_users = {
                    "admin@adara.com": {
                        "id": "admin-001",
                        "email": "admin@adara.com",
                        "name": "Admin User",
                        "password": "adminpass",
                        "company_roles": []
                    }
                }
                
                if username in test_users and test_users[username]["password"] == password:
                    return test_users[username]
            
            return None
            
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return None

    async def _record_failed_attempt(self, username: str, reason: str, device_info: Optional[Dict[str, Any]]):
        """Record failed authentication attempt"""
        try:
            now = datetime.utcnow()
            
            if username not in self.failed_attempts:
                self.failed_attempts[username] = {
                    "count": 0,
                    "first_attempt": now,
                    "last_attempt": now,
                    "locked_until": None
                }
            
            self.failed_attempts[username]["count"] += 1
            self.failed_attempts[username]["last_attempt"] = now
            
            if self.failed_attempts[username]["count"] >= self.max_failed_attempts:
                lockout_until = now + timedelta(minutes=self.account_lockout_duration_minutes)
                self.failed_attempts[username]["locked_until"] = lockout_until
            
            # Log the failed attempt
            await self._log_auth_event(username, f"failed_attempt_{reason}", device_info)
            
        except Exception as e:
            logger.error(f"Failed to record failed attempt: {e}")

    async def _clear_failed_attempts(self, username: str):
        """Clear failed attempts for user"""
        if username in self.failed_attempts:
            del self.failed_attempts[username]

    async def _is_mfa_required(self, user_id: str) -> bool:
        """Check if MFA is required for user"""
        # In production, this would check user preferences or policy
        return True  # For now, require MFA for all users

    async def _create_mfa_challenge(self, user_id: str) -> MFAChallenge:
        """Create MFA challenge"""
        challenge_id = secrets.token_urlsafe(32)
        challenge = MFAChallenge(
            challenge_id=challenge_id,
            user_id=user_id,
            method=AuthMethod.MFA_TOTP,  # Default to TOTP
            challenge_data={"code_length": 6},
            expires_at=datetime.utcnow() + timedelta(minutes=self.mfa_challenge_expire_minutes),
            attempts_remaining=3,
            created_at=datetime.utcnow()
        )
        
        self.mfa_challenges[challenge_id] = challenge
        return challenge

    async def _verify_mfa_code(self, challenge: MFAChallenge, mfa_code: str) -> bool:
        """Verify MFA code"""
        # In production, this would verify against TOTP/SMS/Email
        # For development, accept "123456" as valid code
        return mfa_code == "123456"

    async def _get_user_data(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user data by ID"""
        try:
            if self.repo:
                user = await self.repo.get_user_by_id(user_id)
                if user:
                    return {
                        "id": user.id,
                        "email": user.email,
                        "name": user.name,
                        "company_roles": user.company_roles
                    }
            else:
                # Fallback for development
                if user_id == "admin-001":
                    return {
                        "id": "admin-001",
                        "email": "admin@adara.com",
                        "name": "Admin User",
                        "company_roles": []
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Get user data error: {e}")
            return None

    async def _process_device_fingerprint(self, user_id: str, device_info: Dict[str, Any]) -> str:
        """Process device fingerprint and return device ID"""
        try:
            device_id = device_info.get("device_id", f"device_{user_id}_{datetime.now().timestamp()}")
            
            # Create device fingerprint
            fingerprint = DeviceFingerprint(
                device_id=device_id,
                hardware_id=device_info.get("hardware_id", "unknown"),
                software_signature=device_info.get("software_signature", "unknown"),
                network_signature=device_info.get("network_signature", "unknown"),
                geolocation=device_info.get("geolocation"),
                trust_score=0.8,  # Initial trust score
                first_seen=datetime.utcnow(),
                last_seen=datetime.utcnow()
            )
            
            self.device_fingerprints[device_id] = fingerprint
            return device_id
            
        except Exception as e:
            logger.error(f"Device fingerprint processing error: {e}")
            return f"fallback_{user_id}"

    async def _generate_access_token(self, user_id: str, user_data: Dict[str, Any], device_id: Optional[str]) -> str:
        """Generate JWT access token"""
        try:
            now = datetime.utcnow()
            payload = {
                "type": TokenType.ACCESS.value,
                "user_id": user_id,
                "device_id": device_id,
                "email": user_data.get("email"),
                "name": user_data.get("name"),
                "company_roles": user_data.get("company_roles", []),
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(minutes=self.access_token_expire_minutes)).timestamp()),
                "iss": "openkiosk-auth",
                "aud": "openkiosk-api"
            }
            
            if self.private_key:
                # Use RSA signing
                return jwt.encode(payload, self.private_key, algorithm=self.jwt_algorithm)
            else:
                # Fallback to HMAC
                return jwt.encode(payload, self.jwt_secret_key, algorithm="HS256")
                
        except Exception as e:
            logger.error(f"Access token generation error: {e}")
            raise

    async def _generate_refresh_token(self, user_id: str, device_id: Optional[str]) -> str:
        """Generate JWT refresh token"""
        try:
            now = datetime.utcnow()
            payload = {
                "type": TokenType.REFRESH.value,
                "user_id": user_id,
                "device_id": device_id,
                "iat": int(now.timestamp()),
                "exp": int((now + timedelta(days=self.refresh_token_expire_days)).timestamp()),
                "iss": "openkiosk-auth",
                "aud": "openkiosk-api"
            }
            
            if self.private_key:
                # Use RSA signing
                return jwt.encode(payload, self.private_key, algorithm=self.jwt_algorithm)
            else:
                # Fallback to HMAC
                return jwt.encode(payload, self.jwt_secret_key, algorithm="HS256")
                
        except Exception as e:
            logger.error(f"Refresh token generation error: {e}")
            raise

    async def _verify_jwt_token(self, token: str, expected_type: TokenType) -> Optional[Dict[str, Any]]:
        """Verify JWT token and return payload"""
        try:
            if self.public_key:
                # Use RSA verification
                payload = jwt.decode(token, self.public_key, algorithms=[self.jwt_algorithm])
            else:
                # Fallback to HMAC
                payload = jwt.decode(token, self.jwt_secret_key, algorithms=["HS256"])
            
            # Check token type
            if payload.get("type") != expected_type.value:
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            return None

    async def _log_auth_event(self, username: str, event_type: str, device_info: Optional[Dict[str, Any]], error: Optional[str] = None):
        """Log authentication event"""
        try:
            if self.audit_logger:
                self.audit_logger.log_auth_event(event_type, {
                    "username": username,
                    "device_info": device_info,
                    "error": error,
                    "timestamp": datetime.utcnow().isoformat()
                })
            else:
                logger.info(f"Auth event: {event_type} for {username}")
                
        except Exception as e:
            logger.error(f"Failed to log auth event: {e}")

    async def _cleanup_revoked_tokens(self):
        """Clean up expired revoked tokens"""
        try:
            # In production, this would use Redis expiration
            # For now, just limit the size
            if len(self.revoked_tokens) > 10000:
                # Keep only the most recent 5000 tokens
                self.revoked_tokens = set(list(self.revoked_tokens)[-5000:])
                
        except Exception as e:
            logger.error(f"Token cleanup error: {e}")

# Global enterprise auth service instance
enterprise_auth_service = EnterpriseAuthService()