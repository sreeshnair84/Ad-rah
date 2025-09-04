# Clean Database Service for Adārah Digital Signage Platform
# Removes in-memory fallback and provides clean MongoDB-only operations

import logging
import asyncio
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import uuid
from bson import ObjectId

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo.errors import (
    ConnectionFailure, 
    DuplicateKeyError, 
    OperationFailure,
    ServerSelectionTimeoutError
)

from app.config import settings
from app.rbac_models_new import (
    User, UserCreate, UserUpdate, UserProfile,
    Company, CompanyCreate, CompanyUpdate,
    DeviceCredentials,
    UserType, CompanyType, CompanyRole,
    get_permissions_for_role, get_accessible_navigation,
    generate_organization_code, generate_registration_key, generate_api_key
)

logger = logging.getLogger(__name__)


class DatabaseService:
    """Clean MongoDB database service for RBAC operations"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.connected = False
    
    async def initialize(self) -> bool:
        """Initialize MongoDB connection"""
        if not settings.MONGO_URI:
            raise ValueError("MONGO_URI environment variable is required")
        
        try:
            self.client = AsyncIOMotorClient(
                settings.MONGO_URI,
                maxPoolSize=10,
                minPoolSize=1,
                serverSelectionTimeoutMS=5000
            )
            
            # Test connection
            await self.client.admin.command('ping')
            
            # Get database name from URI or use default
            self.db = self.client.get_default_database() or self.client.openkiosk
            
            # Create indexes
            await self._create_indexes()
            
            self.connected = True
            logger.info("✅ MongoDB connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            self.connected = False
            raise ConnectionError(f"Database connection failed: {e}")
    
    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("🔌 MongoDB connection closed")
    
    async def _create_indexes(self):
        """Create necessary database indexes"""
        try:
            # Users collection indexes
            users = self.db.users
            await users.create_index("email", unique=True)
            await users.create_index([("company_id", 1), ("user_type", 1)])
            await users.create_index("user_type")
            
            # Companies collection indexes
            companies = self.db.companies
            await companies.create_index("organization_code", unique=True)
            await companies.create_index("registration_key", unique=True)
            await companies.create_index("company_type")
            
            # Devices collection indexes
            devices = self.db.devices
            await devices.create_index("api_key", unique=True)
            await devices.create_index([("company_id", 1), ("status", 1)])
            
            logger.info("📊 Database indexes created successfully")
            
        except Exception as e:
            logger.warning(f"⚠️ Failed to create some indexes: {e}")
    
    def _ensure_connected(self):
        """Ensure database is connected"""
        if not self.connected or not self.db:
            raise ConnectionError("Database not connected. Call initialize() first.")
    
    def _object_id_to_str(self, doc: Dict) -> Dict:
        """Convert ObjectId to string for JSON serialization"""
        if doc and "_id" in doc:
            doc["id"] = str(doc["_id"])
            del doc["_id"]
        return doc
    
    # ================================
    # USER MANAGEMENT
    # ================================
    
    async def create_user(self, user_data: UserCreate, hashed_password: str) -> User:
        """Create a new user"""
        self._ensure_connected()
        
        # Validate user data
        from app.rbac_models_new import validate_user_creation
        validate_user_creation(user_data)
        
        user_doc = {
            "id": str(uuid.uuid4()),
            "email": user_data.email,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "phone": user_data.phone,
            "user_type": user_data.user_type.value,
            "company_id": user_data.company_id,
            "company_role": user_data.company_role.value if user_data.company_role else None,
            "hashed_password": hashed_password,
            "permissions": [],  # Will be computed from role
            "is_active": True,
            "email_verified": False,
            "last_login": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        try:
            result = await self.db.users.insert_one(user_doc)
            user_doc["_id"] = result.inserted_id
            user_doc = self._object_id_to_str(user_doc)
            
            logger.info(f"👤 User created: {user_data.email}")
            return User(**user_doc)
            
        except DuplicateKeyError:
            raise ValueError(f"User with email {user_data.email} already exists")
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        """Get user by email"""
        self._ensure_connected()
        
        user = await self.db.users.find_one({"email": email, "is_active": True})
        return self._object_id_to_str(user) if user else None
    
    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        self._ensure_connected()
        
        user = await self.db.users.find_one({"id": user_id, "is_active": True})
        if not user:
            return None
        
        user = self._object_id_to_str(user)
        return User(**user)
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        """Get enhanced user profile with permissions and company data"""
        self._ensure_connected()
        
        # Get user
        user = await self.db.users.find_one({"id": user_id, "is_active": True})
        if not user:
            return None
        
        user = self._object_id_to_str(user)
        
        # Get company data if user belongs to a company
        company = None
        if user.get("company_id"):
            company_doc = await self.db.companies.find_one({"id": user["company_id"]})
            if company_doc:
                company = self._object_id_to_str(company_doc)
        
        # Compute permissions based on role
        user_type = UserType(user["user_type"])
        company_type = CompanyType(company["company_type"]) if company else None
        company_role = CompanyRole(user["company_role"]) if user.get("company_role") else None
        
        permissions = get_permissions_for_role(user_type, company_type, company_role)
        permission_strings = [p.value for p in permissions]
        
        # Get accessible navigation
        accessible_navigation = get_accessible_navigation(
            user_type, company_type, company_role, permission_strings
        )
        
        # Create display name and role display
        display_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        if not display_name:
            display_name = user.get('email', 'Unknown User')
        
        if user_type == UserType.SUPER_USER:
            role_display = "Super User"
        elif company_role:
            role_display = company_role.value.title()
        else:
            role_display = "User"
        
        # Build profile
        profile_data = {
            **user,
            "permissions": permission_strings,
            "company": company,
            "accessible_navigation": accessible_navigation,
            "display_name": display_name,
            "role_display": role_display
        }
        
        return UserProfile(**profile_data)
    
    async def update_user(self, user_id: str, updates: UserUpdate) -> bool:
        """Update user"""
        self._ensure_connected()
        
        update_doc = {
            "updated_at": datetime.utcnow()
        }
        
        if updates.first_name is not None:
            update_doc["first_name"] = updates.first_name
        if updates.last_name is not None:
            update_doc["last_name"] = updates.last_name
        if updates.phone is not None:
            update_doc["phone"] = updates.phone
        if updates.company_role is not None:
            update_doc["company_role"] = updates.company_role.value
        if updates.is_active is not None:
            update_doc["is_active"] = updates.is_active
        
        result = await self.db.users.update_one(
            {"id": user_id},
            {"$set": update_doc}
        )
        
        return result.modified_count > 0
    
    async def list_users(self, company_id: Optional[str] = None) -> List[User]:
        """List users, optionally filtered by company"""
        self._ensure_connected()
        
        query = {"is_active": True}
        if company_id:
            query["company_id"] = company_id
        
        cursor = self.db.users.find(query).sort("created_at", -1)
        users = []
        
        async for user_doc in cursor:
            user_doc = self._object_id_to_str(user_doc)
            users.append(User(**user_doc))
        
        return users
    
    async def update_user_login(self, user_id: str):
        """Update user last login timestamp"""
        self._ensure_connected()
        
        await self.db.users.update_one(
            {"id": user_id},
            {"$set": {"last_login": datetime.utcnow()}}
        )
    
    # ================================
    # COMPANY MANAGEMENT
    # ================================
    
    async def create_company(self, company_data: CompanyCreate) -> Company:
        """Create a new company"""
        self._ensure_connected()
        
        # Generate codes if not provided
        organization_code = company_data.organization_code or generate_organization_code()
        registration_key = generate_registration_key()
        
        company_doc = {
            "id": str(uuid.uuid4()),
            "name": company_data.name,
            "company_type": company_data.company_type.value,
            "organization_code": organization_code,
            "registration_key": registration_key,
            "address": company_data.address,
            "city": company_data.city,
            "country": company_data.country,
            "phone": company_data.phone,
            "email": company_data.email,
            "website": company_data.website,
            "status": "active",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        try:
            result = await self.db.companies.insert_one(company_doc)
            company_doc["_id"] = result.inserted_id
            company_doc = self._object_id_to_str(company_doc)
            
            logger.info(f"🏢 Company created: {company_data.name}")
            return Company(**company_doc)
            
        except DuplicateKeyError as e:
            if "organization_code" in str(e):
                raise ValueError("Organization code already exists")
            raise ValueError("Company registration key already exists")
        except Exception as e:
            logger.error(f"Failed to create company: {e}")
            raise
    
    async def get_company(self, company_id: str) -> Optional[Company]:
        """Get company by ID"""
        self._ensure_connected()
        
        company = await self.db.companies.find_one({"id": company_id})
        if not company:
            return None
        
        company = self._object_id_to_str(company)
        return Company(**company)
    
    async def get_company_by_org_code(self, org_code: str) -> Optional[Company]:
        """Get company by organization code"""
        self._ensure_connected()
        
        company = await self.db.companies.find_one({"organization_code": org_code})
        if not company:
            return None
        
        company = self._object_id_to_str(company)
        return Company(**company)
    
    async def list_companies(self) -> List[Company]:
        """List all companies"""
        self._ensure_connected()
        
        cursor = self.db.companies.find({"status": "active"}).sort("created_at", -1)
        companies = []
        
        async for company_doc in cursor:
            company_doc = self._object_id_to_str(company_doc)
            companies.append(Company(**company_doc))
        
        return companies
    
    async def update_company(self, company_id: str, updates: CompanyUpdate) -> bool:
        """Update company"""
        self._ensure_connected()
        
        update_doc = {"updated_at": datetime.utcnow()}
        
        for field, value in updates.model_dump(exclude_unset=True).items():
            if value is not None:
                update_doc[field] = value
        
        result = await self.db.companies.update_one(
            {"id": company_id},
            {"$set": update_doc}
        )
        
        return result.modified_count > 0
    
    # ================================
    # DEVICE MANAGEMENT
    # ================================
    
    async def create_device(
        self,
        device_name: str,
        company_id: str,
        device_type: str = "kiosk",
        location: Optional[str] = None
    ) -> DeviceCredentials:
        """Create device credentials"""
        self._ensure_connected()
        
        device_doc = {
            "id": str(uuid.uuid4()),
            "device_id": str(uuid.uuid4()),  # Separate device ID
            "company_id": company_id,
            "api_key": generate_api_key(),
            "device_name": device_name,
            "device_type": device_type,
            "location": location,
            "status": "active",
            "last_seen": None,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        try:
            result = await self.db.devices.insert_one(device_doc)
            device_doc["_id"] = result.inserted_id
            device_doc = self._object_id_to_str(device_doc)
            
            logger.info(f"📱 Device created: {device_name}")
            return DeviceCredentials(**device_doc)
            
        except Exception as e:
            logger.error(f"Failed to create device: {e}")
            raise
    
    async def get_device_by_api_key(self, api_key: str) -> Optional[DeviceCredentials]:
        """Get device by API key"""
        self._ensure_connected()
        
        device = await self.db.devices.find_one({"api_key": api_key, "status": "active"})
        if not device:
            return None
        
        device = self._object_id_to_str(device)
        return DeviceCredentials(**device)
    
    async def list_devices(self, company_id: Optional[str] = None) -> List[DeviceCredentials]:
        """List devices, optionally filtered by company"""
        self._ensure_connected()
        
        query = {"status": {"$ne": "deleted"}}
        if company_id:
            query["company_id"] = company_id
        
        cursor = self.db.devices.find(query).sort("created_at", -1)
        devices = []
        
        async for device_doc in cursor:
            device_doc = self._object_id_to_str(device_doc)
            devices.append(DeviceCredentials(**device_doc))
        
        return devices
    
    async def update_device_last_seen(self, api_key: str):
        """Update device last seen timestamp"""
        self._ensure_connected()
        
        await self.db.devices.update_one(
            {"api_key": api_key},
            {"$set": {"last_seen": datetime.utcnow()}}
        )
    
    # ================================
    # AUTHENTICATION HELPERS
    # ================================
    
    async def check_user_permission(
        self,
        user_id: str,
        permission: str
    ) -> bool:
        """Check if user has a specific permission"""
        self._ensure_connected()
        
        user_profile = await self.get_user_profile(user_id)
        if not user_profile:
            return False
        
        # Super users have all permissions
        if user_profile.user_type == UserType.SUPER_USER:
            return True
        
        return permission in user_profile.permissions
    
    async def check_company_access(
        self,
        user_id: str,
        company_id: str
    ) -> bool:
        """Check if user has access to a company's data"""
        self._ensure_connected()
        
        user_profile = await self.get_user_profile(user_id)
        if not user_profile:
            return False
        
        # Super users can access all companies
        if user_profile.user_type == UserType.SUPER_USER:
            return True
        
        # Company users can only access their own company
        return user_profile.company_id == company_id


# Global database service instance
db_service = DatabaseService()