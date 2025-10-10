import asyncio
import sys
import types
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_PATH = REPO_ROOT / "platform" / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.append(str(BACKEND_PATH))

ARCHIVE_BACKEND_PATH = REPO_ROOT / "archive" / "legacy" / "backend"
if ARCHIVE_BACKEND_PATH.exists() and str(ARCHIVE_BACKEND_PATH) not in sys.path:
    sys.path.append(str(ARCHIVE_BACKEND_PATH))

from api_gateway.api_versions.v1.si_endpoints.business_endpoints.erp_endpoints import (  # noqa: E402
    ERPEndpointsV1,
    create_erp_router,
)
from api_gateway.role_routing.models import (  # noqa: E402
    HTTPRoutingContext,
    PlatformRole,
    ServiceRole as RoutingServiceRole,
)
from core_platform.messaging.message_router import MessageRouter, ServiceRole  # noqa: E402
from si_services import SIServiceRegistry  # noqa: E402


class _InMemoryERPRepository:
    def __init__(self):
        self._records: Dict[str, Any] = {}

    async def create(self, record):
        self._records[record.connection_id] = record
        return record

    async def list(self, *, organization_id: str = None, erp_system: str = None, status: str = None):
        results = list(self._records.values())
        if organization_id:
            results = [rec for rec in results if rec.organization_id == organization_id]
        if erp_system:
            results = [rec for rec in results if rec.erp_system == erp_system]
        return results

    async def get(self, connection_id: str):
        return self._records.get(connection_id)

    async def update(self, connection_id: str, updates: Dict[str, Any]):
        record = self._records.get(connection_id)
        if not record:
            return None
        for key, value in updates.items():
            if hasattr(record, key):
                setattr(record, key, value)
        return record

    async def delete(self, connection_id: str):
        return self._records.pop(connection_id, None)


class _StubOdooConnector:
    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def get_invoice_by_id(self, invoice_id: Any) -> Dict[str, Any]:
        normalized = int(invoice_id) if str(invoice_id).isdigit() else invoice_id
        return {"id": normalized, "amount_total": 150.0}

    async def transform_to_firs_format(self, invoice: Dict[str, Any], target_format: str = "UBL_BIS_3.0"):
        return {"firs_invoice": {"invoice": invoice, "format": target_format}}

    def get_invoices(self, limit: int = 50, include_attachments: bool = False) -> List[Dict[str, Any]]:
        return [{"id": index, "amount_total": 200.0 + index} for index in range(1, limit + 1)]


def _provide_context() -> HTTPRoutingContext:
    context = HTTPRoutingContext(
        user_id="si-user",
        organization_id="org-1",
        platform_role=PlatformRole.SYSTEM_INTEGRATOR,
        service_role=RoutingServiceRole.SYSTEM_INTEGRATOR,
        is_authenticated=True,
    )
    context.metadata["source"] = "test"
    return context


class _StubRoleDetector:
    async def detect_role_context(self, request):
        return _provide_context()


class _AllowAllPermissionGuard:
    async def check_endpoint_permission(self, context, path: str, method: str) -> bool:
        return True


