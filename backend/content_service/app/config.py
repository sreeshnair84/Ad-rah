import os
import secrets
import logging
import asyncio
from typing import Optional
from dotenv import load_dotenv
from app.security.key_vault_service import KeyVaultService

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

def _generate_secret_key() -> str:
    """Generate a secure secret key if none is provided"""
    return secrets.token_urlsafe(32)

def _validate_secret_key(secret_key: str) -> str:
    """Validate and return a secure secret key"""
    if not secret_key or secret_key in [
        "CHANGE_ME_REPLACE_WITH_SECURE_SECRET", 
        "your-secure-secret-key-here",
        "change-me",
        "secret",
        "development"
    ]:
        if os.getenv("ENVIRONMENT", "development").lower() == "production":
            raise ValueError(
                "CRITICAL SECURITY ERROR: Insecure or default SECRET_KEY detected in production! "
                "Please set a secure SECRET_KEY environment variable."
            )
        else:
            logger.warning(
                "WARNING: Using default SECRET_KEY in development. "
                "This is NOT secure for production use!"
            )
            return _generate_secret_key()
    
    if len(secret_key) < 32:
        logger.warning(
            f"WARNING: SECRET_KEY length ({len(secret_key)}) is shorter than recommended minimum (32 characters)"
        )
    
    return secret_key

