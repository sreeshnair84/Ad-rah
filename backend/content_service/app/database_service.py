# Copyright (c) 2025 Adara Screen by Hebron
# Owner: Sujesh M S
# All Rights Reserved
#
# This software is proprietary to Adara Screen by Hebron.
# Unauthorized use, reproduction, or distribution is strictly prohibited.

# Clean Database Service
import logging
import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo.errors import DuplicateKeyError
from app.config import settings
from app.rbac_models import *

logger = logging.getLogger(__name__)

class DatabaseService:
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[Any] = None
        self.connected = False
    
    async def initialize(self) -> bool:
        if not settings.MONGO_URI:
            raise ValueError("MONGO_URI environment variable is required")
        
        try:
            self.client = AsyncIOMotorClient(settings.MONGO_URI, maxPoolSize=10)
            await self.client.admin.command('ping')
            try:
                self.db = self.client.get_default_database()
            except:
                self.db = self.client.openkiosk
            await self._create_indexes()
            self.connected = True
            logger.info("✅ MongoDB connection established")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB: {e}")
            raise ConnectionError(f"Database connection failed: {e}")
    
    async def close(self):
        if self.client:
            self.client.close()
            self.connected = False
    
    async def _create_indexes(self):
        try:
            await self.db.users.create_index("email", unique=True)
            await self.db.users.create_index([("company_id", 1), ("user_type", 1)])
            await self.db.companies.create_index("organization_code", unique=True)
            await self.db.companies.create_index("registration_key", unique=True)
            await self.db.devices.create_index("api_key", unique=True)
            logger.info("📊 Database indexes created")
        except Exception as e:
            logger.warning(f"⚠️ Failed to create some indexes: {e}")
    
    def _object_id_to_str(self, doc: Dict) -> Dict:
        if doc and "_id" in doc:
            doc["id"] = str(doc["_id"])
            del doc["_id"]
        return doc
    
    async def create_user(self, user_data: UserCreate, hashed_password: str) -> User:
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
            "permissions": [],
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
            return User(**user_doc)
        except DuplicateKeyError:
            raise ValueError(f"User with email {user_data.email} already exists")
    
    async def get_user_by_email(self, email: str) -> Optional[Dict]:
        user = await self.db.users.find_one({"email": email, "is_active": True})
        return self._object_id_to_str(user) if user else None
    
    async def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        # First try querying by id field (from JWT token)
        user = await self.db.users.find_one({"id": user_id, "is_active": True})
        
        # Fallback: try querying by MongoDB _id in case it's provided
        if not user:
            try:
                from bson import ObjectId
                user = await self.db.users.find_one({"_id": ObjectId(user_id), "is_active": True})
            except:
                pass  # Invalid ObjectId format
                
        if not user:
            return None
        
        user = self._object_id_to_str(user)
        
        # Get company data
        company = None
        if user.get("company_id"):
            # Try by id field first (standard approach)
            company_doc = await self.db.companies.find_one({"id": user["company_id"]})
            # Fallback to _id field
            if not company_doc:
                company_doc = await self.db.companies.find_one({"_id": user["company_id"]})
            if company_doc:
                company_doc = self._object_id_to_str(company_doc)
                company = Company(**company_doc)  # Convert to Company object
        
        # Compute permissions
        user_type = UserType(user["user_type"])
        company_type = CompanyType(company.company_type) if company else None
        company_role = CompanyRole(user["company_role"]) if user.get("company_role") else None
        
        permissions = get_permissions_for_role(user_type, company_type, company_role)
        permission_strings = [p.value for p in permissions]
        
        # Navigation access - comprehensive for super users, permission-based for others
        if user_type == UserType.SUPER_USER:
            # Super users get access to ALL pages across all company types
            accessible_navigation = [
                # Overview
                "dashboard", "unified",
                # User Management
                "users", "roles", "registration",
                # Content Management (all types)
                "content", "my-content", "my-ads", "upload", "moderation", 
                "ads-approval", "host-review", "content-overlay",
                # Device Management (all HOST features)
                "kiosks", "device-keys", "digital-twin",
                # Analytics & Reports  
                "analytics", "analytics/real-time", "performance",
                # Scheduling & Planning
                "schedules", 
                # System & Admin
                "settings", "master-data", "billing"
            ]
        else:
            # Company users get permission and role-based access
            accessible_navigation = []
            
            # Basic navigation items available to all authenticated users
            if "dashboard_view" in permission_strings:
                accessible_navigation.append("dashboard")
            
            # User management - only ADMIN and SUPER_USER can access user/role screens
            if "user_read" in permission_strings and (user_type == UserType.SUPER_USER or company_role == CompanyRole.ADMIN):
                accessible_navigation.append("users")
                # Only super users can manage roles
                if user_type == UserType.SUPER_USER:
                    accessible_navigation.append("roles")
            # Company registration is ONLY for super users
            if "user_create" in permission_strings and user_type == UserType.SUPER_USER:
                accessible_navigation.append("registration")
            
            # Content management
            if "content_read" in permission_strings:
                accessible_navigation.extend(["content", "my-content"])
            if "content_upload" in permission_strings:
                accessible_navigation.append("upload")
            if "content_moderate" in permission_strings:
                accessible_navigation.append("moderation")
            if "content_approve" in permission_strings:
                accessible_navigation.extend(["ads-approval", "host-review"])
            if "content_update" in permission_strings:
                accessible_navigation.extend(["content-overlay", "schedules"])
            
            # Company type specific features
            if company_type == CompanyType.HOST:
                # Device management for HOST companies
                if "device_read" in permission_strings:
                    accessible_navigation.append("kiosks")
                if "device_register" in permission_strings:
                    accessible_navigation.append("device-keys")
                if "device_monitor" in permission_strings:
                    accessible_navigation.append("digital-twin")
            elif company_type == CompanyType.ADVERTISER:
                # Advertiser-specific features
                if "content_read" in permission_strings:
                    accessible_navigation.append("my-ads")
            
            # Analytics
            if "analytics_read" in permission_strings:
                accessible_navigation.extend(["analytics", "analytics/real-time"])
            if "analytics_reports" in permission_strings:
                accessible_navigation.append("performance")
            
            # Settings and admin
            if "settings_read" in permission_strings:
                accessible_navigation.append("settings")
            if company_role == CompanyRole.ADMIN:
                accessible_navigation.append("billing")
        
        # Remove duplicates while preserving order
        accessible_navigation = list(dict.fromkeys(accessible_navigation))
        
        # Display helpers
        display_name = f"{user.get('first_name', '')} {user.get('last_name', '')}".strip()
        if not display_name:
            display_name = user.get('email', 'Unknown User')
        
        role_display = "Super User" if user_type == UserType.SUPER_USER else (
            company_role.value.title() if company_role else "User"
        )
        
        profile_data = {
            **user,
            "permissions": permission_strings,
            "company": company.model_dump() if company else None,
            "accessible_navigation": accessible_navigation,
            "display_name": display_name,
            "role_display": role_display
        }
        
        return UserProfile(**profile_data)
    
    async def create_company(self, company_data) -> Company:
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
        
        result = await self.db.companies.insert_one(company_doc)
        company_doc["_id"] = result.inserted_id
        company_doc = self._object_id_to_str(company_doc)
        return Company(**company_doc)
    
    async def get_company(self, company_id: str) -> Optional[Company]:
        company = await self.db.companies.find_one({"_id": company_id})
        if not company:
            return None
        company = self._object_id_to_str(company)
        return Company(**company)
    
    async def list_companies(self) -> List[Company]:
        cursor = self.db.companies.find({"status": "active"}).sort("created_at", -1)
        companies = []
        async for company_doc in cursor:
            company_doc = self._object_id_to_str(company_doc)
            companies.append(Company(**company_doc))
        return companies
    
    async def update_user_login(self, user_id: str):
        await self.db.users.update_one(
            {"id": user_id},
            {"$set": {"last_login": datetime.utcnow()}}
        )
    
    async def list_all_users(self) -> List[UserProfile]:
        cursor = self.db.users.find({"is_active": True}).sort("created_at", -1)
        users = []
        async for user_doc in cursor:
            user_doc = self._object_id_to_str(user_doc)
            user_profile = await self.get_user_profile(user_doc["id"])
            if user_profile:
                users.append(user_profile)
        return users
    
    async def list_users_by_company(self, company_id: str) -> List[UserProfile]:
        cursor = self.db.users.find({"company_id": company_id, "is_active": True}).sort("created_at", -1)
        users = []
        async for user_doc in cursor:
            user_doc = self._object_id_to_str(user_doc)
            user_profile = await self.get_user_profile(user_doc["id"])
            if user_profile:
                users.append(user_profile)
        return users

    # Content History Tracking Methods
    async def create_content_history(self, history_data: Dict) -> Dict:
        """Create a content history event"""
        history_doc = {
            "id": str(uuid.uuid4()),
            **history_data,
            "created_at": datetime.utcnow()
        }

        try:
            result = await self.db.content_history.insert_one(history_doc)
            history_doc["_id"] = result.inserted_id
            return self._object_id_to_str(history_doc)
        except Exception as e:
            logger.error(f"Failed to create content history: {e}")
            raise

    async def find_content_history(
        self,
        filters: Dict,
        limit: int = 100,
        offset: int = 0,
        sort: Optional[List] = None
    ) -> List[Dict]:
        """Find content history events with filtering"""
        try:
            cursor = self.db.content_history.find(filters)

            if sort:
                cursor = cursor.sort(sort)
            else:
                cursor = cursor.sort("event_timestamp", -1)

            cursor = cursor.skip(offset).limit(limit)

            history_events = []
            async for doc in cursor:
                history_events.append(self._object_id_to_str(doc))

            return history_events
        except Exception as e:
            logger.error(f"Failed to find content history: {e}")
            raise

    async def get_content_history_count(self, filters: Dict) -> int:
        """Get count of content history events matching filters"""
        try:
            return await self.db.content_history.count_documents(filters)
        except Exception as e:
            logger.error(f"Failed to count content history: {e}")
            return 0

    async def create_device_history(self, history_data: Dict) -> Dict:
        """Create a device history event"""
        history_doc = {
            "id": str(uuid.uuid4()),
            **history_data,
            "created_at": datetime.utcnow()
        }

        try:
            result = await self.db.device_history.insert_one(history_doc)
            history_doc["_id"] = result.inserted_id
            return self._object_id_to_str(history_doc)
        except Exception as e:
            logger.error(f"Failed to create device history: {e}")
            raise

    async def find_device_history(
        self,
        filters: Dict,
        limit: int = 100,
        offset: int = 0,
        sort: Optional[List] = None
    ) -> List[Dict]:
        """Find device history events with filtering"""
        try:
            cursor = self.db.device_history.find(filters)

            if sort:
                cursor = cursor.sort(sort)
            else:
                cursor = cursor.sort("event_timestamp", -1)

            cursor = cursor.skip(offset).limit(limit)

            history_events = []
            async for doc in cursor:
                history_events.append(self._object_id_to_str(doc))

            return history_events
        except Exception as e:
            logger.error(f"Failed to find device history: {e}")
            raise

    async def create_system_audit_log(self, audit_data: Dict) -> Dict:
        """Create a system audit log entry"""
        audit_doc = {
            "id": str(uuid.uuid4()),
            **audit_data,
            "created_at": datetime.utcnow()
        }

        try:
            result = await self.db.system_audit_log.insert_one(audit_doc)
            audit_doc["_id"] = result.inserted_id
            return self._object_id_to_str(audit_doc)
        except Exception as e:
            logger.error(f"Failed to create system audit log: {e}")
            raise

    async def find_system_audit_logs(
        self,
        filters: Dict,
        limit: int = 100,
        offset: int = 0,
        sort: Optional[List] = None
    ) -> List[Dict]:
        """Find system audit logs with filtering"""
        try:
            cursor = self.db.system_audit_log.find(filters)

            if sort:
                cursor = cursor.sort(sort)
            else:
                cursor = cursor.sort("timestamp", -1)

            cursor = cursor.skip(offset).limit(limit)

            audit_logs = []
            async for doc in cursor:
                audit_logs.append(self._object_id_to_str(doc))

            return audit_logs
        except Exception as e:
            logger.error(f"Failed to find system audit logs: {e}")
            raise

    async def get_content_by_id(self, content_id: str, company_id: str) -> Optional[Dict]:
        """Get content by ID with company scoping"""
        try:
            content = await self.db.content.find_one({
                "id": content_id,
                "company_id": company_id
            })
            return self._object_id_to_str(content) if content else None
        except Exception as e:
            logger.error(f"Failed to get content by ID: {e}")
            return None

    async def get_user_by_id(self, user_id: str) -> Optional[Dict]:
        """Get user by ID"""
        try:
            user = await self.db.users.find_one({"id": user_id, "is_active": True})
            return self._object_id_to_str(user) if user else None
        except Exception as e:
            logger.error(f"Failed to get user by ID: {e}")
            return None

    # Generic database methods for event handlers
    async def get_document(self, collection: str, query: Dict) -> Optional[Dict]:
        """Get a single document from collection"""
        try:
            return await self.db[collection].find_one(query)
        except Exception as e:
            logger.error(f"Failed to get document from {collection}: {e}")
            return None

    async def update_document(self, collection: str, query: Dict, update: Dict, upsert: bool = False):
        """Update a document in collection"""
        try:
            return await self.db[collection].update_one(query, update, upsert=upsert)
        except Exception as e:
            logger.error(f"Failed to update document in {collection}: {e}")
            return None

    async def insert_document(self, collection: str, document: Dict) -> str:
        """Insert a document into collection"""
        try:
            result = await self.db[collection].insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Failed to insert document into {collection}: {e}")
            return None

    async def find_documents(self, collection: str, query: Dict, sort: List = None, limit: int = None) -> List[Dict]:
        """Find multiple documents in collection"""
        try:
            cursor = self.db[collection].find(query)
            if sort:
                cursor = cursor.sort(sort)
            if limit:
                cursor = cursor.limit(limit)
            return await cursor.to_list(length=limit)
        except Exception as e:
            logger.error(f"Failed to find documents in {collection}: {e}")
            return []

    async def insert_many(self, collection: str, documents: List[Dict]) -> List[str]:
        """Insert multiple documents into collection"""
        try:
            result = await self.db[collection].insert_many(documents)
            return [str(id) for id in result.inserted_ids]
        except Exception as e:
            logger.error(f"Failed to insert documents into {collection}: {e}")
            return []

    async def update_many(self, collection: str, query: Dict, update: Dict):
        """Update multiple documents in collection"""
        try:
            return await self.db[collection].update_many(query, update)
        except Exception as e:
            logger.error(f"Failed to update documents in {collection}: {e}")
            return None

    async def delete_many(self, collection: str, query: Dict):
        """Delete multiple documents from collection"""
        try:
            return await self.db[collection].delete_many(query)
        except Exception as e:
            logger.error(f"Failed to delete documents from {collection}: {e}")
            return None

    async def distinct(self, collection: str, field: str, query: Dict = None) -> List:
        """Get distinct values from collection"""
        try:
            return await self.db[collection].distinct(field, query or {})
        except Exception as e:
            logger.error(f"Failed to get distinct values from {collection}: {e}")
            return []

    async def aggregate(self, collection: str, pipeline: List[Dict]) -> List[Dict]:
        """Run aggregation pipeline on collection"""
        try:
            cursor = self.db[collection].aggregate(pipeline)
            return await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Failed to run aggregation on {collection}: {e}")
            return []

# Global instance
db_service = DatabaseService()
