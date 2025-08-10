"""
Configuration settings for submission retry and failure handling.

This module extends the core application configuration with settings
specific to the retry mechanism and failure alerting system.
"""

from pydantic import validator, Field

# Handle both Pydantic V1 and V2 compatibility
try:
    # Try importing from pydantic (V1)
    from pydantic import BaseSettings
except ImportError:
    # Fall back to pydantic-settings (V2)
    from pydantic_settings import BaseSettings
from typing import List, Dict, Any, Optional


class RetrySettings(BaseSettings):
    """Settings for submission retry and failure handling."""
    
    # Configuration for Pydantic V2
    model_config = {
        "case_sensitive": True,
        "env_file": ".env",
        "extra": "ignore"  # Allow extra fields in environment variables
    }
    
    # Retry mechanism settings
    MAX_RETRY_ATTEMPTS: int = 5
    BASE_RETRY_DELAY: int = 60  # seconds
    RETRY_BACKOFF_FACTOR: float = 2.0
    RETRY_JITTER: float = 0.1
    RETRY_PROCESSOR_INTERVAL: int = 60  # seconds
    
    # Alert settings
    ENABLE_FAILURE_ALERTS: bool = True
    EMAIL_ALERTS_ENABLED: bool = False
    SLACK_ALERTS_ENABLED: bool = False
    
    # Email alert settings
    ALERT_EMAIL_RECIPIENTS: List[str] = []
    ALERT_EMAIL_FROM: str = "alerts@taxpoynt.einvoice"
    
    # Slack alert settings
    SLACK_WEBHOOK_URL: Optional[str] = None
    
    # Failure logging settings
    DETAILED_FAILURE_LOGGING: bool = True
    
    # Alert thresholds
    ALERT_ON_CONSECUTIVE_FAILURES: int = 3
    ALERT_ON_FAILURE_PERCENTAGE: float = 0.1  # Alert if 10% of submissions fail
    


# Create an instance for importing
retry_settings = RetrySettings()
