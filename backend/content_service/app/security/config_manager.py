"""
Secure Configuration Manager
Handles sensitive configuration data with proper validation and encryption
"""
import os
import logging
import base64
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
try:
    from azure.keyvault.secrets import SecretClient
    from azure.identity import DefaultAzureCredential
except Exception:  # pragma: no cover - optional dependency
    SecretClient = None
    DefaultAzureCredential = None
import secrets

logger = logging.getLogger(__name__)

class SecureConfigManager:
    """Manages secure configuration with Azure Key Vault integration"""
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "development")
        self.key_vault_url = os.getenv("AZURE_KEY_VAULT_URL")
        self.encryption_key = self._get_encryption_key()
        self.fernet = Fernet(self.encryption_key) if self.encryption_key else None
        self.key_vault_client = self._init_key_vault()
        
    def _get_encryption_key(self) -> Optional[bytes]:
        """Get or generate encryption key for data at rest"""
        key_str = os.getenv("ENCRYPTION_KEY")
        if key_str:
            try:
                return base64.urlsafe_b64decode(key_str)
            except Exception as e:
                logger.error(f"Invalid encryption key format: {e}")
        
        # Generate new key if none exists (development only)
        if self.environment == "development":
            key = Fernet.generate_key()
            logger.warning(f"Generated new encryption key for development: {base64.urlsafe_b64encode(key).decode()}")
            logger.warning("Add this to your .env file as ENCRYPTION_KEY")
            return key
        
        return None
    
    def _init_key_vault(self) -> Optional[Any]:
        """Initialize Azure Key Vault client if configured"""
        if not self.key_vault_url:
            logger.info("Azure Key Vault not configured, using environment variables")
            return None
        
        try:
            if DefaultAzureCredential is None or SecretClient is None:
                logger.warning("Azure SDK not installed; skipping Key Vault initialization")
                return None

            credential = DefaultAzureCredential()
            client = SecretClient(vault_url=self.key_vault_url, credential=credential)
            logger.info("Azure Key Vault client initialized successfully")
            return client
        except Exception as e:
            logger.error(f"Failed to initialize Key Vault client: {e}")
            return None
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get secret from Key Vault or environment variables
        Priority: Azure Key Vault > Environment Variables > Default
        """
        # Try Azure Key Vault first
        if self.key_vault_client:
            try:
                secret = self.key_vault_client.get_secret(key.replace('_', '-').lower())
                logger.debug(f"Retrieved secret '{key}' from Key Vault")
                return secret.value
            except Exception as e:
                logger.debug(f"Secret '{key}' not found in Key Vault: {e}")
        
        # Fallback to environment variables
        value = os.getenv(key)
        if value:
            logger.debug(f"Retrieved secret '{key}' from environment")
            return value
        
        if default:
            logger.debug(f"Using default value for '{key}'")
            return default
        
        logger.warning(f"Secret '{key}' not found in any source")
        return None
    
    def encrypt_data(self, data: str) -> Optional[str]:
        """Encrypt sensitive data for storage"""
        if not self.fernet:
            logger.error("Encryption not available - no valid encryption key")
            return None
        
        try:
            encrypted = self.fernet.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            logger.error(f"Failed to encrypt data: {e}")
            return None
    
    def decrypt_data(self, encrypted_data: str) -> Optional[str]:
        """Decrypt sensitive data from storage"""
        if not self.fernet:
            logger.error("Decryption not available - no valid encryption key")
            return None
        
        try:
            encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted = self.fernet.decrypt(encrypted_bytes)
            return decrypted.decode()
        except Exception as e:
            logger.error(f"Failed to decrypt data: {e}")
            return None
    
    def validate_required_secrets(self) -> Dict[str, bool]:
        """Validate that all required secrets are present"""
        required_secrets = {
            "SECRET_KEY": False,
            "JWT_SECRET_KEY": False,
            "MONGO_URI": False,
        }
        
        for secret_name in required_secrets.keys():
            value = self.get_secret(secret_name)
            if value and len(value) >= 32:  # Minimum 32 characters for security
                required_secrets[secret_name] = True
            else:
                logger.error(f"Required secret '{secret_name}' is missing or too short")
        
        return required_secrets
    
    def generate_secure_secret(self, length: int = 32) -> str:
        """Generate a cryptographically secure secret"""
        return secrets.token_urlsafe(length)
    
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() in ["production", "prod"]
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return {
            "mongo_uri": self.get_secret("MONGO_URI", "mongodb://localhost:27017/openkiosk"),
            "db_name": self.get_secret("MONGO_DB_NAME", "openkiosk"),
            "encryption_enabled": os.getenv("DATA_ENCRYPTION_ENABLED", "true").lower() == "true"
        }
    
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration"""
        return {
            "secret_key": self.get_secret("SECRET_KEY"),
            "jwt_secret": self.get_secret("JWT_SECRET_KEY"),
            "refresh_secret": self.get_secret("REFRESH_TOKEN_SECRET"),
            "encryption_enabled": self.fernet is not None,
            "certificate_validation": os.getenv("DEVICE_CERTIFICATE_VALIDATION", "true").lower() == "true",
            "message_validation": os.getenv("WEBSOCKET_MESSAGE_VALIDATION", "strict"),
            "rate_limit_rpm": int(os.getenv("RATE_LIMIT_REQUESTS_PER_MINUTE", "60")),
            "rate_limit_uploads": int(os.getenv("RATE_LIMIT_UPLOADS_PER_HOUR", "10"))
        }
    
    def get_content_config(self) -> Dict[str, Any]:
        """Get content security configuration"""
        return {
            "max_size_mb": int(os.getenv("CONTENT_MAX_SIZE_MB", "100")),
            "allowed_types": os.getenv("ALLOWED_FILE_TYPES", "jpg,jpeg,png,gif,webp,mp4,avi,mov,txt,json").split(","),
            "scan_enabled": os.getenv("CONTENT_SCAN_ENABLED", "true").lower() == "true",
            "copyright_check": os.getenv("COPYRIGHT_CHECK_ENABLED", "true").lower() == "true"
        }
    
    def get_compliance_config(self) -> Dict[str, Any]:
        """Get compliance and privacy configuration"""
        return {
            "gdpr_mode": os.getenv("GDPR_COMPLIANCE_MODE", "true").lower() == "true",
            "audit_logging": os.getenv("AUDIT_LOGGING_ENABLED", "true").lower() == "true",
            "data_retention_days": int(os.getenv("DATA_RETENTION_DAYS", "365")),
            "dmca_email": self.get_secret("DMCA_NOTIFICATION_EMAIL", "dmca@localhost")
        }

# Global configuration instance
config_manager = SecureConfigManager()