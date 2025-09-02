"""
Core Platform Models
===================
Central data models and structures for the TaxPoynt platform.
"""

from .invoice import Invoice, InvoiceItem, CustomerInfo, create_invoice_from_items, validate_invoice_structure
from .exceptions import (
    TaxPoyntException,
    InvoiceGenerationError,
    ValidationError,
    DataIntegrityError,
    ConfigurationError,
    IntegrationError,
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    ServiceUnavailableError,
    TimeoutError,
    ResourceNotFoundError,
    DuplicateResourceError,
    BusinessLogicError,
    ComplianceError
)
from .validation import (
    ValidationResult,
    CrossRoleValidation,
    ValidationRule,
    ValidationSeverity,
    validate_tin,
    validate_amount,
    validate_email,
    validate_phone,
    validate_currency,
    validate_date_range,
    validate_required_fields,
    validate_field_length,
    validate_numeric_range,
    validate_enum_value
)

__all__ = [
    # Invoice models
    "Invoice",
    "InvoiceItem", 
    "CustomerInfo",
    "create_invoice_from_items",
    "validate_invoice_structure",
    
    # Exceptions
    "TaxPoyntException",
    "InvoiceGenerationError",
    "ValidationError",
    "DataIntegrityError",
    "ConfigurationError",
    "IntegrationError",
    "AuthenticationError",
    "AuthorizationError",
    "RateLimitError",
    "ServiceUnavailableError",
    "TimeoutError",
    "ResourceNotFoundError",
    "DuplicateResourceError",
    "BusinessLogicError",
    "ComplianceError",
    
    # Validation models and utilities
    "ValidationResult",
    "CrossRoleValidation", 
    "ValidationRule",
    "ValidationSeverity",
    "validate_tin",
    "validate_amount",
    "validate_email",
    "validate_phone",
    "validate_currency",
    "validate_date_range",
    "validate_required_fields",
    "validate_field_length",
    "validate_numeric_range",
    "validate_enum_value"
]