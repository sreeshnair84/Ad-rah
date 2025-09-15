"""
Field-Level Encryption Service for PII Data Protection
Implements AES-256 encryption for sensitive user data with key rotation support
"""

import base64
import logging
from typing import Optional, Any, Dict
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import os
import json
from datetime import datetime, timedelta
from functools import wraps

logger = logging.getLogger(__name__)

class EncryptionService:
    """
    AES-256 encryption service for protecting PII data
    Supports key rotation and multiple encryption keys
    """
    
    def __init__(self):
        self.fernet_instances: Dict[str, Fernet] = {}
        self.current_key_id = "default"
        self.salt = b'salt_1234567890123456'  # Should be from Key Vault in production
        self._initialized = False
    
    async def initialize(self, encryption_keys: Dict[str, str]) -> bool:
        """
        Initialize encryption service with keys from Key Vault
        
        Args:
            encryption_keys: Dictionary of key_id -> base64_encoded_key
        """
        try:
            for key_id, key_value in encryption_keys.items():
                # Derive Fernet key from the base key
                fernet_key = self._derive_fernet_key(key_value.encode())
                self.fernet_instances[key_id] = Fernet(fernet_key)
            
            # Set the most recent key as current
            if encryption_keys:
                self.current_key_id = max(encryption_keys.keys())
            
            self._initialized = True
            logger.info(f"Encryption service initialized with {len(encryption_keys)} keys")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize encryption service: {e}")
            return False
    
    def _derive_fernet_key(self, password: bytes) -> bytes:
        """Derive a Fernet-compatible key from a password"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
            backend=default_backend()
        )
        key = base64.urlsafe_b64encode(kdf.derive(password))
        return key
    
    def encrypt(self, plaintext: str, key_id: Optional[str] = None) -> Optional[str]:
        """
        Encrypt plaintext using AES-256
        
        Args:
            plaintext: Text to encrypt
            key_id: Specific key to use (defaults to current key)
            
        Returns:
            Encrypted text with key_id prefix, or None if encryption fails
        """
        if not self._initialized:
            logger.error("Encryption service not initialized")
            return None
        
        if not plaintext:
            return plaintext  # Don't encrypt empty strings
        
        try:
            key_id = key_id or self.current_key_id
            
            if key_id not in self.fernet_instances:
                logger.error(f"Encryption key {key_id} not found")
                return None
            
            fernet = self.fernet_instances[key_id]
            encrypted_bytes = fernet.encrypt(plaintext.encode('utf-8'))
            encrypted_b64 = base64.b64encode(encrypted_bytes).decode('utf-8')
            
            # Prefix with key ID for key rotation support
            return f"{key_id}:{encrypted_b64}"
            
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            return None
    
    def decrypt(self, encrypted_text: str) -> Optional[str]:
        """
        Decrypt encrypted text
        
        Args:
            encrypted_text: Text to decrypt (with key_id prefix)
            
        Returns:
            Decrypted plaintext or None if decryption fails
        """
        if not self._initialized:
            logger.error("Encryption service not initialized")
            return None
        
        if not encrypted_text or ':' not in encrypted_text:
            # Assume unencrypted text (for migration compatibility)
            return encrypted_text
        
        try:
            key_id, encrypted_b64 = encrypted_text.split(':', 1)
            
            if key_id not in self.fernet_instances:
                logger.error(f"Decryption key {key_id} not found")
                return None
            
            fernet = self.fernet_instances[key_id]
            encrypted_bytes = base64.b64decode(encrypted_b64.encode('utf-8'))
            decrypted_bytes = fernet.decrypt(encrypted_bytes)
            
            return decrypted_bytes.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            return None
    
    def encrypt_dict(self, data: Dict[str, Any], fields_to_encrypt: list) -> Dict[str, Any]:
        """
        Encrypt specific fields in a dictionary
        
        Args:
            data: Dictionary containing data to encrypt
            fields_to_encrypt: List of field names to encrypt
            
        Returns:
            Dictionary with specified fields encrypted
        """
        if not isinstance(data, dict):
            return data
        
        encrypted_data = data.copy()
        
        for field in fields_to_encrypt:
            if field in encrypted_data and encrypted_data[field]:
                encrypted_value = self.encrypt(str(encrypted_data[field]))
                if encrypted_value is not None:
                    encrypted_data[field] = encrypted_value
                    encrypted_data[f"{field}_encrypted"] = True
        
        return encrypted_data
    
    def decrypt_dict(self, data: Dict[str, Any], fields_to_decrypt: list) -> Dict[str, Any]:
        """
        Decrypt specific fields in a dictionary
        
        Args:
            data: Dictionary containing data to decrypt
            fields_to_decrypt: List of field names to decrypt
            
        Returns:
            Dictionary with specified fields decrypted
        """
        if not isinstance(data, dict):
            return data
        
        decrypted_data = data.copy()
        
        for field in fields_to_decrypt:
            if field in decrypted_data and decrypted_data[field]:
                decrypted_value = self.decrypt(decrypted_data[field])
                if decrypted_value is not None:
                    decrypted_data[field] = decrypted_value
                    decrypted_data.pop(f"{field}_encrypted", None)
        
        return decrypted_data
    
    async def rotate_keys(self, new_key: str) -> bool:
        """
        Add a new encryption key for key rotation
        
        Args:
            new_key: New encryption key
            
        Returns:
            True if successful
        """
        try:
            # Generate new key ID based on timestamp
            new_key_id = f"key_{int(datetime.utcnow().timestamp())}"
            
            # Add new key
            fernet_key = self._derive_fernet_key(new_key.encode())
            self.fernet_instances[new_key_id] = Fernet(fernet_key)
            self.current_key_id = new_key_id
            
            logger.info(f"Added new encryption key: {new_key_id}")
            return True
            
        except Exception as e:
            logger.error(f"Key rotation failed: {e}")
            return False

# Global encryption service instance
encryption_service = EncryptionService()

# PII field definitions
PII_FIELDS = [
    'email',
    'phone',
    'address',
    'full_name',
    'first_name',
    'last_name',
    'ssn',
    'tax_id',
    'passport_number',
    'driver_license',
    'credit_card',
    'bank_account'
]

def encrypted_field(func):
    """
    Decorator to automatically encrypt/decrypt PII fields
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        # This would be implemented based on your ORM/database layer
        # For now, it's a placeholder for the concept
        return func(*args, **kwargs)
    return wrapper

