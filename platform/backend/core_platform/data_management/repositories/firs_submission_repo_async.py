"""
Async Repository: FIRS Submissions
=================================

Targeted migration module that demonstrates async SQLAlchemy usage and
tenant scoping via ContextVar. Reads the current tenant (organization_id)
from tenant context by default.
"""
from __future__ import annotations

from typing import List, Optional, Union, Dict, Any
from copy import deepcopy
import time
from uuid import UUID as UUIDType
import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, desc, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from core_platform.authentication.tenant_context import get_current_tenant
from core_platform.data_management.models.firs_submission import FIRSSubmission
from core_platform.monitoring.prometheus_integration import get_prometheus_integration


async def get_submission_by_id(
    db: AsyncSession,
    *,
    submission_id: Union[UUIDType, str],
    organization_id: Optional[Union[UUIDType, str]] = None,
) -> Optional[FIRSSubmission]:
    """Fetch a single FIRS submission by ID, tenant-scoped.

    If `organization_id` is not provided, uses current tenant from context.
    Returns None on invalid IDs or when not found.
    """
    # Normalize IDs
    sub_id: Optional[UUIDType]
    if isinstance(submission_id, uuid.UUID):
        sub_id = submission_id
    else:
        try:
            sub_id = uuid.UUID(str(submission_id))
        except Exception:
            return None

    org_id: Optional[Union[UUIDType, str]] = organization_id or get_current_tenant()
    if not org_id:
        return None
    if isinstance(org_id, str):
        try:
            org_id = uuid.UUID(org_id)
        except Exception:
            return None

    stmt = (
        select(FIRSSubmission)
        .where(FIRSSubmission.id == sub_id, FIRSSubmission.organization_id == org_id)
        .limit(1)
    )
    start = time.monotonic()
    outcome = "success"
    try:
        res = await db.execute(stmt)
        row = res.scalars().first()
        return row
    except Exception:
        outcome = "error"
        raise
    finally:
        dt = time.monotonic() - start
        integ = get_prometheus_integration()
        if integ:
            integ.record_metric(
                "taxpoynt_repository_queries_total", 1,
                {"repository": "firs_submission", "method": "get_submission_by_id", "table": "firs_submissions", "outcome": outcome}
            )
            integ.record_metric(
                "taxpoynt_repository_query_duration_seconds", dt,
                {"repository": "firs_submission", "method": "get_submission_by_id", "table": "firs_submissions"}
            )

async def list_recent_submissions(
    db: AsyncSession,
    *,
    limit: int = 10,
    offset: int = 0,
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
        .offset(max(0, int(offset)))
        .limit(max(1, int(limit)))
    )
    start = time.monotonic()
    outcome = "success"
    try:
        result = await db.execute(stmt)
        rows = result.scalars().all()
        return rows
    except Exception:
        outcome = "error"
        raise
    finally:
        dt = time.monotonic() - start
        integ = get_prometheus_integration()
        if integ:
            integ.record_metric(
                "taxpoynt_repository_queries_total", 1,
                {"repository": "firs_submission", "method": "list_recent_submissions", "table": "firs_submissions", "outcome": outcome}
            )
            integ.record_metric(
                "taxpoynt_repository_query_duration_seconds", dt,
                {"repository": "firs_submission", "method": "list_recent_submissions", "table": "firs_submissions"}
            )


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

    start = time.monotonic()
    outcome = "success"
    try:
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
    except Exception:
        outcome = "error"
        raise
    finally:
        dt = time.monotonic() - start
        integ = get_prometheus_integration()
        if integ:
            integ.record_metric(
                "taxpoynt_repository_queries_total", 1,
                {"repository": "firs_submission", "method": "get_submission_metrics", "table": "firs_submissions", "outcome": outcome}
            )
            integ.record_metric(
                "taxpoynt_repository_query_duration_seconds", dt,
                {"repository": "firs_submission", "method": "get_submission_metrics", "table": "firs_submissions"}
            )


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


def _to_iso(dt: Optional[datetime]) -> Optional[str]:
    return dt.isoformat() if dt else None


