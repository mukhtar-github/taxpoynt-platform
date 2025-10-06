"""
Async Repository: FIRS Submissions
=================================

Targeted migration module that demonstrates async SQLAlchemy usage and
tenant scoping via ContextVar. Reads the current tenant (organization_id)
from tenant context by default.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Union
from copy import deepcopy
import time
from uuid import UUID as UUIDType
import uuid
from datetime import datetime, timedelta, timezone
import json

from sqlalchemy import select, desc, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from core_platform.authentication.tenant_context import get_current_tenant
from core_platform.data_management.models.firs_submission import (
    FIRSSubmission,
    ValidationStatus,
    SubmissionStatus,
)
from core_platform.data_management.repositories.validation_batch_repo_async import (
    list_recent_validation_batches,
)
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


async def _collect_validation_error_counts(
    db: AsyncSession,
    *,
    organization_id: UUIDType,
    limit: int = 200,
) -> Dict[str, int]:
    stmt = (
        select(FIRSSubmission.error_details)
        .where(
            FIRSSubmission.organization_id == organization_id,
            FIRSSubmission.error_details.is_not(None),
        )
        .order_by(desc(FIRSSubmission.updated_at))
        .limit(limit)
    )
    rows = await db.execute(stmt)

    counts = {"schema": 0, "format": 0, "business_rule": 0}
    for (error_details,) in rows.all():
        for error in _normalise_validation_errors(error_details):
            category = _classify_error(error)
            if category in counts:
                counts[category] += 1
    return counts


def _normalise_validation_errors(details: Any) -> List[Dict[str, Any]]:
    if details is None:
        return []

    if isinstance(details, str):
        try:
            parsed = json.loads(details)
        except Exception:
            parsed = {"message": details}
        return _normalise_validation_errors(parsed)

    entries: List[Dict[str, Any]] = []

    if isinstance(details, dict):
        candidate_lists: List[Any] = []
        for key in ("errors", "validation_errors", "issues", "items", "details"):
            value = details.get(key)
            if isinstance(value, list):
                candidate_lists.append(value)
        if not candidate_lists:
            candidate_lists = [[details]]
        for value_list in candidate_lists:
            for item in value_list:
                if isinstance(item, dict):
                    entries.append(item)
                else:
                    entries.append({"message": str(item)})
        return entries

    if isinstance(details, list):
        for item in details:
            if isinstance(item, dict):
                entries.append(item)
            else:
                entries.append({"message": str(item)})
        return entries

    return [{"message": str(details)}]


def _classify_error(error: Dict[str, Any]) -> str:
    category = (error.get("type") or error.get("category") or "").lower()
    message = (error.get("message") or error.get("detail") or "").lower()
    tokens = f"{category} {message}"
    if any(token in tokens for token in ("schema", "structure", "missing field")):
        return "schema"
    if any(token in tokens for token in ("format", "date", "pattern", "regex")):
        return "format"
    if any(token in tokens for token in ("business", "rule", "vat", "tax")):
        return "business_rule"
    return "other"


async def get_validation_error_insights(
    db: AsyncSession,
    *,
    organization_id: Optional[Union[UUIDType, str]] = None,
    error_code: str,
    limit: int = 50,
) -> Dict[str, Any]:
    org_id: Optional[Union[UUIDType, str]] = organization_id or get_current_tenant()
    if org_id and isinstance(org_id, str):
        try:
            org_id = uuid.UUID(org_id)
        except Exception:
            org_id = None

    if not org_id:
        return {"occurrences": 0, "samples": []}

    stmt = (
        select(
            FIRSSubmission.invoice_number,
            FIRSSubmission.error_details,
            FIRSSubmission.validation_status,
            FIRSSubmission.updated_at,
        )
        .where(
            FIRSSubmission.organization_id == org_id,
            FIRSSubmission.error_details.is_not(None),
        )
        .order_by(desc(FIRSSubmission.updated_at))
        .limit(max(1, int(limit)))
    )
    rows = await db.execute(stmt)

    matches: List[Dict[str, Any]] = []
    search_token = error_code.lower()
    for invoice_number, error_details, validation_status, updated_at in rows.all():
        normalized = _normalise_validation_errors(error_details)
        matching_errors = [
            {
                "type": err.get("type") or err.get("category") or "unknown",
                "field": err.get("field"),
                "message": err.get("message") or err.get("detail") or str(err),
                "severity": (err.get("severity") or err.get("level") or "error").lower(),
                "code": err.get("code") or err.get("rule_id") or None,
            }
            for err in normalized
            if search_token
            in (str(err.get("code")) + str(err.get("rule_id")) + str(err.get("field")) + str(err.get("message"))).lower()
        ]
        if not matching_errors:
            continue
        matches.append(
            {
                "invoice": invoice_number,
                "status": validation_status.value if validation_status else None,
                "observedAt": updated_at.isoformat() if updated_at else None,
                "errors": matching_errors,
            }
        )

    return {"occurrences": len(matches), "samples": matches}


async def get_compliance_metrics_data(
    db: AsyncSession,
    *,
    organization_id: Optional[Union[UUIDType, str]] = None,
    overdue_hours: int = 4,
    recent_limit: int = 5,
) -> Dict[str, Any]:
    metrics = await get_submission_metrics(db, organization_id=organization_id)

    org_id: Optional[Union[UUIDType, str]] = organization_id or get_current_tenant()
    if org_id and isinstance(org_id, str):
        try:
            org_id = uuid.UUID(org_id)
        except Exception:
            org_id = None

    overdue_count = 0
    last_accepted: Optional[datetime] = None
    next_deadline: Optional[datetime] = None
    if org_id:
        now = datetime.now(timezone.utc)
        threshold = now - timedelta(hours=max(1, overdue_hours))
        overdue_stmt = (
            select(func.count(FIRSSubmission.id))
            .where(
                FIRSSubmission.organization_id == org_id,
                FIRSSubmission.status.in_(
                    [SubmissionStatus.PENDING, SubmissionStatus.PROCESSING, SubmissionStatus.SUBMITTED]
                ),
                FIRSSubmission.created_at < threshold,
            )
        )
        overdue_count = (await db.execute(overdue_stmt)).scalar_one_or_none() or 0

        last_stmt = (
            select(FIRSSubmission.accepted_at)
            .where(
                FIRSSubmission.organization_id == org_id,
                FIRSSubmission.accepted_at.is_not(None),
            )
            .order_by(desc(FIRSSubmission.accepted_at))
            .limit(1)
        )
        last_accepted = (await db.execute(last_stmt)).scalar_one_or_none()

        pending_stmt = (
            select(FIRSSubmission.created_at)
            .where(
                FIRSSubmission.organization_id == org_id,
                FIRSSubmission.status.in_(
                    [SubmissionStatus.PENDING, SubmissionStatus.PROCESSING, SubmissionStatus.SUBMITTED]
                ),
            )
            .order_by(FIRSSubmission.created_at)
            .limit(1)
        )
        oldest_pending = (await db.execute(pending_stmt)).scalar_one_or_none()
        if oldest_pending:
            next_deadline = oldest_pending + timedelta(hours=max(1, overdue_hours))

    pending_reports = metrics.get("processing", 0) + metrics.get("submitted", 0)

    recent_submissions = await list_recent_submissions(
        db,
        organization_id=org_id,
        limit=recent_limit,
        offset=0,
    )

    report_entries: List[Dict[str, Any]] = []
    for submission in recent_submissions:
        status_value = submission.status.value if submission.status else "unknown"
        status_label = {
            SubmissionStatus.ACCEPTED.value: "approved",
            SubmissionStatus.SUBMITTED.value: "submitted",
            SubmissionStatus.PROCESSING.value: "processing",
            SubmissionStatus.PENDING.value: "pending",
            SubmissionStatus.REJECTED.value: "rejected",
            SubmissionStatus.FAILED.value: "failed",
        }.get(status_value, "pending")

        completion = {
            "approved": 100,
            "submitted": 85,
            "processing": 60,
            "pending": 40,
            "rejected": 40,
            "failed": 30,
        }.get(status_label, 50)

        deadline = None
        if submission.created_at:
            deadline = submission.created_at + timedelta(hours=max(1, overdue_hours))

        report_entries.append(
            {
                "id": str(submission.id),
                "title": f"Invoice {submission.invoice_number}",
                "type": submission.invoice_type.value if submission.invoice_type else "invoice",
                "status": status_label,
                "created": submission.created_at.isoformat() if submission.created_at else None,
                "deadline": deadline.isoformat() if deadline else None,
                "completionPercentage": completion,
            }
        )

    return {
        "metrics": metrics,
        "overdue": overdue_count,
        "pendingReports": pending_reports,
        "lastAcceptedAt": last_accepted.isoformat() if last_accepted else None,
        "nextDeadline": next_deadline.isoformat() if next_deadline else None,
        "reports": report_entries,
        "slaHours": overdue_hours,
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


async def get_validation_metrics_data(
    db: AsyncSession,
    *,
    organization_id: Optional[Union[UUIDType, str]] = None,
    error_sample_limit: int = 200,
) -> Dict[str, Any]:
    """Aggregate validation metrics for the given tenant."""

    org_id: Optional[Union[UUIDType, str]] = organization_id or get_current_tenant()
    if not org_id:
        return {
            "totalValidated": 0,
            "passRate": 0.0,
            "errorRate": 0.0,
            "warningRate": 0.0,
            "schemaErrors": 0,
            "formatErrors": 0,
            "businessRuleErrors": 0,
            "pending": 0,
        }
    if isinstance(org_id, str):
        try:
            org_id = uuid.UUID(org_id)
        except Exception:
            return {
                "totalValidated": 0,
                "passRate": 0.0,
                "errorRate": 0.0,
                "warningRate": 0.0,
                "schemaErrors": 0,
                "formatErrors": 0,
                "businessRuleErrors": 0,
                "pending": 0,
            }

    status_stmt = (
        select(FIRSSubmission.validation_status, func.count(FIRSSubmission.id))
        .where(FIRSSubmission.organization_id == org_id)
        .group_by(FIRSSubmission.validation_status)
    )
    status_results = await db.execute(status_stmt)

    counts: Dict[str, int] = {
        (status.value if status else "unknown"): int(count)
        for status, count in status_results.all()
    }

    total = sum(counts.values())
    pending = counts.get(ValidationStatus.PENDING.value, 0)
    processed = max(total - pending, 0)
    valid_count = counts.get(ValidationStatus.VALID.value, 0)
    invalid_count = counts.get(ValidationStatus.INVALID.value, 0)
    warning_count = counts.get(ValidationStatus.WARNING.value, 0)

    def _ratio(numerator: int) -> float:
        return round((numerator / processed) * 100, 2) if processed else 0.0

    error_counts = await _collect_validation_error_counts(
        db,
        organization_id=org_id,
        limit=error_sample_limit,
    )

    return {
        "totalValidated": total,
        "passRate": _ratio(valid_count),
        "errorRate": _ratio(invalid_count),
        "warningRate": _ratio(warning_count),
        "schemaErrors": error_counts.get("schema", 0),
        "formatErrors": error_counts.get("format", 0),
        "businessRuleErrors": error_counts.get("business_rule", 0),
        "pending": pending,
    }


async def list_recent_validation_results_data(
    db: AsyncSession,
    *,
    organization_id: Optional[Union[UUIDType, str]] = None,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Return recent submissions with validation context."""

    org_id: Optional[Union[UUIDType, str]] = organization_id or get_current_tenant()
    if org_id and isinstance(org_id, str):
        try:
            org_id = uuid.UUID(org_id)
        except Exception:
            org_id = None

    if not org_id:
        return []

    batch_history = await list_recent_validation_batches(
        db,
        organization_id=org_id,
        limit=limit,
    )
    batch_items = (batch_history or {}).get("items", [])
    if batch_items:
        submissions: List[Dict[str, Any]] = []
        for item in batch_items:
            payload = item.get("resultPayload") or {}
            totals = item.get("totals") or {}
            total = int(
                totals.get("total")
                or (payload.get("summary") or {}).get("total")
                or payload.get("invoice_count")
                or payload.get("invoiceCount")
                or 0
            )
            passed = int(
                totals.get("passed")
                or (payload.get("summary") or {}).get("passed")
                or payload.get("passed_count")
                or payload.get("passed")
                or 0
            )
            failed = int(
                totals.get("failed")
                or (payload.get("summary") or {}).get("failed")
                or payload.get("failed_count")
                or payload.get("failed")
                or 0
            )
            raw_status = str(payload.get("status") or item.get("status") or "").lower()

            if failed > 0 or raw_status in {"failed", "error", "errored"}:
                status_value = "failed"
            elif raw_status in {"processing", "queued", "running", "pending"}:
                status_value = "processing"
            elif raw_status in {"warning", "partial", "partial_success"}:
                status_value = "warning"
            elif total and passed >= total and failed == 0:
                status_value = "passed"
            elif total and failed == 0 and passed and passed < total:
                status_value = "warning"
            elif raw_status in {"completed", "success", "passed"} and failed == 0:
                status_value = "passed"
            else:
                status_value = "processing"

            error_source = item.get("errorSummary")
            if not error_source and isinstance(payload, dict):
                error_source = payload.get("errors") or payload.get("error_summary")

            normalized_errors = _normalise_validation_errors(error_source)
            errors = [
                {
                    "type": error.get("type") or error.get("category") or "unknown",
                    "field": error.get("field") or error.get("code") or None,
                    "message": error.get("message") or error.get("detail") or str(error),
                    "severity": (error.get("severity") or error.get("level") or "error").lower(),
                }
                for error in normalized_errors
            ]

            timestamp = item.get("createdAt")
            if not timestamp and isinstance(payload, dict):
                timestamp = (
                    payload.get("completed_at")
                    or payload.get("completedAt")
                    or payload.get("timestamp")
                )

            record_id = item.get("validationId") or item.get("batchId")
            if isinstance(timestamp, datetime):
                timestamp = timestamp.isoformat()

            submissions.append(
                {
                    "id": str(record_id) if record_id else None,
                    "batchId": item.get("batchId"),
                    "invoiceCount": total,
                    "status": status_value,
                    "timestamp": timestamp,
                    "errors": errors,
                    "passedInvoices": passed,
                    "failedInvoices": failed,
                }
            )

        return submissions

    stmt = (
        select(FIRSSubmission)
        .where(FIRSSubmission.organization_id == org_id)
        .order_by(
            desc(FIRSSubmission.updated_at),
            desc(FIRSSubmission.created_at),
        )
        .limit(limit)
    )
    result = await db.execute(stmt)

    submissions: List[Dict[str, Any]] = []
    for submission in result.scalars():
        errors_payload = _normalise_validation_errors(submission.error_details)
        errors = [
            {
                "type": error.get("type") or error.get("category") or "unknown",
                "field": error.get("field") or error.get("code") or None,
                "message": error.get("message") or error.get("detail") or str(error),
                "severity": (error.get("severity") or error.get("level") or "error").lower(),
            }
            for error in errors_payload
        ]

        raw_status = submission.validation_status.value if submission.validation_status else "pending"
        status_value = {
            ValidationStatus.VALID.value: "passed",
            ValidationStatus.INVALID.value: "failed",
            ValidationStatus.WARNING.value: "warning",
            ValidationStatus.PENDING.value: "processing",
        }.get(raw_status, "processing")
        passed = 1 if status_value == "passed" else 0
        failed = 1 if status_value == "failed" else 0

        submissions.append(
            {
                "id": str(submission.id),
                "batchId": submission.request_id or submission.invoice_number,
                "invoiceCount": 1,
                "status": status_value,
                "timestamp": _to_iso(submission.updated_at)
                or _to_iso(submission.created_at),
                "errors": errors,
                "passedInvoices": passed,
                "failedInvoices": failed,
            }
        )

    return submissions


