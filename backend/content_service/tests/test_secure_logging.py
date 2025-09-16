"""
Tests for secure logging utilities
"""

import pytest
import logging
import json
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.utils.secure_logging import (
    SecureFormatter,
    SecureJSONFormatter,
    SecureFileHandler,
    AuditLogger,
    SecurityLogger,
    setup_secure_logging,
    get_audit_logger,
    get_security_logger,
    log_api_request,
    log_security_event
)


class TestSecureFormatter:
    """Test secure log formatter"""

    def test_sanitize_message_removes_sensitive_data(self):
        """Test that sensitive data is sanitized from log messages"""
        formatter = SecureFormatter()

        # Test API key sanitization
        message = 'API call with key: "api_key": "sk-1234567890abcdef"'
        sanitized = formatter._sanitize_message(message)
        assert "sk-1234567890abcdef" not in sanitized
        assert "***" in sanitized

        # Test password sanitization
        message = 'Login with password: "password": "secret123"'
        sanitized = formatter._sanitize_message(message)
        assert "secret123" not in sanitized
        assert "***" in sanitized

        # Test token sanitization
        message = 'Bearer token: Bearer abc123def456'
        sanitized = formatter._sanitize_message(message)
        assert "abc123def456" not in sanitized
        assert "***" in sanitized

    def test_format_preserves_non_sensitive_data(self):
        """Test that non-sensitive data is preserved"""
        formatter = SecureFormatter()

        # Create a mock log record
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Normal message without sensitive data",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)
        assert "Normal message without sensitive data" in formatted

    def test_sanitize_extra_data(self):
        """Test sanitization of extra data in log records"""
        formatter = SecureFormatter()

        extra = {
            "user_id": "12345",
            "api_key": "sk-abcdef123456",
            "normal_field": "normal_value",
            "nested": {
                "password": "secret",
                "safe": "value"
            }
        }

        sanitized = formatter._sanitize_extra(extra)

        assert sanitized["user_id"] == "12345"
        assert sanitized["api_key"] == "***"
        assert sanitized["normal_field"] == "normal_value"
        assert sanitized["nested"]["password"] == "***"
        assert sanitized["nested"]["safe"] == "value"


class TestSecureJSONFormatter:
    """Test secure JSON formatter"""

    def test_format_creates_valid_json(self):
        """Test that formatter creates valid JSON"""
        formatter = SecureJSONFormatter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg="Test message",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed

    def test_sanitizes_sensitive_data_in_json(self):
        """Test that sensitive data is sanitized in JSON output"""
        formatter = SecureJSONFormatter()

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=10,
            msg='API call with "api_key": "sk-123456"',
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert "sk-123456" not in parsed["message"]
        assert "***" in parsed["message"]


class TestSecureFileHandler:
    """Test secure file handler"""

    def test_file_permissions_set_correctly(self):
        """Test that log files have restrictive permissions"""
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            handler = SecureFileHandler(temp_path)
            handler.close()

            # Check file permissions (on systems that support it)
            if os.name != 'nt':  # Skip on Windows
                file_path = Path(temp_path)
                permissions = oct(file_path.stat().st_mode)[-3:]
                assert permissions == "600"
        finally:
            os.unlink(temp_path)