def _serialize_submission(submission: FIRSSubmission) -> Dict[str, Any]:
    """Serialize a submission to a JSON-safe dict."""
    return {
        "id": str(submission.id),
        "invoice_number": submission.invoice_number,
        "irn": submission.irn,
        "status": submission.status.value if submission.status else None,
        "validation_status": submission.validation_status.value if submission.validation_status else None,
        "total_amount": float(submission.total_amount) if submission.total_amount is not None else None,
        "currency": submission.currency,
        "submitted_at": _to_iso(submission.submitted_at),
        "accepted_at": _to_iso(submission.accepted_at),
        "rejected_at": _to_iso(submission.rejected_at),
        "created_at": _to_iso(submission.created_at),
        "updated_at": _to_iso(submission.updated_at),
        "firs_message": submission.firs_message,
        "retry_count": submission.retry_count,
    }


async def get_status_distribution(
    db: AsyncSession,
    *,
    organization_id: Optional[Union[UUIDType, str]] = None,
) -> Dict[str, int]:
    """Return counts per submission status for a tenant."""
    org_id: Optional[Union[UUIDType, str]] = organization_id or get_current_tenant()
    if not org_id:
        return {}
    if isinstance(org_id, str):
        try:
            org_id = uuid.UUID(org_id)
        except Exception:
            return {}

    stmt = (
        select(FIRSSubmission.status, func.count(FIRSSubmission.id))
        .where(FIRSSubmission.organization_id == org_id)
        .group_by(FIRSSubmission.status)
    )
    res = await db.execute(stmt)
    return {
        (status.value if status else "unknown"): int(count)
        for status, count in res.all()
    }