@pytest.fixture
def erp_test_client(monkeypatch):
    app = FastAPI()
    message_router = MessageRouter()
    registry = SIServiceRegistry(message_router=message_router)
    repository = _InMemoryERPRepository()
    registry.erp_connection_repository = repository

    async def fake_register_system(config):
        return True

    async def fake_unregister_system(system_id: str):
        return True

    monkeypatch.setattr(
        "si_services.integration_management.connection_manager.register_system",
        fake_register_system,
    )
    monkeypatch.setattr(
        "si_services.integration_management.connection_manager.unregister_system",
        fake_unregister_system,
    )
    connector_module = types.ModuleType("external_integrations.business_systems.erp.odoo.connector")
    connector_module.OdooConnector = _StubOdooConnector
    monkeypatch.setitem(
        sys.modules,
        "external_integrations.business_systems.erp.odoo.connector",
        connector_module,
    )
    odoo_package = types.ModuleType("external_integrations.business_systems.erp.odoo")
    odoo_package.connector = connector_module
    monkeypatch.setitem(
        sys.modules,
        "external_integrations.business_systems.erp.odoo",
        odoo_package,
    )
    erp_package = types.ModuleType("external_integrations.business_systems.erp")
    erp_package.odoo = odoo_package
    monkeypatch.setitem(
        sys.modules,
        "external_integrations.business_systems.erp",
        erp_package,
    )

    role_detector = _StubRoleDetector()
    permission_guard = _AllowAllPermissionGuard()

    async def _fake_require_si_role(self, request):
        return _provide_context()

    monkeypatch.setattr(ERPEndpointsV1, "_require_si_role", _fake_require_si_role, raising=False)
    router = create_erp_router(role_detector, permission_guard, message_router)
    app.include_router(router, prefix="/api/v1/si/business")

    async def setup_services():
        integration_callback = registry._create_integration_callback({})
        await message_router.register_service(
            service_name="integration_management",
            service_role=ServiceRole.SYSTEM_INTEGRATOR,
            callback=integration_callback,
            metadata={
                "operations": [
                    "create_erp_connection",
                    "list_erp_connections",
                    "get_erp_connection",
                    "update_erp_connection",
                    "delete_erp_connection",
                    "test_erp_connection",
                ]
            },
        )
        erp_callback = registry._create_erp_callback({})
        await message_router.register_service(
            service_name="erp_integration",
            service_role=ServiceRole.SYSTEM_INTEGRATOR,
            callback=erp_callback,
            metadata={
                "operations": [
                    "fetch_odoo_invoices_for_firs",
                    "fetch_odoo_invoice_batch_for_firs",
                ]
            },
        )

    asyncio.run(setup_services())

    client = TestClient(app)
    try:
        yield client, repository
    finally:
        client.close()


def test_create_get_and_list_connections_flow(erp_test_client):
    client, _repo = erp_test_client

    create_payload = {
        "erp_system": "odoo",
        "organization_id": "org-1",
        "connection_config": {"url": "http://odoo.local"},
        "connection_name": "Demo Connection",
    }

    create_response = client.post(
        "/api/v1/si/business/erp/connections",
        json=create_payload,
    )
    assert create_response.status_code == 201
    create_body = create_response.json()
    connection = create_body["data"]["connection"]
    connection_id = connection["connection_id"]
    assert connection["erp_system"] == "odoo"

    list_response = client.get("/api/v1/si/business/erp/connections")
    assert list_response.status_code == 200
    list_body = list_response.json()
    assert list_body["data"]["total_count"] == 1
    assert list_body["data"]["connections"][0]["connection_id"] == connection_id

    detail_response = client.get(f"/api/v1/si/business/erp/connections/{connection_id}")
    assert detail_response.status_code == 200
    detail_body = detail_response.json()
    assert detail_body["data"]["connection_id"] == connection_id


def test_test_fetch_invoices_endpoint_uses_mocked_odoo(erp_test_client):
    client, _repo = erp_test_client

    payload = {
        "invoice_ids": ["101"],
        "odoo_config": {"url": "http://odoo.local"},
        "transform": True,
        "target_format": "UBL_BIS_3.0",
    }

    response = client.post(
        "/api/v1/si/business/erp/odoo/test-fetch-invoices",
        json=payload,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["fetched_count"] == 1
    assert body["data"]["invoices"][0]["invoice"]["id"] == 101
    assert body["data"]["errors"] == []


def test_test_fetch_invoice_batch_endpoint_uses_mocked_odoo(erp_test_client):
    client, _repo = erp_test_client

    payload = {
        "batch_size": 2,
        "include_attachments": False,
        "odoo_config": {"url": "http://odoo.local"},
        "transform": True,
        "target_format": "UBL_BIS_3.0",
    }

    response = client.post(
        "/api/v1/si/business/erp/odoo/test-fetch-batch",
        json=payload,
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["fetched_count"] == 2
    assert len(body["data"]["invoices"]) == 2
    assert all("invoice" in invoice for invoice in body["data"]["invoices"])
    assert body["data"]["errors"] == []
