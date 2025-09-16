"""
Base Service Class for Clean Architecture Pattern
================================================

This module provides the foundation for all business logic services in the platform.
It implements dependency injection, logging, and error handling patterns.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, TypeVar, Generic
from datetime import datetime
import logging
from functools import wraps

from app.database_service import db_service
from app.repo import repo

T = TypeVar('T')


class ServiceException(Exception):
    """Base exception for service layer errors"""

    def __init__(self, message: str, error_code: str = None, details: Dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ServiceException):
    """Raised when service validation fails"""
    pass


class NotFoundError(ServiceException):
    """Raised when a requested resource is not found"""
    pass


class PermissionError(ServiceException):
    """Raised when user lacks required permissions"""
    pass


def log_service_call(func):
    """Decorator to log service method calls"""
    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        service_name = self.__class__.__name__
        method_name = func.__name__

        self.logger.info(f"{service_name}.{method_name} called with args: {args}, kwargs: {kwargs}")

        start_time = datetime.utcnow()
        try:
            result = await func(self, *args, **kwargs)
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.info(f"{service_name}.{method_name} completed in {duration:.3f}s")
            return result
        except Exception as e:
            duration = (datetime.utcnow() - start_time).total_seconds()
            self.logger.error(f"{service_name}.{method_name} failed after {duration:.3f}s: {str(e)}")
            raise

    return wrapper


class BaseService(ABC):
    """
    Abstract base class for all business services

    Provides:
    - Dependency injection for database and repository
    - Standardized logging
    - Error handling patterns
    - Validation helpers
    - Transaction management
    """

    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
        self._db = None
        self._repo = None

    @property
    def db(self):
        """Lazy-loaded database service"""
        if self._db is None:
            self._db = db_service
        return self._db

    @property
    def repo(self):
        """Lazy-loaded repository service"""
        if self._repo is None:
            self._repo = repo
        return self._repo

    def validate_required_fields(self, data: Dict, required_fields: List[str]):
        """Validate that all required fields are present and not empty"""
        missing_fields = []
        empty_fields = []

        for field in required_fields:
            if field not in data:
                missing_fields.append(field)
            elif not data[field] or (isinstance(data[field], str) and not data[field].strip()):
                empty_fields.append(field)

        if missing_fields or empty_fields:
            error_details = {}
            if missing_fields:
                error_details["missing_fields"] = missing_fields
            if empty_fields:
                error_details["empty_fields"] = empty_fields

            raise ValidationError(
                f"Validation failed: {', '.join(missing_fields + empty_fields)}",
                error_code="VALIDATION_ERROR",
                details=error_details
            )

    def validate_permissions(self, user_permissions: List[str], required_permission: str):
        """Check if user has required permission"""
        if required_permission not in user_permissions:
            raise PermissionError(
                f"Permission '{required_permission}' required",
                error_code="INSUFFICIENT_PERMISSIONS",
                details={"required": required_permission, "user_permissions": user_permissions}
            )

    def validate_company_access(self, user_company_id: str, resource_company_id: str, user_type: str = None):
        """Validate user can access company-scoped resources"""
        if user_type == "SUPER_USER":
            return  # Super users bypass company checks

        if user_company_id != resource_company_id:
            raise PermissionError(
                "Access denied: Resource belongs to different company",
                error_code="COMPANY_ACCESS_DENIED",
                details={
                    "user_company_id": user_company_id,
                    "resource_company_id": resource_company_id
                }
            )

    async def get_user_context(self, user_id: str) -> Dict:
        """Get comprehensive user context for authorization"""
        user = await self.repo.get_user_by_id(user_id)
        if not user:
            raise NotFoundError(f"User {user_id} not found", error_code="USER_NOT_FOUND")

        return {
            "user_id": user.id,
            "user_type": user.user_type,
            "company_id": user.company_id,
            "permissions": user.permissions or [],
            "is_active": user.status == "active"
        }

    def handle_service_error(self, error: Exception, context: str) -> ServiceException:
        """Convert generic exceptions to service exceptions"""
        if isinstance(error, ServiceException):
            return error

        self.logger.error(f"Unexpected error in {context}: {str(error)}")
        return ServiceException(
            f"Service error in {context}",
            error_code="INTERNAL_SERVICE_ERROR",
            details={"original_error": str(error)}
        )


class CRUDService(BaseService, Generic[T]):
    """
    Generic CRUD service providing common create, read, update, delete operations
    """

    @abstractmethod
    def get_model_name(self) -> str:
        """Return the name of the model this service manages"""
        pass

    @abstractmethod
    async def create(self, data: Dict, user_context: Dict) -> T:
        """Create a new entity"""
        pass

    @abstractmethod
    async def get_by_id(self, entity_id: str, user_context: Dict) -> Optional[T]:
        """Get entity by ID"""
        pass

    @abstractmethod
    async def update(self, entity_id: str, data: Dict, user_context: Dict) -> T:
        """Update an existing entity"""
        pass

    @abstractmethod
    async def delete(self, entity_id: str, user_context: Dict) -> bool:
        """Delete an entity"""
        pass

    @abstractmethod
    async def list(self, filters: Dict, user_context: Dict) -> List[T]:
        """List entities with filters"""
        pass


class CompanyAwareService(BaseService):
    """
    Service mixin for company-scoped operations
    Ensures proper multi-tenant isolation
    """

    def filter_by_company(self, query_filters: Dict, user_context: Dict) -> Dict:
        """Add company filtering to query"""
        if user_context.get("user_type") != "SUPER_USER":
            # Non-super users can only see their company's data
            query_filters["company_id"] = user_context["company_id"]

        return query_filters

    def validate_company_permission(self, user_context: Dict, action: str, resource_company_id: str = None):
        """Validate user can perform action on company resource"""
        user_type = user_context.get("user_type")
        user_company_id = user_context.get("company_id")

        # Super users can access everything
        if user_type == "SUPER_USER":
            return

        # Company users can only access their own company's resources
        if resource_company_id and user_company_id != resource_company_id:
            raise PermissionError(
                f"Cannot {action} resource from different company",
                error_code="CROSS_COMPANY_ACCESS_DENIED"
            )


class AuditableService(BaseService):
    """
    Service mixin for operations that require audit logging
    """

    async def log_audit_event(self,
                             action: str,
                             resource_type: str,
                             resource_id: str,
                             user_context: Dict,
                             details: Dict = None):
        """Log an audit event"""
        try:
            from app.history_service import history_service

            audit_data = {
                "action": action,
                "resource_type": resource_type,
                "resource_id": resource_id,
                "user_id": user_context.get("user_id"),
                "company_id": user_context.get("company_id"),
                "timestamp": datetime.utcnow(),
                "details": details or {}
            }

            await history_service.log_audit_event(audit_data)

        except Exception as e:
            # Don't fail the operation if audit logging fails
            self.logger.warning(f"Failed to log audit event: {e}")


# Service registry for dependency injection
class ServiceRegistry:
    """Simple service registry for dependency injection"""

    _services: Dict[str, Any] = {}

    @classmethod
    def register(cls, service_name: str, service_instance: Any):
        """Register a service instance"""
        cls._services[service_name] = service_instance

    @classmethod
    def get(cls, service_name: str) -> Any:
        """Get a registered service"""
        return cls._services.get(service_name)

    @classmethod
    def clear(cls):
        """Clear all registered services (for testing)"""
        cls._services.clear()


# Initialize service registry
service_registry = ServiceRegistry()