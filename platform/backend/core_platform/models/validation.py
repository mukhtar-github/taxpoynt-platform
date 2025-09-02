"""
Core Validation Utilities
========================
Central validation functions used across the TaxPoynt platform.
"""

import re
from decimal import Decimal
from typing import Any, Optional, List, Dict
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from .exceptions import ValidationError


class ValidationSeverity(str, Enum):
    """Severity levels for validation issues."""
    CRITICAL = "critical"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationResult:
    """Standard validation result structure."""
    
    def __init__(self, is_valid: bool, field: Optional[str] = None, message: str = "", 
                 severity: ValidationSeverity = ValidationSeverity.ERROR, error_code: Optional[str] = None,
                 expected_value: Any = None, actual_value: Any = None, suggestions: Optional[List[str]] = None):
        self.is_valid = is_valid
        self.field = field
        self.message = message
        self.severity = severity
        self.error_code = error_code
        self.expected_value = expected_value
        self.actual_value = actual_value
        self.suggestions = suggestions or []
        self.timestamp = datetime.utcnow()


@dataclass
class CrossRoleValidation:
    """Cross-role validation result structure."""
    validation_id: str
    roles_involved: List[str]
    validation_type: str
    is_valid: bool
    results: List[ValidationResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass 
class ValidationRule:
    """Validation rule definition."""
    rule_id: str
    rule_name: str
    description: str
    severity: ValidationSeverity
    field_path: Optional[str] = None
    validation_function: Optional[callable] = None
    parameters: Dict[str, Any] = field(default_factory=dict)


def validate_tin(tin: str) -> bool:
    """
    Validate Tax Identification Number (TIN) format.
    
    Args:
        tin: TIN string to validate
        
    Returns:
        True if TIN is valid, False otherwise
        
    Raises:
        ValidationError: If TIN format is invalid
    """
    if not tin:
        raise ValidationError("TIN cannot be empty", "tin", tin, "required")
    
    # Remove any spaces or special characters
    tin = re.sub(r'[^A-Z0-9]', '', tin.upper())
    
    # Basic TIN validation rules
    if len(tin) < 5:
        raise ValidationError("TIN must be at least 5 characters long", "tin", tin, "min_length")
    
    if len(tin) > 20:
        raise ValidationError("TIN cannot exceed 20 characters", "tin", tin, "max_length")
    
    # Check if TIN contains only alphanumeric characters
    if not re.match(r'^[A-Z0-9]+$', tin):
        raise ValidationError("TIN can only contain letters and numbers", "tin", tin, "alphanumeric_only")
    
    # Nigerian TIN specific validation (if it's a Nigerian TIN)
    if len(tin) == 11 and tin.startswith('TIN'):
        # Nigerian TIN format: TIN + 8 digits
        if not tin[3:].isdigit():
            raise ValidationError("Nigerian TIN must end with 8 digits", "tin", tin, "nigerian_format")
    
    return True


def validate_amount(amount: Any, min_amount: Optional[Decimal] = None, max_amount: Optional[Decimal] = None) -> bool:
    """
    Validate monetary amount.
    
    Args:
        amount: Amount to validate
        min_amount: Minimum allowed amount
        max_amount: Maximum allowed amount
        
    Returns:
        True if amount is valid, False otherwise
        
    Raises:
        ValidationError: If amount is invalid
    """
    try:
        # Convert to Decimal if it's not already
        if not isinstance(amount, Decimal):
            amount = Decimal(str(amount))
    except (ValueError, TypeError):
        raise ValidationError("Amount must be a valid number", "amount", amount, "numeric")
    
    # Check if amount is positive
    if amount < 0:
        raise ValidationError("Amount cannot be negative", "amount", amount, "positive")
    
    # Check minimum amount
    if min_amount is not None and amount < min_amount:
        raise ValidationError(f"Amount must be at least {min_amount}", "amount", amount, "min_amount")
    
    # Check maximum amount
    if max_amount is not None and amount > max_amount:
        raise ValidationError(f"Amount cannot exceed {max_amount}", "amount", amount, "max_amount")
    
    # Check decimal places (limit to 2 for currency)
    if amount.as_tuple().exponent < -2:
        raise ValidationError("Amount cannot have more than 2 decimal places", "amount", amount, "decimal_places")
    
    return True


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email string to validate
        
    Returns:
        True if email is valid, False otherwise
        
    Raises:
        ValidationError: If email format is invalid
    """
    if not email:
        raise ValidationError("Email cannot be empty", "email", email, "required")
    
    # Basic email regex pattern
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    
    if not re.match(email_pattern, email):
        raise ValidationError("Invalid email format", "email", email, "format")
    
    # Check length
    if len(email) > 254:
        raise ValidationError("Email address too long", "email", email, "max_length")
    
    return True


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone string to validate
        
    Returns:
        True if phone is valid, False otherwise
        
    Raises:
        ValidationError: If phone format is invalid
    """
    if not phone:
        raise ValidationError("Phone number cannot be empty", "phone", phone, "required")
    
    # Remove spaces, dashes, and parentheses
    phone = re.sub(r'[\s\-\(\)]', '', phone)
    
    # Check if it's a valid Nigerian phone number
    if phone.startswith('+234'):
        # International format
        if len(phone) != 14:
            raise ValidationError("Invalid Nigerian phone number length", "phone", phone, "length")
        if not phone[4:].isdigit():
            raise ValidationError("Invalid Nigerian phone number format", "phone", phone, "format")
    elif phone.startswith('0'):
        # Local format
        if len(phone) != 11:
            raise ValidationError("Invalid local phone number length", "phone", phone, "length")
        if not phone.isdigit():
            raise ValidationError("Invalid local phone number format", "phone", phone, "format")
    else:
        raise ValidationError("Phone number must start with +234 or 0", "phone", phone, "prefix")
    
    return True


def validate_currency(currency: str) -> bool:
    """
    Validate currency code.
    
    Args:
        currency: Currency code to validate
        
    Returns:
        True if currency is valid, False otherwise
        
    Raises:
        ValidationError: If currency code is invalid
    """
    if not currency:
        raise ValidationError("Currency code cannot be empty", "currency", currency, "required")
    
    # Supported currencies
    supported_currencies = ["NGN", "USD", "EUR", "GBP", "CAD", "AUD", "JPY", "CHF"]
    
    if currency not in supported_currencies:
        raise ValidationError(f"Unsupported currency: {currency}", "currency", currency, "supported")
    
    return True


def validate_date_range(start_date: Any, end_date: Any) -> bool:
    """
    Validate date range (start_date must be before end_date).
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        True if date range is valid, False otherwise
        
    Raises:
        ValidationError: If date range is invalid
    """
    try:
        from datetime import datetime, date
        
        # Convert to date objects if they're strings
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date).date()
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date).date()
        
        # Check if start_date is before end_date
        if start_date >= end_date:
            raise ValidationError("Start date must be before end date", "date_range", 
                                {"start_date": start_date, "end_date": end_date}, "chronological_order")
        
        return True
        
    except (ValueError, TypeError) as e:
        raise ValidationError(f"Invalid date format: {e}", "date_range", 
                            {"start_date": start_date, "end_date": end_date}, "date_format")


