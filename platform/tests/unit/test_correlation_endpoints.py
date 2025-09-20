import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
import importlib.util

# Ensure backend modules are importable
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def _load_module(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader, f"Failed to load module spec for {name}"
    spec.loader.exec_module(mod)  # type: ignore
    return mod


def test_correlation_get_list_hybrid_role(monkeypatch):
    from api_gateway.role_routing.models import HTTPRoutingContext
    from core_platform.authentication.role_manager import PlatformRole
    from core_platform.data_management.db_async import get_async_session

    # Stub role detector and permission guard
    class StubRoleDetector:
        async def detect_role_context(self, request):
            return HTTPRoutingContext(
                user_id="u-1",
                organization_id="11111111-1111-1111-1111-111111111111",
                platform_role=PlatformRole.HYBRID,
            )

    class StubPermissionGuard:
        async def check_endpoint_permission(self, context, path, method):
            return True

    # Stub correlation service
    class _Item:
        def __init__(self, org_id: str):
            self.organization_id = org_id

        def to_dict(self):
            return {
                "id": "1",
                "correlation_id": "COR-ABC123",
                "organization_id": "11111111-1111-1111-1111-111111111111",
                "si_invoice_id": "INV-1",
                "app_submission_id": None,
                "irn": "IRN-1",
                "current_status": "si_generated",
                "last_status_update": "2024-01-01T00:00:00Z",
                "invoice_number": "INV-1",
                "total_amount": 1.0,
                "currency": "NGN",
                "customer_name": "Test",
                "processing_duration": 0,
                "is_complete": False,
                "is_successful": False,
                "retry_count": "0",
                "firs_status": None,
            }

    class StubService:
        def __init__(self, db):
            pass

        async def get_organization_correlations(self, organization_id, status=None, limit=50, offset=0):
            return [_Item(str(organization_id))]

    # Load module and monkeypatch service
    module_path = BACKEND_DIR / "api_gateway" / "api_versions" / "v1" / "hybrid_endpoints" / "correlation_endpoints.py"
    mod = _load_module(module_path, "correlation_endpoints_mod")
    monkeypatch.setattr(mod, "SIAPPCorrelationService", StubService)

    # Fake DB dependency
    class _FakeDB:
        pass

    async def _fake_session():
        yield _FakeDB()

    app = FastAPI()
    app.dependency_overrides[get_async_session] = _fake_session
    router = mod.create_correlation_router(StubRoleDetector(), StubPermissionGuard())
    app.include_router(router, prefix="/api/v1/hybrid")

    client = TestClient(app)
    r = client.get("/api/v1/hybrid/correlations")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total_count"] == 1
    assert body["correlations"][0]["correlation_id"] == "COR-ABC123"


def test_correlation_app_received_app_role(monkeypatch):
    from api_gateway.role_routing.models import HTTPRoutingContext
    from core_platform.authentication.role_manager import PlatformRole
    from core_platform.data_management.db_async import get_async_session

    class StubRoleDetector:
        async def detect_role_context(self, request):
            return HTTPRoutingContext(
                user_id="u-1",
                organization_id="11111111-1111-1111-1111-111111111111",
                platform_role=PlatformRole.ACCESS_POINT_PROVIDER,
            )

    class StubPermissionGuard:
        async def check_endpoint_permission(self, context, path, method):
            return True

    class StubService:
        def __init__(self, db):
            pass

        async def update_app_received(self, irn: str, app_submission_id: str, metadata=None) -> bool:
            return irn == "IRN-OK" and app_submission_id.startswith("APP-")

    module_path = BACKEND_DIR / "api_gateway" / "api_versions" / "v1" / "hybrid_endpoints" / "correlation_endpoints.py"
    mod = _load_module(module_path, "correlation_endpoints_mod2")
    monkeypatch.setattr(mod, "SIAPPCorrelationService", StubService)

    class _FakeDB:
        pass

    async def _fake_session():
        yield _FakeDB()

    app = FastAPI()
    app.dependency_overrides[get_async_session] = _fake_session
    router = mod.create_correlation_router(StubRoleDetector(), StubPermissionGuard())
    app.include_router(router, prefix="/api/v1/app")

    client = TestClient(app)
    r = client.post(
        "/api/v1/app/correlations/irn/IRN-OK/app-received",
        json={"status": "app_received", "app_submission_id": "APP-123"},
    )
    assert r.status_code == 200, r.text
    assert r.json()["success"] is True

