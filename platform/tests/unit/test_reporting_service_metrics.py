import asyncio
import pytest
from datetime import datetime

from platform.backend.si_services.reporting_services.reporting_service import SIReportingService
from platform.backend.core_platform.data_management.models.firs_submission import SubmissionStatus


class FakeScalarResult:
    def __init__(self, rows):
        self._rows = rows

    def scalars(self):
        class S:
            def __init__(self, rows):
                self._rows = rows

            def all(self):
                return self._rows

        return S(self._rows)


class FakeDB:
    def __init__(self, rows):
        self._rows = rows

    async def execute(self, stmt):
        return FakeScalarResult(self._rows)


class Row:
    def __init__(self, status, created_at, firs_message=None, invoice_type=None, currency="NGN"):
        self.status = status
        self.created_at = created_at
        self.firs_message = firs_message
        self.invoice_type = invoice_type
        self.currency = currency


@pytest.mark.asyncio
async def test_transaction_metrics_histogram_and_counts():
    class InvoiceType:
        STANDARD_INVOICE = type("EnumVal", (), {"value": "standard_invoice"})()
        CREDIT_NOTE = type("EnumVal", (), {"value": "credit_note"})()

    rows = [
        Row(SubmissionStatus.ACCEPTED, datetime(2024, 1, 1, 10, 0, 0), None, InvoiceType.STANDARD_INVOICE, "NGN"),
        Row(SubmissionStatus.SUBMITTED, datetime(2024, 1, 1, 12, 0, 0), None, InvoiceType.CREDIT_NOTE, "USD"),
        Row(SubmissionStatus.REJECTED, datetime(2024, 1, 2, 9, 0, 0), "Bad TIN", InvoiceType.STANDARD_INVOICE, "NGN"),
        Row(SubmissionStatus.FAILED, datetime(2024, 1, 2, 11, 0, 0), "Bad TIN", InvoiceType.STANDARD_INVOICE, "ngn"),
    ]
    db = FakeDB(rows)
    service = SIReportingService()

    result = await service.handle_operation(
        "generate_transaction_compliance_report",
        {
            "organization_id": None,
            "start_date": "2023-12-31T00:00:00",
            "end_date": "2024-01-31T23:59:59",
            "include_metrics": True,
        },
        db=db,
    )

    assert result["success"] is True
    report = result["report"]
    assert report["summary"]["total"] == 4
    assert report["summary"]["compliant"] == 2
    assert report["summary"]["non_compliant"] == 2

    metrics = report["metrics"]
    assert metrics["daily_counts"]["2024-01-01"] == 2
    assert metrics["daily_counts"]["2024-01-02"] == 2
    # status histogram keys are string enum values
    assert metrics["status_histogram"][SubmissionStatus.ACCEPTED.value] == 1
    assert metrics["status_histogram"][SubmissionStatus.SUBMITTED.value] == 1
    assert metrics["status_histogram"][SubmissionStatus.REJECTED.value] == 1
    assert metrics["status_histogram"][SubmissionStatus.FAILED.value] == 1

    # top errors should aggregate
    top_errors = report["top_errors"]
    assert top_errors and top_errors[0]["message"] == "Bad TIN"
    assert top_errors[0]["count"] == 2

    # extra histograms
    inv_hist = report["metrics"]["invoice_type_histogram"]
    assert inv_hist["standard_invoice"] == 3
    assert inv_hist["credit_note"] == 1
    curr_hist = report["metrics"]["currency_histogram"]
    assert curr_hist["NGN"] == 3
    assert curr_hist["USD"] == 1
