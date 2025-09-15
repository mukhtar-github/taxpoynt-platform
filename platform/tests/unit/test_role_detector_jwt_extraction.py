import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

# Ensure backend modules are importable
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def build_app_for_role_detector():
    from api_gateway.role_routing.role_detector import HTTPRoleDetector
    detector = HTTPRoleDetector()
    app = FastAPI()

    @app.get("/inspect")
    async def inspect(request: Request):
        ctx = await detector.detect_role_context(request)
        return {
            "user_id": ctx.user_id,
            "organization_id": ctx.organization_id,
            "tenant_id": ctx.tenant_id,
            "is_authenticated": ctx.is_authenticated,
        }

    return app


def test_role_detector_with_valid_and_invalid_tokens(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")

    from core_platform.security import get_jwt_manager

    app = build_app_for_role_detector()
    client = TestClient(app)

    jwt_manager = get_jwt_manager()
    token = jwt_manager.create_access_token({
        "user_id": "detector-user-1",
        "email": "detector@example.com",
        "role": "system_integrator",
        "organization_id": "org-abc",
        "permissions": []
    })

    # Valid token path
    r1 = client.get("/inspect", headers={"Authorization": f"Bearer {token}"})
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["is_authenticated"] is True
    assert d1["user_id"] == "detector-user-1"
    assert d1["organization_id"] == "org-abc"

    # Invalid token path
    r2 = client.get("/inspect", headers={"Authorization": "Bearer not-a-valid-token"})
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["is_authenticated"] is False
    assert d2["user_id"] is None
