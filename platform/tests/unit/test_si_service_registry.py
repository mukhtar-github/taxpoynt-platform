from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

import pytest
import sys
import types


REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_PATH = REPO_ROOT / "platform" / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.append(str(BACKEND_PATH))

ARCHIVE_BACKEND_PATH = REPO_ROOT / "archive" / "legacy" / "backend"
if ARCHIVE_BACKEND_PATH.exists() and str(ARCHIVE_BACKEND_PATH) not in sys.path:
    sys.path.append(str(ARCHIVE_BACKEND_PATH))

from core_platform.messaging.message_router import MessageRouter  # noqa: E402
from si_services import SIServiceRegistry  # noqa: E402
from si_services.integration_management import (  # noqa: E402
    erp_connection_repository as repo_module,
)
from si_services.integration_management.erp_connection_repository import (  # noqa: E402
    ERPConnectionRecord,
    ERPConnectionRepository,
)


class _StubOdooConnector:
    """Lightweight stub mimicking the Odoo connector used by ERP callbacks."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._stored_invoices: Dict[Any, Dict[str, Any]] = {}

    def get_invoice_by_id(self, invoice_id: Any) -> Dict[str, Any]:
        normalized = int(invoice_id) if str(invoice_id).isdigit() else invoice_id
        invoice = {"id": normalized, "total": 150.0}
        self._stored_invoices[normalized] = invoice
        return invoice

    async def transform_to_firs_format(self, invoice: Dict[str, Any], target_format: str = "UBL_BIS_3.0"):
        return {"firs_invoice": {"invoice": invoice, "format": target_format}}

    def get_invoices(self, limit: int = 50, include_attachments: bool = False) -> List[Dict[str, Any]]:
        return [{"id": index, "total": 200.0 + index} for index in range(1, limit + 1)]


@pytest.fixture(autouse=True)
def _patch_odoo_connector(monkeypatch):
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


@pytest.mark.asyncio
async def test_erp_callback_fetch_invoices_transforms_payload():
    registry = SIServiceRegistry(message_router=MessageRouter())
    erp_callback = registry._create_erp_callback(erp_service={})

    payload = {
        "odoo_config": {"url": "http://odoo.local"},
        "invoice_ids": ["123"],
        "transform": True,
        "target_format": "UBL_BIS_3.0",
    }

    result = await erp_callback("fetch_odoo_invoices_for_firs", payload)

    assert result["operation"] == "fetch_odoo_invoices_for_firs"
    assert result["success"] is True
    invoices = result["data"]["invoices"]
    assert len(invoices) == 1
    assert invoices[0]["invoice"]["id"] == 123
    assert result["data"].get("errors", []) == []


@pytest.mark.asyncio
async def test_erp_callback_fetch_invoice_batch_transforms_payload():
    registry = SIServiceRegistry(message_router=MessageRouter())
    erp_callback = registry._create_erp_callback(erp_service={})

    payload = {
        "odoo_config": {"url": "http://odoo.local"},
        "batch_size": 2,
        "transform": True,
        "target_format": "UBL_BIS_3.0",
    }

    result = await erp_callback("fetch_odoo_invoice_batch_for_firs", payload)

    assert result["operation"] == "fetch_odoo_invoice_batch_for_firs"
    assert result["success"] is True
    invoices = result["data"]["invoices"]
    assert len(invoices) == 2
    assert all("invoice" in invoice for invoice in invoices)
    assert result["data"].get("errors", []) == []


def _patch_async_session(monkeypatch, db_handle: Any = "db"):
    async def fake_get_async_session():
        yield db_handle

    monkeypatch.setattr(repo_module, "get_async_session", fake_get_async_session)


@pytest.mark.asyncio
async def test_repository_create_calls_db_layer(monkeypatch):
    captured: Dict[str, Any] = {}

    async def fake_create_connection(db, **kwargs):
        captured["db"] = db
        captured["kwargs"] = kwargs
        return {
            "connection_id": kwargs["connection_id"],
            "organization_id": kwargs["organization_id"],
            "erp_system": kwargs["erp_system"],
            "connection_name": kwargs["connection_name"],
            "environment": kwargs["environment"],
            "connection_config": kwargs["connection_config"],
            "metadata": kwargs["metadata"],
            "status": kwargs["status"],
            "owner_user_id": kwargs["owner_user_id"],
            "status_reason": kwargs["status_reason"],
            "is_active": True,
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }

    _patch_async_session(monkeypatch)
    monkeypatch.setattr(repo_module, "db_create_connection", fake_create_connection)

    repo = ERPConnectionRepository()
    record = ERPConnectionRecord(
        connection_id="cx-1",
        organization_id="org-1",
        erp_system="odoo",
        connection_name="Test",
        environment="sandbox",
        connection_config={"url": "http://example.com"},
    )

    result = await repo.create(record)

    assert captured["db"] == "db"
    assert captured["kwargs"]["connection_id"] == "cx-1"
    assert isinstance(result, ERPConnectionRecord)
    assert result.connection_id == "cx-1"


@pytest.mark.asyncio
async def test_repository_list_returns_filtered_records(monkeypatch):
    captured_filters: Dict[str, Any] = {}

    async def fake_list_connections(db, **filters):
        captured_filters.update(filters)
        return [
            {
                "connection_id": "cx-1",
                "organization_id": "org-1",
                "erp_system": "odoo",
                "connection_name": "Primary",
                "environment": "sandbox",
                "connection_config": {"url": "http://example.com"},
                "metadata": {},
                "status": "configured",
                "owner_user_id": None,
                "status_reason": None,
                "is_active": True,
                "created_at": datetime.now(timezone.utc),
                "updated_at": datetime.now(timezone.utc),
            }
        ]

    _patch_async_session(monkeypatch)
    monkeypatch.setattr(repo_module, "db_list_connections", fake_list_connections)

    repo = ERPConnectionRepository()
    results = await repo.list(organization_id="org-1", erp_system="odoo")

    assert captured_filters["organization_id"] == "org-1"
    assert captured_filters["erp_system"] == "odoo"
    assert len(results) == 1
    assert isinstance(results[0], ERPConnectionRecord)


@pytest.mark.asyncio
async def test_repository_get_update_delete(monkeypatch):
    stored_record = {
        "connection_id": "cx-1",
        "organization_id": "org-1",
        "erp_system": "odoo",
        "connection_name": "Primary",
        "environment": "sandbox",
        "connection_config": {"url": "http://example.com"},
        "metadata": {},
        "status": "configured",
        "owner_user_id": None,
        "status_reason": None,
        "is_active": True,
        "created_at": datetime.now(timezone.utc),
        "updated_at": datetime.now(timezone.utc),
    }

    async def fake_get_connection(db, connection_id: str):
        return stored_record if connection_id == "cx-1" else None

    async def fake_update_connection(db, connection_id: str, updates: Dict[str, Any]):
        if connection_id != "cx-1":
            return None
        updated = dict(stored_record)
        updated.update(updates)
        updated["updated_at"] = datetime.now(timezone.utc)
        return updated

    async def fake_delete_connection(db, connection_id: str):
        return dict(stored_record) if connection_id == "cx-1" else None

    _patch_async_session(monkeypatch)
    monkeypatch.setattr(repo_module, "db_get_connection", fake_get_connection)
    monkeypatch.setattr(repo_module, "db_update_connection", fake_update_connection)
    monkeypatch.setattr(repo_module, "db_delete_connection", fake_delete_connection)

    repo = ERPConnectionRepository()

    fetched = await repo.get("cx-1")
    assert fetched and fetched.connection_id == "cx-1"

    updated = await repo.update("cx-1", {"status": "active"})
    assert updated and updated.status == "active"

    deleted = await repo.delete("cx-1")
    assert deleted and deleted.connection_id == "cx-1"

    missing = await repo.get("missing")
    assert missing is None
