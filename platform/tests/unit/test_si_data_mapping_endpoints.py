"""Unit coverage for SI ERP data-mapping endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Tuple
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api_gateway.api_versions.v1.si_endpoints.business_endpoints.erp_endpoints import (
    create_erp_router,
)
from api_gateway.role_routing.models import HTTPRoutingContext
from core_platform.authentication.role_manager import PlatformRole


TEST_USER_ID = "si-user-001"
TEST_ORG_ID = "c9c1c6b8-34d6-4cbf-a7a3-3c5c9fe64d12"


class StubRoleDetector:
    """Always returns the seeded SI context."""

    def __init__(self) -> None:
        ctx = HTTPRoutingContext(user_id=TEST_USER_ID, platform_role=PlatformRole.SYSTEM_INTEGRATOR)
        ctx.primary_role = PlatformRole.SYSTEM_INTEGRATOR
        ctx.organization_id = TEST_ORG_ID
        ctx.metadata["service_package"] = "si"
        self._context = ctx

    async def detect_role_context(self, request) -> HTTPRoutingContext:
        return self._context


class StubPermissionGuard:
    """Permit all requests while tracking invocations if needed."""

    async def check_endpoint_permission(self, context, path, method) -> bool:
        return True


class StubMessageRouter:
    """Message router placeholder for endpoints that do not route messages."""

    async def route_message(self, *_, **__) -> Dict[str, Any]:
        return {"success": True}


class StubOnboardingService:
    """Minimal in-memory onboarding service for mapping persistence."""

    def __init__(self) -> None:
        self.calls: List[Tuple[str, Dict[str, Any]]] = []
        self.state: Dict[str, Any] = {
            "user_id": TEST_USER_ID,
            "service_package": "si",
            "current_step": "system-connectivity",
            "completed_steps": [],
            "metadata": {},
        }

    async def handle_operation(self, operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        self.calls.append((operation, payload))
        if operation == "get_onboarding_state":
            return {"success": True, "data": self.state}
        if operation == "update_onboarding_state":
            onboarding_data = payload.get("onboarding_data") or {}
            if "current_step" in onboarding_data:
                self.state["current_step"] = onboarding_data["current_step"]
            if "completed_steps" in onboarding_data:
                self.state["completed_steps"] = onboarding_data["completed_steps"]
            metadata = onboarding_data.get("metadata")
            if metadata is not None:
                # store defensive copy so later mutations in tests don't leak
                self.state["metadata"] = {**metadata}
            return {"success": True, "data": self.state}
        raise AssertionError(f"Unsupported onboarding operation requested: {operation}")


def _build_app(onboarding_service: StubOnboardingService) -> TestClient:
    role_detector = StubRoleDetector()
    permission_guard = StubPermissionGuard()
    message_router = StubMessageRouter()

    fastapi_app = FastAPI()
    erp_router = create_erp_router(
        role_detector=role_detector,
        permission_guard=permission_guard,
        message_router=message_router,
        onboarding_service=onboarding_service,
    )
    fastapi_app.include_router(erp_router, prefix="/api/v1/si/business")

    return TestClient(fastapi_app)


def _sample_rules_for_required_fields() -> List[Dict[str, Any]]:
    return [
        {"id": "rule-invoice-number", "sourceField": "name", "targetField": "invoice_number", "transformation": {"type": "direct"}},
        {"id": "rule-invoice-date", "sourceField": "invoice_date", "targetField": "invoice_date", "transformation": {"type": "direct"}},
        {"id": "rule-supplier-tin", "sourceField": "company_id.vat", "targetField": "supplier_tin", "transformation": {"type": "direct"}},
        {"id": "rule-line-items", "sourceField": "invoice_line_ids", "targetField": "line_items", "transformation": {"type": "direct"}},
        {"id": "rule-total-amount", "sourceField": "amount_total", "targetField": "total_amount", "transformation": {"type": "direct"}},
        {"id": "rule-currency", "sourceField": "currency_id.name", "targetField": "currency", "transformation": {"type": "direct"}},
    ]


def test_validate_mapping_success() -> None:
    onboarding_service = StubOnboardingService()
    client = _build_app(onboarding_service)

    payload = {
        "system_id": "odoo",
        "organization_id": TEST_ORG_ID,
        "mapping_rules": [
            {"id": "rule-invoice-number", "sourceField": "name", "targetField": "invoice_number", "transformation": {"type": "direct"}},
            {"id": "rule-invoice-date", "sourceField": "invoice_date", "targetField": "invoice_date", "transformation": {"type": "direct"}},
        ],
        "firs_schema": [
            {"id": "invoice_number", "required": True},
            {"id": "invoice_date", "required": True},
        ],
    }

    response = client.post("/api/v1/si/business/erp/data-mapping/validate", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["preview_data"]["mapped_fields"]["invoice_number"] == "name"
    assert body["preview_data"]["validated_targets"] == ["invoice_date", "invoice_number"]


def test_validate_mapping_reports_missing_required_field() -> None:
    onboarding_service = StubOnboardingService()
    client = _build_app(onboarding_service)

    payload = {
        "system_id": "odoo",
        "mapping_rules": [
            {"id": "rule-invoice-number", "sourceField": "name", "targetField": "invoice_number", "transformation": {"type": "direct"}},
        ],
        "firs_schema": [
            {"id": "invoice_number", "required": True},
            {"id": "invoice_date", "required": True},
        ],
    }

    response = client.post("/api/v1/si/business/erp/data-mapping/validate", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert "invoice_date" in body["errors"]
    assert "Required field missing mapping." in body["errors"]["invoice_date"]


def test_save_and_retrieve_mapping_round_trip() -> None:
    onboarding_service = StubOnboardingService()
    client = _build_app(onboarding_service)

    save_payload = {
        "system_id": "odoo",
        "organization_id": TEST_ORG_ID,
        "mapping_rules": _sample_rules_for_required_fields(),
    }

    save_response = client.post("/api/v1/si/business/erp/data-mapping/save", json=save_payload)
    assert save_response.status_code == 200
    save_body = save_response.json()
    assert save_body["success"] is True
    assert save_body["system_id"] == "odoo"
    assert save_body["organization_id"] == TEST_ORG_ID

    fetch_response = client.get(f"/api/v1/si/business/erp/data-mapping/{TEST_ORG_ID}/odoo")
    assert fetch_response.status_code == 200
    fetch_body = fetch_response.json()
    assert fetch_body["success"] is True
    assert len(fetch_body["mapping_rules"]) == len(_sample_rules_for_required_fields())
