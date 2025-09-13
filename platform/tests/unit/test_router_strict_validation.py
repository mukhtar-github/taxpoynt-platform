"""
Unit test: verify strict op-mapping validation raises when enabled.

Sets ROUTER_STRICT_OPS=true before constructing MessageRouter, registers a
service that does not advertise the tested operation, and asserts that
route_message raises a RuntimeError instead of just warning.
"""
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
async def test_strict_op_validation_raises():
    prev = os.environ.get("ROUTER_STRICT_OPS")
    os.environ["ROUTER_STRICT_OPS"] = "true"
    try:
        router = MessageRouter()

        # Register a dummy APP endpoint that advertises only 'known_op'
        async def dummy_callback(operation: str, payload: dict):
            return {"operation": operation, "success": True}

        await router.register_service(
            service_name="dummy_app",
            service_role=ServiceRole.ACCESS_POINT_PROVIDER,
            callback=dummy_callback,
            metadata={"operations": ["known_op"]},
        )

        # Attempt to route an unknown operation; strict mode should raise
        with pytest.raises(RuntimeError):
            await router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="unknown_op",
                payload={}
            )
    finally:
        # Restore env
        if prev is None:
            os.environ.pop("ROUTER_STRICT_OPS", None)
        else:
            os.environ["ROUTER_STRICT_OPS"] = prev

