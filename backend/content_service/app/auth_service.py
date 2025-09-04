# Clean Authentication Service
import logging
from datetime import datetime, timedelta
from typing import Optional
import hashlib
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

try:
    from passlib.context import CryptContext
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    BCRYPT_AVAILABLE = True
except ImportError:
    pwd_context = None
    BCRYPT_AVAILABLE = False

from app.config import settings
from app.database_service import db_service
from app.rbac_models import *

logger = logging.getLogger(__name__)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

SECRET_KEY = settings.JWT_SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES

class AuthService:
    def __init__(self):
        if not BCRYPT_AVAILABLE:
            logger.warning("⚠️ BCRYPT not available - using fallback password hashing")
    
    def hash_password(self, password: str) -> str:
        if not password:
            raise ValueError("Password cannot be empty")
        
        if BCRYPT_AVAILABLE and pwd_context:
            return pwd_context.hash(password)
        else:
            salt = settings.SECRET_KEY
            return hashlib.sha256((salt + password).encode()).hexdigest()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        if not plain_password or not hashed_password:
            return False
        
        if BCRYPT_AVAILABLE and pwd_context:
            try:
                return pwd_context.verify(plain_password, hashed_password)
            except Exception:
                return False
        else:
            salt = settings.SECRET_KEY
            expected_hash = hashlib.sha256((salt + plain_password).encode()).hexdigest()
            return expected_hash == hashed_password
    
    def create_access_token(self, user_profile: UserProfile) -> str:
        expires_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        expire = datetime.utcnow() + expires_delta
        
        token_data = {
            "sub": user_profile.id,
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
    
    def verify_token(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
            
            if payload.get("type") != "access_token":
                raise JWTError("Invalid token type")
            
            user_id = payload.get("sub")
            email = payload.get("email")
            
            if not user_id or not email:
                raise JWTError("Invalid token format")
            
            return payload
        except JWTError as e:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token",
                headers={"WWW-Authenticate": "Bearer"}
            )
    
    async def authenticate_user(self, email: str, password: str) -> Optional[UserProfile]:
        try:
            user_data = await db_service.get_user_by_email(email)
            if not user_data:
                return None
            
            if not self.verify_password(password, user_data.get("hashed_password", "")):
                return None
            
            if not user_data.get("is_active", True):
                return None
            
            user_profile = await db_service.get_user_profile(user_data["id"])
            if user_profile:
                await db_service.update_user_login(user_data["id"])
            
            return user_profile
        except Exception as e:
            logger.error(f"Authentication error for {email}: {e}")
            return None
    
    async def login(self, login_request: LoginRequest) -> LoginResponse:
        user_profile = await self.authenticate_user(login_request.email, login_request.password)
        
        if not user_profile:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        access_token = self.create_access_token(user_profile)
        
        return LoginResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user=user_profile
        )
    
    async def get_current_user(self, token: str) -> UserProfile:
        payload = self.verify_token(token)
        user_id = payload["sub"]
        
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
    
    async def register_user(self, user_data: UserCreate) -> UserProfile:
        hashed_password = self.hash_password(user_data.password)
        user = await db_service.create_user(user_data, hashed_password)
        user_profile = await db_service.get_user_profile(user.id)
        if not user_profile:
            raise HTTPException(status_code=500, detail="Failed to create user profile")
        return user_profile

# Global instance
auth_service = AuthService()

# FastAPI Dependencies
async def get_current_user(token: str = Depends(oauth2_scheme)) -> UserProfile:
    return await auth_service.get_current_user(token)

async def get_current_active_user(current_user: UserProfile = Depends(get_current_user)) -> UserProfile:
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user account")
    return current_user

def require_permission(permission: str):
    async def permission_dependency(current_user: UserProfile = Depends(get_current_active_user)) -> UserProfile:
        if current_user.user_type != UserType.SUPER_USER and permission not in current_user.permissions:
            raise HTTPException(status_code=403, detail=f"Permission required: {permission}")
        return current_user
    return permission_dependency

def require_user_type(*allowed_types: UserType):
    async def user_type_dependency(current_user: UserProfile = Depends(get_current_active_user)) -> UserProfile:
        if current_user.user_type not in allowed_types:
            raise HTTPException(status_code=403, detail=f"User type required: {[t.value for t in allowed_types]}")
        return current_user
    return user_type_dependency
