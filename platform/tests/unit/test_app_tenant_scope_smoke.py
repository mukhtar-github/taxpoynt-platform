import sys
from pathlib import Path
from fastapi import FastAPI, Depends
from fastapi.testclient import TestClient

# Ensure backend modules are importable
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def test_app_tenant_scope_dependency_sets_context():
    from api_gateway.dependencies.tenant import make_tenant_scope_dependency
    from api_gateway.role_routing.models import HTTPRoutingContext
    from core_platform.authentication.tenant_context import get_current_tenant

    app = FastAPI()

    # Stub role guard that returns a context with an org id
    async def stub_require_app_role():
        return HTTPRoutingContext(user_id="u1", organization_id="org-123")

    tenant_scope = make_tenant_scope_dependency(stub_require_app_role)

    @app.get("/api/v1/app/smoke", dependencies=[Depends(tenant_scope)])
    async def smoke():
        return {"tenant": get_current_tenant()}

    client = TestClient(app)
    r = client.get("/api/v1/app/smoke")
    assert r.status_code == 200
    assert r.json()["tenant"] == "org-123"

