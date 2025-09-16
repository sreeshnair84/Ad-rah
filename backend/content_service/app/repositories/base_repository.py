# Copyright (c) 2025 Adara Screen by Hebron
# Owner: Sujesh M S
# All Rights Reserved
#
# This software is proprietary to Adara Screen by Hebron.
# Unauthorized use, reproduction, or distribution is strictly prohibited.

"""
Base Repository Pattern

This module provides the foundation for all domain-specific repositories,
implementing common database operations and patterns.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime
from bson import ObjectId
import uuid
import logging

logger = logging.getLogger(__name__)


class BaseRepository(ABC):
    """Abstract base repository with common database operations"""

    def __init__(self, db_service):
        self.db_service = db_service
        self.logger = logging.getLogger(self.__class__.__name__)

    @property
    @abstractmethod
    def collection_name(self) -> str:
        """Return the MongoDB collection name for this repository"""
        pass

    @property
    def collection(self):
        """Get the MongoDB collection"""
        return self.db_service.db[self.collection_name]

    def _object_id_to_str(self, doc: Optional[Dict]) -> Optional[Dict]:
        """Convert MongoDB ObjectId to string for JSON serialization"""
        if not doc:
            return None

        if "_id" in doc:
            doc["_id"] = str(doc["_id"])

        return doc

    def _generate_id(self) -> str:
        """Generate a new UUID for document ID"""
        return str(uuid.uuid4())

    async def create(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new document"""
        try:
            # Add ID and timestamps if not present
            if "id" not in data:
                data["id"] = self._generate_id()

            if "created_at" not in data:
                data["created_at"] = datetime.utcnow()

            if "updated_at" not in data:
                data["updated_at"] = datetime.utcnow()

            # Insert document
            result = await self.collection.insert_one(data)
            data["_id"] = result.inserted_id

            self.logger.info(f"Created document in {self.collection_name}: {data['id']}")
            return self._object_id_to_str(data)

        except Exception as e:
            self.logger.error(f"Failed to create document in {self.collection_name}: {e}")
            raise

    async def get_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get document by ID"""
        try:
            # Try by id field first
            doc = await self.collection.find_one({"id": doc_id})

            # Fallback to _id field if needed
            if not doc:
                try:
                    doc = await self.collection.find_one({"_id": ObjectId(doc_id)})
                except:
                    pass

            return self._object_id_to_str(doc)

        except Exception as e:
            self.logger.error(f"Failed to get document by ID {doc_id} from {self.collection_name}: {e}")
            return None

    async def get_by_field(self, field: str, value: Any) -> Optional[Dict[str, Any]]:
        """Get document by a specific field"""
        try:
            doc = await self.collection.find_one({field: value})
            return self._object_id_to_str(doc)

        except Exception as e:
            self.logger.error(f"Failed to get document by {field}={value} from {self.collection_name}: {e}")
            return None

    async def list_all(self, filters: Optional[Dict] = None,
                      limit: Optional[int] = None,
                      offset: int = 0,
                      sort_field: str = "created_at",
                      sort_direction: int = -1) -> List[Dict[str, Any]]:
        """List documents with optional filtering and pagination"""
        try:
            query = filters or {}
            cursor = self.collection.find(query).sort(sort_field, sort_direction)

            if offset > 0:
                cursor = cursor.skip(offset)

            if limit:
                cursor = cursor.limit(limit)

            docs = []
            async for doc in cursor:
                docs.append(self._object_id_to_str(doc))

            return docs

        except Exception as e:
            self.logger.error(f"Failed to list documents from {self.collection_name}: {e}")
            return []

    async def list_by_company(self, company_id: str,
                             filters: Optional[Dict] = None,
                             limit: Optional[int] = None,
                             offset: int = 0) -> List[Dict[str, Any]]:
        """List documents filtered by company ID"""
        query = {"company_id": company_id}
        if filters:
            query.update(filters)

        return await self.list_all(query, limit, offset)

    async def update_by_id(self, doc_id: str, update_data: Dict[str, Any]) -> bool:
        """Update document by ID"""
        try:
            # Add update timestamp
            update_data["updated_at"] = datetime.utcnow()

            # Try updating by id field first
            result = await self.collection.update_one(
                {"id": doc_id},
                {"$set": update_data}
            )

            # Fallback to _id field if needed
            if result.matched_count == 0:
                try:
                    result = await self.collection.update_one(
                        {"_id": ObjectId(doc_id)},
                        {"$set": update_data}
                    )
                except:
                    pass

            success = result.matched_count > 0
            if success:
                self.logger.info(f"Updated document {doc_id} in {self.collection_name}")
            else:
                self.logger.warning(f"No document found with ID {doc_id} in {self.collection_name}")

            return success

        except Exception as e:
            self.logger.error(f"Failed to update document {doc_id} in {self.collection_name}: {e}")
            return False

    async def delete_by_id(self, doc_id: str, soft_delete: bool = True) -> bool:
        """Delete document by ID (soft delete by default)"""
        try:
            if soft_delete:
                # Soft delete - just mark as deleted
                return await self.update_by_id(doc_id, {
                    "is_deleted": True,
                    "deleted_at": datetime.utcnow()
                })
            else:
                # Hard delete
                result = await self.collection.delete_one({"id": doc_id})

                if result.deleted_count == 0:
                    try:
                        result = await self.collection.delete_one({"_id": ObjectId(doc_id)})
                    except:
                        pass

                success = result.deleted_count > 0
                if success:
                    self.logger.info(f"Deleted document {doc_id} from {self.collection_name}")

                return success

        except Exception as e:
            self.logger.error(f"Failed to delete document {doc_id} from {self.collection_name}: {e}")
            return False

    async def count(self, filters: Optional[Dict] = None) -> int:
        """Count documents matching filters"""
        try:
            query = filters or {}
            return await self.collection.count_documents(query)

        except Exception as e:
            self.logger.error(f"Failed to count documents in {self.collection_name}: {e}")
            return 0

    async def exists(self, doc_id: str) -> bool:
        """Check if document exists by ID"""
        return await self.get_by_id(doc_id) is not None

    async def find_by_query(self, query: Dict[str, Any],
                           limit: Optional[int] = None,
                           sort: Optional[List] = None) -> List[Dict[str, Any]]:
        """Find documents by custom query"""
        try:
            cursor = self.collection.find(query)

            if sort:
                cursor = cursor.sort(sort)

            if limit:
                cursor = cursor.limit(limit)

            docs = []
            async for doc in cursor:
                docs.append(self._object_id_to_str(doc))

            return docs

        except Exception as e:
            self.logger.error(f"Failed to find documents in {self.collection_name}: {e}")
            return []

    async def aggregate(self, pipeline: List[Dict]) -> List[Dict[str, Any]]:
        """Run aggregation pipeline"""
        try:
            cursor = self.collection.aggregate(pipeline)

            docs = []
            async for doc in cursor:
                docs.append(self._object_id_to_str(doc))

            return docs

        except Exception as e:
            self.logger.error(f"Failed to run aggregation in {self.collection_name}: {e}")
            return []