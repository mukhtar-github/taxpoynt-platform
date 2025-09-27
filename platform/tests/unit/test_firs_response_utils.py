"""Tests for FIRS response normalization utilities."""

from core_platform.utils.firs_response import (
    extract_firs_identifiers,
    merge_identifiers_into_payload,
    map_firs_status_to_submission,
)


def test_extract_identifiers_from_nested_payload():
    payload = {
        "data": {
            "irn": "INV-123",
            "cryptographicStamp": "CSID-456",
            "response": {
                "qr_code": "{\"value\":\"qr-data\"}",
                "statusCode": "200",
                "submissionId": "abc-001",
                "details": {"stampMetadata": {"issuer": "FIRS"}},
            },
        }
    }

    identifiers = extract_firs_identifiers(payload)

    assert identifiers["irn"] == "INV-123"
    assert identifiers["csid"] == "CSID-456"
    assert identifiers["status_code"] == "200"
    assert identifiers["response_id"] == "abc-001"
    assert identifiers["firs_stamp_metadata"] == {"issuer": "FIRS"}
    assert identifiers["qr_payload"] == {"value": "qr-data"}


def test_merge_identifiers_into_payload():
    payload = {"status": "submitted"}
    identifiers = {
        "irn": "INV-123",
        "csid": "CS-789",
        "csid_hash": "HASH",
        "qr_payload": {"value": "qr"},
    }

    merged = merge_identifiers_into_payload(payload, identifiers)

    assert merged["identifiers"] == identifiers
    assert merged["irn"] == "INV-123"
    assert merged["csid"] == "CS-789"
    assert merged["csidHash"] == "HASH"
    assert merged["qr"] == {"value": "qr"}


def test_map_firs_status_to_submission():
    assert map_firs_status_to_submission("Accepted") == "accepted"
    assert map_firs_status_to_submission("REJECTED") == "rejected"
    assert map_firs_status_to_submission("Processing") == "processing"
    assert map_firs_status_to_submission(None) == "submitted"
