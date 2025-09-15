"""
Security Middleware for HTTP Security Headers and Content Security Policy
Implements comprehensive security headers and request validation
"""

import logging
from typing import Callable, Dict, Any, Optional
from fastapi import FastAPI, Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from fastapi.responses import JSONResponse
import time
import re
from urllib.parse import urlparse
import secrets
import hashlib

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses"""
    
    def __init__(
        self,
        app: FastAPI,
        csp_config: Optional[Dict[str, Any]] = None,
        hsts_max_age: int = 31536000,  # 1 year
        enable_hsts: bool = True,
        enable_nosniff: bool = True,
        enable_xss_protection: bool = True,
        enable_frame_options: bool = True,
        enable_referrer_policy: bool = True,
        allowed_hosts: Optional[list] = None
    ):
        super().__init__(app)
        self.csp_config = csp_config or self._default_csp_config()
        self.hsts_max_age = hsts_max_age
        self.enable_hsts = enable_hsts
        self.enable_nosniff = enable_nosniff
        self.enable_xss_protection = enable_xss_protection
        self.enable_frame_options = enable_frame_options
        self.enable_referrer_policy = enable_referrer_policy
        self.allowed_hosts = allowed_hosts or []
        
    def _default_csp_config(self) -> Dict[str, Any]:
        """Default Content Security Policy configuration"""
        return {
            "default-src": ["'self'"],
            "script-src": ["'self'", "'unsafe-inline'"],  # More restrictive in production
            "style-src": ["'self'", "'unsafe-inline'"],
            "img-src": ["'self'", "data:", "https:"],
            "font-src": ["'self'", "https://fonts.gstatic.com"],
            "connect-src": ["'self'"],
            "frame-src": ["'none'"],
            "object-src": ["'none'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"],
            "frame-ancestors": ["'none'"],
            "upgrade-insecure-requests": True
        }
    
    def _build_csp_header(self, nonce: Optional[str] = None) -> str:
        """Build Content Security Policy header string"""
        csp_parts = []
        
        for directive, values in self.csp_config.items():
            if directive == "upgrade-insecure-requests" and values:
                csp_parts.append("upgrade-insecure-requests")
            elif isinstance(values, list):
                directive_value = " ".join(values)
                if nonce and directive in ["script-src", "style-src"]:
                    directive_value += f" 'nonce-{nonce}'"
                csp_parts.append(f"{directive} {directive_value}")
        
        return "; ".join(csp_parts)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and add security headers to response"""
        start_time = time.time()
        
        # Host validation
        if self.allowed_hosts and request.url.hostname not in self.allowed_hosts:
            logger.warning(f"Host validation failed for: {request.url.hostname}")
            return JSONResponse(
                status_code=400,
                content={"error": "Invalid host"}
            )
        
        # Generate nonce for CSP
        nonce = secrets.token_urlsafe(16)
        request.state.csp_nonce = nonce
        
        try:
            response = await call_next(request)
        except Exception as e:
            logger.error(f"Request processing failed: {e}")
            raise
        
        # Add security headers
        self._add_security_headers(response, nonce)
        
        # Add timing header (for monitoring)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        
        return response
    
    def _add_security_headers(self, response: Response, nonce: str):
        """Add all security headers to the response"""
        
        # Content Security Policy
        csp_header = self._build_csp_header(nonce)
        response.headers["Content-Security-Policy"] = csp_header
        
        # HTTP Strict Transport Security
        if self.enable_hsts:
            response.headers["Strict-Transport-Security"] = f"max-age={self.hsts_max_age}; includeSubDomains; preload"
        
        # X-Content-Type-Options
        if self.enable_nosniff:
            response.headers["X-Content-Type-Options"] = "nosniff"
        
        # X-XSS-Protection (legacy, but still useful)
        if self.enable_xss_protection:
            response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # X-Frame-Options
        if self.enable_frame_options:
            response.headers["X-Frame-Options"] = "DENY"
        
        # Referrer Policy
        if self.enable_referrer_policy:
            response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Additional security headers
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["X-Download-Options"] = "noopen"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Remove server information (use del instead of pop for MutableHeaders)
        if "Server" in response.headers:
            del response.headers["Server"]


