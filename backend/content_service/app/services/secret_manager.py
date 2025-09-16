"""
Secure Secret Management for AI Services

This module provides secure handling of API keys and sensitive configuration
for AI service providers with validation and secure storage capabilities.
"""

import os
import re
import logging
from typing import Optional, Dict, Any, Union
from pathlib import Path
import hashlib
import secrets
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class SecretValidationError(Exception):
    """Raised when secret validation fails"""
    pass


class SecretStorageError(Exception):
    """Raised when secret storage operations fail"""
    pass


class Provider(str, Enum):
    """Supported AI providers"""
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    AZURE_OPENAI = "azure_openai"


@dataclass
class SecretMetadata:
    """Metadata for stored secrets"""
    provider: Provider
    key_hash: str  # SHA-256 hash for verification
    created_at: str
    last_validated: Optional[str] = None
    is_valid: bool = False
    validation_attempts: int = 0
    last_error: Optional[str] = None


class SecretManager:
    """
    Secure secret manager for AI provider API keys

    Features:
    - API key format validation
    - Secure storage with encryption
    - Key rotation support
    - Audit logging
    - Health monitoring
    """

    # API key format patterns for validation
    KEY_PATTERNS = {
        Provider.GEMINI: re.compile(r'^[A-Za-z0-9_-]{20,}$'),  # Gemini keys are typically longer
        Provider.OPENAI: re.compile(r'^sk-[A-Za-z0-9_-]{20,}$'),
        Provider.ANTHROPIC: re.compile(r'^sk-ant-[A-Za-z0-9_-]{20,}$'),
        Provider.AZURE_OPENAI: re.compile(r'^[A-Za-z0-9_-]{20,}$'),  # Azure keys vary
        Provider.OLLAMA: re.compile(r'^[A-Za-z0-9_-]{0,}$'),  # Ollama may not require keys
    }

    # Environment variable names
    ENV_VARS = {
        Provider.GEMINI: "GEMINI_API_KEY",
        Provider.OPENAI: "OPENAI_API_KEY",
        Provider.ANTHROPIC: "ANTHROPIC_API_KEY",
        Provider.AZURE_OPENAI: "AZURE_OPENAI_API_KEY",
        Provider.OLLAMA: "OLLAMA_URL",  # Ollama uses URL instead of API key
    }

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize the secret manager

        Args:
            storage_path: Path to store encrypted secrets (optional)
        """
        self.storage_path = storage_path or Path(".ai_secrets")
        self._secrets: Dict[Provider, str] = {}
        self._metadata: Dict[Provider, SecretMetadata] = {}
        self._encryption_key = self._generate_encryption_key()

        # Create storage directory if it doesn't exist
        self.storage_path.mkdir(exist_ok=True, parents=True)

        # Load existing secrets
        self._load_secrets()

    def _generate_encryption_key(self) -> bytes:
        """Generate or load encryption key"""
        key_file = self.storage_path / ".key"

        if key_file.exists():
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = secrets.token_bytes(32)
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            key_file.chmod(0o600)
            return key

    def _load_secrets(self) -> None:
        """Load secrets from secure storage"""
        try:
            for provider in Provider:
                secret_file = self.storage_path / f"{provider.value}.enc"
                meta_file = self.storage_path / f"{provider.value}.meta"

                if secret_file.exists() and meta_file.exists():
                    # Load encrypted secret and metadata
                    with open(secret_file, 'rb') as f:
                        encrypted_data = f.read()

                    with open(meta_file, 'r') as f:
                        metadata = SecretMetadata(**json.load(f))

                    # Decrypt secret (simple XOR for demo - use proper encryption in production)
                    secret = self._decrypt_data(encrypted_data)

                    # Validate secret format
                    if self._validate_key_format(provider, secret):
                        self._secrets[provider] = secret
                        self._metadata[provider] = metadata
                        logger.info(f"Loaded secret for {provider.value}")
                    else:
                        logger.warning(f"Invalid secret format for {provider.value}")

        except Exception as e:
            logger.error(f"Failed to load secrets: {str(e)}")

    def _encrypt_data(self, data: str) -> bytes:
        """Encrypt data using simple XOR (replace with proper encryption in production)"""
        data_bytes = data.encode('utf-8')
        encrypted = bytearray()

        for i, byte in enumerate(data_bytes):
            key_byte = self._encryption_key[i % len(self._encryption_key)]
            encrypted.append(byte ^ key_byte)

        return bytes(encrypted)

    def _decrypt_data(self, encrypted_data: bytes) -> str:
        """Decrypt data using simple XOR (replace with proper encryption in production)"""
        decrypted = bytearray()

        for i, byte in enumerate(encrypted_data):
            key_byte = self._encryption_key[i % len(self._encryption_key)]
            decrypted.append(byte ^ key_byte)

        return decrypted.decode('utf-8')

    def _validate_key_format(self, provider: Provider, key: str) -> bool:
        """
        Validate API key format for a provider

        Args:
            provider: The AI provider
            key: The API key to validate

        Returns:
            True if key format is valid, False otherwise
        """
        if provider == Provider.OLLAMA:
            # Ollama uses URL, so accept any non-empty string
            return bool(key.strip())

        pattern = self.KEY_PATTERNS.get(provider)
        if not pattern:
            logger.warning(f"No validation pattern for {provider.value}")
            return True  # Allow if no pattern defined

        is_valid = bool(pattern.match(key))

        if not is_valid:
            logger.warning(f"Invalid key format for {provider.value}")

        return is_valid

    def _compute_key_hash(self, key: str) -> str:
        """Compute SHA-256 hash of the key for integrity checking"""
        return hashlib.sha256(key.encode('utf-8')).hexdigest()

    def store_secret(self, provider: Provider, secret: str, validate: bool = True) -> bool:
        """
        Store a secret securely

        Args:
            provider: The AI provider
            secret: The secret to store
            validate: Whether to validate the secret format

        Returns:
            True if stored successfully, False otherwise

        Raises:
            SecretValidationError: If validation fails
            SecretStorageError: If storage fails
        """
        try:
            # Validate format if requested
            if validate and not self._validate_key_format(provider, secret):
                raise SecretValidationError(f"Invalid secret format for {provider.value}")

            # Encrypt and store secret
            encrypted_data = self._encrypt_data(secret)
            secret_file = self.storage_path / f"{provider.value}.enc"

            with open(secret_file, 'wb') as f:
                f.write(encrypted_data)

            # Set restrictive permissions
            secret_file.chmod(0o600)

            # Store metadata
            import datetime
            metadata = SecretMetadata(
                provider=provider,
                key_hash=self._compute_key_hash(secret),
                created_at=datetime.datetime.utcnow().isoformat(),
                is_valid=True
            )

            meta_file = self.storage_path / f"{provider.value}.meta"
            with open(meta_file, 'w') as f:
                json.dump(metadata.__dict__, f, indent=2)

            meta_file.chmod(0o600)

            # Update in-memory storage
            self._secrets[provider] = secret
            self._metadata[provider] = metadata

            logger.info(f"Successfully stored secret for {provider.value}")
            return True

        except SecretValidationError:
            raise
        except Exception as e:
            logger.error(f"Failed to store secret for {provider.value}: {str(e)}")
            raise SecretStorageError(f"Storage failed: {str(e)}")

    def get_secret(self, provider: Provider, validate: bool = True) -> Optional[str]:
        """
        Retrieve a secret

        Args:
            provider: The AI provider
            validate: Whether to validate the secret before returning

        Returns:
            The secret if available and valid, None otherwise
        """
        # First check environment variables
        env_var = self.ENV_VARS.get(provider)
        if env_var:
            env_secret = os.getenv(env_var)
            if env_secret:
                if validate and not self._validate_key_format(provider, env_secret):
                    logger.warning(f"Invalid secret in environment for {provider.value}")
                    return None
                return env_secret

        # Then check stored secrets
        if provider in self._secrets:
            secret = self._secrets[provider]
            if validate and not self._validate_key_format(provider, secret):
                logger.warning(f"Stored secret validation failed for {provider.value}")
                return None
            return secret

        return None

    def validate_secret(self, provider: Provider, secret: Optional[str] = None) -> bool:
        """
        Validate a secret for a provider

        Args:
            provider: The AI provider
            secret: The secret to validate (if None, uses stored/ env secret)

        Returns:
            True if secret is valid, False otherwise
        """
        if secret is None:
            secret = self.get_secret(provider, validate=False)

        if not secret:
            return False

        is_valid = self._validate_key_format(provider, secret)

        # Update metadata
        if provider in self._metadata:
            import datetime
            self._metadata[provider].last_validated = datetime.datetime.utcnow().isoformat()
            self._metadata[provider].is_valid = is_valid
            self._metadata[provider].validation_attempts += 1

            if not is_valid:
                self._metadata[provider].last_error = "Format validation failed"

        return is_valid

    def rotate_secret(self, provider: Provider, new_secret: str) -> bool:
        """
        Rotate a secret for a provider

        Args:
            provider: The AI provider
            new_secret: The new secret

        Returns:
            True if rotation successful, False otherwise
        """
        try:
            # Validate new secret
            if not self._validate_key_format(provider, new_secret):
                logger.error(f"Cannot rotate to invalid secret for {provider.value}")
                return False

            # Store new secret
            success = self.store_secret(provider, new_secret, validate=False)

            if success:
                logger.info(f"Successfully rotated secret for {provider.value}")

                # Update environment variable if it exists
                env_var = self.ENV_VARS.get(provider)
                if env_var and os.getenv(env_var):
                    os.environ[env_var] = new_secret

            return success

        except Exception as e:
            logger.error(f"Failed to rotate secret for {provider.value}: {str(e)}")
            return False

    def get_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Get status of all secrets

        Returns:
            Dictionary with status information for each provider
        """
        status = {}

        for provider in Provider:
            provider_status = {
                "available": False,
                "valid": False,
                "source": None,
                "last_validated": None,
                "validation_attempts": 0
            }

            # Check if secret is available
            secret = self.get_secret(provider, validate=False)
            if secret:
                provider_status["available"] = True

                # Check environment variable
                env_var = self.ENV_VARS.get(provider)
                if env_var and os.getenv(env_var):
                    provider_status["source"] = "environment"
                else:
                    provider_status["source"] = "stored"

            # Get metadata if available
            if provider in self._metadata:
                metadata = self._metadata[provider]
                provider_status["valid"] = metadata.is_valid
                provider_status["last_validated"] = metadata.last_validated
                provider_status["validation_attempts"] = metadata.validation_attempts

            status[provider.value] = provider_status

        return status

    def cleanup_expired_secrets(self, max_age_days: int = 90) -> int:
        """
        Clean up expired or old secrets

        Args:
            max_age_days: Maximum age in days for secrets to keep

        Returns:
            Number of secrets cleaned up
        """
        import datetime
        cleaned_count = 0

        for provider in list(self._secrets.keys()):
            if provider in self._metadata:
                metadata = self._metadata[provider]
                created_at = datetime.datetime.fromisoformat(metadata.created_at)
                age = datetime.datetime.utcnow() - created_at

                if age.days > max_age_days:
                    # Remove files
                    secret_file = self.storage_path / f"{provider.value}.enc"
                    meta_file = self.storage_path / f"{provider.value}.meta"

                    try:
                        if secret_file.exists():
                            secret_file.unlink()
                        if meta_file.exists():
                            meta_file.unlink()

                        # Remove from memory
                        del self._secrets[provider]
                        del self._metadata[provider]

                        cleaned_count += 1
                        logger.info(f"Cleaned up expired secret for {provider.value}")

                    except Exception as e:
                        logger.error(f"Failed to cleanup secret for {provider.value}: {str(e)}")

        return cleaned_count


# Global secret manager instance
_secret_manager: Optional[SecretManager] = None


def get_secret_manager() -> SecretManager:
    """Get or create the global secret manager instance"""
    global _secret_manager

    if _secret_manager is None:
        _secret_manager = SecretManager()

    return _secret_manager


def validate_api_key(provider: str, key: str) -> bool:
    """
    Convenience function to validate an API key

    Args:
        provider: Provider name (string)
        key: API key to validate

    Returns:
        True if valid, False otherwise
    """
    try:
        provider_enum = Provider(provider.lower())
        manager = get_secret_manager()
        return manager._validate_key_format(provider_enum, key)
    except (ValueError, AttributeError):
        logger.warning(f"Unknown provider: {provider}")
        return False


def secure_get_api_key(provider: str) -> Optional[str]:
    """
    Securely get an API key for a provider

    Args:
        provider: Provider name (string)

    Returns:
        API key if available and valid, None otherwise
    """
    try:
        provider_enum = Provider(provider.lower())
        manager = get_secret_manager()
        return manager.get_secret(provider_enum)
    except (ValueError, AttributeError):
        logger.warning(f"Unknown provider: {provider}")
        return None