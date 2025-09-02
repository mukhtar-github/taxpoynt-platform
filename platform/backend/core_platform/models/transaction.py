"""
Core Transaction Models
======================
Central transaction data models used across the TaxPoynt platform.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional
from pydantic import BaseModel


class BankTransaction(BaseModel):
    """Banking transaction data structure."""
    id: str
    account_number: str
    transaction_reference: str
    amount: Decimal
    currency: str = "NGN"
    transaction_date: datetime
    description: str
    transaction_type: str  # "credit" or "debit"
    balance_after: Optional[Decimal] = None
    metadata: Dict[str, Any] = {}
    
    class Config:
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat()
        }