class EnhancedConfig:
    """Enhanced application configuration with Azure Key Vault integration"""
    
    def __init__(self):
        # Initialize Key Vault service
        self.key_vault_service = None
        self._initialize_key_vault()
        
        # Environment configuration
        self.ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
        
        # Database
        self.MONGO_URI = os.getenv("MONGO_URI")
        
        # JWT Configuration - will be loaded from Key Vault or environment
        self.JWT_SECRET_KEY = None
        self.JWT_REFRESH_SECRET_KEY = None
        self.JWT_ALGORITHM = "HS256"
        self.ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
        self.REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
        
        # Azure Configuration
        self.AZURE_STORAGE_CONNECTION_STRING = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.AZURE_CONTAINER_NAME = os.getenv("AZURE_CONTAINER_NAME", "openkiosk-media")
        self.LOCAL_MEDIA_DIR = os.getenv("LOCAL_MEDIA_DIR", "./data/media")
        
        # Azure AI Content Safety
        self.AZURE_AI_ENDPOINT = os.getenv("AZURE_AI_ENDPOINT")
        self.AZURE_AI_KEY = os.getenv("AZURE_AI_KEY")
        
        # Azure Service Bus
        self.SERVICE_BUS_CONNECTION_STRING = os.getenv("SERVICE_BUS_CONNECTION_STRING")
        
        # Azure Key Vault Configuration
        self.AZURE_KEY_VAULT_URL = os.getenv("AZURE_KEY_VAULT_URL")
        self.AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
        self.AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET")
        self.AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID")
        
        # Redis Configuration (for token management)
        self.REDIS_URL = os.getenv("REDIS_URL")
        
        # Security Configuration
        self.ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")
        self.ENABLE_SECURITY_HEADERS = os.getenv("ENABLE_SECURITY_HEADERS", "true").lower() == "true"
        self.ENABLE_RATE_LIMITING = os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true"
        
        # Content Security
        self.CONTENT_MAX_SIZE_MB = int(os.getenv("CONTENT_MAX_SIZE_MB", "100"))
        self.ALLOWED_FILE_TYPES = os.getenv("ALLOWED_FILE_TYPES", "jpg,jpeg,png,gif,webp,mp4,avi,mov,txt,json")
        self.CONTENT_SCAN_ENABLED = os.getenv("CONTENT_SCAN_ENABLED", "true").lower() == "true"
        self.COPYRIGHT_CHECK_ENABLED = os.getenv("COPYRIGHT_CHECK_ENABLED", "true").lower() == "true"
        
        # Rate Limiting
        self.RATE_LIMIT_REQUESTS_PER_MINUTE = int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "100"))
        self.RATE_LIMIT_UPLOADS_PER_HOUR = int(os.getenv("RATE_LIMIT_UPLOADS_PER_HOUR", "10"))
        
        # Compliance
        self.DATA_ENCRYPTION_ENABLED = os.getenv("DATA_ENCRYPTION_ENABLED", "true").lower() == "true"
        self.AUDIT_LOGGING_ENABLED = os.getenv("AUDIT_LOGGING_ENABLED", "true").lower() == "true"
        self.GDPR_COMPLIANCE_MODE = os.getenv("GDPR_COMPLIANCE_MODE", "true").lower() == "true"
        self.DATA_RETENTION_DAYS = int(os.getenv("DATA_RETENTION_DAYS", "365"))
        
        # Device Security
        self.DEVICE_CERTIFICATE_VALIDATION = os.getenv("DEVICE_CERTIFICATE_VALIDATION", "true").lower() == "true"
        self.WEBSOCKET_MESSAGE_VALIDATION = os.getenv("WEBSOCKET_MESSAGE_VALIDATION", "strict")
        self.DEVICE_HEARTBEAT_TIMEOUT_SECONDS = int(os.getenv("DEVICE_HEARTBEAT_TIMEOUT_SECONDS", "300"))
        
        # Local development settings
        self.USE_LOCAL_EVENT_PROCESSOR = os.getenv("USE_LOCAL_EVENT_PROCESSOR", "true").lower() == "true"
        self.EVENT_PROCESSOR_QUEUE_SIZE = int(os.getenv("EVENT_PROCESSOR_QUEUE_SIZE", "100"))
        
        # CORS Configuration
        self.ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")
        self.ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "").split(",") if os.getenv("ALLOWED_HOSTS") else []
        
        # Logging
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        
        # Track initialization state
        self._secrets_initialized = False
    
    def _initialize_key_vault(self):
        """Initialize Key Vault service if configured"""
        key_vault_url = os.getenv("AZURE_KEY_VAULT_URL")
        
        if key_vault_url:
            try:
                self.key_vault_service = KeyVaultService()
                logger.info("Key Vault service initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize Key Vault: {e}")
                self.key_vault_service = None
        else:
            logger.info("Azure Key Vault URL not configured, using environment variables")
    
    async def initialize_secrets(self):
        """Initialize secrets from Key Vault or environment variables"""
        if self._secrets_initialized:
            return
        
        try:
            if self.key_vault_service:
                # Initialize the Key Vault connection first
                await self.key_vault_service.initialize()
                await self._load_secrets_from_key_vault()
            else:
                await self._load_secrets_from_environment()
            
            self._secrets_initialized = True
            logger.info("Secrets initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize secrets: {e}")
            # Fallback to environment variables
            await self._load_secrets_from_environment()
            self._secrets_initialized = True
    
    async def _load_secrets_from_key_vault(self):
        """Load secrets from Azure Key Vault"""
        if not self.key_vault_service:
            raise ValueError("Key Vault service not initialized")
            
        try:
            # Load JWT secrets
            self.JWT_SECRET_KEY = await self.key_vault_service.get_secret("jwt-secret-key")
            if not self.JWT_SECRET_KEY:
                self.JWT_SECRET_KEY = self._generate_fallback_secret()
                logger.warning("JWT secret not found in Key Vault, using generated fallback")
            
            self.JWT_REFRESH_SECRET_KEY = await self.key_vault_service.get_secret("jwt-refresh-secret-key")
            if not self.JWT_REFRESH_SECRET_KEY:
                self.JWT_REFRESH_SECRET_KEY = self._generate_fallback_secret()
                logger.warning("JWT refresh secret not found in Key Vault, using generated fallback")
            
            # Load encryption key
            if not self.ENCRYPTION_KEY:
                self.ENCRYPTION_KEY = await self.key_vault_service.get_secret("encryption-key")
                if not self.ENCRYPTION_KEY:
                    self.ENCRYPTION_KEY = self._generate_fallback_secret()
                    logger.warning("Encryption key not found in Key Vault, using generated fallback")
            
            # Load Azure AI key if not in environment
            if not self.AZURE_AI_KEY:
                self.AZURE_AI_KEY = await self.key_vault_service.get_secret("azure-ai-content-safety-key")
            
            # Load Azure Storage connection string if not in environment
            if not self.AZURE_STORAGE_CONNECTION_STRING:
                self.AZURE_STORAGE_CONNECTION_STRING = await self.key_vault_service.get_secret(
                    "azure-storage-connection-string"
                )
            
            # Load MongoDB connection string from Key Vault if available
            vault_mongodb_url = await self.key_vault_service.get_secret("mongodb-connection-string")
            if vault_mongodb_url:
                self.MONGO_URI = vault_mongodb_url
            
            # Load Service Bus connection string if not in environment
            if not self.SERVICE_BUS_CONNECTION_STRING:
                self.SERVICE_BUS_CONNECTION_STRING = await self.key_vault_service.get_secret(
                    "service-bus-connection-string"
                )
            
            logger.info("Secrets loaded from Azure Key Vault")
            
        except Exception as e:
            logger.error(f"Failed to load secrets from Key Vault: {e}")
            raise
    
    async def _load_secrets_from_environment(self):
        """Load secrets from environment variables (fallback)"""
        # JWT secrets
        self.JWT_SECRET_KEY = self._get_jwt_secret()
        self.JWT_REFRESH_SECRET_KEY = self._get_refresh_secret()
        
        # Encryption key
        if not self.ENCRYPTION_KEY:
            self.ENCRYPTION_KEY = self._generate_fallback_secret()
            logger.warning("ENCRYPTION_KEY not set. Generated temporary key for development.")
        
        logger.info("Secrets loaded from environment variables")
    
    def _get_jwt_secret(self) -> str:
        """Get JWT secret with proper validation"""
        secret = os.getenv("JWT_SECRET_KEY")
        
        if not secret:
            if self.ENVIRONMENT == "development":
                # Generate a secure random key for development
                secret = secrets.token_urlsafe(32)
                logger.warning("JWT_SECRET_KEY not set. Generated temporary key for development.")
            else:
                raise ValueError("JWT_SECRET_KEY must be set in production environment")
        
        return self._validate_secret_key(secret)
    
    def _get_refresh_secret(self) -> str:
        """Get JWT refresh secret with proper validation"""
        secret = os.getenv("JWT_REFRESH_SECRET_KEY")
        
        if not secret:
            if self.ENVIRONMENT == "development":
                # Generate a secure random key for development
                secret = secrets.token_urlsafe(32)
                logger.warning("JWT_REFRESH_SECRET_KEY not set. Generated temporary key for development.")
            else:
                raise ValueError("JWT_REFRESH_SECRET_KEY must be set in production environment")
        
        return self._validate_secret_key(secret)
    
    def _generate_fallback_secret(self) -> str:
        """Generate a fallback secret for development"""
        if self.ENVIRONMENT == "development":
            return secrets.token_urlsafe(32)
        else:
            raise ValueError("Cannot generate fallback secret in production environment")
    
    def _validate_secret_key(self, secret: str) -> str:
        """Validate the secret key meets security requirements"""
        if len(secret) < 32:
            if self.ENVIRONMENT == "development":
                logger.warning("JWT secret is too short. Consider using a longer key.")
            else:
                raise ValueError("JWT secret must be at least 32 characters long")
        
        return secret

