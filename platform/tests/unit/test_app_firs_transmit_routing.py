"""
Unit test: ensure APP FIRS transmit and confirm operations route and are recognized.

We don't spin up FastAPI here; instead we validate MessageRouter operation
handling with a mocked APP service callback that simulates the HTTP client.
"""
import logging
import os
import sys
import pytest

# Put platform/backend on sys.path so 'core_platform' can be imported directly
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from core_platform.messaging.message_router import MessageRouter, ServiceRole


@pytest.mark.asyncio
async def test_app_transmit_and_confirm_ops_registered(caplog):
    router = MessageRouter()

    advertised_ops = [
        "transmit_firs_invoice",
        "confirm_firs_receipt",
    ]

    async def dummy_app_callback(operation: str, payload: dict):
        if operation == "transmit_firs_invoice":
            assert payload.get("irn") == "IRN-TEST-123"
            return {"operation": operation, "success": True, "data": {"transmit": "ok"}}
        if operation == "confirm_firs_receipt":
            assert payload.get("irn") == "IRN-TEST-123"
            return {"operation": operation, "success": True, "data": {"confirm": "ok"}}
        return {"operation": operation, "success": False, "error": "unexpected"}

    await router.register_service(
        service_name="firs_communication",
        service_role=ServiceRole.ACCESS_POINT_PROVIDER,
        callback=dummy_app_callback,
        metadata={"operations": advertised_ops},
    )

    caplog.set_level(logging.WARNING)

    # Transmit
    resp1 = await router.route_message(
        service_role=ServiceRole.ACCESS_POINT_PROVIDER,
        operation="transmit_firs_invoice",
        payload={"irn": "IRN-TEST-123"}
    )
    assert resp1.get("routing_successful")

    # Confirm receipt
    resp2 = await router.route_message(
        service_role=ServiceRole.ACCESS_POINT_PROVIDER,
        operation="confirm_firs_receipt",
        payload={"irn": "IRN-TEST-123"}
    )
    assert resp2.get("routing_successful")

    # Ensure no mapping warnings were logged
    for rec in caplog.records:
        assert "op not registered" not in rec.getMessage()
