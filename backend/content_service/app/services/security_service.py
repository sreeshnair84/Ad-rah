"""
Security Service - Comprehensive Security Management
===================================================

Provides enterprise-grade security features:
- Rate limiting and DDoS protection
- Security headers and CORS management
- Input validation and sanitization
- Vulnerability scanning and monitoring
- Security event logging
"""

import asyncio
import hashlib
import secrets
import time
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque
from dataclasses import dataclass
import re
import ipaddress

from fastapi import Request, HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param

from app.services.base_service import BaseService, log_service_call
from app.services.config_service import get_config


@dataclass
class SecurityEvent:
    """Security event data structure"""
    event_type: str
    severity: str  # low, medium, high, critical
    source_ip: str
    user_id: Optional[str]
    details: Dict[str, Any]
    timestamp: datetime
    blocked: bool = False


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration"""
    requests_per_minute: int
    burst_limit: int
    window_size_minutes: int = 1
    block_duration_minutes: int = 15


class IPWhitelist:
    """IP whitelist management"""

    def __init__(self):
        self.whitelist: Set[str] = set()
        self.whitelist_networks: List[ipaddress.IPv4Network] = []

    def add_ip(self, ip: str):
        """Add IP address to whitelist"""
        try:
            # Check if it's a network range
            if '/' in ip:
                network = ipaddress.IPv4Network(ip, strict=False)
                self.whitelist_networks.append(network)
            else:
                self.whitelist.add(ip)
        except Exception:
            pass  # Invalid IP format

    def is_whitelisted(self, ip: str) -> bool:
        """Check if IP is whitelisted"""
        if ip in self.whitelist:
            return True

        try:
            ip_addr = ipaddress.IPv4Address(ip)
            for network in self.whitelist_networks:
                if ip_addr in network:
                    return True
        except Exception:
            pass

        return False


class RateLimiter:
    """Advanced rate limiter with multiple strategies"""

    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.blocked_ips: Dict[str, datetime] = {}
        self.rules: Dict[str, RateLimitRule] = {}

        # Default rules
        self.rules["default"] = RateLimitRule(
            requests_per_minute=60,
            burst_limit=10,
            window_size_minutes=1,
            block_duration_minutes=15
        )

        self.rules["auth"] = RateLimitRule(
            requests_per_minute=10,
            burst_limit=3,
            window_size_minutes=1,
            block_duration_minutes=30
        )

        self.rules["upload"] = RateLimitRule(
            requests_per_minute=5,
            burst_limit=2,
            window_size_minutes=1,
            block_duration_minutes=10
        )

    def is_allowed(self, ip: str, endpoint: str = "default") -> tuple[bool, Optional[str]]:
        """Check if request is allowed"""
        current_time = datetime.utcnow()

        # Check if IP is currently blocked
        if ip in self.blocked_ips:
            if current_time < self.blocked_ips[ip]:
                return False, "IP temporarily blocked due to rate limiting"
            else:
                # Unblock IP
                del self.blocked_ips[ip]

        # Get rate limit rule
        rule = self.rules.get(endpoint, self.rules["default"])

        # Clean old requests
        cutoff_time = current_time - timedelta(minutes=rule.window_size_minutes)
        request_queue = self.requests[f"{ip}:{endpoint}"]

        while request_queue and request_queue[0] < cutoff_time:
            request_queue.popleft()

        # Check rate limits
        request_count = len(request_queue)

        if request_count >= rule.requests_per_minute:
            # Block IP
            block_until = current_time + timedelta(minutes=rule.block_duration_minutes)
            self.blocked_ips[ip] = block_until
            return False, f"Rate limit exceeded: {rule.requests_per_minute} requests per minute"

        # Check burst limit
        recent_requests = sum(1 for req_time in request_queue
                            if req_time > current_time - timedelta(seconds=60))

        if recent_requests >= rule.burst_limit:
            return False, f"Burst limit exceeded: {rule.burst_limit} requests per minute"

        # Allow request
        request_queue.append(current_time)
        return True, None

    def add_request(self, ip: str, endpoint: str = "default"):
        """Record a request for rate limiting"""
        current_time = datetime.utcnow()
        self.requests[f"{ip}:{endpoint}"].append(current_time)


class InputValidator:
    """Input validation and sanitization"""

    # Common injection patterns
    SQL_INJECTION_PATTERNS = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION)\b)",
        r"(--|#|/\*|\*/)",
        r"(\bOR\b.*=.*\bOR\b)",
        r"(\bAND\b.*=.*\bAND\b)",
        r"('(''|[^'])*')",
    ]

    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<embed[^>]*>",
        r"<object[^>]*>",
    ]

    PATH_TRAVERSAL_PATTERNS = [
        r"\.\./",
        r"\.\.\\",
        r"/etc/",
        r"/proc/",
        r"/sys/",
        r"C:\\",
        r"\\\\",
    ]

    @classmethod
    def validate_input(cls, value: str, check_types: List[str] = None) -> tuple[bool, List[str]]:
        """Validate input for security threats"""
        if not value or not isinstance(value, str):
            return True, []

        threats = []
        check_types = check_types or ["sql", "xss", "path"]

        # Check for SQL injection
        if "sql" in check_types:
            for pattern in cls.SQL_INJECTION_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    threats.append("sql_injection")
                    break

        # Check for XSS
        if "xss" in check_types:
            for pattern in cls.XSS_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    threats.append("xss")
                    break

        # Check for path traversal
        if "path" in check_types:
            for pattern in cls.PATH_TRAVERSAL_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    threats.append("path_traversal")
                    break

        return len(threats) == 0, threats

    @classmethod
    def sanitize_input(cls, value: str) -> str:
        """Sanitize input by removing/escaping dangerous characters"""
        if not value or not isinstance(value, str):
            return value

        # Basic HTML escaping
        value = value.replace("&", "&amp;")
        value = value.replace("<", "&lt;")
        value = value.replace(">", "&gt;")
        value = value.replace('"', "&quot;")
        value = value.replace("'", "&#x27;")

        # Remove null bytes
        value = value.replace("\x00", "")

        # Remove control characters except tabs, newlines, and carriage returns
        value = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', value)

        return value


class SecurityService(BaseService):
    """
    Comprehensive security service for the platform
    """

    def __init__(self):
        super().__init__()
        self.rate_limiter = RateLimiter()
        self.ip_whitelist = IPWhitelist()
        self.security_events: List[SecurityEvent] = []
        self.blocked_tokens: Set[str] = set()
        self.suspicious_ips: Set[str] = set()

        # Load security configuration
        self.config = get_config().security

        # Initialize IP whitelist
        self._init_ip_whitelist()

    def _init_ip_whitelist(self):
        """Initialize IP whitelist with common safe IPs"""
        safe_ips = [
            "127.0.0.1",      # localhost
            "::1",            # localhost IPv6
            "10.0.0.0/8",     # Private network
            "172.16.0.0/12",  # Private network
            "192.168.0.0/16", # Private network
        ]

        for ip in safe_ips:
            self.ip_whitelist.add_ip(ip)

    @log_service_call
    async def check_request_security(self, request: Request, endpoint_type: str = "default") -> tuple[bool, Optional[str]]:
        """Comprehensive security check for incoming requests"""

        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")

        # Check IP whitelist
        if self.ip_whitelist.is_whitelisted(client_ip):
            return True, None

        # Check if IP is marked as suspicious
        if client_ip in self.suspicious_ips:
            await self._log_security_event(
                "SUSPICIOUS_IP_ACCESS",
                "medium",
                client_ip,
                None,
                {"user_agent": user_agent, "endpoint": str(request.url)}
            )

        # Rate limiting check
        allowed, message = self.rate_limiter.is_allowed(client_ip, endpoint_type)
        if not allowed:
            await self._log_security_event(
                "RATE_LIMIT_EXCEEDED",
                "medium",
                client_ip,
                None,
                {"endpoint": endpoint_type, "message": message}
            )
            return False, message

        # Check for suspicious user agents
        if self._is_suspicious_user_agent(user_agent):
            await self._log_security_event(
                "SUSPICIOUS_USER_AGENT",
                "low",
                client_ip,
                None,
                {"user_agent": user_agent}
            )

        # Record the request
        self.rate_limiter.add_request(client_ip, endpoint_type)

        return True, None

    @log_service_call
    async def validate_token(self, token: str) -> tuple[bool, Optional[str]]:
        """Validate JWT token security"""

        if not token:
            return False, "No token provided"

        # Check if token is blocked
        token_hash = hashlib.sha256(token.encode()).hexdigest()
        if token_hash in self.blocked_tokens:
            return False, "Token has been revoked"

        # Additional token validation can be added here
        # - Check token age
        # - Check token source
        # - Check for token reuse patterns

        return True, None

    @log_service_call
    async def validate_input_data(self, data: Dict[str, Any], user_context: Dict = None) -> tuple[bool, List[str]]:
        """Validate input data for security threats"""

        threats = []

        for key, value in data.items():
            if isinstance(value, str):
                is_safe, found_threats = InputValidator.validate_input(value)
                if not is_safe:
                    threats.extend([f"{key}: {threat}" for threat in found_threats])

                    # Log security event for threats
                    await self._log_security_event(
                        "INPUT_VALIDATION_THREAT",
                        "high",
                        user_context.get("ip_address", "unknown") if user_context else "unknown",
                        user_context.get("user_id") if user_context else None,
                        {
                            "field": key,
                            "threats": found_threats,
                            "value_length": len(value)
                        }
                    )

        return len(threats) == 0, threats

    @log_service_call
    async def sanitize_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize input data"""

        sanitized = {}

        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key] = InputValidator.sanitize_input(value)
            elif isinstance(value, dict):
                sanitized[key] = await self.sanitize_data(value)
            elif isinstance(value, list):
                sanitized[key] = [
                    InputValidator.sanitize_input(item) if isinstance(item, str) else item
                    for item in value
                ]
            else:
                sanitized[key] = value

        return sanitized

    @log_service_call
    async def revoke_token(self, token: str, reason: str = "manual_revocation"):
        """Revoke a JWT token"""

        token_hash = hashlib.sha256(token.encode()).hexdigest()
        self.blocked_tokens.add(token_hash)

        await self._log_security_event(
            "TOKEN_REVOKED",
            "medium",
            "system",
            None,
            {"reason": reason, "token_hash": token_hash[:16]}
        )

    @log_service_call
    async def mark_ip_suspicious(self, ip: str, reason: str):
        """Mark an IP address as suspicious"""

        self.suspicious_ips.add(ip)

        await self._log_security_event(
            "IP_MARKED_SUSPICIOUS",
            "medium",
            ip,
            None,
            {"reason": reason}
        )

    def get_security_headers(self) -> Dict[str, str]:
        """Get security headers to add to responses"""

        headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';",
        }

        return headers

    def get_cors_settings(self) -> Dict[str, Any]:
        """Get CORS settings"""

        return {
            "allow_origins": self.config.allowed_origins if self.config.enable_cors else [],
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["*"],
        }

    async def get_security_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get security summary for the last N hours"""

        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_events = [
            event for event in self.security_events
            if event.timestamp > cutoff_time
        ]

        event_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        blocked_count = 0

        for event in recent_events:
            event_counts[event.event_type] += 1
            severity_counts[event.severity] += 1
            if event.blocked:
                blocked_count += 1

        return {
            "time_period_hours": hours,
            "total_events": len(recent_events),
            "blocked_requests": blocked_count,
            "events_by_type": dict(event_counts),
            "events_by_severity": dict(severity_counts),
            "blocked_tokens": len(self.blocked_tokens),
            "suspicious_ips": len(self.suspicious_ips),
            "rate_limited_ips": len(self.rate_limiter.blocked_ips),
        }

    # Private helper methods

    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP from request"""
        # Check for forwarded headers
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()

        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip

        # Fall back to client host
        if request.client:
            return request.client.host

        return "unknown"

    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is suspicious"""
        if not user_agent:
            return True

        suspicious_patterns = [
            r"bot",
            r"crawl",
            r"spider",
            r"scrape",
            r"curl",
            r"wget",
            r"python",
            r"go-http",
            r"scanner",
        ]

        user_agent_lower = user_agent.lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, user_agent_lower):
                return True

        return False

    async def _log_security_event(self,
                                event_type: str,
                                severity: str,
                                source_ip: str,
                                user_id: Optional[str],
                                details: Dict[str, Any],
                                blocked: bool = False):
        """Log a security event"""

        event = SecurityEvent(
            event_type=event_type,
            severity=severity,
            source_ip=source_ip,
            user_id=user_id,
            details=details,
            timestamp=datetime.utcnow(),
            blocked=blocked
        )

        self.security_events.append(event)

        # Keep only recent events (last 1000)
        if len(self.security_events) > 1000:
            self.security_events = self.security_events[-1000:]

        # Log to application logger
        self.logger.warning(f"Security Event: {event_type} from {source_ip} - {details}")


# Create service instance
security_service = SecurityService()

# Register in service registry
from app.services.base_service import service_registry
service_registry.register("security", security_service)