# Create enhanced config instance
enhanced_config = EnhancedConfig()

# Get and validate secret key for backward compatibility
_secret_key = _validate_secret_key(os.getenv("SECRET_KEY", "CHANGE_ME_REPLACE_WITH_SECURE_SECRET"))

# Legacy settings object for backward compatibility
from types import SimpleNamespace

settings = SimpleNamespace(
    AZURE_STORAGE_CONNECTION_STRING=enhanced_config.AZURE_STORAGE_CONNECTION_STRING,
    AZURE_CONTAINER_NAME=enhanced_config.AZURE_CONTAINER_NAME,
    LOCAL_MEDIA_DIR=enhanced_config.LOCAL_MEDIA_DIR,
    MONGO_URI=enhanced_config.MONGO_URI,
    SERVICE_BUS_CONNECTION_STRING=enhanced_config.SERVICE_BUS_CONNECTION_STRING,
    AZURE_AI_ENDPOINT=enhanced_config.AZURE_AI_ENDPOINT,
    AZURE_AI_KEY=enhanced_config.AZURE_AI_KEY,
    SECRET_KEY=_secret_key,
    ALGORITHM=enhanced_config.JWT_ALGORITHM,
    ACCESS_TOKEN_EXPIRE_MINUTES=enhanced_config.ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS=enhanced_config.REFRESH_TOKEN_EXPIRE_DAYS,
    ENVIRONMENT=enhanced_config.ENVIRONMENT,
    USE_LOCAL_EVENT_PROCESSOR=enhanced_config.USE_LOCAL_EVENT_PROCESSOR,
    EVENT_PROCESSOR_QUEUE_SIZE=enhanced_config.EVENT_PROCESSOR_QUEUE_SIZE,
    
    # Security enhancements
    JWT_SECRET_KEY=None,  # Will be loaded asynchronously
    REFRESH_TOKEN_SECRET=None,  # Will be loaded asynchronously
    ENCRYPTION_KEY=enhanced_config.ENCRYPTION_KEY,
    
    # Content security
    CONTENT_MAX_SIZE_MB=enhanced_config.CONTENT_MAX_SIZE_MB,
    ALLOWED_FILE_TYPES=enhanced_config.ALLOWED_FILE_TYPES,
    CONTENT_SCAN_ENABLED=enhanced_config.CONTENT_SCAN_ENABLED,
    COPYRIGHT_CHECK_ENABLED=enhanced_config.COPYRIGHT_CHECK_ENABLED,
    
    # Rate limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE=enhanced_config.RATE_LIMIT_REQUESTS_PER_MINUTE,
    RATE_LIMIT_UPLOADS_PER_HOUR=enhanced_config.RATE_LIMIT_UPLOADS_PER_HOUR,
    
    # Compliance
    DATA_ENCRYPTION_ENABLED=enhanced_config.DATA_ENCRYPTION_ENABLED,
    AUDIT_LOGGING_ENABLED=enhanced_config.AUDIT_LOGGING_ENABLED,
    GDPR_COMPLIANCE_MODE=enhanced_config.GDPR_COMPLIANCE_MODE,
    DATA_RETENTION_DAYS=enhanced_config.DATA_RETENTION_DAYS,
    
    # Device security
    DEVICE_CERTIFICATE_VALIDATION=enhanced_config.DEVICE_CERTIFICATE_VALIDATION,
    WEBSOCKET_MESSAGE_VALIDATION=enhanced_config.WEBSOCKET_MESSAGE_VALIDATION,
    DEVICE_HEARTBEAT_TIMEOUT_SECONDS=enhanced_config.DEVICE_HEARTBEAT_TIMEOUT_SECONDS,
    
    # Azure Key Vault
    AZURE_KEY_VAULT_URL=enhanced_config.AZURE_KEY_VAULT_URL,
    AZURE_CLIENT_ID=enhanced_config.AZURE_CLIENT_ID,
    AZURE_CLIENT_SECRET=enhanced_config.AZURE_CLIENT_SECRET,
    AZURE_TENANT_ID=enhanced_config.AZURE_TENANT_ID,
)

# Async initialization function
async def initialize_config():
    """Initialize configuration with secrets from Key Vault"""
    await enhanced_config.initialize_secrets()
    
    # Update legacy settings object
    settings.JWT_SECRET_KEY = enhanced_config.JWT_SECRET_KEY
    settings.REFRESH_TOKEN_SECRET = enhanced_config.JWT_REFRESH_SECRET_KEY
    settings.ENCRYPTION_KEY = enhanced_config.ENCRYPTION_KEY

# Debug logging for database configuration
logger.info(f"MONGO_URI configured: {enhanced_config.MONGO_URI is not None}")
if enhanced_config.MONGO_URI:
    logger.info(f"MONGO_URI value: {enhanced_config.MONGO_URI}")
else:
    logger.warning("MONGO_URI not set, using in-memory storage")
