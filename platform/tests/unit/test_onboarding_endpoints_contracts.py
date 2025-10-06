"""Unit coverage for v1 onboarding routers.

These tests verify that the APP and unified (SI/HYBRID/APP) onboarding
routers surface the service responses using the new v1 response helper and
route messages with the expected service role + payload metadata.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api_gateway.api_versions.v1.app_endpoints.onboarding_endpoints import (
    APPOnboardingEndpointsV1,
)
from api_gateway.api_versions.v1.si_endpoints.onboarding_endpoints import (
    OnboardingEndpointsV1,
)
from api_gateway.role_routing.models import HTTPRoutingContext
from core_platform.authentication.role_manager import PlatformRole
from core_platform.messaging.message_router import ServiceRole


class StubRoleDetector:
    """Role detector that returns a configurable context."""

    def __init__(self, context_factory: Optional[Callable[[], HTTPRoutingContext]] = None) -> None:
        self._context_factory = context_factory or _app_context
        self.calls: list[str] = []

    def set_context_factory(self, factory: Callable[[], HTTPRoutingContext]) -> None:
        self._context_factory = factory

    async def detect_role_context(self, request):
        self.calls.append(str(request.url.path))
        return self._context_factory()


class StubPermissionGuard:
    """Permit every request while recording invocations."""

    def __init__(self) -> None:
        self.calls = []

    async def check_endpoint_permission(self, context, path, method):
        self.calls.append((context.user_id, path, method))
        return True


@dataclass
class RecordedCall:
    service_role: ServiceRole
    operation: str
    payload: Dict[str, Any]


class StubMessageRouter:
    """Capture calls and return preconfigured responses per operation."""

    def __init__(self) -> None:
        self.calls: list[RecordedCall] = []
        self.stubbed: Dict[str, Dict[str, Any]] = {}

    def set_response(self, operation: str, response: Dict[str, Any]) -> None:
        self.stubbed[operation] = response

    async def route_message(
        self,
        service_role: ServiceRole,
        operation: str,
        payload: Dict[str, Any],
        **_: Any,
    ) -> Dict[str, Any]:
        self.calls.append(RecordedCall(service_role=service_role, operation=operation, payload=payload))
        return self.stubbed.get(operation, {"success": True, "data": {"operation": operation}})


def _app_context() -> HTTPRoutingContext:
    ctx = HTTPRoutingContext(user_id="app-user-123", platform_role=PlatformRole.ACCESS_POINT_PROVIDER)
    ctx.primary_role = PlatformRole.ACCESS_POINT_PROVIDER
    ctx.metadata["service_package"] = "app"
    return ctx


def _si_context() -> HTTPRoutingContext:
    ctx = HTTPRoutingContext(user_id="si-user-123", platform_role=PlatformRole.SYSTEM_INTEGRATOR)
    ctx.primary_role = PlatformRole.SYSTEM_INTEGRATOR
    ctx.metadata["service_package"] = "si"
    return ctx


def _hybrid_context() -> HTTPRoutingContext:
    ctx = HTTPRoutingContext(user_id="hybrid-user-456", platform_role=PlatformRole.HYBRID)
    ctx.primary_role = PlatformRole.HYBRID
    ctx.metadata["service_package"] = "hybrid"
    return ctx


@pytest.fixture()
def app_onboarding_client():
    role_detector = StubRoleDetector(_app_context)
    permission_guard = StubPermissionGuard()
    message_router = StubMessageRouter()

    fastapi_app = FastAPI()
    endpoints = APPOnboardingEndpointsV1(
        role_detector=role_detector,
        permission_guard=permission_guard,
        message_router=message_router,
    )
    fastapi_app.include_router(endpoints.router, prefix="/api/v1/app")

    client = TestClient(fastapi_app)
    return client, message_router, permission_guard


@pytest.fixture()
def unified_onboarding_app():
    role_detector = StubRoleDetector(_si_context)
    permission_guard = StubPermissionGuard()
    message_router = StubMessageRouter()

    fastapi_app = FastAPI()
    endpoints = OnboardingEndpointsV1(
        role_detector=role_detector,
        permission_guard=permission_guard,
        message_router=message_router,
    )
    fastapi_app.include_router(endpoints.router, prefix="/api/v1/si")

    client = TestClient(fastapi_app)

    return client, endpoints, message_router, permission_guard, fastapi_app, role_detector


def _set_unified_context(
    role_detector: StubRoleDetector,
    context_factory: Callable[[], HTTPRoutingContext],
) -> None:
    role_detector.set_context_factory(context_factory)


def test_app_get_state_unwraps_service_payload(app_onboarding_client):
    client, message_router, permission_guard = app_onboarding_client
    message_router.set_response(
        "get_onboarding_state",
        {
            "success": True,
            "data": {
                "user_id": "app-user-123",
                "current_step": "service_introduction",
                "completed_steps": [],
            },
        },
    )

    response = client.get("/api/v1/app/onboarding/state")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["action"] == "app_onboarding_state_retrieved"
    assert body["data"]["current_step"] == "service_introduction"
    assert message_router.calls[0].service_role == ServiceRole.ACCESS_POINT_PROVIDER
    assert message_router.calls[0].payload["user_id"] == "app-user-123"
    assert permission_guard.calls[0][1].endswith("/onboarding/state")


def test_app_get_state_failure_propagates_success_flag(app_onboarding_client):
    client, message_router, _permission_guard = app_onboarding_client
    message_router.set_response(
        "get_onboarding_state",
        {
            "success": False,
            "error": "datastore unavailable",
        },
    )

    response = client.get("/api/v1/app/onboarding/state")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is False
    assert body["data"]["error"] == "datastore unavailable"


def test_unified_si_request_routes_to_si_service(unified_onboarding_app):
    client, endpoints, message_router, permission_guard, _app, role_detector = unified_onboarding_app
    _set_unified_context(role_detector, _si_context)

    message_router.set_response(
        "get_onboarding_state",
        {
            "success": True,
            "data": {"user_id": "si-user-123", "service_package": "si"},
        },
    )

    response = client.get("/api/v1/si/onboarding/state")

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["service_package"] == "si"

    call = message_router.calls[0]
    assert call.service_role == ServiceRole.SYSTEM_INTEGRATOR
    assert call.payload["service_package"] == "si"
    assert permission_guard.calls[0][1].endswith("/onboarding/state")


def test_unified_app_request_routes_to_app_service(unified_onboarding_app):
    client, endpoints, message_router, _permission_guard, _app, role_detector = unified_onboarding_app
    _set_unified_context(role_detector, _app_context)

    message_router.set_response(
        "get_onboarding_state",
        {
            "success": True,
            "data": {"user_id": "app-user-123", "service_package": "app"},
        },
    )

    response = client.get("/api/v1/si/onboarding/state")

    assert response.status_code == 200
    call = message_router.calls[0]
    assert call.service_role == ServiceRole.ACCESS_POINT_PROVIDER
    assert call.payload["service_package"] == "app"


def test_unified_hybrid_routes_as_si(unified_onboarding_app):
    client, endpoints, message_router, _permission_guard, _app, role_detector = unified_onboarding_app
    _set_unified_context(role_detector, _hybrid_context)

    message_router.set_response(
        "get_onboarding_state",
        {
            "success": True,
            "data": {"user_id": "hybrid-user-456", "service_package": "hybrid"},
        },
    )

    response = client.get("/api/v1/si/onboarding/state")

    assert response.status_code == 200
    call = message_router.calls[0]
    assert call.service_role == ServiceRole.SYSTEM_INTEGRATOR
    assert call.payload["service_package"] == "hybrid"
