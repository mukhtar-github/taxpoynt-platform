"""
Core Platform Exceptions
========================
Standard exception classes used across the TaxPoynt platform.
"""

class ServiceError(Exception):
    """Base exception for all service-related errors"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or "SERVICE_ERROR"
        self.details = details or {}


class AuthenticationError(ServiceError):
    """Authentication-related errors"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message, error_code or "AUTH_ERROR", details)


class AuthorizationError(ServiceError):
    """Authorization-related errors"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message, error_code or "AUTHZ_ERROR", details)


class ValidationError(ServiceError):
    """Data validation errors"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message, error_code or "VALIDATION_ERROR", details)


class ConfigurationError(ServiceError):
    """Configuration-related errors"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message, error_code or "CONFIG_ERROR", details)


class IntegrationError(ServiceError):
    """External integration errors"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message, error_code or "INTEGRATION_ERROR", details)


class DatabaseError(ServiceError):
    """Database-related errors"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message, error_code or "DATABASE_ERROR", details)


class NetworkError(ServiceError):
    """Network-related errors"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message, error_code or "NETWORK_ERROR", details)


class SecurityError(ServiceError):
    """Security-related errors"""
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message, error_code or "SECURITY_ERROR", details)