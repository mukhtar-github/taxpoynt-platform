"""
Integration smoke test for SI tenant scope via middleware.
Ensures that hitting a /api/v1/si/* route with ?org_id=... sets
the tenant ContextVar for the duration of the request.
"""
import os
import sys


def test_si_tenant_scope_middleware_sets_context():
    # Put platform/backend on sys.path so imports resolve
    CURRENT_DIR = os.path.dirname(__file__)
    BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "backend"))
    if BACKEND_DIR not in sys.path:
        sys.path.insert(0, BACKEND_DIR)

    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from api_gateway.middleware.tenant_scope import TenantScopeMiddleware
    from core_platform.authentication.tenant_context import get_current_tenant

    app = FastAPI()
    # Apply middleware (now supports /api/v1/si/* as well)
    app.add_middleware(TenantScopeMiddleware)

    @app.get("/api/v1/si/smoke")
    async def smoke():
        return {"tenant": get_current_tenant()}

    client = TestClient(app)
    r = client.get("/api/v1/si/smoke?org_id=org-xyz")
    assert r.status_code == 200
    assert r.json()["tenant"] == "org-xyz"
