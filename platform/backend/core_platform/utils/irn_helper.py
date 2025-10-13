"""
Canonical IRN helper utilities.

Produces the platform's canonical Invoice Reference Number (IRN) using the
FIRS-mandated structure:

    {InvoiceNumber}-{ServiceID}-{YYYYMMDD}

This helper enforces the latest requirements where the SI generates the IRN
locally before forwarding invoices to FIRS for clearance.
"""

from __future__ import annotations

import re
from datetime import date, datetime
from typing import Union

__all__ = ["generate_canonical_irn", "IRNGenerationError"]

_SERVICE_ID_PATTERN = re.compile(r"[^A-Z0-9]")


class IRNGenerationError(ValueError):
    """Raised when canonical IRN generation cannot proceed."""


def generate_canonical_irn(
    invoice_number: str,
    service_id: str,
    issued_on: Union[datetime, date, str],
) -> str:
    """
    Generate the canonical IRN string.

    Args:
        invoice_number: Raw invoice number supplied by upstream systems.
        service_id: Registered FIRS service identifier for the organisation.
        issued_on: Invoice issue date (`datetime`, `date`, or ISO string).

    Returns:
        Canonical IRN string in the form `{InvoiceNumber}-{ServiceID}-{YYYYMMDD}`.

    Raises:
        IRNGenerationError: If any input cannot be normalised.
    """

    normalized_invoice = _normalize_invoice_number(invoice_number)
    normalized_service = _normalize_service_id(service_id)
    issued_date = _normalize_issue_date(issued_on)

    return f"{normalized_invoice}-{normalized_service}-{issued_date.strftime('%Y%m%d')}"


def _normalize_invoice_number(raw: str) -> str:
    if raw is None:
        raise IRNGenerationError("invoice_number is required")

    value = str(raw).strip().upper()
    if value.startswith("INV-"):
        value = value[4:]
    elif value == "INV":
        value = ""

    value = re.sub(r"[^A-Z0-9]", "", value)

    if not value:
        raise IRNGenerationError("invoice_number must contain alphanumeric characters")

    return value[:48]


def _normalize_service_id(raw: str) -> str:
    if raw is None:
        raise IRNGenerationError("service_id is required")

    value = str(raw).strip().upper()
    value = _SERVICE_ID_PATTERN.sub("", value)

    if len(value) != 8:
        raise IRNGenerationError("service_id must be 8 alphanumeric characters")

    return value


def _normalize_issue_date(raw: Union[datetime, date, str]) -> datetime:
    if isinstance(raw, datetime):
        return raw
    if isinstance(raw, date):
        return datetime.combine(raw, datetime.min.time())
    if isinstance(raw, str):
        text = raw.strip()
        if not text:
            raise IRNGenerationError("issued_on cannot be empty")

        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue

        try:
            return datetime.fromisoformat(text.replace("Z", "+00:00"))
        except ValueError as exc:  # pragma: no cover - fallback exception path
            raise IRNGenerationError(f"Unable to parse issued_on value '{raw}'") from exc

    raise IRNGenerationError(f"Unsupported issued_on type: {type(raw)!r}")