class RequestValidationMiddleware(BaseHTTPMiddleware):
    """Middleware for request validation and sanitization"""
    
    def __init__(
        self,
        app: FastAPI,
        max_request_size: int = 50 * 1024 * 1024,  # 50MB
        blocked_user_agents: Optional[list] = None,
        blocked_ips: Optional[list] = None,
        enable_request_logging: bool = True
    ):
        super().__init__(app)
        self.max_request_size = max_request_size
        self.blocked_user_agents = blocked_user_agents or []
        self.blocked_ips = blocked_ips or []
        self.enable_request_logging = enable_request_logging
        
        # Compile regex patterns for blocked user agents
        self.blocked_agent_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.blocked_user_agents
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate and process request"""
        
        # IP blocking
        client_ip = self._get_client_ip(request)
        if client_ip in self.blocked_ips:
            logger.warning(f"Blocked IP attempted access: {client_ip}")
            return JSONResponse(
                status_code=403,
                content={"error": "Access forbidden"}
            )
        
        # User agent blocking
        user_agent = request.headers.get("User-Agent", "")
        if self._is_blocked_user_agent(user_agent):
            logger.warning(f"Blocked user agent: {user_agent}")
            return JSONResponse(
                status_code=403,
                content={"error": "Access forbidden"}
            )
        
        # Request size validation
        content_length = request.headers.get("Content-Length")
        if content_length and int(content_length) > self.max_request_size:
            logger.warning(f"Request too large: {content_length} bytes")
            return JSONResponse(
                status_code=413,
                content={"error": "Request entity too large"}
            )
        
        # Log request if enabled
        if self.enable_request_logging:
            self._log_request(request, client_ip)
        
        # Process request
        response = await call_next(request)
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get the real client IP address"""
        # Check for forwarded headers (when behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to direct connection
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _is_blocked_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is blocked"""
        return any(pattern.search(user_agent) for pattern in self.blocked_agent_patterns)
    
    def _log_request(self, request: Request, client_ip: str):
        """Log request details"""
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {client_ip} "
            f"User-Agent: {request.headers.get('User-Agent', 'unknown')}"
        )


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """Simple rate limiting middleware"""
    
    def __init__(
        self,
        app: FastAPI,
        requests_per_minute: int = 100,
        burst_requests: int = 20,
        enable_rate_limiting: bool = True
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_requests = burst_requests
        self.enable_rate_limiting = enable_rate_limiting
        
        # Simple in-memory store (use Redis in production)
        self.request_counts = {}
        self.last_reset = time.time()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting"""
        
        if not self.enable_rate_limiting:
            return await call_next(request)
        
        client_ip = self._get_client_ip(request)
        current_time = time.time()
        
        # Reset counts every minute
        if current_time - self.last_reset > 60:
            self.request_counts.clear()
            self.last_reset = current_time
        
        # Check rate limit
        if client_ip in self.request_counts:
            if self.request_counts[client_ip] >= self.requests_per_minute:
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return JSONResponse(
                    status_code=429,
                    content={"error": "Rate limit exceeded"},
                    headers={"Retry-After": "60"}
                )
            self.request_counts[client_ip] += 1
        else:
            self.request_counts[client_ip] = 1
        
        response = await call_next(request)
        
        # Add rate limit headers
        remaining = max(0, self.requests_per_minute - self.request_counts[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(self.last_reset + 60))
        
        return response
    
    def _get_client_ip(self, request: Request) -> str:
        """Get the real client IP address"""
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        if request.client:
            return request.client.host
        
        return "unknown"


def configure_security_middleware(
    app: FastAPI,
    environment: str = "development",
    custom_csp: Optional[Dict[str, Any]] = None,
    allowed_hosts: Optional[list] = None,
    enable_rate_limiting: bool = True,
    requests_per_minute: int = 100
):
    """Configure security middleware for the FastAPI application"""
    
    # Production-specific CSP configuration
    if environment == "production":
        production_csp = {
            "default-src": ["'self'"],
            "script-src": ["'self'"],  # No unsafe-inline in production
            "style-src": ["'self'"],   # No unsafe-inline in production
            "img-src": ["'self'", "data:", "https:"],
            "font-src": ["'self'", "https://fonts.gstatic.com"],
            "connect-src": ["'self'"],
            "frame-src": ["'none'"],
            "object-src": ["'none'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"],
            "frame-ancestors": ["'none'"],
            "upgrade-insecure-requests": True
        }
        csp_config = custom_csp or production_csp
    else:
        # Development CSP (more permissive)
        csp_config = custom_csp
    
    # Add security middleware in order
    app.add_middleware(
        SecurityHeadersMiddleware,
        csp_config=csp_config,
        enable_hsts=(environment == "production"),
        allowed_hosts=allowed_hosts
    )
    
    app.add_middleware(
        RequestValidationMiddleware,
        enable_request_logging=(environment != "production")
    )
    
    if enable_rate_limiting:
        app.add_middleware(
            RateLimitingMiddleware,
            requests_per_minute=requests_per_minute,
            enable_rate_limiting=True
        )
    
    logger.info(f"Security middleware configured for {environment} environment")


# CORS configuration for production
def get_cors_config(environment: str = "development") -> Dict[str, Any]:
    """Get CORS configuration based on environment"""
    
    if environment == "production":
        return {
            "allow_origins": [
                "https://yourdomain.com",
                "https://app.yourdomain.com"
            ],
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE", "PATCH"],
            "allow_headers": ["*"],
            "expose_headers": ["X-Process-Time", "X-RateLimit-Remaining"]
        }
    else:
        # Development CORS (more permissive)
        return {
            "allow_origins": ["*"],
            "allow_credentials": True,
            "allow_methods": ["*"],
            "allow_headers": ["*"]
        }