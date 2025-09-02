# Database Service Factory
# Enterprise-grade factory for creating database service instances

import logging
from typing import Optional, Dict, Any
from urllib.parse import urlparse

from .base import IDatabaseService, DatabaseProvider, ConnectionException
from .mongodb_service import MongoDBService
from .postgresql_service import PostgreSQLService  
from .supabase_service import SupabaseService

logger = logging.getLogger(__name__)

class DatabaseServiceFactory:
    """Factory class for creating database service instances"""
    
    @staticmethod
    def create_service(
        provider: DatabaseProvider,
        connection_config: Dict[str, Any]
    ) -> IDatabaseService:
        """
        Create a database service instance based on provider type
        
        Args:
            provider: Database provider type
            connection_config: Provider-specific configuration
            
        Returns:
            IDatabaseService: Database service instance
            
        Raises:
            ConnectionException: If provider is not supported or config is invalid
        """
        try:
            if provider == DatabaseProvider.MONGODB:
                return DatabaseServiceFactory._create_mongodb_service(connection_config)
            elif provider == DatabaseProvider.POSTGRESQL:
                return DatabaseServiceFactory._create_postgresql_service(connection_config)
            elif provider == DatabaseProvider.SUPABASE:
                return DatabaseServiceFactory._create_supabase_service(connection_config)
            else:
                raise ConnectionException(f"Unsupported database provider: {provider}")
                
        except Exception as e:
            logger.error(f"Failed to create database service for {provider}: {e}")
            raise ConnectionException(f"Database service creation failed: {e}")

    @staticmethod
    def _create_mongodb_service(config: Dict[str, Any]) -> MongoDBService:
        """Create MongoDB service instance"""
        connection_string = config.get('connection_string')
        if not connection_string:
            raise ConnectionException("MongoDB connection_string is required")
        
        database_name = config.get('database_name')
        pool_size = config.get('pool_size', 10)
        timeout_seconds = config.get('timeout_seconds', 30)
        
        return MongoDBService(
            connection_string=connection_string,
            database_name=database_name,
            pool_size=pool_size,
            timeout_seconds=timeout_seconds
        )

    @staticmethod
    def _create_postgresql_service(config: Dict[str, Any]) -> PostgreSQLService:
        """Create PostgreSQL service instance"""
        connection_string = config.get('connection_string')
        if not connection_string:
            raise ConnectionException("PostgreSQL connection_string is required")
        
        min_connections = config.get('min_connections', 5)
        max_connections = config.get('max_connections', 20)
        command_timeout = config.get('command_timeout', 60)
        
        return PostgreSQLService(
            connection_string=connection_string,
            min_connections=min_connections,
            max_connections=max_connections,
            command_timeout=command_timeout
        )

    @staticmethod
    def _create_supabase_service(config: Dict[str, Any]) -> SupabaseService:
        """Create Supabase service instance"""
        project_url = config.get('project_url')
        service_key = config.get('service_key')
        
        if not project_url:
            raise ConnectionException("Supabase project_url is required")
        if not service_key:
            raise ConnectionException("Supabase service_key is required")
        
        timeout_seconds = config.get('timeout_seconds', 30)
        
        return SupabaseService(
            project_url=project_url,
            service_key=service_key,
            timeout_seconds=timeout_seconds
        )

    @staticmethod
    def detect_provider_from_url(connection_string: str) -> DatabaseProvider:
        """
        Auto-detect database provider from connection string
        
        Args:
            connection_string: Database connection string
            
        Returns:
            DatabaseProvider: Detected provider type
            
        Raises:
            ConnectionException: If provider cannot be detected
        """
        try:
            parsed = urlparse(connection_string)
            scheme = parsed.scheme.lower()
            
            # MongoDB patterns
            if scheme in ['mongodb', 'mongodb+srv']:
                return DatabaseProvider.MONGODB
            
            # PostgreSQL patterns
            elif scheme in ['postgresql', 'postgres']:
                return DatabaseProvider.POSTGRESQL
            
            # Supabase (typically PostgreSQL with specific domain)
            elif 'supabase' in parsed.hostname.lower() if parsed.hostname else False:
                return DatabaseProvider.SUPABASE
            
            # Generic PostgreSQL fallback
            elif scheme == 'postgresql':
                return DatabaseProvider.POSTGRESQL
            
            else:
                raise ConnectionException(f"Unknown database provider for scheme: {scheme}")
                
        except Exception as e:
            raise ConnectionException(f"Failed to detect database provider: {e}")

    @staticmethod
    def create_from_url(
        connection_string: str,
        additional_config: Optional[Dict[str, Any]] = None
    ) -> IDatabaseService:
        """
        Create database service from connection string (auto-detect provider)
        
        Args:
            connection_string: Database connection string
            additional_config: Additional provider-specific configuration
            
        Returns:
            IDatabaseService: Database service instance
        """
        provider = DatabaseServiceFactory.detect_provider_from_url(connection_string)
        
        config = {'connection_string': connection_string}
        if additional_config:
            config.update(additional_config)
        
        return DatabaseServiceFactory.create_service(provider, config)

