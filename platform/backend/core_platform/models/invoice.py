"""
Core Invoice Models
==================
Central invoice data models used across the TaxPoynt platform.

These models provide a unified structure for invoice data that can be used by:
- Banking integration services
- FIRS formatters
- ERP connectors
- Billing engines
- Compliance validators
"""

import uuid
from datetime import datetime, date
from decimal import Decimal
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, validator


class CustomerInfo(BaseModel):
    """Customer information for invoices."""
    name: str
    tin: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    customer_type: str = "INDIVIDUAL"
    
    @validator('tin')
    def validate_tin(cls, v):
        """Validate TIN format if provided."""
        if v and len(v) < 5:
            raise ValueError("TIN must be at least 5 characters long")
        return v
    
    @validator('customer_type')
    def validate_customer_type(cls, v):
        """Validate customer type."""
        valid_types = ["INDIVIDUAL", "CORPORATE"]
        if v not in valid_types:
            raise ValueError(f"Customer type must be one of: {valid_types}")
        return v


class InvoiceItem(BaseModel):
    """Individual line item in an invoice."""
    id: str = None
    description: str
    quantity: Decimal
    unit_price: Decimal
    total_amount: Decimal
    tax_rate: Decimal = Decimal("0.075")
    tax_amount: Decimal
    currency: str = "NGN"
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.id is None:
            self.id = str(uuid.uuid4())
    
    @validator('quantity')
    def validate_quantity(cls, v):
        """Validate quantity is positive."""
        if v <= 0:
            raise ValueError("Quantity must be greater than zero")
        return v
    
    @validator('unit_price')
    def validate_unit_price(cls, v):
        """Validate unit price is positive."""
        if v <= 0:
            raise ValueError("Unit price must be greater than zero")
        return v
    
    @validator('total_amount')
    def validate_total_amount(cls, v, values):
        """Validate total amount matches quantity * unit_price."""
        if 'quantity' in values and 'unit_price' in values:
            expected_total = values['quantity'] * values['unit_price']
            if abs(v - expected_total) > Decimal('0.01'):
                raise ValueError("Total amount must equal quantity * unit_price")
        return v
    
    @validator('tax_amount')
    def validate_tax_amount(cls, v, values):
        """Validate tax amount matches total_amount * tax_rate."""
        if 'total_amount' in values and 'tax_rate' in values:
            expected_tax = values['total_amount'] * values['tax_rate']
            if abs(v - expected_tax) > Decimal('0.01'):
                raise ValueError("Tax amount must equal total_amount * tax_rate")
        return v


