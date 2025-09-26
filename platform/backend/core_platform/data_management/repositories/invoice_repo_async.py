"""Async helpers for retrieving invoice payloads for submissions.

Provides a lightweight repository to resolve invoice data from either the
FIRS submission table or the SI ↔ APP correlation records. This is used by
the APP transmission service to pull full invoice payloads when only an
invoice identifier is supplied upstream (e.g. invoice number, submission ID,
correlation ID).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence
from uuid import UUID
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core_platform.data_management.models.firs_submission import FIRSSubmission
from core_platform.data_management.models.si_app_correlation import (
    SIAPPCorrelation,
)


@dataclass
class InvoiceRecord:
    """Resolved invoice payload and related identifiers."""

    invoice_data: Dict[str, Any]
    invoice_number: Optional[str] = None
    submission_id: Optional[str] = None
    organization_id: Optional[str] = None
    irn: Optional[str] = None
    si_invoice_id: Optional[str] = None
    correlation_id: Optional[str] = None
    source: str = "unknown"


def _coerce_uuid(value: Optional[str | UUID]) -> Optional[UUID]:
    if value in (None, "", 0):
        return None
    if isinstance(value, UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except Exception:
        return None


async def get_invoice_record(
    session: AsyncSession,
    *,
    organization_id: Optional[str | UUID] = None,
    invoice_number: Optional[str] = None,
    submission_id: Optional[str | UUID] = None,
    irn: Optional[str] = None,
    correlation_id: Optional[str] = None,
    si_invoice_id: Optional[str] = None,
) -> Optional[InvoiceRecord]:
    """Fetch invoice payload using the available identifiers."""

    org_uuid = _coerce_uuid(organization_id)
    submission_uuid = _coerce_uuid(submission_id)

    # Prefer direct submission lookups
    submission = await _find_submission(
        session,
        organization_id=org_uuid,
        submission_id=submission_uuid,
        invoice_number=invoice_number,
        irn=irn,
    )
    if submission:
        return _record_from_submission(submission)

    # Fallback to correlation tracking
    correlation = await _find_correlation(
        session,
        organization_id=org_uuid,
        correlation_id=correlation_id,
        invoice_number=invoice_number,
        irn=irn,
        si_invoice_id=si_invoice_id,
    )
    if correlation:
        return _record_from_correlation(correlation)

    return None


async def get_invoice_records_by_numbers(
    session: AsyncSession,
    *,
    organization_id: Optional[str | UUID],
    invoice_numbers: Sequence[str],
) -> Dict[str, InvoiceRecord]:
    """Batch fetch invoice records keyed by invoice number."""

    results: Dict[str, InvoiceRecord] = {}
    if not invoice_numbers:
        return results

    org_uuid = _coerce_uuid(organization_id)

    stmt = select(FIRSSubmission).where(
        FIRSSubmission.invoice_number.in_(list(set(invoice_numbers)))
    )
    if org_uuid:
        stmt = stmt.where(FIRSSubmission.organization_id == org_uuid)
    submissions = (await session.execute(stmt)).scalars().all()
    for submission in submissions:
        record = _record_from_submission(submission)
        if record.invoice_number:
            results[record.invoice_number] = record

    missing = [num for num in invoice_numbers if num not in results]
    if not missing:
        return results

    stmt = select(SIAPPCorrelation).where(
        SIAPPCorrelation.invoice_number.in_(missing)
    )
    if org_uuid:
        stmt = stmt.where(SIAPPCorrelation.organization_id == org_uuid)
    correlations = (await session.execute(stmt)).scalars().all()
    for correlation in correlations:
        record = _record_from_correlation(correlation)
        if record.invoice_number and record.invoice_number not in results:
            results[record.invoice_number] = record

    return results


async def _find_submission(
    session: AsyncSession,
    *,
    organization_id: Optional[UUID],
    submission_id: Optional[UUID],
    invoice_number: Optional[str],
    irn: Optional[str],
) -> Optional[FIRSSubmission]:
    if submission_id:
        stmt = select(FIRSSubmission).where(FIRSSubmission.id == submission_id)
        if organization_id:
            stmt = stmt.where(FIRSSubmission.organization_id == organization_id)
        submission = (await session.execute(stmt)).scalars().first()
        if submission:
            return submission

    if invoice_number:
        stmt = select(FIRSSubmission).where(FIRSSubmission.invoice_number == invoice_number)
        if organization_id:
            stmt = stmt.where(FIRSSubmission.organization_id == organization_id)
        submission = (await session.execute(stmt)).scalars().first()
        if submission:
            return submission

    if irn:
        stmt = select(FIRSSubmission).where(FIRSSubmission.irn == irn)
        if organization_id:
            stmt = stmt.where(FIRSSubmission.organization_id == organization_id)
        submission = (await session.execute(stmt)).scalars().first()
        if submission:
            return submission

    return None


async def _find_correlation(
    session: AsyncSession,
    *,
    organization_id: Optional[UUID],
    correlation_id: Optional[str],
    invoice_number: Optional[str],
    irn: Optional[str],
    si_invoice_id: Optional[str],
) -> Optional[SIAPPCorrelation]:
    stmt = select(SIAPPCorrelation)
    filters = []
    if organization_id:
        filters.append(SIAPPCorrelation.organization_id == organization_id)
    if correlation_id:
        filters.append(SIAPPCorrelation.correlation_id == correlation_id)
    if invoice_number:
        filters.append(SIAPPCorrelation.invoice_number == invoice_number)
    if irn:
        filters.append(SIAPPCorrelation.irn == irn)
    if si_invoice_id:
        filters.append(SIAPPCorrelation.si_invoice_id == si_invoice_id)

    if not filters:
        return None

    for condition in filters:
        stmt = stmt.where(condition)

    return (await session.execute(stmt.limit(1))).scalars().first()


def _record_from_submission(submission: FIRSSubmission) -> InvoiceRecord:
    invoice_data = submission.invoice_data or {}
    if not isinstance(invoice_data, dict):
        invoice_data = {}

    irn = submission.irn
    if not irn:
        irn = _extract_irn(invoice_data) or _extract_irn(submission.firs_response)

    return InvoiceRecord(
        invoice_data=invoice_data,
        invoice_number=submission.invoice_number,
        submission_id=str(submission.id),
        organization_id=str(submission.organization_id) if submission.organization_id else None,
        irn=irn,
        source="firs_submission",
    )


def _record_from_correlation(correlation: SIAPPCorrelation) -> InvoiceRecord:
    invoice_data = correlation.invoice_data or {}
    if not isinstance(invoice_data, dict):
        invoice_data = {}

    if "irn" not in invoice_data and correlation.irn:
        invoice_data = dict(invoice_data)
        invoice_data.setdefault("irn", correlation.irn)

    return InvoiceRecord(
        invoice_data=invoice_data,
        invoice_number=correlation.invoice_number,
        submission_id=correlation.app_submission_id,
        organization_id=str(correlation.organization_id) if correlation.organization_id else None,
        irn=correlation.irn,
        si_invoice_id=correlation.si_invoice_id,
        correlation_id=correlation.correlation_id,
        source="si_correlation",
    )


def _extract_irn(data: Any) -> Optional[str]:
    if not isinstance(data, dict):
        return None
    for key in ("irn", "IRN", "invoiceReferenceNumber"):
        value = data.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


__all__ = ["InvoiceRecord", "get_invoice_record", "get_invoice_records_by_numbers"]

