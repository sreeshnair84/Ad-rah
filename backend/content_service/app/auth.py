import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
try:
    from passlib.context import CryptContext
    _PASSLIB_AVAILABLE = True
except Exception:
    CryptContext = None
    _PASSLIB_AVAILABLE = False
import hashlib

from app.repo import repo
from app.models import User, UserRole, Company

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "CHANGE_ME_REPLACE_WITH_SECURE_SECRET")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

if _PASSLIB_AVAILABLE:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
else:
    pwd_context = None
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def _simple_hash(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def verify_password(plain_password, hashed_password):
    if pwd_context:
        return pwd_context.verify(plain_password, hashed_password)
    # fallback simple comparison using sha256
    return _simple_hash(plain_password) == hashed_password


def get_password_hash(password):
    if pwd_context:
        return pwd_context.hash(password)
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
    
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
            
        # Check token expiration
        exp = payload.get("exp")
        if exp is None:
            raise credentials_exception
            
        # Verify token hasn't expired
        if datetime.utcnow().timestamp() > exp:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except JWTError as e:
        print(f"JWT Error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_data = await repo.get_user_by_email(username)
    if user_data is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user roles
    user_roles = await repo.get_user_roles(user_data["id"])
    user_data["roles"] = user_roles

    return user_data


async def get_current_user_with_roles(token: str = Depends(oauth2_scheme)):
    """Get current user with their roles and companies"""
    user_data = await get_current_user(token)

    # Get all companies for user's roles
    companies = []
    for role in user_data.get("roles", []):
        company = await repo.get_company(role["company_id"])
        if company:
            companies.append(company)

    user_data["companies"] = companies
    
    # Expand roles with role details
    expanded_roles = []
    for user_role in user_data.get("roles", []):
        role_id = user_role.get("role_id")
        if role_id and role_id.strip():  # Check if role_id is not empty
            role = await repo.get_role(role_id)
            if role:
                expanded_role = {
                    **user_role,
                    "role": role.get("role_group"),  # Add role_group as 'role' for frontend compatibility
                    "role_name": role.get("name"),   # Add role name
                    "role_details": role
                }
                expanded_roles.append(expanded_role)
            else:
                # Role not found, keep original but add default role info
                expanded_roles.append({
                    **user_role,
                    "role": "ADMIN",  # Default to ADMIN for missing roles
                    "role_name": "Administrator"
                })
        else:
            # No role_id, this might be an old format or corrupted data
            # Try to find a suitable default role for the company
            company_id = user_role.get("company_id")
            if company_id:
                # Look for default roles for this company
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
                else:
                    # No default role found, use fallback
                    expanded_roles.append({
                        **user_role,
                        "role": "ADMIN",
                        "role_name": "Administrator"
                    })
            else:
                # No company_id either, use fallback
                expanded_roles.append({
                    **user_role,
                    "role": "ADMIN",
                    "role_name": "Administrator"
                })
    
    user_data["roles"] = expanded_roles
    
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


# Initialize with some default data for development
async def init_default_data():
    """Initialize default companies and users for development"""
    try:
        print("Starting default data initialization...")
        
        # Check if default data already exists
        existing_companies = await repo.list_companies()
        existing_users = await repo.list_users()
        
        # Also check for user roles - if users exist but have no roles, we need to create roles
        user_roles_exist = False
        if existing_users:
            for user in existing_users:
                user_id = user.get("id")
                if user_id:
                    user_roles = await repo.get_user_roles(user_id)
                    # Check if roles exist and have valid company_id and role_id
                    if user_roles and any(role.get("company_id") and role.get("role_id") for role in user_roles):
                        user_roles_exist = True
                        break
        
        if existing_companies and existing_users and user_roles_exist:
            print(f"Found {len(existing_companies)} existing companies and {len(existing_users)} existing users with roles, skipping initialization")
            return
        
        print(f"Found {len(existing_companies)} companies and {len(existing_users)} users, user roles exist: {user_roles_exist}, proceeding with initialization...")

        # Create default companies
        admin_company = Company(
            name="OpenKiosk Admin",
            type="HOST",
            address="Dubai Media City",
            city="Dubai",
            country="UAE",
            email="admin@openkiosk.com",
            status="active"
        )

        host_company = Company(
            name="Dubai Mall Management",
            type="HOST",
            address="Financial Centre Road",
            city="Dubai",
            country="UAE",
            phone="+971-4-123-4567",
            email="admin@dubaill.com",
            website="https://www.dubaill.com",
            status="active"
        )

        advertiser_company = Company(
            name="Brand Solutions UAE",
            type="ADVERTISER",
            address="Business Bay",
            city="Dubai",
            country="UAE",
            phone="+971-4-555-0123",
            email="contact@brandsolutions.ae",
            website="https://www.brandsolutions.ae",
            status="active"
        )

        admin_company_data = await repo.save_company(admin_company)
        host_company_data = await repo.save_company(host_company)
        advertiser_company_data = await repo.save_company(advertiser_company)

        # Create default roles
        from app.models import Role, RoleGroup, RolePermission, Screen, Permission

        admin_role = Role(
            name="System Administrator",
            role_group=RoleGroup.ADMIN,
            company_id=admin_company_data["id"] if admin_company_data else "",
            is_default=True,
            status="active"
        )

        host_role = Role(
            name="Host Manager",
            role_group=RoleGroup.HOST,
            company_id=host_company_data["id"] if host_company_data else "",
            is_default=True,
            status="active"
        )

        advertiser_role = Role(
            name="Advertiser Manager",
            role_group=RoleGroup.ADVERTISER,
            company_id=advertiser_company_data["id"] if advertiser_company_data else "",
            is_default=True,
            status="active"
        )

        admin_role_data = await repo.save_role(admin_role)
        host_role_data = await repo.save_role(host_role)
        advertiser_role_data = await repo.save_role(advertiser_role)

        # Create default users
        admin_user = User(
            name="System Admin",
            email="admin@openkiosk.com",
            hashed_password=get_password_hash("adminpass"),
            status="active"
        )

        host_user = User(
            name="Host Manager",
            email="host@openkiosk.com",
            hashed_password=get_password_hash("hostpass"),
            status="active"
        )

        advertiser_user = User(
            name="Advertiser Manager",
            email="advertiser@openkiosk.com",
            hashed_password=get_password_hash("advertiserpass"),
            status="active"
        )

        await repo.save_user(admin_user)
        await repo.save_user(host_user)
        await repo.save_user(advertiser_user)

        # Refresh user data with IDs
        admin_user_data = await repo.get_user_by_email("admin@openkiosk.com")
        host_user_data = await repo.get_user_by_email("host@openkiosk.com")
        advertiser_user_data = await repo.get_user_by_email("advertiser@openkiosk.com")

        # Create user roles
        admin_user_role = UserRole(
            user_id=admin_user_data["id"] if admin_user_data else "",
            company_id=admin_company_data["id"] if admin_company_data else "",
            role_id=admin_role_data["id"] if admin_role_data else "",
            is_default=True,
            status="active"
        )

        host_user_role = UserRole(
            user_id=host_user_data["id"] if host_user_data else "",
            company_id=host_company_data["id"] if host_company_data else "",
            role_id=host_role_data["id"] if host_role_data else "",
            is_default=True,
            status="active"
        )

        advertiser_user_role = UserRole(
            user_id=advertiser_user_data["id"] if advertiser_user_data else "",
            company_id=advertiser_company_data["id"] if advertiser_company_data else "",
            role_id=advertiser_role_data["id"] if advertiser_role_data else "",
            is_default=True,
            status="active"
        )

        await repo.save_user_role(admin_user_role)
        await repo.save_user_role(host_user_role)
        await repo.save_user_role(advertiser_user_role)

        # Create default content meta and metadata for development
        from app.models import ContentMeta, ContentMetadata, Review
        from datetime import datetime, timedelta

        # Mock content for host user
        try:
            content_meta1 = ContentMeta(
                id=None,
                owner_id=host_user_data["id"] if host_user_data else "",
                filename="sample_ad.mp4",
                content_type="video/mp4",
                size=1024000,
                status="approved"
            )

            content_meta2 = ContentMeta(
                id=None,
                owner_id=advertiser_user_data["id"] if advertiser_user_data else "",
                filename="banner.jpg",
                content_type="image/jpeg",
                size=512000,
                status="approved"
            )

            await repo.save_content_meta(content_meta1)
            await repo.save_content_meta(content_meta2)

            # Refresh content meta with IDs
            content_meta1_data = await repo.get_content_meta(content_meta1.id) if content_meta1.id else None
            content_meta2_data = await repo.get_content_meta(content_meta2.id) if content_meta2.id else None

            # Create content metadata
            content_metadata1 = ContentMetadata(
                title="Dubai Mall Advertisement",
                description="Promotional video for Dubai Mall showcasing latest offers",
                owner_id=host_user_data["id"] if host_user_data else "",
                categories=["advertisement", "shopping"],
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(days=7),
                tags=["dubai", "mall", "offers"]
            )

            content_metadata2 = ContentMetadata(
                title="Brand Solutions Banner",
                description="Banner advertisement for Brand Solutions UAE",
                owner_id=advertiser_user_data["id"] if advertiser_user_data else "",
                categories=["banner", "advertisement"],
                start_time=datetime.utcnow(),
                end_time=datetime.utcnow() + timedelta(days=30),
                tags=["brand", "solutions", "uae"]
            )

            await repo.save(content_metadata1)
            await repo.save(content_metadata2)

            # Create some reviews
            review1 = Review(
                content_id=content_metadata1.id if content_metadata1.id else "",
                ai_confidence=0.95,
                action="approved",
                reviewer_id=admin_user_data["id"] if admin_user_data else "",
                notes="High quality promotional content"
            )

            review2 = Review(
                content_id=content_metadata2.id if content_metadata2.id else "",
                ai_confidence=0.88,
                action="approved",
                reviewer_id=admin_user_data["id"] if admin_user_data else "",
                notes="Good banner design"
            )

            await repo.save_review(review1.model_dump())
            await repo.save_review(review2.model_dump())
        except Exception as e:
            print(f"Error creating content data: {e}")
            # Continue with user/role setup even if content creation fails

    except Exception as e:
        print(f"Error initializing default data: {e}")
