"""
Async repository helpers for validation batch results.
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, Optional, Union
from uuid import UUID as UUIDType, UUID

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core_platform.authentication.tenant_context import get_current_tenant
from core_platform.data_management.models.validation_batch import ValidationBatchResult


def _as_int(value: Any) -> int:
    try:
        if value is None:
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def _normalize_status(value: Any) -> str:
    if value is None:
        return "unknown"
    return str(value).lower() or "unknown"


async def record_validation_batch(
    db: AsyncSession,
    *,
    organization_id: Optional[Union[UUIDType, str]],
    batch_payload: Dict[str, Any],
) -> ValidationBatchResult:
    org_id: Optional[Union[UUIDType, str]] = organization_id or get_current_tenant()
    if not org_id:
        raise ValueError("Organization context is required to persist validation batch")

    if isinstance(org_id, str):
        org_id = UUID(org_id)

    record = ValidationBatchResult(
        organization_id=org_id,
        batch_id=batch_payload.get("batch_id") or batch_payload.get("id") or "unknown",
        validation_id=batch_payload.get("validation_id"),
        total_invoices=_as_int(
            (batch_payload.get("summary", {}) or {}).get("total")
            or batch_payload.get("invoice_count")
            or batch_payload.get("invoiceCount")
        ),
        passed_invoices=_as_int(
            (batch_payload.get("summary", {}) or {}).get("passed")
            or batch_payload.get("passed_count")
            or batch_payload.get("passed")
        ),
        failed_invoices=_as_int(
            (batch_payload.get("summary", {}) or {}).get("failed")
            or batch_payload.get("failed_count")
            or batch_payload.get("failed")
        ),
        status=str(batch_payload.get("status") or "completed"),
        error_summary=(
            batch_payload.get("errors")
            or batch_payload.get("error_summary")
            or batch_payload.get("errorSummary")
        ),
        result_payload=batch_payload,
    )

    db.add(record)
    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    await db.refresh(record)
    return record


async def list_recent_validation_batches(
    db: AsyncSession,
    *,
    organization_id: Optional[Union[UUIDType, str]] = None,
    limit: int = 20,
) -> Dict[str, Any]:
    org_id: Optional[Union[UUIDType, str]] = organization_id or get_current_tenant()
    if not org_id:
        return {"items": [], "count": 0}

    if isinstance(org_id, str):
        try:
            org_id = UUID(org_id)
        except Exception:
            return {"items": [], "count": 0}

    stmt = (
        select(ValidationBatchResult)
        .where(ValidationBatchResult.organization_id == org_id)
        .order_by(desc(ValidationBatchResult.created_at))
        .limit(max(1, int(limit)))
    )

    rows = (await db.execute(stmt)).scalars().all()
    return {
        "items": [
            {
                "batchId": row.batch_id,
                "validationId": row.validation_id,
                "status": row.status,
                "totals": {
                    "total": int(row.total_invoices or 0),
                    "passed": int(row.passed_invoices or 0),
                    "failed": int(row.failed_invoices or 0),
                },
                "createdAt": row.created_at.isoformat() if row.created_at else None,
                "errorSummary": row.error_summary,
                "resultPayload": row.result_payload,
            }
            for row in rows
        ],
        "count": len(rows),
    }


async def summarize_validation_batches(
    db: AsyncSession,
    *,
    organization_id: Optional[Union[UUIDType, str]] = None,
    limit: int = 10,
) -> Dict[str, Any]:
    """Return recent batch history alongside aggregated counts."""

    history = await list_recent_validation_batches(
        db,
        organization_id=organization_id,
        limit=limit,
    )

    items = history.get("items", []) if isinstance(history, dict) else []

    status_counter: Counter[str] = Counter()
    totals = {"total": 0, "passed": 0, "failed": 0}

    for item in items:
        status_counter[_normalize_status(item.get("status"))] += 1
        batch_totals = item.get("totals") or {}
        totals["total"] += _as_int(batch_totals.get("total"))
        totals["passed"] += _as_int(batch_totals.get("passed"))
        totals["failed"] += _as_int(batch_totals.get("failed"))

    summary = {
        "totalBatches": len(items),
        "statusCounts": dict(status_counter),
        "totals": totals,
        "lastRunAt": items[0].get("createdAt") if items else None,
    }

    return {"items": items, "summary": summary}
