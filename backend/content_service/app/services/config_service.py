"""
Configuration Service - Centralized Configuration Management
==========================================================

Provides centralized configuration management with:
- Environment-based configuration loading
- Validation and type checking
- Secret management integration
- Configuration caching and hot-reload
"""

import os
import json
from typing import Dict, Any, Optional, Union
from enum import Enum
from dataclasses import dataclass, field
from pathlib import Path

from app.services.base_service import BaseService, ValidationError


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class DatabaseConfig:
    """Database configuration"""
    uri: str
    name: str = "content_service"
    min_connections: int = 1
    max_connections: int = 10
    connection_timeout: int = 30
    query_timeout: int = 30


@dataclass
class AuthConfig:
    """Authentication configuration"""
    secret_key: str
    jwt_secret_key: str
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_hash_rounds: int = 12
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15


@dataclass
class AIConfig:
    """AI service configuration"""
    primary_provider: str = "gemini"
    providers: Dict[str, Dict] = field(default_factory=dict)
    fallback_enabled: bool = True
    confidence_threshold: float = 0.8
    max_retries: int = 3
    timeout_seconds: int = 30


@dataclass
class StorageConfig:
    """File storage configuration"""
    provider: str = "azure"  # azure, aws, gcp, local
    connection_string: str = ""
    container_name: str = "content"
    max_file_size_mb: int = 100
    allowed_extensions: list = field(default_factory=lambda: [
        "jpg", "jpeg", "png", "gif", "webp",
        "mp4", "webm", "mov", "avi",
        "pdf", "html", "css", "js"
    ])


@dataclass
class SecurityConfig:
    """Security configuration"""
    enable_rate_limiting: bool = True
    rate_limit_requests_per_minute: int = 60
    enable_cors: bool = True
    allowed_origins: list = field(default_factory=lambda: ["*"])
    enable_https_redirect: bool = True
    session_security: bool = True


@dataclass
class ComplianceConfig:
    """Compliance and privacy configuration"""
    enable_audit_logging: bool = True
    audit_retention_days: int = 90
    enable_gdpr_compliance: bool = True
    enable_data_anonymization: bool = True
    privacy_policy_url: str = ""
    terms_of_service_url: str = ""


@dataclass
class ApplicationConfig:
    """Main application configuration"""
    app_name: str = "Adara Digital Signage Platform"
    version: str = "1.0.0"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000
    log_level: str = "INFO"

    # Sub-configurations
    database: DatabaseConfig = None
    auth: AuthConfig = None
    ai: AIConfig = None
    storage: StorageConfig = None
    security: SecurityConfig = None
    compliance: ComplianceConfig = None

    # Custom settings
    custom: Dict[str, Any] = field(default_factory=dict)


