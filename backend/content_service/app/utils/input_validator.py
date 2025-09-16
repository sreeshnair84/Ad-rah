"""
Input Validation and Sanitization Utilities

This module provides comprehensive input validation and sanitization
for the AI content moderation system to prevent injection attacks,
malformed data, and security vulnerabilities.
"""

import re
import os
import logging
from typing import Optional, Dict, Any, List, Union
from pathlib import Path
# import magic  # For file type detection - commented out as it's not installed
from urllib.parse import urlparse
import json

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when input validation fails"""
    pass


class SanitizationError(Exception):
    """Raised when input sanitization fails"""
    pass


class ContentValidator:
    """
    Comprehensive content validation and sanitization

    Handles text, file paths, URLs, and other input types
    """

    # Content type limits
    MAX_TEXT_LENGTH = 100000  # 100KB
    MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB
    MAX_URL_LENGTH = 2048

    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),
        re.compile(r'javascript:', re.IGNORECASE),
        re.compile(r'data:', re.IGNORECASE),
        re.compile(r'vbscript:', re.IGNORECASE),
        re.compile(r'on\w+\s*=', re.IGNORECASE),
        re.compile(r'<iframe[^>]*>.*?</iframe>', re.IGNORECASE | re.DOTALL),
        re.compile(r'<object[^>]*>.*?</object>', re.IGNORECASE | re.DOTALL),
        re.compile(r'<embed[^>]*>.*?</embed>', re.IGNORECASE | re.DOTALL),
    ]

    # Allowed file extensions by content type
    ALLOWED_EXTENSIONS = {
        'text': ['.txt', '.md', '.csv', '.json', '.xml'],
        'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.svg'],
        'video': ['.mp4', '.avi', '.mov', '.wmv', '.flv', '.webm'],
        'audio': ['.mp3', '.wav', '.flac', '.aac', '.ogg'],
        'document': ['.pdf', '.doc', '.docx', '.ppt', '.pptx', '.xls', '.xlsx']
    }

    # MIME type mappings
    MIME_TYPES = {
        'text': ['text/plain', 'text/markdown', 'text/csv', 'application/json', 'application/xml'],
        'image': ['image/jpeg', 'image/png', 'image/gif', 'image/bmp', 'image/webp', 'image/svg+xml'],
        'video': ['video/mp4', 'video/avi', 'video/quicktime', 'video/x-ms-wmv', 'video/webm'],
        'audio': ['audio/mpeg', 'audio/wav', 'audio/flac', 'audio/aac', 'audio/ogg'],
        'document': ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']
    }

    @staticmethod
    def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize text input to prevent XSS and injection attacks

        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length

        Returns:
            Sanitized text

        Raises:
            ValidationError: If text is invalid
            SanitizationError: If sanitization fails
        """
        if not isinstance(text, str):
            raise ValidationError("Input must be a string")

        # Check length
        if max_length is None:
            max_length = ContentValidator.MAX_TEXT_LENGTH

        if len(text) > max_length:
            raise ValidationError(f"Text exceeds maximum length of {max_length} characters")

        # Remove null bytes and other control characters
        sanitized = text.replace('\x00', '').replace('\r\n', '\n').replace('\r', '\n')

        # Remove dangerous patterns
        for pattern in ContentValidator.DANGEROUS_PATTERNS:
            sanitized = pattern.sub('', sanitized)

        # Normalize whitespace
        sanitized = re.sub(r'\s+', ' ', sanitized).strip()

        # Basic HTML entity encoding for common characters
        sanitized = sanitized.replace('&', '&amp;')
        sanitized = sanitized.replace('<', '&lt;')
        sanitized = sanitized.replace('>', '&gt;')
        sanitized = sanitized.replace('"', '&quot;')
        sanitized = sanitized.replace("'", '&#x27;')

        return sanitized

    @staticmethod
    def validate_file_path(file_path: str, allowed_extensions: Optional[List[str]] = None,
                         base_dir: Optional[str] = None) -> str:
        """
        Validate and sanitize file path to prevent directory traversal

        Args:
            file_path: File path to validate
            allowed_extensions: List of allowed file extensions
            base_dir: Base directory to restrict paths to

        Returns:
            Sanitized and validated file path

        Raises:
            ValidationError: If path is invalid
        """
        if not file_path or not isinstance(file_path, str):
            raise ValidationError("File path must be a non-empty string")

        # Remove any null bytes
        file_path = file_path.replace('\x00', '')

        # Resolve the path to prevent directory traversal
        try:
            resolved_path = Path(file_path).resolve()
        except (OSError, ValueError) as e:
            raise ValidationError(f"Invalid file path: {str(e)}")

        # Check for directory traversal attempts
        if '..' in file_path or file_path.startswith('/'):
            raise ValidationError("Directory traversal detected")

        # Check if path is within allowed base directory
        if base_dir:
            base_path = Path(base_dir).resolve()
            if not str(resolved_path).startswith(str(base_path)):
                raise ValidationError("File path outside allowed directory")

        # Check file extension
        if allowed_extensions:
            file_extension = resolved_path.suffix.lower()
            if file_extension not in [ext.lower() for ext in allowed_extensions]:
                raise ValidationError(f"File extension '{file_extension}' not allowed")

        # Check if file exists and is readable
        if not resolved_path.exists():
            raise ValidationError("File does not exist")

        if not resolved_path.is_file():
            raise ValidationError("Path is not a file")

        # Check file size
        file_size = resolved_path.stat().st_size
        if file_size > ContentValidator.MAX_FILE_SIZE:
            raise ValidationError(f"File size {file_size} exceeds maximum allowed size")

        return str(resolved_path)

    @staticmethod
    def validate_url(url: str) -> str:
        """
        Validate and sanitize URL

        Args:
            url: URL to validate

        Returns:
            Sanitized URL

        Raises:
            ValidationError: If URL is invalid
        """
        if not url or not isinstance(url, str):
            raise ValidationError("URL must be a non-empty string")

        if len(url) > ContentValidator.MAX_URL_LENGTH:
            raise ValidationError(f"URL exceeds maximum length of {ContentValidator.MAX_URL_LENGTH}")

        try:
            parsed = urlparse(url)

            # Must have scheme and netloc
            if not parsed.scheme or not parsed.netloc:
                raise ValidationError("Invalid URL format")

            # Only allow http and https
            if parsed.scheme not in ['http', 'https']:
                raise ValidationError("Only HTTP and HTTPS URLs are allowed")

            # Prevent localhost/private IP access
            if ContentValidator._is_private_host(parsed.netloc):
                raise ValidationError("Access to private/localhost addresses not allowed")

            return url

        except Exception as e:
            raise ValidationError(f"Invalid URL: {str(e)}")

    @staticmethod
    def _is_private_host(host: str) -> bool:
        """Check if host is private/localhost"""
        private_patterns = [
            r'^localhost$',
            r'^127\.',
            r'^10\.',
            r'^172\.(1[6-9]|2[0-9]|3[0-1])\.',
            r'^192\.168\.',
            r'^169\.254\.',
            r'^\[::1\]$',
            r'^\[fc00:',
            r'^\[fe80:'
        ]

        for pattern in private_patterns:
            if re.match(pattern, host, re.IGNORECASE):
                return True
        return False

    @staticmethod
    def validate_json(data: str) -> Dict[str, Any]:
        """
        Validate and parse JSON data

        Args:
            data: JSON string to validate

        Returns:
            Parsed JSON data

        Raises:
            ValidationError: If JSON is invalid
        """
        if not isinstance(data, str):
            raise ValidationError("JSON data must be a string")

        if len(data) > ContentValidator.MAX_TEXT_LENGTH:
            raise ValidationError("JSON data exceeds maximum length")

        try:
            parsed = json.loads(data)

            # Basic structure validation
            if not isinstance(parsed, dict):
                raise ValidationError("JSON must be an object")

            # Check for dangerous content in string values
            ContentValidator._validate_json_content(parsed)

            return parsed

        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON: {str(e)}")

    @staticmethod
    def _validate_json_content(data: Any, max_depth: int = 10, current_depth: int = 0) -> None:
        """Recursively validate JSON content"""
        if current_depth > max_depth:
            raise ValidationError("JSON structure too deep")

        if isinstance(data, str):
            # Check string content
            if len(data) > ContentValidator.MAX_TEXT_LENGTH:
                raise ValidationError("JSON string value too long")

            # Check for dangerous patterns
            for pattern in ContentValidator.DANGEROUS_PATTERNS:
                if pattern.search(data):
                    raise ValidationError("Dangerous content detected in JSON")

        elif isinstance(data, dict):
            for key, value in data.items():
                if not isinstance(key, str):
                    raise ValidationError("JSON object keys must be strings")
                ContentValidator._validate_json_content(value, max_depth, current_depth + 1)

        elif isinstance(data, list):
            for item in data:
                ContentValidator._validate_json_content(item, max_depth, current_depth + 1)

    @staticmethod
    def detect_file_type(file_path: str) -> str:
        """
        Detect actual file type using file extension (fallback when magic is not available)

        Args:
            file_path: Path to file

        Returns:
            Detected MIME type based on extension

        Raises:
            ValidationError: If file type detection fails
        """
        try:
            path = Path(file_path)
            extension = path.suffix.lower()

            # Simple MIME type mapping
            mime_map = {
                '.txt': 'text/plain',
                '.md': 'text/markdown',
                '.csv': 'text/csv',
                '.json': 'application/json',
                '.xml': 'application/xml',
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif',
                '.bmp': 'image/bmp',
                '.webp': 'image/webp',
                '.svg': 'image/svg+xml',
                '.mp4': 'video/mp4',
                '.avi': 'video/avi',
                '.mov': 'video/quicktime',
                '.mp3': 'audio/mpeg',
                '.wav': 'audio/wav',
                '.pdf': 'application/pdf',
            }

            mime_type = mime_map.get(extension)
            if not mime_type:
                # Default to binary if unknown
                mime_type = 'application/octet-stream'

            return mime_type

        except Exception as e:
            raise ValidationError(f"File type detection failed: {str(e)}")

    @staticmethod
    def validate_content_type(file_path: str, expected_type: str) -> bool:
        """
        Validate that file content matches expected type

        Args:
            file_path: Path to file
            expected_type: Expected content type ('text', 'image', etc.)

        Returns:
            True if content type matches

        Raises:
            ValidationError: If validation fails
        """
        detected_mime = ContentValidator.detect_file_type(file_path)

        allowed_mimes = ContentValidator.MIME_TYPES.get(expected_type, [])
        if detected_mime not in allowed_mimes:
            raise ValidationError(f"File content type {detected_mime} does not match expected type {expected_type}")

        return True

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and injection

        Args:
            filename: Original filename

        Returns:
            Sanitized filename

        Raises:
            ValidationError: If filename is invalid
        """
        if not filename or not isinstance(filename, str):
            raise ValidationError("Filename must be a non-empty string")

        # Remove path separators and dangerous characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '', filename)

        # Remove control characters
        sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', sanitized)

        # Limit length
        if len(sanitized) > 255:
            raise ValidationError("Filename too long")

        # Ensure it's not empty after sanitization
        if not sanitized.strip():
            raise ValidationError("Filename becomes empty after sanitization")

        return sanitized.strip()


class RequestValidator:
    """
    Request-level validation for API endpoints
    """

    @staticmethod
    def validate_content_request(content_id: str, content_type: str,
                               text_content: Optional[str] = None,
                               file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate a content moderation request

        Args:
            content_id: Unique content identifier
            content_type: Type of content ('text', 'image', etc.)
            text_content: Text content if applicable
            file_path: File path if applicable

        Returns:
            Validated and sanitized request data

        Raises:
            ValidationError: If validation fails
        """
        # Validate content ID
        if not content_id or not isinstance(content_id, str):
            raise ValidationError("Content ID must be a non-empty string")

        if len(content_id) > 100:
            raise ValidationError("Content ID too long")

        # Validate content type
        allowed_types = ['text', 'image', 'video', 'audio', 'mixed']
        if content_type not in allowed_types:
            raise ValidationError(f"Content type must be one of: {', '.join(allowed_types)}")

        validated_data = {
            'content_id': ContentValidator.sanitize_text(content_id, 100),
            'content_type': content_type
        }

        # Validate text content
        if text_content is not None:
            if content_type != 'text':
                raise ValidationError("Text content only allowed for text content type")

            validated_data['text_content'] = ContentValidator.sanitize_text(text_content)

        # Validate file path
        if file_path is not None:
            allowed_extensions = ContentValidator.ALLOWED_EXTENSIONS.get(content_type, [])
            validated_data['file_path'] = ContentValidator.validate_file_path(
                file_path, allowed_extensions
            )

            # Validate content type matches file
            ContentValidator.validate_content_type(file_path, content_type)

        return validated_data

    @staticmethod
    def validate_provider_config(provider: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate provider configuration

        Args:
            provider: Provider name
            config: Configuration dictionary

        Returns:
            Validated configuration

        Raises:
            ValidationError: If validation fails
        """
        if not isinstance(config, dict):
            raise ValidationError("Configuration must be a dictionary")

        validated_config = {}

        # Validate API key if present
        if 'api_key' in config:
            api_key = config['api_key']
            if not isinstance(api_key, str) or len(api_key.strip()) == 0:
                raise ValidationError("API key must be a non-empty string")

            # Basic format validation (will be enhanced when secret_manager is available)
            if len(api_key) < 10:
                raise ValidationError(f"API key too short for {provider}")

            validated_config['api_key'] = api_key

        # Validate timeout
        if 'timeout' in config:
            timeout = config['timeout']
            if not isinstance(timeout, (int, float)) or timeout <= 0:
                raise ValidationError("Timeout must be a positive number")
            validated_config['timeout'] = timeout

        # Validate model name
        if 'model' in config:
            model = config['model']
            if not isinstance(model, str) or len(model.strip()) == 0:
                raise ValidationError("Model must be a non-empty string")
            validated_config['model'] = model.strip()

        # Validate URL if present
        if 'base_url' in config:
            validated_config['base_url'] = ContentValidator.validate_url(config['base_url'])

        return validated_config


# Convenience functions for common validation tasks
def sanitize_user_input(text: str) -> str:
    """Sanitize user input text"""
    return ContentValidator.sanitize_text(text)


def validate_file_upload(file_path: str, content_type: str) -> str:
    """Validate uploaded file"""
    allowed_extensions = ContentValidator.ALLOWED_EXTENSIONS.get(content_type, [])
    return ContentValidator.validate_file_path(file_path, allowed_extensions)


def validate_api_request(content_id: str, content_type: str, **kwargs) -> Dict[str, Any]:
    """Validate API request data"""
    return RequestValidator.validate_content_request(content_id, content_type, **kwargs)