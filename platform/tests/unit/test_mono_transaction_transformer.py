from decimal import Decimal
import pytest

from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.transformer import (
    MonoTransactionTransformer,
    MonoTransformationError,
)


@pytest.fixture
def transformer():
    return MonoTransactionTransformer()


def base_raw(**overrides):
    raw = {
        "id": "tx-001",
        "amount": 12500,
        "type": "credit",
        "date": "2024-05-01",
        "narration": "POS Purchase",
        "category": "pos",
        "balance": 500000,
    }
    raw.update(overrides)
    return raw


def test_transform_credit_transaction(transformer):
    raw = base_raw()
    tx = transformer.transform(raw, account_number="0123456789", provider_account_id="acc-01")

    assert tx.id == "tx-001"
    assert tx.account_number == "0123456789"
    assert tx.provider_account_id == "acc-01"
    assert tx.transaction_type == "credit"
    assert tx.amount == Decimal("125.00")
    assert tx.balance_after == Decimal("5000.00")
    assert "pos" in tx.tags
    assert tx.metadata["provider"] == "mono"


def test_transform_debit_populates_tags_and_metadata(transformer):
    raw = base_raw(id="tx-100", amount=30000, type="debit", category="transfer")
    tx = transformer.transform(raw, account_number="123", provider_account_id="acc-02")

    assert tx.transaction_type == "debit"
    assert tx.metadata["signed_amount"] == str(Decimal("-300.00"))
    assert set(tx.tags) == {"transfer", "debit"}


def test_transform_handles_reversal_flag(transformer):
    raw = base_raw(status="reversed", meta={"original_transaction_id": "tx-parent"})
    tx = transformer.transform(raw, account_number="789", provider_account_id="acc-03")

    assert tx.is_reversal is True
    assert tx.original_transaction_id == "tx-parent"


def test_transform_zero_amount_requires_hold(transformer):
    raw = base_raw(amount=0, status="pending", meta={"is_hold": True})
    tx = transformer.transform(raw, account_number="456")
    assert tx.metadata["is_hold"] is True

    raw_missing_flag = base_raw(amount=0)
    with pytest.raises(MonoTransformationError):
        transformer.transform(raw_missing_flag, account_number="456")


def test_transform_with_enrichment_hooks():
    transformer = MonoTransactionTransformer(tag_hooks=[lambda payload: [payload.get("category", "")] , lambda _: ["custom"]])
    raw = base_raw(category="Utilities")
    tx = transformer.transform(raw, account_number="111")
    assert set(tx.tags) == {"utilities", "credit", "custom"}


def test_transform_missing_fields_raise_error(transformer):
    raw = {"amount": 1000, "type": "credit", "date": "2024-01-01"}
    with pytest.raises(MonoTransformationError):
        transformer.transform(raw, account_number="123")


def test_transform_invalid_amount_raises_error(transformer):
    raw = base_raw(amount="invalid")
    with pytest.raises(MonoTransformationError):
        transformer.transform(raw, account_number="123")


def test_transform_requires_account_number(transformer):
    raw = base_raw()
    with pytest.raises(MonoTransformationError):
        transformer.transform(raw, account_number="")
