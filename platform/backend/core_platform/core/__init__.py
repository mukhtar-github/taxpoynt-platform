"""
Core Module
==========
Core functionality re-exported from core_platform for backward compatibility.
"""

# Re-export models for backward compatibility
from ..models import (
    Invoice,
    InvoiceItem,
    CustomerInfo,
    create_invoice_from_items,
    validate_invoice_structure,
    TaxPoyntException,
    InvoiceGenerationError,
    ValidationError,
    validate_tin,
    validate_amount
)

__all__ = [
    "Invoice",
    "InvoiceItem",
    "CustomerInfo", 
    "create_invoice_from_items",
    "validate_invoice_structure",
    "TaxPoyntException",
    "InvoiceGenerationError",
    "ValidationError",
    "validate_tin",
    "validate_amount"
]