async def get_tracking_overview_data(
    db: AsyncSession,
    *,
    organization_id: Optional[Union[UUIDType, str]] = None,
    recent_limit: int = 5,
    trend_days: int = 7,
) -> Dict[str, Any]:
    """Build tracking overview payload with metrics, recent submissions, and alerts."""
    metrics = await get_submission_metrics(db, organization_id=organization_id)
    distribution = await get_status_distribution(db, organization_id=organization_id)
    recent = await list_recent_submissions(
        db,
        organization_id=organization_id,
        limit=recent_limit,
        offset=0,
    )

    # Trend: daily counts for last N days (newest last)
    org_id: Optional[Union[UUIDType, str]] = organization_id or get_current_tenant()
    trend: List[Dict[str, Any]] = []
    if org_id:
        if isinstance(org_id, str):
            try:
                org_id = uuid.UUID(org_id)
            except Exception:
                org_id = None
        if org_id:
            start_date = datetime.now(timezone.utc).date()
            day_counts: Dict[str, int] = {}
            stmt = (
                select(func.date(FIRSSubmission.created_at), func.count(FIRSSubmission.id))
                .where(
                    FIRSSubmission.organization_id == org_id,
                    FIRSSubmission.created_at >= datetime.now(timezone.utc) - timedelta(days=trend_days - 1),
                )
                .group_by(func.date(FIRSSubmission.created_at))
            )
            res = await db.execute(stmt)
            for date_str, count in res.all():
                day_counts[str(date_str)] = int(count)
            for idx in range(trend_days - 1, -1, -1):
                day = start_date - timedelta(days=idx)
                key = day.isoformat()
                trend.append({"date": key, "total": day_counts.get(key, 0)})

    alerts = await list_tracking_alerts(db, organization_id=organization_id, include_acknowledged=False)

    return {
        "metrics": metrics,
        "status_distribution": distribution,
        "recent_submissions": [_serialize_submission(sub) for sub in recent],
        "alerts": alerts,
        "trend": trend,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


async def list_transmission_statuses_data(
    db: AsyncSession,
    *,
    organization_id: Optional[Union[UUIDType, str]] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """Return transmission status list for dashboards."""
    org_id: Optional[Union[UUIDType, str]] = organization_id or get_current_tenant()
    if not org_id:
        return {"items": [], "count": 0}
    if isinstance(org_id, str):
        try:
            org_id = uuid.UUID(org_id)
        except Exception:
            return {"items": [], "count": 0}

    stmt = select(FIRSSubmission).where(FIRSSubmission.organization_id == org_id)
    if status:
        from core_platform.data_management.models.firs_submission import SubmissionStatus

        try:
            stmt = stmt.where(FIRSSubmission.status == SubmissionStatus[status.upper()])
        except KeyError:
            return {"items": [], "count": 0}

    stmt = stmt.order_by(desc(FIRSSubmission.created_at)).limit(max(1, int(limit)))
    res = await db.execute(stmt)
    rows = res.scalars().all()
    return {
        "items": [_serialize_submission(r) for r in rows],
        "count": len(rows),
    }


async def list_recent_status_changes_data(
    db: AsyncSession,
    *,
    organization_id: Optional[Union[UUIDType, str]] = None,
    hours: int = 24,
    limit: int = 100,
) -> Dict[str, Any]:
    """Return recent status changes ordered by update time."""
    org_id: Optional[Union[UUIDType, str]] = organization_id or get_current_tenant()
    if not org_id:
        return {"items": [], "count": 0}
    if isinstance(org_id, str):
        try:
            org_id = uuid.UUID(org_id)
        except Exception:
            return {"items": [], "count": 0}

    since = datetime.now(timezone.utc) - timedelta(hours=max(1, hours))
    stmt = (
        select(FIRSSubmission)
        .where(
            FIRSSubmission.organization_id == org_id,
            and_(FIRSSubmission.updated_at.is_not(None), FIRSSubmission.updated_at >= since),
        )
        .order_by(desc(FIRSSubmission.updated_at))
        .limit(max(1, int(limit)))
    )
    res = await db.execute(stmt)
    rows = res.scalars().all()
    return {
        "items": [
            {
                **_serialize_submission(row),
                "event": row.status.value if row.status else None,
            }
            for row in rows
        ],
        "count": len(rows),
        "since": since.isoformat(),
    }


def _build_alert_payload(submission: FIRSSubmission, alert_type: str, acknowledged: bool, acknowledged_at: Optional[str], acknowledged_by: Optional[str]) -> Dict[str, Any]:
    severity = "critical" if submission.status and submission.status.value == "failed" else "high"
    return {
        "alert_id": f"{submission.id}:{alert_type}",
        "submission_id": str(submission.id),
        "invoice_number": submission.invoice_number,
        "status": submission.status.value if submission.status else None,
        "severity": severity,
        "message": submission.firs_message or "Submission requires attention",
        "detected_at": _to_iso(submission.updated_at) or _to_iso(submission.created_at),
        "acknowledged": acknowledged,
        "acknowledged_at": acknowledged_at,
        "acknowledged_by": acknowledged_by,
    }


async def list_tracking_alerts(
    db: AsyncSession,
    *,
    organization_id: Optional[Union[UUIDType, str]] = None,
    include_acknowledged: bool = True,
    limit: int = 25,
) -> List[Dict[str, Any]]:
    """Build alert list from failed or rejected submissions."""
    org_id: Optional[Union[UUIDType, str]] = organization_id or get_current_tenant()
    if not org_id:
        return []
    if isinstance(org_id, str):
        try:
            org_id = uuid.UUID(org_id)
        except Exception:
            return []

    from core_platform.data_management.models.firs_submission import SubmissionStatus

    stmt = (
        select(FIRSSubmission)
        .where(
            FIRSSubmission.organization_id == org_id,
            FIRSSubmission.status.in_([SubmissionStatus.REJECTED, SubmissionStatus.FAILED]),
        )
        .order_by(desc(FIRSSubmission.updated_at))
        .limit(max(1, int(limit)))
    )
    res = await db.execute(stmt)
    rows = res.scalars().all()

    alerts: List[Dict[str, Any]] = []
    for row in rows:
        details = row.error_details if isinstance(row.error_details, dict) else {}
        tracking_alerts = details.get("tracking_alerts", {}) if isinstance(details.get("tracking_alerts"), dict) else {}
        for alert_type in ("submission_failed", "submission_rejected"):
            if alert_type == "submission_failed" and row.status == SubmissionStatus.FAILED:
                meta = tracking_alerts.get(alert_type, {})
                acknowledged = bool(meta.get("acknowledged"))
                if not include_acknowledged and acknowledged:
                    continue
                alerts.append(
                    _build_alert_payload(
                        row,
                        alert_type,
                        acknowledged,
                        meta.get("acknowledged_at"),
                        meta.get("acknowledged_by"),
                    )
                )
            if alert_type == "submission_rejected" and row.status == SubmissionStatus.REJECTED:
                meta = tracking_alerts.get(alert_type, {})
                acknowledged = bool(meta.get("acknowledged"))
                if not include_acknowledged and acknowledged:
                    continue
                alerts.append(
                    _build_alert_payload(
                        row,
                        alert_type,
                        acknowledged,
                        meta.get("acknowledged_at"),
                        meta.get("acknowledged_by"),
                    )
                )

    return alerts


async def acknowledge_tracking_alert(
    db: AsyncSession,
    *,
    alert_id: str,
    acknowledged_by: str,
    organization_id: Optional[Union[UUIDType, str]] = None,
) -> Optional[Dict[str, Any]]:
    """Mark a derived tracking alert as acknowledged on the submission record."""
    if not alert_id or ":" not in alert_id:
        return None
    submission_part, alert_type = alert_id.split(":", 1)
    submission = await get_submission_by_id(
        db,
        submission_id=submission_part,
        organization_id=organization_id,
    )
    if not submission:
        return None

    details_raw = submission.error_details if isinstance(submission.error_details, dict) else {}
    details = deepcopy(details_raw)
    tracking_alerts = details.get("tracking_alerts")
    if not isinstance(tracking_alerts, dict):
        tracking_alerts = {}
    alert_entry = dict(tracking_alerts.get(alert_type) or {})
    now_iso = datetime.now(timezone.utc).isoformat()
    alert_entry.update(
        {
            "acknowledged": True,
            "acknowledged_at": now_iso,
            "acknowledged_by": acknowledged_by,
        }
    )
    tracking_alerts[alert_type] = alert_entry
    details["tracking_alerts"] = tracking_alerts
    submission.error_details = details
    db.add(submission)
    await db.commit()
    await db.refresh(submission)

    return _build_alert_payload(
        submission,
        alert_type,
        acknowledged=True,
        acknowledged_at=now_iso,
        acknowledged_by=acknowledged_by,
    )


async def list_firs_responses_data(
    db: AsyncSession,
    *,
    organization_id: Optional[Union[UUIDType, str]] = None,
    status: Optional[str] = None,
    limit: int = 50,
) -> Dict[str, Any]:
    """Return FIRS responses stored on submissions."""
    org_id: Optional[Union[UUIDType, str]] = organization_id or get_current_tenant()
    if not org_id:
        return {"responses": [], "count": 0}
    if isinstance(org_id, str):
        try:
            org_id = uuid.UUID(org_id)
        except Exception:
            return {"responses": [], "count": 0}

    stmt = select(FIRSSubmission).where(
        FIRSSubmission.organization_id == org_id,
        FIRSSubmission.firs_response.is_not(None),
    )

    if status:
        from core_platform.data_management.models.firs_submission import SubmissionStatus

        try:
            stmt = stmt.where(FIRSSubmission.status == SubmissionStatus[status.upper()])
        except KeyError:
            return {"responses": [], "count": 0}

    stmt = stmt.order_by(desc(FIRSSubmission.updated_at)).limit(max(1, int(limit)))
    res = await db.execute(stmt)
    rows = res.scalars().all()

    responses: List[Dict[str, Any]] = []
    for row in rows:
        responses.append(
            {
                **_serialize_submission(row),
                "firs_response": row.firs_response,
                "firs_submission_id": row.firs_submission_id,
                "firs_status_code": row.firs_status_code,
            }
        )

    return {"responses": responses, "count": len(responses)}


async def get_firs_response_detail(
    db: AsyncSession,
    *,
    organization_id: Optional[Union[UUIDType, str]] = None,
    transmission_id: Union[str, UUIDType],
) -> Optional[Dict[str, Any]]:
    """Return detailed FIRS response for a submission."""
    submission = await get_submission_by_id(
        db,
        submission_id=transmission_id,
        organization_id=organization_id,
    )
    if not submission or not submission.firs_response:
        return None

    payload = _serialize_submission(submission)
    payload.update(
        {
            "firs_response": submission.firs_response,
            "firs_submission_id": submission.firs_submission_id,
            "firs_status_code": submission.firs_status_code,
        }
    )
    return payload