class EncryptedModel:
    """
    Base class for models with encrypted fields
    """
    
    _encrypted_fields = []
    
    def encrypt_fields(self):
        """Encrypt PII fields before saving"""
        if not encryption_service._initialized:
            logger.warning("Encryption service not initialized")
            return
        
        for field in self._encrypted_fields:
            if hasattr(self, field):
                value = getattr(self, field)
                if value and not self._is_encrypted(value):
                    encrypted_value = encryption_service.encrypt(str(value))
                    if encrypted_value:
                        setattr(self, field, encrypted_value)
    
    def decrypt_fields(self):
        """Decrypt PII fields after loading"""
        if not encryption_service._initialized:
            logger.warning("Encryption service not initialized")
            return
        
        for field in self._encrypted_fields:
            if hasattr(self, field):
                value = getattr(self, field)
                if value and self._is_encrypted(value):
                    decrypted_value = encryption_service.decrypt(value)
                    if decrypted_value:
                        setattr(self, field, decrypted_value)
    
    def _is_encrypted(self, value: str) -> bool:
        """Check if a value is encrypted (has key_id prefix)"""
        return isinstance(value, str) and ':' in value and value.split(':', 1)[0].startswith('key_')

# Usage examples for different model classes
class EncryptedUserProfile(EncryptedModel):
    """User profile with encrypted PII fields"""
    
    _encrypted_fields = ['email', 'phone', 'full_name', 'address']
    
    def __init__(self, **kwargs):
        self.email = kwargs.get('email')
        self.phone = kwargs.get('phone')
        self.full_name = kwargs.get('full_name')
        self.address = kwargs.get('address')
        self.username = kwargs.get('username')  # Not encrypted
        self.role = kwargs.get('role')  # Not encrypted

class EncryptedCompanyData(EncryptedModel):
    """Company data with encrypted sensitive fields"""
    
    _encrypted_fields = ['contact_email', 'contact_phone', 'billing_address', 'tax_id']
    
    def __init__(self, **kwargs):
        self.contact_email = kwargs.get('contact_email')
        self.contact_phone = kwargs.get('contact_phone')
        self.billing_address = kwargs.get('billing_address')
        self.tax_id = kwargs.get('tax_id')
        self.company_name = kwargs.get('company_name')  # Not encrypted
        self.company_type = kwargs.get('company_type')  # Not encrypted

async def initialize_encryption_service(key_vault_service):
    """Initialize encryption service with keys from Key Vault"""
    try:
        # Get encryption keys from Key Vault
        encryption_keys = {
            "default": await key_vault_service.get_encryption_key()
        }
        
        # Initialize encryption service
        success = await encryption_service.initialize(encryption_keys)
        if success:
            logger.info("Encryption service initialized successfully")
        else:
            logger.error("Failed to initialize encryption service")
        
        return success
        
    except Exception as e:
        logger.error(f"Failed to initialize encryption service: {e}")
        return False