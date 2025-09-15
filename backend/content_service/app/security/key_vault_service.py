"""
Azure Key Vault Service for Secure Secret Management
Provides secure access to secrets, keys, and certificates stored in Azure Key Vault
"""

import os
import logging
from typing import Optional, Dict, Any
from azure.keyvault.secrets import SecretClient
from azure.identity import DefaultAzureCredential, ClientSecretCredential
from azure.core.exceptions import AzureError
from functools import lru_cache
import asyncio
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class KeyVaultService:
    """Secure Azure Key Vault service for managing application secrets"""
    
    def __init__(self):
        self.client: Optional[SecretClient] = None
        self.is_initialized = False
        self._secret_cache: Dict[str, Any] = {}
        self._cache_expiry: Dict[str, datetime] = {}
        self.cache_duration = timedelta(minutes=30)  # Cache secrets for 30 minutes
        
    async def initialize(self) -> bool:
        """Initialize the Key Vault client with proper authentication"""
        try:
            vault_url = os.getenv("AZURE_KEY_VAULT_URL")
            if not vault_url:
                logger.warning("AZURE_KEY_VAULT_URL not configured, using environment variables")
                return False
            
            # Try different authentication methods in order of preference
            credential = None
            
            # 1. Try Managed Identity (preferred for production)
            try:
                credential = DefaultAzureCredential()
                # Test the credential
                test_client = SecretClient(vault_url=vault_url, credential=credential)
                # Try to get a test secret to validate authentication
                await asyncio.get_event_loop().run_in_executor(
                    None, lambda: test_client.get_secret("test-secret")
                )
                logger.info("Successfully authenticated using Managed Identity")
            except Exception as e:
                logger.debug(f"Managed Identity authentication failed: {e}")
                credential = None
            
            # 2. Try Service Principal (for development/testing)
            if not credential:
                client_id = os.getenv("AZURE_CLIENT_ID")
                client_secret = os.getenv("AZURE_CLIENT_SECRET")
                tenant_id = os.getenv("AZURE_TENANT_ID")
                
                if client_id and client_secret and tenant_id:
                    try:
                        credential = ClientSecretCredential(
                            tenant_id=tenant_id,
                            client_id=client_id,
                            client_secret=client_secret
                        )
                        # Test the credential
                        test_client = SecretClient(vault_url=vault_url, credential=credential)
                        await asyncio.get_event_loop().run_in_executor(
                            None, lambda: test_client.get_secret("test-secret")
                        )
                        logger.info("Successfully authenticated using Service Principal")
                    except Exception as e:
                        logger.debug(f"Service Principal authentication failed: {e}")
                        credential = None
            
            if not credential:
                logger.error("Failed to authenticate with Azure Key Vault")
                return False
            
            self.client = SecretClient(vault_url=vault_url, credential=credential)
            self.is_initialized = True
            logger.info(f"Key Vault service initialized successfully with {vault_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Key Vault service: {e}")
            return False
    
    async def get_secret(self, secret_name: str, use_cache: bool = True) -> Optional[str]:
        """
        Retrieve a secret from Azure Key Vault with caching
        
        Args:
            secret_name: Name of the secret to retrieve
            use_cache: Whether to use cached value if available
            
        Returns:
            Secret value or None if not found
        """
        if not self.is_initialized:
            logger.warning("Key Vault service not initialized, falling back to environment variables")
            return os.getenv(secret_name.upper().replace("-", "_"))
        
        # Check cache first
        if use_cache and secret_name in self._secret_cache:
            if datetime.utcnow() < self._cache_expiry.get(secret_name, datetime.min):
                logger.debug(f"Returning cached secret for {secret_name}")
                return self._secret_cache[secret_name]
            else:
                # Cache expired, remove it
                self._secret_cache.pop(secret_name, None)
                self._cache_expiry.pop(secret_name, None)
        
        try:
            # Retrieve secret from Key Vault
            secret = await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.get_secret(secret_name)
            )
            
            secret_value = secret.value
            
            # Cache the secret
            if use_cache:
                self._secret_cache[secret_name] = secret_value
                self._cache_expiry[secret_name] = datetime.utcnow() + self.cache_duration
            
            logger.debug(f"Successfully retrieved secret {secret_name} from Key Vault")
            return secret_value
            
        except AzureError as e:
            logger.error(f"Failed to retrieve secret {secret_name} from Key Vault: {e}")
            # Fallback to environment variable
            fallback_value = os.getenv(secret_name.upper().replace("-", "_"))
            if fallback_value:
                logger.warning(f"Using environment variable fallback for {secret_name}")
            return fallback_value
        except Exception as e:
            logger.error(f"Unexpected error retrieving secret {secret_name}: {e}")
            return None
    
    async def set_secret(self, secret_name: str, secret_value: str) -> bool:
        """
        Store a secret in Azure Key Vault
        
        Args:
            secret_name: Name of the secret
            secret_value: Value to store
            
        Returns:
            True if successful, False otherwise
        """
        if not self.is_initialized:
            logger.error("Key Vault service not initialized, cannot store secret")
            return False
        
        try:
            await asyncio.get_event_loop().run_in_executor(
                None, lambda: self.client.set_secret(secret_name, secret_value)
            )
            
            # Update cache
            self._secret_cache[secret_name] = secret_value
            self._cache_expiry[secret_name] = datetime.utcnow() + self.cache_duration
            
            logger.info(f"Successfully stored secret {secret_name} in Key Vault")
            return True
            
        except AzureError as e:
            logger.error(f"Failed to store secret {secret_name} in Key Vault: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error storing secret {secret_name}: {e}")
            return False
    
    async def get_jwt_secret(self) -> str:
        """Get the JWT signing secret with automatic generation if not found"""
        secret_value = await self.get_secret("jwt-secret-key")
        
        if not secret_value:
            # Generate a new secure secret
            import secrets
            new_secret = secrets.token_urlsafe(32)
            
            # Try to store it in Key Vault
            if await self.set_secret("jwt-secret-key", new_secret):
                logger.info("Generated and stored new JWT secret in Key Vault")
            else:
                logger.warning("Generated JWT secret but could not store in Key Vault")
            
            return new_secret
        
        return secret_value
    
    async def get_refresh_token_secret(self) -> str:
        """Get the refresh token signing secret"""
        secret_value = await self.get_secret("refresh-token-secret")
        
        if not secret_value:
            import secrets
            new_secret = secrets.token_urlsafe(32)
            await self.set_secret("refresh-token-secret", new_secret)
            return new_secret
        
        return secret_value
    
    async def get_encryption_key(self) -> str:
        """Get the encryption key for PII data"""
        secret_value = await self.get_secret("pii-encryption-key")
        
        if not secret_value:
            import secrets
            # Generate a 32-byte key for AES-256
            new_key = secrets.token_urlsafe(32)
            await self.set_secret("pii-encryption-key", new_key)
            return new_key
        
        return secret_value
    
    async def get_database_credentials(self) -> Dict[str, Optional[str]]:
        """Get database connection credentials"""
        return {
            "mongo_uri": await self.get_secret("mongo-uri"),
            "mongo_username": await self.get_secret("mongo-username"),
            "mongo_password": await self.get_secret("mongo-password"),
        }
    
    async def get_azure_ai_credentials(self) -> Dict[str, Optional[str]]:
        """Get Azure AI service credentials"""
        return {
            "endpoint": await self.get_secret("azure-ai-endpoint"),
            "key": await self.get_secret("azure-ai-key"),
        }
    
    async def get_storage_credentials(self) -> Dict[str, Optional[str]]:
        """Get Azure Storage credentials"""
        return {
            "connection_string": await self.get_secret("azure-storage-connection-string"),
            "account_name": await self.get_secret("azure-storage-account-name"),
            "account_key": await self.get_secret("azure-storage-account-key"),
        }
    
    def clear_cache(self):
        """Clear the secret cache"""
        self._secret_cache.clear()
        self._cache_expiry.clear()
        logger.info("Secret cache cleared")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the Key Vault service"""
        health_status = {
            "service": "Key Vault",
            "status": "unknown",
            "initialized": self.is_initialized,
            "cached_secrets": len(self._secret_cache),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        if not self.is_initialized:
            health_status["status"] = "not_initialized"
            return health_status
        
        try:
            # Try to get a test secret
            test_result = await self.get_secret("health-check", use_cache=False)
            health_status["status"] = "healthy"
            health_status["can_read_secrets"] = True
        except Exception as e:
            health_status["status"] = "unhealthy"
            health_status["error"] = str(e)
            health_status["can_read_secrets"] = False
        
        return health_status

# Global Key Vault service instance
key_vault_service = KeyVaultService()

async def initialize_key_vault() -> bool:
    """Initialize the global Key Vault service"""
    return await key_vault_service.initialize()

async def get_secure_config() -> Dict[str, str]:
    """Get all secure configuration from Key Vault"""
    if not key_vault_service.is_initialized:
        await initialize_key_vault()
    
    config = {}
    
    # Get all required secrets
    config["jwt_secret"] = await key_vault_service.get_jwt_secret()
    config["refresh_secret"] = await key_vault_service.get_refresh_token_secret()
    config["encryption_key"] = await key_vault_service.get_encryption_key()
    
    # Get database credentials
    db_creds = await key_vault_service.get_database_credentials()
    config.update(db_creds)
    
    # Get Azure AI credentials
    ai_creds = await key_vault_service.get_azure_ai_credentials()
    config.update(ai_creds)
    
    # Get storage credentials
    storage_creds = await key_vault_service.get_storage_credentials()
    config.update(storage_creds)
    
    return config