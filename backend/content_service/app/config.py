import os
import secrets
import logging
from types import SimpleNamespace

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

# Get and validate secret key
_secret_key = _validate_secret_key(os.getenv("SECRET_KEY", "CHANGE_ME_REPLACE_WITH_SECURE_SECRET"))

# Settings object using environment variables with security validations
settings = SimpleNamespace(
    AZURE_STORAGE_CONNECTION_STRING=os.getenv("AZURE_STORAGE_CONNECTION_STRING"),
    AZURE_CONTAINER_NAME=os.getenv("AZURE_CONTAINER_NAME", "openkiosk-media"),
    LOCAL_MEDIA_DIR=os.getenv("LOCAL_MEDIA_DIR", "./data/media"),
    MONGO_URI=os.getenv("MONGO_URI"),
    SERVICE_BUS_CONNECTION_STRING=os.getenv("SERVICE_BUS_CONNECTION_STRING"),
    AZURE_AI_ENDPOINT=os.getenv("AZURE_AI_ENDPOINT"),
    AZURE_AI_KEY=os.getenv("AZURE_AI_KEY"),
    SECRET_KEY=_secret_key,
    ALGORITHM="HS256",
    ACCESS_TOKEN_EXPIRE_MINUTES=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),  # Reduced from 60 for better security
    REFRESH_TOKEN_EXPIRE_DAYS=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
    # Environment detection
    ENVIRONMENT=os.getenv("ENVIRONMENT", "development").lower(),
    # Local development settings
    USE_LOCAL_EVENT_PROCESSOR=os.getenv("USE_LOCAL_EVENT_PROCESSOR", "true").lower() == "true",
    EVENT_PROCESSOR_QUEUE_SIZE=int(os.getenv("EVENT_PROCESSOR_QUEUE_SIZE", "100")),
    
    # Security enhancements
    JWT_SECRET_KEY=os.getenv("JWT_SECRET_KEY", _secret_key),
    REFRESH_TOKEN_SECRET=os.getenv("REFRESH_TOKEN_SECRET", _secret_key + "_refresh"),
    ENCRYPTION_KEY=os.getenv("ENCRYPTION_KEY"),
    
    # Content security
    CONTENT_MAX_SIZE_MB=int(os.getenv("CONTENT_MAX_SIZE_MB", "100")),
    ALLOWED_FILE_TYPES=os.getenv("ALLOWED_FILE_TYPES", "jpg,jpeg,png,gif,webp,mp4,avi,mov,txt,json"),
    CONTENT_SCAN_ENABLED=os.getenv("CONTENT_SCAN_ENABLED", "true").lower() == "true",
    COPYRIGHT_CHECK_ENABLED=os.getenv("COPYRIGHT_CHECK_ENABLED", "true").lower() == "true",
    
    # Rate limiting
    RATE_LIMIT_REQUESTS_PER_MINUTE=int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60")),
    RATE_LIMIT_UPLOADS_PER_HOUR=int(os.getenv("RATE_LIMIT_UPLOADS_PER_HOUR", "10")),
    
    # Compliance
    DATA_ENCRYPTION_ENABLED=os.getenv("DATA_ENCRYPTION_ENABLED", "true").lower() == "true",
    AUDIT_LOGGING_ENABLED=os.getenv("AUDIT_LOGGING_ENABLED", "true").lower() == "true",
    GDPR_COMPLIANCE_MODE=os.getenv("GDPR_COMPLIANCE_MODE", "true").lower() == "true",
    DATA_RETENTION_DAYS=int(os.getenv("DATA_RETENTION_DAYS", "365")),
    
    # Device security
    DEVICE_CERTIFICATE_VALIDATION=os.getenv("DEVICE_CERTIFICATE_VALIDATION", "true").lower() == "true",
    WEBSOCKET_MESSAGE_VALIDATION=os.getenv("WEBSOCKET_MESSAGE_VALIDATION", "strict"),
    DEVICE_HEARTBEAT_TIMEOUT_SECONDS=int(os.getenv("DEVICE_HEARTBEAT_TIMEOUT_SECONDS", "300")),
    
    # Azure Key Vault
    AZURE_KEY_VAULT_URL=os.getenv("AZURE_KEY_VAULT_URL"),
    AZURE_CLIENT_ID=os.getenv("AZURE_CLIENT_ID"),
    AZURE_CLIENT_SECRET=os.getenv("AZURE_CLIENT_SECRET"),
    AZURE_TENANT_ID=os.getenv("AZURE_TENANT_ID"),
)

# Debug logging for database configuration
logger.info(f"MONGO_URI configured: {settings.MONGO_URI is not None}")
if settings.MONGO_URI:
    logger.info(f"MONGO_URI value: {settings.MONGO_URI}")
else:
    logger.warning("MONGO_URI not set, using in-memory storage")
