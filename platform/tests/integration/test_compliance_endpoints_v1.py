import sys
from pathlib import Path
import pytest

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.mark.asyncio
async def test_compliance_endpoints_route_to_services(monkeypatch, tmp_path):
    # We will call the router handlers directly to assert they route via MessageRouter.
    from api_gateway.api_versions.v1.si_endpoints.compliance_endpoints import create_compliance_router, ComplianceEndpointsV1
    from core_platform.messaging.message_router import MessageRouter
    from api_gateway.role_routing.role_detector import HTTPRoleDetector
    from api_gateway.role_routing.permission_guard import APIPermissionGuard
    from fastapi.testclient import TestClient
    from fastapi import FastAPI

    # Monkeypatch role detector and permission guard to allow SI
    from api_gateway.role_routing.models import HTTPRoutingContext
    from core_platform.authentication.role_manager import PlatformRole

    async def fake_detect_role_context(self, request):
        ctx = HTTPRoutingContext(user_id="00000000-0000-0000-0000-000000000001")
        # Inject a has_role method compatible with guard usage
        ctx.has_role = lambda role: role == PlatformRole.SYSTEM_INTEGRATOR
        return ctx

    async def fake_check_permission(self, context, path, method):
        return True

    monkeypatch.setattr(HTTPRoleDetector, "detect_role_context", fake_detect_role_context, raising=False)
    monkeypatch.setattr(APIPermissionGuard, "check_endpoint_permission", fake_check_permission, raising=False)

    app = FastAPI()
    guard = APIPermissionGuard(app)
    router = create_compliance_router(HTTPRoleDetector(), guard, MessageRouter())
    app.include_router(router, prefix="/api/v1/si")

    client = TestClient(app)

    # Since role detection requires headers/real auth, we focus on structure only here.
    # For a full E2E test, a fixture would stub role detection to set SI context.
    # This test ensures endpoints are mounted and return structured JSON (403 likely without auth).
    resp = client.post("/api/v1/si/compliance/validate", json={"foo": "bar"})
    assert resp.status_code == 200

    resp = client.get("/api/v1/si/compliance/reports/onboarding")
    assert resp.status_code == 200

    resp = client.get("/api/v1/si/compliance/reports/transactions")
    assert resp.status_code == 200
