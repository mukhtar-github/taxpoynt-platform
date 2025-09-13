"""
Unit test: ensure APP FIRS validation operations are recognized by the router
and do not emit 'operation not registered' warnings.

We test the MessageRouter in isolation by registering an APP service with
metadata that advertises the operations added in app_services.__init__ and
then route messages for those operations, asserting no warnings are logged.
"""
import asyncio
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
async def test_app_validation_ops_registered_no_warnings(caplog):
    router = MessageRouter()

    # Register a dummy APP endpoint with the advertised operations
    advertised_ops = [
        "validate_invoice_for_firs",
        "validate_invoice_batch_for_firs",
        "get_firs_validation_rules",
    ]

    async def dummy_callback(operation: str, payload: dict):
        return {"operation": operation, "success": True, "data": {"ok": True}}

    # register_service is async in Redis router; here it's sync router so use it directly
    await router.register_service(
        service_name="firs_communication",
        service_role=ServiceRole.ACCESS_POINT_PROVIDER,
        callback=dummy_callback,
        metadata={"operations": advertised_ops},
    )

    caplog.set_level(logging.WARNING)

    # Route all advertised operations; should not emit our validator warning
    for op in advertised_ops:
        _ = await router.route_message(
            service_role=ServiceRole.ACCESS_POINT_PROVIDER,
            operation=op,
            payload={}
        )

    # Ensure no 'Route op not registered' warning in logs
    for rec in caplog.records:
        assert "op not registered" not in rec.getMessage()
