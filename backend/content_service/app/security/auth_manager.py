"""
Secure Authentication Manager
Implements industry-standard authentication with proper JWT validation, device certificates, and audit logging
"""
import jwt
import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from typing import Dict, Optional, Any, Tuple
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
import logging

from .config_manager import config_manager
from .audit_logger import audit_logger

logger = logging.getLogger(__name__)

class SecureAuthManager:
    """Manages secure authentication with certificates and JWT tokens"""
    
    def __init__(self):
        self.security_config = config_manager.get_security_config()
        self.jwt_secret = self.security_config.get("jwt_secret")
        self.refresh_secret = self.security_config.get("refresh_secret")
        # If secrets are missing, allow development fallback but fail in production
        if not self.jwt_secret or not self.refresh_secret:
            if config_manager.is_production():
                logger.critical("JWT secrets not configured - authentication will fail in production")
                raise ValueError("Authentication secrets not properly configured")
            # Development: generate temporary secrets to allow local runs and tests
            logger.warning("JWT secrets not configured - generating development secrets (not for production)")
            self.jwt_secret = self.jwt_secret or config_manager.generate_secure_secret(64)
            self.refresh_secret = self.refresh_secret or config_manager.generate_secure_secret(64)
            # Update local security_config for consistency
            self.security_config["jwt_secret"] = self.jwt_secret
            self.security_config["refresh_secret"] = self.refresh_secret
    
    def hash_password(self, password: str, salt: Optional[str] = None) -> Tuple[str, str]:
        """
        Hash password with salt using PBKDF2
        Returns (hashed_password, salt)
        """
        if not salt:
            salt = secrets.token_hex(32)
        
        # Use PBKDF2 with SHA-256 (industry standard)
        hashed = hashlib.pbkdf2_hmac('sha256', 
                                   password.encode('utf-8'), 
                                   salt.encode('utf-8'), 
                                   100000)  # 100k iterations
        
        return hashed.hex(), salt
    
    def verify_password(self, password: str, hashed_password: str, salt: str) -> bool:
        """Verify password against stored hash"""
        try:
            computed_hash, _ = self.hash_password(password, salt)
            return secrets.compare_digest(computed_hash, hashed_password)
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False
    
    def generate_jwt_token(self, payload: Dict[str, Any], expires_in: int = 3600) -> str:
        """Generate JWT token with expiration"""
        now = datetime.utcnow()
        token_payload = {
            **payload,
            'iat': now,
            'exp': now + timedelta(seconds=expires_in),
            'jti': str(uuid.uuid4()),  # JWT ID for token tracking
        }
        
        return jwt.encode(token_payload, self.jwt_secret, algorithm='HS256')
    
    def verify_jwt_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])
            
            # Additional security checks
            if not payload.get('jti'):
                logger.warning("JWT token missing JTI (token ID)")
                return None
            
            # Log token usage for audit
            audit_logger.log_auth_event("jwt_token_used", {
                "jti": payload.get('jti'),
                "subject": payload.get('sub'),
                "expires": payload.get('exp')
            })
            
            return payload
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid JWT token: {e}")
            return None
    
    def generate_refresh_token(self, user_id: str) -> str:
        """Generate secure refresh token"""
        payload = {
            'sub': user_id,
            'type': 'refresh',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + timedelta(days=7),  # 7 days
            'jti': str(uuid.uuid4())
        }
        
        return jwt.encode(payload, self.refresh_secret, algorithm='HS256')
    
    def verify_refresh_token(self, token: str) -> Optional[str]:
        """Verify refresh token and return user ID"""
        try:
            payload = jwt.decode(token, self.refresh_secret, algorithms=['HS256'])
            
            if payload.get('type') != 'refresh':
                logger.warning("Invalid refresh token type")
                return None
            
            return payload.get('sub')
        except jwt.ExpiredSignatureError:
            logger.warning("Refresh token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid refresh token: {e}")
            return None
    
    def generate_device_certificate(self, device_id: str, organization_name: str) -> Tuple[str, str]:
        """
        Generate X.509 certificate for device authentication
        Returns (certificate_pem, private_key_pem)
        """
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Create certificate subject
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "AE"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Dubai"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Dubai"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization_name),
                x509.NameAttribute(NameOID.COMMON_NAME, f"device-{device_id}"),
            ])
            
            # Create certificate
            cert = x509.CertificateBuilder().subject_name(
                subject
            ).issuer_name(
                issuer
            ).public_key(
                private_key.public_key()
            ).serial_number(
                x509.random_serial_number()
            ).not_valid_before(
                datetime.utcnow()
            ).not_valid_after(
                datetime.utcnow() + timedelta(days=365)  # 1 year validity
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(f"device-{device_id}.local"),
                    x509.DNSName(f"{device_id}.adarah.local"),
                ]),
                critical=False,
            ).add_extension(
                x509.KeyUsage(
                    digital_signature=True,
                    key_encipherment=True,
                    content_commitment=False,
                    data_encipherment=False,
                    key_agreement=False,
                    key_cert_sign=False,
                    crl_sign=False,
                    encipher_only=False,
                    decipher_only=False,
                ),
                critical=True,
            ).sign(private_key, hashes.SHA256())
            
            # Convert to PEM format
            cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode()
            key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode()
            
            # Log certificate generation
            audit_logger.log_security_event("device_certificate_generated", {
                "device_id": device_id,
                "organization": organization_name,
                "serial_number": str(cert.serial_number),
                "expires": cert.not_valid_after.isoformat()
            })
            
            return cert_pem, key_pem
            
        except Exception as e:
            logger.error(f"Failed to generate device certificate: {e}")
            raise
    
    def verify_device_certificate(self, cert_pem: str, device_id: str) -> bool:
        """Verify device certificate is valid and matches device ID"""
        try:
            cert = x509.load_pem_x509_certificate(cert_pem.encode())
            
            # Check if certificate is still valid
            now = datetime.utcnow()
            if now < cert.not_valid_before or now > cert.not_valid_after:
                logger.warning(f"Device certificate for {device_id} has expired")
                return False
            
            # Check if certificate is for the correct device
            common_name = None
            for attribute in cert.subject:
                if attribute.oid == NameOID.COMMON_NAME:
                    common_name = attribute.value
                    break
            
            if common_name != f"device-{device_id}":
                logger.warning(f"Certificate common name mismatch: expected 'device-{device_id}', got '{common_name}'")
                return False
            
            # Log certificate verification
            audit_logger.log_security_event("device_certificate_verified", {
                "device_id": device_id,
                "serial_number": str(cert.serial_number),
                "subject": str(cert.subject)
            })
            
            return True
            
        except Exception as e:
            logger.error(f"Certificate verification failed for device {device_id}: {e}")
            return False
    
    def create_secure_session(self, user_id: str, user_type: str, additional_claims: Optional[Dict] = None) -> Dict[str, str]:
        """Create secure session with access and refresh tokens"""
        base_payload = {
            'sub': user_id,
            'user_type': user_type,
            'session_id': str(uuid.uuid4())
        }
        
        if additional_claims:
            base_payload.update(additional_claims)
        
        access_token = self.generate_jwt_token(base_payload, expires_in=3600)  # 1 hour
        refresh_token = self.generate_refresh_token(user_id)
        
        # Log session creation
        audit_logger.log_auth_event("session_created", {
            "user_id": user_id,
            "user_type": user_type,
            "session_id": base_payload['session_id']
        })
        
        return {
            'access_token': access_token,
            'refresh_token': refresh_token,
            'token_type': 'Bearer',
            'expires_in': 3600
        }
    
    def revoke_token(self, token: str, token_type: str = 'access') -> bool:
        """Revoke a token (add to blacklist)"""
        try:
            payload = self.verify_jwt_token(token)
            if payload:
                jti = payload.get('jti')
                if jti:
                    # Add to token blacklist (implement in your database)
                    audit_logger.log_security_event("token_revoked", {
                        "jti": jti,
                        "token_type": token_type,
                        "subject": payload.get('sub')
                    })
                    return True
            return False
        except Exception as e:
            logger.error(f"Failed to revoke token: {e}")
            return False

# Global authentication manager instance
auth_manager = SecureAuthManager()