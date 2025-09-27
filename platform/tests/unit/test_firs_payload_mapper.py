"""Tests for the APP-side FIRS payload mapper."""

from datetime import datetime

from app_services.firs_communication.firs_payload_mapper import build_firs_invoice


def test_mapper_matches_required_fields(tmp_path):
    firs_invoice = build_firs_invoice({
        "invoice_number": "INV-123",
        "supplier": {"tin": "11111111-0001", "cacNumber": "RC12345"},
        "customer": {"name": "Buyer", "tin": "22222222-0001"},
        "items": [{"name": "Service", "quantity": 1, "unit_price": 1000, "vat_amount": 75}],
    })

    for key in (
        "version",
        "standard",
        "documentMetadata",
        "supplierInformation",
        "buyerInformation",
        "lineItems",
        "taxSummary",
        "paymentInformation",
        "additionalDocumentReferences",
    ):
        assert key in firs_invoice


def test_maps_platform_invoice_to_firs_structure():
    platform_invoice = {
        "invoice_number": "INV-001",
        "invoice_date": "2024-11-05",
        "currency": "ngn",
        "customer": {
            "name": "Acme Corp",
            "tin": "12345678-0001",
            "email": "billing@acme.test",
            "address": {
                "street": "12 Business Road",
                "city": "Lagos",
                "state": "LA",
                "postal_code": "100001",
            },
        },
        "supplier": {
            "name": "TaxPoynt",
            "tin": "87654321-0001",
        },
        "items": [
            {
                "name": "Consulting",
                "quantity": 2,
                "unit_price": 50000,
                "vat_amount": 7500,
            },
            {
                "name": "Implementation",
                "quantity": 1,
                "unit_price": 25000,
                "vat_amount": 3750,
            },
        ],
    }

    firs_invoice = build_firs_invoice(platform_invoice)

    metadata = firs_invoice["documentMetadata"]
    assert metadata["invoiceNumber"] == "INV-001"
    assert metadata["invoiceDate"] == "2024-11-05"
    assert metadata["currencyCode"] == "NGN"
    assert metadata["invoiceType"] == "STANDARD"

    buyer = firs_invoice["buyerInformation"]
    assert buyer["tin"] == "12345678-0001"
    assert buyer["address"]["cityName"] == "Lagos"
    assert buyer["address"]["stateCode"] == "LA"

    assert len(firs_invoice["lineItems"]) == 2
    first_line = firs_invoice["lineItems"][0]
    assert first_line["lineNumber"] == 1
    assert first_line["productDescription"] == "Consulting"
    assert first_line["vatRate"] == 7.5

    summary = firs_invoice["taxSummary"]
    assert summary["subtotal"] == 125000.0
    assert summary["totalVAT"] == 11250.0
    assert summary["totalPayable"] == 136250.0


def test_mapper_preserves_existing_firs_invoice():
    firs_ready = {
        "invoice_reference": "INV-900",
        "invoice_number": "INV-900",
        "invoice_date": datetime(2024, 9, 10),
        "currency_code": "NGN",
        "line_items": [
            {
                "description": "Service",
                "quantity": 1,
                "unit_price": 100000,
                "total_amount": 107500,
                "vat_amount": 7500,
                "vat_rate": 7.5,
            }
        ],
        "supplier": {"name": "TaxPoynt"},
        "customer": {"name": "Client"},
    }

    mapped = build_firs_invoice(firs_ready)

    metadata = mapped["documentMetadata"]
    assert metadata["invoiceNumber"] == "INV-900"
    assert metadata["invoiceDate"] == "2024-09-10"

    summary = mapped["taxSummary"]
    assert summary["totalVAT"] == 7500.0
    assert summary["totalPayable"] == 107500.0


def test_mapper_handles_missing_line_items():
    platform_invoice = {
        "invoice_number": "INV-777",
        "total_amount": "50000",
        "vat_amount": "3750",
    }

    firs_invoice = build_firs_invoice(platform_invoice)

    line_items = firs_invoice["lineItems"]
    assert len(line_items) == 1
    item = line_items[0]
    assert item["totalAmount"] == 50000.0
    assert item["vatAmount"] == 3750.0

    summary = firs_invoice["taxSummary"]
    assert summary["subtotal"] == 46250.0