class DatabaseConfig:
    """Database configuration helper"""
    
    @staticmethod
    def mongodb_config(
        connection_string: str,
        database_name: Optional[str] = None,
        pool_size: int = 10,
        timeout_seconds: int = 30
    ) -> Dict[str, Any]:
        """Create MongoDB configuration"""
        return {
            'connection_string': connection_string,
            'database_name': database_name,
            'pool_size': pool_size,
            'timeout_seconds': timeout_seconds
        }
    
    @staticmethod
    def postgresql_config(
        connection_string: str,
        min_connections: int = 5,
        max_connections: int = 20,
        command_timeout: int = 60
    ) -> Dict[str, Any]:
        """Create PostgreSQL configuration"""
        return {
            'connection_string': connection_string,
            'min_connections': min_connections,
            'max_connections': max_connections,
            'command_timeout': command_timeout
        }
    
    @staticmethod
    def supabase_config(
        project_url: str,
        service_key: str,
        timeout_seconds: int = 30
    ) -> Dict[str, Any]:
        """Create Supabase configuration"""
        return {
            'project_url': project_url,
            'service_key': service_key,
            'timeout_seconds': timeout_seconds
        }

class DatabaseManager:
    """Global database manager for the application"""
    
    def __init__(self):
        self._service: Optional[IDatabaseService] = None
        self._is_initialized = False
    
    async def initialize(
        self,
        provider: DatabaseProvider,
        connection_config: Dict[str, Any]
    ) -> bool:
        """Initialize database connection"""
        try:
            if self._service:
                await self._service.close()
            
            self._service = DatabaseServiceFactory.create_service(provider, connection_config)
            success = await self._service.initialize()
            
            if success:
                self._is_initialized = True
                logger.info(f"✅ Database manager initialized with {provider.value}")
            else:
                logger.error(f"❌ Failed to initialize database manager with {provider.value}")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Database manager initialization failed: {e}")
            self._service = None
            self._is_initialized = False
            return False
    
    async def initialize_from_url(
        self,
        connection_string: str,
        additional_config: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Initialize database connection from URL (auto-detect provider)"""
        try:
            if self._service:
                await self._service.close()
            
            self._service = DatabaseServiceFactory.create_from_url(
                connection_string, 
                additional_config
            )
            success = await self._service.initialize()
            
            if success:
                self._is_initialized = True
                logger.info(f"✅ Database manager initialized with {self._service.provider.value}")
            else:
                logger.error(f"❌ Failed to initialize database manager")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Database manager initialization failed: {e}")
            self._service = None
            self._is_initialized = False
            return False
    
    @property
    def service(self) -> IDatabaseService:
        """Get the current database service"""
        if not self._service or not self._is_initialized:
            raise ConnectionException("Database manager not initialized")
        return self._service
    
    @property
    def is_initialized(self) -> bool:
        """Check if database manager is initialized"""
        return self._is_initialized
    
    @property
    def provider(self) -> Optional[DatabaseProvider]:
        """Get current database provider"""
        return self._service.provider if self._service else None
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform database health check"""
        if not self._service or not self._is_initialized:
            return {
                "status": "unhealthy",
                "error": "Database manager not initialized"
            }
        
        return await self._service.health_check()
    
    async def close(self) -> None:
        """Close database connections"""
        if self._service:
            await self._service.close()
            self._service = None
            self._is_initialized = False
            logger.info("Database manager closed")

# Global database manager instance
db_manager = DatabaseManager()

def get_db_service() -> IDatabaseService:
    """Get the global database service instance"""
    return db_manager.service

async def initialize_database(
    provider: DatabaseProvider,
    connection_config: Dict[str, Any]
) -> bool:
    """Initialize global database connection"""
    return await db_manager.initialize(provider, connection_config)

async def initialize_database_from_url(
    connection_string: str,
    additional_config: Optional[Dict[str, Any]] = None
) -> bool:
    """Initialize global database connection from URL"""
    return await db_manager.initialize_from_url(connection_string, additional_config)

async def close_database() -> None:
    """Close global database connection"""
    await db_manager.close()