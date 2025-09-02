"""
Core Exceptions
==============
Central exception classes used across the TaxPoynt platform.
"""


class TaxPoyntException(Exception):
    """Base exception for all TaxPoynt platform errors."""
    
    def __init__(self, message: str, error_code: str = None, details: dict = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class InvoiceGenerationError(TaxPoyntException):
    """Raised when invoice generation fails."""
    
    def __init__(self, message: str, invoice_id: str = None, validation_errors: list = None):
        super().__init__(message, "INVOICE_GENERATION_ERROR", {
            "invoice_id": invoice_id,
            "validation_errors": validation_errors or []
        })


class ValidationError(TaxPoyntException):
    """Raised when data validation fails."""
    
    def __init__(self, message: str, field: str = None, value: any = None, validation_rule: str = None):
        super().__init__(message, "VALIDATION_ERROR", {
            "field": field,
            "value": value,
            "validation_rule": validation_rule
        })


class DataIntegrityError(TaxPoyntException):
    """Raised when data integrity constraints are violated."""
    
    def __init__(self, message: str, entity_type: str = None, entity_id: str = None):
        super().__init__(message, "DATA_INTEGRITY_ERROR", {
            "entity_type": entity_type,
            "entity_id": entity_id
        })


class ConfigurationError(TaxPoyntException):
    """Raised when system configuration is invalid."""
    
    def __init__(self, message: str, config_key: str = None, config_value: any = None):
        super().__init__(message, "CONFIGURATION_ERROR", {
            "config_key": config_key,
            "config_value": config_value
        })


class IntegrationError(TaxPoyntException):
    """Raised when external system integration fails."""
    
    def __init__(self, message: str, integration_name: str = None, response_code: int = None):
        super().__init__(message, "INTEGRATION_ERROR", {
            "integration_name": integration_name,
            "response_code": response_code
        })


class AuthenticationError(TaxPoyntException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str, user_id: str = None, auth_method: str = None):
        super().__init__(message, "AUTHENTICATION_ERROR", {
            "user_id": user_id,
            "auth_method": auth_method
        })


class AuthorizationError(TaxPoyntException):
    """Raised when authorization fails."""
    
    def __init__(self, message: str, user_id: str = None, required_permission: str = None):
        super().__init__(message, "AUTHORIZATION_ERROR", {
            "user_id": user_id,
            "required_permission": required_permission
        })


class RateLimitError(TaxPoyntException):
    """Raised when rate limits are exceeded."""
    
    def __init__(self, message: str, limit_type: str = None, retry_after: int = None):
        super().__init__(message, "RATE_LIMIT_ERROR", {
            "limit_type": limit_type,
            "retry_after": retry_after
        })


class ServiceUnavailableError(TaxPoyntException):
    """Raised when a required service is unavailable."""
    
    def __init__(self, message: str, service_name: str = None, retry_after: int = None):
        super().__init__(message, "SERVICE_UNAVAILABLE_ERROR", {
            "service_name": service_name,
            "retry_after": retry_after
        })


class TimeoutError(TaxPoyntException):
    """Raised when an operation times out."""
    
    def __init__(self, message: str, operation: str = None, timeout_seconds: int = None):
        super().__init__(message, "TIMEOUT_ERROR", {
            "operation": operation,
            "timeout_seconds": timeout_seconds
        })


class ResourceNotFoundError(TaxPoyntException):
    """Raised when a requested resource is not found."""
    
    def __init__(self, message: str, resource_type: str = None, resource_id: str = None):
        super().__init__(message, "RESOURCE_NOT_FOUND_ERROR", {
            "resource_type": resource_type,
            "resource_id": resource_id
        })


class DuplicateResourceError(TaxPoyntException):
    """Raised when trying to create a duplicate resource."""
    
    def __init__(self, message: str, resource_type: str = None, resource_id: str = None):
        super().__init__(message, "DUPLICATE_RESOURCE_ERROR", {
            "resource_type": resource_type,
            "resource_id": resource_id
        })


class BusinessLogicError(TaxPoyntException):
    """Raised when business logic rules are violated."""
    
    def __init__(self, message: str, business_rule: str = None, context: dict = None):
        super().__init__(message, "BUSINESS_LOGIC_ERROR", {
            "business_rule": business_rule,
            "context": context or {}
        })


class ComplianceError(TaxPoyntException):
    """Raised when compliance requirements are not met."""
    
    def __init__(self, message: str, compliance_rule: str = None, regulation: str = None):
        super().__init__(message, "COMPLIANCE_ERROR", {
            "compliance_rule": compliance_rule,
            "regulation": regulation
        })
