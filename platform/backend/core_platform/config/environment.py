"""
TaxPoynt Platform - Environment-Aware Configuration
===================================================

Single source of truth for environment configuration with automatic overrides.
Eliminates the need for multiple .env files by detecting ENVIRONMENT variable
and applying appropriate settings.
"""

import os
from typing import Dict, Any, Optional
from enum import Enum
import logging


def _env_flag(name: str, default: bool = False) -> bool:
    """Parse boolean feature flags from environment variables."""
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}

logger = logging.getLogger(__name__)


class Environment(Enum):
    """Supported deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class EnvironmentConfig:
    """
    Environment-aware configuration manager.
    
    Reads from single .env file and applies environment-specific overrides
    based on the ENVIRONMENT variable.
    """
    
    def __init__(self):
        self.environment = Environment(os.getenv("ENVIRONMENT", "production"))
        self._config_cache: Dict[str, Any] = {}
        
        logger.info(f"🌍 Environment detected: {self.environment.value}")
        
    def get_database_url(self) -> str:
        """Get the appropriate database URL for the current environment."""
        base_url = os.getenv("DATABASE_URL", "")
        
        if self.environment == Environment.DEVELOPMENT:
            # Use Docker PostgreSQL for development
            return "postgresql://taxpoynt_user:taxpoynt_dev_pass@localhost:5433/taxpoynt_platform"
        elif self.environment == Environment.STAGING:
            # Use staging database (could be Railway or other provider)
            staging_url = os.getenv("STAGING_DATABASE_URL")
            return staging_url or base_url
        else:  # PRODUCTION
            # Use Railway PostgreSQL (from environment)
            return base_url
            
    def get_redis_url(self) -> str:
        """Get the appropriate Redis URL for the current environment."""
        base_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        if self.environment == Environment.DEVELOPMENT:
            # Use Docker Redis for development
            return "redis://localhost:6380/0"
        elif self.environment == Environment.STAGING:
            # Use staging Redis
            staging_url = os.getenv("STAGING_REDIS_URL")
            return staging_url or base_url
        else:  # PRODUCTION
            # Use Railway Redis (from environment)
            return base_url
            
    def get_frontend_url(self) -> str:
        """Get the appropriate frontend URL for the current environment."""
        base_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        
        if self.environment == Environment.DEVELOPMENT:
            return "http://localhost:3000"
        elif self.environment == Environment.STAGING:
            return os.getenv("STAGING_FRONTEND_URL", "https://staging-taxpoynt.vercel.app")
        else:  # PRODUCTION
            return base_url
            
    def get_api_url(self) -> str:
        """Get the appropriate API URL for the current environment."""
        base_url = os.getenv("NEXT_PUBLIC_API_URL", "http://localhost:8000/api/v1")
        
        if self.environment == Environment.DEVELOPMENT:
            return "http://localhost:8000/api/v1"
        elif self.environment == Environment.STAGING:
            return os.getenv("STAGING_API_URL", "https://staging-api-taxpoynt.railway.app/api/v1")
        else:  # PRODUCTION
            return base_url
    
    def is_debug_enabled(self) -> bool:
        """Check if debug mode should be enabled."""
        base_debug = os.getenv("DEBUG", "false").lower() == "true"
        
        if self.environment in [Environment.DEVELOPMENT, Environment.STAGING]:
            return True
        else:  # PRODUCTION
            return base_debug
            
    def get_log_level(self) -> str:
        """Get the appropriate log level for the current environment."""
        base_level = os.getenv("LOG_LEVEL", "INFO")
        
        if self.environment == Environment.DEVELOPMENT:
            return "DEBUG"
        elif self.environment == Environment.STAGING:
            return "DEBUG"
        else:  # PRODUCTION
            return base_level
            
    def get_allowed_origins(self) -> list[str]:
        """Get CORS allowed origins for the current environment."""
        base_origins = os.getenv("ALLOWED_ORIGINS", "").split(",")
        
        if self.environment == Environment.DEVELOPMENT:
            return [
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",  # Secondary dev port
            ]
        elif self.environment == Environment.STAGING:
            return [
                "https://staging-taxpoynt.vercel.app",
                "http://localhost:3000",  # Allow local dev to connect to staging API
            ]
        else:  # PRODUCTION
            return [origin.strip() for origin in base_origins if origin.strip()]
            
    def get_feature_flags(self) -> Dict[str, bool]:
        """Get feature flags for the current environment."""
        base_flags = {
            "ENABLE_REAL_TIME_MONITORING": False,
            "ENABLE_ODOO_DIRECT_CONNECT": False,
            "ENABLE_ADVANCED_ANALYTICS": False,
            "ENABLE_DEBUG_TOOLBAR": False,
            "ENABLE_SQL_LOGGING": False,
            "DISABLE_RATE_LIMITING": False,
            "FIRS_REMOTE_IRN": False,
        }

        if self.environment == Environment.DEVELOPMENT:
            base_flags.update({
                "ENABLE_REAL_TIME_MONITORING": True,
                "ENABLE_ODOO_DIRECT_CONNECT": True,
                "ENABLE_ADVANCED_ANALYTICS": True,
                "ENABLE_DEBUG_TOOLBAR": True,
                "ENABLE_SQL_LOGGING": True,
                "DISABLE_RATE_LIMITING": True,
                "FIRS_REMOTE_IRN": _env_flag("FIRS_REMOTE_IRN", default=False),
            })
        elif self.environment == Environment.STAGING:
            base_flags.update({
                "ENABLE_REAL_TIME_MONITORING": True,
                "ENABLE_ADVANCED_ANALYTICS": True,
                "ENABLE_DEBUG_TOOLBAR": True,
                "FIRS_REMOTE_IRN": _env_flag("FIRS_REMOTE_IRN", default=False),
            })
        else:  # PRODUCTION
            base_flags.update({
                "ENABLE_REAL_TIME_MONITORING": _env_flag("NEXT_PUBLIC_ENABLE_REAL_TIME_MONITORING", default=False),
                "ENABLE_ODOO_DIRECT_CONNECT": _env_flag("NEXT_PUBLIC_ENABLE_ODOO_DIRECT_CONNECT", default=False),
                "ENABLE_ADVANCED_ANALYTICS": _env_flag("NEXT_PUBLIC_ENABLE_ADVANCED_ANALYTICS", default=False),
                "FIRS_REMOTE_IRN": _env_flag("FIRS_REMOTE_IRN", default=False),
            })

        return base_flags
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get complete database configuration for the current environment."""
        config = {
            "url": self.get_database_url(),
            "pool_size": int(os.getenv("DB_POOL_SIZE", "5")),
            "max_overflow": int(os.getenv("DB_MAX_OVERFLOW", "10")),
            "echo": self.is_debug_enabled() and os.getenv("ENABLE_SQL_LOGGING", "false").lower() == "true",
            "pool_pre_ping": True,  # Always enable connection health checks
        }
        
        # Development-specific optimizations
        if self.environment == Environment.DEVELOPMENT:
            config.update({
                "pool_size": 2,  # Smaller pool for development
                "max_overflow": 5,
                "echo": True,  # Enable SQL logging in development
            })
            
        return config
        
    def get_security_config(self) -> Dict[str, Any]:
        """Get security configuration for the current environment."""
        base_config = {
            "secret_key": os.getenv("SECRET_KEY", ""),
            "jwt_secret_key": os.getenv("JWT_SECRET_KEY", ""),
            "jwt_algorithm": os.getenv("JWT_ALGORITHM", "HS256"),
            "jwt_access_token_expire_minutes": int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60")),
            "jwt_refresh_token_expire_days": int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30")),
        }
        
        # Development overrides
        if self.environment == Environment.DEVELOPMENT:
            base_config.update({
                "secret_key": "development_secret_key_32_char_minimum_for_jwt_signing_security",
                "jwt_secret_key": "development_jwt_secret_key_64_chars_for_maximum_security_strength",
                "jwt_access_token_expire_minutes": 480,  # 8 hours for development convenience
            })
        
        return base_config
        
    def get_test_database_url(self) -> str:
        """Get test database URL for the current environment."""
        base_test_url = os.getenv("TEST_DATABASE_URL", "")
        
        if self.environment == Environment.DEVELOPMENT:
            return "postgresql://taxpoynt_user:taxpoynt_dev_pass@localhost:5433/taxpoynt_test"
        else:
            return base_test_url or self.get_database_url().replace("/railway", "/taxpoynt_test")
            
    def validate_configuration(self) -> Dict[str, list[str]]:
        """Validate current configuration and return any issues."""
        issues = {
            "errors": [],
            "warnings": [],
            "info": []
        }
        
        # Check database URL
        db_url = self.get_database_url()
        if not db_url:
            issues["errors"].append("DATABASE_URL is required")
        elif not db_url.startswith("postgresql://"):
            issues["warnings"].append("Non-PostgreSQL database detected - some features may not work")
            
        # Check Redis URL
        if not self.get_redis_url():
            issues["warnings"].append("REDIS_URL not configured - caching disabled")
            
        # Check security configuration
        security = self.get_security_config()
        if len(security["secret_key"]) < 32:
            issues["errors"].append("SECRET_KEY must be at least 32 characters long")
            
        # Environment-specific checks
        if self.environment == Environment.PRODUCTION:
            if "development" in security["secret_key"].lower():
                issues["errors"].append("Production environment using development security keys!")
                
        return issues


# Global configuration instance
config = EnvironmentConfig()


def get_config() -> EnvironmentConfig:
    """Get the global configuration instance."""
    return config
