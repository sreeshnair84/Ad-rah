# Authentication Service Layer
# Enterprise-grade authentication with JWT and RBAC integration

import logging
import jwt
import secrets
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

from app.database import get_db_service, QueryFilter, FilterOperation, DatabaseResult
from app.rbac.permissions import PermissionManager, Page, Permission, is_super_admin
from app.services.user_service import UserService
from app.config import settings

logger = logging.getLogger(__name__)

class AuthService:
    """Authentication and authorization service"""
    
    def __init__(self):
        self._db = None
        self._user_service = None
        self.jwt_secret = getattr(settings, 'JWT_SECRET_KEY', 'default-secret-change-in-production')
        self.jwt_algorithm = 'HS256'
        self.access_token_expire_minutes = getattr(settings, 'ACCESS_TOKEN_EXPIRE_MINUTES', 30)
        self.refresh_token_expire_days = getattr(settings, 'REFRESH_TOKEN_EXPIRE_DAYS', 7)
    
    @property
    def db(self):
        """Lazy initialization of database service"""
        if self._db is None:
            self._db = get_db_service()
        return self._db
    
    @property
    def user_service(self):
        """Lazy initialization of user service"""
        if self._user_service is None:
            self._user_service = UserService()
        return self._user_service
    
    async def login(
        self,
        email: str,
        password: str,
        device_info: Optional[Dict[str, Any]] = None
    ) -> DatabaseResult:
        """Authenticate user and return tokens with role information"""
        try:
            # Authenticate user
            auth_result = await self.user_service.authenticate_user(email, password)
            if not auth_result.success:
                return auth_result
            
            user_profile = auth_result.data
            user_id = user_profile["id"]
            
            # Generate tokens
            access_token = self._generate_access_token(user_profile)
            refresh_token = self._generate_refresh_token(user_id)
            
            # Store refresh token
            await self._store_refresh_token(user_id, refresh_token, device_info)
            
            # Get user permissions for active company
            permissions_result = await self.user_service.get_user_permissions(
                user_id, 
                user_profile.get("active_company")
            )
            
            permissions_data = permissions_result.data if permissions_result.success else {"permissions": [], "is_super_admin": False}
            
            return DatabaseResult(success=True, data={
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60,
                "user": user_profile,
                "permissions": permissions_data["permissions"],
                "is_super_admin": permissions_data["is_super_admin"]
            })
            
        except Exception as e:
            logger.error(f"Login failed: {e}")
            return DatabaseResult(success=False, error="Authentication failed")
    
    async def refresh_access_token(self, refresh_token: str) -> DatabaseResult:
        """Refresh access token using refresh token"""
        try:
            # Validate refresh token
            token_result = await self._validate_refresh_token(refresh_token)
            if not token_result.success:
                return token_result
            
            token_data = token_result.data
            user_id = token_data["user_id"]
            
            # Get current user profile
            profile_result = await self.user_service.get_user_profile(user_id)
            if not profile_result.success:
                return DatabaseResult(success=False, error="User not found")
            
            user_profile = profile_result.data
            
            # Generate new access token
            access_token = self._generate_access_token(user_profile)
            
            # Update refresh token last used
            await self.db.update_record("refresh_tokens", token_data["id"], {
                "last_used": datetime.utcnow(),
                "use_count": token_data.get("use_count", 0) + 1
            })
            
            return DatabaseResult(success=True, data={
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60,
                "user": user_profile
            })
            
        except Exception as e:
            logger.error(f"Token refresh failed: {e}")
            return DatabaseResult(success=False, error="Token refresh failed")
    
    async def logout(self, user_id: str, refresh_token: Optional[str] = None) -> DatabaseResult:
        """Logout user and revoke tokens"""
        try:
            if refresh_token:
                # Revoke specific refresh token
                filters = [
                    QueryFilter("token_hash", FilterOperation.EQUALS, self._hash_token(refresh_token)),
                    QueryFilter("user_id", FilterOperation.EQUALS, user_id),
                    QueryFilter("is_revoked", FilterOperation.EQUALS, False)
                ]
                
                token_result = await self.db.find_one_record("refresh_tokens", filters)
                if token_result.success:
                    await self.db.update_record("refresh_tokens", token_result.data["id"], {
                        "is_revoked": True,
                        "revoked_at": datetime.utcnow()
                    })
            else:
                # Revoke all user's refresh tokens
                await self._revoke_all_user_tokens(user_id)
            
            return DatabaseResult(success=True, data={"logged_out": True})
            
        except Exception as e:
            logger.error(f"Logout failed: {e}")
            return DatabaseResult(success=False, error="Logout failed")
    
    async def validate_access_token(self, token: str) -> DatabaseResult:
        """Validate JWT access token and return user info"""
        try:
            # Decode JWT - this will automatically validate expiration
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            
            user_id = payload.get("sub")
            if not user_id:
                return DatabaseResult(success=False, error="Invalid token")
            
            # Get current user profile
            profile_result = await self.user_service.get_user_profile(user_id)
            if not profile_result.success:
                return DatabaseResult(success=False, error="User not found")
            
            user_profile = profile_result.data
            
            # Check if user is still active
            if user_profile.get("status") != "active":
                return DatabaseResult(success=False, error="User account is not active")
            
            return DatabaseResult(success=True, data={
                "user": user_profile,
                "token_payload": payload
            })
            
        except jwt.ExpiredSignatureError:
            return DatabaseResult(success=False, error="Token expired")
        except jwt.InvalidTokenError as e:
            logger.error(f"Invalid token: {e}")
            return DatabaseResult(success=False, error="Invalid token")
        except Exception as e:
            logger.error(f"Token validation failed: {e}")
            return DatabaseResult(success=False, error="Token validation failed")
    
    async def check_permission(
        self,
        user_id: str,
        company_id: Optional[str],
        page: Page,
        permission: Permission
    ) -> DatabaseResult:
        """Check if user has specific permission"""
        try:
            # Get user permissions
            permissions_result = await self.user_service.get_user_permissions(user_id, company_id)
            if not permissions_result.success:
                return permissions_result
            
            permissions_data = permissions_result.data["permissions"]
            user_permissions = PermissionManager.deserialize_permissions(
                PermissionManager.serialize_permissions([
                    PermissionManager.PagePermissions.from_dict(p) for p in permissions_data
                ])
            )
            
            # Check permission
            has_permission = PermissionManager.check_permission(user_permissions, page, permission)
            
            return DatabaseResult(success=True, data={
                "has_permission": has_permission,
                "is_super_admin": is_super_admin(user_permissions)
            })
            
        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return DatabaseResult(success=False, error="Permission check failed")
    
    async def switch_company_context(
        self,
        user_id: str,
        company_id: Optional[str]
    ) -> DatabaseResult:
        """Switch user's active company context"""
        try:
            # Verify user has access to the company
            if company_id:
                filters = [
                    QueryFilter("user_id", FilterOperation.EQUALS, user_id),
                    QueryFilter("company_id", FilterOperation.EQUALS, company_id),
                    QueryFilter("status", FilterOperation.EQUALS, "active")
                ]
                
                role_result = await self.db.find_one_record("user_company_roles", filters)
                if not role_result.success:
                    return DatabaseResult(success=False, error="Access denied to company")
            
            # Get updated user profile with new context
            profile_result = await self.user_service.get_user_profile(user_id)
            if not profile_result.success:
                return profile_result
            
            user_profile = profile_result.data
            
            # Update active company in profile
            user_profile["active_company"] = company_id
            
            # Get permissions for new context
            permissions_result = await self.user_service.get_user_permissions(user_id, company_id)
            permissions_data = permissions_result.data if permissions_result.success else {"permissions": [], "is_super_admin": False}
            
            # Generate new access token with updated context
            access_token = self._generate_access_token(user_profile)
            
            return DatabaseResult(success=True, data={
                "access_token": access_token,
                "token_type": "bearer",
                "expires_in": self.access_token_expire_minutes * 60,
                "user": user_profile,
                "permissions": permissions_data["permissions"],
                "is_super_admin": permissions_data["is_super_admin"]
            })
            
        except Exception as e:
            logger.error(f"Company context switch failed: {e}")
            return DatabaseResult(success=False, error="Context switch failed")
    
    async def get_active_sessions(self, user_id: str) -> DatabaseResult:
        """Get user's active sessions"""
        try:
            filters = [
                QueryFilter("user_id", FilterOperation.EQUALS, user_id),
                QueryFilter("is_revoked", FilterOperation.EQUALS, False),
                QueryFilter("expires_at", FilterOperation.GREATER_THAN, datetime.utcnow())
            ]
            
            sessions_result = await self.db.find_records("refresh_tokens", filters)
            if not sessions_result.success:
                return sessions_result
            
            # Remove sensitive data
            sessions = []
            for session in sessions_result.data:
                sessions.append({
                    "id": session["id"],
                    "device_info": session.get("device_info", {}),
                    "created_at": session["created_at"],
                    "last_used": session.get("last_used"),
                    "use_count": session.get("use_count", 0),
                    "expires_at": session["expires_at"]
                })
            
            return DatabaseResult(success=True, data=sessions)
            
        except Exception as e:
            logger.error(f"Get active sessions failed: {e}")
            return DatabaseResult(success=False, error="Failed to get sessions")
    
    async def revoke_session(self, user_id: str, session_id: str) -> DatabaseResult:
        """Revoke specific user session"""
        try:
            # Verify session belongs to user
            session_result = await self.db.get_record("refresh_tokens", session_id)
            if not session_result.success:
                return DatabaseResult(success=False, error="Session not found")
            
            session_data = session_result.data
            if session_data["user_id"] != user_id:
                return DatabaseResult(success=False, error="Access denied")
            
            # Revoke session
            result = await self.db.update_record("refresh_tokens", session_id, {
                "is_revoked": True,
                "revoked_at": datetime.utcnow()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Revoke session failed: {e}")
            return DatabaseResult(success=False, error="Failed to revoke session")
    
    # Private helper methods
    
    def _generate_access_token(self, user_profile: Dict[str, Any]) -> str:
        """Generate JWT access token"""
        now = datetime.now(timezone.utc)
        payload = {
            "sub": user_profile["id"],
            "email": user_profile["email"],
            "name": user_profile.get("name"),
            "active_company": user_profile.get("active_company"),
            "active_role": user_profile.get("active_role"),
            "iat": int(now.timestamp()),
            "exp": int((now + timedelta(minutes=self.access_token_expire_minutes)).timestamp()),
            "type": "access"
        }
        
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def _generate_refresh_token(self, user_id: str) -> str:
        """Generate secure refresh token"""
        return secrets.token_urlsafe(32)
    
    async def _store_refresh_token(
        self,
        user_id: str,
        refresh_token: str,
        device_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store refresh token in database"""
        token_data = {
            "user_id": user_id,
            "token_hash": self._hash_token(refresh_token),
            "expires_at": datetime.utcnow() + timedelta(days=self.refresh_token_expire_days),
            "device_info": device_info or {},
            "is_revoked": False,
            "use_count": 0
        }
        
        await self.db.create_record("refresh_tokens", token_data)
    
    async def _validate_refresh_token(self, refresh_token: str) -> DatabaseResult:
        """Validate refresh token"""
        token_hash = self._hash_token(refresh_token)
        
        filters = [
            QueryFilter("token_hash", FilterOperation.EQUALS, token_hash),
            QueryFilter("is_revoked", FilterOperation.EQUALS, False),
            QueryFilter("expires_at", FilterOperation.GREATER_THAN, datetime.utcnow())
        ]
        
        return await self.db.find_one_record("refresh_tokens", filters)
    
    async def _revoke_all_user_tokens(self, user_id: str) -> None:
        """Revoke all refresh tokens for a user"""
        filters = [
            QueryFilter("user_id", FilterOperation.EQUALS, user_id),
            QueryFilter("is_revoked", FilterOperation.EQUALS, False)
        ]
        
        tokens_result = await self.db.find_records("refresh_tokens", filters)
        if tokens_result.success:
            for token in tokens_result.data:
                await self.db.update_record("refresh_tokens", token["id"], {
                    "is_revoked": True,
                    "revoked_at": datetime.utcnow()
                })
    
    def _hash_token(self, token: str) -> str:
        """Hash token for secure storage"""
        import hashlib
        return hashlib.sha256(token.encode()).hexdigest()