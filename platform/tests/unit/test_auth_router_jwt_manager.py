import os
import sys
from pathlib import Path
import uuid as uuidlib
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure backend modules are importable
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def create_app_with_auth_router():
    # Defer imports to ensure env vars are set first
    from api_gateway.role_routing.auth_router import (
        create_auth_router,
    )
    from api_gateway.role_routing.role_detector import HTTPRoleDetector
    from api_gateway.role_routing.permission_guard import APIPermissionGuard
    from core_platform.messaging.message_router import MessageRouter

    app = FastAPI()
    # Minimal stubs for router factory; router does not use these for register/login
    role_detector = HTTPRoleDetector()
    permission_guard = APIPermissionGuard  # not used by router construction
    message_router = MessageRouter()  # not used in these endpoints
    router = create_auth_router(role_detector, permission_guard, message_router)
    # Router already has prefix "/auth"; include without extra prefix
    app.include_router(router)
    return app


def test_register_and_verify_token_with_jwt_manager(tmp_path, monkeypatch):
    # Ensure development mode so jwt_manager can generate a secret without env
    monkeypatch.setenv("ENVIRONMENT", "development")
    # Point sqlite DB to a temp file to avoid polluting repo
    db_file = tmp_path / "taxpoynt_auth.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")

    app = create_app_with_auth_router()
    client = TestClient(app)

    # Perform registration (produces access token using jwt_manager)
    payload = {
        "email": "user.test@example.com",
        "password": "Password123!",
        "first_name": "User",
        "last_name": "Test",
        "service_package": "si",
        "business_name": "TestCo",
        "terms_accepted": True,
        "privacy_accepted": True
    }
    r = client.post("/auth/register", json=payload)
    assert r.status_code == 200, r.text
    data = r.json()
    token = data["access_token"]
    user = data["user"]

    # Verify token using centralized manager
    from core_platform.security import get_jwt_manager

    jwt_manager = get_jwt_manager()
    claims = jwt_manager.verify_token(token)
    assert claims.get("sub") == user["id"]
    assert claims.get("email") == payload["email"]

    # Verify /auth/me works with the token and returns user info
    r2 = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200, r2.text
    me = r2.json()
    assert me["id"] == user["id"]
    assert me["email"] == payload["email"]