def validate_required_fields(data: dict, required_fields: List[str]) -> bool:
    """
    Validate that all required fields are present in data.
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        
    Returns:
        True if all required fields are present, False otherwise
        
    Raises:
        ValidationError: If required fields are missing
    """
    missing_fields = []
    
    for field in required_fields:
        if field not in data or data[field] is None:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}", 
                            "required_fields", missing_fields, "presence")
    
    return True


def validate_field_length(value: str, field_name: str, max_length: int, min_length: int = 0) -> bool:
    """
    Validate field length constraints.
    
    Args:
        value: Field value to validate
        field_name: Name of the field being validated
        max_length: Maximum allowed length
        min_length: Minimum required length
        
    Returns:
        True if length is valid, False otherwise
        
    Raises:
        ValidationError: If length constraints are violated
    """
    if not isinstance(value, str):
        raise ValidationError(f"{field_name} must be a string", field_name, value, "string_type")
    
    if len(value) < min_length:
        raise ValidationError(f"{field_name} must be at least {min_length} characters long", 
                            field_name, value, "min_length")
    
    if len(value) > max_length:
        raise ValidationError(f"{field_name} cannot exceed {max_length} characters", 
                            field_name, value, "max_length")
    
    return True


def validate_numeric_range(value: Any, field_name: str, min_value: Optional[float] = None, 
                          max_value: Optional[float] = None) -> bool:
    """
    Validate numeric value is within specified range.
    
    Args:
        value: Numeric value to validate
        field_name: Name of the field being validated
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        
    Returns:
        True if value is within range, False otherwise
        
    Raises:
        ValidationError: If value is outside allowed range
    """
    try:
        numeric_value = float(value)
    except (ValueError, TypeError):
        raise ValidationError(f"{field_name} must be a valid number", field_name, value, "numeric")
    
    if min_value is not None and numeric_value < min_value:
        raise ValidationError(f"{field_name} must be at least {min_value}", field_name, value, "min_value")
    
    if max_value is not None and numeric_value > max_value:
        raise ValidationError(f"{field_name} cannot exceed {max_value}", field_name, value, "max_value")
    
    return True


def validate_enum_value(value: Any, field_name: str, allowed_values: List[Any]) -> bool:
    """
    Validate that value is one of the allowed enum values.
    
    Args:
        value: Value to validate
        field_name: Name of the field being validated
        allowed_values: List of allowed values
        
    Returns:
        True if value is allowed, False otherwise
        
    Raises:
        ValidationError: If value is not in allowed values
    """
    if value not in allowed_values:
        raise ValidationError(f"{field_name} must be one of: {', '.join(map(str, allowed_values))}", 
                            field_name, value, "enum_value")
    
    return True
