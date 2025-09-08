"""
Enhanced Device Registration Security System
Implements comprehensive security features for device registration including:
- Rate limiting and IP blocking
- Device fingerprinting and risk scoring
- Enhanced audit logging and monitoring
- Real-time security statistics
"""

import time
import hashlib
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, Counter
import asyncio
import json
import ipaddress
from fastapi import Request, HTTPException

from app.models import DeviceRegistrationCreate, DeviceFingerprint, DeviceCapabilities
from app.repo import repo
# from app.api.device import register_device as basic_register_device  # Module no longer exists

logger = logging.getLogger(__name__)

@dataclass
class SecurityAttempt:
    """Track registration attempts for security analysis"""
    ip_address: str
    timestamp: datetime
    success: bool
    risk_score: float
    device_name: str = ""
    user_agent: str = ""
    failure_reason: str = ""

@dataclass
class SecurityStats:
    """Security statistics for monitoring"""
    total_attempts: int = 0
    successful_registrations: int = 0
    failed_registrations: int = 0
    blocked_ip_addresses: int = 0
    recent_attempts_last_hour: int = 0
    active_monitoring_ips: int = 0
    total_registered_devices: int = 0
    high_risk_registrations: int = 0

class EnhancedDeviceRegistration:
    """Enhanced device registration with comprehensive security features"""
    
    def __init__(self):
        # Security configuration
        self.max_attempts_per_hour = 5
        self.max_attempts_per_day = 20
        self.block_duration_minutes = 30
        self.high_risk_threshold = 7.0
        self.cleanup_interval_hours = 24
        
        # Security tracking
        self.failed_attempts: Dict[str, List[datetime]] = defaultdict(list)
        self.blocked_ips: set = set()
        self.ip_blocks: Dict[str, datetime] = {}
        self.registration_attempts: List[SecurityAttempt] = []
        self.risk_scores: Dict[str, float] = {}
        
        # Statistics
        self.stats = SecurityStats()
        
        # Initialize cleanup task flag
        self._cleanup_task = None
        self._ensure_cleanup_task()
    
    def _ensure_cleanup_task(self):
        """Ensure cleanup task is running"""
        try:
            loop = asyncio.get_running_loop()
            if self._cleanup_task is None or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
        except RuntimeError:
            # No event loop running, task will be created when needed
            pass
    
    async def register_device_enhanced(
        self, 
        device_data: DeviceRegistrationCreate, 
        request: Request
    ) -> Dict[str, Any]:
        """
        Enhanced device registration with security features
        """
        # Ensure cleanup task is running
        self._ensure_cleanup_task()
        
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        logger.info(f"Enhanced registration attempt from IP: {client_ip}")
        
        try:
            # 1. Rate limiting and IP blocking check
            await self._check_rate_limits(client_ip)
            
            # 2. Risk assessment
            risk_score = await self._calculate_risk_score(device_data, request)
            
            # 3. Enhanced validation
            await self._enhanced_validation(device_data, risk_score)
            
            # 4. Perform registration using existing logic
            result = await basic_register_device(device_data, request)
            
            # 5. Post-registration security processing
            await self._post_registration_processing(
                client_ip, device_data, risk_score, True, result
            )
            
            # 6. Update statistics
            self._update_stats(True)
            
            # 7. Add security metadata to response
            result["security"] = {
                "risk_score": risk_score,
                "security_level": self._get_security_level(risk_score),
                "registration_method": "enhanced"
            }
            
            logger.info(f"Enhanced registration successful for {device_data.device_name}")
            return result
            
        except Exception as e:
            # Log failed attempt
            await self._record_failed_attempt(
                client_ip, device_data.device_name, user_agent, str(e)
            )
            
            # Update failure statistics
            self._update_stats(False)
            
            logger.warning(f"Enhanced registration failed: {e}")
            raise
    
    async def _check_rate_limits(self, ip_address: str) -> None:
        """Check rate limits and IP blocking"""
        
        # Check if IP is currently blocked
        if ip_address in self.blocked_ips:
            block_time = self.ip_blocks.get(ip_address)
            if block_time and datetime.utcnow() < block_time + timedelta(minutes=self.block_duration_minutes):
                raise HTTPException(
                    status_code=429,
                    detail=f"IP address temporarily blocked due to suspicious activity. Try again later."
                )
            else:
                # Block expired, remove from blocked list
                self.blocked_ips.discard(ip_address)
                if ip_address in self.ip_blocks:
                    del self.ip_blocks[ip_address]
        
        # Check hourly rate limit
        now = datetime.utcnow()
        hour_ago = now - timedelta(hours=1)
        recent_attempts = [
            attempt for attempt in self.failed_attempts[ip_address]
            if attempt > hour_ago
        ]
        
        if len(recent_attempts) >= self.max_attempts_per_hour:
            raise HTTPException(
                status_code=429,
                detail=f"Too many registration attempts. Maximum {self.max_attempts_per_hour} per hour allowed."
            )
        
        # Check daily rate limit
        day_ago = now - timedelta(days=1)
        daily_attempts = [
            attempt for attempt in self.failed_attempts[ip_address]
            if attempt > day_ago
        ]
        
        if len(daily_attempts) >= self.max_attempts_per_day:
            raise HTTPException(
                status_code=429,
                detail=f"Daily registration limit exceeded. Maximum {self.max_attempts_per_day} per day allowed."
            )
    
    async def _calculate_risk_score(
        self, 
        device_data: DeviceRegistrationCreate, 
        request: Request
    ) -> float:
        """Calculate risk score for the registration attempt"""
        
        risk_score = 0.0
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # 1. IP-based risk (previous failures)
        failed_count = len(self.failed_attempts.get(client_ip, []))
        risk_score += min(failed_count * 0.5, 3.0)  # Max 3.0 points
        
        # 2. Temporal risk (off-hours registration)
        current_hour = datetime.utcnow().hour
        if current_hour < 6 or current_hour > 22:  # Outside 6 AM - 10 PM
            risk_score += 1.0
        
        # 3. Device fingerprint risk
        fingerprint_data = getattr(device_data, 'fingerprint', None)
        if not fingerprint_data:
            risk_score += 2.0  # No fingerprint data
        
        # 4. User agent analysis
        if not user_agent:
            risk_score += 1.5  # No user agent
        elif "bot" in user_agent.lower() or "crawler" in user_agent.lower():
            risk_score += 3.0  # Bot detection
        
        # 5. Multiple rapid attempts from same IP
        recent_attempts = [
            attempt for attempt in self.registration_attempts
            if attempt.ip_address == client_ip and 
            attempt.timestamp > datetime.utcnow() - timedelta(minutes=10)
        ]
        if len(recent_attempts) > 2:
            risk_score += 2.0
        
        # 6. Device name patterns (suspicious names)
        suspicious_patterns = ["test", "temp", "fake", "bot", "admin"]
        if any(pattern in device_data.device_name.lower() for pattern in suspicious_patterns):
            risk_score += 1.5
        
        logger.debug(f"Calculated risk score {risk_score} for IP {client_ip}")
        return risk_score
    
    async def _enhanced_validation(
        self, 
        device_data: DeviceRegistrationCreate, 
        risk_score: float
    ) -> None:
        """Enhanced validation beyond basic checks"""
        
        # 1. High-risk threshold check
        if risk_score >= self.high_risk_threshold:
            # Still allow registration but flag for review
            logger.warning(f"High-risk registration detected: {device_data.device_name} (score: {risk_score})")
        
        # 2. Device name uniqueness check (enhanced)
        existing_devices = await repo.list_digital_screens()
        device_names = [device.get("name", "").lower() for device in existing_devices]
        if device_data.device_name.lower() in device_names:
            raise HTTPException(
                status_code=400,
                detail="Device name already exists. Please choose a unique name."
            )
        
        # 3. Registration key age validation
        key_data = await repo.get_device_registration_key(device_data.registration_key)
        if key_data:
            created_at = key_data.get("created_at")
            if created_at:
                key_age = datetime.utcnow() - created_at
                if key_age.days > 30:  # Key older than 30 days
                    logger.warning(f"Old registration key used: {key_age.days} days old")
    
    async def _post_registration_processing(
        self,
        ip_address: str,
        device_data: DeviceRegistrationCreate,
        risk_score: float,
        success: bool,
        result: Dict[str, Any]
    ) -> None:
        """Post-registration security processing"""
        
        # Record the attempt
        attempt = SecurityAttempt(
            ip_address=ip_address,
            timestamp=datetime.utcnow(),
            success=success,
            risk_score=risk_score,
            device_name=device_data.device_name
        )
        self.registration_attempts.append(attempt)
        
        # High-risk device handling
        if risk_score >= self.high_risk_threshold and success:
            # Flag device for manual review
            device_id = result.get("device_id")
            if device_id:
                logger.warning(f"Device {device_id} flagged for manual review (risk score: {risk_score})")
                # Here you could update device status to 'PENDING' for manual review
        
        # Clear failed attempts for successful registration
        if success and ip_address in self.failed_attempts:
            self.failed_attempts[ip_address].clear()
    
    async def _record_failed_attempt(
        self,
        ip_address: str,
        device_name: str,
        user_agent: str,
        failure_reason: str
    ) -> None:
        """Record failed registration attempt"""
        
        now = datetime.utcnow()
        self.failed_attempts[ip_address].append(now)
        
        # Record detailed attempt
        attempt = SecurityAttempt(
            ip_address=ip_address,
            timestamp=now,
            success=False,
            risk_score=0.0,  # Will be calculated if needed
            device_name=device_name,
            user_agent=user_agent,
            failure_reason=failure_reason
        )
        self.registration_attempts.append(attempt)
        
        # Check if IP should be blocked
        recent_failures = [
            attempt for attempt in self.failed_attempts[ip_address]
            if attempt > now - timedelta(hours=1)
        ]
        
        if len(recent_failures) >= 10:  # Block after 10 failures in an hour
            self.blocked_ips.add(ip_address)
            self.ip_blocks[ip_address] = now
            logger.warning(f"IP {ip_address} blocked due to {len(recent_failures)} failed attempts")
    
    def _update_stats(self, success: bool) -> None:
        """Update security statistics"""
        self.stats.total_attempts += 1
        
        if success:
            self.stats.successful_registrations += 1
        else:
            self.stats.failed_registrations += 1
        
        # Update other stats
        self.stats.blocked_ip_addresses = len(self.blocked_ips)
        
        # Recent attempts (last hour)
        hour_ago = datetime.utcnow() - timedelta(hours=1)
        self.stats.recent_attempts_last_hour = len([
            attempt for attempt in self.registration_attempts
            if attempt.timestamp > hour_ago
        ])
        
        # Active monitoring IPs
        self.stats.active_monitoring_ips = len(self.failed_attempts)
    
    async def get_registration_stats(self) -> Dict[str, Any]:
        """Get current registration statistics"""
        
        # Get total registered devices from database
        devices = await repo.list_digital_screens()
        self.stats.total_registered_devices = len(devices)
        
        # Calculate success rate
        success_rate = 0.0
        if self.stats.total_attempts > 0:
            success_rate = (self.stats.successful_registrations / self.stats.total_attempts) * 100
        
        return {
            "total_registration_attempts": self.stats.total_attempts,
            "successful_registrations": self.stats.successful_registrations,
            "failed_registrations": self.stats.failed_registrations,
            "success_rate": round(success_rate, 1),
            "blocked_ip_addresses": self.stats.blocked_ip_addresses,
            "recent_attempts_last_hour": self.stats.recent_attempts_last_hour,
            "active_monitoring_ips": self.stats.active_monitoring_ips,
            "total_registered_devices": self.stats.total_registered_devices,
            "high_risk_registrations": self.stats.high_risk_registrations
        }
    
    async def get_security_status(self) -> Dict[str, Any]:
        """Get current security status"""
        
        stats = await self.get_registration_stats()
        
        # Determine security level
        level = "normal"
        if stats["blocked_ip_addresses"] > 0 or stats["failed_registrations"] > 10:
            level = "elevated"
        if stats["blocked_ip_addresses"] > 5 or stats["failed_registrations"] > 50:
            level = "high"
        
        return {
            "level": level,
            "blocked_ip_count": stats["blocked_ip_addresses"],
            "recent_failed_attempts": stats["failed_registrations"],
            "device_status_breakdown": {
                "active": stats["total_registered_devices"],
                "pending": 0  # Would need to query for pending devices
            },
            "total_monitored_ips": stats["active_monitoring_ips"],
            "last_updated": datetime.utcnow().isoformat()
        }
    
    async def unblock_ip(self, ip_address: str) -> bool:
        """Manually unblock an IP address"""
        
        if ip_address in self.blocked_ips:
            self.blocked_ips.discard(ip_address)
            if ip_address in self.ip_blocks:
                del self.ip_blocks[ip_address]
            
            # Clear failed attempts
            if ip_address in self.failed_attempts:
                self.failed_attempts[ip_address].clear()
            
            logger.info(f"IP {ip_address} manually unblocked")
            return True
        
        return False
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request"""
        # Check for forwarded headers first
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    def _get_security_level(self, risk_score: float) -> str:
        """Get security level based on risk score"""
        if risk_score < 3.0:
            return "low"
        elif risk_score < 5.0:
            return "medium"
        elif risk_score < 7.0:
            return "high"
        else:
            return "critical"
    
    async def _periodic_cleanup(self) -> None:
        """Periodic cleanup of old data"""
        while True:
            try:
                await asyncio.sleep(3600)  # Run every hour
                
                cutoff_time = datetime.utcnow() - timedelta(hours=self.cleanup_interval_hours)
                
                # Clean old failed attempts
                for ip in list(self.failed_attempts.keys()):
                    self.failed_attempts[ip] = [
                        attempt for attempt in self.failed_attempts[ip]
                        if attempt > cutoff_time
                    ]
                    
                    # Remove empty entries
                    if not self.failed_attempts[ip]:
                        del self.failed_attempts[ip]
                
                # Clean old registration attempts
                self.registration_attempts = [
                    attempt for attempt in self.registration_attempts
                    if attempt.timestamp > cutoff_time
                ]
                
                # Clean expired IP blocks
                expired_blocks = [
                    ip for ip, block_time in self.ip_blocks.items()
                    if datetime.utcnow() > block_time + timedelta(minutes=self.block_duration_minutes)
                ]
                
                for ip in expired_blocks:
                    self.blocked_ips.discard(ip)
                    del self.ip_blocks[ip]
                
                logger.debug("Security data cleanup completed")
                
            except Exception as e:
                logger.error(f"Error in security cleanup: {e}")

# Global instance
enhanced_device_registration = EnhancedDeviceRegistration()
