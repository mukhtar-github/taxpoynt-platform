"""Transmission orchestration for APP message router callbacks.

This module provides a service layer that backs the App Gateway transmission
endpoints using the platform's async repositories and FIRS client helpers.
It replaces the earlier mock replies with database-backed results while
preserving the route-facing contract.
"""

from __future__ import annotations

import logging
import uuid
from contextlib import asynccontextmanager, nullcontext
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Optional
from uuid import UUID

from sqlalchemy import select

from core_platform.authentication.tenant_context import tenant_context
from core_platform.data_management.db_async import get_async_session
from core_platform.data_management.models.firs_submission import (
    FIRSSubmission,
    InvoiceType,
    SubmissionStatus,
)
from core_platform.data_management.repositories import (
    firs_submission_repo_async as firs_repo,
    invoice_repo_async as invoice_repo,
)
from core_platform.messaging.message_router import MessageRouter, ServiceRole
from core_platform.messaging.queue_manager import get_queue_manager
from core_platform.messaging.queue_manager import QueueConfiguration, QueueType, QueueStrategy

from app_services.firs_communication.firs_payload_mapper import build_firs_invoice


InvoiceRecord = invoice_repo.InvoiceRecord


class TransmissionService:
    """Handle APP transmission operations routed through the MessageRouter."""

    _BATCH_STATUSES = {
        SubmissionStatus.PENDING,
        SubmissionStatus.PROCESSING,
    }

    _STATUS_MAP = {
        "submitted": SubmissionStatus.SUBMITTED,
        "submitting": SubmissionStatus.SUBMITTED,
        "accepted": SubmissionStatus.ACCEPTED,
        "acknowledged": SubmissionStatus.ACCEPTED,
        "completed": SubmissionStatus.ACCEPTED,
        "processing": SubmissionStatus.PROCESSING,
        "pending": SubmissionStatus.PENDING,
        "failed": SubmissionStatus.FAILED,
        "rejected": SubmissionStatus.REJECTED,
        "cancelled": SubmissionStatus.CANCELLED,
    }

    def __init__(self, message_router: MessageRouter) -> None:
        self.message_router = message_router
        self.logger = logging.getLogger(__name__)

    async def handle(self, operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        handlers = {
            "get_available_batches": self._handle_get_available_batches,
            "list_transmission_batches": self._handle_list_transmission_batches,
            "get_batch_details": self._handle_get_batch_details,
            "submit_invoice_batches": self._handle_submit_invoice_batches,
            "submit_invoice_file": self._handle_submit_invoice_file,
            "submit_single_batch": self._handle_submit_single_batch,
            "generate_firs_compliant_invoice": self._handle_generate_invoice,
            "generate_invoice_batch": self._handle_generate_invoice_batch,
            "submit_invoice": self._handle_submit_invoice,
            "submit_invoice_batch": self._handle_submit_invoice_batches,
            "get_submission_status": self._handle_get_submission_status,
            "list_submissions": self._handle_list_submissions,
            "cancel_invoice_submission": self._handle_cancel_submission,
            "cancel_transmission": self._handle_cancel_submission,
            "resubmit_invoice": self._handle_resubmit_invoice,
            "retry_transmission": self._handle_retry_transmission,
            "get_invoice": self._handle_get_invoice,
            "get_transmission_history": self._handle_get_transmission_history,
            "get_transmission_details": self._handle_get_transmission_details,
            "generate_transmission_report": self._handle_generate_transmission_report,
            "get_transmission_status": self._handle_get_submission_status,
            "get_transmission_statistics": self._handle_get_transmission_statistics,
            "transmit_batch": self._handle_queue_transmission,
            "transmit_real_time": self._handle_queue_transmission,
        }

        handler = handlers.get(operation)
        if not handler:
            return self._unsupported(operation)

        try:
            data = await handler(payload)
            return self._success(operation, data)
        except Exception as exc:  # pragma: no cover - defensive catch for router path
            self.logger.exception("Transmission operation failed: %s", operation)
            return self._failure(operation, str(exc))

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    @asynccontextmanager
    async def _session_scope(self):
        async for session in get_async_session():
            yield session
            break

    def _resolve_org_id(self, payload: Dict[str, Any]) -> Optional[str]:
        """Best-effort extraction of organization/tenant identifier from payload."""

        def _extract(source: Dict[str, Any]) -> Optional[str]:
            for key in ("organization_id", "organizationId", "org_id", "tenant_id", "tenantId"):
                value = source.get(key)
                if value:
                    return str(value)
            return None

        if not isinstance(payload, dict):
            return None

        direct = _extract(payload)
        if direct:
            return direct

        nested_candidates = (
            payload.get("context"),
            payload.get("metadata"),
            payload.get("invoice_data"),
            payload.get("submission_data"),
            payload.get("batch_submission_data"),
            payload.get("generation_data"),
            payload.get("filters"),
        )
        for candidate in nested_candidates:
            if isinstance(candidate, dict):
                value = _extract(candidate)
                if value:
                    return value

        return None

    def _resolve_invoice_number(self, payload: Any, fallback: Optional[str] = None) -> Optional[str]:
        """Extract invoice identifier from assorted payload shapes."""

        if isinstance(payload, dict):
            for key in ("invoice_id", "invoiceId", "invoice_number", "invoiceNumber", "irn"):
                value = payload.get(key)
                if value:
                    return str(value)

            metadata = payload.get("metadata")
            if isinstance(metadata, dict):
                for key in ("invoice_id", "invoiceNumber", "invoice_number"):
                    value = metadata.get(key)
                    if value:
                        return str(value)

        return fallback

    def _ensure_uuid(self, value: Any) -> Optional[UUID]:
        if not value:
            return None
        try:
            return UUID(str(value))
        except Exception:
            return None

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _iso(self, dt: Optional[datetime]) -> Optional[str]:
        if not dt:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    def _parse_decimal(self, raw: Any) -> Optional[Decimal]:
        if raw is None:
            return None
        try:
            return Decimal(str(raw))
        except (InvalidOperation, ValueError, TypeError):
            return None

    def _map_status(self, status_value: Any, success_hint: Optional[bool] = None) -> SubmissionStatus:
        if isinstance(status_value, SubmissionStatus):
            return status_value
        if isinstance(status_value, str):
            status_key = status_value.lower()
        elif isinstance(status_value, dict):
            status_key = str(status_value.get("status", "")).lower()
        else:
            status_key = ""
        mapped = self._STATUS_MAP.get(status_key)
        if mapped:
            return mapped
        if success_hint is False:
            return SubmissionStatus.FAILED
        if success_hint is True:
            return SubmissionStatus.SUBMITTED
        return SubmissionStatus.PROCESSING

    def _normalize_invoice_payload(self, data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not isinstance(data, dict):
            return None
        if "invoice_data" in data and isinstance(data["invoice_data"], dict):
            return self._normalize_invoice_payload(data["invoice_data"])
        if "firs_invoice" in data and isinstance(data["firs_invoice"], dict):
            return self._normalize_invoice_payload(data["firs_invoice"])
        if "documentMetadata" in data and isinstance(data["documentMetadata"], dict):
            normalized = dict(data)
            metadata = normalized["documentMetadata"]
            invoice_number = metadata.get("invoiceNumber") or metadata.get("invoice_number")
            if invoice_number:
                normalized.setdefault("invoiceNumber", invoice_number)
                normalized.setdefault("invoice_number", invoice_number)
            if metadata.get("invoiceDate"):
                normalized.setdefault("invoice_date", metadata.get("invoiceDate"))
            return normalized
        return data

    def _looks_like_invoice_payload(self, data: Any) -> bool:
        normalized = self._normalize_invoice_payload(data)
        if not isinstance(normalized, dict):
            return False
        indicators = {
            "items",
            "lineItems",
            "totalAmount",
            "total_amount",
            "subtotal",
            "customer",
            "customer_info",
        }
        return any(key in normalized for key in indicators)

    def _combine_invoice_payload(
        self,
        existing: Optional[Dict[str, Any]],
        record: Optional[InvoiceRecord],
    ) -> Optional[Dict[str, Any]]:
        merged: Dict[str, Any] = {}
        if record and isinstance(record.invoice_data, dict):
            merged.update(record.invoice_data)
        if isinstance(existing, dict):
            merged.update(existing)
        return merged or None

    async def _fetch_invoice_record(
        self,
        *,
        organization_id: Optional[str],
        invoice_number: Optional[str],
        submission_id: Optional[str],
        irn: Optional[str],
        correlation_id: Optional[str],
        si_invoice_id: Optional[str],
    ) -> Optional[InvoiceRecord]:
        async with self._session_scope() as session:
            return await invoice_repo.get_invoice_record(
                session,
                organization_id=organization_id,
                invoice_number=invoice_number,
                submission_id=submission_id,
                irn=irn,
                correlation_id=correlation_id,
                si_invoice_id=si_invoice_id,
            )

    def _select_invoice_number(
        self,
        primary: Optional[str],
        fallback: Optional[str],
        record: Optional[InvoiceRecord],
        invoice_payload: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        if primary:
            return primary
        if fallback:
            return fallback
        if record and record.invoice_number:
            return record.invoice_number
        normalized = self._normalize_invoice_payload(invoice_payload or {})
        if isinstance(normalized, dict):
            for key in ("invoiceNumber", "invoice_number", "id", "invoiceId"):
                value = normalized.get(key)
                if value:
                    return str(value)
        return None

    def _select_irn(
        self,
        irn: Optional[str],
        record: Optional[InvoiceRecord],
        invoice_payload: Optional[Dict[str, Any]] = None,
        firs_response: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        if irn:
            return irn
        if record and record.irn:
            return record.irn
        for source in (invoice_payload, firs_response):
            if isinstance(source, dict):
                candidate = source.get("irn") or source.get("IRN")
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()
        return None

    def _serialize_submission(self, submission: FIRSSubmission) -> Dict[str, Any]:
        return {
            "id": str(submission.id),
            "invoiceNumber": submission.invoice_number,
            "invoiceType": submission.invoice_type.value if submission.invoice_type else None,
            "status": submission.status.value,
            "statusDisplay": submission.status.value.replace("_", " ").title(),
            "irn": submission.irn,
            "firsSubmissionId": submission.firs_submission_id,
            "firsStatusCode": submission.firs_status_code,
            "firsMessage": submission.firs_message,
            "totalAmount": float(submission.total_amount) if submission.total_amount is not None else None,
            "currency": submission.currency,
            "retryCount": submission.retry_count,
            "submittedAt": self._iso(submission.submitted_at),
            "acceptedAt": self._iso(submission.accepted_at),
            "rejectedAt": self._iso(submission.rejected_at),
            "createdAt": self._iso(getattr(submission, "created_at", None)),
            "updatedAt": self._iso(getattr(submission, "updated_at", None)),
            "metadata": submission.invoice_data or {},
        }

    def _serialize_batch(self, submission: FIRSSubmission) -> Dict[str, Any]:
        data = self._serialize_submission(submission)
        return {
            "batch_id": data["id"],
            "invoiceNumber": data["invoiceNumber"],
            "status": data["status"],
            "invoiceCount": len(data["metadata"].get("invoices", [])) if isinstance(data["metadata"], dict) else 1,
            "submittedAt": data["submittedAt"],
            "createdAt": data["createdAt"],
        }

    def _build_summary(self, submissions: Iterable[FIRSSubmission]) -> Dict[str, Any]:
        submissions = list(submissions)
        total = len(submissions)
        compliant_set = {SubmissionStatus.ACCEPTED, SubmissionStatus.SUBMITTED}
        non_compliant_set = {SubmissionStatus.REJECTED, SubmissionStatus.FAILED}
        compliant = sum(1 for s in submissions if s.status in compliant_set)
        non_compliant = sum(1 for s in submissions if s.status in non_compliant_set)
        pending = total - compliant - non_compliant
        return {
            "total": total,
            "compliant": compliant,
            "non_compliant": non_compliant,
            "pending": pending,
        }

    def _build_metrics(self, submissions: Iterable[FIRSSubmission]) -> Dict[str, Dict[str, int]]:
        submissions = list(submissions)
        daily: Dict[str, int] = {}
        status_hist: Dict[str, int] = {}
        invoice_hist: Dict[str, int] = {}
        currency_hist: Dict[str, int] = {}
        for sub in submissions:
            created = getattr(sub, "created_at", None)
            if created:
                day = created.date().isoformat()
                daily[day] = daily.get(day, 0) + 1
            status_hist[sub.status.value] = status_hist.get(sub.status.value, 0) + 1
            inv_type = sub.invoice_type.value if sub.invoice_type else "unknown"
            invoice_hist[inv_type] = invoice_hist.get(inv_type, 0) + 1
            currency = (sub.currency or "unknown").upper()
            currency_hist[currency] = currency_hist.get(currency, 0) + 1
        return {
            "daily_counts": daily,
            "status_histogram": status_hist,
            "invoice_type_histogram": invoice_hist,
            "currency_histogram": currency_hist,
        }

    async def _persist_submission(
        self,
        session,
        organization_id: Optional[str],
        invoice_data: Optional[Dict[str, Any]],
        firs_response: Dict[str, Any],
        status_hint: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Optional[FIRSSubmission]:
        org_uuid = self._ensure_uuid(organization_id)
        if org_uuid is None:
            return None

        invoice_data = invoice_data or {}
        if not isinstance(invoice_data, dict):
            invoice_data = {}
        invoice_number = (
            invoice_data.get("invoiceNumber")
            or invoice_data.get("invoice_number")
            or self._make_identifier("INV")
        )
        total_amount = self._parse_decimal(
            invoice_data.get("totalAmount") or invoice_data.get("total_amount")
        )
        currency = (
            invoice_data.get("currency")
            or invoice_data.get("currency_code")
            or invoice_data.get("documentMetadata", {}).get("currencyCode")
            or "NGN"
        ).upper()
        invoice_type_value = invoice_data.get("invoiceType") or invoice_data.get("invoice_type")
        invoice_type_enum = None
        if invoice_type_value:
            try:
                invoice_type_enum = InvoiceType(invoice_type_value)
            except Exception:
                invoice_type_enum = None

        response_data = firs_response.get("data") if isinstance(firs_response, dict) else {}
        response_status = response_data.get("status") if isinstance(response_data, dict) else None
        status_enum = self._map_status(status_hint or response_status, firs_response.get("success"))

        async with session.begin():
            existing_stmt = select(FIRSSubmission).where(
                FIRSSubmission.organization_id == org_uuid,
                FIRSSubmission.invoice_number == invoice_number,
            ).limit(1)
            existing = (await session.execute(existing_stmt)).scalars().first()
            if existing:
                target = existing
            else:
                target = FIRSSubmission(
                    organization_id=org_uuid,
                    invoice_number=invoice_number,
                    invoice_type=invoice_type_enum or InvoiceType.STANDARD_INVOICE,
                )
                session.add(target)

            target.status = status_enum
            target.invoice_type = invoice_type_enum or target.invoice_type
            target.invoice_data = invoice_data
            target.total_amount = total_amount
            target.currency = currency
            target.firs_response = response_data if isinstance(response_data, dict) else {}  # type: ignore[assignment]
            target.firs_submission_id = (
                response_data.get("submission_id")
                or response_data.get("submissionId")
                or target.firs_submission_id
            )
            target.firs_status_code = response_data.get("statusCode") or response_data.get("status_code")
            target.firs_message = response_data.get("message") or firs_response.get("error")
            irn_value = self._select_irn(
                target.irn,
                None,
                invoice_payload=invoice_data,
                firs_response=response_data if isinstance(response_data, dict) else {},
            )
            if irn_value:
                target.irn = irn_value
            now = datetime.now(timezone.utc)
            target.submitted_at = target.submitted_at or now
            if status_enum == SubmissionStatus.ACCEPTED:
                target.accepted_at = now
            if status_enum in {SubmissionStatus.REJECTED, SubmissionStatus.FAILED, SubmissionStatus.CANCELLED}:
                target.rejected_at = now
            if request_id:
                target.request_id = request_id

        await session.refresh(target)
        return target

    async def _update_submission_status(
        self,
        submission_id: Optional[str],
        organization_id: Optional[str],
        new_status: SubmissionStatus,
        message: Optional[str] = None,
        *,
        invoice_number: Optional[str] = None,
    ) -> Optional[FIRSSubmission]:
        async with self._session_scope() as session:
            org_uuid = self._ensure_uuid(organization_id)
            tenant_id = str(org_uuid) if org_uuid else (
                organization_id if isinstance(organization_id, str) else None
            )

            with tenant_context(tenant_id) if tenant_id else nullcontext():
                submission: Optional[FIRSSubmission] = None

                sub_uuid = self._ensure_uuid(submission_id)
                if sub_uuid is not None:
                    submission = await firs_repo.get_submission_by_id(
                        session,
                        submission_id=sub_uuid,
                        organization_id=org_uuid,
                    )

                if submission is None and invoice_number:
                    submission = await self._get_submission_by_invoice(
                        session,
                        invoice_number=invoice_number,
                        organization_id=org_uuid,
                    )

                if submission is None:
                    return None

                async with session.begin():
                    submission.status = new_status
                    if new_status == SubmissionStatus.CANCELLED:
                        submission.rejected_at = datetime.now(timezone.utc)
                    if message:
                        submission.firs_message = message

                await session.refresh(submission)
                return submission

    async def _get_submission_by_invoice(
        self,
        session,
        *,
        invoice_number: str,
        organization_id: Optional[UUID],
    ) -> Optional[FIRSSubmission]:
        if not invoice_number:
            return None

        stmt = select(FIRSSubmission).where(
            FIRSSubmission.invoice_number == str(invoice_number)
        ).limit(1)

        if organization_id is not None:
            stmt = stmt.where(FIRSSubmission.organization_id == organization_id)

        result = await session.execute(stmt)
        return result.scalars().first()

    async def _list_submissions(
        self,
        payload: Dict[str, Any],
        *,
        status: Optional[str] = None,
        limit: int = 50,
        page: int = 1,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[FIRSSubmission]:
        organization_id = self._resolve_org_id(payload)

        filters = payload.get("filters") if isinstance(payload.get("filters"), dict) else {}

        status_value = status or filters.get("status") or filters.get("submissionStatus")
        status_filter = status_value.upper() if isinstance(status_value, str) else status_value

        start_date = (
            start_date
            or filters.get("start_date")
            or filters.get("startDate")
            or filters.get("from")
        )
        end_date = (
            end_date
            or filters.get("end_date")
            or filters.get("endDate")
            or filters.get("to")
        )

        async with self._session_scope() as session:
            with tenant_context(organization_id) if organization_id else nullcontext():
                rows = await firs_repo.list_submissions_filtered(
                    session,
                    organization_id=organization_id,
                    status=status_filter,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit * max(page, 1),
                )
        offset = max(page - 1, 0) * limit
        return rows[offset : offset + limit]

    # ------------------------------------------------------------------
    # Operation handlers
    # ------------------------------------------------------------------

    async def _handle_get_available_batches(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        limit = int(payload.get("limit", 20))
        submissions = await self._list_submissions(payload, limit=limit)
        batches = [s for s in submissions if s.status in self._BATCH_STATUSES]
        return {
            "batches": [self._serialize_batch(s) for s in batches],
            "total": len(batches),
            "generated_at": self._now_iso(),
        }

    async def _handle_list_transmission_batches(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        limit = int(payload.get("limit", 50))
        filters = payload.get("filters") if isinstance(payload.get("filters"), dict) else {}
        status = payload.get("status") or filters.get("status")
        submissions = await self._list_submissions(payload, status=status, limit=limit)
        return {
            "batches": [self._serialize_batch(s) for s in submissions],
            "meta": {
                "limit": limit,
                "count": len(submissions),
                "generated_at": self._now_iso(),
            },
        }

    async def _handle_get_batch_details(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        batch_id = payload.get("batch_id") or payload.get("transmission_id")
        organization_id = self._resolve_org_id(payload)
        async with self._session_scope() as session:
            with tenant_context(organization_id) if organization_id else nullcontext():
                submission = await firs_repo.get_submission_by_id(
                    session, submission_id=batch_id, organization_id=organization_id
                )
        if not submission:
            return {"batch_id": batch_id, "found": False, "checked_at": self._now_iso()}
        return {
            "batch_id": batch_id,
            "details": self._serialize_submission(submission),
            "checked_at": self._now_iso(),
        }

    async def _handle_submit_invoice_batches(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        batch_submission = payload.get("batch_submission_data")
        invoices = payload.get("invoices") or payload.get("batch_data") or []

        if isinstance(batch_submission, dict):
            invoices = batch_submission.get("invoices") or batch_submission.get("items") or invoices

        if isinstance(invoices, dict) and "invoices" in invoices:
            invoices = invoices["invoices"]

        if not isinstance(invoices, list):
            invoices = [invoices] if invoices else []

        organization_id = self._resolve_org_id(payload) or self._resolve_org_id(batch_submission or {})

        resolved_invoices: List[Dict[str, Any]] = []
        references: List[Dict[str, Any]] = []

        for entry in invoices:
            if self._looks_like_invoice_payload(entry):
                normalized = self._normalize_invoice_payload(entry) or {}
                resolved_invoices.append(dict(normalized))
            else:
                ref_dict: Dict[str, Any]
                if isinstance(entry, dict):
                    ref_dict = dict(entry)
                elif isinstance(entry, str):
                    ref_dict = {"invoice_number": entry}
                else:
                    ref_dict = {}
                references.append(ref_dict)

        if references:
            async with self._session_scope() as session:
                for ref in references:
                    invoice_number = self._select_invoice_number(
                        ref.get("invoice_number")
                        or ref.get("invoiceNumber")
                        or ref.get("invoice_id")
                        or ref.get("invoiceId"),
                        None,
                        None,
                        ref,
                    )
                    record = await invoice_repo.get_invoice_record(
                        session,
                        organization_id=organization_id,
                        invoice_number=invoice_number,
                        submission_id=ref.get("submission_id") or ref.get("transmission_id"),
                        irn=ref.get("irn"),
                        correlation_id=ref.get("correlation_id"),
                        si_invoice_id=ref.get("si_invoice_id"),
                    )
                    if not record or not record.invoice_data:
                        identifier = invoice_number or ref.get("submission_id") or ref.get("irn") or "invoice_reference_missing"
                        raise ValueError(f"invoice_payload_unavailable:{identifier}")
                    invoice_payload = dict(record.invoice_data)
                    if record.irn and "irn" not in invoice_payload:
                        invoice_payload.setdefault("irn", record.irn)
                    resolved_invoices.append(invoice_payload)

        if not resolved_invoices:
            raise ValueError("invoice_payload_unavailable")

        request_id = payload.get("request_id")
        resolved_invoices = [build_firs_invoice(inv) for inv in resolved_invoices]

        firs_payload: Dict[str, Any] = {
            "invoices": resolved_invoices,
            "organization_id": organization_id,
        }
        if isinstance(batch_submission, dict):
            firs_payload["metadata"] = batch_submission

        firs_response = await self._call_firs("submit_invoice_batch_to_firs", firs_payload)

        persisted_ids: List[str] = []
        async with self._session_scope() as session:
            with tenant_context(organization_id) if organization_id else nullcontext():
                for invoice in resolved_invoices:
                    submission = await self._persist_submission(
                        session,
                        organization_id,
                        invoice,
                        firs_response,
                        status_hint="submitted",
                        request_id=request_id,
                    )
                    if submission:
                        persisted_ids.append(str(submission.id))

        try:
            delivery = payload.get("delivery") or {}
            await self._enqueue_outbound_delivery(organization_id, resolved_invoices, delivery)
        except Exception:
            self.logger.debug("Outbound delivery enqueue skipped")

        return {
            "submitted_at": self._now_iso(),
            "firs_response": firs_response,
            "persisted_submissions": persisted_ids,
        }

    async def _handle_submit_invoice_file(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "processing",
            "transmission_id": self._make_identifier("TX"),
            "file_name": payload.get("file_name"),
            "received_at": self._now_iso(),
        }

    async def _handle_submit_single_batch(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized_payload = dict(payload)
        submission_config = normalized_payload.get("submission_config") or {}
        if "batch_submission_data" not in normalized_payload:
            normalized_payload["batch_submission_data"] = submission_config
        if "invoices" not in normalized_payload and isinstance(submission_config, dict):
            normalized_payload["invoices"] = submission_config.get("invoices") or submission_config.get("items")
        return await self._handle_submit_invoice_batches(normalized_payload)

    async def _handle_generate_invoice(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        generation_data = payload.get("generation_data", {})
        invoice_data = generation_data.get("invoice_data", {})
        invoice_id = invoice_data.get("invoiceNumber") or self._make_identifier("INV")
        return {
            "invoice_id": invoice_id,
            "validated": True,
            "generated_at": self._now_iso(),
            "source": generation_data.get("source", "app"),
        }

    async def _handle_generate_invoice_batch(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        batch_data = payload.get("batch_generation_data", {})
        invoices = batch_data.get("invoices", [])
        return {
            "batch_id": self._make_identifier("BATCH"),
            "invoice_count": len(invoices),
            "created_at": self._now_iso(),
            "metadata": {
                "priority": batch_data.get("priority", "normal"),
                "auto_validate": batch_data.get("auto_validate", True),
            },
        }

    async def _handle_submit_invoice(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raw_submission = payload.get("submission_data")
        submission_data = raw_submission if isinstance(raw_submission, dict) else {}

        invoice_payload = self._normalize_invoice_payload(payload.get("invoice_data"))
        organization_id = self._resolve_org_id(payload) or self._resolve_org_id(submission_data)
        invoice_number_primary = self._resolve_invoice_number(payload)
        invoice_number_fallback = self._resolve_invoice_number(submission_data)
        submission_identifier = (
            payload.get("submission_id")
            or payload.get("transmission_id")
            or submission_data.get("submission_id")
        )
        irn_candidate = payload.get("irn") or submission_data.get("irn")

        record = None
        if not self._looks_like_invoice_payload(invoice_payload):
            record = await self._fetch_invoice_record(
                organization_id=organization_id,
                invoice_number=invoice_number_primary or invoice_number_fallback,
                submission_id=submission_identifier,
                irn=irn_candidate,
                correlation_id=payload.get("correlation_id") or submission_data.get("correlation_id"),
                si_invoice_id=payload.get("si_invoice_id") or submission_data.get("si_invoice_id"),
            )
            invoice_payload = self._combine_invoice_payload(invoice_payload, record)

        if not invoice_payload:
            raise ValueError("invoice_payload_unavailable")

        invoice_number = self._select_invoice_number(
            invoice_number_primary,
            invoice_number_fallback,
            record,
            invoice_payload,
        )
        irn_value = self._select_irn(irn_candidate, record, invoice_payload=invoice_payload)
        if irn_value and "irn" not in invoice_payload:
            invoice_payload = dict(invoice_payload)
            invoice_payload.setdefault("irn", irn_value)

        request_id = payload.get("request_id")
        original_invoice = dict(invoice_payload)
        invoice_payload = build_firs_invoice(original_invoice)

        firs_payload = {
            "invoice_data": invoice_payload,
            "invoice_number": invoice_number,
            "organization_id": organization_id,
        }
        if irn_value:
            firs_payload["irn"] = irn_value

        firs_response = await self._call_firs("submit_invoice_to_firs", firs_payload)

        submission = None
        async with self._session_scope() as session:
            with tenant_context(organization_id) if organization_id else nullcontext():
                submission = await self._persist_submission(
                    session,
                    organization_id,
                    invoice_payload,
                    firs_response,
                    status_hint="submitted",
                    request_id=request_id,
                )

        try:
            delivery = payload.get("delivery") or submission_data.get("delivery") or {}
            await self._enqueue_outbound_delivery(organization_id, [invoice_payload], delivery)
        except Exception:
            self.logger.debug("Outbound delivery enqueue skipped")

        return {
            "submission_id": str(submission.id) if submission else self._make_identifier("SUB"),
            "submitted_at": self._now_iso(),
            "firs_response": firs_response,
            "submission": self._serialize_submission(submission) if submission else None,
        }

    async def _enqueue_outbound_delivery(
        self,
        organization_id: Optional[str],
        invoices: List[Dict[str, Any]],
        delivery: Dict[str, Any],
    ) -> None:
        """Enqueue outbound delivery messages when buyer AP delivery is requested.

        Expects optional delivery config with keys like:
          - participant_identifier (buyer)
          - endpoint_url (direct override)
          - headers/meta (optional)
        """
        if not isinstance(delivery, dict) or not invoices:
            return

        # Allow disabling auto delivery via env or flag
        import os
        auto_enabled = str(os.getenv("OUTBOUND_AUTO_DELIVER", "true")).lower() in ("1", "true", "yes", "on")

        participant_identifier = delivery.get("participant_identifier") or delivery.get("identifier")
        endpoint_url = delivery.get("endpoint_url") or delivery.get("ap_endpoint_url")
        if not participant_identifier and not endpoint_url and not auto_enabled:
            return

        qm = get_queue_manager()
        await qm.initialize()

        # Prepare one message per invoice to keep retries independent
        for inv in invoices:
            # Auto-infer identifier if not provided explicitly
            identifier = participant_identifier or (self._extract_buyer_identifier(inv) if auto_enabled else None)
            # Skip if neither explicit endpoint nor identifier available
            if not endpoint_url and not identifier:
                continue

            payload = {
                "organization_id": organization_id,
                "identifier": identifier,
                "endpoint_url": endpoint_url,
                "document": inv,
                "metadata": delivery.get("metadata") or {},
            }
            await qm.enqueue_message("ap_outbound", payload)

    def _extract_buyer_identifier(self, invoice: Dict[str, Any]) -> Optional[str]:
        """Best-effort extraction of buyer participant identifier (e.g., TIN) from invoice payload.

        Tries common keys in both our normalized and UBL-like structures.
        """
        if not isinstance(invoice, dict):
            return None
        # Common shapes
        for path in (
            ("customer", "tax_id"),
            ("customer", "tin"),
            ("buyer", "tax_id"),
            ("buyer", "tin"),
            ("buyer", "party_tax_id"),
        ):
            cur = invoice
            for key in path:
                if not isinstance(cur, dict) or key not in cur:
                    cur = None
                    break
                cur = cur.get(key)
            if isinstance(cur, str) and cur.strip():
                return cur.strip()
        # UBL-like: accounting_customer_party.party.party_tax_scheme.company_id
        try:
            acp = invoice.get("accounting_customer_party") or {}
            party = acp.get("party") or {}
            tax_scheme = party.get("party_tax_scheme") or {}
            cid = tax_scheme.get("company_id")
            if isinstance(cid, str) and cid.strip():
                return cid.strip()
        except Exception:
            pass
        # Other camelCase variants
        for key in ("customerTaxId", "customerTIN", "buyerTaxId", "buyerTIN"):
            val = invoice.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
        return None

    async def _handle_get_submission_status(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        submission_id = payload.get("submission_id") or payload.get("transmission_id")
        invoice_identifier = (
            payload.get("invoice_id")
            or payload.get("invoiceNumber")
            or payload.get("irn")
        )
        organization_id = self._resolve_org_id(payload)
        db_submission = None
        async with self._session_scope() as session:
            org_uuid = self._ensure_uuid(organization_id)
            tenant_id = str(org_uuid) if org_uuid else (
                organization_id if isinstance(organization_id, str) else None
            )
            with tenant_context(tenant_id) if tenant_id else nullcontext():
                sub_uuid = self._ensure_uuid(submission_id)
                if sub_uuid is not None:
                    db_submission = await firs_repo.get_submission_by_id(
                        session,
                        submission_id=sub_uuid,
                        organization_id=org_uuid,
                    )
                if db_submission is None and invoice_identifier:
                    db_submission = await self._get_submission_by_invoice(
                        session,
                        invoice_number=invoice_identifier,
                        organization_id=org_uuid,
                    )
                if db_submission is None and payload.get("irn"):
                    stmt = select(FIRSSubmission).where(
                        FIRSSubmission.irn == payload["irn"]
                    ).limit(1)
                    db_submission = (await session.execute(stmt)).scalars().first()
        if db_submission:
            return {
                "submission_id": str(db_submission.id),
                "status": db_submission.status.value,
                "details": self._serialize_submission(db_submission),
                "checked_at": self._now_iso(),
            }
        firs_response = await self._call_firs(
            "get_firs_submission_status",
            {"submission_id": submission_id, "irn": payload.get("irn")},
        )
        return {
            "submission_id": submission_id,
            "status_checked_at": self._now_iso(),
            "firs_response": firs_response,
        }

    async def _handle_list_submissions(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pagination = payload.get("pagination") if isinstance(payload.get("pagination"), dict) else {}

        raw_limit = payload.get("limit") or pagination.get("limit")
        limit = int(raw_limit or 50)

        raw_page = payload.get("page") or pagination.get("page")
        if raw_page is None and payload.get("offset") is not None:
            try:
                offset_val = int(payload.get("offset", 0))
            except (TypeError, ValueError):
                offset_val = 0
            page = (max(offset_val, 0) // max(limit, 1)) + 1
        else:
            page = int(raw_page or 1)

        submissions = await self._list_submissions(payload, limit=limit, page=page)
        return {
            "items": [self._serialize_submission(s) for s in submissions],
            "count": len(submissions),
            "page": page,
            "limit": limit,
            "generated_at": self._now_iso(),
        }

    async def _handle_cancel_submission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        submission_id = (
            payload.get("submission_id")
            or payload.get("transmission_id")
            or payload.get("invoice_id")
        )
        organization_id = self._resolve_org_id(payload)
        invoice_number = self._resolve_invoice_number(payload, fallback=submission_id)
        reason = payload.get("reason") or payload.get("cancellation_reason")

        firs_response = None
        if submission_id or invoice_number:
            firs_response = await self._call_firs(
                "update_firs_submission_status",
                {
                    "submission_id": submission_id,
                    "invoice_number": invoice_number,
                    "status": "cancelled",
                    "reason": reason,
                },
            )

        updated = await self._update_submission_status(
            submission_id,
            organization_id,
            SubmissionStatus.CANCELLED,
            reason,
            invoice_number=invoice_number,
        )
        return {
            "submission_id": submission_id,
            "cancelled_at": self._now_iso(),
            "submission": self._serialize_submission(updated) if updated else None,
            "firs_response": firs_response,
        }

    async def _handle_resubmit_invoice(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raw_resubmission = payload.get("resubmission_data")
        resubmission_data = raw_resubmission if isinstance(raw_resubmission, dict) else {}

        submission_id = (
            payload.get("submission_id")
            or payload.get("transmission_id")
            or payload.get("invoice_id")
            or resubmission_data.get("submission_id")
        )
        invoice_number = self._resolve_invoice_number(resubmission_data, fallback=self._resolve_invoice_number(payload))
        organization_id = self._resolve_org_id(payload) or self._resolve_org_id(resubmission_data)

        invoice_payload = self._normalize_invoice_payload(resubmission_data.get("invoice_data"))
        irn_value = payload.get("irn") or resubmission_data.get("irn")

        record = None
        if not self._looks_like_invoice_payload(invoice_payload) or not irn_value:
            record = await self._fetch_invoice_record(
                organization_id=organization_id,
                invoice_number=invoice_number,
                submission_id=submission_id,
                irn=irn_value,
                correlation_id=payload.get("correlation_id") or resubmission_data.get("correlation_id"),
                si_invoice_id=payload.get("si_invoice_id") or resubmission_data.get("si_invoice_id"),
            )
            invoice_payload = self._combine_invoice_payload(invoice_payload, record)
            irn_value = self._select_irn(irn_value, record, invoice_payload=invoice_payload)

        if not irn_value:
            raise ValueError("irn_required_for_resubmission")

        invoice_payload = dict(invoice_payload) if isinstance(invoice_payload, dict) else {}

        firs_payload = {
            "irn": irn_value,
            "invoice_data": invoice_payload,
            "organization_id": organization_id,
            "options": resubmission_data.get("options") if isinstance(resubmission_data, dict) else None,
        }

        firs_response = await self._call_firs("transmit_firs_invoice", firs_payload)

        updated = await self._update_submission_status(
            submission_id,
            organization_id,
            SubmissionStatus.PROCESSING,
            firs_response.get("error"),
            invoice_number=invoice_number or submission_id,
        )
        return {
            "submission_id": submission_id,
            "resubmitted_at": self._now_iso(),
            "firs_response": firs_response,
            "submission": self._serialize_submission(updated) if updated else None,
        }

    async def _handle_retry_transmission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        submission_id = (
            payload.get("submission_id")
            or payload.get("transmission_id")
            or payload.get("invoice_id")
        )
        invoice_number = self._resolve_invoice_number(payload, fallback=submission_id)

        firs_response = None
        if submission_id or invoice_number:
            firs_response = await self._call_firs(
                "update_firs_submission_status",
                {
                    "submission_id": submission_id,
                    "invoice_number": invoice_number,
                    "status": "processing",
                },
            )

        updated = await self._update_submission_status(
            submission_id,
            self._resolve_org_id(payload),
            SubmissionStatus.PROCESSING,
            invoice_number=invoice_number,
        )
        return {
            "submission_id": submission_id,
            "retry": True,
            "submission": self._serialize_submission(updated) if updated else None,
            "firs_response": firs_response,
        }

    async def _handle_get_invoice(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        submission_id = payload.get("submission_id")
        invoice_identifier = (
            payload.get("invoice_id")
            or payload.get("invoiceNumber")
            or payload.get("irn")
        )
        organization_id = self._resolve_org_id(payload)
        async with self._session_scope() as session:
            org_uuid = self._ensure_uuid(organization_id)
            tenant_id = str(org_uuid) if org_uuid else (
                organization_id if isinstance(organization_id, str) else None
            )
            with tenant_context(tenant_id) if tenant_id else nullcontext():
                submission = None
                sub_uuid = self._ensure_uuid(submission_id)
                if sub_uuid is not None:
                    submission = await firs_repo.get_submission_by_id(
                        session,
                        submission_id=sub_uuid,
                        organization_id=org_uuid,
                    )
                if submission is None and invoice_identifier:
                    submission = await self._get_submission_by_invoice(
                        session,
                        invoice_number=invoice_identifier,
                        organization_id=org_uuid,
                    )
        return {
            "invoice_id": invoice_identifier or submission_id,
            "submission": self._serialize_submission(submission) if submission else None,
        }

    async def _handle_get_transmission_history(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        limit = int(payload.get("limit", 25))
        page = int(payload.get("page", 1))
        date_range = payload.get("date_range") if isinstance(payload.get("date_range"), dict) else {}
        submissions = await self._list_submissions(
            payload,
            limit=limit,
            page=page,
            status=payload.get("status"),
            start_date=date_range.get("start"),
            end_date=date_range.get("end"),
        )
        summary = self._build_summary(submissions)
        return {
            "items": [self._serialize_submission(s) for s in submissions],
            "page": page,
            "limit": limit,
            "total": summary["total"],
            "generated_at": self._now_iso(),
        }

    async def _handle_get_transmission_details(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        transmission_id = payload.get("transmission_id") or payload.get("submission_id")
        invoice_identifier = (
            payload.get("invoice_id")
            or payload.get("invoiceNumber")
            or payload.get("irn")
        )
        organization_id = self._resolve_org_id(payload)
        async with self._session_scope() as session:
            org_uuid = self._ensure_uuid(organization_id)
            tenant_id = str(org_uuid) if org_uuid else (
                organization_id if isinstance(organization_id, str) else None
            )
            with tenant_context(tenant_id) if tenant_id else nullcontext():
                submission = None
                sub_uuid = self._ensure_uuid(transmission_id)
                if sub_uuid is not None:
                    submission = await firs_repo.get_submission_by_id(
                        session,
                        submission_id=sub_uuid,
                        organization_id=org_uuid,
                    )
                if submission is None and invoice_identifier:
                    submission = await self._get_submission_by_invoice(
                        session,
                        invoice_number=invoice_identifier,
                        organization_id=org_uuid,
                    )
        resolved_identifier = transmission_id or invoice_identifier
        if not submission:
            return {"transmission_id": resolved_identifier, "found": False}
        return {
            "transmission_id": resolved_identifier,
            "details": self._serialize_submission(submission),
        }

    async def _handle_generate_transmission_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        limit = int(payload.get("limit", 100))
        submissions = await self._list_submissions(
            payload,
            limit=limit,
            status=payload.get("status"),
            start_date=payload.get("start_date"),
            end_date=payload.get("end_date"),
        )
        summary = self._build_summary(submissions)
        metrics = self._build_metrics(submissions)
        return {
            "generated_at": self._now_iso(),
            "summary": summary,
            "metrics": metrics,
            "records": [self._serialize_submission(s) for s in submissions],
        }

    async def _handle_get_transmission_statistics(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        organization_id = self._resolve_org_id(payload)
        async with self._session_scope() as session:
            with tenant_context(organization_id) if organization_id else nullcontext():
                metrics = await firs_repo.get_submission_metrics(
                    session, organization_id=organization_id
                )
        return {"statistics": metrics, "generated_at": self._now_iso()}

    async def _handle_queue_transmission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "queued_operation": payload.get("operation") or payload.get("action"),
            "queued_at": self._now_iso(),
            "status": "queued",
        }

    # ------------------------------------------------------------------
    # Messaging helpers
    # ------------------------------------------------------------------

    async def _call_firs(self, operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation=operation,
                payload=payload or {},
                source_service="transmission_service",
            )
        except Exception as exc:  # pragma: no cover - defensive fallback
            self.logger.warning("FIRS call failed: %s", exc)
            return {"operation": operation, "success": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # Common response helpers
    # ------------------------------------------------------------------

    def _success(self, operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"operation": operation, "success": True, "data": data}

    def _failure(self, operation: str, error: str) -> Dict[str, Any]:
        return {"operation": operation, "success": False, "error": error}

    def _unsupported(self, operation: str) -> Dict[str, Any]:
        return {"operation": operation, "success": False, "error": "unsupported_operation"}

    def _make_identifier(self, prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:12]}"


__all__ = ["TransmissionService"]