class TestAuditLogger:
    """Test audit logger"""

    def test_log_auth_attempt(self):
        """Test logging authentication attempts"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            audit_logger = AuditLogger("test_audit", temp_path)

            audit_logger.log_auth_attempt(
                user_id="user123",
                action="login",
                success=True,
                ip_address="192.168.1.1"
            )

            # Close the logger to flush and release the file
            audit_logger.close()

            # Read the log file
            with open(temp_path, 'r') as f:
                log_content = f.read().strip()
                # Get the last line (most recent log entry)
                last_line = log_content.split('\n')[-1]
                log_data = json.loads(last_line)

            assert log_data["extra"]["event_type"] == "auth_attempt"
            assert log_data["extra"]["success"] is True
            assert log_data["extra"]["ip_address"] == "192.168.1.1"
            # User ID should be hashed
            assert log_data["extra"]["user_id"] != "user123"

        finally:
            os.unlink(temp_path)

    def test_log_api_access(self):
        """Test logging API access"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            audit_logger = AuditLogger("test_audit", temp_path)

            audit_logger.log_api_access(
                endpoint="/api/test",
                method="GET",
                user_id="user123",
                status_code=200,
                response_time=0.5
            )

            # Close the logger to flush and release the file
            audit_logger.close()

            with open(temp_path, 'r') as f:
                log_content = f.read().strip()
                # Get the last line (most recent log entry)
                last_line = log_content.split('\n')[-1]
                log_data = json.loads(last_line)

            assert log_data["extra"]["event_type"] == "api_access"
            assert log_data["extra"]["endpoint"] == "/api/test"
            assert log_data["extra"]["method"] == "GET"
            assert log_data["extra"]["status_code"] == 200
            assert log_data["extra"]["response_time"] == 0.5

        finally:
            os.unlink(temp_path)

    def test_log_config_change(self):
        """Test logging configuration changes"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            audit_logger = AuditLogger("test_audit", temp_path)

            audit_logger.log_config_change(
                key="setting_name",
                action="update",
                user_id="admin",
                old_value="old_key",
                new_value="new_key"
            )

            # Close the logger to flush and release the file
            audit_logger.close()

            with open(temp_path, 'r') as f:
                log_content = f.read().strip()
                # Get the last line (most recent log entry)
                last_line = log_content.split('\n')[-1]
                log_data = json.loads(last_line)

            assert log_data["extra"]["event_type"] == "config_change"
            assert log_data["extra"]["setting_name"] == "setting_name"
            assert log_data["extra"]["action"] == "update"
            # Sensitive values should be masked
            assert log_data["extra"]["old_value"] == "***"
            assert log_data["extra"]["new_value"] == "***"

        finally:
            os.unlink(temp_path)


class TestSecurityLogger:
    """Test security logger"""

    def test_log_failed_login(self):
        """Test logging failed login attempts"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            security_logger = SecurityLogger()
            # Override the audit logger to use our test file
            security_logger.audit_logger = AuditLogger("test_security", temp_path)

            security_logger.log_failed_login(
                username="testuser",
                ip_address="192.168.1.100",
                reason="invalid_password"
            )

            # Close the logger to flush and release the file
            security_logger.close()

            with open(temp_path, 'r') as f:
                log_content = f.read().strip()
                # Get the last line (most recent log entry)
                last_line = log_content.split('\n')[-1]
                log_data = json.loads(last_line)

            assert log_data["extra"]["event_type"] == "failed_login"
            assert log_data["extra"]["severity"] == "medium"
            assert "Failed login attempt" in log_data["extra"]["description"]

        finally:
            os.unlink(temp_path)

    def test_log_suspicious_activity(self):
        """Test logging suspicious activity"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            security_logger = SecurityLogger()
            security_logger.audit_logger = AuditLogger("test_security", temp_path)

            security_logger.log_suspicious_activity(
                user_id="user123",
                activity="multiple_failed_logins",
                details={"attempts": 5, "time_window": "5m"}
            )

            # Close the logger to flush and release the file
            security_logger.close()

            with open(temp_path, 'r') as f:
                log_content = f.read().strip()
                # Get the last line (most recent log entry)
                last_line = log_content.split('\n')[-1]
                log_data = json.loads(last_line)

            assert log_data["extra"]["event_type"] == "suspicious_activity"
            assert log_data["extra"]["severity"] == "high"
            assert "Suspicious activity detected" in log_data["extra"]["description"]

        finally:
            os.unlink(temp_path)
class TestGlobalLoggers:
    """Test global logger instances"""

    def test_get_audit_logger_returns_instance(self):
        """Test that get_audit_logger returns a logger instance"""
        logger = get_audit_logger()
        assert isinstance(logger, AuditLogger)

    def test_get_security_logger_returns_instance(self):
        """Test that get_security_logger returns a logger instance"""
        logger = get_security_logger()
        assert isinstance(logger, SecurityLogger)

    def test_get_audit_logger_returns_same_instance(self):
        """Test that get_audit_logger returns the same instance"""
        logger1 = get_audit_logger()
        logger2 = get_audit_logger()
        assert logger1 is logger2

    def test_get_security_logger_returns_same_instance(self):
        """Test that get_security_logger returns the same instance"""
        logger1 = get_security_logger()
        logger2 = get_security_logger()
        assert logger1 is logger2


class TestConvenienceFunctions:
    """Test convenience logging functions"""

    @patch('app.utils.secure_logging.get_audit_logger')
    def test_log_api_request_calls_audit_logger(self, mock_get_logger):
        """Test that log_api_request calls the audit logger"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        log_api_request("/api/test", "GET", "user123", 200, 0.5)

        mock_logger.log_api_access.assert_called_once_with(
            "/api/test", "GET", "user123", 200, 0.5
        )

    @patch('app.utils.secure_logging.get_security_logger')
    def test_log_security_event_calls_security_logger(self, mock_get_logger):
        """Test that log_security_event calls the security logger"""
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger

        log_security_event("test_event", "high", "Test description")

        mock_logger.audit_logger.log_security_event.assert_called_once_with(
            "test_event", "high", "Test description", None
        )


class TestSetupSecureLogging:
    """Test secure logging setup"""

    def test_setup_secure_logging_configures_root_logger(self):
        """Test that setup_secure_logging configures the root logger"""
        # Reset root logger
        root_logger = logging.getLogger()
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)

        setup_secure_logging("INFO")

        # Check that handlers were added
        assert len(root_logger.handlers) >= 1

        # Check that a console handler is present
        console_handlers = [h for h in root_logger.handlers if isinstance(h, logging.StreamHandler)]
        assert len(console_handlers) >= 1

    def test_setup_secure_logging_with_file_handler(self):
        """Test that setup_secure_logging can add file handler"""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = os.path.join(temp_dir, "test.log")

            # Reset root logger
            root_logger = logging.getLogger()
            for handler in root_logger.handlers[:]:
                root_logger.removeHandler(handler)

            setup_secure_logging("INFO", log_file)

            # Check that file handler was added
            file_handlers = [h for h in root_logger.handlers if hasattr(h, 'baseFilename')]
            assert len(file_handlers) >= 1

            # Close handlers to release files
            for handler in root_logger.handlers[:]:
                handler.close()
                root_logger.removeHandler(handler)