# Supabase Database Service Implementation
# Enterprise-grade Supabase service with REST API and real-time features

import logging
import asyncio
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import json
import uuid
import aiohttp

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

class SupabaseService(IDatabaseService):
    """Supabase implementation of the database service"""
    
    def __init__(
        self,
        project_url: str,
        service_key: str,
        timeout_seconds: int = 30
    ):
        self.project_url = project_url.rstrip('/')
        self.service_key = service_key
        self.timeout_seconds = timeout_seconds
        
        # API endpoints
        self.rest_url = f"{self.project_url}/rest/v1"
        self.auth_url = f"{self.project_url}/auth/v1"
        
        # Headers
        self.headers = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
            "Prefer": "return=representation"
        }
        
        self._session: Optional[aiohttp.ClientSession] = None
        self._is_initialized = False

    @property
    def provider(self) -> DatabaseProvider:
        return DatabaseProvider.SUPABASE

    async def initialize(self) -> bool:
        """Initialize Supabase connection"""
        try:
            logger.info("Initializing Supabase connection")
            
            # Create HTTP session
            timeout = aiohttp.ClientTimeout(total=self.timeout_seconds)
            self._session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=timeout
            )
            
            # Test connection
            async with self._session.get(f"{self.rest_url}/") as response:
                if response.status >= 400:
                    raise ConnectionException(f"Supabase connection failed: {response.status}")
            
            # Initialize schema if needed
            await self._initialize_schema()
            
            self._is_initialized = True
            logger.info("✅ Supabase connection initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize Supabase: {str(e)}")
            if self._session:
                await self._session.close()
                self._session = None
            self._is_initialized = False
            raise ConnectionException(f"Failed to connect to Supabase: {str(e)}", "supabase", "initialize")

    async def health_check(self) -> Dict[str, Any]:
        """Check Supabase health status"""
        try:
            if not self._is_initialized or not self._session:
                return {
                    "status": "unhealthy",
                    "provider": "supabase",
                    "error": "Not initialized"
                }
            
            # Test API connectivity
            async with self._session.get(f"{self.rest_url}/") as response:
                if response.status >= 400:
                    return {
                        "status": "unhealthy",
                        "provider": "supabase",
                        "error": f"API returned status {response.status}"
                    }
                
                return {
                    "status": "healthy",
                    "provider": "supabase",
                    "project_url": self.project_url,
                    "api_status": response.status,
                    "response_time": response.headers.get("x-response-time", "unknown")
                }
                
        except Exception as e:
            logger.error(f"Supabase health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "provider": "supabase",
                "error": str(e)
            }

    async def close(self) -> None:
        """Close Supabase connections"""
        if self._session:
            await self._session.close()
            self._session = None
            self._is_initialized = False
            logger.info("Supabase connection closed")

    def _build_supabase_filter(self, filters: List[QueryFilter]) -> str:
        """Build Supabase filter query string from QueryFilter objects"""
        if not filters:
            return ""
        
        filter_parts = []
        
        for filter_obj in filters:
            field = filter_obj.field
            operation = filter_obj.operation
            value = filter_obj.value
            
            if operation == FilterOperation.EQUALS:
                filter_parts.append(f"{field}=eq.{value}")
            elif operation == FilterOperation.NOT_EQUALS:
                filter_parts.append(f"{field}=neq.{value}")
            elif operation == FilterOperation.GREATER_THAN:
                filter_parts.append(f"{field}=gt.{value}")
            elif operation == FilterOperation.GREATER_THAN_EQUAL:
                filter_parts.append(f"{field}=gte.{value}")
            elif operation == FilterOperation.LESS_THAN:
                filter_parts.append(f"{field}=lt.{value}")
            elif operation == FilterOperation.LESS_THAN_EQUAL:
                filter_parts.append(f"{field}=lte.{value}")
            elif operation == FilterOperation.IN:
                values = value if isinstance(value, list) else [value]
                values_str = ",".join([str(v) for v in values])
                filter_parts.append(f"{field}=in.({values_str})")
            elif operation == FilterOperation.NOT_IN:
                values = value if isinstance(value, list) else [value]
                values_str = ",".join([str(v) for v in values])
                filter_parts.append(f"{field}=not.in.({values_str})")
            elif operation == FilterOperation.CONTAINS:
                filter_parts.append(f"{field}=ilike.*{value}*")
            elif operation == FilterOperation.STARTS_WITH:
                filter_parts.append(f"{field}=ilike.{value}*")
            elif operation == FilterOperation.ENDS_WITH:
                filter_parts.append(f"{field}=ilike.*{value}")
            elif operation == FilterOperation.IS_NULL:
                filter_parts.append(f"{field}=is.null")
            elif operation == FilterOperation.IS_NOT_NULL:
                filter_parts.append(f"{field}=not.is.null")
        
        return "&".join(filter_parts)

    async def _initialize_schema(self) -> None:
        """Initialize database schema (create tables if needed)"""
        try:
            # Supabase typically handles schema through migrations
            # This is a placeholder for any initialization logic
            logger.info("Schema initialization completed")
            
        except Exception as e:
            logger.error(f"Error initializing schema: {e}")
            raise

    # CRUD Operations Implementation

    async def create_record(
        self,
        table: str,
        data: Dict[str, Any],
        return_record: bool = True
    ) -> DatabaseResult:
        """Create a new record"""
        try:
            if not self._session:
                return DatabaseResult(success=False, error="Not initialized")
            
            # Prepare data
            record_data = data.copy()
            if 'id' not in record_data:
                record_data['id'] = self.generate_id()
            
            now = self.current_timestamp()
            if 'created_at' not in record_data:
                record_data['created_at'] = now.isoformat()
            if 'updated_at' not in record_data:
                record_data['updated_at'] = now.isoformat()
            
            url = f"{self.rest_url}/{table}"
            
            async with self._session.post(url, json=record_data) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    error_msg = error_data.get('message', f'HTTP {response.status}')
                    
                    if response.status == 409:  # Conflict - duplicate key
                        return DatabaseResult(success=False, error="Record already exists")
                    
                    return DatabaseResult(success=False, error=error_msg)
                
                if return_record:
                    result_data = await response.json()
                    if isinstance(result_data, list) and result_data:
                        return DatabaseResult(success=True, data=result_data[0])
                    elif isinstance(result_data, dict):
                        return DatabaseResult(success=True, data=result_data)
                
                return DatabaseResult(success=True, data={"id": record_data['id']})
                
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
            if not self._session:
                return DatabaseResult(success=False, error="Not initialized")
            
            url = f"{self.rest_url}/{table}?id=eq.{record_id}"
            
            if include_related:
                # Handle related data selection
                select_fields = "*"
                for relation in include_related:
                    select_fields += f",{relation}(*)"
                url += f"&select={select_fields}"
            
            async with self._session.get(url) as response:
                if response.status >= 400:
                    return DatabaseResult(success=False, error=f"HTTP {response.status}")
                
                result_data = await response.json()
                
                if not result_data:
                    return DatabaseResult(success=False, error="Record not found")
                
                return DatabaseResult(success=True, data=result_data[0])
                
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
            if not self._session:
                return DatabaseResult(success=False, error="Not initialized")
            
            # Prepare update data
            update_data = data.copy()
            update_data['updated_at'] = self.current_timestamp().isoformat()
            
            url = f"{self.rest_url}/{table}?id=eq.{record_id}"
            
            async with self._session.patch(url, json=update_data) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    return DatabaseResult(success=False, error=error_data.get('message', f'HTTP {response.status}'))
                
                if return_record:
                    result_data = await response.json()
                    if not result_data:
                        return DatabaseResult(success=False, error="Record not found")
                    
                    return DatabaseResult(success=True, data=result_data[0] if isinstance(result_data, list) else result_data)
                else:
                    return DatabaseResult(success=True, data={"updated": 1})
                
        except Exception as e:
            logger.error(f"Error updating record in {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    async def delete_record(self, table: str, record_id: str) -> DatabaseResult:
        """Delete a record by ID"""
        try:
            if not self._session:
                return DatabaseResult(success=False, error="Not initialized")
            
            url = f"{self.rest_url}/{table}?id=eq.{record_id}"
            
            async with self._session.delete(url) as response:
                if response.status >= 400:
                    return DatabaseResult(success=False, error=f"HTTP {response.status}")
                
                # Supabase returns the deleted records
                result_data = await response.json()
                
                if not result_data:
                    return DatabaseResult(success=False, error="Record not found")
                
                return DatabaseResult(success=True, data={"deleted": len(result_data)})
                
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
            if not self._session:
                return DatabaseResult(success=False, error="Not initialized")
            
            url = f"{self.rest_url}/{table}"
            query_params = []
            
            # Apply filters
            if options and options.filters:
                filter_string = self._build_supabase_filter(options.filters)
                if filter_string:
                    query_params.append(filter_string)
            
            # Apply sorting
            if options and options.sort_by:
                direction = "desc" if options.sort_desc else "asc"
                query_params.append(f"order={options.sort_by}.{direction}")
            
            # Apply pagination
            if options and options.limit:
                query_params.append(f"limit={options.limit}")
            
            if options and options.offset:
                query_params.append(f"offset={options.offset}")
            
            # Build final URL
            if query_params:
                url += "?" + "&".join(query_params)
            
            # Get count if needed
            count = None
            if options and (options.limit or options.offset):
                count_url = f"{self.rest_url}/{table}?select=count"
                if options and options.filters:
                    filter_string = self._build_supabase_filter(options.filters)
                    if filter_string:
                        count_url += f"&{filter_string}"
                
                async with self._session.get(count_url, headers={**self.headers, "Prefer": "count=exact"}) as count_response:
                    if count_response.status == 200:
                        count_header = count_response.headers.get("content-range", "")
                        if "/" in count_header:
                            count = int(count_header.split("/")[1])
            
            async with self._session.get(url) as response:
                if response.status >= 400:
                    return DatabaseResult(success=False, error=f"HTTP {response.status}")
                
                result_data = await response.json()
                return DatabaseResult(success=True, data=result_data, count=count)
                
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
            if not self._session:
                return DatabaseResult(success=False, error="Not initialized")
            
            url = f"{self.rest_url}/{table}?select=count"
            
            if filters:
                filter_string = self._build_supabase_filter(filters)
                if filter_string:
                    url += f"&{filter_string}"
            
            headers = {**self.headers, "Prefer": "count=exact"}
            
            async with self._session.get(url, headers=headers) as response:
                if response.status >= 400:
                    return DatabaseResult(success=False, error=f"HTTP {response.status}")
                
                count_header = response.headers.get("content-range", "")
                if "/" in count_header:
                    count = int(count_header.split("/")[1])
                    return DatabaseResult(success=True, data=count)
                else:
                    return DatabaseResult(success=False, error="Could not get count")
                
        except Exception as e:
            logger.error(f"Error counting records in {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    async def record_exists(self, table: str, record_id: str) -> DatabaseResult:
        """Check if a record exists"""
        try:
            if not self._session:
                return DatabaseResult(success=False, error="Not initialized")
            
            url = f"{self.rest_url}/{table}?id=eq.{record_id}&select=id"
            
            async with self._session.get(url) as response:
                if response.status >= 400:
                    return DatabaseResult(success=False, error=f"HTTP {response.status}")
                
                result_data = await response.json()
                return DatabaseResult(success=True, data=len(result_data) > 0)
                
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
        # Reuse list_records with filters in options
        if not options:
            options = QueryOptions(filters=filters)
        else:
            options.filters = filters
        
        return await self.list_records(table, options)

    async def find_one_record(
        self,
        table: str,
        filters: List[QueryFilter],
        include_related: Optional[List[str]] = None
    ) -> DatabaseResult:
        """Find single record using filter conditions"""
        try:
            if not self._session:
                return DatabaseResult(success=False, error="Not initialized")
            
            url = f"{self.rest_url}/{table}"
            filter_string = self._build_supabase_filter(filters)
            
            if filter_string:
                url += f"?{filter_string}&limit=1"
            else:
                url += "?limit=1"
            
            if include_related:
                select_fields = "*"
                for relation in include_related:
                    select_fields += f",{relation}(*)"
                url += f"&select={select_fields}"
            
            async with self._session.get(url) as response:
                if response.status >= 400:
                    return DatabaseResult(success=False, error=f"HTTP {response.status}")
                
                result_data = await response.json()
                
                if not result_data:
                    return DatabaseResult(success=False, error="Record not found")
                
                return DatabaseResult(success=True, data=result_data[0])
                
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
            if not self._session:
                return DatabaseResult(success=False, error="Not initialized")
            
            if not records:
                return DatabaseResult(success=True, data={"created": 0, "ids": []})
            
            # Prepare records
            now = self.current_timestamp()
            prepared_records = []
            ids = []
            
            for record in records:
                prepared = record.copy()
                if 'id' not in prepared:
                    prepared['id'] = self.generate_id()
                if 'created_at' not in prepared:
                    prepared['created_at'] = now.isoformat()
                if 'updated_at' not in prepared:
                    prepared['updated_at'] = now.isoformat()
                
                prepared_records.append(prepared)
                ids.append(prepared['id'])
            
            url = f"{self.rest_url}/{table}"
            
            async with self._session.post(url, json=prepared_records) as response:
                if response.status >= 400:
                    error_data = await response.json()
                    return DatabaseResult(success=False, error=error_data.get('message', f'HTTP {response.status}'))
                
                return DatabaseResult(
                    success=True,
                    data={"created": len(ids), "ids": ids}
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
            if not self._session:
                return DatabaseResult(success=False, error="Not initialized")
            
            updated_count = 0
            
            # Supabase doesn't have native batch update, so we do individual updates
            for update in updates:
                if 'id' not in update:
                    continue
                
                record_id = update['id']
                update_data = {k: v for k, v in update.items() if k != 'id'}
                update_data['updated_at'] = self.current_timestamp().isoformat()
                
                result = await self.update_record(table, record_id, update_data, return_record=False)
                if result.success:
                    updated_count += 1
            
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
            if not self._session:
                return DatabaseResult(success=False, error="Not initialized")
            
            if not record_ids:
                return DatabaseResult(success=True, data={"deleted": 0})
            
            ids_str = ",".join(record_ids)
            url = f"{self.rest_url}/{table}?id=in.({ids_str})"
            
            async with self._session.delete(url) as response:
                if response.status >= 400:
                    return DatabaseResult(success=False, error=f"HTTP {response.status}")
                
                result_data = await response.json()
                return DatabaseResult(success=True, data={"deleted": len(result_data)})
                
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
            # Supabase doesn't support explicit transactions via REST API
            # We'll execute operations sequentially and rollback on error
            results = []
            executed_operations = []
            
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
                    # Rollback previous operations (best effort)
                    await self._rollback_operations(executed_operations)
                    return DatabaseResult(success=False, error=f"Transaction failed: {result.error}")
                
                results.append(result.data)
                executed_operations.append({**operation, 'result': result})
            
            return DatabaseResult(success=True, data=results)
                
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            return DatabaseResult(success=False, error=str(e))

    async def _rollback_operations(self, executed_operations: List[Dict[str, Any]]) -> None:
        """Best effort rollback of executed operations"""
        try:
            # Reverse the operations
            for operation in reversed(executed_operations):
                op_type = operation.get('type')
                table = operation.get('table')
                
                if op_type == 'create':
                    # Delete the created record
                    data = operation.get('data', {})
                    if 'id' in data:
                        await self.delete_record(table, data['id'])
                elif op_type == 'delete':
                    # Can't easily restore deleted records
                    pass
                # Update rollback would require storing original values
                
        except Exception as e:
            logger.error(f"Rollback failed: {e}")

    # Schema Operations

    async def create_table(
        self,
        table: str,
        schema: Dict[str, Any]
    ) -> DatabaseResult:
        """Create a table with specified schema (Supabase handles schema via migrations)"""
        # Supabase typically handles schema creation through migrations
        # This would require admin access and SQL execution
        return DatabaseResult(success=False, error="Table creation not supported via REST API")

    async def table_exists(self, table: str) -> DatabaseResult:
        """Check if a table exists"""
        try:
            if not self._session:
                return DatabaseResult(success=False, error="Not initialized")
            
            # Try to query the table
            url = f"{self.rest_url}/{table}?limit=0"
            
            async with self._session.get(url) as response:
                exists = response.status < 400
                return DatabaseResult(success=True, data=exists)
                
        except Exception as e:
            logger.error(f"Error checking table existence {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    async def get_table_schema(self, table: str) -> DatabaseResult:
        """Get table schema information"""
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
        """Create an index on specified fields (requires admin access)"""
        return DatabaseResult(success=False, error="Index creation not supported via REST API")

    async def drop_index(self, table: str, name: str) -> DatabaseResult:
        """Drop an index (requires admin access)"""
        return DatabaseResult(success=False, error="Index dropping not supported via REST API")