class Invoice(BaseModel):
    """Complete invoice record with all necessary fields."""
    id: str = None
    invoice_number: str
    date: date
    due_date: Optional[date] = None
    
    # Customer and supplier information
    customer_info: Optional[CustomerInfo] = None
    supplier_info: Optional[Dict[str, Any]] = None
    
    # Financial details
    subtotal: Decimal
    vat_amount: Decimal
    total_amount: Decimal
    currency: str = "NGN"
    
    # Line items
    items: List[InvoiceItem] = []
    
    # Metadata
    metadata: Dict[str, Any] = {}
    created_at: datetime = None
    updated_at: datetime = None
    
    def __init__(self, **data):
        super().__init__(**data)
        if self.id is None:
            self.id = str(uuid.uuid4())
        if self.created_at is None:
            self.created_at = datetime.utcnow()
        if self.updated_at is None:
            self.updated_at = datetime.utcnow()
    
    @validator('date')
    def validate_date(cls, v):
        """Validate invoice date is not in the future."""
        if v > date.today():
            raise ValueError("Invoice date cannot be in the future")
        return v
    
    @validator('due_date')
    def validate_due_date(cls, v, values):
        """Validate due date is after invoice date."""
        if v and 'date' in values and v <= values['date']:
            raise ValueError("Due date must be after invoice date")
        return v
    
    @validator('total_amount')
    def validate_total_amount(cls, v, values):
        """Validate total amount matches subtotal + vat_amount."""
        if 'subtotal' in values and 'vat_amount' in values:
            expected_total = values['subtotal'] + values['vat_amount']
            if abs(v - expected_total) > Decimal('0.01'):
                raise ValueError("Total amount must equal subtotal + vat_amount")
        return v
    
    @validator('items')
    def validate_items(cls, v):
        """Validate that invoice has at least one item."""
        if not v:
            raise ValueError("Invoice must have at least one line item")
        return v
    
    def calculate_totals(self) -> Dict[str, Decimal]:
        """Calculate invoice totals from line items."""
        subtotal = sum(item.total_amount for item in self.items)
        vat_amount = sum(item.tax_amount for item in self.items)
        total_amount = subtotal + vat_amount
        
        return {
            "subtotal": subtotal,
            "vat_amount": vat_amount,
            "total_amount": total_amount
        }
    
    def update_totals(self):
        """Update invoice totals based on line items."""
        totals = self.calculate_totals()
        self.subtotal = totals["subtotal"]
        self.vat_amount = totals["vat_amount"]
        self.total_amount = totals["total_amount"]
        self.updated_at = datetime.utcnow()
    
    def add_item(self, item: InvoiceItem):
        """Add a line item to the invoice."""
        self.items.append(item)
        self.update_totals()
    
    def remove_item(self, item_id: str):
        """Remove a line item from the invoice."""
        self.items = [item for item in self.items if item.id != item_id]
        self.update_totals()
    
    def get_item_by_id(self, item_id: str) -> Optional[InvoiceItem]:
        """Get a line item by ID."""
        for item in self.items:
            if item.id == item_id:
                return item
        return None
    
    def is_overdue(self) -> bool:
        """Check if the invoice is overdue."""
        if not self.due_date:
            return False
        return date.today() > self.due_date
    
    def get_days_overdue(self) -> int:
        """Get the number of days the invoice is overdue."""
        if not self.due_date:
            return 0
        overdue_days = (date.today() - self.due_date).days
        return max(0, overdue_days)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert invoice to dictionary representation."""
        return {
            "id": self.id,
            "invoice_number": self.invoice_number,
            "date": self.date.isoformat(),
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "customer_info": self.customer_info.dict() if self.customer_info else None,
            "supplier_info": self.supplier_info,
            "subtotal": str(self.subtotal),
            "vat_amount": str(self.vat_amount),
            "total_amount": str(self.total_amount),
            "currency": self.currency,
            "items": [item.dict() for item in self.items],
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Invoice':
        """Create invoice from dictionary representation."""
        # Convert date strings back to date objects
        if 'date' in data and isinstance(data['date'], str):
            data['date'] = date.fromisoformat(data['date'])
        if 'due_date' in data and data['due_date'] and isinstance(data['due_date'], str):
            data['due_date'] = date.fromisoformat(data['due_date'])
        
        # Convert decimal strings back to Decimal objects
        for field in ['subtotal', 'vat_amount', 'total_amount']:
            if field in data and isinstance(data[field], str):
                data[field] = Decimal(data[field])
        
        # Convert items
        if 'items' in data:
            data['items'] = [InvoiceItem(**item) for item in data['items']]
        
        # Convert customer info
        if 'customer_info' in data and data['customer_info']:
            data['customer_info'] = CustomerInfo(**data['customer_info'])
        
        return cls(**data)


# Convenience functions for common operations
def create_invoice_from_items(
    invoice_number: str,
    items: List[InvoiceItem],
    customer_info: Optional[CustomerInfo] = None,
    invoice_date: Optional[date] = None,
    due_date: Optional[date] = None,
    currency: str = "NGN"
) -> Invoice:
    """Create an invoice from a list of items with automatic total calculation."""
    if not items:
        raise ValueError("Invoice must have at least one line item")
    
    # Calculate totals
    subtotal = sum(item.total_amount for item in items)
    vat_amount = sum(item.tax_amount for item in items)
    total_amount = subtotal + vat_amount
    
    return Invoice(
        invoice_number=invoice_number,
        date=invoice_date or date.today(),
        due_date=due_date,
        customer_info=customer_info,
        subtotal=subtotal,
        vat_amount=vat_amount,
        total_amount=total_amount,
        currency=currency,
        items=items
    )


def validate_invoice_structure(invoice: Invoice) -> List[str]:
    """Validate invoice structure and return list of validation errors."""
    errors = []
    
    if not invoice.invoice_number:
        errors.append("Invoice number is required")
    
    if not invoice.date:
        errors.append("Invoice date is required")
    
    if not invoice.items:
        errors.append("Invoice must have at least one line item")
    
    if invoice.total_amount <= 0:
        errors.append("Invoice total amount must be greater than zero")
    
    if invoice.currency not in ["NGN", "USD", "EUR", "GBP"]:
        errors.append("Unsupported currency")
    
    # Validate line items
    for i, item in enumerate(invoice.items):
        if not item.description:
            errors.append(f"Item {i+1}: Description is required")
        if item.quantity <= 0:
            errors.append(f"Item {i+1}: Quantity must be greater than zero")
        if item.unit_price <= 0:
            errors.append(f"Item {i+1}: Unit price must be greater than zero")
    
    return errors
