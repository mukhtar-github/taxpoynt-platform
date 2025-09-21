import asyncio
from fastapi import FastAPI, APIRouter
from fastapi.testclient import TestClient

from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from core_platform.messaging.message_router import MessageRouter, ServiceRole

from api_gateway.api_versions.v1.si_endpoints.financial_endpoints.payment_processor_endpoints import (
    create_payment_processor_router,
)


async def _register_dummy_payment_ops(router: MessageRouter):
    async def cb(op: str, payload: dict):
        if op == "receive_payment_webhook":
            return {"accepted": True, "provider": payload.get("provider")}
        return {"ok": True}

    await router.register_service(
        service_name="test_payment_service",
        service_role=ServiceRole.SYSTEM_INTEGRATOR,
        callback=cb,
        metadata={"operations": ["receive_payment_webhook"]},
    )


def _build_app_with_payments(message_router: MessageRouter) -> TestClient:
    app = FastAPI()
    role_detector = HTTPRoleDetector()
    permission_guard = APIPermissionGuard(app=None)

    si_base = APIRouter(prefix="/api/v1/si")
    si_base.include_router(create_payment_processor_router(role_detector, permission_guard, message_router))
    app.include_router(si_base)
    return TestClient(app)


def test_inbound_payment_webhook_requires_signature():
    router = MessageRouter()
    asyncio.run(_register_dummy_payment_ops(router))
    client = _build_app_with_payments(router)

    # Missing signature -> 401
    r = client.post("/api/v1/si/payments/webhooks/inbound/paystack", json={"event": "charge.success"})
    assert r.status_code == 401


def test_inbound_payment_webhook_ok_with_signature():
    router = MessageRouter()
    asyncio.run(_register_dummy_payment_ops(router))
    client = _build_app_with_payments(router)

    r = client.post(
        "/api/v1/si/payments/webhooks/inbound/paystack",
        headers={"x-webhook-signature": "testsig"},
        json={"event": "charge.success"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body.get("action") == "payment_webhook_received"
