"""Unit tests for enhanced APP TransmissionService pipeline."""

import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone, timedelta
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from unittest.mock import AsyncMock


CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "backend"))
if BACKEND_DIR not in os.sys.path:
    os.sys.path.insert(0, BACKEND_DIR)

from core_platform.messaging.message_router import MessageRouter
from app_services.transmission.transmission_service import TransmissionService
from decimal import Decimal

from core_platform.data_management.models.firs_submission import InvoiceType, SubmissionStatus


class DummyRouter(MessageRouter):
    def __init__(self):
        self.calls = []

    async def route_message(self, service_role, operation, payload, source_service=None):
        self.calls.append({
            "role": service_role,
            "operation": operation,
            "payload": payload,
        })
        return {"success": True, "data": {"operation": operation, "payload": payload}}


@pytest.mark.asyncio
async def test_prepare_invoice_for_submission_signs(monkeypatch):
    service = TransmissionService(message_router=DummyRouter())

    # Avoid heavy transformer logic by returning invoice as-is
    monkeypatch.setattr(
        "app_services.transmission.transmission_service.build_firs_invoice",
        lambda inv: dict(inv),
    )

    async def fake_validate(self, invoice_payload, *, organization_id, invoice_number):
        return {
            "validation_results": {},
            "summary": {"total_errors": 0},
            "overall_status": "compliant",
        }

    async def fake_get_cert(self, organization_id):
        return "cert-123"

    monkeypatch.setattr(TransmissionService, "_validate_invoice", fake_validate, raising=False)
    monkeypatch.setattr(TransmissionService, "_get_signing_certificate_id", fake_get_cert, raising=False)
    monkeypatch.setattr(
        service._digital_certificate_service,
        "sign_invoice_document",
        lambda document, certificate_id: {"signature": "ok", "certificate_id": certificate_id},
    )

    monkeypatch.setenv("APP_TRANSMISSION_AUTO_SIGN", "true")

    prepared, metadata, warnings = await service._prepare_invoice_for_submission(
        {"invoice_number": "INV-001"},
        organization_id="org-1",
        invoice_number="INV-001",
    )

    assert prepared["signature"]["signature"] == "ok"
    assert metadata["signature"]["certificate_id"] == "cert-123"
    assert warnings == []


@pytest.mark.asyncio
async def test_handle_submit_invoice_includes_pipeline_metadata(monkeypatch):
    service = TransmissionService(message_router=DummyRouter())

    pipeline_metadata = {
        "validation_report": {"summary": "ok"},
        "signature": {"signature": "sig"},
    }

    async def fake_prepare(self, invoice, *, organization_id, invoice_number, options=None):
        return ({"invoiceNumber": invoice_number}, pipeline_metadata, ["late_warning"])

    async def fake_persist(self, session, organization_id, invoice_data, firs_response, status_hint=None, request_id=None):
        return SimpleNamespace(
            id=uuid4(),
            status=SubmissionStatus.PENDING,
            organization_id=UUID("11111111-1111-1111-1111-111111111111"),
            invoice_number=invoice_data.get("invoiceNumber"),
            invoice_type=InvoiceType.STANDARD_INVOICE,
            irn=None,
            firs_submission_id=None,
            firs_status_code=None,
            firs_message=None,
            total_amount=Decimal("0"),
            currency="NGN",
            retry_count=0,
            submitted_at=datetime.now(timezone.utc),
            accepted_at=None,
            rejected_at=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            invoice_data=invoice_data,
        )

    monkeypatch.setattr(TransmissionService, "_prepare_invoice_for_submission", fake_prepare, raising=False)
    monkeypatch.setattr(TransmissionService, "_persist_submission", fake_persist, raising=False)
    monkeypatch.setattr(TransmissionService, "_fetch_invoice_record", AsyncMock(return_value=None), raising=False)
    monkeypatch.setattr(service, "_enqueue_outbound_delivery", AsyncMock())
    monkeypatch.setattr(service, "_schedule_status_poll", AsyncMock())
    monkeypatch.setattr(service, "_call_firs", AsyncMock(return_value={"success": True, "data": {"status": "submitted"}}))

    payload = {
        "invoice_data": {"invoice_number": "INV-010"},
        "submission_data": {},
        "organization_id": str(UUID("11111111-1111-1111-1111-111111111111")),
        "irn": "IRN-010",
    }

    result = await service._handle_submit_invoice(payload)

    assert result["validation_report"] == pipeline_metadata["validation_report"]
    assert result["signature"] == pipeline_metadata["signature"]
    assert "late_warning" in result.get("pipeline_warnings", [])
    service._schedule_status_poll.assert_awaited()

    operations = [call["operation"] for call in service.message_router.calls]
    assert operations[:4] == [
        "update_app_received",
        "update_app_submitting",
        "update_app_submitted",
        "update_firs_response",
    ]

    stages = [
        service.message_router.calls[i]["payload"]["metadata"]["stage"]
        for i in range(4)
    ]
    assert stages == [
        "APP_RECEIVED",
        "APP_SUBMITTING",
        "APP_SUBMITTED",
        "FIRS_RESPONSE",
    ]

    final_payload = service.message_router.calls[3]["payload"]
    assert "correlation_metadata" in final_payload["response_data"]
    assert (
        final_payload["response_data"]["correlation_metadata"]["stage"]
        == "FIRS_RESPONSE"
    )


@pytest.mark.asyncio
async def test_run_b2c_reporting_job_queues_pending(monkeypatch):
    queued_requests = []

    async def fake_queue(self, **kwargs):
        queued_requests.append(kwargs)
        return "job-id"

    async def fake_update(self, submission_id, organization_id, new_status, message=None, invoice_number=None):
        return None

    complete_submission = SimpleNamespace(
        id=uuid4(),
        invoice_number="INV-B2C",
        invoice_data={"invoiceNumber": "INV-B2C", "documentMetadata": {"customerType": "B2C"}},
        status=SubmissionStatus.PENDING,
        organization_id=UUID("22222222-2222-2222-2222-222222222222"),
        customer_tin=None,
        submitted_at=datetime.now(timezone.utc) - timedelta(hours=30),
        created_at=datetime.now(timezone.utc) - timedelta(hours=36),
        updated_at=datetime.now(timezone.utc) - timedelta(hours=35),
        request_id=None,
    )

    class DummyResult:
        def __init__(self, items):
            self._items = items

        def scalars(self):
            return self

        def all(self):
            return self._items

    class DummySession:
        async def execute(self, stmt):
            return DummyResult([complete_submission])

        async def get(self, model, pk):
            return None

        def begin(self):
            @asynccontextmanager
            async def ctx():
                yield

            return ctx()

    @asynccontextmanager
    async def fake_session_scope(self):
        yield DummySession()

    service = TransmissionService(message_router=DummyRouter())

    monkeypatch.setattr(TransmissionService, "_session_scope", fake_session_scope, raising=False)
    monkeypatch.setattr(TransmissionService, "_queue_transmission_job", fake_queue, raising=False)
    monkeypatch.setattr(TransmissionService, "_update_submission_status", fake_update, raising=False)
    monkeypatch.setattr(TransmissionService, "_prepare_invoice_for_submission", AsyncMock(return_value=({"invoiceNumber": "INV-B2C"}, {}, [])))

    result = await service._handle_run_b2c_reporting_job({"lookback_hours": 1, "max_invoices": 5})

    assert result["queued"]
    assert queued_requests
