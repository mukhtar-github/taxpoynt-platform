import uuid
from typing import Dict, Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _registration_payload(email: str) -> Dict[str, str | bool]:
    return {
        "email": email,
        "password": "Str0ngPass!",
        "first_name": "Pilot",
        "last_name": "User",
        "service_package": "si",
        "business_name": "Pilot Systems",
        "terms_accepted": True,
        "privacy_accepted": True,
    }


@pytest.fixture
def registration_client(monkeypatch, tmp_path):
    def _make_client(extra_env: Optional[Dict[str, str]] = None) -> TestClient:
        extra_env = extra_env or {}

        for var in [
            "BUSINESS_EMAIL_ALLOWLIST",
            "BUSINESS_EMAIL_ALLOWLIST_PATH",
            "BUSINESS_EMAIL_DENYLIST",
            "BUSINESS_EMAIL_DENYLIST_PATH",
            "BUSINESS_EMAIL_POLICY_MODE",
        ]:
            monkeypatch.delenv(var, raising=False)

        db_file = tmp_path / f"auth_{uuid.uuid4().hex}.db"
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")

        for key, value in extra_env.items():
            if value is None:
                monkeypatch.delenv(key, raising=False)
            else:
                monkeypatch.setenv(key, value)

        from api_gateway.role_routing import auth_router

        async def _fake_send_verification_email(*_args, **_kwargs):
            return None

        monkeypatch.setattr(auth_router, "_send_verification_email", _fake_send_verification_email)

        app = FastAPI()

        from api_gateway.role_routing.role_detector import HTTPRoleDetector
        from api_gateway.role_routing.permission_guard import APIPermissionGuard
        from core_platform.messaging.message_router import MessageRouter

        router = auth_router.create_auth_router(
            HTTPRoleDetector(),
            APIPermissionGuard,
            MessageRouter(),
        )
        app.include_router(router)

        return TestClient(app)

    return _make_client


def test_register_blocks_free_email_domain(registration_client):
    client = registration_client()
    response = client.post(
        "/auth/register",
        json=_registration_payload(f"founder-{uuid.uuid4().hex}@gmail.com"),
    )
    assert response.status_code == 400, response.json()
    assert response.json()["detail"] == "Please use a business email address to sign up."


def test_allowlist_overrides_free_email_block(registration_client):
    client = registration_client({"BUSINESS_EMAIL_ALLOWLIST": "gmail.com"})
    response = client.post(
        "/auth/register",
        json=_registration_payload(f"pilot-{uuid.uuid4().hex}@gmail.com"),
    )
    assert response.status_code == 200, response.json()
    payload = response.json()
    assert payload.get("status") == "pending"


def test_disabled_policy_allows_free_domain(registration_client):
    client = registration_client({"BUSINESS_EMAIL_POLICY_MODE": "disabled"})
    response = client.post(
        "/auth/register",
        json=_registration_payload(f"pilot-{uuid.uuid4().hex}@gmail.com"),
    )
    assert response.status_code == 200, response.json()
    payload = response.json()
    assert payload.get("status") == "pending"


def test_allowlist_only_requires_configured_domain(registration_client):
    client = registration_client(
        {
            "BUSINESS_EMAIL_POLICY_MODE": "allowlist_only",
            "BUSINESS_EMAIL_ALLOWLIST": "partner.example",
        }
    )

    rejected = client.post("/auth/register", json=_registration_payload("team@example.com"))
    assert rejected.status_code == 400
    assert rejected.json()["detail"] == "This sign-up requires an approved business email domain."

    accepted = client.post("/auth/register", json=_registration_payload("lead@partner.example"))
    assert accepted.status_code == 200
    assert accepted.json().get("status") == "pending"
