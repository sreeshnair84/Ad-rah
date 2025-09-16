# Copyright (c) 2025 Adara Screen by Hebron
# Owner: Sujesh M S
# All Rights Reserved
#
# This software is proprietary to Adara Screen by Hebron.
# Unauthorized use, reproduction, or distribution is strictly prohibited.

"""
Repository Layer

This module provides the repository pattern implementation for the Adara
Digital Signage Platform, replacing the monolithic repository approach
with domain-specific repositories.

Architecture Benefits:
- Clear separation of concerns
- Domain-driven design principles
- Easier testing and mocking
- Better maintainability
- Consistent database access patterns
"""

from .base_repository import BaseRepository

# Authentication and authorization repositories
from .auth_repository import (
    UserRepository,
    CompanyRepository,
    RoleRepository,
    UserRoleRepository
)

# Content management repositories
from .content_repository import (
    ContentRepository,
    ContentOverlayRepository,
    ContentLayoutRepository,
    ContentDeploymentRepository
)

# Device and hardware repositories
from .device_repository import (
    DeviceRepository,
    DeviceHeartbeatRepository,
    DeviceAnalyticsRepository,
    DeviceRegistrationKeyRepository
)

__all__ = [
    # Base repository
    "BaseRepository",

    # Auth repositories
    "UserRepository",
    "CompanyRepository",
    "RoleRepository",
    "UserRoleRepository",

    # Content repositories
    "ContentRepository",
    "ContentOverlayRepository",
    "ContentLayoutRepository",
    "ContentDeploymentRepository",

    # Device repositories
    "DeviceRepository",
    "DeviceHeartbeatRepository",
    "DeviceAnalyticsRepository",
    "DeviceRegistrationKeyRepository"
]


class RepositoryManager:
    """
    Centralized repository manager for dependency injection

    This class provides a single point of access to all repositories
    and handles database service injection.
    """

    def __init__(self, db_service):
        self.db_service = db_service
        self._repositories = {}

    def get_repository(self, repository_class):
        """Get a repository instance with automatic caching"""
        repo_name = repository_class.__name__

        if repo_name not in self._repositories:
            self._repositories[repo_name] = repository_class(self.db_service)

        return self._repositories[repo_name]

    # Convenience properties for commonly used repositories
    @property
    def users(self) -> UserRepository:
        return self.get_repository(UserRepository)

    @property
    def companies(self) -> CompanyRepository:
        return self.get_repository(CompanyRepository)

    @property
    def content(self) -> ContentRepository:
        return self.get_repository(ContentRepository)

    @property
    def devices(self) -> DeviceRepository:
        return self.get_repository(DeviceRepository)

    @property
    def device_analytics(self) -> DeviceAnalyticsRepository:
        return self.get_repository(DeviceAnalyticsRepository)

    @property
    def overlays(self) -> ContentOverlayRepository:
        return self.get_repository(ContentOverlayRepository)

    @property
    def layouts(self) -> ContentLayoutRepository:
        return self.get_repository(ContentLayoutRepository)

    @property
    def deployments(self) -> ContentDeploymentRepository:
        return self.get_repository(ContentDeploymentRepository)

    @property
    def roles(self) -> RoleRepository:
        return self.get_repository(RoleRepository)

    @property
    def user_roles(self) -> UserRoleRepository:
        return self.get_repository(UserRoleRepository)

    @property
    def heartbeats(self) -> DeviceHeartbeatRepository:
        return self.get_repository(DeviceHeartbeatRepository)

    @property
    def registration_keys(self) -> DeviceRegistrationKeyRepository:
        return self.get_repository(DeviceRegistrationKeyRepository)


# Global repository manager instance (will be initialized with db_service)
repo_manager: Optional[RepositoryManager] = None


def initialize_repositories(db_service):
    """Initialize the global repository manager"""
    global repo_manager
    repo_manager = RepositoryManager(db_service)
    return repo_manager


def get_repo_manager() -> RepositoryManager:
    """Get the global repository manager instance"""
    if repo_manager is None:
        raise RuntimeError("Repository manager not initialized. Call initialize_repositories() first.")
    return repo_manager