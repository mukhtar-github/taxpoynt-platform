"""Guard enforcement tests for APP transmission endpoints."""
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient


# Ensure backend modules are importable when running from repo root
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def test_app_transmission_routes_require_app_role():
    from api_gateway.role_routing.models import HTTPRoutingContext
    from core_platform.authentication.role_manager import PlatformRole
    from api_gateway.api_versions.v1.app_endpoints.transmission_management_endpoints import (
        TransmissionManagementEndpointsV1,
    )

    class StubRoleDetector:
        async def detect_role_context(self, request):
            # Return a context without the APP role to trigger the guard
            return HTTPRoutingContext(user_id="user-123", platform_role=PlatformRole.SYSTEM_INTEGRATOR)

    class StubPermissionGuard:
        async def check_endpoint_permission(self, context, path, method):
            return True

    class StubMessageRouter:
        async def route_message(self, *args, **kwargs):
            return {}

    endpoints = TransmissionManagementEndpointsV1(
        role_detector=StubRoleDetector(),
        permission_guard=StubPermissionGuard(),
        message_router=StubMessageRouter(),
    )

    app = FastAPI()
    app.include_router(endpoints.router)

    client = TestClient(app)
    response = client.get("/transmission/available-batches")

    assert response.status_code == 403
    assert response.json()["detail"] == "Access Point Provider role required for v1 API"

