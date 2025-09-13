"""
Async Repository: FIRS Submissions
=================================

Targeted migration module that demonstrates async SQLAlchemy usage and
tenant scoping via ContextVar. Reads the current tenant (organization_id)
from tenant context by default.
"""
from __future__ import annotations

from typing import List, Optional, Union, Dict, Any
from uuid import UUID as UUIDType
import uuid

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from core_platform.authentication.tenant_context import get_current_tenant
from core_platform.data_management.models.firs_submission import FIRSSubmission


async def list_recent_submissions(
    db: AsyncSession,
    *,
    limit: int = 10,
    organization_id: Optional[Union[UUIDType, str]] = None,
) -> List[FIRSSubmission]:
    """Return recent FIRS submissions for the current tenant (organization).

    If `organization_id` is not provided, uses the tenant context value.
    If neither is available, returns an empty list.
    """
    org_id: Optional[Union[UUIDType, str]] = organization_id or get_current_tenant()
    if not org_id:
        return []

    # Normalize to UUID object if provided as string
    if isinstance(org_id, str):
        try:
            org_id = uuid.UUID(org_id)
        except Exception:
            # If it cannot be parsed, return empty to avoid mismatched filter
            return []

    stmt = (
        select(FIRSSubmission)
        .where(FIRSSubmission.organization_id == org_id)
        .order_by(desc(FIRSSubmission.created_at))
        .limit(max(1, int(limit)))
    )
    result = await db.execute(stmt)
    rows = result.scalars().all()
    return rows


async def get_submission_metrics(
    db: AsyncSession,
    *,
    organization_id: Optional[Union[UUIDType, str]] = None,
) -> Dict[str, Any]:
    """Compute basic submission metrics for a tenant (organization).

    Returns keys compatible with the APP tracking metrics shape.
    - totalTransmissions
    - processing (PENDING, PROCESSING)
    - completed (ACCEPTED)
    - failed (REJECTED, FAILED)
    - submitted (SUBMITTED)
    - averageProcessingTime (minutes, if computable)
    - successRate (accepted / total * 100)
    - todayTransmissions (created today, UTC)
    """
    org_id: Optional[Union[UUIDType, str]] = organization_id or get_current_tenant()
    if not org_id:
        return {
            "totalTransmissions": 0,
            "processing": 0,
            "completed": 0,
            "failed": 0,
            "submitted": 0,
            "averageProcessingTime": None,
            "successRate": 0.0,
            "todayTransmissions": 0,
        }

    if isinstance(org_id, str):
        try:
            org_id = uuid.UUID(org_id)
        except Exception:
            return {
                "totalTransmissions": 0,
                "processing": 0,
                "completed": 0,
                "failed": 0,
                "submitted": 0,
                "averageProcessingTime": None,
                "successRate": 0.0,
                "todayTransmissions": 0,
            }

    from sqlalchemy import select, func
    from datetime import datetime, timezone
    from core_platform.data_management.models.firs_submission import SubmissionStatus, FIRSSubmission

    # Totals by status
    status_stmt = (
        select(FIRSSubmission.status, func.count(FIRSSubmission.id))
        .where(FIRSSubmission.organization_id == org_id)
        .group_by(FIRSSubmission.status)
    )
    res = await db.execute(status_stmt)
    by_status = {row[0]: row[1] for row in res.all()}

    total = sum(by_status.values())
    processing = sum(by_status.get(s, 0) for s in (SubmissionStatus.PENDING, SubmissionStatus.PROCESSING))
    completed = by_status.get(SubmissionStatus.ACCEPTED, 0)
    failed = sum(by_status.get(s, 0) for s in (SubmissionStatus.REJECTED, SubmissionStatus.FAILED))
    submitted = by_status.get(SubmissionStatus.SUBMITTED, 0)

    # Today transmissions (UTC, created_at date)
    today = datetime.now(timezone.utc).date()
    today_stmt = (
        select(func.count(FIRSSubmission.id))
        .where(
            FIRSSubmission.organization_id == org_id,
            func.date(FIRSSubmission.created_at) == today.isoformat(),
        )
    )
    today_count = (await db.execute(today_stmt)).scalar_one_or_none() or 0

    # Average processing time over accepted submissions (in minutes)
    time_stmt = (
        select(FIRSSubmission.submitted_at, FIRSSubmission.accepted_at)
        .where(
            FIRSSubmission.organization_id == org_id,
            FIRSSubmission.accepted_at.isnot(None),
            FIRSSubmission.submitted_at.isnot(None),
        )
    )
    times = (await db.execute(time_stmt)).all()
    avg_minutes = None
    if times:
        deltas = [
            (acc - sub).total_seconds() / 60.0
            for (sub, acc) in times
            if acc and sub and acc > sub
        ]
        if deltas:
            avg_minutes = round(sum(deltas) / len(deltas), 2)

    success_rate = round((completed / total) * 100.0, 2) if total else 0.0

    return {
        "totalTransmissions": int(total),
        "processing": int(processing),
        "completed": int(completed),
        "failed": int(failed),
        "submitted": int(submitted),
        "averageProcessingTime": f"{avg_minutes} minutes" if avg_minutes is not None else None,
        "successRate": success_rate,
        "todayTransmissions": int(today_count),
    }
