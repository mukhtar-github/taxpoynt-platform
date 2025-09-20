import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
import importlib.util

# Ensure backend modules are importable
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def test_si_generate_uses_routing_context(monkeypatch):
    """
    Guardrail: SI generate endpoint must use HTTPRoutingContext.organization_id
    (not current_user), and should not crash when org lookup returns None.
    """
    from api_gateway.role_routing.models import HTTPRoutingContext, PlatformRole
    from core_platform.data_management.db_async import get_async_session

    # Stub role detector and permission guard
    class StubRoleDetector:
        async def detect_role_context(self, request):
            return HTTPRoutingContext(
                user_id="u-1",
                organization_id="11111111-1111-1111-1111-111111111111",
                platform_role=PlatformRole.SYSTEM_INTEGRATOR,
            )

    class StubPermissionGuard:
        async def check_endpoint_permission(self, context, path, method):
            return True

    # Monkeypatch generator to capture organization_id
    captured = {}

    class StubGen:
        def __init__(self, db, formatter):
            pass

        async def get_generation_statistics(self):
            return {"invoices_generated": 1}

        async def generate_firs_invoices(self, req):
            captured["org_id"] = str(req.organization_id)
            # Minimal shape expected by endpoint
            from types import SimpleNamespace
            invoice = {
                "irn": "IRN-TEST",
                "invoice_number": "INV-1",
                "customer": {"name": "Test"},
                "total_amount": 1.0,
                "tax_amount": 0.0,
                "currency": "NGN",
                "invoice_date": "2024-01-01",
                "source_data": {"transaction_count": 1},
            }
            return SimpleNamespace(
                success=True,
                invoices=[invoice],
                errors=[],
                warnings=[],
                total_amount=1.0,
            )

    # Pre-seed a stub package path to satisfy absolute imports inside the module
    import types, sys as _sys
    vm_mod = types.ModuleType("api_gateway.api_versions.v1.si_endpoints.version_models")
    try:
        from pydantic import BaseModel
        class _StubV1ResponseModel(BaseModel):
            success: bool = True
            message: str = ""
            data: dict = {}
        vm_mod.V1ResponseModel = _StubV1ResponseModel
    except Exception:
        # Fallback if pydantic missing in test context
        class _StubV1ResponseModel(dict):
            pass
        vm_mod.V1ResponseModel = _StubV1ResponseModel

    # Register minimal package hierarchy in sys.modules
    _sys.modules.setdefault("api_gateway", types.ModuleType("api_gateway"))
    _sys.modules.setdefault("api_gateway.api_versions", types.ModuleType("api_gateway.api_versions"))
    _sys.modules.setdefault("api_gateway.api_versions.v1", types.ModuleType("api_gateway.api_versions.v1"))
    _sys.modules.setdefault("api_gateway.api_versions.v1.si_endpoints", types.ModuleType("api_gateway.api_versions.v1.si_endpoints"))
    _sys.modules["api_gateway.api_versions.v1.si_endpoints.version_models"] = vm_mod

    # Load the router module directly by path to avoid package __init__ side effects
    module_path = (
        BACKEND_DIR
        / "api_gateway"
        / "api_versions"
        / "v1"
        / "si_endpoints"
        / "firs_invoice_endpoints.py"
    )
    spec = importlib.util.spec_from_file_location("firs_invoice_endpoints_mod", str(module_path))
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader, "Failed to load firs_invoice_endpoints module spec"
    spec.loader.exec_module(mod)  # type: ignore
    
    # Monkeypatch generator in the loaded module
    monkeypatch.setattr(mod, "ComprehensiveFIRSInvoiceGenerator", StubGen)

    # Override DB session to avoid real DB calls (org lookup returns None)
    class _FakeResult:
        def scalar_one_or_none(self):
            return None

    class _FakeDB:
        async def execute(self, *args, **kwargs):
            return _FakeResult()

    async def _fake_session():
        yield _FakeDB()

    app = FastAPI()
    app.dependency_overrides[get_async_session] = _fake_session

    router = mod.create_firs_invoice_router(StubRoleDetector(), StubPermissionGuard())
    app.include_router(router, prefix="/api/v1/si")

    client = TestClient(app)
    r = client.post(
        "/api/v1/si/firs/invoices/generate",
        json={
            "transaction_ids": ["sample-1"],
            "invoice_type": "standard",
            "consolidate": False,
            "include_digital_signature": False,
        },
    )

    assert r.status_code == 200, r.text
    assert captured.get("org_id") == "11111111-1111-1111-1111-111111111111"
