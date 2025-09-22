"""
SI Reporting Service (Scaffold)
===============================

Provides simple reporting operations for onboarding and transaction compliance.
"""
from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


class SIReportingService:
    def __init__(self) -> None:
        self.service_name = "SI Reporting Service"

    async def handle_operation(self, operation: str, payload: Dict[str, Any], db=None) -> Dict[str, Any]:
        try:
            if operation == "generate_onboarding_report":
                summary = {"organizations": 0, "completed": 0, "in_progress": 0}
                if db is not None:
                    from sqlalchemy import select
                    from core_platform.data_management.models.organization import Organization
                    org_id: Optional[str] = payload.get("organization_id")
                    stmt = select(Organization)
                    if org_id:
                        try:
                            from uuid import UUID
                            stmt = stmt.where(Organization.id == UUID(org_id))
                        except Exception:
                            # Ignore bad UUID and return empty scoped result
                            stmt = stmt.where(Organization.id == None)  # noqa: E711
                    total = (await db.execute(stmt)).scalars().all()
                    summary["organizations"] = len(total)
                    summary["completed"] = sum(1 for o in total if getattr(o, "firs_app_status", "") == "active")
                    summary["in_progress"] = sum(1 for o in total if getattr(o, "firs_app_status", "") == "pending")
                return {
                    "operation": operation,
                    "success": True,
                    "report": {
                        "type": "onboarding",
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "summary": summary,
                    },
                }

            if operation == "generate_transaction_compliance_report":
                summary = {"total": 0, "compliant": 0, "non_compliant": 0}
                top_errors = []
                metrics: Dict[str, Any] = {}
                if db is not None:
                    from sqlalchemy import select
                    from core_platform.data_management.models.firs_submission import FIRSSubmission, SubmissionStatus
                    from core_platform.data_management.models.organization import Organization
                    from uuid import UUID

                    org_id: Optional[str] = payload.get("organization_id")
                    start_date_str: Optional[str] = payload.get("start_date")
                    end_date_str: Optional[str] = payload.get("end_date")
                    include_metrics: bool = bool(payload.get("include_metrics", True))

                    stmt = select(FIRSSubmission)
                    if org_id:
                        try:
                            stmt = stmt.where(FIRSSubmission.organization_id == UUID(org_id))
                        except Exception:
                            stmt = stmt.where(FIRSSubmission.organization_id == None)  # noqa: E711
                    # Apply date range to created_at if provided
                    if start_date_str:
                        try:
                            start_dt = datetime.fromisoformat(start_date_str)
                            stmt = stmt.where(FIRSSubmission.created_at >= start_dt)
                        except Exception:
                            pass
                    if end_date_str:
                        try:
                            end_dt = datetime.fromisoformat(end_date_str)
                            stmt = stmt.where(FIRSSubmission.created_at <= end_dt)
                        except Exception:
                            pass

                    rows = (await db.execute(stmt)).scalars().all()
                    summary["total"] = len(rows)

                    def _status_value(status_obj: Any) -> str:
                        value = getattr(status_obj, "value", status_obj)
                        return str(value).lower() if value is not None else "unknown"

                    compliant_values = {
                        SubmissionStatus.ACCEPTED.value.lower(),
                        SubmissionStatus.SUBMITTED.value.lower(),
                    }
                    non_compliant_values = {
                        SubmissionStatus.REJECTED.value.lower(),
                        SubmissionStatus.FAILED.value.lower(),
                    }

                    for submission in rows:
                        status_val = _status_value(getattr(submission, "status", None))
                        if status_val in compliant_values:
                            summary["compliant"] += 1
                        elif status_val in non_compliant_values:
                            summary["non_compliant"] += 1
                    # Derive common error messages if any
                    errors = {}
                    for r in rows:
                        msg = (r.firs_message or "").strip()
                        if msg:
                            errors[msg] = errors.get(msg, 0) + 1
                    top_errors = sorted([{ "message": k, "count": v } for k, v in errors.items()], key=lambda x: x["count"], reverse=True)[:5]

                    if include_metrics:
                        # Daily counts by created_at date
                        daily_counts: Dict[str, int] = {}
                        status_histogram: Dict[str, int] = {}
                        invoice_type_histogram: Dict[str, int] = {}
                        currency_histogram: Dict[str, int] = {}
                        for r in rows:
                            d = getattr(r, "created_at", None)
                            if d:
                                day = d.date().isoformat()
                                daily_counts[day] = daily_counts.get(day, 0) + 1
                            st = getattr(r, "status", None)
                            key = _status_value(st)
                            status_histogram[key] = status_histogram.get(key, 0) + 1
                            inv_t = getattr(r, "invoice_type", None)
                            inv_key = inv_t.value if getattr(inv_t, "value", None) else (inv_t or "unknown")
                            invoice_type_histogram[inv_key] = invoice_type_histogram.get(inv_key, 0) + 1
                            curr = (getattr(r, "currency", None) or "unknown").upper()
                            currency_histogram[curr] = currency_histogram.get(curr, 0) + 1
                        metrics = {
                            "daily_counts": daily_counts,
                            "status_histogram": status_histogram,
                            "invoice_type_histogram": invoice_type_histogram,
                            "currency_histogram": currency_histogram,
                        }
                return {
                    "operation": operation,
                    "success": True,
                    "report": {
                        "type": "transaction_compliance",
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "summary": summary,
                        "top_errors": top_errors,
                        "metrics": metrics,
                    },
                }

            raise ValueError(f"Unsupported operation: {operation}")
        except Exception as e:
            logger.error(f"Reporting operation failed: {operation}: {e}")
            return {"operation": operation, "success": False, "error": str(e)}
