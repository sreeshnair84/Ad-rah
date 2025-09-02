# PostgreSQL Database Service Implementation
# Enterprise-grade PostgreSQL service with connection pooling and advanced features

import logging
import asyncio
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
import json
import uuid

import asyncpg
from asyncpg import Connection, Pool
from asyncpg.exceptions import (
    UniqueViolationError,
    ForeignKeyViolationError,
    NotNullViolationError,
    CheckViolationError,
    ConnectionDoesNotExistError
)

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
from .schemas import get_schema, get_all_table_names, FieldType, FieldDefinition, TableSchema

logger = logging.getLogger(__name__)

class PostgreSQLService(IDatabaseService):
    """PostgreSQL implementation of the database service"""
    
    def __init__(
        self,
        connection_string: str,
        min_connections: int = 5,
        max_connections: int = 20,
        command_timeout: int = 60
    ):
        self.connection_string = connection_string
        self.min_connections = min_connections
        self.max_connections = max_connections
        self.command_timeout = command_timeout
        
        self._pool: Optional[Pool] = None
        self._is_initialized = False

    @property
    def provider(self) -> DatabaseProvider:
        return DatabaseProvider.POSTGRESQL

    async def initialize(self) -> bool:
        """Initialize PostgreSQL connection pool"""
        try:
            logger.info("Initializing PostgreSQL connection pool")
            
            # Create connection pool
            self._pool = await asyncpg.create_pool(
                self.connection_string,
                min_size=self.min_connections,
                max_size=self.max_connections,
                command_timeout=self.command_timeout,
                server_settings={
                    'application_name': 'openkiosk_backend',
                    'timezone': 'UTC'
                }
            )
            
            # Test connection
            async with self._pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            
            # Create tables and indexes
            await self._create_schema()
            
            self._is_initialized = True
            logger.info("✅ PostgreSQL connection pool initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to initialize PostgreSQL: {str(e)}")
            self._pool = None
            self._is_initialized = False
            raise ConnectionException(f"Failed to connect to PostgreSQL: {str(e)}", "postgresql", "initialize")

    async def health_check(self) -> Dict[str, Any]:
        """Check PostgreSQL health status"""
        try:
            if not self._is_initialized or not self._pool:
                return {
                    "status": "unhealthy",
                    "provider": "postgresql",
                    "error": "Not initialized"
                }
            
            async with self._pool.acquire() as conn:
                # Test basic connectivity
                result = await conn.fetchval("SELECT 1")
                
                # Get database info
                version = await conn.fetchval("SELECT version()")
                current_db = await conn.fetchval("SELECT current_database()")
                
                # Get connection stats
                stats = self._pool.get_stats()
                
                return {
                    "status": "healthy",
                    "provider": "postgresql",
                    "database": current_db,
                    "version": version,
                    "ping": result == 1,
                    "pool_stats": {
                        "current_size": stats.current_size,
                        "max_size": stats.max_size,
                        "idle_connections": stats.idle_connections,
                        "busy_connections": stats.busy_connections
                    }
                }
                
        except Exception as e:
            logger.error(f"PostgreSQL health check failed: {str(e)}")
            return {
                "status": "unhealthy",
                "provider": "postgresql",
                "error": str(e)
            }

    async def close(self) -> None:
        """Close PostgreSQL connection pool"""
        if self._pool:
            await self._pool.close()
            self._pool = None
            self._is_initialized = False
            logger.info("PostgreSQL connection pool closed")

    def _get_postgres_type(self, field_type: FieldType, max_length: Optional[int] = None) -> str:
        """Convert FieldType to PostgreSQL type"""
        type_mapping = {
            FieldType.STRING: f"VARCHAR({max_length or 255})",
            FieldType.TEXT: "TEXT",
            FieldType.INTEGER: "INTEGER",
            FieldType.FLOAT: "REAL",
            FieldType.BOOLEAN: "BOOLEAN",
            FieldType.DATETIME: "TIMESTAMP WITH TIME ZONE",
            FieldType.JSON: "JSONB",
            FieldType.UUID: "UUID",
            FieldType.EMAIL: f"VARCHAR({max_length or 320})",
            FieldType.URL: f"VARCHAR({max_length or 2048})",
            FieldType.ENUM: "VARCHAR(50)"  # Will be handled specially
        }
        return type_mapping.get(field_type, "TEXT")

    def _build_create_table_sql(self, schema: TableSchema) -> str:
        """Build CREATE TABLE SQL from schema"""
        columns = []
        
        for field in schema.fields:
            col_def = f'"{field.name}" {self._get_postgres_type(field.field_type, field.max_length)}'
            
            # Add constraints
            if field.required:
                col_def += " NOT NULL"
            
            if field.unique:
                col_def += " UNIQUE"
            
            if field.default_value is not None:
                if field.default_value == "NOW()":
                    col_def += " DEFAULT CURRENT_TIMESTAMP"
                elif isinstance(field.default_value, str):
                    col_def += f" DEFAULT '{field.default_value}'"
                else:
                    col_def += f" DEFAULT {field.default_value}"
            
            columns.append(col_def)
        
        # Add primary key
        columns.append('PRIMARY KEY ("id")')
        
        column_definitions = ",\n  ".join(columns)
        return f'CREATE TABLE IF NOT EXISTS "{schema.name}" (\n  {column_definitions}\n)'

    def _build_postgres_filter(self, filters: List[QueryFilter]) -> tuple[str, list]:
        """Build PostgreSQL WHERE clause from QueryFilter objects"""
        if not filters:
            return "", []
        
        conditions = []
        params = []
        param_count = 1
        
        for filter_obj in filters:
            field = f'"{filter_obj.field}"'
            operation = filter_obj.operation
            value = filter_obj.value
            
            if operation == FilterOperation.EQUALS:
                conditions.append(f"{field} = ${param_count}")
                params.append(value)
                param_count += 1
            elif operation == FilterOperation.NOT_EQUALS:
                conditions.append(f"{field} != ${param_count}")
                params.append(value)
                param_count += 1
            elif operation == FilterOperation.GREATER_THAN:
                conditions.append(f"{field} > ${param_count}")
                params.append(value)
                param_count += 1
            elif operation == FilterOperation.GREATER_THAN_EQUAL:
                conditions.append(f"{field} >= ${param_count}")
                params.append(value)
                param_count += 1
            elif operation == FilterOperation.LESS_THAN:
                conditions.append(f"{field} < ${param_count}")
                params.append(value)
                param_count += 1
            elif operation == FilterOperation.LESS_THAN_EQUAL:
                conditions.append(f"{field} <= ${param_count}")
                params.append(value)
                param_count += 1
            elif operation == FilterOperation.IN:
                values = value if isinstance(value, list) else [value]
                placeholders = ",".join([f"${param_count + i}" for i in range(len(values))])
                conditions.append(f"{field} = ANY(ARRAY[{placeholders}])")
                params.extend(values)
                param_count += len(values)
            elif operation == FilterOperation.NOT_IN:
                values = value if isinstance(value, list) else [value]
                placeholders = ",".join([f"${param_count + i}" for i in range(len(values))])
                conditions.append(f"{field} != ALL(ARRAY[{placeholders}])")
                params.extend(values)
                param_count += len(values)
            elif operation == FilterOperation.CONTAINS:
                conditions.append(f"{field} ILIKE ${param_count}")
                params.append(f"%{value}%")
                param_count += 1
            elif operation == FilterOperation.STARTS_WITH:
                conditions.append(f"{field} ILIKE ${param_count}")
                params.append(f"{value}%")
                param_count += 1
            elif operation == FilterOperation.ENDS_WITH:
                conditions.append(f"{field} ILIKE ${param_count}")
                params.append(f"%{value}")
                param_count += 1
            elif operation == FilterOperation.IS_NULL:
                conditions.append(f"({field} IS NULL OR {field} = '')")
            elif operation == FilterOperation.IS_NOT_NULL:
                conditions.append(f"({field} IS NOT NULL AND {field} != '')")
        
        where_clause = " WHERE " + " AND ".join(conditions) if conditions else ""
        return where_clause, params

    async def _create_schema(self) -> None:
        """Create database schema (tables and indexes)"""
        try:
            async with self._pool.acquire() as conn:
                # Enable UUID extension
                await conn.execute("CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\"")
                
                # Create tables
                for schema in [get_schema(name) for name in get_all_table_names()]:
                    if schema:
                        create_sql = self._build_create_table_sql(schema)
                        await conn.execute(create_sql)
                        logger.debug(f"Created table: {schema.name}")
                        
                        # Create indexes
                        for index_config in schema.indexes:
                            await self._create_table_index(conn, schema.name, index_config)
                
                logger.info("Database schema created successfully")
                
        except Exception as e:
            logger.error(f"Error creating schema: {e}")
            raise

    async def _create_table_index(self, conn: Connection, table_name: str, index_config: Dict[str, Any]) -> None:
        """Create an index for a table"""
        try:
            fields = index_config.get('fields', [])
            unique = index_config.get('unique', False)
            
            if not fields:
                return
            
            # Generate index name
            index_name = f"idx_{table_name}_{'_'.join(fields)}"
            if unique:
                index_name = f"uniq_{table_name}_{'_'.join(fields)}"
            
            # Build index SQL
            unique_sql = "UNIQUE " if unique else ""
            fields_sql = ', '.join([f'"{field}"' for field in fields])
            
            index_sql = f'CREATE {unique_sql}INDEX IF NOT EXISTS "{index_name}" ON "{table_name}" ({fields_sql})'
            
            await conn.execute(index_sql)
            logger.debug(f"Created index: {index_name}")
            
        except Exception as e:
            logger.warning(f"Failed to create index for {table_name}: {e}")

    # CRUD Operations Implementation

    async def create_record(
        self,
        table: str,
        data: Dict[str, Any],
        return_record: bool = True
    ) -> DatabaseResult:
        """Create a new record"""
        try:
            async with self._pool.acquire() as conn:
                # Prepare data
                record_data = data.copy()
                if 'id' not in record_data:
                    record_data['id'] = self.generate_id()
                
                now = self.current_timestamp()
                if 'created_at' not in record_data:
                    record_data['created_at'] = now
                if 'updated_at' not in record_data:
                    record_data['updated_at'] = now
                
                # Build INSERT query
                fields = list(record_data.keys())
                values = list(record_data.values())
                placeholders = ",".join([f"${i+1}" for i in range(len(values))])
                fields_sql = ",".join([f'"{field}"' for field in fields])
                
                insert_sql = f'INSERT INTO "{table}" ({fields_sql}) VALUES ({placeholders})'
                
                if return_record:
                    insert_sql += f' RETURNING *'
                    result = await conn.fetchrow(insert_sql, *values)
                    return DatabaseResult(success=True, data=dict(result))
                else:
                    await conn.execute(insert_sql, *values)
                    return DatabaseResult(success=True, data={"id": record_data['id']})
                
        except UniqueViolationError as e:
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
            async with self._pool.acquire() as conn:
                result = await conn.fetchrow(f'SELECT * FROM "{table}" WHERE "id" = $1', record_id)
                
                if not result:
                    return DatabaseResult(success=False, error="Record not found")
                
                return DatabaseResult(success=True, data=dict(result))
                
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
            async with self._pool.acquire() as conn:
                # Prepare update data
                update_data = data.copy()
                update_data['updated_at'] = self.current_timestamp()
                
                # Build UPDATE query
                fields = list(update_data.keys())
                values = list(update_data.values())
                set_clause = ",".join([f'"{field}" = ${i+1}' for i, field in enumerate(fields)])
                
                update_sql = f'UPDATE "{table}" SET {set_clause} WHERE "id" = ${len(values)+1}'
                values.append(record_id)
                
                if return_record:
                    update_sql += ' RETURNING *'
                    result = await conn.fetchrow(update_sql, *values)
                    if not result:
                        return DatabaseResult(success=False, error="Record not found")
                    return DatabaseResult(success=True, data=dict(result))
                else:
                    result = await conn.execute(update_sql, *values)
                    # Extract affected rows from result status
                    affected = int(result.split()[1]) if result else 0
                    if affected == 0:
                        return DatabaseResult(success=False, error="Record not found")
                    return DatabaseResult(success=True, data={"updated": affected})
                
        except Exception as e:
            logger.error(f"Error updating record in {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    async def delete_record(self, table: str, record_id: str) -> DatabaseResult:
        """Delete a record by ID"""
        try:
            async with self._pool.acquire() as conn:
                result = await conn.execute(f'DELETE FROM "{table}" WHERE "id" = $1', record_id)
                
                # Extract affected rows from result status
                affected = int(result.split()[1]) if result else 0
                if affected == 0:
                    return DatabaseResult(success=False, error="Record not found")
                
                return DatabaseResult(success=True, data={"deleted": affected})
                
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
            async with self._pool.acquire() as conn:
                # Build base query
                base_sql = f'SELECT * FROM "{table}"'
                params = []
                
                # Apply filters
                where_clause = ""
                if options and options.filters:
                    where_clause, params = self._build_postgres_filter(options.filters)
                
                # Build ORDER BY
                order_clause = ""
                if options and options.sort_by:
                    direction = "DESC" if options.sort_desc else "ASC"
                    order_clause = f' ORDER BY "{options.sort_by}" {direction}'
                
                # Build LIMIT/OFFSET
                limit_clause = ""
                if options and options.limit:
                    limit_clause += f" LIMIT ${len(params)+1}"
                    params.append(options.limit)
                
                if options and options.offset:
                    limit_clause += f" OFFSET ${len(params)+1}"
                    params.append(options.offset)
                
                # Execute query
                query_sql = base_sql + where_clause + order_clause + limit_clause
                results = await conn.fetch(query_sql, *params)
                
                # Get total count if pagination is used
                count = None
                if options and (options.limit or options.offset):
                    count_sql = f'SELECT COUNT(*) FROM "{table}"' + where_clause
                    count_params = params[:-2] if options.limit and options.offset else params[:-1] if (options.limit or options.offset) else params
                    count = await conn.fetchval(count_sql, *count_params)
                
                data = [dict(row) for row in results]
                return DatabaseResult(success=True, data=data, count=count)
                
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
            async with self._pool.acquire() as conn:
                base_sql = f'SELECT COUNT(*) FROM "{table}"'
                
                where_clause, params = self._build_postgres_filter(filters or [])
                
                count = await conn.fetchval(base_sql + where_clause, *params)
                return DatabaseResult(success=True, data=count)
                
        except Exception as e:
            logger.error(f"Error counting records in {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    async def record_exists(self, table: str, record_id: str) -> DatabaseResult:
        """Check if a record exists"""
        try:
            async with self._pool.acquire() as conn:
                count = await conn.fetchval(f'SELECT COUNT(*) FROM "{table}" WHERE "id" = $1', record_id)
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
            async with self._pool.acquire() as conn:
                base_sql = f'SELECT * FROM "{table}"'
                where_clause, params = self._build_postgres_filter(filters)
                
                result = await conn.fetchrow(base_sql + where_clause + " LIMIT 1", *params)
                
                if not result:
                    return DatabaseResult(success=False, error="Record not found")
                
                return DatabaseResult(success=True, data=dict(result))
                
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
            async with self._pool.acquire() as conn:
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
                        prepared['created_at'] = now
                    if 'updated_at' not in prepared:
                        prepared['updated_at'] = now
                    
                    prepared_records.append(prepared)
                    ids.append(prepared['id'])
                
                # Use COPY for bulk insert
                fields = list(prepared_records[0].keys())
                fields_sql = ",".join([f'"{field}"' for field in fields])
                
                copy_sql = f'COPY "{table}" ({fields_sql}) FROM STDIN'
                
                # Prepare data for COPY
                data_rows = []
                for record in prepared_records:
                    values = [record.get(field) for field in fields]
                    data_rows.append(values)
                
                await conn.copy_records_to_table(table, records=data_rows, columns=fields)
                
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
            async with self._pool.acquire() as conn:
                updated_count = 0
                
                async with conn.transaction():
                    for update in updates:
                        if 'id' not in update:
                            continue
                        
                        record_id = update['id']
                        update_data = {k: v for k, v in update.items() if k != 'id'}
                        update_data['updated_at'] = self.current_timestamp()
                        
                        # Build UPDATE query
                        fields = list(update_data.keys())
                        values = list(update_data.values())
                        set_clause = ",".join([f'"{field}" = ${i+1}' for i, field in enumerate(fields)])
                        
                        update_sql = f'UPDATE "{table}" SET {set_clause} WHERE "id" = ${len(values)+1}'
                        values.append(record_id)
                        
                        result = await conn.execute(update_sql, *values)
                        affected = int(result.split()[1]) if result else 0
                        updated_count += affected
                
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
            async with self._pool.acquire() as conn:
                if not record_ids:
                    return DatabaseResult(success=True, data={"deleted": 0})
                
                placeholders = ",".join([f"${i+1}" for i in range(len(record_ids))])
                delete_sql = f'DELETE FROM "{table}" WHERE "id" = ANY(ARRAY[{placeholders}])'
                
                result = await conn.execute(delete_sql, *record_ids)
                affected = int(result.split()[1]) if result else 0
                
                return DatabaseResult(success=True, data={"deleted": affected})
                
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
            async with self._pool.acquire() as conn:
                results = []
                
                async with conn.transaction():
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
        """Create a table with specified schema"""
        try:
            async with self._pool.acquire() as conn:
                table_schema = get_schema(table)
                if table_schema:
                    create_sql = self._build_create_table_sql(table_schema)
                    await conn.execute(create_sql)
                    
                    # Create indexes
                    for index_config in table_schema.indexes:
                        await self._create_table_index(conn, table, index_config)
                    
                    return DatabaseResult(success=True, data={"table": table, "created": True})
                else:
                    return DatabaseResult(success=False, error="Schema not found")
                
        except Exception as e:
            logger.error(f"Error creating table {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    async def table_exists(self, table: str) -> DatabaseResult:
        """Check if a table exists"""
        try:
            async with self._pool.acquire() as conn:
                result = await conn.fetchval(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
                    table
                )
                return DatabaseResult(success=True, data=result)
                
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
        """Create an index on specified fields"""
        try:
            async with self._pool.acquire() as conn:
                index_name = name or f"idx_{table}_{'_'.join(fields)}"
                if unique:
                    index_name = f"uniq_{table}_{'_'.join(fields)}"
                
                unique_sql = "UNIQUE " if unique else ""
                fields_sql = ', '.join([f'"{field}"' for field in fields])
                
                index_sql = f'CREATE {unique_sql}INDEX IF NOT EXISTS "{index_name}" ON "{table}" ({fields_sql})'
                
                await conn.execute(index_sql)
                return DatabaseResult(success=True, data={"index": index_name, "created": True})
                
        except Exception as e:
            logger.error(f"Error creating index on {table}: {e}")
            return DatabaseResult(success=False, error=str(e))

    async def drop_index(self, table: str, name: str) -> DatabaseResult:
        """Drop an index"""
        try:
            async with self._pool.acquire() as conn:
                await conn.execute(f'DROP INDEX IF EXISTS "{name}"')
                return DatabaseResult(success=True, data={"index": name, "dropped": True})
                
        except Exception as e:
            logger.error(f"Error dropping index on {table}: {e}")
            return DatabaseResult(success=False, error=str(e))