from datetime import datetime
import uuid
from app.models import Role, User, UserRole, Company
from app.repo import repo
from app.auth_service import auth_service
from passlib.context import CryptContext

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


async def initialize_mock_data():
    """Initialize comprehensive mock data for users, roles, and companies"""
    
    # Initialize companies first
    await initialize_companies()
    
    # Initialize roles
    await initialize_roles()
    
    # Initialize users with proper role assignments
    await initialize_users()


async def initialize_companies():
    """Initialize mock companies"""
    companies = [
        {
            "id": "company_001",
            "name": "TechCorp Solutions",
            "type": "HOST",
            "address": "123 Business Ave",
            "city": "New York",
            "country": "USA",
            "phone": "+1-555-0101",
            "email": "contact@techcorp.com",
            "website": "https://techcorp.com",
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": "company_002",
            "name": "Creative Ads Inc",
            "type": "ADVERTISER",
            "address": "456 Marketing St",
            "city": "San Francisco",
            "country": "USA",
            "phone": "+1-555-0102",
            "email": "hello@creativeads.com",
            "website": "https://creativeads.com",
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": "company_003",
            "name": "Digital Displays LLC",
            "type": "HOST",
            "address": "789 Display Rd",
            "city": "Austin",
            "country": "USA",
            "phone": "+1-555-0103",
            "email": "support@digitaldisplays.com",
            "website": "https://digitaldisplays.com",
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": "company_004",
            "name": "AdVantage Media",
            "type": "ADVERTISER",
            "address": "321 Commerce Blvd",
            "city": "Chicago",
            "country": "USA",
            "phone": "+1-555-0104",
            "email": "info@advantage-media.com",
            "website": "https://advantage-media.com",
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    ]
    
    # Check if repo has _store (InMemoryRepo) or use MongoDB methods
    if hasattr(repo, '_store'):
        # InMemoryRepo
        company_store = repo._store.setdefault("__companies__", {})
        for company in companies:
            if company["id"] not in company_store:
                company_store[company["id"]] = company
    else:
        # MongoRepo - use proper async methods
        for company_data in companies:
            from app.models import Company
            # Create Company object with proper datetime conversion
            company = Company(
                id=company_data["id"],
                name=company_data["name"],
                type=company_data["type"],
                address=company_data["address"],
                city=company_data["city"],
                country=company_data["country"],
                phone=company_data.get("phone"),
                email=company_data.get("email"),
                website=company_data.get("website"),
                status=company_data["status"],
                created_at=datetime.fromisoformat(company_data["created_at"]),
                updated_at=datetime.fromisoformat(company_data["updated_at"])
            )
            # Check if company already exists
            if company.id:
                existing = await repo.get_company(company.id)
                if not existing:
                    await repo.save_company(company)


async def initialize_roles():
    """Initialize comprehensive role structure"""
    roles = [
        # System Administrator Role
        {
            "id": "role_001",
            "name": "System Administrator",
            "role_group": "ADMIN",
            "company_id": "global",
            "is_default": True,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        
        # TechCorp Solutions Roles (HOST)
        {
            "id": "role_002",
            "name": "TechCorp Manager",
            "role_group": "HOST",
            "company_id": "company_001",
            "is_default": True,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": "role_003",
            "name": "TechCorp Screen Operator",
            "role_group": "HOST",
            "company_id": "company_001",
            "is_default": False,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        
        # Creative Ads Inc Roles (ADVERTISER)
        {
            "id": "role_004",
            "name": "Creative Director",
            "role_group": "ADVERTISER",
            "company_id": "company_002",
            "is_default": True,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": "role_005",
            "name": "Content Creator",
            "role_group": "ADVERTISER",
            "company_id": "company_002",
            "is_default": False,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        
        # Digital Displays LLC Roles (HOST)
        {
            "id": "role_006",
            "name": "Display Manager",
            "role_group": "HOST",
            "company_id": "company_003",
            "is_default": True,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        
        # AdVantage Media Roles (ADVERTISER)
        {
            "id": "role_007",
            "name": "Media Manager",
            "role_group": "ADVERTISER",
            "company_id": "company_004",
            "is_default": True,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    ]
    
    # Check if repo has _store (InMemoryRepo) or use MongoDB methods
    if hasattr(repo, '_store'):
        # InMemoryRepo
        role_store = repo._store.setdefault("__roles__", {})
        for role in roles:
            if role["id"] not in role_store:
                role_store[role["id"]] = role
    else:
        # MongoRepo - use proper async methods
        for role_data in roles:
            from app.models import Role, RoleGroup
            # Create Role object with proper enum conversion
            role = Role(
                id=role_data["id"],
                name=role_data["name"],
                role_group=RoleGroup(role_data["role_group"]),
                company_id=role_data["company_id"],
                is_default=role_data["is_default"],
                status=role_data["status"],
                created_at=datetime.fromisoformat(role_data["created_at"]),
                updated_at=datetime.fromisoformat(role_data["updated_at"])
            )
            # Check if role already exists
            if role.id:
                existing = await repo.get_role(role.id)
                if not existing:
                    await repo.save_role(role)
    
    # Initialize role permissions
    await initialize_role_permissions()


async def initialize_role_permissions():
    """Initialize comprehensive role permissions"""
    permissions = [
        # System Administrator - Full access
        {
            "id": "perm_001",
            "role_id": "role_001",
            "screen": "dashboard",
            "permissions": ["view", "edit", "delete", "access"],
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "perm_002",
            "role_id": "role_001",
            "screen": "users",
            "permissions": ["view", "edit", "delete", "access"],
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "perm_003",
            "role_id": "role_001",
            "screen": "companies",
            "permissions": ["view", "edit", "delete", "access"],
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "perm_004",
            "role_id": "role_001",
            "screen": "content",
            "permissions": ["view", "edit", "delete", "access"],
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "perm_005",
            "role_id": "role_001",
            "screen": "moderation",
            "permissions": ["view", "edit", "delete", "access"],
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "perm_006",
            "role_id": "role_001",
            "screen": "analytics",
            "permissions": ["view", "access"],
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "perm_007",
            "role_id": "role_001",
            "screen": "settings",
            "permissions": ["view", "edit", "access"],
            "created_at": datetime.utcnow().isoformat()
        },
        
        # HOST Roles - Content and screen management
        {
            "id": "perm_008",
            "role_id": "role_002",
            "screen": "dashboard",
            "permissions": ["view", "access"],
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "perm_009",
            "role_id": "role_002",
            "screen": "content",
            "permissions": ["view", "edit", "access"],
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "perm_010",
            "role_id": "role_002",
            "screen": "moderation",
            "permissions": ["view", "edit", "access"],
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "perm_011",
            "role_id": "role_002",
            "screen": "analytics",
            "permissions": ["view", "access"],
            "created_at": datetime.utcnow().isoformat()
        },
        
        # ADVERTISER Roles - Content creation and analytics
        {
            "id": "perm_012",
            "role_id": "role_004",
            "screen": "dashboard",
            "permissions": ["view", "access"],
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "perm_013",
            "role_id": "role_004",
            "screen": "content",
            "permissions": ["view", "edit", "access"],
            "created_at": datetime.utcnow().isoformat()
        },
        {
            "id": "perm_014",
            "role_id": "role_004",
            "screen": "analytics",
            "permissions": ["view", "access"],
            "created_at": datetime.utcnow().isoformat()
        }
    ]
    
    # Check if repo has _store (InMemoryRepo) or use MongoDB methods
    if hasattr(repo, '_store'):
        # InMemoryRepo
        permission_store = repo._store.setdefault("__role_permissions__", {})
        for permission in permissions:
            if permission["id"] not in permission_store:
                permission_store[permission["id"]] = permission
    else:
        # MongoRepo - use proper async methods
        for permission_data in permissions:
            from app.models import RolePermission, Screen, Permission
            # Create RolePermission object with proper enum conversion
            permission = RolePermission(
                id=permission_data["id"],
                role_id=permission_data["role_id"],
                screen=Screen(permission_data["screen"]),
                permissions=[Permission(p) for p in permission_data["permissions"]],
                created_at=datetime.fromisoformat(permission_data["created_at"])
            )
            # Check if permission already exists
            if permission.id:
                existing_permissions = await repo.get_role_permissions(permission.role_id)
                existing_ids = [p.get("id") for p in existing_permissions if p.get("id")]
                if permission.id not in existing_ids:
                    await repo.save_role_permission(permission)


async def initialize_users():
    """Initialize comprehensive user base with proper role assignments"""
    users = [
        # System Administrator
        {
            "id": "user_001",
            "name": "System Admin",
            "email": "admin@adara.com",
            "phone": "+1-555-0001",
            "status": "active",
            "hashed_password": auth_service.hash_password("adminpass"),
            "oauth_provider": None,
            "oauth_id": None,
            "email_verified": True,
            "last_login": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        
        # TechCorp Users
        {
            "id": "user_002",
            "name": "John Smith",
            "email": "john.smith@techcorp.com",
            "phone": "+1-555-0002",
            "status": "active",
            "hashed_password": get_password_hash("hostpass"),
            "oauth_provider": None,
            "oauth_id": None,
            "email_verified": True,
            "last_login": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": "user_003",
            "name": "Sarah Johnson",
            "email": "sarah.johnson@techcorp.com",
            "phone": "+1-555-0003",
            "status": "active",
            "hashed_password": get_password_hash("hostpass"),
            "oauth_provider": None,
            "oauth_id": None,
            "email_verified": True,
            "last_login": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        
        # Creative Ads Users
        {
            "id": "user_004",
            "name": "Mike Creative",
            "email": "mike@creativeads.com",
            "phone": "+1-555-0004",
            "status": "active",
            "hashed_password": get_password_hash("advertiserpass"),
            "oauth_provider": None,
            "oauth_id": None,
            "email_verified": True,
            "last_login": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": "user_005",
            "name": "Emma Designer",
            "email": "emma@creativeads.com",
            "phone": "+1-555-0005",
            "status": "active",
            "hashed_password": get_password_hash("advertiserpass"),
            "oauth_provider": None,
            "oauth_id": None,
            "email_verified": True,
            "last_login": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        
        # Digital Displays Users
        {
            "id": "user_006",
            "name": "David Display",
            "email": "david@digitaldisplays.com",
            "phone": "+1-555-0006",
            "status": "active",
            "hashed_password": get_password_hash("hostpass"),
            "oauth_provider": None,
            "oauth_id": None,
            "email_verified": True,
            "last_login": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        
        # AdVantage Media Users
        {
            "id": "user_007",
            "name": "Lisa Marketing",
            "email": "lisa@advantage-media.com",
            "phone": "+1-555-0007",
            "status": "active",
            "hashed_password": get_password_hash("advertiserpass"),
            "oauth_provider": None,
            "oauth_id": None,
            "email_verified": True,
            "last_login": datetime.utcnow().isoformat(),
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        
        # Inactive/Pending Users
        {
            "id": "user_008",
            "name": "Test User",
            "email": "test@example.com",
            "phone": "+1-555-0008",
            "status": "inactive",
            "hashed_password": get_password_hash("testpass"),
            "oauth_provider": None,
            "oauth_id": None,
            "email_verified": False,
            "last_login": None,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    ]
    
    # Check if repo has _store (InMemoryRepo) or use MongoDB methods
    if hasattr(repo, '_store'):
        # InMemoryRepo
        user_store = repo._store.setdefault("__users__", {})
        for user in users:
            if user["id"] not in user_store:
                user_store[user["id"]] = user
    else:
        # MongoRepo - use proper async methods
        for user_data in users:
            from app.models import User
            # Create User object with proper datetime conversion
            user = User(
                id=user_data["id"],
                name=user_data["name"],
                email=user_data["email"],
                phone=user_data.get("phone"),
                status=user_data["status"],
                hashed_password=user_data["hashed_password"],
                oauth_provider=user_data.get("oauth_provider"),
                oauth_id=user_data.get("oauth_id"),
                email_verified=user_data["email_verified"],
                last_login=datetime.fromisoformat(user_data["last_login"]) if user_data.get("last_login") else None,
                created_at=datetime.fromisoformat(user_data["created_at"]),
                updated_at=datetime.fromisoformat(user_data["updated_at"])
            )
            # Check if user already exists
            if user.id:
                existing = await repo.get_user(user.id)
                if not existing:
                    await repo.save_user(user)
    
    # Initialize user role assignments
    await initialize_user_roles()


async def initialize_user_roles():
    """Initialize user role assignments"""
    user_roles = [
        # System Admin
        {
            "id": "user_role_001",
            "user_id": "user_001",
            "company_id": "global",
            "role_id": "role_001",
            "is_default": True,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        
        # TechCorp Users
        {
            "id": "user_role_002",
            "user_id": "user_002",
            "company_id": "company_001",
            "role_id": "role_002",
            "is_default": True,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": "user_role_003",
            "user_id": "user_003",
            "company_id": "company_001",
            "role_id": "role_003",
            "is_default": True,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        
        # Creative Ads Users
        {
            "id": "user_role_004",
            "user_id": "user_004",
            "company_id": "company_002",
            "role_id": "role_004",
            "is_default": True,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        {
            "id": "user_role_005",
            "user_id": "user_005",
            "company_id": "company_002",
            "role_id": "role_005",
            "is_default": True,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        
        # Digital Displays User
        {
            "id": "user_role_006",
            "user_id": "user_006",
            "company_id": "company_003",
            "role_id": "role_006",
            "is_default": True,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        },
        
        # AdVantage Media User
        {
            "id": "user_role_007",
            "user_id": "user_007",
            "company_id": "company_004",
            "role_id": "role_007",
            "is_default": True,
            "status": "active",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
    ]
    
    # Check if repo has _store (InMemoryRepo) or use MongoDB methods
    if hasattr(repo, '_store'):
        # InMemoryRepo
        user_role_store = repo._store.setdefault("__user_roles__", {})
        for user_role in user_roles:
            if user_role["id"] not in user_role_store:
                user_role_store[user_role["id"]] = user_role
    else:
        # MongoRepo - use proper async methods
        for user_role_data in user_roles:
            from app.models import UserRole
            # Create UserRole object with proper datetime conversion
            user_role = UserRole(
                id=user_role_data["id"],
                user_id=user_role_data["user_id"],
                company_id=user_role_data["company_id"],
                role_id=user_role_data["role_id"],
                is_default=user_role_data["is_default"],
                status=user_role_data["status"],
                created_at=datetime.fromisoformat(user_role_data["created_at"]),
                updated_at=datetime.fromisoformat(user_role_data["updated_at"])
            )
            # Check if user role already exists
            if user_role.id:
                existing_roles = await repo.get_user_roles(user_role.user_id)
                existing_ids = [r.get("id") for r in existing_roles if r.get("id")]
                if user_role.id not in existing_ids:
                    await repo.save_user_role(user_role)