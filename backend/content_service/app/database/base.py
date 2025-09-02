# Database Service Interface Layer
# Enterprise-grade database abstraction for multi-database support

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

# Database Provider Types
class DatabaseProvider(str, Enum):
    MONGODB = "mongodb"
    POSTGRESQL = "postgresql"
    SUPABASE = "supabase"
    INMEMORY = "inmemory"  # For testing/development

# Query Operation Types
class QueryOperation(str, Enum):
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"
    COUNT = "count"
    EXISTS = "exists"

# Filter Operations for Complex Queries
class FilterOperation(str, Enum):
    EQUALS = "eq"
    NOT_EQUALS = "neq"
    GREATER_THAN = "gt"
    GREATER_THAN_EQUAL = "gte"
    LESS_THAN = "lt"
    LESS_THAN_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    STARTS_WITH = "starts_with"
    ENDS_WITH = "ends_with"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"

class QueryFilter:
    """Represents a filter condition for database queries"""
    def __init__(self, field: str, operation: FilterOperation, value: Any = None):
        self.field = field
        self.operation = operation
        self.value = value

class QueryOptions:
    """Options for database queries"""
    def __init__(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort_by: Optional[str] = None,
        sort_desc: bool = False,
        filters: Optional[List[QueryFilter]] = None,
        include_related: Optional[List[str]] = None
    ):
        self.limit = limit
        self.offset = offset
        self.sort_by = sort_by
        self.sort_desc = sort_desc
        self.filters = filters or []
        self.include_related = include_related or []

class DatabaseResult:
    """Standardized result wrapper for database operations"""
    def __init__(
        self,
        success: bool,
        data: Any = None,
        error: Optional[str] = None,
        count: Optional[int] = None,
        metadata: Optional[Dict] = None
    ):
        self.success = success
        self.data = data
        self.error = error
        self.count = count
        self.metadata = metadata or {}

