"""
Enhanced Device Registration System
Provides secure, rate-limited device registration with comprehensive security features
"""
import logging
import asyncio
import hashlib
import json
import secrets
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from collections import defaultdict
from dataclasses import dataclass, asdict

from fastapi import Request, HTTPException
from app.models import (
    DeviceRegistrationCreate, DeviceCapabilities, DeviceFingerprint,
    DeviceType, DigitalScreen, ScreenOrientation, ScreenStatus
)
from app.repo import repo

logger = logging.getLogger(__name__)

@dataclass
class RegistrationAttempt:
    """Track registration attempts for rate limiting"""
    ip_address: str
    timestamp: datetime
    success: bool
    device_name: Optional[str] = None
    registration_key: Optional[str] = None
    failure_reason: Optional[str] = None

@dataclass
class DeviceSecurityProfile:
    """Enhanced security profile for device registration"""
    fingerprint_hash: str
    ip_address: str
    user_agent: Optional[str]
    timestamp: datetime
    risk_score: float
    geo_location: Optional[Dict] = None

class EnhancedDeviceRegistration:
    """Enhanced device registration with security features"""
    
    def __init__(self):
        # Rate limiting storage (in production, use Redis)
        self.registration_attempts = defaultdict(list)
        self.failed_attempts = defaultdict(int)
        self.blocked_ips = set()
        
        # Security settings
        self.max_attempts_per_hour = 5
        self.max_attempts_per_day = 20
        self.block_duration_minutes = 30
        self.high_risk_threshold = 7.0
        
    def _cleanup_old_attempts(self):
        """Clean up old registration attempts"""
        cutoff = datetime.utcnow() - timedelta(days=1)
        for ip, attempts in list(self.registration_attempts.items()):
            self.registration_attempts[ip] = [
                attempt for attempt in attempts 
                if attempt.timestamp > cutoff
            ]
            if not self.registration_attempts[ip]:
                del self.registration_attempts[ip]
    
    def _check_rate_limit(self, ip_address: str) -> Tuple[bool, str]:
        """Check if IP address is rate limited"""
        self._cleanup_old_attempts()
        
        # Check if IP is blocked
        if ip_address in self.blocked_ips:
            return False, "IP address is temporarily blocked due to suspicious activity"
        
        attempts = self.registration_attempts[ip_address]
        now = datetime.utcnow()
        
        # Check hourly limit
        hour_ago = now - timedelta(hours=1)
        recent_attempts = [a for a in attempts if a.timestamp > hour_ago]
        if len(recent_attempts) >= self.max_attempts_per_hour:
            return False, f"Too many registration attempts. Maximum {self.max_attempts_per_hour} per hour"
        
        # Check daily limit
        day_ago = now - timedelta(days=1)
        daily_attempts = [a for a in attempts if a.timestamp > day_ago]
        if len(daily_attempts) >= self.max_attempts_per_day:
            return False, f"Too many registration attempts. Maximum {self.max_attempts_per_day} per day"
        
        return True, "Rate limit passed"
    
    def _log_registration_attempt(self, ip_address: str, success: bool, 
                                device_name: str = None, registration_key: str = None,
                                failure_reason: str = None):
        """Log registration attempt for audit and rate limiting"""
        attempt = RegistrationAttempt(
            ip_address=ip_address,
            timestamp=datetime.utcnow(),
            success=success,
            device_name=device_name,
            registration_key=registration_key[:8] + "..." if registration_key else None,
            failure_reason=failure_reason
        )
        
        self.registration_attempts[ip_address].append(attempt)
        
        # Track consecutive failures
        if not success:
            self.failed_attempts[ip_address] += 1
            if self.failed_attempts[ip_address] >= 10:  # Block after 10 failures
                self.blocked_ips.add(ip_address)
                logger.warning(f"Blocked IP {ip_address} due to repeated registration failures")
        else:
            self.failed_attempts[ip_address] = 0  # Reset on success
        
        # Audit log
        logger.info(f"Device registration attempt: IP={ip_address}, Success={success}, "
                   f"Device={device_name}, Reason={failure_reason}")
    
    def _extract_device_fingerprint(self, request: Request, 
                                   device_data: DeviceRegistrationCreate) -> DeviceFingerprint:
        """Extract comprehensive device fingerprint"""
        headers = request.headers
        
        # Generate hardware fingerprint from available data
        fingerprint_components = [
            device_data.device_name,
            device_data.organization_code,
            headers.get("user-agent", ""),
            headers.get("accept-language", ""),
            str(getattr(device_data, 'capabilities', {}))
        ]
        
        hardware_id = hashlib.sha256(
            "|".join(fingerprint_components).encode()
        ).hexdigest()[:16]
        
        # Extract network information
        mac_addresses = []
        if hasattr(device_data, 'fingerprint') and device_data.fingerprint:
            existing_fp = device_data.fingerprint
            mac_addresses = existing_fp.get("mac_addresses", [])
        
        # Create comprehensive fingerprint
        fingerprint = DeviceFingerprint(
            hardware_id=f"hw-{hardware_id}",
            mac_addresses=mac_addresses,
            device_serial=getattr(device_data, 'serial_number', None),
            manufacturer=getattr(device_data, 'manufacturer', None),
            model=getattr(device_data, 'model', None),
            timezone=headers.get("timezone"),
            locale=headers.get("accept-language", "").split(',')[0] if headers.get("accept-language") else None
        )
        
        return fingerprint
    
    def _calculate_risk_score(self, ip_address: str, fingerprint: DeviceFingerprint,
                            request: Request) -> float:
        """Calculate security risk score for device registration"""
        risk_score = 0.0
        
        # IP-based risk factors
        failed_count = self.failed_attempts.get(ip_address, 0)
        risk_score += min(failed_count * 0.5, 3.0)  # Max 3 points for failed attempts
        
        # Time-based risk (registrations outside business hours)
        current_hour = datetime.utcnow().hour
        if current_hour < 6 or current_hour > 22:  # Outside 6 AM - 10 PM UTC
            risk_score += 1.0
        
        # Device fingerprint risk factors
        if not fingerprint.hardware_id or len(fingerprint.hardware_id) < 10:
            risk_score += 2.0  # Weak fingerprint
        
        if not fingerprint.mac_addresses:
            risk_score += 1.0  # No MAC addresses provided
        
        # User-Agent analysis
        user_agent = request.headers.get("user-agent", "").lower()
        if not user_agent:
            risk_score += 1.5  # No user agent
        elif any(bot in user_agent for bot in ["bot", "crawler", "spider", "scraper"]):
            risk_score += 3.0  # Bot/crawler detected
        
        # Request frequency risk
        recent_attempts = len([
            attempt for attempt in self.registration_attempts[ip_address]
            if attempt.timestamp > datetime.utcnow() - timedelta(minutes=10)
        ])
        if recent_attempts > 2:
            risk_score += 2.0  # Multiple recent attempts
        
        return min(risk_score, 10.0)  # Cap at 10.0
    
    async def _validate_registration_key_enhanced(self, registration_key: str, 
                                                ip_address: str) -> Tuple[bool, Dict, str]:
        """Enhanced registration key validation"""
        # Get registration key data
        key_data = await repo.get_device_registration_key(registration_key)
        if not key_data:
            return False, None, "Invalid registration key"
        
        # Check if already used
        if key_data.get("used"):
            return False, key_data, "Registration key has already been used"
        
        # Check expiration
        expires_at = key_data.get("expires_at")
        if expires_at:
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at)
            if expires_at < datetime.utcnow():
                return False, key_data, "Registration key has expired"
        
        # Additional security checks
        created_at = key_data.get("created_at")
        if created_at:
            if isinstance(created_at, str):
                created_at = datetime.fromisoformat(created_at)
            # Keys older than 30 days are suspicious
            if (datetime.utcnow() - created_at).days > 30:
                logger.warning(f"Old registration key used: {registration_key[:8]}...")
        
        return True, key_data, "Registration key valid"
    
    async def _check_device_name_uniqueness(self, device_name: str, 
                                          company_id: str) -> Tuple[bool, str]:
        """Check if device name is unique within company"""
        existing_devices = await repo.list_digital_screens(company_id)
        
        # Check exact match
        if any(device.get("name") == device_name for device in existing_devices):
            return False, "Device name already exists for this company"
        
        # Check similar names (potential typos or duplicates)
        similar_names = [
            device.get("name") for device in existing_devices
            if device.get("name") and 
            device.get("name").lower().replace(" ", "").replace("-", "") == 
            device_name.lower().replace(" ", "").replace("-", "")
        ]
        
        if similar_names:
            return False, f"Similar device name already exists: {similar_names[0]}"
        
        return True, "Device name is unique"
    
    def _get_client_info(self, request: Request) -> Dict:
        """Extract comprehensive client information"""
        headers = request.headers
        
        # Get IP address with proxy support
        client_ip = "unknown"
        forwarded = headers.get("X-Forwarded-For")
        if forwarded:
            client_ip = forwarded.split(",")[0].strip()
        elif headers.get("X-Real-IP"):
            client_ip = headers.get("X-Real-IP")
        elif request.client:
            client_ip = request.client.host
        
        return {
            "ip_address": client_ip,
            "user_agent": headers.get("User-Agent"),
            "accept_language": headers.get("Accept-Language"),
            "accept_encoding": headers.get("Accept-Encoding"),
            "connection": headers.get("Connection"),
            "host": headers.get("Host"),
            "referer": headers.get("Referer"),
            "origin": headers.get("Origin")
        }
    
    async def register_device_enhanced(self, device_data: DeviceRegistrationCreate, 
                                     request: Request) -> Dict:
        """Enhanced device registration with comprehensive security"""
        client_info = self._get_client_info(request)
        ip_address = client_info["ip_address"]
        
        try:
            # Step 1: Rate limiting check
            rate_ok, rate_message = self._check_rate_limit(ip_address)
            if not rate_ok:
                self._log_registration_attempt(
                    ip_address, False, device_data.device_name, 
                    device_data.registration_key, rate_message
                )
                raise HTTPException(status_code=429, detail=rate_message)
            
            # Step 2: Enhanced registration key validation
            key_valid, key_data, key_message = await self._validate_registration_key_enhanced(
                device_data.registration_key, ip_address
            )
            if not key_valid:
                self._log_registration_attempt(
                    ip_address, False, device_data.device_name,
                    device_data.registration_key, key_message
                )
                raise HTTPException(status_code=400, detail=key_message)
            
            # Step 3: Company validation
            company_id = key_data.get("company_id")
            companies = await repo.list_companies()
            company = next((c for c in companies if c.get("id") == company_id), None)
            if not company:
                self._log_registration_attempt(
                    ip_address, False, device_data.device_name,
                    device_data.registration_key, "Company not found"
                )
                raise HTTPException(status_code=400, detail="Company associated with key not found")
            
            # Step 4: Device name uniqueness check
            name_unique, name_message = await self._check_device_name_uniqueness(
                device_data.device_name, company_id
            )
            if not name_unique:
                self._log_registration_attempt(
                    ip_address, False, device_data.device_name,
                    device_data.registration_key, name_message
                )
                raise HTTPException(status_code=400, detail=name_message)
            
            # Step 5: Enhanced device fingerprinting
            fingerprint = self._extract_device_fingerprint(request, device_data)
            
            # Step 6: Risk assessment
            risk_score = self._calculate_risk_score(ip_address, fingerprint, request)
            
            # Step 7: High-risk registration handling
            if risk_score >= self.high_risk_threshold:
                logger.warning(f"High-risk device registration attempt: "
                             f"IP={ip_address}, Risk={risk_score}, Device={device_data.device_name}")
                
                # For high-risk registrations, require additional verification
                # In production, this could trigger admin approval or additional checks
                security_profile = DeviceSecurityProfile(
                    fingerprint_hash=hashlib.sha256(json.dumps(asdict(fingerprint), sort_keys=True).encode()).hexdigest(),
                    ip_address=ip_address,
                    user_agent=client_info.get("user_agent"),
                    timestamp=datetime.utcnow(),
                    risk_score=risk_score
                )
                
                # For now, log and continue, but mark for review
                logger.warning(f"High-risk device registered, requires review: {asdict(security_profile)}")
            
            # Step 8: Create device record
            device_id = secrets.token_urlsafe(16)  # More secure ID generation
            
            # Enhanced capabilities extraction
            capabilities = DeviceCapabilities()
            if hasattr(device_data, 'capabilities') and device_data.capabilities:
                capabilities = device_data.capabilities
            
            # Create comprehensive device record
            screen_record = DigitalScreen(
                id=device_id,
                name=device_data.device_name,
                description=f"Auto-registered device - {company.get('name')} - Risk Score: {risk_score:.1f}",
                company_id=company_id,
                location=getattr(device_data, 'location_description', "Location TBD"),
                resolution_width=capabilities.max_resolution_width,
                resolution_height=capabilities.max_resolution_height,
                orientation=ScreenOrientation.LANDSCAPE,
                aspect_ratio=device_data.aspect_ratio or "16:9",
                registration_key=device_data.registration_key,
                status=ScreenStatus.ACTIVE if risk_score < self.high_risk_threshold else ScreenStatus.PENDING,
                ip_address=ip_address,
                mac_address=fingerprint.mac_addresses[0] if fingerprint.mac_addresses else None,
                last_seen=datetime.utcnow(),
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                device_type=getattr(device_data, 'device_type', DeviceType.KIOSK),
                capabilities=capabilities.model_dump() if capabilities else None,
                fingerprint=fingerprint.model_dump() if fingerprint else None
            )
            
            # Step 9: Save device
            await repo.save_digital_screen(screen_record)
            
            # Step 10: Generate authentication credentials
            from app.device_auth import device_auth_service
            auth_result = await device_auth_service.authenticate_device(
                device_id, company.get('name')
            )
            
            # Step 11: Mark registration key as used
            await repo.mark_key_used(key_data["id"], device_id)
            
            # Step 12: Log successful registration
            self._log_registration_attempt(
                ip_address, True, device_data.device_name,
                device_data.registration_key, None
            )
            
            logger.info(f"Successfully registered device {device_id} for company {company_id} "
                       f"(Risk Score: {risk_score:.1f})")
            
            return {
                "success": True,
                "device_id": device_id,
                "message": "Device registered successfully with enhanced security",
                "organization_code": device_data.organization_code,
                "company_name": company.get("name"),
                "ip_address": ip_address,
                "risk_score": risk_score,
                "status": screen_record.status.value,
                "requires_review": risk_score >= self.high_risk_threshold,
                # Authentication credentials
                "certificate": auth_result.get("certificate"),
                "private_key": auth_result.get("private_key"),
                "jwt_token": auth_result.get("jwt_token"),
                "refresh_token": auth_result.get("refresh_token"),
                "token_expires_in": auth_result.get("expires_in"),
                # Security information
                "fingerprint_id": fingerprint.hardware_id,
                "registration_timestamp": datetime.utcnow().isoformat()
            }
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Device registration error: {str(e)}")
            self._log_registration_attempt(
                ip_address, False, device_data.device_name,
                device_data.registration_key, f"Internal error: {str(e)}"
            )
            raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
    
    async def get_registration_stats(self) -> Dict:
        """Get registration statistics for monitoring"""
        self._cleanup_old_attempts()
        
        total_attempts = sum(len(attempts) for attempts in self.registration_attempts.values())
        successful_attempts = sum(
            len([a for a in attempts if a.success])
            for attempts in self.registration_attempts.values()
        )
        
        blocked_ips = len(self.blocked_ips)
        
        # Recent activity (last hour)
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        recent_attempts = sum(
            len([a for a in attempts if a.timestamp > hour_ago])
            for attempts in self.registration_attempts.values()
        )
        
        return {
            "total_registration_attempts": total_attempts,
            "successful_registrations": successful_attempts,
            "failed_registrations": total_attempts - successful_attempts,
            "success_rate": (successful_attempts / total_attempts * 100) if total_attempts > 0 else 0,
            "blocked_ip_addresses": blocked_ips,
            "recent_attempts_last_hour": recent_attempts,
            "active_monitoring_ips": len(self.registration_attempts),
            "timestamp": datetime.utcnow().isoformat()
        }

# Global instance
enhanced_device_registration = EnhancedDeviceRegistration()