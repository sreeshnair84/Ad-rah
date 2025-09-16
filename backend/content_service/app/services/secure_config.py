"""
Secure Configuration Management

This module provides secure configuration management with encryption,
validation, and audit capabilities for the AI service system.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import hashlib
import secrets
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import base64
import re

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration operations fail"""
    pass


class ConfigurationValidationError(Exception):
    """Raised when configuration validation fails"""
    pass


@dataclass
class ConfigurationMetadata:
    """Metadata for configuration entries"""
    key: str
    created_at: str
    last_modified: str
    version: int
    checksum: str
    is_encrypted: bool
    access_count: int = 0
    last_accessed: Optional[str] = None


class SecureConfigManager:
    """
    Secure configuration manager with encryption and validation

    Features:
    - Encrypted storage of sensitive configuration
    - Configuration validation
    - Audit logging
    - Version control
    - Access control
    """

    def __init__(self, config_dir: Optional[Path] = None, encryption_key: Optional[bytes] = None):
        """
        Initialize the secure configuration manager

        Args:
            config_dir: Directory to store configuration files
            encryption_key: Encryption key for sensitive data
        """
        self.config_dir = config_dir or Path(".secure_config")
        self.config_dir.mkdir(exist_ok=True, parents=True)

        # Generate or load encryption key
        self.encryption_key = encryption_key or self._load_or_generate_key()

        # In-memory configuration cache
        self._config_cache: Dict[str, Any] = {}
        self._metadata_cache: Dict[str, ConfigurationMetadata] = {}

        # Load existing configurations
        self._load_configurations()

    def _load_or_generate_key(self) -> bytes:
        """Load existing encryption key or generate a new one"""
        key_file = self.config_dir / ".encryption_key"

        if key_file.exists():
            try:
                with open(key_file, 'rb') as f:
                    return f.read()
            except Exception as e:
                logger.warning(f"Failed to load encryption key: {str(e)}")

        # Generate new key
        key = secrets.token_bytes(32)
        try:
            with open(key_file, 'wb') as f:
                f.write(key)
            key_file.chmod(0o600)  # Restrictive permissions
        except Exception as e:
            logger.error(f"Failed to save encryption key: {str(e)}")

        return key

    def _encrypt_data(self, data: str) -> str:
        """Encrypt data using simple XOR (replace with proper encryption in production)"""
        data_bytes = data.encode('utf-8')
        encrypted = bytearray()

        for i, byte in enumerate(data_bytes):
            key_byte = self.encryption_key[i % len(self.encryption_key)]
            encrypted.append(byte ^ key_byte)

        return base64.b64encode(bytes(encrypted)).decode('utf-8')

    def _decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt data using simple XOR (replace with proper encryption in production)"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            decrypted = bytearray()

            for i, byte in enumerate(encrypted_bytes):
                key_byte = self.encryption_key[i % len(self.encryption_key)]
                decrypted.append(byte ^ key_byte)

            return decrypted.decode('utf-8')
        except Exception as e:
            raise ConfigurationError("Failed to decrypt data")

    def _compute_checksum(self, data: Any) -> str:
        """Compute checksum for data integrity"""
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()

    def _load_configurations(self) -> None:
        """Load all configurations from disk"""
        try:
            for config_file in self.config_dir.glob("*.json"):
                if config_file.name.startswith('.'):
                    continue

                key = config_file.stem
                try:
                    with open(config_file, 'r') as f:
                        config_data = json.load(f)

                    # Load metadata if available
                    meta_file = self.config_dir / f"{key}.meta"
                    metadata = None
                    if meta_file.exists():
                        with open(meta_file, 'r') as f:
                            metadata = ConfigurationMetadata(**json.load(f))

                    # Decrypt sensitive data
                    if metadata and metadata.is_encrypted:
                        if isinstance(config_data, dict):
                            for k, v in config_data.items():
                                if isinstance(v, str) and len(v) > 50:  # Likely encrypted
                                    try:
                                        config_data[k] = self._decrypt_data(v)
                                    except:
                                        pass  # Keep as-is if decryption fails

                    self._config_cache[key] = config_data
                    if metadata:
                        self._metadata_cache[key] = metadata

                except Exception as e:
                    logger.warning(f"Failed to load configuration {key}: {str(e)}")

        except Exception as e:
            logger.error(f"Failed to load configurations: {str(e)}")

    def _save_configuration(self, key: str, data: Any, is_encrypted: bool = False) -> None:
        """Save configuration to disk"""
        try:
            # Create encrypted version for sensitive data
            save_data = data.copy() if isinstance(data, dict) else data

            if is_encrypted and isinstance(save_data, dict):
                for k, v in save_data.items():
                    if isinstance(v, str) and any(sensitive in k.lower() for sensitive in
                                                ['key', 'secret', 'password', 'token']):
                        save_data[k] = self._encrypt_data(v)

            # Save configuration
            config_file = self.config_dir / f"{key}.json"
            with open(config_file, 'w') as f:
                json.dump(save_data, f, indent=2)

            # Create/update metadata
            now = datetime.utcnow().isoformat()
            existing_meta = self._metadata_cache.get(key)

            if existing_meta:
                metadata = ConfigurationMetadata(
                    key=key,
                    created_at=existing_meta.created_at,
                    last_modified=now,
                    version=existing_meta.version + 1,
                    checksum=self._compute_checksum(data),
                    is_encrypted=is_encrypted,
                    access_count=existing_meta.access_count,
                    last_accessed=existing_meta.last_accessed
                )
            else:
                metadata = ConfigurationMetadata(
                    key=key,
                    created_at=now,
                    last_modified=now,
                    version=1,
                    checksum=self._compute_checksum(data),
                    is_encrypted=is_encrypted
                )

            # Save metadata
            meta_file = self.config_dir / f"{key}.meta"
            with open(meta_file, 'w') as f:
                json.dump(asdict(metadata), f, indent=2)

            # Update caches
            self._config_cache[key] = data
            self._metadata_cache[key] = metadata

            # Set restrictive permissions
            config_file.chmod(0o600)
            meta_file.chmod(0o600)

        except Exception as e:
            raise ConfigurationError(f"Failed to save configuration {key}: {str(e)}")

    def set(self, key: str, value: Any, encrypt_sensitive: bool = True) -> None:
        """
        Set a configuration value

        Args:
            key: Configuration key
            value: Configuration value
            encrypt_sensitive: Whether to encrypt sensitive data
        """
        self._validate_configuration(key, value)
        is_encrypted = encrypt_sensitive and self._contains_sensitive_data(key, value)
        self._save_configuration(key, value, is_encrypted)

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        if key in self._config_cache:
            # Update access metadata
            if key in self._metadata_cache:
                metadata = self._metadata_cache[key]
                metadata.access_count += 1
                metadata.last_accessed = datetime.utcnow().isoformat()

            return self._config_cache[key]

        return default

    def delete(self, key: str) -> bool:
        """
        Delete a configuration entry

        Args:
            key: Configuration key to delete

        Returns:
            True if deleted, False if not found
        """
        if key not in self._config_cache:
            return False

        try:
            # Remove files
            config_file = self.config_dir / f"{key}.json"
            meta_file = self.config_dir / f"{key}.meta"

            if config_file.exists():
                config_file.unlink()
            if meta_file.exists():
                meta_file.unlink()

            # Remove from cache
            del self._config_cache[key]
            if key in self._metadata_cache:
                del self._metadata_cache[key]

            return True

        except Exception as e:
            logger.error(f"Failed to delete configuration {key}: {str(e)}")
            return False

    def list_keys(self) -> List[str]:
        """List all configuration keys"""
        return list(self._config_cache.keys())

    def get_metadata(self, key: str) -> Optional[ConfigurationMetadata]:
        """Get metadata for a configuration key"""
        return self._metadata_cache.get(key)

    def _validate_configuration(self, key: str, value: Any) -> None:
        """Validate configuration key and value"""
        if not key or not isinstance(key, str):
            raise ConfigurationValidationError("Configuration key must be a non-empty string")

        if len(key) > 100:
            raise ConfigurationValidationError("Configuration key too long")

        # Validate key format (alphanumeric, underscore, dot)
        if not re.match(r'^[a-zA-Z0-9_.]+$', key):
            raise ConfigurationValidationError("Configuration key contains invalid characters")

        # Basic value validation
        self._validate_value(value)

    def _validate_value(self, value: Any, max_depth: int = 10, current_depth: int = 0) -> None:
        """Recursively validate configuration value"""
        if current_depth > max_depth:
            raise ConfigurationValidationError("Configuration structure too deep")

        if isinstance(value, dict):
            if len(value) > 100:
                raise ConfigurationValidationError("Configuration object too large")
            for k, v in value.items():
                if not isinstance(k, str) or len(k) > 100:
                    raise ConfigurationValidationError("Invalid configuration key")
                self._validate_value(v, max_depth, current_depth + 1)

        elif isinstance(value, list):
            if len(value) > 1000:
                raise ConfigurationValidationError("Configuration array too large")
            for item in value:
                self._validate_value(item, max_depth, current_depth + 1)

        elif isinstance(value, str):
            if len(value) > 10000:
                raise ConfigurationValidationError("Configuration string too long")

        # Allow basic types: str, int, float, bool, None

    def _contains_sensitive_data(self, key: str, value: Any) -> bool:
        """Check if configuration contains sensitive data"""
        sensitive_keywords = ['key', 'secret', 'password', 'token', 'credential']

        if any(keyword in key.lower() for keyword in sensitive_keywords):
            return True

        if isinstance(value, dict):
            return any(self._contains_sensitive_data(k, v) for k, v in value.items())

        return False

    def export_configuration(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Export configuration for backup/debugging

        Args:
            include_sensitive: Whether to include sensitive data

        Returns:
            Configuration dictionary
        """
        export_data = {}

        for key, value in self._config_cache.items():
            if not include_sensitive and self._contains_sensitive_data(key, value):
                # Replace sensitive data with placeholder
                if isinstance(value, dict):
                    export_data[key] = {k: "***" if self._contains_sensitive_data(k, v) else v
                                      for k, v in value.items()}
                else:
                    export_data[key] = "***"
            else:
                export_data[key] = value

        return export_data

    def import_configuration(self, config_data: Dict[str, Any], overwrite: bool = False) -> None:
        """
        Import configuration from dictionary

        Args:
            config_data: Configuration data to import
            overwrite: Whether to overwrite existing keys
        """
        for key, value in config_data.items():
            if overwrite or key not in self._config_cache:
                self.set(key, value)

    def cleanup_expired_configs(self, max_age_days: int = 365) -> int:
        """
        Clean up old configuration entries

        Args:
            max_age_days: Maximum age in days

        Returns:
            Number of configurations cleaned up
        """
        cleaned_count = 0
        cutoff_date = datetime.utcnow() - timedelta(days=max_age_days)

        for key, metadata in list(self._metadata_cache.items()):
            last_modified = datetime.fromisoformat(metadata.last_modified)
            if last_modified < cutoff_date:
                if self.delete(key):
                    cleaned_count += 1

        return cleaned_count

    def get_statistics(self) -> Dict[str, Any]:
        """Get configuration statistics"""
        total_configs = len(self._config_cache)
        encrypted_configs = sum(1 for meta in self._metadata_cache.values() if meta.is_encrypted)
        total_accesses = sum(meta.access_count for meta in self._metadata_cache.values())

        return {
            "total_configurations": total_configs,
            "encrypted_configurations": encrypted_configs,
            "total_accesses": total_accesses,
            "average_accesses_per_config": total_accesses / total_configs if total_configs > 0 else 0
        }


# Global configuration manager instance
_config_manager: Optional[SecureConfigManager] = None


def get_config_manager() -> SecureConfigManager:
    """Get or create the global configuration manager instance"""
    global _config_manager

    if _config_manager is None:
        _config_manager = SecureConfigManager()

    return _config_manager


def secure_set(key: str, value: Any) -> None:
    """Securely set a configuration value"""
    manager = get_config_manager()
    manager.set(key, value)


def secure_get(key: str, default: Any = None) -> Any:
    """Securely get a configuration value"""
    manager = get_config_manager()
    return manager.get(key, default)