"""Unit tests for APP v1 FIRS integration endpoints.

These tests verify that key APP FIRS routes validate input and forward
requests through the message router with the expected payloads while only
requiring mocked dependencies (no live FIRS access).
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api_gateway.api_versions.v1.app_endpoints.firs_integration_endpoints import (
    FIRSIntegrationEndpointsV1,
)
from api_gateway.role_routing.models import HTTPRoutingContext
from core_platform.authentication.role_manager import PlatformRole
from core_platform.messaging.message_router import ServiceRole


class StubRoleDetector:
    """Return an APP routing context for every request."""

    def __init__(self) -> None:
        self.calls = []

    async def detect_role_context(self, request):  # pragma: no cover - simple stub
        self.calls.append(request.url.path)
        return HTTPRoutingContext(
            user_id="app-user-123",
            platform_role=PlatformRole.ACCESS_POINT_PROVIDER,
        )


class StubPermissionGuard:
    """Allow every request while recording invocations."""

    def __init__(self) -> None:
        self.calls = []

    async def check_endpoint_permission(self, context, path, method):  # pragma: no cover - simple stub
        self.calls.append((path, method))
        return True


class StubMessageRouter:
    """Capture route_message calls and return canned responses."""

    def __init__(self) -> None:
        self.calls = []

    async def route_message(self, service_role, operation, payload, source_service=None, **kwargs):
        call = {
            "service_role": service_role,
            "operation": operation,
            "payload": payload,
        }
        self.calls.append(call)
        return {"operation": operation}


@pytest.fixture()
def app_client():
    role_detector = StubRoleDetector()
    permission_guard = StubPermissionGuard()
    message_router = StubMessageRouter()

    app = FastAPI()

    # Instantiate endpoints so we can register dependency overrides.
    endpoints = FIRSIntegrationEndpointsV1(
        role_detector=role_detector,
        permission_guard=permission_guard,
        message_router=message_router,
    )
    app.include_router(endpoints.router, prefix="/api/v1/app")

    async def _stub_context():
        return HTTPRoutingContext(
            user_id="app-user-123",
            platform_role=PlatformRole.ACCESS_POINT_PROVIDER,
        )

    # Override dependency in both global and method-level registrations.
    app.dependency_overrides[FIRSIntegrationEndpointsV1._require_app_role] = _stub_context
    app.dependency_overrides[endpoints._require_app_role] = _stub_context

    client = TestClient(app)
    return client, role_detector, permission_guard, message_router


def test_submit_invoice_to_firs_routes_payload(app_client):
    client, _role_detector, _permission_guard, message_router = app_client

    payload = {"taxpayer_id": "TIN123", "invoice_data": {"amount": 1000}}

    response = client.post("/api/v1/app/firs/invoices/submit", json=payload)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["action"] == "invoice_submitted_to_firs"
    assert body["data"] == {"operation": "submit_invoice_to_firs"}

    assert len(message_router.calls) == 1
    call = message_router.calls[0]
    assert call["service_role"] == ServiceRole.ACCESS_POINT_PROVIDER
    assert call["operation"] == "submit_invoice_to_firs"
    assert call["payload"]["submission_data"]["taxpayer_id"] == "TIN123"
    assert call["payload"]["app_id"] == "app-user-123"


def test_test_firs_connection_routes_credentials(app_client):
    client, _role_detector, _permission_guard, message_router = app_client

    request_payload = {
        "api_key": "example-key",
        "api_secret": "example-secret",
        "environment": "production",
    }

    response = client.post("/api/v1/app/firs/test-connection", json=request_payload)

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["success"] is True
    assert body["action"] == "firs_connection_tested"
    assert body["data"] == {"operation": "test_firs_connection"}

    call = message_router.calls[-1]
    assert call["operation"] == "test_firs_connection"
    assert call["payload"]["credentials"] == request_payload
    assert call["payload"]["app_id"] == "app-user-123"


def test_test_firs_connection_validation_error(app_client):
    client, *_ = app_client

    response = client.post(
        "/api/v1/app/firs/test-connection",
        json={"api_key": "missing-secret"},
    )

    assert response.status_code == 400
    body = response.json()
    assert body["success"] is False
    assert body["error_code"] == "VALIDATION_ERROR"


def test_get_firs_auth_status_routes(app_client):
    client, _role_detector, _permission_guard, message_router = app_client

    response = client.get("/api/v1/app/firs/auth/status")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["action"] == "firs_auth_status_retrieved"
    assert body["data"] == {"operation": "get_firs_auth_status"}

    call = message_router.calls[-1]
    assert call["operation"] == "get_firs_auth_status"
    assert call["payload"]["app_id"] == "app-user-123"
