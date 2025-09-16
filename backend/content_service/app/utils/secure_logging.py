"""
Secure Logging Utilities

This module provides secure logging practices that prevent sensitive data
exposure while maintaining comprehensive audit trails.
"""

import logging
import logging.handlers
import json
import os
from typing import Dict, Any, Optional, Union
from pathlib import Path
from datetime import datetime
import hashlib
import re
from dataclasses import dataclass, asdict


@dataclass
class LogEntry:
    """Structured log entry"""
    timestamp: str
    level: str
    logger: str
    message: str
    module: str
    function: str
    line: int
    extra: Optional[Dict[str, Any]] = None


class SecureFormatter(logging.Formatter):
    """
    Secure log formatter that sanitizes sensitive data
    """

    # Patterns that indicate sensitive data
    SENSITIVE_PATTERNS = [
        re.compile(r'("api_key"\s*:\s*)"[^"]*"', re.IGNORECASE),
        re.compile(r'("password"\s*:\s*)"[^"]*"', re.IGNORECASE),
        re.compile(r'("secret"\s*:\s*)"[^"]*"', re.IGNORECASE),
        re.compile(r'("token"\s*:\s*)"[^"]*"', re.IGNORECASE),
        re.compile(r'(Bearer\s+)[^\s]+', re.IGNORECASE),
        re.compile(r'(Authorization:\s+)[^\s]+', re.IGNORECASE),
    ]

    def __init__(self, fmt: Optional[str] = None, sanitize: bool = True):
        super().__init__(fmt)
        self.sanitize = sanitize

    def format(self, record: logging.LogRecord) -> str:
        """Format log record with sensitive data sanitization"""
        # Create a copy of the record to avoid modifying the original
        record_copy = logging.LogRecord(
            name=record.name,
            level=record.levelno,
            pathname=record.pathname,
            lineno=record.lineno,
            msg=record.msg,
            args=record.args,
            exc_info=record.exc_info
        )

        # Sanitize the message
        if self.sanitize:
            record_copy.msg = self._sanitize_message(str(record.msg))

        # Sanitize any extra data
        if hasattr(record, '__dict__') and 'extra' in record.__dict__:
            record_copy.__dict__['extra'] = self._sanitize_extra(record.__dict__['extra'])

        return super().format(record_copy)

    def _sanitize_message(self, message: str) -> str:
        """Sanitize sensitive data from log message"""
        sanitized = message

        for pattern in self.SENSITIVE_PATTERNS:
            sanitized = pattern.sub(r'\1***', sanitized)

        return sanitized

    def _sanitize_extra(self, extra: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize sensitive data from extra fields"""
        sanitized = {}

        for key, value in extra.items():
            if self._is_sensitive_key(key):
                sanitized[key] = self._mask_value(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, str):
                sanitized[key] = self._sanitize_message(value)
            else:
                sanitized[key] = value

        return sanitized

    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a key contains sensitive information"""
        sensitive_keywords = [
            'password', 'secret', 'key', 'token', 'credential',
            'auth', 'authorization', 'bearer', 'apikey'
        ]
        return any(keyword in key.lower() for keyword in sensitive_keywords)

    def _mask_value(self, value: Any) -> str:
        """Mask sensitive values"""
        if isinstance(value, str):
            if len(value) <= 4:
                return '*' * len(value)
            else:
                return '***'
        else:
            return '***'

    def _sanitize_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sanitize dictionary data"""
        sanitized = {}

        for key, value in data.items():
            if self._is_sensitive_key(key):
                sanitized[key] = self._mask_value(value)
            elif isinstance(value, dict):
                sanitized[key] = self._sanitize_dict(value)
            elif isinstance(value, str):
                sanitized[key] = self._sanitize_message(value)
            else:
                sanitized[key] = value

        return sanitized


class SecureJSONFormatter(SecureFormatter):
    """
    JSON formatter for structured logging with security
    """

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        # Extract extra data from record.__dict__
        # Extra data passed via logging extra parameter gets flattened into the record
        standard_fields = {
            'name', 'msg', 'args', 'levelname', 'levelno', 'pathname', 'filename',
            'module', 'exc_info', 'exc_text', 'stack_info', 'lineno', 'funcName',
            'created', 'msecs', 'relativeCreated', 'thread', 'threadName',
            'processName', 'process'
        }

        extra_data = {}
        for key, value in record.__dict__.items():
            if key not in standard_fields:
                extra_data[key] = value

        log_entry = LogEntry(
            timestamp=datetime.utcnow().isoformat(),
            level=record.levelname,
            logger=record.name,
            message=self._sanitize_message(str(record.msg)),
            module=getattr(record, 'module', 'unknown'),
            function=getattr(record, 'funcName', 'unknown'),
            line=getattr(record, 'lineno', 0),
            extra=self._sanitize_extra(extra_data) if extra_data else {}
        )

        # Add exception info if present
        if record.exc_info:
            log_entry.extra = log_entry.extra or {}
            log_entry.extra['exception'] = self.formatException(record.exc_info)

        return json.dumps(asdict(log_entry), default=str)


class SecureFileHandler(logging.handlers.RotatingFileHandler):
    """
    Secure file handler with log rotation and integrity checks
    """

    def __init__(self, filename: str, maxBytes: int = 10*1024*1024, backupCount: int = 5):
        super().__init__(filename, maxBytes=maxBytes, backupCount=backupCount)

        # Set restrictive permissions on log files
        log_path = Path(filename)
        if log_path.exists():
            log_path.chmod(0o600)

    def doRollover(self):
        """Override rollover to set permissions on rotated files"""
        super().doRollover()

        # Set permissions on the new current log file
        if self.baseFilename:
            current_log = Path(self.baseFilename)
            if current_log.exists():
                current_log.chmod(0o600)

        # Set permissions on rotated files
        for i in range(1, self.backupCount + 1):
            rotated_file = Path(f"{self.baseFilename}.{i}")
            if rotated_file.exists():
                rotated_file.chmod(0o600)


class AuditLogger:
    """
    Specialized logger for security audit events
    """

    def __init__(self, name: str = "audit", log_file: Optional[str] = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # Create secure formatter
        formatter = SecureJSONFormatter()

        # File handler for audit logs
        if log_file:
            self.file_handler = SecureFileHandler(log_file)
            self.file_handler.setFormatter(formatter)
            self.logger.addHandler(self.file_handler)
        else:
            self.file_handler = None

        # Console handler for development
        if os.getenv('DEBUG', '').lower() == 'true':
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(SecureFormatter())
            self.logger.addHandler(console_handler)

    def close(self):
        """Close all handlers"""
        if self.file_handler:
            self.file_handler.close()
            self.logger.removeHandler(self.file_handler)

    def log_auth_attempt(self, user_id: str, action: str, success: bool,
                        ip_address: Optional[str] = None, user_agent: Optional[str] = None):
        """Log authentication attempt"""
        extra_data = {
            'event_type': 'auth_attempt',
            'user_id': self._hash_identifier(user_id),
            'action': action,
            'success': success,
            'ip_address': ip_address,
            'user_agent': user_agent[:200] if user_agent else None  # Truncate long user agents
        }
        self.logger.info("Authentication attempt", extra=extra_data)

    def log_api_access(self, endpoint: str, method: str, user_id: Optional[str] = None,
                      status_code: int = 200, response_time: Optional[float] = None,
                      ip_address: Optional[str] = None):
        """Log API access"""
        extra_data = {
            'event_type': 'api_access',
            'endpoint': endpoint,
            'method': method,
            'user_id': self._hash_identifier(user_id) if user_id else None,
            'status_code': status_code,
            'response_time': response_time,
            'ip_address': ip_address
        }
        self.logger.info("API access", extra=extra_data)

    def log_config_change(self, key: str, action: str, user_id: Optional[str] = None,
                         old_value: Optional[Any] = None, new_value: Optional[Any] = None):
        """Log configuration change"""
        extra_data = {
            'event_type': 'config_change',
            'setting_name': key,
            'action': action,
            'user_id': self._hash_identifier(user_id) if user_id else None,
            'old_value': self._sanitize_config_value(old_value),
            'new_value': self._sanitize_config_value(new_value)
        }
        self.logger.warning("Configuration change", extra=extra_data)

    def log_security_event(self, event_type: str, severity: str, description: str,
                          details: Optional[Dict[str, Any]] = None):
        """Log security event"""
        extra_data = {
            'event_type': event_type,
            'severity': severity,
            'description': description,
            'details': self._sanitize_security_details(details)
        }
        self.logger.error("Security event", extra=extra_data)

    def _hash_identifier(self, identifier: str) -> str:
        """Hash sensitive identifiers for privacy"""
        if not identifier:
            return ""
        return hashlib.sha256(identifier.encode('utf-8')).hexdigest()[:16]

    def _sanitize_config_value(self, value: Any) -> Any:
        """Sanitize configuration values for logging"""
        if isinstance(value, str):
            # Check if it looks like sensitive data
            if any(keyword in value.lower() for keyword in ['key', 'secret', 'password', 'token']):
                return "***"
        elif isinstance(value, dict):
            return {k: self._sanitize_config_value(v) for k, v in value.items()}
        return value

    def _sanitize_security_details(self, details: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Sanitize security event details"""
        if not details:
            return None

        sanitized = {}
        for key, value in details.items():
            if self._is_sensitive_key(key):
                sanitized[key] = "***"
            else:
                sanitized[key] = value

        return sanitized

    def _is_sensitive_key(self, key: str) -> bool:
        """Check if a key contains sensitive information"""
        sensitive_keywords = [
            'password', 'secret', 'key', 'token', 'credential',
            'private', 'auth', 'session', 'cookie'
        ]
        return any(keyword in key.lower() for keyword in sensitive_keywords)


class SecurityLogger:
    """
    Logger specifically for security-related events
    """

    def __init__(self):
        self.audit_logger = AuditLogger("security", "logs/security_audit.log")

    def close(self):
        """Close all handlers"""
        self.audit_logger.close()

    def log_failed_login(self, username: str, ip_address: str, reason: str = "invalid_credentials"):
        """Log failed login attempt"""
        self.audit_logger.log_auth_attempt(
            user_id=username,
            action="login",
            success=False,
            ip_address=ip_address
        )
        self.audit_logger.log_security_event(
            event_type="failed_login",
            severity="medium",
            description=f"Failed login attempt for user {username}",
            details={"reason": reason, "ip_address": ip_address}
        )

    def log_suspicious_activity(self, user_id: str, activity: str, details: Dict[str, Any]):
        """Log suspicious activity"""
        self.audit_logger.log_security_event(
            event_type="suspicious_activity",
            severity="high",
            description=f"Suspicious activity detected: {activity}",
            details={"user_id": user_id, **details}
        )

    def log_unauthorized_access(self, resource: str, user_id: Optional[str], ip_address: str):
        """Log unauthorized access attempt"""
        self.audit_logger.log_security_event(
            event_type="unauthorized_access",
            severity="high",
            description=f"Unauthorized access attempt to {resource}",
            details={
                "resource": resource,
                "user_id": user_id,
                "ip_address": ip_address
            }
        )


# Global instances
_audit_logger: Optional[AuditLogger] = None
_security_logger: Optional[SecurityLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create the global audit logger"""
    global _audit_logger

    if _audit_logger is None:
        _audit_logger = AuditLogger()

    return _audit_logger


def get_security_logger() -> SecurityLogger:
    """Get or create the global security logger"""
    global _security_logger

    if _security_logger is None:
        _security_logger = SecurityLogger()

    return _security_logger


def setup_secure_logging(log_level: str = "INFO", log_file: Optional[str] = None):
    """
    Set up secure logging configuration

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path
    """
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = Path(log_file).parent
        log_dir.mkdir(exist_ok=True, parents=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # Create secure formatter
    formatter = SecureFormatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # File handler if specified
    if log_file:
        file_handler = SecureFileHandler(log_file)
        file_handler.setFormatter(SecureJSONFormatter())
        root_logger.addHandler(file_handler)

    # Suppress noisy loggers
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info("Secure logging configured")


# Convenience functions
def log_api_request(endpoint: str, method: str, user_id: Optional[str] = None,
                   status_code: int = 200, response_time: Optional[float] = None):
    """Convenience function to log API requests"""
    audit_logger = get_audit_logger()
    audit_logger.log_api_access(endpoint, method, user_id, status_code, response_time)


def log_security_event(event_type: str, severity: str, description: str,
                      details: Optional[Dict[str, Any]] = None):
    """Convenience function to log security events"""
    security_logger = get_security_logger()
    security_logger.audit_logger.log_security_event(event_type, severity, description, details)