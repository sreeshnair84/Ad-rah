"""
Integration of Secure Logging into AI Manager

This module demonstrates how to integrate the secure logging utilities
into the existing AI manager system for comprehensive security auditing.
"""

import logging
from pathlib import Path
from app.utils.secure_logging import (
    AuditLogger,
    SecurityLogger,
    setup_secure_logging,
    get_audit_logger,
    get_security_logger,
    log_api_request,
    log_security_event
)
from app.services.ai_service_manager import AIServiceManager
from app.utils.input_validator import ContentValidator
from typing import Optional, Dict, Any


class SecureAIManager:
    """
    AI Manager with integrated secure logging and security features
    """

    def __init__(self, log_file: Optional[str] = None):
        # Initialize security components
        self.input_validator = ContentValidator()
        self.audit_logger = get_audit_logger()
        self.security_logger = get_security_logger()

        # Set up secure logging
        setup_secure_logging(log_file=log_file)

        # Initialize AI service manager
        self.ai_manager = AIServiceManager()

    async def process_content_securely(self, content: str, user_id: str,
                                     content_type: str = "text") -> Dict[str, Any]:
        """
        Process content with comprehensive security logging
        """
        # Log API access
        self.audit_logger.log_api_access(
            endpoint="/api/process_content",
            method="POST",
            user_id=user_id,
            status_code=200
        )

        try:
            # Validate and sanitize input
            sanitized_content = self.input_validator.sanitize_text(content)

            # Get AI service status (placeholder for actual processing)
            result = self.ai_manager.get_status()

            # Log successful processing
            self.audit_logger.log_api_access(
                endpoint="/api/process_content",
                method="POST",
                user_id=user_id,
                status_code=200,
                response_time=0.1  # Placeholder
            )

            return {
                "status": "success",
                "processed_content": sanitized_content,
                "service_status": result
            }

        except Exception as e:
            # Log error
            self.audit_logger.log_api_access(
                endpoint="/api/process_content",
                method="POST",
                user_id=user_id,
                status_code=500
            )

            # Log security event if it's a security-related error
            if "security" in str(e).lower() or "unauthorized" in str(e).lower():
                self.security_logger.log_unauthorized_access(
                    resource="content_processing",
                    user_id=user_id,
                    ip_address="unknown"  # Would be extracted from request in real implementation
                )

            raise

    async def authenticate_user(self, username: str, password: str,
                              ip_address: str) -> bool:
        """
        Authenticate user with secure logging
        """
        try:
            # Validate credentials (placeholder - implement actual auth)
            if username == "admin" and password == "secure_password":  # Placeholder
                # Log successful authentication
                self.audit_logger.log_auth_attempt(
                    user_id=username,
                    action="login",
                    success=True,
                    ip_address=ip_address
                )
                return True
            else:
                # Log failed authentication
                self.audit_logger.log_auth_attempt(
                    user_id=username,
                    action="login",
                    success=False,
                    ip_address=ip_address
                )
                return False

        except Exception as e:
            # Log authentication error
            self.audit_logger.log_auth_attempt(
                user_id=username,
                action="login",
                success=False,
                ip_address=ip_address
            )
            raise

    def update_configuration(self, key: str, value: Any, user_id: str):
        """
        Update configuration with audit logging
        """
        # Get old value (placeholder)
        old_value = self._get_config_value(key)

        # Update configuration (placeholder)
        self._set_config_value(key, value)

        # Log configuration change
        self.audit_logger.log_config_change(
            key=key,
            action="update",
            user_id=user_id,
            old_value=old_value,
            new_value=value
        )

    def _get_config_value(self, key: str) -> Any:
        """Placeholder for getting config value"""
        return "old_value"

    def _set_config_value(self, key: str, value: Any):
        """Placeholder for setting config value"""
        pass


# Convenience functions for easy integration
def log_ai_service_usage(service_name: str, user_id: str, operation: str,
                        success: bool, processing_time: Optional[float] = None):
    """
    Log AI service usage for monitoring and analytics
    """
    audit_logger = get_audit_logger()
    audit_logger.log_api_access(
        endpoint=f"/api/ai/{service_name}/{operation}",
        method="POST",
        user_id=user_id,
        status_code=200 if success else 500,
        response_time=processing_time
    )


def log_security_incident(incident_type: str, severity: str,
                         description: str, details: Dict[str, Any]):
    """
    Log security incidents
    """
    security_logger = get_security_logger()
    security_logger.audit_logger.log_security_event(
        event_type=incident_type,
        severity=severity,
        description=description,
        details=details
    )


# Example usage and integration points
def setup_secure_ai_system(log_file: str = "logs/ai_security.log"):
    """
    Set up the complete secure AI system
    """
    # Ensure log directory exists
    log_path = Path(log_file)
    log_path.parent.mkdir(exist_ok=True, parents=True)

    # Set up secure logging
    setup_secure_logging(log_file=log_file)

    # Create secure AI manager
    ai_manager = SecureAIManager(log_file=log_file)

    return ai_manager


if __name__ == "__main__":
    # Example setup
    manager = setup_secure_ai_system()

    print("Secure AI Manager initialized with comprehensive logging")
    print("- Authentication attempts logged")
    print("- API access audited")
    print("- Configuration changes tracked")
    print("- Security events monitored")
    print("- Sensitive data sanitized")
    print("- User IDs hashed for privacy")