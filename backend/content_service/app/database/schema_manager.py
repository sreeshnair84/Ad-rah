# Database Schema Manager
# Universal schema creation and management across different databases

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .base import IDatabaseService, DatabaseProvider, DatabaseResult
from .schemas import get_all_table_names, get_schema, ALL_SCHEMAS, FieldType

logger = logging.getLogger(__name__)

class SchemaManager:
    """Universal schema management for different database providers"""
    
    def __init__(self, db_service: IDatabaseService):
        self.db = db_service
        self.provider = db_service.provider
    
    async def create_all_tables(self) -> DatabaseResult:
        """Create all tables for the current database provider"""
        try:
            logger.info(f"🔧 Creating database schema for {self.provider.value}")
            
            results = []
            
            # Create tables in dependency order
            table_order = self._get_table_creation_order()
            
            for table_name in table_order:
                result = await self.create_table(table_name)
                results.append({
                    "table": table_name,
                    "success": result.success,
                    "error": result.error if not result.success else None
                })
                
                if result.success:
                    logger.info(f"✅ Created table: {table_name}")
                else:
                    logger.error(f"❌ Failed to create table {table_name}: {result.error}")
            
            # Create indexes
            await self._create_all_indexes()
            
            # Create initial system data
            await self._create_system_data()
            
            success_count = sum(1 for r in results if r["success"])
            total_count = len(results)
            
            logger.info(f"📊 Schema creation complete: {success_count}/{total_count} tables created")
            
            return DatabaseResult(
                success=success_count == total_count,
                data={
                    "provider": self.provider.value,
                    "tables_created": success_count,
                    "total_tables": total_count,
                    "results": results
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Schema creation failed: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def create_table(self, table_name: str) -> DatabaseResult:
        """Create a single table based on provider"""
        try:
            schema = get_schema(table_name)
            if not schema:
                return DatabaseResult(success=False, error=f"Schema not found for table: {table_name}")
            
            # Check if table already exists
            exists_result = await self.db.table_exists(table_name)
            if exists_result.success and exists_result.data:
                logger.info(f"📋 Table {table_name} already exists, skipping")
                return DatabaseResult(success=True, data={"table": table_name, "status": "exists"})
            
            if self.provider == DatabaseProvider.MONGODB:
                return await self._create_mongodb_collection(table_name, schema)
            elif self.provider == DatabaseProvider.POSTGRESQL:
                return await self._create_postgresql_table(table_name, schema)
            elif self.provider == DatabaseProvider.SUPABASE:
                return await self._create_supabase_table(table_name, schema)
            else:
                return DatabaseResult(success=False, error=f"Unsupported provider: {self.provider}")
                
        except Exception as e:
            logger.error(f"Error creating table {table_name}: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def _create_mongodb_collection(self, table_name: str, schema) -> DatabaseResult:
        """Create MongoDB collection with validation and indexes"""
        try:
            # MongoDB creates collections automatically on first insert
            # We'll create validation rules and indexes
            
            # For MongoDB, we can create the collection by inserting a dummy document and removing it
            dummy_doc = {"_temp": True, "created_at": datetime.utcnow()}
            result = await self.db.create_record(table_name, dummy_doc, return_record=False)
            
            if result.success:
                # Remove dummy document
                from .base import QueryFilter, FilterOperation
                filters = [QueryFilter("_temp", FilterOperation.EQUALS, True)]
                dummy_result = await self.db.find_one_record(table_name, filters)
                if dummy_result.success:
                    await self.db.delete_record(table_name, dummy_result.data["id"])
                
                logger.info(f"✅ MongoDB collection {table_name} created")
                return DatabaseResult(success=True, data={"table": table_name, "provider": "mongodb"})
            else:
                return result
                
        except Exception as e:
            logger.error(f"Error creating MongoDB collection {table_name}: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def _create_postgresql_table(self, table_name: str, schema) -> DatabaseResult:
        """Create PostgreSQL table with proper schema"""
        try:
            # PostgreSQL table creation is handled by the PostgreSQL service
            return await self.db.create_table(table_name, schema.__dict__)
            
        except Exception as e:
            logger.error(f"Error creating PostgreSQL table {table_name}: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def _create_supabase_table(self, table_name: str, schema) -> DatabaseResult:
        """Create Supabase table (requires SQL execution - limited via REST API)"""
        try:
            # Supabase table creation typically requires SQL migration files
            # For now, we'll assume tables exist or are created via Supabase dashboard
            logger.warning(f"⚠️ Supabase table creation requires manual SQL migration for: {table_name}")
            return DatabaseResult(success=True, data={"table": table_name, "status": "manual_required"})
            
        except Exception as e:
            logger.error(f"Error with Supabase table {table_name}: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def _create_all_indexes(self) -> None:
        """Create indexes for all tables"""
        try:
            logger.info("🔍 Creating database indexes...")
            
            for table_name in get_all_table_names():
                schema = get_schema(table_name)
                if not schema or not schema.indexes:
                    continue
                
                for index_config in schema.indexes:
                    fields = index_config.get('fields', [])
                    unique = index_config.get('unique', False)
                    
                    if fields:
                        result = await self.db.create_index(table_name, fields, unique)
                        if result.success:
                            logger.debug(f"✅ Created index on {table_name}: {fields}")
                        else:
                            logger.warning(f"⚠️ Index creation failed on {table_name}: {result.error}")
            
            logger.info("✅ Index creation complete")
            
        except Exception as e:
            logger.error(f"❌ Index creation failed: {e}")
    
    async def _create_system_data(self) -> None:
        """Create essential system data"""
        try:
            logger.info("🔧 Creating system data...")
            
            # Create permission templates
            await self._create_permission_templates()
            
            logger.info("✅ System data creation complete")
            
        except Exception as e:
            logger.error(f"❌ System data creation failed: {e}")
    
    async def _create_permission_templates(self) -> None:
        """Create default permission templates"""
        try:
            from app.rbac.permissions import DEFAULT_ROLE_TEMPLATES, PermissionManager
            
            for role, template in DEFAULT_ROLE_TEMPLATES.items():
                template_data = {
                    "name": f"Default {template.name}",
                    "role": role.value,
                    "permissions": PermissionManager.serialize_permissions(template.page_permissions),
                    "description": template.description,
                    "is_system": True,
                    "company_id": None
                }
                
                # Check if template already exists
                from .base import QueryFilter, FilterOperation
                filters = [
                    QueryFilter("role", FilterOperation.EQUALS, role.value),
                    QueryFilter("is_system", FilterOperation.EQUALS, True)
                ]
                
                existing = await self.db.find_one_record("permission_templates", filters)
                if not existing.success:
                    result = await self.db.create_record("permission_templates", template_data)
                    if result.success:
                        logger.info(f"✅ Created permission template: {role.value}")
                    else:
                        logger.warning(f"⚠️ Failed to create permission template: {role.value}")
                
        except Exception as e:
            logger.error(f"Error creating permission templates: {e}")
    
    def _get_table_creation_order(self) -> List[str]:
        """Get table creation order respecting dependencies"""
        # Define table dependencies (tables that must exist before others)
        dependencies = {
            "companies": [],
            "users": [],
            "permission_templates": [],
            "user_company_roles": ["users", "companies"],
            "content": ["users", "companies"],
            "devices": ["companies"],
            "content_schedule": ["content", "devices", "companies"],
            "analytics_events": ["users", "companies", "devices", "content"],
            "audit_log": ["users", "companies"]
        }
        
        # Topological sort
        ordered = []
        remaining = set(get_all_table_names())
        
        while remaining:
            # Find tables with no remaining dependencies
            ready = []
            for table in remaining:
                deps = dependencies.get(table, [])
                if all(dep in ordered for dep in deps):
                    ready.append(table)
            
            if not ready:
                # Add remaining tables (circular dependency or missing dependency)
                ready = list(remaining)
            
            # Add ready tables to ordered list
            for table in ready:
                ordered.append(table)
                remaining.remove(table)
        
        return ordered
    
    async def drop_all_tables(self) -> DatabaseResult:
        """Drop all tables (use with caution!)"""
        try:
            logger.warning("🚨 DROPPING ALL TABLES - THIS WILL DELETE ALL DATA!")
            
            results = []
            
            # Drop tables in reverse dependency order
            table_order = list(reversed(self._get_table_creation_order()))
            
            for table_name in table_order:
                if self.provider == DatabaseProvider.MONGODB:
                    # For MongoDB, we can delete the collection
                    result = await self._drop_mongodb_collection(table_name)
                else:
                    # For SQL databases, we need proper DROP TABLE
                    result = await self._drop_sql_table(table_name)
                
                results.append({
                    "table": table_name,
                    "success": result.success,
                    "error": result.error if not result.success else None
                })
                
                if result.success:
                    logger.info(f"🗑️ Dropped table: {table_name}")
                else:
                    logger.warning(f"⚠️ Failed to drop table {table_name}: {result.error}")
            
            success_count = sum(1 for r in results if r["success"])
            total_count = len(results)
            
            return DatabaseResult(
                success=True,  # Continue even if some drops fail
                data={
                    "tables_dropped": success_count,
                    "total_tables": total_count,
                    "results": results
                }
            )
            
        except Exception as e:
            logger.error(f"❌ Drop tables failed: {e}")
            return DatabaseResult(success=False, error=str(e))
    
    async def _drop_mongodb_collection(self, table_name: str) -> DatabaseResult:
        """Drop MongoDB collection"""
        try:
            # MongoDB doesn't have a direct drop collection in our interface
            # We'll clear all documents instead
            from .base import QueryFilter, FilterOperation
            
            # List all records and delete them
            all_records = await self.db.list_records(table_name)
            if all_records.success and all_records.data:
                record_ids = [record["id"] for record in all_records.data]
                if record_ids:
                    await self.db.batch_delete(table_name, record_ids)
            
            return DatabaseResult(success=True, data={"table": table_name})
            
        except Exception as e:
            return DatabaseResult(success=False, error=str(e))
    
    async def _drop_sql_table(self, table_name: str) -> DatabaseResult:
        """Drop SQL table"""
        try:
            # This would require raw SQL execution which our interface doesn't support
            # For now, we'll just clear the table
            logger.warning(f"⚠️ Cannot drop SQL table {table_name} - clearing data instead")
            return await self._drop_mongodb_collection(table_name)
            
        except Exception as e:
            return DatabaseResult(success=False, error=str(e))
    
    async def get_schema_info(self) -> DatabaseResult:
        """Get information about the current database schema"""
        try:
            info = {
                "provider": self.provider.value,
                "tables": [],
                "total_tables": len(get_all_table_names())
            }
            
            for table_name in get_all_table_names():
                schema = get_schema(table_name)
                exists_result = await self.db.table_exists(table_name)
                
                table_info = {
                    "name": table_name,
                    "exists": exists_result.data if exists_result.success else False,
                    "fields": len(schema.fields) if schema else 0,
                    "indexes": len(schema.indexes) if schema and schema.indexes else 0,
                    "description": schema.description if schema else None
                }
                
                # Get record count if table exists
                if table_info["exists"]:
                    count_result = await self.db.count_records(table_name)
                    table_info["record_count"] = count_result.data if count_result.success else 0
                else:
                    table_info["record_count"] = 0
                
                info["tables"].append(table_info)
            
            info["existing_tables"] = sum(1 for t in info["tables"] if t["exists"])
            info["total_records"] = sum(t["record_count"] for t in info["tables"])
            
            return DatabaseResult(success=True, data=info)
            
        except Exception as e:
            logger.error(f"Error getting schema info: {e}")
            return DatabaseResult(success=False, error=str(e))