class IDatabaseService(ABC):
    """
    Abstract base class for database services.
    Provides a unified interface for different database providers.
    """

    @property
    @abstractmethod
    def provider(self) -> DatabaseProvider:
        """Return the database provider type"""
        pass

    @abstractmethod
    async def initialize(self) -> bool:
        """Initialize the database connection and schema"""
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """Check database health and return status"""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close database connections"""
        pass

    # Generic CRUD Operations
    @abstractmethod
    async def create_record(
        self,
        table: str,
        data: Dict[str, Any],
        return_record: bool = True
    ) -> DatabaseResult:
        """Create a new record"""
        pass

    @abstractmethod
    async def get_record(
        self,
        table: str,
        record_id: str,
        include_related: Optional[List[str]] = None
    ) -> DatabaseResult:
        """Get a record by ID"""
        pass

    @abstractmethod
    async def update_record(
        self,
        table: str,
        record_id: str,
        data: Dict[str, Any],
        return_record: bool = True
    ) -> DatabaseResult:
        """Update a record by ID"""
        pass

    @abstractmethod
    async def delete_record(
        self,
        table: str,
        record_id: str
    ) -> DatabaseResult:
        """Delete a record by ID"""
        pass

    @abstractmethod
    async def list_records(
        self,
        table: str,
        options: Optional[QueryOptions] = None
    ) -> DatabaseResult:
        """List records with optional filtering, sorting, and pagination"""
        pass

    @abstractmethod
    async def count_records(
        self,
        table: str,
        filters: Optional[List[QueryFilter]] = None
    ) -> DatabaseResult:
        """Count records matching filters"""
        pass

    @abstractmethod
    async def record_exists(
        self,
        table: str,
        record_id: str
    ) -> DatabaseResult:
        """Check if a record exists"""
        pass

    # Advanced Query Operations
    @abstractmethod
    async def find_records(
        self,
        table: str,
        filters: List[QueryFilter],
        options: Optional[QueryOptions] = None
    ) -> DatabaseResult:
        """Find records using complex filter conditions"""
        pass

    @abstractmethod
    async def find_one_record(
        self,
        table: str,
        filters: List[QueryFilter],
        include_related: Optional[List[str]] = None
    ) -> DatabaseResult:
        """Find single record using filter conditions"""
        pass

    # Batch Operations
    @abstractmethod
    async def batch_create(
        self,
        table: str,
        records: List[Dict[str, Any]]
    ) -> DatabaseResult:
        """Create multiple records in a single operation"""
        pass

    @abstractmethod
    async def batch_update(
        self,
        table: str,
        updates: List[Dict[str, Any]]  # Each dict should contain 'id' and update fields
    ) -> DatabaseResult:
        """Update multiple records in a single operation"""
        pass

    @abstractmethod
    async def batch_delete(
        self,
        table: str,
        record_ids: List[str]
    ) -> DatabaseResult:
        """Delete multiple records in a single operation"""
        pass

    # Transaction Support
    @abstractmethod
    async def execute_transaction(
        self,
        operations: List[Dict[str, Any]]
    ) -> DatabaseResult:
        """Execute multiple operations in a transaction"""
        pass

    # Schema Operations
    @abstractmethod
    async def create_table(
        self,
        table: str,
        schema: Dict[str, Any]
    ) -> DatabaseResult:
        """Create a table with specified schema"""
        pass

    @abstractmethod
    async def table_exists(
        self,
        table: str
    ) -> DatabaseResult:
        """Check if a table exists"""
        pass

    @abstractmethod
    async def get_table_schema(
        self,
        table: str
    ) -> DatabaseResult:
        """Get table schema information"""
        pass

    # Indexing Operations
    @abstractmethod
    async def create_index(
        self,
        table: str,
        fields: List[str],
        unique: bool = False,
        name: Optional[str] = None
    ) -> DatabaseResult:
        """Create an index on specified fields"""
        pass

    @abstractmethod
    async def drop_index(
        self,
        table: str,
        name: str
    ) -> DatabaseResult:
        """Drop an index"""
        pass

    # Utility Methods
    def generate_id(self) -> str:
        """Generate a unique ID for new records"""
        import uuid
        return str(uuid.uuid4())

    def current_timestamp(self) -> datetime:
        """Get current timestamp"""
        return datetime.utcnow()

    async def upsert_record(
        self,
        table: str,
        data: Dict[str, Any],
        unique_fields: List[str]
    ) -> DatabaseResult:
        """Insert or update record based on unique fields"""
        # Build filters for unique fields
        filters = [
            QueryFilter(field, FilterOperation.EQUALS, data.get(field))
            for field in unique_fields
            if field in data
        ]
        
        # Check if record exists
        existing = await self.find_one_record(table, filters)
        
        if existing.success and existing.data:
            # Update existing record
            record_id = existing.data.get('id')
            return await self.update_record(table, record_id, data)
        else:
            # Create new record
            return await self.create_record(table, data)

    async def get_records_by_field(
        self,
        table: str,
        field: str,
        value: Any,
        options: Optional[QueryOptions] = None
    ) -> DatabaseResult:
        """Helper method to get records by a specific field value"""
        filters = [QueryFilter(field, FilterOperation.EQUALS, value)]
        return await self.find_records(table, filters, options)

    async def soft_delete_record(
        self,
        table: str,
        record_id: str
    ) -> DatabaseResult:
        """Soft delete by setting deleted_at timestamp"""
        update_data = {
            "deleted_at": self.current_timestamp(),
            "is_deleted": True
        }
        return await self.update_record(table, record_id, update_data)

class DatabaseException(Exception):
    """Base exception for database operations"""
    def __init__(self, message: str, provider: str = None, operation: str = None):
        super().__init__(message)
        self.provider = provider
        self.operation = operation

class ConnectionException(DatabaseException):
    """Exception for database connection issues"""
    pass

class ValidationException(DatabaseException):
    """Exception for data validation issues"""
    pass

class NotFoundException(DatabaseException):
    """Exception for record not found"""
    pass

class DuplicateException(DatabaseException):
    """Exception for duplicate record creation"""
    pass

class TransactionException(DatabaseException):
    """Exception for transaction failures"""
    pass