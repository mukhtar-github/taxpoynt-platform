import asyncio
from fastapi import FastAPI, APIRouter
from fastapi.testclient import TestClient

from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from core_platform.messaging.message_router import MessageRouter, ServiceRole

from api_gateway.api_versions.v1.si_endpoints.business_endpoints.crm_endpoints import (
    create_crm_router,
)
from api_gateway.api_versions.v1.si_endpoints.business_endpoints.pos_endpoints import (
    create_pos_router,
)


async def _register_dummy_odoo_business_ops(router: MessageRouter):
    async def cb(operation: str, payload: dict):
        if operation == "get_crm_opportunities":
            return {"items": [{"id": 1, "name": "Opp A"}, {"id": 2, "name": "Opp B"}]}
        if operation == "get_crm_opportunity":
            oid = int(payload.get("opportunity_id", 0))
            return {"data": {"id": oid, "name": f"Opp {oid}"}}
        if operation == "get_pos_orders":
            return {"items": [{"id": 10, "total": 100.0}, {"id": 11, "total": 50.0}]}
        if operation == "get_pos_order":
            oid = int(payload.get("order_id", 0))
            return {"data": {"id": oid, "total": 123.45}}
        return {"data": {}}

    await router.register_service(
        service_name="test_odoo_business",
        service_role=ServiceRole.SYSTEM_INTEGRATOR,
        callback=cb,
        metadata={
            "operations": [
                "get_crm_opportunities",
                "get_crm_opportunity",
                "get_pos_orders",
                "get_pos_order",
            ]
        },
    )


def _build_app_with_routers(message_router: MessageRouter) -> TestClient:
    app = FastAPI()
    role_detector = HTTPRoleDetector()
    permission_guard = APIPermissionGuard(app=None)

    # Build SI base router and include CRM/POS
    si_base = APIRouter(prefix="/api/v1/si")
    si_base.include_router(create_crm_router(role_detector, permission_guard, message_router))
    si_base.include_router(create_pos_router(role_detector, permission_guard, message_router))
    app.include_router(si_base)
    return TestClient(app)


def test_crm_opportunities_list_and_get():
    router = MessageRouter()
    asyncio.run(_register_dummy_odoo_business_ops(router))
    client = _build_app_with_routers(router)

    # List opportunities
    resp = client.get("/api/v1/si/crm/opportunities?limit=2")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("action") == "crm_opportunities_listed"
    data = body.get("data", {})
    # In dev router mode, the message router returns an envelope; validate core markers
    assert data.get("operation") == "get_crm_opportunities"
    assert "message_id" in data

    # Get single opportunity
    resp = client.get("/api/v1/si/crm/opportunities/1")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("action") == "crm_opportunity_retrieved"
    data = body.get("data", {})
    assert data.get("operation") == "get_crm_opportunity"
    assert "message_id" in data


def test_pos_orders_list_and_get():
    router = MessageRouter()
    asyncio.run(_register_dummy_odoo_business_ops(router))
    client = _build_app_with_routers(router)

    # List POS orders
    resp = client.get("/api/v1/si/pos/orders?limit=2")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("action") == "pos_orders_listed"
    data = body.get("data", {})
    assert data.get("operation") == "get_pos_orders"
    assert "message_id" in data

    # Get single POS order
    resp = client.get("/api/v1/si/pos/orders/10")
    assert resp.status_code == 200
    body = resp.json()
    assert body.get("action") == "pos_order_retrieved"
    data = body.get("data", {})
    assert data.get("operation") == "get_pos_order"
    assert "message_id" in data
