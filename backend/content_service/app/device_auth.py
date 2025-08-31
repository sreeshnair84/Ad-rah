import jwt
import uuid
import secrets
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Tuple
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography import x509
from cryptography.x509.oid import NameOID

from app.models import DeviceCredentials, DeviceHeartbeat, DeviceFingerprint, ScreenStatus
from app.repo import repo
from app.config import settings

logger = logging.getLogger(__name__)

class DeviceAuthService:
    """Service for handling device authentication and security"""
    
    def __init__(self):
        self.jwt_algorithm = "HS256"
        self.device_token_expire_hours = 24  # Device tokens last longer than user tokens
        self.refresh_token_expire_days = 30
        
    def generate_device_certificate(self, device_id: str, organization_name: str) -> Tuple[str, str]:
        """Generate a self-signed certificate for device authentication"""
        try:
            # Generate private key
            private_key = rsa.generate_private_key(
                public_exponent=65537,
                key_size=2048,
            )
            
            # Generate certificate
            subject = issuer = x509.Name([
                x509.NameAttribute(NameOID.COUNTRY_NAME, "AE"),
                x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Dubai"),
                x509.NameAttribute(NameOID.LOCALITY_NAME, "Dubai"),
                x509.NameAttribute(NameOID.ORGANIZATION_NAME, organization_name),
                x509.NameAttribute(NameOID.COMMON_NAME, f"Device-{device_id}"),
            ])
            
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
                datetime.utcnow() + timedelta(days=365)
            ).add_extension(
                x509.SubjectAlternativeName([
                    x509.DNSName(f"device-{device_id}.local"),
                    x509.DNSName(f"device-{device_id}.openkiosk.local"),
                ]),
                critical=False,
            ).sign(private_key, hashes.SHA256())
            
            # Serialize to PEM format
            cert_pem = cert.public_bytes(serialization.Encoding.PEM).decode('utf-8')
            private_key_pem = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ).decode('utf-8')
            
            return cert_pem, private_key_pem
            
        except Exception as e:
            logger.error(f"Failed to generate device certificate: {e}")
            raise
    
    def create_device_jwt(self, device_id: str, company_id: str, capabilities: Optional[Dict] = None) -> str:
        """Create JWT token for device authentication"""
        now = datetime.utcnow()
        expires_at = now + timedelta(hours=self.device_token_expire_hours)
        
        payload = {
            "sub": device_id,  # Subject: device ID
            "iss": "openkiosk-backend",  # Issuer
            "aud": "openkiosk-device",  # Audience
            "iat": now.timestamp(),  # Issued at
            "exp": expires_at.timestamp(),  # Expires
            "company_id": company_id,
            "device_type": "kiosk",
            "capabilities": capabilities or {}
        }
        
        # Use the correct PyJWT API for newer versions
        token = jwt.encode(payload, settings.SECRET_KEY, algorithm=self.jwt_algorithm)
        return token
    
    def verify_device_jwt(self, token: str) -> Optional[Dict]:
        """Verify and decode device JWT token"""
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[self.jwt_algorithm])
            
            # Verify audience
            if payload.get("aud") != "openkiosk-device":
                logger.warning(f"Invalid audience in device token: {payload.get('aud')}")
                return None
                
            return payload
            
        except jwt.ExpiredSignatureError:
            logger.info("Device token has expired")
            return None
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid device token: {e}")
            return None
    
    def generate_refresh_token(self) -> str:
        """Generate secure refresh token"""
        return secrets.token_urlsafe(32)
    
    def hash_private_key(self, private_key_pem: str) -> str:
        """Hash private key for storage (we don't store the actual private key)"""
        return hashlib.sha256(private_key_pem.encode()).hexdigest()
    
    async def authenticate_device(self, device_id: str, organization_name: str) -> Dict:
        """Create authentication credentials for a device"""
        try:
            # Generate certificate and private key
            cert_pem, private_key_pem = self.generate_device_certificate(device_id, organization_name)
            
            # Get device info for JWT
            device = await repo.get_digital_screen(device_id)
            if not device:
                raise ValueError("Device not found")
            
            company_id = device.get("company_id")
            if not company_id:
                raise ValueError("Device not associated with a company")
            
            # Create JWT token
            jwt_token = self.create_device_jwt(device_id, company_id)
            refresh_token = self.generate_refresh_token()
            
            # Store credentials
            credentials = DeviceCredentials(
                device_id=device_id,
                certificate_pem=cert_pem,
                private_key_hash=self.hash_private_key(private_key_pem),
                jwt_token=jwt_token,
                jwt_expires_at=datetime.utcnow() + timedelta(hours=self.device_token_expire_hours),
                refresh_token=refresh_token
            )
            
            saved_credentials = await repo.save_device_credentials(credentials)
            
            return {
                "success": True,
                "certificate": cert_pem,
                "private_key": private_key_pem,  # Only returned once during registration
                "jwt_token": jwt_token,
                "refresh_token": refresh_token,
                "expires_in": self.device_token_expire_hours * 3600,
                "device_id": device_id
            }
            
        except Exception as e:
            logger.error(f"Failed to authenticate device {device_id}: {e}")
            raise
    
    async def refresh_device_token(self, device_id: str, refresh_token: str) -> Optional[Dict]:
        """Refresh device JWT token using refresh token"""
        try:
            # Get current credentials
            credentials = await repo.get_device_credentials(device_id)
            if not credentials:
                logger.warning(f"No credentials found for device {device_id}")
                return None
            
            # Verify refresh token
            if credentials.get("refresh_token") != refresh_token:
                logger.warning(f"Invalid refresh token for device {device_id}")
                return None
            
            # Check if credentials are revoked
            if credentials.get("revoked"):
                logger.warning(f"Credentials revoked for device {device_id}")
                return None
            
            # Get device for new JWT
            device = await repo.get_digital_screen(device_id)
            if not device:
                logger.warning(f"Device {device_id} not found")
                return None
            
            # Create new JWT
            company_id = device.get("company_id")
            new_jwt_token = self.create_device_jwt(device_id, company_id)
            new_refresh_token = self.generate_refresh_token()
            
            # Update credentials
            updates = {
                "jwt_token": new_jwt_token,
                "jwt_expires_at": datetime.utcnow() + timedelta(hours=self.device_token_expire_hours),
                "refresh_token": new_refresh_token
            }
            
            success = await repo.update_device_credentials(device_id, updates)
            if not success:
                logger.error(f"Failed to update credentials for device {device_id}")
                return None
            
            return {
                "success": True,
                "jwt_token": new_jwt_token,
                "refresh_token": new_refresh_token,
                "expires_in": self.device_token_expire_hours * 3600
            }
            
        except Exception as e:
            logger.error(f"Failed to refresh token for device {device_id}: {e}")
            return None
    
    async def revoke_device_credentials(self, device_id: str) -> bool:
        """Revoke all credentials for a device"""
        try:
            success = await repo.revoke_device_credentials(device_id)
            if success:
                logger.info(f"Revoked credentials for device {device_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to revoke credentials for device {device_id}: {e}")
            return False
    
    async def process_device_heartbeat(self, device_id: str, heartbeat_data: Dict) -> Dict:
        """Process and store device heartbeat"""
        try:
            # Verify device exists and is authenticated
            device_info = await repo.get_device_with_credentials(device_id)
            if not device_info or not device_info.get("device"):
                return {"success": False, "error": "Device not found or not authenticated"}
            
            # Create heartbeat record
            heartbeat = DeviceHeartbeat(
                device_id=device_id,
                status=ScreenStatus(heartbeat_data.get("status", "active")),
                cpu_usage=heartbeat_data.get("cpu_usage"),
                memory_usage=heartbeat_data.get("memory_usage"),
                storage_usage=heartbeat_data.get("storage_usage"),
                temperature=heartbeat_data.get("temperature"),
                network_strength=heartbeat_data.get("network_strength"),
                bandwidth_mbps=heartbeat_data.get("bandwidth_mbps"),
                current_content_id=heartbeat_data.get("current_content_id"),
                content_errors=heartbeat_data.get("content_errors", 0),
                latitude=heartbeat_data.get("latitude"),
                longitude=heartbeat_data.get("longitude"),
                error_logs=heartbeat_data.get("error_logs", []),
                performance_score=self._calculate_performance_score(heartbeat_data)
            )
            
            # Save heartbeat
            await repo.save_device_heartbeat(heartbeat)
            
            # Update device last_seen
            await repo.update_digital_screen(device_id, {"last_seen": datetime.utcnow()})
            
            return {
                "success": True,
                "message": "Heartbeat processed successfully",
                "performance_score": heartbeat.performance_score
            }
            
        except Exception as e:
            logger.error(f"Failed to process heartbeat for device {device_id}: {e}")
            return {"success": False, "error": str(e)}
    
    def _calculate_performance_score(self, heartbeat_data: Dict) -> float:
        """Calculate overall device performance score (0-100)"""
        score = 100.0
        
        # CPU usage penalty
        cpu_usage = heartbeat_data.get("cpu_usage")
        if cpu_usage is not None:
            if cpu_usage > 80:
                score -= 20
            elif cpu_usage > 60:
                score -= 10
        
        # Memory usage penalty
        memory_usage = heartbeat_data.get("memory_usage")
        if memory_usage is not None:
            if memory_usage > 90:
                score -= 15
            elif memory_usage > 70:
                score -= 5
        
        # Storage usage penalty
        storage_usage = heartbeat_data.get("storage_usage")
        if storage_usage is not None:
            if storage_usage > 95:
                score -= 25
            elif storage_usage > 80:
                score -= 10
        
        # Network strength penalty
        network_strength = heartbeat_data.get("network_strength")
        if network_strength is not None:
            if network_strength < 30:
                score -= 20
            elif network_strength < 50:
                score -= 10
        
        # Content errors penalty
        content_errors = heartbeat_data.get("content_errors", 0)
        if content_errors > 0:
            score -= min(content_errors * 5, 30)  # Max 30 point penalty
        
        # Error logs penalty
        error_logs = heartbeat_data.get("error_logs", [])
        if error_logs:
            score -= min(len(error_logs) * 2, 20)  # Max 20 point penalty
        
        return max(0.0, min(100.0, score))

# Global device auth service instance
device_auth_service = DeviceAuthService()