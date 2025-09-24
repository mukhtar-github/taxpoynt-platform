import asyncio
import uuid
from typing import Dict, Any

import pytest

from core_platform.messaging.message_router import MessageRouter
from app_services import APPServiceRegistry


def _sample_invoice(**overrides: Dict[str, Any]) -> Dict[str, Any]:
    base = {
        "document_id": str(uuid.uuid4()),
        "document_type": "invoice",
        "invoice_number": "INV-001",
        "invoice_date": "2024-01-01",
        "due_date": "2024-01-10",
        "currency": "NGN",
        "subtotal": 1000.0,
        "tax_amount": 75.0,
        "total_amount": 1075.0,
        "supplier": {
            "name": "Supplier",
            "tin": "12345678-1234",
            "vat_number": "12345678-1234",
            "phone": "+2348012345678",
            "email": "supplier@example.com",
            "address": {
                "street": "1 Street",
                "city": "Lagos",
                "state": "LA",
                "country": "NG",
                "postal_code": "100001",
            },
        },
        "customer": {
            "name": "Customer",
            "tin": "87654321-4321",
            "vat_number": "87654321-4321",
            "phone": "+2348098765432",
            "email": "customer@example.com",
            "address": {
                "street": "2 Street",
                "city": "Abuja",
                "state": "FC",
                "country": "NG",
                "postal_code": "900001",
            },
        },
        "items": [
            {"description": "Item A", "quantity": 5, "unit_price": 100.0, "total_price": 500.0, "tax_amount": 37.5},
            {"description": "Item B", "quantity": 5, "unit_price": 100.0, "total_price": 500.0, "tax_amount": 37.5},
        ],
        "workflow_status": "reviewed",
    }
    base.update(overrides)
    return base


@pytest.fixture
def validation_environment():
    registry = APPServiceRegistry(MessageRouter())
    validation_service = registry._create_validation_service_state()
    callback = registry._create_validation_callback(validation_service)
    return validation_service, callback


@pytest.mark.asyncio
async def test_validate_single_invoice_success(validation_environment):
    service_state, callback = validation_environment
    invoice = _sample_invoice()

    response = await callback("validate_single_invoice", {"invoice_data": invoice})

    assert response["success"] is True
    data = response["data"]
    assert data["summary"]["compliance"]["is_valid"] is True
    assert data["summary"]["submission"]["readiness"] in {"ready", "pending"}
    assert service_state["metrics"]["total_requests"] == 1
    assert service_state["validation_store"][data["validation_id"]]["status"] == data["status"]


@pytest.mark.asyncio
async def test_validation_metrics_and_quality_report(validation_environment):
    service_state, callback = validation_environment

    good_invoice = _sample_invoice()
    bad_invoice = _sample_invoice(supplier={"name": "Supplier", "tin": "INVALID", "address": {"street": "1 Street", "city": "Lagos", "state": "LA", "country": "NG", "postal_code": "100001"}})

    await callback("validate_single_invoice", {"invoice_data": good_invoice})
    await callback("validate_single_invoice", {"invoice_data": bad_invoice})

    metrics_response = await callback("get_validation_metrics", {})
    metrics = metrics_response["data"]["metrics"]
    assert metrics["total_validations"] == 2
    assert metrics["passed"] + metrics["failed"] == 2

    quality_response = await callback("get_data_quality_metrics", {})
    quality_data = quality_response["data"]
    assert "overall_quality_score" in quality_data
    assert quality_data["total_validations"] == 2

    report_response = await callback("generate_quality_report", {"report_config": {}})
    assert report_response["success"] is True
    assert "report_id" in report_response["data"]


@pytest.mark.asyncio
async def test_validate_invoice_batch_tracks_results(validation_environment):
    service_state, callback = validation_environment
    invoices = [_sample_invoice(), _sample_invoice(invoice_number="INV-002")]

    batch_response = await callback(
        "validate_invoice_batch",
        {"batch_data": {"batch_id": "BATCH-TEST", "invoices": invoices}},
    )

    assert batch_response["success"] is True
    batch_data = batch_response["data"]
    assert batch_data["summary"]["total"] == len(invoices)
    status_response = await callback("get_batch_validation_status", {"batch_id": "BATCH-TEST"})
    assert status_response["success"] is True
    assert status_response["data"]["batch_id"] == "BATCH-TEST"

    analysis_response = await callback("get_validation_error_analysis", {})
    assert analysis_response["success"] is True
    assert "analysis" in analysis_response["data"]
