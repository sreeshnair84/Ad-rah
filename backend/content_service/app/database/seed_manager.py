# Database Seed Manager
# Universal seed data system that works across all database providers

import logging
import secrets
import string
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .base import IDatabaseService, DatabaseResult, QueryFilter, FilterOperation
from app.rbac.permissions import Role, PermissionManager, DEFAULT_ROLE_TEMPLATES

logger = logging.getLogger(__name__)

class SeedManager:
    """Universal seed data management for different database providers"""
    
    def __init__(self, db_service: IDatabaseService):
        self.db = db_service
        self.provider = db_service.provider
    
    async def seed_all_data(self, include_demo: bool = True) -> DatabaseResult:
        """Seed all essential and demo data"""
        try:
            logger.info(f"🌱 Seeding database with {self.provider.value}")
            
            results = []
            
            # 1. Seed permission templates
            result = await self.seed_permission_templates()
            results.append(("permission_templates", result))
            
            # 2. Seed system companies
            result = await self.seed_companies()
            results.append(("companies", result))
            
            # 3. Seed system users
            result = await self.seed_users()
            results.append(("users", result))
            
            # 4. Seed user roles
            result = await self.seed_user_roles()
            results.append(("user_roles", result))
            
            if include_demo:
                # 5. Seed demo content
                result = await self.seed_demo_content()
                results.append(("demo_content", result))
                
                # 6. Seed demo devices
                result = await self.seed_demo_devices()
                results.append(("demo_devices", result))
            
            # Summary
            success_count = sum(1 for _, r in results if r.success)
            total_count = len(results)
            
            logger.info(f"🌱 Seeding complete: {success_count}/{total_count} operations successful")
            
            return DatabaseResult(
                success=success_count == total_count,
                data={
                    "provider": self.provider.value,
                    "operations": total_count,
                    "successful": success_count,
                    "results": {name: r.success for name, r in results}
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Seeding failed: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def seed_permission_templates(self) -> DatabaseResult:
        """Seed default permission templates"""
        try:
            logger.info("🔐 Seeding permission templates...")
            
            created_count = 0
            
            for role, template in DEFAULT_ROLE_TEMPLATES.items():
                # Check if template already exists
                filters = [
                    QueryFilter("role", FilterOperation.EQUALS, role.value),
                    QueryFilter("is_system", FilterOperation.EQUALS, True)
                ]
                
                existing = await self.db.find_one_record("permission_templates", filters)
                if existing.success:
                    logger.debug(f"📋 Template for {role.value} already exists")
                    continue
                
                # Create template
                template_data = {
                    "name": f"Default {template.name}",
                    "role": role.value,
                    "permissions": PermissionManager.serialize_permissions(template.page_permissions),
                    "description": template.description,
                    "is_system": True,
                    "company_id": None
                }
                
                result = await self.db.create_record("permission_templates", template_data)
                if result.success:
                    created_count += 1
                    logger.info(f"✅ Created permission template: {role.value}")
                else:
                    logger.error(f"❌ Failed to create template {role.value}: {result.error}")
            
            return DatabaseResult(
                success=True,
                data={"created": created_count, "total_templates": len(DEFAULT_ROLE_TEMPLATES)}
            )
            
        except Exception as e:
            logger.error(f"Error seeding permission templates: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def seed_companies(self) -> DatabaseResult:
        """Seed system and demo companies"""
        try:
            logger.info("🏢 Seeding companies...")
            
            companies = [
                {
                    "name": "System Administration",
                    "company_type": "HOST",
                    "organization_code": "ORG-SYSTEM",
                    "business_license": "SYS-2024-001",
                    "email": "admin@system.local",
                    "phone": "+1-555-0100",
                    "address": "1 System Drive",
                    "city": "System City",
                    "country": "System",
                    "website": "https://system.local",
                    "description": "System administration company",
                    "status": "active",
                    "settings": {
                        "allow_content_sharing": True,
                        "max_shared_companies": 100,
                        "require_approval_for_sharing": False
                    },
                    "limits": {
                        "max_users": 1000,
                        "max_devices": 1000,
                        "max_content_size_mb": 10240
                    }
                },
                {
                    "name": "TechCorp Solutions",
                    "company_type": "HOST",
                    "organization_code": "ORG-TC001",
                    "business_license": "TC-2024-001",
                    "email": "contact@techcorp.com",
                    "phone": "+1-555-0101",
                    "address": "123 Tech Street",
                    "city": "San Francisco",
                    "country": "United States",
                    "website": "https://techcorp.com",
                    "description": "Technology solutions company with digital signage network",
                    "status": "active",
                    "settings": {
                        "allow_content_sharing": True,
                        "max_shared_companies": 10,
                        "require_approval_for_sharing": True
                    },
                    "limits": {
                        "max_users": 50,
                        "max_devices": 100,
                        "max_content_size_mb": 1024
                    }
                },
                {
                    "name": "Creative Ads Inc",
                    "company_type": "ADVERTISER",
                    "organization_code": "ORG-CA001", 
                    "business_license": "CA-2024-001",
                    "email": "hello@creativeads.com",
                    "phone": "+1-555-0102",
                    "address": "456 Creative Avenue",
                    "city": "New York",
                    "country": "United States", 
                    "website": "https://creativeads.com",
                    "description": "Creative advertising agency specializing in digital content",
                    "status": "active",
                    "settings": {
                        "allow_content_sharing": True,
                        "max_shared_companies": 20,
                        "require_approval_for_sharing": True
                    },
                    "limits": {
                        "max_users": 25,
                        "max_devices": 0,  # Advertisers don't own devices
                        "max_content_size_mb": 2048
                    }
                }
            ]
            
            created_count = 0
            company_ids = {}
            
            for company_data in companies:
                # Check if company exists
                filters = [QueryFilter("organization_code", FilterOperation.EQUALS, company_data["organization_code"])]
                existing = await self.db.find_one_record("companies", filters)
                
                if existing.success:
                    logger.debug(f"🏢 Company {company_data['name']} already exists")
                    company_ids[company_data["organization_code"]] = existing.data["id"]
                    continue
                
                # Create company
                result = await self.db.create_record("companies", company_data)
                if result.success:
                    created_count += 1
                    company_ids[company_data["organization_code"]] = result.data["id"]
                    logger.info(f"✅ Created company: {company_data['name']}")
                else:
                    logger.error(f"❌ Failed to create company {company_data['name']}: {result.error}")
            
            # Store company IDs for later use
            self._company_ids = company_ids
            
            return DatabaseResult(
                success=True,
                data={
                    "created": created_count,
                    "total_companies": len(companies),
                    "company_ids": company_ids
                }
            )
            
        except Exception as e:
            logger.error(f"Error seeding companies: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def seed_users(self) -> DatabaseResult:
        """Seed system and demo users"""
        try:
            logger.info("👤 Seeding users...")
            
            # Ensure we have company IDs
            if not hasattr(self, '_company_ids'):
                # Get company IDs
                self._company_ids = {}
                for org_code in ["ORG-SYSTEM", "ORG-TC001", "ORG-CA001"]:
                    filters = [QueryFilter("organization_code", FilterOperation.EQUALS, org_code)]
                    result = await self.db.find_one_record("companies", filters)
                    if result.success:
                        self._company_ids[org_code] = result.data["id"]
            
            users = [
                {
                    "name": "Super Administrator",
                    "email": "admin@openkiosk.com",
                    "phone": "+1-555-0001",
                    "hashed_password": self._hash_password("adminpass123"),
                    "user_type": "SUPER_USER",
                    "status": "active",
                    "email_verified": True,
                    "login_count": 0
                },
                {
                    "name": "John Smith",
                    "email": "john.smith@techcorp.com", 
                    "phone": "+1-555-0201",
                    "hashed_password": self._hash_password("hostpass123"),
                    "user_type": "COMPANY_USER",
                    "status": "active",
                    "email_verified": True,
                    "login_count": 0
                },
                {
                    "name": "Sarah Johnson",
                    "email": "sarah.johnson@techcorp.com",
                    "phone": "+1-555-0202", 
                    "hashed_password": self._hash_password("hostpass123"),
                    "user_type": "COMPANY_USER",
                    "status": "active",
                    "email_verified": True,
                    "login_count": 0
                },
                {
                    "name": "Mike Chen",
                    "email": "mike.chen@creativeads.com",
                    "phone": "+1-555-0301",
                    "hashed_password": self._hash_password("advertiserpass123"),
                    "user_type": "COMPANY_USER", 
                    "status": "active",
                    "email_verified": True,
                    "login_count": 0
                },
                {
                    "name": "Emily Davis",
                    "email": "emily.davis@creativeads.com",
                    "phone": "+1-555-0302",
                    "hashed_password": self._hash_password("advertiserpass123"),
                    "user_type": "COMPANY_USER",
                    "status": "active", 
                    "email_verified": True,
                    "login_count": 0
                }
            ]
            
            created_count = 0
            user_ids = {}
            
            for user_data in users:
                # Check if user exists
                filters = [QueryFilter("email", FilterOperation.EQUALS, user_data["email"])]
                existing = await self.db.find_one_record("users", filters)
                
                if existing.success:
                    logger.debug(f"👤 User {user_data['email']} already exists")
                    user_ids[user_data["email"]] = existing.data["id"]
                    continue
                
                # Create user
                result = await self.db.create_record("users", user_data)
                if result.success:
                    created_count += 1
                    user_ids[user_data["email"]] = result.data["id"]
                    logger.info(f"✅ Created user: {user_data['name']} ({user_data['email']})")
                else:
                    logger.error(f"❌ Failed to create user {user_data['email']}: {result.error}")
            
            # Store user IDs for role assignment
            self._user_ids = user_ids
            
            return DatabaseResult(
                success=True,
                data={
                    "created": created_count,
                    "total_users": len(users),
                    "user_ids": user_ids
                }
            )
            
        except Exception as e:
            logger.error(f"Error seeding users: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def seed_user_roles(self) -> DatabaseResult:
        """Seed user role assignments"""
        try:
            logger.info("🔐 Seeding user roles...")
            
            # Ensure we have IDs
            if not hasattr(self, '_user_ids') or not hasattr(self, '_company_ids'):
                logger.error("Missing user or company IDs - run seed_users and seed_companies first")
                return DatabaseResult(success=False, error="Missing dependencies")
            
            # Get permission templates
            templates = {}
            for role in Role:
                filters = [
                    QueryFilter("role", FilterOperation.EQUALS, role.value),
                    QueryFilter("is_system", FilterOperation.EQUALS, True)
                ]
                result = await self.db.find_one_record("permission_templates", filters)
                if result.success:
                    templates[role.value] = result.data["permissions"]
            
            role_assignments = [
                # Super Admin
                {
                    "user_email": "admin@openkiosk.com",
                    "company_id": None,  # Global
                    "role": Role.SUPER_ADMIN.value,
                    "is_primary": True
                },
                # TechCorp Host Company
                {
                    "user_email": "john.smith@techcorp.com",
                    "company_id": self._company_ids["ORG-TC001"],
                    "role": Role.COMPANY_ADMIN.value,
                    "is_primary": True
                },
                {
                    "user_email": "sarah.johnson@techcorp.com",
                    "company_id": self._company_ids["ORG-TC001"], 
                    "role": Role.CONTENT_MANAGER.value,
                    "is_primary": True
                },
                # Creative Ads Advertiser Company
                {
                    "user_email": "mike.chen@creativeads.com",
                    "company_id": self._company_ids["ORG-CA001"],
                    "role": Role.COMPANY_ADMIN.value,
                    "is_primary": True
                },
                {
                    "user_email": "emily.davis@creativeads.com", 
                    "company_id": self._company_ids["ORG-CA001"],
                    "role": Role.EDITOR.value,
                    "is_primary": True
                }
            ]
            
            created_count = 0
            
            for assignment in role_assignments:
                user_id = self._user_ids.get(assignment["user_email"])
                if not user_id:
                    logger.warning(f"⚠️ User not found: {assignment['user_email']}")
                    continue
                
                # Check if role assignment exists
                filters = [
                    QueryFilter("user_id", FilterOperation.EQUALS, user_id),
                    QueryFilter("role", FilterOperation.EQUALS, assignment["role"])
                ]
                
                if assignment["company_id"]:
                    filters.append(QueryFilter("company_id", FilterOperation.EQUALS, assignment["company_id"]))
                else:
                    filters.append(QueryFilter("company_id", FilterOperation.IS_NULL))
                
                existing = await self.db.find_one_record("user_company_roles", filters)
                if existing.success:
                    logger.debug(f"🔐 Role {assignment['role']} already assigned to {assignment['user_email']}")
                    continue
                
                # Create role assignment
                role_data = {
                    "user_id": user_id,
                    "company_id": assignment["company_id"],
                    "role": assignment["role"],
                    "permissions": templates.get(assignment["role"], "[]"),
                    "is_primary": assignment["is_primary"],
                    "status": "active"
                }
                
                result = await self.db.create_record("user_company_roles", role_data)
                if result.success:
                    created_count += 1
                    logger.info(f"✅ Assigned {assignment['role']} to {assignment['user_email']}")
                else:
                    logger.error(f"❌ Failed to assign role: {result.error}")
            
            return DatabaseResult(
                success=True,
                data={
                    "created": created_count,
                    "total_assignments": len(role_assignments)
                }
            )
            
        except Exception as e:
            logger.error(f"Error seeding user roles: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def seed_demo_content(self) -> DatabaseResult:
        """Seed demo content"""
        try:
            logger.info("📁 Seeding demo content...")
            
            if not hasattr(self, '_user_ids') or not hasattr(self, '_company_ids'):
                return DatabaseResult(success=False, error="Missing dependencies")
            
            demo_content = [
                {
                    "title": "Welcome to TechCorp",
                    "description": "Company welcome message for lobby display",
                    "filename": "welcome-techcorp.jpg",
                    "file_path": "/demo/images/welcome-techcorp.jpg",
                    "file_size": 2048000,
                    "content_type": "image/jpeg",
                    "file_hash": "abc123def456",
                    "owner_id": self._user_ids.get("john.smith@techcorp.com"),
                    "company_id": self._company_ids["ORG-TC001"],
                    "status": "approved",
                    "duration_seconds": 10,
                    "categories": ["corporate", "welcome"],
                    "tags": ["lobby", "welcome", "corporate"]
                },
                {
                    "title": "Product Showcase Video",
                    "description": "Latest product demonstration video",
                    "filename": "product-demo.mp4",
                    "file_path": "/demo/videos/product-demo.mp4",
                    "file_size": 15360000,
                    "content_type": "video/mp4",
                    "file_hash": "def456ghi789",
                    "owner_id": self._user_ids.get("emily.davis@creativeads.com"),
                    "company_id": self._company_ids["ORG-CA001"],
                    "status": "approved", 
                    "duration_seconds": 45,
                    "categories": ["marketing", "product"],
                    "tags": ["demo", "product", "video"]
                }
            ]
            
            created_count = 0
            
            for content_data in demo_content:
                if not content_data["owner_id"]:
                    continue
                
                # Check if content exists
                filters = [
                    QueryFilter("title", FilterOperation.EQUALS, content_data["title"]),
                    QueryFilter("owner_id", FilterOperation.EQUALS, content_data["owner_id"])
                ]
                existing = await self.db.find_one_record("content", filters)
                
                if existing.success:
                    logger.debug(f"📁 Content '{content_data['title']}' already exists")
                    continue
                
                result = await self.db.create_record("content", content_data)
                if result.success:
                    created_count += 1
                    logger.info(f"✅ Created demo content: {content_data['title']}")
                else:
                    logger.error(f"❌ Failed to create content: {result.error}")
            
            return DatabaseResult(
                success=True,
                data={
                    "created": created_count,
                    "total_content": len(demo_content)
                }
            )
            
        except Exception as e:
            logger.error(f"Error seeding demo content: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def seed_demo_devices(self) -> DatabaseResult:
        """Seed demo devices"""
        try:
            logger.info("📺 Seeding demo devices...")
            
            if not hasattr(self, '_company_ids'):
                return DatabaseResult(success=False, error="Missing company IDs")
            
            demo_devices = [
                {
                    "name": "Lobby Display - Main",
                    "device_type": "indoor_screen", 
                    "company_id": self._company_ids["ORG-TC001"],
                    "location": "Main Lobby, 1st Floor",
                    "api_key": self._generate_api_key(),
                    "screen_config": {
                        "resolution_width": 1920,
                        "resolution_height": 1080,
                        "orientation": "landscape",
                        "aspect_ratio": "16:9"
                    },
                    "capabilities": {
                        "max_resolution_width": 1920,
                        "max_resolution_height": 1080,
                        "supported_formats": ["jpg", "png", "mp4", "webp"],
                        "has_touch": False,
                        "has_audio": True,
                        "storage_gb": 32
                    },
                    "status": "active"
                },
                {
                    "name": "Conference Room Display", 
                    "device_type": "interactive_display",
                    "company_id": self._company_ids["ORG-TC001"],
                    "location": "Conference Room A, 2nd Floor",
                    "api_key": self._generate_api_key(),
                    "screen_config": {
                        "resolution_width": 1920,
                        "resolution_height": 1080,
                        "orientation": "landscape",
                        "aspect_ratio": "16:9"
                    },
                    "capabilities": {
                        "max_resolution_width": 1920,
                        "max_resolution_height": 1080,
                        "supported_formats": ["jpg", "png", "mp4", "webp"],
                        "has_touch": True,
                        "has_audio": True,
                        "storage_gb": 64
                    },
                    "status": "active"
                }
            ]
            
            created_count = 0
            
            for device_data in demo_devices:
                # Check if device exists
                filters = [
                    QueryFilter("name", FilterOperation.EQUALS, device_data["name"]),
                    QueryFilter("company_id", FilterOperation.EQUALS, device_data["company_id"])
                ]
                existing = await self.db.find_one_record("devices", filters)
                
                if existing.success:
                    logger.debug(f"📺 Device '{device_data['name']}' already exists")
                    continue
                
                result = await self.db.create_record("devices", device_data)
                if result.success:
                    created_count += 1
                    logger.info(f"✅ Created demo device: {device_data['name']}")
                else:
                    logger.error(f"❌ Failed to create device: {result.error}")
            
            return DatabaseResult(
                success=True,
                data={
                    "created": created_count,
                    "total_devices": len(demo_devices)
                }
            )
            
        except Exception as e:
            logger.error(f"Error seeding demo devices: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def clear_all_data(self) -> DatabaseResult:
        """Clear all data from all tables (use with caution!)"""
        try:
            logger.warning("🚨 CLEARING ALL DATA - THIS WILL DELETE EVERYTHING!")
            
            from .schemas import get_all_table_names
            
            results = []
            
            # Clear tables in reverse dependency order  
            table_order = ["analytics_events", "audit_log", "content_schedule", "devices", 
                          "content", "user_company_roles", "permission_templates", "users", "companies"]
            
            for table_name in table_order:
                try:
                    # Get all records
                    all_records = await self.db.list_records(table_name)
                    if all_records.success and all_records.data:
                        record_ids = [record["id"] for record in all_records.data]
                        if record_ids:
                            result = await self.db.batch_delete(table_name, record_ids)
                            if result.success:
                                logger.info(f"🗑️ Cleared table: {table_name} ({len(record_ids)} records)")
                                results.append((table_name, len(record_ids), True))
                            else:
                                logger.error(f"❌ Failed to clear {table_name}: {result.error}")
                                results.append((table_name, 0, False))
                        else:
                            results.append((table_name, 0, True))
                    else:
                        results.append((table_name, 0, True))
                        
                except Exception as e:
                    logger.error(f"Error clearing {table_name}: {e}")
                    results.append((table_name, 0, False))
            
            total_deleted = sum(count for _, count, success in results if success)
            
            return DatabaseResult(
                success=True,
                data={
                    "tables_cleared": len([r for r in results if r[2]]),
                    "total_records_deleted": total_deleted,
                    "results": results
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Clear all data failed: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    def _hash_password(self, password: str) -> str:
        """Hash password using consistent method"""
        import hashlib
        import secrets
        
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"
    
    def _generate_api_key(self) -> str:
        """Generate secure API key for devices"""
        return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))