async def get_validation_error_summary(
    db: AsyncSession,
    *,
    organization_id: Optional[Union[UUIDType, str]] = None,
    limit: int = 100,
) -> Dict[str, Any]:
    """Summarize validation errors by category and severity."""

    org_id: Optional[Union[UUIDType, str]] = organization_id or get_current_tenant()
    if org_id and isinstance(org_id, str):
        try:
            org_id = uuid.UUID(org_id)
        except Exception:
            org_id = None

    if not org_id:
        return {"totalErrors": 0, "groupedByType": {}, "severity": {}, "recentSamples": []}

    stmt = (
        select(
            FIRSSubmission.invoice_number,
            FIRSSubmission.error_details,
            FIRSSubmission.validation_status,
            FIRSSubmission.updated_at,
        )
        .where(
            FIRSSubmission.organization_id == org_id,
            FIRSSubmission.error_details.is_not(None),
        )
        .order_by(desc(FIRSSubmission.updated_at))
        .limit(limit)
    )
    rows = await db.execute(stmt)

    grouped_counts = {"schema": 0, "format": 0, "business_rule": 0, "other": 0}
    severity_counts = {"error": 0, "warning": 0}
    samples: List[Dict[str, Any]] = []

    for invoice_number, error_details, validation_status, updated_at in rows.all():
        normalized = _normalise_validation_errors(error_details)
        if not normalized:
            continue

        for error in normalized:
            category = _classify_error(error)
            severity = (error.get("severity") or error.get("level") or "error").lower()
            grouped_counts[category] = grouped_counts.get(category, 0) + 1
            if severity == "warning":
                severity_counts["warning"] += 1
            else:
                severity_counts["error"] += 1

        samples.append(
            {
                "invoice": invoice_number,
                "status": validation_status.value if validation_status else None,
                "errors": [
                    {
                        "type": error.get("type") or error.get("category") or "unknown",
                        "field": error.get("field"),
                        "message": error.get("message") or error.get("detail") or str(error),
                        "severity": (error.get("severity") or error.get("level") or "error").lower(),
                    }
                    for error in normalized
                ],
                "observedAt": updated_at.isoformat() if updated_at else None,
            }
        )

    total_errors = sum(grouped_counts.values())
    return {
        "totalErrors": total_errors,
        "groupedByType": grouped_counts,
        "severity": severity_counts,
        "recentSamples": samples,
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
