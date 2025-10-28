"""
Core Transaction Models
======================
Canonical banking transaction Pydantic models shared across the platform.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, root_validator, validator


class Counterparty(BaseModel):
    """Counterparty information attached to a banking transaction."""

    name: Optional[str] = None
    account_number: Optional[str] = None
    bank_name: Optional[str] = None
    identifier: Optional[str] = Field(None, description="External counterparty identifier (e.g., BVN, TIN).")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LedgerInfo(BaseModel):
    """Ledger balances captured alongside a transaction."""

    available_balance: Optional[Decimal] = None
    ledger_balance: Optional[Decimal] = None
    currency: Optional[str] = Field(None, min_length=3, max_length=3)

    @validator("currency")
    def normalise_currency(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        if len(v.strip()) != 3 or not v.isalpha():
            raise ValueError("Ledger currency must be a 3-letter ISO code.")
        return v.upper()


class BankTransaction(BaseModel):
    """
    Canonical banking transaction payload.

    Attributes mirror the canonical schema consumed by SI onboarding and banking ingestion.
    """

    id: str = Field(..., alias="transaction_id")
    account_number: str = Field(..., min_length=1)
    provider_account_id: Optional[str] = Field(
        None, description="Provider-specific account identifier."
    )
    transaction_reference: Optional[str] = None
    amount: Decimal
    transaction_type: str = Field(..., regex="^(credit|debit)$")
    transaction_date: datetime = Field(..., alias="posted_at")
    value_date: Optional[datetime] = None
    description: Optional[str] = None
    narration: Optional[str] = None
    status: str = Field("completed", description="completed|pending|reversed")
    balance_after: Optional[Decimal] = None
    currency: str = Field("NGN", min_length=3, max_length=3)
    ledger_info: Optional[LedgerInfo] = None
    counterparty: Optional[Counterparty] = None
    tags: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    is_reversal: bool = False
    original_transaction_id: Optional[str] = None

    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            Decimal: lambda v: str(v),
            datetime: lambda v: v.isoformat(),
        }

    @validator("transaction_date", "value_date", pre=True)
    def parse_datetime(cls, v: Any) -> datetime:
        if v is None:
            return None
        if isinstance(v, datetime):
            return v
        try:
            value = str(v).replace("Z", "+00:00")
            return datetime.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("Invalid datetime format.") from exc

    @root_validator
    def validate_sign_convention(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        tx_type = values.get("transaction_type")
        amount = values.get("amount")
        metadata: Dict[str, Any] = values.get("metadata") or {}
        if amount is None:
            raise ValueError("Amount is required.")

        # Allow zero-value holds if explicitly flagged
        if amount == 0 and not metadata.get("is_hold", False):
            raise ValueError("Zero-amount transactions must be flagged as holds (metadata.is_hold=true).")

        if amount == 0:
            return values

        expected_negative = tx_type == "debit"
        signed_value = metadata.get("signed_amount")

        # When upstream passes signed_amount in metadata, enforce consistency.
        if signed_value is not None:
            try:
                signed_decimal = Decimal(signed_value)
            except (InvalidOperation, TypeError) as exc:
                raise ValueError("metadata.signed_amount must be numeric.") from exc
            if expected_negative and signed_decimal > 0:
                raise ValueError("Debit transactions must have negative signed_amount.")
            if not expected_negative and signed_decimal < 0:
                raise ValueError("Credit transactions must have positive signed_amount.")

        try:
            decimal_amount = Decimal(amount)
        except (InvalidOperation, TypeError) as exc:
            raise ValueError("Amount must be a valid decimal.") from exc

        if decimal_amount < 0:
            raise ValueError("Amount must be non-negative; use transaction_type to express direction.")

        values["amount"] = decimal_amount
        return values

    @validator("tags", each_item=True)
    def validate_tags(cls, v: str) -> str:
        if not v or len(v.strip()) == 0:
            raise ValueError("Tags must be non-empty strings.")
        return v.strip().lower()

    @validator("status")
    def validate_status(cls, v: str) -> str:
        allowed = {"completed", "pending", "reversed"}
        status = v.lower()
        if status not in allowed:
            raise ValueError(f"Status must be one of {allowed}.")
        return status

    @validator("currency", pre=True, always=True)
    def normalise_currency(cls, v: Any) -> str:
        currency = str(v or "NGN").strip()
        if len(currency) != 3 or not currency.isalpha():
            raise ValueError("Currency must be a 3-letter ISO code.")
        return currency.upper()
