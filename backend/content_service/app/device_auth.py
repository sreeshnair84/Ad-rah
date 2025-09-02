import jwt
import uuid
import secrets
import hashlib
import logging
import json
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

# Import security modules
try:
    from app.security import audit_logger, AuditSeverity
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    logging.warning("Security module not available - using basic device authentication")

# Import monitoring modules
try:
    from app.monitoring import device_health_monitor
    HEALTH_MONITORING_AVAILABLE = True
except ImportError:
    HEALTH_MONITORING_AVAILABLE = False
    logging.warning("Health monitoring not available - using basic heartbeat processing")

class DeviceAuthService:
    """Service for handling device authentication and security"""
    
    def __init__(self):
        self.jwt_algorithm = "HS256"
        self.device_token_expire_hours = 24  # Device tokens last longer than user tokens
        self.refresh_token_expire_days = 30
        
        # Security enhancements
        self.failed_attempts = {}  # Track failed authentication attempts
        self.blocked_devices = set()  # Blocked device IDs
        self.max_failed_attempts = 5
        self.block_duration_minutes = 30
        
        # Certificate validation
        self.certificate_validation_enabled = getattr(settings, 'DEVICE_CERTIFICATE_VALIDATION', True)
        
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
            # First try to decode without audience to check if token has audience claim
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[self.jwt_algorithm])
            
            # Check audience if present
            audience = payload.get("aud")
            if audience is not None and audience != "openkiosk-device":
                logger.warning(f"Invalid audience in device token: {audience}")
                return None
            
            # If no audience claim, accept for backward compatibility
            # But log a warning
            if audience is None:
                logger.warning("Device token missing audience claim - accepting for backward compatibility")
            
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
            if not company_id:
                logger.warning(f"Device {device_id} has no company_id")
                return None
                
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
        """Process and store device heartbeat with comprehensive health monitoring"""
        try:
            # Verify device exists and is authenticated
            device_info = await repo.get_device_with_credentials(device_id)
            if not device_info or not device_info.get("device"):
                return {"success": False, "error": "Device not found or not authenticated"}
            
            # Use comprehensive health monitoring if available
            if HEALTH_MONITORING_AVAILABLE:
                # Process through health monitor for enhanced analysis
                health_result = await device_health_monitor.process_device_heartbeat(device_id, heartbeat_data)
                
                if not health_result.get("success"):
                    return health_result
                
                # Get health status and metrics
                health_status = await device_health_monitor.get_device_health_status(device_id)
                
                # Update device with health information
                device_updates = {
                    "last_seen": datetime.utcnow(),
                    "health_status": health_status.get("overall_health", "unknown"),
                    "performance_score": health_status.get("performance_score", 0),
                    "sla_compliance": health_status.get("sla_compliance", 0)
                }
                
                await repo.update_digital_screen(device_id, device_updates)
                
                # Return comprehensive health information
                return {
                    "success": True,
                    "message": "Heartbeat processed with health monitoring",
                    "health_status": health_status,
                    "alerts": health_result.get("alerts", []),
                    "recommendations": health_result.get("recommendations", [])
                }
            else:
                # Fallback to basic heartbeat processing
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
    
    def _create_device_fingerprint(self, device_info: Dict) -> str:
        """Create device fingerprint hash for security validation"""
        # Extract key device characteristics for fingerprinting
        fingerprint_data = {
            "platform": device_info.get("platform", ""),
            "model": device_info.get("model", ""),
            "brand": device_info.get("brand", ""),
            "screen_resolution": f"{device_info.get('screen_width', 0)}x{device_info.get('screen_height', 0)}",
            "os_version": device_info.get("os_version", "")
        }
        
        # Create hash of fingerprint data
        fingerprint_str = json.dumps(fingerprint_data, sort_keys=True)
        return hashlib.sha256(fingerprint_str.encode()).hexdigest()[:16]  # First 16 chars
    
    def _record_failed_attempt(self, device_id: str) -> bool:
        """Record failed authentication attempt and check if device should be blocked"""
        if device_id not in self.failed_attempts:
            self.failed_attempts[device_id] = []
        
        # Add current timestamp
        now = datetime.utcnow()
        self.failed_attempts[device_id].append(now)
        
        # Remove attempts older than 1 hour
        cutoff = now - timedelta(hours=1)
        self.failed_attempts[device_id] = [
            attempt for attempt in self.failed_attempts[device_id]
            if attempt > cutoff
        ]
        
        # Check if device should be blocked
        if len(self.failed_attempts[device_id]) >= self.max_failed_attempts:
            self.blocked_devices.add(device_id)
            
            # Log security event
            if SECURITY_AVAILABLE:
                audit_logger.log_security_event("device_blocked", {
                    "device_id": device_id,
                    "failed_attempts": len(self.failed_attempts[device_id]),
                    "block_duration_minutes": self.block_duration_minutes
                }, severity=AuditSeverity.HIGH)
            
            return True
        
        return False
    
    def _is_device_blocked(self, device_id: str) -> bool:
        """Check if device is currently blocked"""
        return device_id in self.blocked_devices
    
    def unblock_device(self, device_id: str) -> bool:
        """Manually unblock a device"""
        if device_id in self.blocked_devices:
            self.blocked_devices.remove(device_id)
            if device_id in self.failed_attempts:
                del self.failed_attempts[device_id]
            
            if SECURITY_AVAILABLE:
                audit_logger.log_security_event("device_unblocked", {
                    "device_id": device_id,
                    "manual_unblock": True
                }, severity=AuditSeverity.MEDIUM)
            
            return True
        return False
    
    async def get_device_health_summary(self, device_id: str) -> Dict:
        """Get comprehensive health summary for a device"""
        try:
            if HEALTH_MONITORING_AVAILABLE:
                # Get comprehensive health information
                health_status = await device_health_monitor.get_device_health_status(device_id)
                health_metrics = await device_health_monitor.get_device_metrics(device_id)
                sla_status = await device_health_monitor.get_sla_compliance_status(device_id)
                
                # Get recent alerts
                recent_alerts = await device_health_monitor.get_device_alerts(device_id, hours=24)
                
                return {
                    "success": True,
                    "device_id": device_id,
                    "health_status": health_status,
                    "metrics": health_metrics,
                    "sla_compliance": sla_status,
                    "recent_alerts": recent_alerts,
                    "monitoring_available": True
                }
            else:
                # Basic device information
                device = await repo.get_digital_screen(device_id)
                if not device:
                    return {"success": False, "error": "Device not found"}
                
                # Get recent heartbeat
                recent_heartbeat = await repo.get_latest_device_heartbeat(device_id)
                
                return {
                    "success": True,
                    "device_id": device_id,
                    "basic_info": {
                        "last_seen": device.get("last_seen"),
                        "status": device.get("status", "unknown"),
                        "recent_heartbeat": recent_heartbeat
                    },
                    "monitoring_available": False
                }
                
        except Exception as e:
            logger.error(f"Failed to get health summary for device {device_id}: {e}")
            return {"success": False, "error": str(e)}
    
    async def validate_device_certificate(self, device_id: str, cert_pem: str) -> bool:
        """Validate device certificate"""
        if not self.certificate_validation_enabled:
            return True
        
        try:
            # Load and validate certificate
            cert = x509.load_pem_x509_certificate(cert_pem.encode())
            
            # Check if certificate is still valid
            now = datetime.utcnow()
            if now < cert.not_valid_before or now > cert.not_valid_after:
                logger.warning(f"Certificate for device {device_id} has expired")
                if SECURITY_AVAILABLE:
                    audit_logger.log_security_event("expired_certificate", {
                        "device_id": device_id,
                        "not_valid_before": cert.not_valid_before.isoformat(),
                        "not_valid_after": cert.not_valid_after.isoformat()
                    }, severity=AuditSeverity.HIGH)
                return False
            
            # Check certificate subject
            common_name = None
            for attribute in cert.subject:
                if attribute.oid == NameOID.COMMON_NAME:
                    common_name = attribute.value
                    break
            
            if common_name != f"Device-{device_id}":
                logger.warning(f"Certificate common name mismatch for device {device_id}")
                if SECURITY_AVAILABLE:
                    audit_logger.log_security_event("certificate_mismatch", {
                        "device_id": device_id,
                        "expected_cn": f"Device-{device_id}",
                        "actual_cn": common_name
                    }, severity=AuditSeverity.HIGH)
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Certificate validation failed for device {device_id}: {e}")
            if SECURITY_AVAILABLE:
                audit_logger.log_security_event("certificate_validation_error", {
                    "device_id": device_id,
                    "error": str(e)
                }, severity=AuditSeverity.HIGH)
            return False

# Global device auth service instance
device_auth_service = DeviceAuthService()