import os
import sys
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

# Ensure backend modules are importable
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def test_role_authenticator_populates_routing_context(monkeypatch):
    # Ensure jwt_manager can self-configure
    monkeypatch.setenv("ENVIRONMENT", "development")

    from api_gateway.middleware.role_authenticator import RoleAuthenticator
    from core_platform.authentication.role_manager import RoleManager
    from api_gateway.role_routing.role_detector import HTTPRoleDetector
    from core_platform.security import get_jwt_manager

    app = FastAPI()

    # Add a simple route that echoes routing context
    @app.get("/protected")
    async def protected(request: Request):
        ctx = getattr(request.state, "routing_context", None)
        if not ctx:
            return {"has_context": False}
        return {
            "has_context": True,
            "user_id": ctx.user_id,
            "is_authenticated": ctx.is_authenticated,
        }

    # Wire middleware (jwt_secret_key arg is retained for compatibility)
    app.add_middleware(
        RoleAuthenticator,
        role_manager=RoleManager({}),
        role_detector=HTTPRoleDetector(),
        jwt_secret_key="dev-secret",
    )

    client = TestClient(app)

    # Create a valid platform token
    jwt_manager = get_jwt_manager()
    access_token = jwt_manager.create_access_token({
        "user_id": "test-user-123",
        "email": "test@example.com",
        "role": "system_integrator",
        "organization_id": None,
        "permissions": []
    })

    r = client.get("/protected", headers={"Authorization": f"Bearer {access_token}"})
    assert r.status_code == 200
    body = r.json()
    assert body["has_context"] is True
    assert body["is_authenticated"] is True
    assert body["user_id"] == "test-user-123"
