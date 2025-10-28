import uuid
from typing import Dict, Any

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api_gateway.role_routing import auth_router as auth_module
from api_gateway.role_routing.auth_router import create_auth_router
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from core_platform.messaging.message_router import ServiceRole


class StubMessageRouter:
    def __init__(self) -> None:
        self.calls: list[tuple[Any, str, Dict[str, Any]]] = []

    async def route_message(self, service_role, operation, payload, **_: Any):
        self.calls.append((service_role, operation, payload))
        return {"success": True}


@pytest.fixture()
def auth_test_app(monkeypatch, tmp_path):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("BUSINESS_EMAIL_POLICY_MODE", "disabled")
    db_path = tmp_path / f"auth_test_{uuid.uuid4().hex}.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    sent_codes: Dict[str, str] = {}

    async def fake_send_verification_email(recipient: str, code: str, first_name: str | None = None):
        sent_codes[recipient.lower()] = code

    async def fake_record_onboarding_status(*args, **kwargs):
        return None

    monkeypatch.setattr(auth_module, "_send_verification_email", fake_send_verification_email)
    monkeypatch.setattr(auth_module, "_record_onboarding_account_status", fake_record_onboarding_status)

    app = FastAPI()
    message_router = StubMessageRouter()
    router = create_auth_router(HTTPRoleDetector(), APIPermissionGuard, message_router)
    app.include_router(router)

    client = TestClient(app)
    return client, message_router, sent_codes


def _registration_payload(email: str) -> Dict[str, Any]:
    return {
        "email": email,
        "password": "SecurePass123!",
        "first_name": "Ayo",
        "last_name": "Okonkwo",
        "service_package": "si",
        "business_name": "Okonkwo Systems",
        "terms_accepted": True,
        "privacy_accepted": True,
    }


def _verify_payload(email: str, code: str, *, terms: bool = True, privacy: bool = True) -> Dict[str, Any]:
    payload = {
        "email": email,
        "code": code,
        "service_package": "si",
    }
    if terms:
        payload["terms_accepted"] = True
    if privacy:
        payload["privacy_accepted"] = True
    return payload


def test_registration_returns_pending_contract(auth_test_app):
    client, message_router, sent_codes = auth_test_app
    email = f"registrant-{uuid.uuid4().hex}@example.com"

    response = client.post("/auth/register", json=_registration_payload(email))
    assert response.status_code == 200
    payload = response.json()

    assert payload["status"] == "pending"
    assert payload["next"] == "/auth/verify-email"
    assert payload["user"]["email"] == email
    assert payload["user"]["is_email_verified"] is False
    assert "onboarding_token" in payload
    assert sent_codes[email.lower()]
    assert not message_router.calls


def test_verify_email_emits_analytics_events(auth_test_app):
    client, message_router, sent_codes = auth_test_app
    email = f"verifier-{uuid.uuid4().hex}@example.com"

    register = client.post("/auth/register", json=_registration_payload(email))
    assert register.status_code == 200
    code = sent_codes[email.lower()]
    message_router.calls.clear()

    verify_response = client.post("/auth/verify-email", json=_verify_payload(email, code))
    assert verify_response.status_code == 200
    body = verify_response.json()

    assert body["access_token"]
    assert body["user"]["email"] == email
    assert body["user"]["is_email_verified"] is True

    assert message_router.calls, "Analytics events should be emitted"
    service_role, operation, payload = message_router.calls[0]
    assert service_role == ServiceRole.ANALYTICS
    assert operation == "process_onboarding_events"

    events = payload["events"]
    event_types = {event["eventType"] for event in events}
    assert "si_onboarding.email_verified" in event_types
    assert "si_onboarding.terms_confirmed" in event_types

    email_event = next(event for event in events if event["eventType"] == "si_onboarding.email_verified")
    terms_event = next(event for event in events if event["eventType"] == "si_onboarding.terms_confirmed")

    assert email_event["stepId"] == "email_verification"
    assert email_event["userRole"] == "si"
    assert email_event["metadata"]["verified_at"]
    assert email_event["metadata"]["terms_accepted"] is True

    assert terms_event["stepId"] == "terms_acceptance"
    assert terms_event["userRole"] == "si"
    assert terms_event["metadata"]["terms_accepted_at"]


def test_verify_email_legacy_payload_without_terms(auth_test_app):
    client, message_router, sent_codes = auth_test_app
    email = f"legacy-{uuid.uuid4().hex}@example.com"

    register = client.post("/auth/register", json=_registration_payload(email))
    assert register.status_code == 200
    code = sent_codes[email.lower()]
    message_router.calls.clear()

    # Legacy clients omit explicit consent flags
    verify_payload = {"email": email, "code": code}
    verify_response = client.post("/auth/verify-email", json=verify_payload)
    assert verify_response.status_code == 200
    data = verify_response.json()
    assert data["user"]["is_email_verified"] is True

    assert message_router.calls
    _, _, payload = message_router.calls[0]
    events = payload["events"]
    assert any(event["eventType"] == "si_onboarding.email_verified" for event in events)
    assert not any(event["eventType"] == "si_onboarding.terms_confirmed" for event in events)
