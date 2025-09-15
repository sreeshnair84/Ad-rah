"""
Enhanced Authentication API Endpoints
Provides secure authentication with refresh tokens and improved security features
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from datetime import datetime

from app.auth_service import (
    auth_service, get_current_user, require_permissions, 
    TokenData, SecurityEvent
)
from app.models import User
from app.repo import repo
from app.config import enhanced_config

logger = logging.getLogger(__name__)
security = HTTPBearer()

# Request/Response Models
class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: Dict[str, Any]

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class RefreshTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class LogoutRequest(BaseModel):
    refresh_token: str

class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str

# Create router
router = APIRouter(prefix="/auth", tags=["Enhanced Authentication"])

@router.post("/login", response_model=LoginResponse)
async def enhanced_login(request: LoginRequest, http_request: Request):
    """Enhanced login with refresh tokens and security monitoring"""
    
    # Check if account is locked
    if await auth_service.is_account_locked(request.username):
        await auth_service.log_security_event(SecurityEvent.LOGIN_FAILED, {
            "username": request.username,
            "reason": "account_locked",
            "ip_address": http_request.client.host if http_request.client else "unknown"
        })
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="Account is temporarily locked due to multiple failed login attempts"
        )
    
    try:
        # Find user
        user = await repo.get_user_by_username(request.username)
        if not user:
            await auth_service.record_failed_attempt(request.username)
            await auth_service.log_security_event(SecurityEvent.LOGIN_FAILED, {
                "username": request.username,
                "reason": "user_not_found"
            })
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Verify password
        if not auth_service.verify_password(request.password, user.password_hash):
            await auth_service.record_failed_attempt(request.username)
            await auth_service.log_security_event(SecurityEvent.LOGIN_FAILED, {
                "username": request.username,
                "reason": "invalid_password"
            })
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Check if user is active
        if user.status != "active":
            await auth_service.log_security_event(SecurityEvent.LOGIN_FAILED, {
                "username": request.username,
                "reason": "user_inactive"
            })
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is not active"
            )
        
        # Reset failed attempts on successful login
        await auth_service.reset_failed_attempts(request.username)
        
        # Create user data for token
        user_data = {
            "id": user.id,
            "user_type": user.user_type,
            "company_id": user.company_id,
            "permissions": user.permissions or []
        }
        
        # Create token pair
        access_token, refresh_token = await auth_service.create_token_pair(user_data)
        
        # Log successful login
        await auth_service.log_security_event(SecurityEvent.LOGIN_SUCCESS, {
            "user_id": user.id,
            "username": request.username,
            "ip_address": http_request.client.host if http_request.client else "unknown"
        })
        
        # Return response
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=enhanced_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user={
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "user_type": user.user_type,
                "company_id": user.company_id,
                "permissions": user.permissions or []
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error for {request.username}: {e}")
        await auth_service.log_security_event(SecurityEvent.LOGIN_FAILED, {
            "username": request.username,
            "reason": "system_error",
            "error": str(e)
        })
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed due to system error"
        )

@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_access_token(request: RefreshTokenRequest):
    """Refresh access token using refresh token"""
    
    try:
        new_access_token = await auth_service.refresh_access_token(request.refresh_token)
        
        return RefreshTokenResponse(
            access_token=new_access_token,
            expires_in=enhanced_config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/logout")
async def logout(
    request: LogoutRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Logout user by revoking tokens"""
    
    try:
        # Get access token from authorization header
        credentials: HTTPAuthorizationCredentials = Depends(security)
        access_token = credentials.credentials
        
        # Revoke both tokens
        await auth_service.logout(access_token, request.refresh_token)
        
        await auth_service.log_security_event(SecurityEvent.LOGOUT, {
            "user_id": current_user.user_id
        })
        
        return {"message": "Successfully logged out"}
        
    except Exception as e:
        logger.error(f"Logout error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/me")
async def get_current_user_profile(current_user: TokenData = Depends(get_current_user)):
    """Get current user profile information"""
    
    try:
        user = await repo.get_user_by_id(current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "user_type": user.user_type,
            "company_id": user.company_id,
            "permissions": user.permissions or [],
            "status": user.status,
            "created_at": user.created_at,
            "last_login": user.last_login,
            "token_info": {
                "user_type": current_user.user_type,
                "permissions": current_user.permissions,
                "issued_at": current_user.issued_at,
                "expires_at": current_user.expires_at
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Profile retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user profile"
        )

@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    current_user: TokenData = Depends(get_current_user)
):
    """Change user password"""
    
    try:
        # Get user
        user = await repo.get_user_by_id(current_user.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Verify current password
        if not auth_service.verify_password(request.current_password, user.password_hash):
            await auth_service.log_security_event(SecurityEvent.SUSPICIOUS_ACTIVITY, {
                "user_id": current_user.user_id,
                "activity": "invalid_password_change_attempt"
            })
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )
        
        # Validate new password (add your password policy here)
        if len(request.new_password) < 8:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 8 characters long"
            )
        
        # Hash and update password
        new_password_hash = auth_service.hash_password(request.new_password)
        user.password_hash = new_password_hash
        user.updated_at = datetime.utcnow()
        
        await repo.save_user(user)
        
        await auth_service.log_security_event(SecurityEvent.LOGIN_SUCCESS, {
            "user_id": current_user.user_id,
            "activity": "password_changed"
        })
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Password change error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )

@router.get("/security-events")
async def get_security_events(
    current_user: TokenData = Depends(require_permissions("view_security_logs"))
):
    """Get security events (admin only)"""
    
    # This would typically fetch from a security monitoring system
    # For now, return a placeholder response
    
    return {
        "message": "Security events endpoint",
        "note": "This would integrate with your security monitoring system",
        "user_permissions": current_user.permissions
    }

# Health check for authentication service
@router.get("/health")
async def auth_health_check():
    """Check authentication service health"""
    
    try:
        # Test token creation (without saving)
        test_user_data = {
            "id": "test",
            "user_type": "TEST",
            "company_id": None,
            "permissions": []
        }
        
        test_token = auth_service.create_access_token(test_user_data)
        
        return {
            "status": "healthy",
            "features": [
                "Enhanced JWT Authentication",
                "Refresh Token Support",
                "Account Lockout Protection",
                "Security Event Logging",
                "Rate Limiting",
                "Password Security"
            ],
            "config": {
                "access_token_expiry_minutes": enhanced_config.ACCESS_TOKEN_EXPIRE_MINUTES,
                "refresh_token_expiry_days": enhanced_config.REFRESH_TOKEN_EXPIRE_DAYS,
                "key_vault_enabled": enhanced_config.key_vault_service is not None
            }
        }
        
    except Exception as e:
        logger.error(f"Auth health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }