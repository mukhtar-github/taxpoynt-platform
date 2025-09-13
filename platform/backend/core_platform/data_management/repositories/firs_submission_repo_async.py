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


async def list_submissions_filtered(
    db: AsyncSession,
    *,
    organization_id: Optional[Union[UUIDType, str]] = None,
    status: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
) -> List[FIRSSubmission]:
    """List submissions for a tenant with basic filters.

    - status: one of SubmissionStatus names (case-insensitive)
    - start_date, end_date: ISO8601 date (YYYY-MM-DD)
    - limit: max rows
    """
    org_id: Optional[Union[UUIDType, str]] = organization_id or get_current_tenant()
    if not org_id:
        return []
    if isinstance(org_id, str):
        try:
            org_id = uuid.UUID(org_id)
        except Exception:
            return []

    from sqlalchemy import select, func
    from datetime import datetime
    from core_platform.data_management.models.firs_submission import SubmissionStatus

    stmt = select(FIRSSubmission).where(FIRSSubmission.organization_id == org_id)

    if status:
        try:
            st = SubmissionStatus[status.upper()]
            stmt = stmt.where(FIRSSubmission.status == st)
        except KeyError:
            # Unknown status -> return empty
            return []

    # Date filtering on created_at (by date)
    if start_date:
        try:
            stmt = stmt.where(func.date(FIRSSubmission.created_at) >= start_date)
        except Exception:
            pass
    if end_date:
        try:
            stmt = stmt.where(func.date(FIRSSubmission.created_at) <= end_date)
        except Exception:
            pass

    stmt = stmt.order_by(FIRSSubmission.created_at.desc()).limit(max(1, int(limit)))
    res = await db.execute(stmt)
    return res.scalars().all()
