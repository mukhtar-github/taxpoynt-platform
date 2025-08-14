"""
Core Platform Shared Components
===============================
Shared base classes and utilities used across the platform services.
"""

from .base_service import BaseService
from .exceptions import (
    AuthenticationError,
    AuthorizationError,
    ValidationError,
    ConfigurationError,
    ServiceError
)

__all__ = [
    'BaseService',
    'AuthenticationError', 
    'AuthorizationError',
    'ValidationError',
    'ConfigurationError', 
    'ServiceError'
]