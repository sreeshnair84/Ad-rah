"""
Comprehensive Audit Logging System
Implements GDPR-compliant audit logging for all security-sensitive operations
"""
import json
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from enum import Enum
import uuid
import hashlib
from pathlib import Path

from .config_manager import config_manager

class AuditEventType(Enum):
    """Audit event types for classification"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    SECURITY = "security"
    PRIVACY = "privacy"
    CONTENT = "content"
    DEVICE = "device"
    SYSTEM = "system"

class AuditSeverity(Enum):
    """Audit event severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AuditLogger:
    """Comprehensive audit logging system"""
    
    def __init__(self):
        self.config = config_manager.get_compliance_config()
        self.audit_enabled = self.config.get("audit_logging", True)
        # Initialize audit storage and ensure logs directory exists before setting up logger
        self.audit_file = Path("logs/audit.log")
        try:
            self.audit_file.parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            # If creation fails, continue and let _setup_logger handle fallback
            pass

        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup dedicated audit logger"""
        logger = logging.getLogger("audit")
        logger.setLevel(logging.INFO)
        # Ensure logs directory exists before creating file handler
        audit_dir = self.audit_file.parent
        try:
            audit_dir.mkdir(parents=True, exist_ok=True)
        except Exception:
            # If path is invalid or cannot be created, fall back to current directory
            audit_dir = Path('.')

        # Create file handler for audit logs
        handler = logging.FileHandler(audit_dir / "audit.log", encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S UTC'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def _create_audit_entry(self, event_type: AuditEventType, event_name: str, 
                           details: Dict[str, Any], severity: AuditSeverity = AuditSeverity.MEDIUM,
                           user_id: Optional[str] = None, ip_address: Optional[str] = None) -> Dict[str, Any]:
        """Create standardized audit entry"""
        entry = {
            "audit_id": str(uuid.uuid4()),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type.value,
            "event_name": event_name,
            "severity": severity.value,
            "details": details,
            "user_id": user_id,
            "ip_address": ip_address,
            "checksum": None  # Will be calculated
        }
        
        # Calculate checksum for integrity
        entry_str = json.dumps(entry, sort_keys=True, exclude=["checksum"])
        entry["checksum"] = hashlib.sha256(entry_str.encode()).hexdigest()
        
        return entry
    
    def _log_entry(self, entry: Dict[str, Any]) -> None:
        """Log audit entry to file and database"""
        if not self.audit_enabled:
            return
        
        try:
            # Log to file
            self.logger.info(json.dumps(entry, ensure_ascii=False))
            
            # TODO: Also store in database for searchability
            # await self.store_in_database(entry)
            
        except Exception as e:
            # Critical: audit logging failure should never crash the application
            # but should be logged to system logger
            logging.getLogger(__name__).error(f"Audit logging failed: {e}")
    
    # Authentication Events
    def log_auth_event(self, event_name: str, details: Dict[str, Any], 
                      user_id: Optional[str] = None, ip_address: Optional[str] = None,
                      severity: AuditSeverity = AuditSeverity.MEDIUM) -> None:
        """Log authentication-related events"""
        entry = self._create_audit_entry(
            AuditEventType.AUTHENTICATION, event_name, details, severity, user_id, ip_address
        )
        self._log_entry(entry)
    
    # Security Events
    def log_security_event(self, event_name: str, details: Dict[str, Any],
                          user_id: Optional[str] = None, ip_address: Optional[str] = None,
                          severity: AuditSeverity = AuditSeverity.HIGH) -> None:
        """Log security-related events"""
        entry = self._create_audit_entry(
            AuditEventType.SECURITY, event_name, details, severity, user_id, ip_address
        )
        self._log_entry(entry)
    
    # Data Access Events (GDPR Compliance)
    def log_data_access(self, data_type: str, record_id: str, operation: str,
                       user_id: Optional[str] = None, ip_address: Optional[str] = None,
                       pii_accessed: bool = False) -> None:
        """Log data access events for GDPR compliance"""
        details = {
            "data_type": data_type,
            "record_id": record_id,
            "operation": operation,
            "pii_accessed": pii_accessed
        }
        
        severity = AuditSeverity.HIGH if pii_accessed else AuditSeverity.MEDIUM
        
        entry = self._create_audit_entry(
            AuditEventType.DATA_ACCESS, "data_accessed", details, severity, user_id, ip_address
        )
        self._log_entry(entry)
    
    # Data Modification Events
    def log_data_modification(self, data_type: str, record_id: str, operation: str,
                             changes: Dict[str, Any], user_id: Optional[str] = None,
                             ip_address: Optional[str] = None) -> None:
        """Log data modification events"""
        details = {
            "data_type": data_type,
            "record_id": record_id,
            "operation": operation,
            "changes": changes
        }
        
        entry = self._create_audit_entry(
            AuditEventType.DATA_MODIFICATION, "data_modified", details, 
            AuditSeverity.MEDIUM, user_id, ip_address
        )
        self._log_entry(entry)
    
    # Content Events
    def log_content_event(self, event_name: str, content_id: str, details: Dict[str, Any],
                         user_id: Optional[str] = None, ip_address: Optional[str] = None) -> None:
        """Log content-related events (upload, moderation, etc.)"""
        details.update({"content_id": content_id})
        
        entry = self._create_audit_entry(
            AuditEventType.CONTENT, event_name, details, AuditSeverity.MEDIUM, user_id, ip_address
        )
        self._log_entry(entry)
    
    # Privacy Events (GDPR)
    def log_privacy_event(self, event_name: str, details: Dict[str, Any],
                         user_id: Optional[str] = None, ip_address: Optional[str] = None) -> None:
        """Log privacy-related events (consent, data deletion, etc.)"""
        entry = self._create_audit_entry(
            AuditEventType.PRIVACY, event_name, details, AuditSeverity.HIGH, user_id, ip_address
        )
        self._log_entry(entry)
    
    # Device Events
    def log_device_event(self, event_name: str, device_id: str, details: Dict[str, Any],
                        severity: AuditSeverity = AuditSeverity.MEDIUM) -> None:
        """Log device-related events"""
        details.update({"device_id": device_id})
        
        entry = self._create_audit_entry(
            AuditEventType.DEVICE, event_name, details, severity
        )
        self._log_entry(entry)
    
    # System Events
    def log_system_event(self, event_name: str, details: Dict[str, Any],
                        severity: AuditSeverity = AuditSeverity.LOW) -> None:
        """Log system-related events"""
        entry = self._create_audit_entry(
            AuditEventType.SYSTEM, event_name, details, severity
        )
        self._log_entry(entry)
    
    # Specialized logging methods for common scenarios
    def log_failed_login(self, email: str, ip_address: str, reason: str) -> None:
        """Log failed login attempt"""
        self.log_auth_event("login_failed", {
            "email": email,
            "reason": reason,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, ip_address=ip_address, severity=AuditSeverity.HIGH)
    
    def log_successful_login(self, user_id: str, email: str, ip_address: str) -> None:
        """Log successful login"""
        self.log_auth_event("login_successful", {
            "email": email,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, user_id=user_id, ip_address=ip_address, severity=AuditSeverity.MEDIUM)
    
    def log_content_upload(self, user_id: str, filename: str, content_type: str, 
                          size: int, ip_address: str) -> None:
        """Log content upload event"""
        self.log_content_event("content_uploaded", str(uuid.uuid4()), {
            "filename": filename,
            "content_type": content_type,
            "size_bytes": size,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, user_id=user_id, ip_address=ip_address)
    
    def log_content_moderation(self, content_id: str, decision: str, reviewer_id: str,
                              ai_confidence: Optional[float] = None) -> None:
        """Log content moderation decision"""
        details = {
            "decision": decision,
            "reviewer_id": reviewer_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        if ai_confidence is not None:
            details["ai_confidence"] = ai_confidence
        
        self.log_content_event("content_moderated", content_id, details)
    
    def log_device_registration(self, device_id: str, organization_id: str, ip_address: str) -> None:
        """Log device registration"""
        self.log_device_event("device_registered", device_id, {
            "organization_id": organization_id,
            "ip_address": ip_address,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, severity=AuditSeverity.MEDIUM)
    
    def log_suspicious_activity(self, activity_type: str, details: Dict[str, Any],
                               ip_address: Optional[str] = None) -> None:
        """Log suspicious activity"""
        self.log_security_event("suspicious_activity", {
            "activity_type": activity_type,
            **details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, ip_address=ip_address, severity=AuditSeverity.CRITICAL)
    
    def log_gdpr_request(self, request_type: str, user_id: str, details: Dict[str, Any]) -> None:
        """Log GDPR-related requests (data export, deletion, etc.)"""
        self.log_privacy_event(f"gdpr_{request_type}", {
            **details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }, user_id=user_id)
    
    # Query methods for audit trail analysis
    def get_user_activity(self, user_id: str, start_date: datetime, end_date: datetime) -> List[Dict]:
        """Get user activity for specified date range (for GDPR data export)"""
        # TODO: Implement database query
        # This is a placeholder - in production, query from database
        return []
    
    def detect_suspicious_patterns(self, ip_address: str, time_window_hours: int = 24) -> List[Dict]:
        """Detect suspicious activity patterns from an IP"""
        # TODO: Implement pattern detection
        # Look for: multiple failed logins, rapid requests, unusual access patterns
        return []

# Global audit logger instance
audit_logger = AuditLogger()