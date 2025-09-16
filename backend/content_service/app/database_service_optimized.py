# Copyright (c) 2025 Adara Screen by Hebron
# Owner: Sujesh M S
# All Rights Reserved
#
# This software is proprietary to Adara Screen by Hebron.
# Unauthorized use, reproduction, or distribution is strictly prohibited.

"""
Optimized Database Service

This is the optimized version of the database service with:
- Consistent ObjectId handling
- Repository pattern integration
- Better error handling and logging
- Performance improvements
- Clean architecture principles
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from bson import ObjectId
import uuid

from .repositories import initialize_repositories, get_repo_manager

logger = logging.getLogger(__name__)


class OptimizedDatabaseService:
    """
    Optimized database service with repository pattern integration

    This service provides:
    - Connection management
    - Repository pattern access
    - Consistent ObjectId handling
    - Performance monitoring
    - Error handling
    """

    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.connected: bool = False
        self._repo_manager = None

    async def initialize(self, mongo_uri: str = None, database_name: str = "adara_digital_signage"):
        """Initialize database connection and repositories"""
        try:
            from .config import settings

            # Use provided URI or fallback to settings
            uri = mongo_uri or settings.MONGO_URI
            if not uri:
                raise ValueError("MongoDB URI not provided")

            # Create client with optimized settings
            self.client = AsyncIOMotorClient(
                uri,
                maxPoolSize=20,
                minPoolSize=5,
                maxIdleTimeMS=30000,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000,
                socketTimeoutMS=20000
            )

            # Get database
            self.db = self.client[database_name]

            # Test connection
            await self.client.admin.command('ping')
            self.connected = True

            # Initialize repositories
            self._repo_manager = initialize_repositories(self)

            # Create indexes for performance
            await self._create_indexes()

            logger.info(f"✅ Database connected successfully to {database_name}")

        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            self.connected = False
            raise

    async def close(self):
        """Close database connection"""
        if self.client:
            self.client.close()
            self.connected = False
            logger.info("🔌 Database connection closed")

    @property
    def repos(self):
        """Get repository manager for domain operations"""
        if not self._repo_manager:
            raise RuntimeError("Database service not initialized")
        return self._repo_manager

    async def _create_indexes(self):
        """Create database indexes for optimal performance"""
        try:
            indexes_created = 0

            # Users collection indexes
            await self.db.users.create_index("email", unique=True)
            await self.db.users.create_index("company_id")
            await self.db.users.create_index([("email", 1), ("is_active", 1)])
            indexes_created += 3

            # Companies collection indexes
            await self.db.companies.create_index("organization_code", unique=True)
            await self.db.companies.create_index("registration_key")
            await self.db.companies.create_index("status")
            indexes_created += 3

            # Content collection indexes
            await self.db.content.create_index([("company_id", 1), ("status", 1)])
            await self.db.content.create_index("owner_id")
            await self.db.content.create_index("uploaded_at")
            indexes_created += 3

            # Devices collection indexes
            await self.db.devices.create_index([("company_id", 1), ("status", 1)])
            await self.db.devices.create_index("registration_key")
            await self.db.devices.create_index("last_seen")
            indexes_created += 3

            # Analytics collection indexes
            await self.db.device_analytics.create_index([("device_id", 1), ("timestamp", 1)])
            await self.db.device_analytics.create_index("company_id")
            await self.db.device_analytics.create_index("event_type")
            indexes_created += 3

            # Heartbeats collection indexes
            await self.db.device_heartbeats.create_index([("device_id", 1), ("timestamp", -1)])
            await self.db.device_heartbeats.create_index("timestamp")  # For cleanup operations
            indexes_created += 2

            # Content history indexes
            await self.db.content_history.create_index([("content_id", 1), ("event_timestamp", -1)])
            await self.db.content_history.create_index("company_id")
            await self.db.content_history.create_index("event_type")
            indexes_created += 3

            # Audit logs indexes
            await self.db.system_audit_log.create_index([("company_id", 1), ("timestamp", -1)])
            await self.db.system_audit_log.create_index("performed_by_user_id")
            await self.db.system_audit_log.create_index("resource_type")
            indexes_created += 3

            logger.info(f"✅ Created {indexes_created} database indexes for optimal performance")

        except Exception as e:
            logger.warning(f"⚠️ Failed to create some database indexes: {e}")

    # Utility methods for backward compatibility and common operations

    def _object_id_to_str(self, doc: Optional[Dict]) -> Optional[Dict]:
        """Convert ObjectId fields to strings consistently"""
        if not doc:
            return None

        # Convert _id to string
        if "_id" in doc and isinstance(doc["_id"], ObjectId):
            doc["_id"] = str(doc["_id"])

        # Handle nested ObjectIds in arrays or subdocuments
        for key, value in doc.items():
            if isinstance(value, ObjectId):
                doc[key] = str(value)
            elif isinstance(value, list):
                doc[key] = [str(item) if isinstance(item, ObjectId) else item for item in value]
            elif isinstance(value, dict):
                doc[key] = self._object_id_to_str(value)

        return doc

    async def get_collection_stats(self) -> Dict[str, Any]:
        """Get database collection statistics"""
        try:
            stats = {}
            collections = ["users", "companies", "content", "devices", "device_analytics"]

            for collection_name in collections:
                collection = self.db[collection_name]
                count = await collection.count_documents({})
                stats[collection_name] = count

            return stats

        except Exception as e:
            logger.error(f"Failed to get collection stats: {e}")
            return {}

    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive database health check"""
        try:
            # Check connection
            await self.client.admin.command('ping')

            # Check database stats
            db_stats = await self.db.command("dbStats")

            # Check index usage (sample from users collection)
            index_stats = await self.db.users.aggregate([{"$indexStats": {}}]).to_list(length=None)

            return {
                "connected": True,
                "database": self.db.name,
                "collections": db_stats.get("collections", 0),
                "dataSize": db_stats.get("dataSize", 0),
                "indexSize": db_stats.get("indexSize", 0),
                "indexes": len(index_stats),
                "status": "healthy"
            }

        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "connected": False,
                "error": str(e),
                "status": "unhealthy"
            }

    # High-level convenience methods that use repositories

    async def create_user_with_company(self, user_data: Dict, company_data: Dict) -> Dict[str, Any]:
        """Create user and company together (transaction-like operation)"""
        try:
            # Create company first
            company = await self.repos.companies.create_company(company_data)

            # Add company_id to user data
            user_data["company_id"] = company.id
            user_data["user_type"] = "COMPANY_USER"

            # Create user
            user = await self.repos.users.create_user(user_data)

            return {
                "user": user.model_dump(),
                "company": company.model_dump(),
                "success": True
            }

        except Exception as e:
            logger.error(f"Failed to create user with company: {e}")
            return {"success": False, "error": str(e)}

    async def get_company_dashboard_data(self, company_id: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data for a company"""
        try:
            # Get data from multiple repositories
            users_count = await self.repos.users.count({"company_id": company_id, "is_active": True})
            content_stats = await self.repos.content.get_content_stats(company_id)
            device_stats = await self.repos.devices.get_device_stats(company_id)
            analytics_summary = await self.repos.device_analytics.get_analytics_summary(company_id)

            return {
                "users": {
                    "total": users_count,
                    "active": users_count  # Assuming all are active
                },
                "content": content_stats,
                "devices": device_stats,
                "analytics": analytics_summary,
                "timestamp": datetime.utcnow()
            }

        except Exception as e:
            logger.error(f"Failed to get dashboard data for company {company_id}: {e}")
            return {}

    async def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """Cleanup old data from various collections"""
        try:
            cleanup_results = {}

            # Cleanup old heartbeats
            heartbeats_cleaned = await self.repos.heartbeats.cleanup_old_heartbeats(days_to_keep // 3)
            cleanup_results["heartbeats"] = heartbeats_cleaned

            # Cleanup old analytics (older than specified days)
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
            analytics_result = await self.db.device_analytics.delete_many({"timestamp": {"$lt": cutoff_date}})
            cleanup_results["analytics"] = analytics_result.deleted_count

            # Cleanup old audit logs
            audit_result = await self.db.system_audit_log.delete_many({"timestamp": {"$lt": cutoff_date}})
            cleanup_results["audit_logs"] = audit_result.deleted_count

            logger.info(f"Data cleanup completed: {cleanup_results}")
            return cleanup_results

        except Exception as e:
            logger.error(f"Failed to cleanup old data: {e}")
            return {}


# Global instance
optimized_db_service = OptimizedDatabaseService()


# Backward compatibility function
async def get_database_service():
    """Get the optimized database service instance"""
    return optimized_db_service