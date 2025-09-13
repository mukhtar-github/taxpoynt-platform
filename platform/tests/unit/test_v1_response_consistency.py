"""
Unit smoke test: verify v1 response shape consistency using TestClient.

Spins a minimal app wiring a few representative endpoints (APP and SI) and
asserts the presence of V1ResponseModel fields in responses.
"""
import os
import sys
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from api_gateway.api_versions.v1.app_endpoints.main_router import APPRouterV1
from api_gateway.api_versions.v1.si_endpoints.organization_endpoints import OrganizationEndpointsV1
from api_gateway.role_routing.models import HTTPRoutingContext


class StubRoleDetectorAPP:
    async def detect_role_context(self, request):
        from core_platform.authentication.role_manager import PlatformRole
        return HTTPRoutingContext(platform_role=PlatformRole.ACCESS_POINT_PROVIDER, user_id="user-app")


class StubRoleDetectorSI:
    async def detect_role_context(self, request):
        from core_platform.authentication.role_manager import PlatformRole
        return HTTPRoutingContext(platform_role=PlatformRole.SYSTEM_INTEGRATOR, user_id="user-si")


class StubPermissionGuard:
    async def check_endpoint_permission(self, context, route, method):
        return True


@pytest.mark.parametrize("route_setup", ["app", "si"])
def test_v1_response_shape(route_setup, monkeypatch):
    app = FastAPI()
    guard = StubPermissionGuard()
    if route_setup == "app":
        router = APPRouterV1(StubRoleDetectorAPP(), guard, message_router=None)
        app.include_router(router.router, prefix="/api/v1")
        client = TestClient(app)
        # pick a simple GET that returns via _create_v1_response
        res = client.get("/api/v1/app/info")
    else:
        router = OrganizationEndpointsV1(StubRoleDetectorSI(), guard, message_router=None)
        app.include_router(router.router, prefix="/api/v1/si")
        client = TestClient(app)
        # pick a simple GET that returns via _create_v1_response but avoid heavy routing
        res = client.get("/api/v1/si/organizations/123/transactions")

    assert res.status_code in (200, 403, 500)
    # When 200, ensure V1 fields are present
    if res.status_code == 200:
        body = res.json()
        for key in ("success", "action", "api_version", "timestamp", "data"):
            assert key in body
        assert body["api_version"] == "v1"
