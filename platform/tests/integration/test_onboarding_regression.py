"""
Integration-style regression coverage for onboarding flows.

These tests stitch together the authentication router and the unified
SI onboarding endpoints using lightweight stubs so we can run an
end-to-end sign-up → verification → checklist retrieval scenario
without touching external services.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from api_gateway.api_versions.v1.si_endpoints.onboarding_endpoints import OnboardingEndpointsV1
from api_gateway.role_routing import auth_router as auth_module
from api_gateway.role_routing.auth_router import create_auth_router
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from core_platform.authentication.role_manager import PlatformRole
from core_platform.messaging.message_router import ServiceRole


class StubRoleDetector:
    """Provide a deterministic routing context for onboarding requests."""

    def __init__(self, factory: Optional[Callable[[], HTTPRoutingContext]] = None) -> None:
        self._factory = factory or (lambda: _si_context())
        self.calls: list[str] = []

    def set_context_factory(self, factory: Callable[[], HTTPRoutingContext]) -> None:
        self._factory = factory

    async def detect_role_context(self, request) -> HTTPRoutingContext:  # type: ignore[override]
        self.calls.append(str(request.url.path))
        return self._factory()


class StubPermissionGuard:
    """Permit every onboarding request while recording invocations."""

    def __init__(self) -> None:
        self.calls: list[tuple[Any, str, str]] = []

    async def check_endpoint_permission(self, context, path, method):  # noqa: D401
        self.calls.append((context.user_id, path, method))
        return True


class RecordingMessageRouter:
    """Capture routed operations and replay canned responses."""

    def __init__(self) -> None:
        self.stubbed: Dict[str, Dict[str, Any]] = {}
        self.operations: list[Dict[str, Any]] = []
        self.analytics_events: list[Dict[str, Any]] = []

    def set_response(self, operation: str, response: Dict[str, Any]) -> None:
        self.stubbed[operation] = response

    def clear_operation_log(self) -> None:
        self.operations.clear()

    async def route_message(  # type: ignore[override]
        self,
        service_role: ServiceRole,
        operation: str,
        payload: Dict[str, Any],
        **_: Any,
    ) -> Dict[str, Any]:
        if service_role == ServiceRole.ANALYTICS:
            self.analytics_events.append({"operation": operation, "payload": payload})
            return {"success": True}

        self.operations.append(
            {
                "service_role": service_role,
                "operation": operation,
                "payload": payload,
            }
        )
        return self.stubbed.get(operation, {"success": True, "data": {}})


def _si_context(
    user_id: str = "si-user-123",
    organization_id: str = "org-001",
    service_package: str = "si",
) -> HTTPRoutingContext:
    ctx = HTTPRoutingContext(
        user_id=user_id,
        organization_id=organization_id,
        platform_role=PlatformRole.SYSTEM_INTEGRATOR,
    )
    ctx.primary_role = PlatformRole.SYSTEM_INTEGRATOR
    ctx.metadata["service_package"] = service_package
    return ctx


@pytest.fixture()
def onboarding_regression_app(monkeypatch, tmp_path):
    """Create a FastAPI app with both auth and onboarding routers wired."""
    monkeypatch.setenv("ENVIRONMENT", "development")
    db_path = tmp_path / "auth_regression.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")

    sent_codes: Dict[str, str] = {}
    message_router = RecordingMessageRouter()

    async def fake_send_verification_email(recipient: str, code: str, first_name: Optional[str] = None) -> None:
        sent_codes[recipient.lower()] = code

    async def fake_record_onboarding_status(*_: Any, **__: Any) -> None:
        return None

    monkeypatch.setattr(auth_module, "_send_verification_email", fake_send_verification_email)
    monkeypatch.setattr(auth_module, "_record_onboarding_account_status", fake_record_onboarding_status)

    app = FastAPI()
    auth = create_auth_router(HTTPRoleDetector(), APIPermissionGuard, message_router)
    app.include_router(auth)

    role_detector = StubRoleDetector()
    permission_guard = StubPermissionGuard()
    onboarding = OnboardingEndpointsV1(
        role_detector=role_detector,
        permission_guard=permission_guard,
        message_router=message_router,
    )
    app.include_router(onboarding.router, prefix="/api/v1/si")

    client = TestClient(app)
    return {
        "client": client,
        "message_router": message_router,
        "sent_codes": sent_codes,
        "role_detector": role_detector,
        "onboarding": onboarding,
    }


def test_onboarding_flow_covers_signup_wizard_and_checklist(onboarding_regression_app):
    """AAA: ensure sign-up → verification → checklist retrieval works end-to-end."""
    client: TestClient = onboarding_regression_app["client"]
    message_router: RecordingMessageRouter = onboarding_regression_app["message_router"]
    sent_codes: Dict[str, str] = onboarding_regression_app["sent_codes"]
    role_detector: StubRoleDetector = onboarding_regression_app["role_detector"]

    # Arrange
    email = f"regression-{uuid.uuid4().hex}@example.com"
    registration_payload = {
        "email": email,
        "password": "StrongPassw0rd!",
        "first_name": "Ada",
        "last_name": "Onyeka",
        "service_package": "si",
        "business_name": "Onboarding QA Ltd",
        "terms_accepted": True,
        "privacy_accepted": True,
    }

    state_payload = {
        "user_id": "placeholder",  # filled once we have the user id
        "current_step": "system-connectivity",
        "completed_steps": ["service-selection", "company-profile"],
        "has_started": True,
        "is_complete": False,
        "last_active_date": "2024-04-10T09:15:00Z",
        "metadata": {
            "service_package": "si",
            "expected_steps": [
                "service-selection",
                "company-profile",
                "system-connectivity",
                "review",
                "launch",
            ],
            "wizard": {"company_profile": {"company_name": "Onboarding QA Ltd"}},
        },
        "created_at": "2024-04-09T08:00:00Z",
        "updated_at": "2024-04-10T09:15:00Z",
        "terms_accepted_at": "2024-04-09T08:00:00Z",
        "verified_at": "2024-04-09T08:05:00Z",
    }
    checklist_payload = {
        "user_id": "placeholder",
        "service_package": "si",
        "current_phase": "integration-readiness",
        "phases": [
            {
                "id": "service-foundation",
                "title": "Service foundation",
                "description": "Confirm profile details.",
                "status": "complete",
                "steps": [
                    {
                        "id": "service-selection",
                        "canonical_id": "service-selection",
                        "title": "Service selection",
                        "status": "complete",
                        "completed": True,
                    },
                    {
                        "id": "company-profile",
                        "canonical_id": "company-profile",
                        "title": "Company profile",
                        "status": "complete",
                        "completed": True,
                    },
                ],
            },
            {
                "id": "integration-readiness",
                "title": "Integration readiness",
                "description": "Connect systems and finalize configuration.",
                "status": "in_progress",
                "steps": [
                    {
                        "id": "system-connectivity",
                        "canonical_id": "system-connectivity",
                        "title": "Connect systems",
                        "status": "in_progress",
                        "completed": False,
                    }
                ],
            },
        ],
        "summary": {
            "completed_phases": ["service-foundation"],
            "remaining_phases": ["integration-readiness"],
            "completion_percentage": 45,
        },
        "updated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    }

    # Act
    register_response = client.post("/auth/register", json=registration_payload)
    user_payload = register_response.json()["user"]
    verification_code = sent_codes[email.lower()]

    verify_response = client.post(
        "/auth/verify-email",
        json={
            "email": email,
            "code": verification_code,
            "service_package": "si",
            "terms_accepted": True,
            "privacy_accepted": True,
        },
    )

    message_router.clear_operation_log()
    role_detector.set_context_factory(
        lambda: _si_context(user_id=user_payload["id"], organization_id=user_payload["organization"]["id"])
    )

    state_payload["user_id"] = user_payload["id"]
    state_payload["metadata"]["wizard"]["company_profile"]["company_name"] = user_payload["organization"]["name"]
    checklist_payload["user_id"] = user_payload["id"]

    message_router.set_response("get_onboarding_state", {"success": True, "data": state_payload})
    message_router.set_response("get_onboarding_checklist", {"success": True, "data": checklist_payload})

    state_response = client.get(
        "/api/v1/si/onboarding/state",
        headers={
            "X-User-Id": user_payload["id"],
            "X-Organization-Id": user_payload["organization"]["id"],
        },
    )
    checklist_response = client.get(
        "/api/v1/si/onboarding/checklist",
        headers={
            "X-User-Id": user_payload["id"],
            "X-Organization-Id": user_payload["organization"]["id"],
        },
    )

    # Assert
    assert register_response.status_code == 200
    assert verify_response.status_code == 200

    assert state_response.status_code == 200
    assert state_response.json()["data"]["current_step"] == "system-connectivity"
    assert state_response.json()["data"]["metadata"]["expected_steps"][0] == "service-selection"

    assert checklist_response.status_code == 200
    assert checklist_response.json()["data"]["summary"]["completion_percentage"] == 45

    analytics_events = {
        recorded_event["eventType"]
        for batch in message_router.analytics_events
        for recorded_event in batch["payload"]["events"]
    }
    assert analytics_events == {"si_onboarding.email_verified", "si_onboarding.terms_confirmed"}

    routed_operations = [call["operation"] for call in message_router.operations]
    assert routed_operations == ["get_onboarding_state", "get_onboarding_checklist"]


def test_legacy_nine_step_names_redirect_to_canonical_flow(onboarding_regression_app):
    """AAA: ensure legacy nine-step identifiers map onto the new canonical flow."""
    onboarding: OnboardingEndpointsV1 = onboarding_regression_app["onboarding"]

    # Arrange
    legacy_steps = {
        "organization_setup": "service-selection",
        "compliance_verification": "company-profile",
        "erp_configuration": "system-connectivity",
    }

    # Act
    canonicalised = {step: onboarding._canonicalize_step(step) for step in legacy_steps}

    # Assert
    assert canonicalised == legacy_steps
    assert onboarding._canonicalize_step("review") == "review"
