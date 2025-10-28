from decimal import Decimal
import pytest

from core_platform.models.transaction import BankTransaction


def test_bank_transaction_validates_currency_uppercase():
    tx = BankTransaction(
        id="tx_123",
        account_number="0123456789",
        amount=Decimal("1500.50"),
        currency="ngn",
        transaction_type="credit",
        transaction_date="2024-05-01T10:00:00Z",
    )
    assert tx.currency == "NGN"


def test_bank_transaction_rejects_invalid_currency():
    with pytest.raises(ValueError):
        BankTransaction(
            id="tx_123",
            account_number="0123456789",
            amount=Decimal("1500.50"),
            currency="NAIRA",
            transaction_type="credit",
            transaction_date="2024-05-01T10:00:00Z",
        )


def test_bank_transaction_rejects_negative_amount():
    with pytest.raises(ValueError):
        BankTransaction(
            id="tx_123",
            account_number="0123456789",
            amount=Decimal("-10"),
            currency="NGN",
            transaction_type="credit",
            transaction_date="2024-05-01T10:00:00Z",
        )


def test_zero_amount_requires_hold_flag():
    with pytest.raises(ValueError):
        BankTransaction(
            id="tx_123",
            account_number="0123456789",
            amount=Decimal("0"),
            currency="NGN",
            transaction_type="credit",
            transaction_date="2024-05-01T10:00:00Z",
        )

    tx = BankTransaction(
        id="tx_124",
        account_number="0123456789",
        amount=Decimal("0"),
        currency="NGN",
        transaction_type="credit",
        transaction_date="2024-05-01T10:00:00Z",
        metadata={"is_hold": True},
    )
    assert tx.metadata["is_hold"] is True


def test_tags_normalised_to_lowercase():
    tx = BankTransaction(
        id="tx_125",
        account_number="0123456789",
        amount=Decimal("200"),
        currency="NGN",
        transaction_type="debit",
        transaction_date="2024-05-01T10:00:00Z",
        tags=["FIRS", "PAYROLL"],
    )
    assert tx.tags == ["firs", "payroll"]