class ConfigService(BaseService):
    """
    Centralized configuration service with validation and environment support
    """

    def __init__(self):
        super().__init__()
        self._config: Optional[ApplicationConfig] = None
        self._loaded_from_env = False

    @property
    def config(self) -> ApplicationConfig:
        """Get the current configuration, loading if necessary"""
        if self._config is None:
            self._config = self.load_config()
        return self._config

    def load_config(self, config_file: str = None) -> ApplicationConfig:
        """Load configuration from environment variables and optional config file"""

        # Start with default configuration
        config = ApplicationConfig()

        # Load from environment variables
        config = self._load_from_environment(config)

        # Load from config file if provided
        if config_file:
            config = self._load_from_file(config, config_file)

        # Initialize sub-configurations
        config.database = self._load_database_config()
        config.auth = self._load_auth_config()
        config.ai = self._load_ai_config()
        config.storage = self._load_storage_config()
        config.security = self._load_security_config()
        config.compliance = self._load_compliance_config()

        # Validate configuration
        self._validate_config(config)

        self.logger.info(f"Configuration loaded for environment: {config.environment}")
        return config

    def _load_from_environment(self, config: ApplicationConfig) -> ApplicationConfig:
        """Load configuration from environment variables"""

        # Application settings
        config.environment = Environment(os.getenv("ENVIRONMENT", "development"))
        config.debug = os.getenv("DEBUG", "false").lower() == "true"
        config.host = os.getenv("HOST", "0.0.0.0")
        config.port = int(os.getenv("PORT", "8000"))
        config.log_level = os.getenv("LOG_LEVEL", "INFO")

        return config

    def _load_from_file(self, config: ApplicationConfig, config_file: str) -> ApplicationConfig:
        """Load configuration from JSON file"""
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                self.logger.warning(f"Config file not found: {config_file}")
                return config

            with open(config_path, 'r') as f:
                file_config = json.load(f)

            # Merge file configuration with existing config
            for key, value in file_config.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                else:
                    config.custom[key] = value

            self.logger.info(f"Configuration loaded from file: {config_file}")

        except Exception as e:
            self.logger.warning(f"Failed to load config file {config_file}: {e}")

        return config

    def _load_database_config(self) -> DatabaseConfig:
        """Load database configuration"""
        return DatabaseConfig(
            uri=os.getenv("MONGO_URI", "mongodb://localhost:27017/content_service"),
            name=os.getenv("DB_NAME", "content_service"),
            min_connections=int(os.getenv("DB_MIN_CONNECTIONS", "1")),
            max_connections=int(os.getenv("DB_MAX_CONNECTIONS", "10")),
            connection_timeout=int(os.getenv("DB_CONNECTION_TIMEOUT", "30")),
            query_timeout=int(os.getenv("DB_QUERY_TIMEOUT", "30"))
        )

    def _load_auth_config(self) -> AuthConfig:
        """Load authentication configuration"""
        secret_key = os.getenv("SECRET_KEY")
        jwt_secret_key = os.getenv("JWT_SECRET_KEY")

        if not secret_key or not jwt_secret_key:
            raise ValidationError("SECRET_KEY and JWT_SECRET_KEY must be set in environment")

        return AuthConfig(
            secret_key=secret_key,
            jwt_secret_key=jwt_secret_key,
            access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")),
            refresh_token_expire_days=int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")),
            password_hash_rounds=int(os.getenv("PASSWORD_HASH_ROUNDS", "12")),
            max_login_attempts=int(os.getenv("MAX_LOGIN_ATTEMPTS", "5")),
            lockout_duration_minutes=int(os.getenv("LOCKOUT_DURATION_MINUTES", "15"))
        )

    def _load_ai_config(self) -> AIConfig:
        """Load AI service configuration"""
        providers = {}

        # Gemini configuration
        if os.getenv("GEMINI_API_KEY"):
            providers["gemini"] = {
                "api_key": os.getenv("GEMINI_API_KEY"),
                "enabled": os.getenv("ENABLE_GEMINI_AGENT", "true").lower() == "true"
            }

        # OpenAI configuration
        if os.getenv("OPENAI_API_KEY"):
            providers["openai"] = {
                "api_key": os.getenv("OPENAI_API_KEY"),
                "enabled": os.getenv("ENABLE_OPENAI_AGENT", "true").lower() == "true"
            }

        # Claude configuration
        if os.getenv("ANTHROPIC_API_KEY"):
            providers["claude"] = {
                "api_key": os.getenv("ANTHROPIC_API_KEY"),
                "enabled": os.getenv("ENABLE_CLAUDE_AGENT", "true").lower() == "true"
            }

        # Ollama configuration
        providers["ollama"] = {
            "base_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"),
            "enabled": os.getenv("ENABLE_OLLAMA_AGENT", "true").lower() == "true"
        }

        return AIConfig(
            primary_provider=os.getenv("PRIMARY_AI_PROVIDER", "gemini"),
            providers=providers,
            fallback_enabled=os.getenv("AI_FALLBACK_ENABLED", "true").lower() == "true",
            confidence_threshold=float(os.getenv("AI_CONFIDENCE_THRESHOLD", "0.8")),
            max_retries=int(os.getenv("AI_MAX_RETRIES", "3")),
            timeout_seconds=int(os.getenv("AI_TIMEOUT_SECONDS", "30"))
        )

    def _load_storage_config(self) -> StorageConfig:
        """Load storage configuration"""
        return StorageConfig(
            provider=os.getenv("STORAGE_PROVIDER", "azure"),
            connection_string=os.getenv("AZURE_STORAGE_CONNECTION_STRING", ""),
            container_name=os.getenv("AZURE_CONTAINER_NAME", "content"),
            max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "100"))
        )

    def _load_security_config(self) -> SecurityConfig:
        """Load security configuration"""
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")

        return SecurityConfig(
            enable_rate_limiting=os.getenv("ENABLE_RATE_LIMITING", "true").lower() == "true",
            rate_limit_requests_per_minute=int(os.getenv("RATE_LIMIT_RPM", "60")),
            enable_cors=os.getenv("ENABLE_CORS", "true").lower() == "true",
            allowed_origins=allowed_origins,
            enable_https_redirect=os.getenv("ENABLE_HTTPS_REDIRECT", "true").lower() == "true",
            session_security=os.getenv("SESSION_SECURITY", "true").lower() == "true"
        )

    def _load_compliance_config(self) -> ComplianceConfig:
        """Load compliance configuration"""
        return ComplianceConfig(
            enable_audit_logging=os.getenv("ENABLE_AUDIT_LOGGING", "true").lower() == "true",
            audit_retention_days=int(os.getenv("AUDIT_RETENTION_DAYS", "90")),
            enable_gdpr_compliance=os.getenv("ENABLE_GDPR_COMPLIANCE", "true").lower() == "true",
            enable_data_anonymization=os.getenv("ENABLE_DATA_ANONYMIZATION", "true").lower() == "true",
            privacy_policy_url=os.getenv("PRIVACY_POLICY_URL", ""),
            terms_of_service_url=os.getenv("TERMS_OF_SERVICE_URL", "")
        )

    def _validate_config(self, config: ApplicationConfig):
        """Validate the loaded configuration"""
        errors = []

        # Validate required fields
        if not config.auth.secret_key:
            errors.append("SECRET_KEY is required")

        if not config.auth.jwt_secret_key:
            errors.append("JWT_SECRET_KEY is required")

        if not config.database.uri:
            errors.append("Database URI is required")

        # Validate AI configuration
        if not config.ai.providers:
            errors.append("At least one AI provider must be configured")

        # Validate production-specific settings
        if config.environment == Environment.PRODUCTION:
            if config.debug:
                errors.append("Debug mode should be disabled in production")

            if not config.storage.connection_string:
                errors.append("Storage connection string is required in production")

        if errors:
            raise ValidationError(f"Configuration validation failed: {'; '.join(errors)}")

    def get_setting(self, key: str, default: Any = None) -> Any:
        """Get a configuration setting by key path (e.g., 'database.uri')"""
        try:
            value = self.config
            for part in key.split('.'):
                if hasattr(value, part):
                    value = getattr(value, part)
                elif isinstance(value, dict) and part in value:
                    value = value[part]
                else:
                    return default
            return value
        except Exception:
            return default

    def update_setting(self, key: str, value: Any):
        """Update a configuration setting at runtime"""
        # This is for dynamic configuration updates
        # In production, this should be carefully controlled
        self.logger.warning(f"Runtime configuration update: {key} = {value}")

        # Update in custom settings for now
        self.config.custom[key] = value

    def reload_config(self, config_file: str = None):
        """Reload configuration"""
        self.logger.info("Reloading configuration...")
        self._config = self.load_config(config_file)

    def get_environment_info(self) -> Dict[str, Any]:
        """Get current environment information"""
        return {
            "environment": self.config.environment.value,
            "debug": self.config.debug,
            "version": self.config.version,
            "host": self.config.host,
            "port": self.config.port,
            "database_configured": bool(self.config.database.uri),
            "ai_providers_configured": len(self.config.ai.providers),
            "storage_configured": bool(self.config.storage.connection_string)
        }


# Create global configuration service instance
config_service = ConfigService()

# Convenience function for getting configuration
def get_config() -> ApplicationConfig:
    """Get the current application configuration"""
    return config_service.config

# Convenience function for getting specific settings
def get_setting(key: str, default: Any = None) -> Any:
    """Get a configuration setting by key"""
    return config_service.get_setting(key, default)

# Register in service registry
from app.services.base_service import service_registry
service_registry.register("config", config_service)