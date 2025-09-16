"""
Unit tests for MessageRouter schema/version validation at the router boundary.
"""
import os
import sys
import asyncio
from typing import Optional


def test_pydantic_schema_validation_pass_and_fail(monkeypatch):
    # Enable schema validation and set fail mode to raise for deterministic assertions
    monkeypatch.setenv("ROUTER_VALIDATE_SCHEMA", "true")
    monkeypatch.setenv("ROUTER_SCHEMA_FAIL_MODE", "raise")

    # Ensure backend path
    CURRENT_DIR = os.path.dirname(__file__)
    BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "backend"))
    if BACKEND_DIR not in sys.path:
        sys.path.insert(0, BACKEND_DIR)

    from pydantic import BaseModel
    from core_platform.messaging.message_router import MessageRouter, ServiceRole

    class SubmitInvoiceModel(BaseModel):
        schema_version: str
        invoice_number: str
        amount: float

    router = MessageRouter()
    router.register_operation_schema(
        "submit_invoice",
        pydantic_model=SubmitInvoiceModel,
        expected_version="1.0",
    )

    # Valid payload
    valid = {"schema_version": "1.0", "invoice_number": "INV-001", "amount": 123.45}
    # With no services registered this returns a dev response; we're asserting validation doesn't raise
    result = asyncio.get_event_loop().run_until_complete(
        router.route_message(ServiceRole.ACCESS_POINT_PROVIDER, "submit_invoice", valid)
    )
    assert isinstance(result, dict)

    # Invalid payload: version mismatch
    invalid_version = {"schema_version": "2.0", "invoice_number": "INV-001", "amount": 123.45}
    try:
        asyncio.get_event_loop().run_until_complete(
            router.route_message(ServiceRole.ACCESS_POINT_PROVIDER, "submit_invoice", invalid_version)
        )
        assert False, "expected version mismatch to raise"
    except RuntimeError as e:
        assert "schema_version mismatch" in str(e)

    # Invalid payload: missing field (pydantic)
    invalid_payload = {"schema_version": "1.0", "amount": 10.0}
    try:
        asyncio.get_event_loop().run_until_complete(
            router.route_message(ServiceRole.ACCESS_POINT_PROVIDER, "submit_invoice", invalid_payload)
        )
        assert False, "expected pydantic validation failure"
    except RuntimeError as e:
        assert "pydantic validation failed" in str(e)


def test_jsonschema_validation(monkeypatch):
    monkeypatch.setenv("ROUTER_VALIDATE_SCHEMA", "true")
    monkeypatch.setenv("ROUTER_SCHEMA_FAIL_MODE", "raise")

    CURRENT_DIR = os.path.dirname(__file__)
    BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "backend"))
    if BACKEND_DIR not in sys.path:
        sys.path.insert(0, BACKEND_DIR)

    from core_platform.messaging.message_router import MessageRouter, ServiceRole

    schema = {
        "type": "object",
        "required": ["schema_version", "event_type", "data"],
        "properties": {
            "schema_version": {"type": "string"},
            "event_type": {"type": "string"},
            "data": {"type": "object"},
        },
        "additionalProperties": True,
    }

    router = MessageRouter()
    router.register_operation_schema("notify_firs_status", json_schema=schema, expected_version="1.0")

    ok = {"schema_version": "1.0", "event_type": "status.update", "data": {"status": "accepted"}}
    r = asyncio.get_event_loop().run_until_complete(
        router.route_message(ServiceRole.ACCESS_POINT_PROVIDER, "notify_firs_status", ok)
    )
    assert isinstance(r, dict)

    bad = {"schema_version": "1.0", "event_type": "status.update"}
    try:
        asyncio.get_event_loop().run_until_complete(
            router.route_message(ServiceRole.ACCESS_POINT_PROVIDER, "notify_firs_status", bad)
        )
        assert False, "expected jsonschema validation failure"
    except RuntimeError as e:
        assert "jsonschema validation failed" in str(e)

