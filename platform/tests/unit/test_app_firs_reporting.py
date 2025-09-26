"""Unit tests for APP FIRS reporting-oriented callbacks."""

import asyncio
import os
import sys
from typing import Any, Dict

import pytest

# Ensure backend modules can be imported
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from core_platform.messaging.message_router import MessageRouter
from platform.backend.app_services import APPServiceRegistry


class StubHttpClient:
    def __init__(self) -> None:
        self._transmissions = [
            {
                "id": "SUB-001",
                "irn": "IRN-001",
                "status": "submitted",
                "timestamp": "2025-01-01T10:00:00Z",
                "status_code": "200",
                "message": "submitted successfully",
            },
            {
                "id": "SUB-002",
                "irn": "IRN-002",
                "status": "accepted",
                "timestamp": "2025-01-02T12:30:00Z",
                "status_code": "202",
                "message": "accepted",
            },
        ]

    async def lookup_transmit_by_tin(self, tin: str) -> Dict[str, Any]:  # pragma: no cover - thin wrapper
        return {"success": True, "data": self._transmissions}

    async def transmit_pull(self) -> Dict[str, Any]:
        return {"success": True, "data": self._transmissions}

    async def update_invoice(self, irn: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "success": True,
            "status_code": 200,
            "data": {"irn": irn, "status": "updated", "payload": payload},
        }


class StubResourceCache:
    def __init__(self) -> None:
        self.cached_resources = ["invoice-types", "vat-exemptions"]

    async def get_resources(self) -> Dict[str, Any]:  # pragma: no cover - thin wrapper
        return {
            "invoice-types": ["standard", "credit-note"],
            "vat-exemptions": ["export", "zero-rated"],
        }


def _build_firs_callback(http_client: Any, resource_cache: Any) -> Any:
    registry = APPServiceRegistry(MessageRouter())
    firs_service = {
        "http_client": http_client,
        "resource_cache": resource_cache,
        "auth_handler": None,
        "certificate_store": None,
    }
    return registry._create_firs_callback(firs_service)


@pytest.mark.asyncio
async def test_list_firs_submissions_shapes():
    callback = _build_firs_callback(StubHttpClient(), StubResourceCache())
    payload = {
        "filters": {"status": "accepted"},
        "pagination": {"limit": 1, "offset": 0},
    }
    result = await callback("list_firs_submissions", payload)
    assert result["success"] is True
    data = result["data"]
    assert data["count"] == 1
    assert data["items"][0]["status"] == "accepted"
    assert "summary" in data and "statusCounts" in data["summary"]


@pytest.mark.asyncio
async def test_generate_firs_report_summary():
    callback = _build_firs_callback(StubHttpClient(), StubResourceCache())
    result = await callback("generate_firs_report", {"filters": {"status": "submitted"}})
    assert result["success"] is True
    report = result["data"]
    assert report["total"] >= 1
    assert "statusBreakdown" in report
    assert "dailyCounts" in report


@pytest.mark.asyncio
async def test_get_firs_validation_rules_metadata():
    callback = _build_firs_callback(StubHttpClient(), StubResourceCache())
    result = await callback("get_firs_validation_rules", {})
    assert result["success"] is True
    data = result["data"]
    assert "resources" in data
    assert set(data["metadata"]["resource_keys"]) == {"invoice-types", "vat-exemptions"}


@pytest.mark.asyncio
async def test_update_firs_invoice_response_shape():
    callback = _build_firs_callback(StubHttpClient(), StubResourceCache())
    payload = {
        "invoice_update": {
            "irn": "IRN-001",
            "update_data": {"note": "Updated contact"},
        }
    }
    result = await callback("update_firs_invoice", payload)
    assert result["success"] is True
    data = result["data"]
    assert data["irn"] == "IRN-001"
    assert data["status_code"] == 200
    assert data["firs_response"]["status"] == "updated"
