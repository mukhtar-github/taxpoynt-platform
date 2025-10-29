"""Transformation helpers for Mono -> canonical banking transactions."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Callable, Dict, Iterable, List, Optional

from core_platform.models.transaction import BankTransaction, Counterparty, LedgerInfo


class MonoTransformationError(ValueError):
    """Raised when Mono transaction cannot be transformed cleanly."""


class MonoTransactionTransformer:
    """Maps Mono transaction payloads to the canonical banking schema."""

    def __init__(
        self,
        *,
        default_currency: str = "NGN",
        tag_hooks: Optional[Iterable[Callable[[Dict[str, object]], Iterable[str]]]] = None,
    ) -> None:
        self.default_currency = default_currency
        self._tag_hooks = list(tag_hooks or [])

    def transform(
        self,
        raw: Dict[str, object],
        *,
        account_number: str,
        provider_account_id: Optional[str] = None,
        account_currency: Optional[str] = None,
    ) -> BankTransaction:
        payload = dict(raw)
        if not account_number:
            raise MonoTransformationError("Account number required for transformation")
        transaction_id = self._require(payload, "id")
        amount_kobo = self._require(payload, "amount")
        transaction_type = self._require(payload, "type").lower()
        if transaction_type not in {"credit", "debit"}:
            raise MonoTransformationError("Transaction type must be credit or debit")

        amount = self._convert_amount(amount_kobo)
        status = str(payload.get("status", "completed")).lower()
        description = payload.get("description") or payload.get("narration")
        narration = payload.get("narration")
        currency = (payload.get("currency") or account_currency or self.default_currency).upper()

        if amount == 0:
            is_hold = bool(self._meta(payload).get("is_hold") or status == "pending")
            if not is_hold:
                raise MonoTransformationError("Zero-amount transactions must be flagged as holds")
        else:
            is_hold = False

        tags = self._collect_tags(payload, transaction_type)
        metadata = self._build_metadata(payload, amount, transaction_type, is_hold)

        balance_after = self._convert_optional_amount(payload.get("balance"))
        ledger_info = None
        if balance_after is not None:
            ledger_info = LedgerInfo(ledger_balance=balance_after, currency=currency)

        counterparty = self._build_counterparty(payload)
        is_reversal, original_tx = self._detect_reversal(payload)

        transaction_date = self._parse_date(payload.get("date"))
        value_date = self._parse_optional_datetime(payload.get("value_date"))

        return BankTransaction(
            transaction_id=transaction_id,
            account_number=account_number,
            provider_account_id=provider_account_id,
            transaction_reference=payload.get("reference") or transaction_id,
            amount=amount,
            currency=currency,
            transaction_type=transaction_type,
            transaction_date=transaction_date,
            value_date=value_date,
            description=description,
            narration=narration,
            status=status,
            balance_after=balance_after,
            ledger_info=ledger_info,
            counterparty=counterparty,
            tags=tags,
            metadata=metadata,
            is_reversal=is_reversal,
            original_transaction_id=original_tx,
        )

    def _collect_tags(self, payload: Dict[str, object], transaction_type: str) -> List[str]:
        tags: List[str] = []
        category = payload.get("category")
        if isinstance(category, str) and category.strip():
            tags.append(category.strip().lower())
        tags.append(transaction_type)
        for hook in self._tag_hooks:
            try:
                tags.extend(tag.strip().lower() for tag in hook(payload) if tag)
            except Exception:  # pragma: no cover - enrichment failures shouldn't break transformation
                continue
        # Deduplicate while preserving order
        seen = set()
        unique_tags: List[str] = []
        for tag in tags:
            if tag not in seen:
                unique_tags.append(tag)
                seen.add(tag)
        return unique_tags

    def _build_metadata(self, payload: Dict[str, object], amount: Decimal, transaction_type: str, is_hold: bool) -> Dict[str, object]:
        metadata = {
            "provider": "mono",
            "raw_transaction_id": payload.get("id"),
            "raw_category": payload.get("category"),
            "raw_currency": payload.get("currency"),
            "is_hold": is_hold,
            "raw_amount_kobo": payload.get("amount"),
        }
        signed = amount if transaction_type == "credit" else -amount
        metadata["signed_amount"] = str(signed)
        raw_meta = self._meta(payload)
        if raw_meta:
            metadata["mono_meta"] = raw_meta
        return metadata

    @staticmethod
    def _build_counterparty(payload: Dict[str, object]) -> Optional[Counterparty]:
        meta = payload.get("meta") or {}
        counterparty = meta.get("counterparty") if isinstance(meta, dict) else None
        if not isinstance(counterparty, dict):
            return None
        return Counterparty(
            name=counterparty.get("name"),
            account_number=counterparty.get("account_number"),
            bank_name=counterparty.get("bank"),
            metadata={k: v for k, v in counterparty.items() if k not in {"name", "account_number", "bank"}},
        )

    @staticmethod
    def _detect_reversal(payload: Dict[str, object]) -> (bool, Optional[str]):
        meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
        if str(payload.get("status", "")).lower() == "reversed" or meta.get("is_reversal"):
            original = meta.get("original_transaction_id") or meta.get("reversal_reference")
            return True, original
        return False, None

    def _convert_amount(self, amount_kobo: object) -> Decimal:
        try:
            value = Decimal(str(amount_kobo)) / Decimal("100")
        except (InvalidOperation, TypeError) as exc:
            raise MonoTransformationError("Amount must be numeric") from exc
        if value < 0:
            raise MonoTransformationError("Amount must be non-negative")
        return value.quantize(Decimal("0.01"))

    def _convert_optional_amount(self, amount_kobo: object) -> Optional[Decimal]:
        if amount_kobo is None:
            return None
        return self._convert_amount(amount_kobo)

    @staticmethod
    def _meta(payload: Dict[str, object]) -> Dict[str, object]:
        meta = payload.get("meta")
        return meta if isinstance(meta, dict) else {}

    @staticmethod
    def _parse_date(value: object) -> datetime:
        if value is None:
            raise MonoTransformationError("Transaction date missing")
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError as exc:
            raise MonoTransformationError("Invalid transaction date") from exc

    @staticmethod
    def _parse_optional_datetime(value: object) -> Optional[datetime]:
        if value is None:
            return None
        try:
            return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None

    @staticmethod
    def _require(payload: Dict[str, object], key: str) -> object:
        if key not in payload:
            raise MonoTransformationError(f"Mono payload missing required field '{key}'")
        return payload[key]


__all__ = ["MonoTransactionTransformer", "MonoTransformationError"]
