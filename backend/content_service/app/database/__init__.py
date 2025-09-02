# Database Service Module
# Enterprise-grade database abstraction layer

from .base import (
    IDatabaseService,
    DatabaseProvider,
    DatabaseResult, 
    QueryOptions,
    QueryFilter,
    FilterOperation,
    DatabaseException,
    ConnectionException,
    ValidationException,
    NotFoundException,
    DuplicateException,
    TransactionException
)

from .schemas import (
    get_schema,
    get_all_table_names,
    ALL_SCHEMAS,
    FieldType,
    FieldDefinition, 
    TableSchema
)

from .mongodb_service import MongoDBService
from .postgresql_service import PostgreSQLService
from .supabase_service import SupabaseService

from .factory import (
    DatabaseServiceFactory,
    DatabaseConfig,
    DatabaseManager,
    db_manager,
    get_db_service,
    initialize_database,
    initialize_database_from_url,
    close_database
)

__all__ = [
    # Base interfaces
    'IDatabaseService',
    'DatabaseProvider', 
    'DatabaseResult',
    'QueryOptions',
    'QueryFilter',
    'FilterOperation',
    
    # Exceptions
    'DatabaseException',
    'ConnectionException',
    'ValidationException', 
    'NotFoundException',
    'DuplicateException',
    'TransactionException',
    
    # Schema definitions
    'get_schema',
    'get_all_table_names',
    'ALL_SCHEMAS',
    'FieldType',
    'FieldDefinition',
    'TableSchema',
    
    # Service implementations
    'MongoDBService',
    'PostgreSQLService',
    'SupabaseService',
    
    # Factory and management
    'DatabaseServiceFactory',
    'DatabaseConfig',
    'DatabaseManager',
    'db_manager',
    'get_db_service',
    'initialize_database',
    'initialize_database_from_url',
    'close_database'
]