"""Transmission orchestration for APP message router callbacks.

This module provides a light-weight service layer that backs the App Gateway
transmission endpoints. It bridges the high-level operations (batch listings,
status queries, submission orchestration) with the existing reporting mocks
and FIRS communication callbacks so that every routed operation has a concrete
handler. Once the full persistence layer is ready we can swap the helper
functions to use real repositories without changing the gateway contract.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from core_platform.messaging.message_router import MessageRouter, ServiceRole

from app_services.reporting.transmission_reports import (
    ReportConfig,
    ReportFormat,
    TransmissionRecord,
    TransmissionReportGenerator,
)


class TransmissionService:
    """Handle APP transmission operations routed through the MessageRouter."""

    def __init__(
        self,
        message_router: MessageRouter,
        report_generator: Optional[TransmissionReportGenerator] = None,
    ) -> None:
        self.message_router = message_router
        self.report_generator = report_generator or TransmissionReportGenerator()

    async def handle(self, operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch a transmission operation to the corresponding handler."""
        handlers = {
            "get_available_batches": self._handle_get_available_batches,
            "list_transmission_batches": self._handle_get_available_batches,
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
            "resubmit_invoice": self._handle_resubmit_invoice,
            "get_invoice": self._handle_get_invoice,
            "get_transmission_history": self._handle_get_transmission_history,
            "get_transmission_details": self._handle_get_transmission_details,
            "generate_transmission_report": self._handle_generate_transmission_report,
            "get_transmission_status": self._handle_get_submission_status,
            "retry_transmission": self._handle_retry_transmission,
            "cancel_transmission": self._handle_cancel_submission,
            "get_transmission_statistics": self._handle_get_transmission_statistics,
            "transmit_batch": self._handle_queue_transmission,
            "transmit_real_time": self._handle_queue_transmission,
        }

        handler = handlers.get(operation)
        if not handler:
            return self._unsupported(operation)

        try:
            data = await handler(operation, payload)
            return self._success(operation, data)
        except Exception as exc:  # pragma: no cover - defensive catch for router path
            return self._failure(operation, str(exc))

    async def _handle_get_available_batches(
        self, operation: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        limit = int(payload.get("limit", 20))
        records = await self._sample_records(limit=limit)
        batches = [self._record_to_batch(record) for record in records]
        return {
            "batches": batches,
            "total": len(batches),
            "generated_at": self._now_iso(),
        }

    async def _handle_get_batch_details(
        self, operation: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        batch_id = payload.get("batch_id") or payload.get("transmission_id")
        if not batch_id:
            raise ValueError("batch_id is required")

        record = await self._find_record(batch_id)
        if not record:
            return {
                "batch_id": batch_id,
                "found": False,
                "checked_at": self._now_iso(),
            }

        return {
            "batch_id": batch_id,
            "details": self._record_to_detail(record),
            "checked_at": self._now_iso(),
        }

    async def _handle_submit_invoice_batches(
        self, operation: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        batch_payload = {
            "batch_data": payload.get("batch_generation_data")
            or payload.get("batch_data")
            or payload.get("invoices")
            or payload.get("batch_ids"),
            "submission_config": payload.get("submission_config"),
        }
        firs_response = await self._call_firs("submit_invoice_batch_to_firs", batch_payload)
        return {
            "transmission_id": self._make_identifier("TX"),
            "submitted_at": self._now_iso(),
            "firs_response": firs_response,
        }

    async def _handle_submit_invoice_file(
        self, operation: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "transmission_id": self._make_identifier("TX"),
            "status": "processing",
            "file_name": payload.get("file_name"),
            "file_size": payload.get("file_size"),
            "received_at": self._now_iso(),
        }

    async def _handle_submit_single_batch(
        self, operation: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        batch_id = payload.get("batch_id")
        firs_response = await self._call_firs(
            "submit_invoice_batch_to_firs", {"batch_data": [payload.get("submission_config")], "batch_id": batch_id}
        )
        return {
            "batch_id": batch_id,
            "submitted_at": self._now_iso(),
            "firs_response": firs_response,
        }

    async def _handle_generate_invoice(
        self, operation: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        generation_data = payload.get("generation_data", {})
        invoice_data = generation_data.get("invoice_data", {})
        invoice_id = invoice_data.get("invoiceNumber") or self._make_identifier("INV")
        return {
            "invoice_id": invoice_id,
            "validated": True,
            "generated_at": self._now_iso(),
            "source": generation_data.get("source", "app"),
        }

    async def _handle_generate_invoice_batch(
        self, operation: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
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

    async def _handle_submit_invoice(
        self, operation: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        firs_response = await self._call_firs(
            "submit_invoice_to_firs", {"invoice_data": payload.get("invoice_data")}
        )
        return {
            "submission_id": self._make_identifier("SUB"),
            "submitted_at": self._now_iso(),
            "firs_response": firs_response,
        }

    async def _handle_get_submission_status(
        self, operation: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        submission_id = payload.get("submission_id") or payload.get("transmission_id") or payload.get("irn")
        firs_response = await self._call_firs(
            "get_firs_submission_status", {"submission_id": submission_id, "irn": payload.get("irn")}
        )
        return {
            "submission_id": submission_id,
            "status_checked_at": self._now_iso(),
            "firs_response": firs_response,
        }

    async def _handle_list_submissions(
        self, operation: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        limit = int(payload.get("limit", 20))
        records = await self._sample_records(limit=limit)
        submissions = [self._record_to_history(record) for record in records]
        return {
            "items": submissions,
            "count": len(submissions),
            "generated_at": self._now_iso(),
        }

    async def _handle_cancel_submission(
        self, operation: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        submission_id = (
            payload.get("submission_id")
            or payload.get("transmission_id")
            or payload.get("batch_id")
        )
        return {
            "submission_id": submission_id,
            "status": "cancelled",
            "cancelled_at": self._now_iso(),
        }

    async def _handle_resubmit_invoice(
        self, operation: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        submission_id = payload.get("submission_id")
        firs_response = await self._call_firs(
            "transmit_firs_invoice", {"irn": payload.get("irn"), "submission_id": submission_id}
        )
        return {
            "submission_id": submission_id,
            "resubmitted_at": self._now_iso(),
            "firs_response": firs_response,
        }

    async def _handle_get_invoice(
        self, operation: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        invoice_id = payload.get("invoice_id")
        record = await self._find_record(invoice_id, search_invoice=True)
        if not record:
            return {
                "invoice_id": invoice_id,
                "found": False,
                "checked_at": self._now_iso(),
            }
        return {
            "invoice_id": invoice_id,
            "data": {
                "transmission": self._record_to_history(record),
                "status": record.status.value,
            },
        }

    async def _handle_get_transmission_history(
        self, operation: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        page = max(int(payload.get("page", 1)), 1)
        limit = max(int(payload.get("limit", 10)), 1)
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=30)
        records = await self.report_generator.data_provider.get_transmissions(start, end)
        total = len(records)
        start_idx = (page - 1) * limit
        page_records = records[start_idx : start_idx + limit]
        items = [self._record_to_history(record) for record in page_records]
        return {
            "items": items,
            "page": page,
            "limit": limit,
            "total": total,
            "generated_at": self._now_iso(),
        }

    async def _handle_get_transmission_details(
        self, operation: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        transmission_id = payload.get("transmission_id")
        if not transmission_id:
            raise ValueError("transmission_id is required")
        record = await self._find_record(transmission_id)
        if not record:
            return {
                "transmission_id": transmission_id,
                "found": False,
                "checked_at": self._now_iso(),
            }
        return {
            "transmission_id": transmission_id,
            "details": self._record_to_detail(record),
        }

    async def _handle_generate_transmission_report(
        self, operation: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        days = max(int(payload.get("days", 30)), 1)
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=days)
        config = ReportConfig(
            start_date=start,
            end_date=end,
            format=ReportFormat.JSON,
            include_details=True,
            include_charts=False,
            limit=payload.get("limit"),
        )
        report = await self.report_generator.generate_report(config)
        return {
            "report": report,
            "generated_at": self._now_iso(),
        }

    async def _handle_retry_transmission(
        self, operation: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        transmission_id = payload.get("transmission_id")
        firs_response = await self._call_firs(
            "transmit_firs_invoice", {"irn": payload.get("irn"), "submission_id": transmission_id}
        )
        return {
            "transmission_id": transmission_id,
            "retried_at": self._now_iso(),
            "firs_response": firs_response,
        }

    async def _handle_get_transmission_statistics(
        self, operation: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        config = ReportConfig(
            start_date=datetime.now(timezone.utc) - timedelta(days=30),
            end_date=datetime.now(timezone.utc),
            format=ReportFormat.JSON,
            include_details=False,
            include_charts=False,
        )
        report = await self.report_generator.generate_report(config)
        summary = report.get("report_data", {}).get("summary")
        return {
            "summary": summary,
            "generated_at": self._now_iso(),
        }

    async def _handle_queue_transmission(
        self, operation: str, payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        return {
            "queued_operation": operation,
            "queued_at": self._now_iso(),
            "status": "queued",
        }

    # Helpers -----------------------------------------------------------------
    async def _sample_records(self, limit: int = 20) -> List[TransmissionRecord]:
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=30)
        records = await self.report_generator.data_provider.get_transmissions(start, end)
        return records[:limit]

    async def _find_record(
        self, identifier: Optional[str], search_invoice: bool = False
    ) -> Optional[TransmissionRecord]:
        if not identifier:
            return None
        end = datetime.now(timezone.utc)
        start = end - timedelta(days=30)
        records = await self.report_generator.data_provider.get_transmissions(start, end)
        for record in records:
            if search_invoice:
                if record.invoice_number == identifier or record.irn == identifier:
                    return record
            else:
                if record.transmission_id == identifier:
                    return record
        return None

    async def _call_firs(self, operation: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not self.message_router:
            return None
        try:
            return await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation=operation,
                payload=payload or {},
                source_service="transmission_service",
            )
        except Exception as exc:  # pragma: no cover - defensive path when FIRS mock offline
            return {"operation": operation, "success": False, "error": str(exc)}

    @staticmethod
    def _record_to_batch(record: TransmissionRecord) -> Dict[str, Any]:
        return {
            "id": record.transmission_id,
            "name": f"Transmission {record.transmission_id}",
            "invoiceCount": 1,
            "totalAmount": record.payload_size_bytes,
            "status": record.status.value,
            "submittedAt": record.submitted_at.isoformat(),
            "acknowledgedAt": record.acknowledged_at.isoformat() if record.acknowledged_at else None,
            "completedAt": record.completed_at.isoformat() if record.completed_at else None,
            "retryCount": record.retry_count,
        }

    @staticmethod
    def _record_to_history(record: TransmissionRecord) -> Dict[str, Any]:
        return {
            "id": record.transmission_id,
            "invoiceNumber": record.invoice_number,
            "irn": record.irn,
            "status": record.status.value,
            "submittedAt": record.submitted_at.isoformat(),
            "acknowledgedAt": record.acknowledged_at.isoformat() if record.acknowledged_at else None,
            "completedAt": record.completed_at.isoformat() if record.completed_at else None,
            "processingTimeSeconds": record.processing_time_seconds,
            "retryCount": record.retry_count,
            "errorCode": record.error_code,
            "errorMessage": record.error_message,
        }

    @staticmethod
    def _record_to_detail(record: TransmissionRecord) -> Dict[str, Any]:
        history = TransmissionService._record_to_history(record)
        history.update(
            {
                "firsResponse": record.firs_response,
                "payloadSizeBytes": record.payload_size_bytes,
            }
        )
        return history

    @staticmethod
    def _make_identifier(prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:12]}"

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _success(operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"operation": operation, "success": True, "data": data}

    @staticmethod
    def _failure(operation: str, error: str) -> Dict[str, Any]:
        return {"operation": operation, "success": False, "error": error}

    @staticmethod
    def _unsupported(operation: str) -> Dict[str, Any]:
        return {
            "operation": operation,
            "success": False,
            "error": "unsupported_operation",
        }


__all__ = ["TransmissionService"]

