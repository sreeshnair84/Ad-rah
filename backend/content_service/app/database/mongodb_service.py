# MongoDB Database Service Implementation
# Enterprise-grade MongoDB service with connection pooling and error handling

import logging
import asyncio
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from urllib.parse import urlparse
import uuid

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from pymongo import MongoClient
from pymongo.errors import (
    ConnectionFailure, 
    DuplicateKeyError, 
    OperationFailure,
    ServerSelectionTimeoutError,
    NetworkTimeout
)
from bson import ObjectId

from .base import (
    IDatabaseService, 
    DatabaseProvider, 
    DatabaseResult,
    QueryOptions, 
    QueryFilter, 
    FilterOperation,
    ConnectionException,
    ValidationException,
    NotFoundException,
    DuplicateException,
    TransactionException
)
from .schemas import get_schema, get_all_table_names

logger = logging.getLogger(__name__)

class MongoDBService(IDatabaseService):
    """MongoDB implementation of the database service"""
    
    def __init__(
        self, 
        connection_string: str,
        database_name: Optional[str] = None,
        pool_size: int = 10,
        timeout_seconds: int = 30
    ):
        self.connection_string = connection_string
        self.pool_size = pool_size
        self.timeout_seconds = timeout_seconds
        
        # Extract database name from connection string or use provided
        if database_name:
            self.database_name = database_name
        else:
            parsed = urlparse(connection_string)
            self.database_name = parsed.path.lstrip('/') or 'openkiosk'
        
        self._client: Optional[AsyncIOMotorClient] = None
        self._database: Optional[AsyncIOMotorDatabase] = None
        self._is_initialized = False

    @property
    def provider(self) -> DatabaseProvider:
        return DatabaseProvider.MONGODB

    async def initialize(self) -> bool:
        """Initialize MongoDB connection with proper error handling"""
        try:
            logger.info(f"Initializing MongoDB connection to database: {self.database_name}")
            
            # Create client with connection options
            self._client = AsyncIOMotorClient(
                self.connection_string,
                maxPoolSize=self.pool_size,
                serverSelectionTimeoutMS=self.timeout_seconds * 1000,
                connectTimeoutMS=self.timeout_seconds * 1000,
                socketTimeoutMS=self.timeout_seconds * 1000,
                retryWrites=True,
                w="majority"
            )
            
            # Get database
            self._database = self._client[self.database_name]
            
            # Test connection
            await self._client.admin.command('ismaster')
            
            # Create indexes for all schemas
            await self._create_indexes()
            
            self._is_initialized = True
            logger.info("✅ MongoDB connection initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize MongoDB: {str(e)}")
            self._client = None
            self._database = None
            self._is_initialized = False
            raise ConnectionException(f"Failed to connect to MongoDB: {str(e)}", "mongodb", "initialize")

    async def health_check(self) -> Dict[str, Any]:
        """Check MongoDB health status"""
        try:
            if not self._is_initialized or self._client is None:
                return {
                    "status": "unhealthy",
                    "provider": "mongodb",
                    "error": "Not initialized"
                }
            
            # Test database connection
            result = await self._client.admin.command('ping')
            
            # Get server status
            server_status = await self._client.admin.command('serverStatus')
            
            # Get database stats
            db_stats = await self._database.command('dbstats')
            
            return {
                "status": "healthy",
                "provider": "mongodb",
                "database": self.database_name,
                "ping": result.get('ok', 0) == 1,
                "version": server_status.get('version', 'unknown'),
                "uptime": server_status.get('uptime', 0),
                "connections": server_status.get('connections', {}),
                "collections": db_stats.get('collections', 0),
                "data_size": db_stats.get('dataSize', 0),
                "index_size": db_stats.get('indexSize', 0)
            }
            
        except Exception as e:
            logger.error(f"MongoDB health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "provider": "mongodb",
                "error": str(e)
            }

    async def close(self) -> None:
        """Close MongoDB connections"""
        if self._client:
            self._client.close()
            self._client = None
            self._database = None
            self._is_initialized = False
            logger.info("MongoDB connection closed")

    def _get_collection(self, table: str) -> AsyncIOMotorCollection:
        """Get MongoDB collection"""
        if self._database is None:
            raise ConnectionException("Database not initialized", "mongodb", "get_collection")
        return self._database[table]

    def _convert_id_fields(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """Convert MongoDB ObjectId to string ID, preserving existing UUID id fields"""
        if not document:
            return document
            
        # Only convert _id to id if there's no existing id field (preserve UUIDs)
        if '_id' in document and 'id' not in document:
            document['id'] = str(document['_id'])
        
        # Always remove _id since we use 'id' field
        if '_id' in document:
            del document['_id']
        
        # Convert any ObjectId fields to strings
        for key, value in document.items():
            if isinstance(value, ObjectId):
                document[key] = str(value)
        
        return document

    def _prepare_document(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare document for MongoDB insertion"""
        doc = data.copy()
        
        # Ensure ID field
        if 'id' not in doc:
            doc['id'] = self.generate_id()
        
        # Add timestamps if not present
        now = self.current_timestamp()
        if 'created_at' not in doc:
            doc['created_at'] = now
        if 'updated_at' not in doc:
            doc['updated_at'] = now
        
        # Convert id to _id for MongoDB
        if 'id' in doc:
            doc['_id'] = doc['id']
        
        return doc

    def _build_mongo_filter(self, filters: List[QueryFilter]) -> Dict[str, Any]:
        """Build MongoDB filter from QueryFilter objects"""
        mongo_filter = {}
        
        for filter_obj in filters:
            field = filter_obj.field
            operation = filter_obj.operation
            value = filter_obj.value
            
            # Handle special ID field
            if field == 'id':
                field = '_id'
            
            if operation == FilterOperation.EQUALS:
                mongo_filter[field] = value
            elif operation == FilterOperation.NOT_EQUALS:
                mongo_filter[field] = {"$ne": value}
            elif operation == FilterOperation.GREATER_THAN:
                mongo_filter[field] = {"$gt": value}
            elif operation == FilterOperation.GREATER_THAN_EQUAL:
                mongo_filter[field] = {"$gte": value}
            elif operation == FilterOperation.LESS_THAN:
                mongo_filter[field] = {"$lt": value}
            elif operation == FilterOperation.LESS_THAN_EQUAL:
                mongo_filter[field] = {"$lte": value}
            elif operation == FilterOperation.IN:
                mongo_filter[field] = {"$in": value if isinstance(value, list) else [value]}
            elif operation == FilterOperation.NOT_IN:
                mongo_filter[field] = {"$nin": value if isinstance(value, list) else [value]}
            elif operation == FilterOperation.CONTAINS:
                mongo_filter[field] = {"$regex": str(value), "$options": "i"}
            elif operation == FilterOperation.STARTS_WITH:
                mongo_filter[field] = {"$regex": f"^{str(value)}", "$options": "i"}
            elif operation == FilterOperation.ENDS_WITH:
                mongo_filter[field] = {"$regex": f"{str(value)}$", "$options": "i"}
            elif operation == FilterOperation.IS_NULL:
                mongo_filter[field] = {"$in": [None, ""]}
            elif operation == FilterOperation.IS_NOT_NULL:
                mongo_filter[field] = {"$nin": [None, ""]}
        
        return mongo_filter

    async def _create_indexes(self) -> None:
        """Create indexes for all schemas"""
        try:
            for table_name in get_all_table_names():
                schema = get_schema(table_name)
                if not schema or not schema.indexes:
                    continue
                
                collection = self._get_collection(table_name)
                
                for index_config in schema.indexes:
                    fields = index_config.get('fields', [])
                    unique = index_config.get('unique', False)
                    
                    if not fields:
                        continue
                    
                    # Convert field names for MongoDB
                    index_fields = []
                    for field in fields:
                        if field == 'id':
                            index_fields.append(('_id', 1))
                        else:
                            index_fields.append((field, 1))
                    
                    try:
                        await collection.create_index(index_fields, unique=unique, background=True)
                        logger.debug(f"Created index for {table_name}: {fields}")
                    except Exception as e:
                        logger.warning(f"Failed to create index for {table_name}: {e}")
                        
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")

    # CRUD Operations Implementation
    
    async def create_record(
        self,
        table: str,
        data: Dict[str, Any],
        return_record: bool = True
    ) -> DatabaseResult:
        """Create a new record"""
        try:
            collection = self._get_collection(table)
            doc = self._prepare_document(data)
            
            result = await collection.insert_one(doc)
            
            if return_record:
                created_doc = await collection.find_one({"_id": result.inserted_id})
                created_doc = self._convert_id_fields(created_doc)
                return DatabaseResult(success=True, data=created_doc)
            else:
                return DatabaseResult(success=True, data={"id": str(result.inserted_id)})
                
        except DuplicateKeyError as e:
            logger.error(f"Duplicate key error in {table}: {e}")
            return DatabaseResult(success=False, error="Record already exists")
        except Exception as e:
            logger.error(f"Error creating record in {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    async def get_record(
        self,
        table: str,
        record_id: str,
        include_related: Optional[List[str]] = None
    ) -> DatabaseResult:
        """Get a record by ID"""
        try:
            collection = self._get_collection(table)
            
            # Convert string ID to ObjectId for MongoDB query
            try:
                object_id = ObjectId(record_id)
            except Exception:
                # If conversion fails, try querying with the string directly
                object_id = record_id
            
            doc = await collection.find_one({"_id": object_id})
            
            if not doc:
                return DatabaseResult(success=False, error="Record not found")
            
            doc = self._convert_id_fields(doc)
            return DatabaseResult(success=True, data=doc)
            
        except Exception as e:
            logger.error(f"Error getting record from {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    async def update_record(
        self,
        table: str,
        record_id: str,
        data: Dict[str, Any],
        return_record: bool = True
    ) -> DatabaseResult:
        """Update a record by ID"""
        try:
            collection = self._get_collection(table)
            
            # Add updated_at timestamp
            update_data = data.copy()
            update_data['updated_at'] = self.current_timestamp()
            
            result = await collection.update_one(
                {"_id": record_id},
                {"$set": update_data}
            )
            
            if result.matched_count == 0:
                return DatabaseResult(success=False, error="Record not found")
            
            if return_record:
                updated_doc = await collection.find_one({"_id": record_id})
                updated_doc = self._convert_id_fields(updated_doc)
                return DatabaseResult(success=True, data=updated_doc)
            else:
                return DatabaseResult(success=True, data={"updated": result.modified_count})
                
        except Exception as e:
            logger.error(f"Error updating record in {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    async def delete_record(self, table: str, record_id: str) -> DatabaseResult:
        """Delete a record by ID"""
        try:
            collection = self._get_collection(table)
            result = await collection.delete_one({"_id": record_id})
            
            if result.deleted_count == 0:
                return DatabaseResult(success=False, error="Record not found")
            
            return DatabaseResult(success=True, data={"deleted": result.deleted_count})
            
        except Exception as e:
            logger.error(f"Error deleting record from {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    async def list_records(
        self,
        table: str,
        options: Optional[QueryOptions] = None
    ) -> DatabaseResult:
        """List records with optional filtering, sorting, and pagination"""
        try:
            collection = self._get_collection(table)
            
            # Build query
            query = {}
            if options and options.filters:
                query = self._build_mongo_filter(options.filters)
            
            # Create cursor
            cursor = collection.find(query)
            
            # Apply sorting
            if options and options.sort_by:
                sort_field = "_id" if options.sort_by == "id" else options.sort_by
                sort_direction = -1 if options.sort_desc else 1
                cursor = cursor.sort(sort_field, sort_direction)
            
            # Apply pagination
            if options and options.offset:
                cursor = cursor.skip(options.offset)
            if options and options.limit:
                cursor = cursor.limit(options.limit)
            
            # Execute query
            docs = []
            async for doc in cursor:
                docs.append(self._convert_id_fields(doc))
            
            # Get total count if pagination is used
            count = None
            if options and (options.limit or options.offset):
                count = await collection.count_documents(query)
            
            return DatabaseResult(success=True, data=docs, count=count)
            
        except Exception as e:
            logger.error(f"Error listing records from {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    async def count_records(
        self,
        table: str,
        filters: Optional[List[QueryFilter]] = None
    ) -> DatabaseResult:
        """Count records matching filters"""
        try:
            collection = self._get_collection(table)
            
            query = {}
            if filters:
                query = self._build_mongo_filter(filters)
            
            count = await collection.count_documents(query)
            return DatabaseResult(success=True, data=count)
            
        except Exception as e:
            logger.error(f"Error counting records in {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    async def record_exists(self, table: str, record_id: str) -> DatabaseResult:
        """Check if a record exists"""
        try:
            collection = self._get_collection(table)
            count = await collection.count_documents({"_id": record_id})
            return DatabaseResult(success=True, data=count > 0)
            
        except Exception as e:
            logger.error(f"Error checking record existence in {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    # Advanced Query Operations

    async def find_records(
        self,
        table: str,
        filters: List[QueryFilter],
        options: Optional[QueryOptions] = None
    ) -> DatabaseResult:
        """Find records using complex filter conditions"""
        try:
            collection = self._get_collection(table)
            
            query = self._build_mongo_filter(filters)
            cursor = collection.find(query)
            
            # Apply options
            if options:
                if options.sort_by:
                    sort_field = "_id" if options.sort_by == "id" else options.sort_by
                    sort_direction = -1 if options.sort_desc else 1
                    cursor = cursor.sort(sort_field, sort_direction)
                
                if options.offset:
                    cursor = cursor.skip(options.offset)
                if options.limit:
                    cursor = cursor.limit(options.limit)
            
            docs = []
            async for doc in cursor:
                docs.append(self._convert_id_fields(doc))
            
            return DatabaseResult(success=True, data=docs)
            
        except Exception as e:
            logger.error(f"Error finding records in {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    async def find_one_record(
        self,
        table: str,
        filters: List[QueryFilter],
        include_related: Optional[List[str]] = None
    ) -> DatabaseResult:
        """Find single record using filter conditions"""
        try:
            collection = self._get_collection(table)
            query = self._build_mongo_filter(filters)
            
            doc = await collection.find_one(query)
            if not doc:
                return DatabaseResult(success=False, error="Record not found")
            
            doc = self._convert_id_fields(doc)
            return DatabaseResult(success=True, data=doc)
            
        except Exception as e:
            logger.error(f"Error finding record in {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    # Batch Operations

    async def batch_create(
        self,
        table: str,
        records: List[Dict[str, Any]]
    ) -> DatabaseResult:
        """Create multiple records in a single operation"""
        try:
            collection = self._get_collection(table)
            docs = [self._prepare_document(record) for record in records]
            
            result = await collection.insert_many(docs, ordered=False)
            
            return DatabaseResult(
                success=True, 
                data={"created": len(result.inserted_ids), "ids": [str(id) for id in result.inserted_ids]}
            )
            
        except Exception as e:
            logger.error(f"Error batch creating records in {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    async def batch_update(
        self,
        table: str,
        updates: List[Dict[str, Any]]
    ) -> DatabaseResult:
        """Update multiple records in a single operation"""
        try:
            collection = self._get_collection(table)
            updated_count = 0
            
            for update in updates:
                if 'id' not in update:
                    continue
                
                record_id = update['id']
                update_data = {k: v for k, v in update.items() if k != 'id'}
                update_data['updated_at'] = self.current_timestamp()
                
                result = await collection.update_one(
                    {"_id": record_id},
                    {"$set": update_data}
                )
                updated_count += result.modified_count
            
            return DatabaseResult(success=True, data={"updated": updated_count})
            
        except Exception as e:
            logger.error(f"Error batch updating records in {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    async def batch_delete(
        self,
        table: str,
        record_ids: List[str]
    ) -> DatabaseResult:
        """Delete multiple records in a single operation"""
        try:
            collection = self._get_collection(table)
            result = await collection.delete_many({"_id": {"$in": record_ids}})
            
            return DatabaseResult(success=True, data={"deleted": result.deleted_count})
            
        except Exception as e:
            logger.error(f"Error batch deleting records from {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    # Transaction Support

    async def execute_transaction(
        self,
        operations: List[Dict[str, Any]]
    ) -> DatabaseResult:
        """Execute multiple operations in a transaction"""
        try:
            async with await self._client.start_session() as session:
                async with session.start_transaction():
                    results = []
                    
                    for operation in operations:
                        op_type = operation.get('type')
                        table = operation.get('table')
                        data = operation.get('data', {})
                        
                        if op_type == 'create':
                            result = await self.create_record(table, data, return_record=False)
                        elif op_type == 'update':
                            record_id = operation.get('id')
                            result = await self.update_record(table, record_id, data, return_record=False)
                        elif op_type == 'delete':
                            record_id = operation.get('id')
                            result = await self.delete_record(table, record_id)
                        else:
                            result = DatabaseResult(success=False, error=f"Unknown operation type: {op_type}")
                        
                        if not result.success:
                            raise TransactionException(f"Transaction failed: {result.error}")
                        
                        results.append(result.data)
                    
                    return DatabaseResult(success=True, data=results)
                    
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            return DatabaseResult(success=False, error=str(e))

    # Schema Operations

    async def create_table(
        self,
        table: str,
        schema: Dict[str, Any]
    ) -> DatabaseResult:
        """Create a collection (MongoDB doesn't require explicit table creation)"""
        try:
            # MongoDB creates collections automatically, but we can create indexes
            await self._create_indexes()
            return DatabaseResult(success=True, data={"table": table, "created": True})
            
        except Exception as e:
            logger.error(f"Error creating table {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    async def table_exists(self, table: str) -> DatabaseResult:
        """Check if a collection exists"""
        try:
            collections = await self._database.list_collection_names()
            exists = table in collections
            return DatabaseResult(success=True, data=exists)
            
        except Exception as e:
            logger.error(f"Error checking table existence {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    async def get_table_schema(self, table: str) -> DatabaseResult:
        """Get collection schema information"""
        try:
            schema = get_schema(table)
            if schema:
                return DatabaseResult(success=True, data=schema.__dict__)
            else:
                return DatabaseResult(success=False, error="Schema not found")
                
        except Exception as e:
            logger.error(f"Error getting table schema {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    # Indexing Operations

    async def create_index(
        self,
        table: str,
        fields: List[str],
        unique: bool = False,
        name: Optional[str] = None
    ) -> DatabaseResult:
        """Create an index on specified fields"""
        try:
            collection = self._get_collection(table)
            
            # Convert field names
            index_fields = []
            for field in fields:
                if field == 'id':
                    index_fields.append(('_id', 1))
                else:
                    index_fields.append((field, 1))
            
            await collection.create_index(index_fields, unique=unique, name=name, background=True)
            return DatabaseResult(success=True, data={"index": name or str(fields), "created": True})
            
        except Exception as e:
            logger.error(f"Error creating index on {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    async def drop_index(self, table: str, name: str) -> DatabaseResult:
        """Drop an index"""
        try:
            collection = self._get_collection(table)
            await collection.drop_index(name)
            return DatabaseResult(success=True, data={"index": name, "dropped": True})
            
        except Exception as e:
            logger.error(f"Error dropping index on {table}: {e}")
            return DatabaseResult(success=False, error=str(e))