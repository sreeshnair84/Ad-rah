"""
Security Module for Adara Digital Signage Platform
Provides comprehensive security features including:
- Secure configuration management
- Authentication and authorization
- Audit logging
- Data encryption
- Device certificate management
"""

from .config_manager import config_manager
from .audit_logger import audit_logger, AuditEventType, AuditSeverity

# Import content scanner with graceful fallback
try:
    from .content_scanner import content_scanner
except ImportError as e:
    # Create a mock content scanner for when dependencies are missing
    import logging
    logger = logging.getLogger(__name__)
    logger.warning(f"Content scanner not available due to missing dependencies: {e}")
    
    class MockContentScanner:
        async def scan_content(self, content, filename, content_type):
            return type('MockResult', (), {
                'security_level': 'unknown',
                'scan_errors': [f'Content scanner unavailable: {e}']
            })()
    
    content_scanner = MockContentScanner()

__all__ = [
    'config_manager',
    'audit_logger',
    'content_scanner',
    'AuditEventType',
    'AuditSeverity'
]