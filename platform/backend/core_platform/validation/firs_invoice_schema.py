"""
FIRS Invoice Schema
===================

Pydantic models describing the structure of FIRS UBL-compliant invoice
payloads. These models provide server-side validation before forwarding
requests to FIRS or downstream services.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, ValidationError, validator, constr, condecimal


class SupplierModel(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)
    tin: Optional[str] = Field(None, description="Tax Identification Number (optional)")
    service_id: constr(strip_whitespace=True, min_length=1) = Field(..., alias="serviceId")
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, str]] = None

    class Config:
        allow_population_by_field_name = True


class CustomerModel(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)
    tin: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[Dict[str, str]] = None


class InvoiceLineItemModel(BaseModel):
    description: constr(strip_whitespace=True, min_length=1)
    quantity: condecimal(gt=0, decimal_places=4) = Field(..., alias="quantity")
    unit_price: condecimal(gt=0, decimal_places=4) = Field(..., alias="unitPrice")
    tax_amount: Optional[condecimal(ge=0, decimal_places=4)] = Field(0, alias="taxAmount")
    total: condecimal(gt=0, decimal_places=4)
    metadata: Optional[Dict[str, str]] = None

    @validator("total")
    def validate_total(cls, v: Decimal, values):
        quantity = values.get("quantity")
        unit_price = values.get("unit_price")
        if quantity is not None and unit_price is not None:
            expected = (quantity * unit_price).quantize(Decimal("0.0001"))
            if v < expected:
                raise ValueError("line item total must be >= quantity * unitPrice")
        return v

    class Config:
        allow_population_by_field_name = True


class InvoiceTotalsModel(BaseModel):
    subtotal: condecimal(gt=0, decimal_places=4)
    tax_amount: condecimal(ge=0, decimal_places=4) = Field(..., alias="taxAmount")
    total: condecimal(gt=0, decimal_places=4)
    currency: constr(strip_whitespace=True, min_length=3, max_length=3) = "NGN"

    class Config:
        allow_population_by_field_name = True


class PaymentDetailsModel(BaseModel):
    status: Optional[str] = Field(None, alias="paymentStatus")
    method: Optional[str] = Field(None, alias="paymentMethod")
    due_date: Optional[date] = Field(None, alias="dueDate")

    class Config:
        allow_population_by_field_name = True


class FIRSInvoiceModel(BaseModel):
    invoice_number: constr(strip_whitespace=True, min_length=1, max_length=64) = Field(..., alias="invoiceNumber")
    issue_date: date = Field(..., alias="issueDate")
    due_date: Optional[date] = Field(None, alias="dueDate")
    supplier: SupplierModel
    customer: CustomerModel
    line_items: List[InvoiceLineItemModel] = Field(..., alias="lineItems")
    totals: InvoiceTotalsModel
    payment_details: Optional[PaymentDetailsModel] = Field(None, alias="paymentDetails")
    metadata: Optional[Dict[str, str]] = None
    created_at: Optional[datetime] = None

    @validator("line_items")
    def validate_line_items(cls, v: List[InvoiceLineItemModel]):
        if not v:
            raise ValueError("at least one line item is required")
        return v

    @validator("totals")
    def validate_totals(cls, totals: InvoiceTotalsModel, values):
        line_items: List[InvoiceLineItemModel] = values.get("line_items") or []
        subtotal = sum(item.total for item in line_items)
        if subtotal > totals.subtotal:
            raise ValueError("invoice totals subtotal must be >= sum of line item totals")
        expected_total = (totals.subtotal + totals.tax_amount).quantize(Decimal("0.0001"))
        if expected_total != totals.total.quantize(Decimal("0.0001")):
            raise ValueError("invoice totals do not balance (subtotal + tax != total)")
        return totals

    class Config:
        allow_population_by_field_name = True
        anystr_strip_whitespace = True
        json_encoders = {
            Decimal: lambda v: float(v),
            date: lambda v: v.isoformat(),
        }


__all__ = [
    "FIRSInvoiceModel",
    "SupplierModel",
    "CustomerModel",
    "InvoiceLineItemModel",
    "InvoiceTotalsModel",
    "PaymentDetailsModel",
    "ValidationError",
]
