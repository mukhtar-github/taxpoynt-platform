import pytest
from fastapi import FastAPI
from httpx import AsyncClient

from platform.backend.api_gateway.api_versions.v1.si_endpoints.onboarding_endpoints import (
    OnboardingEndpointsV1,
)
from platform.backend.api_gateway.role_routing.models import HTTPRoutingContext
from platform.backend.core_platform.data_management import db_async
from platform.backend.core_platform.data_management.db_async import (
    get_async_session,
    init_async_engine,
)
from platform.backend.core_platform.data_management.models.base import Base
from platform.backend.core_platform.data_management.repositories.onboarding_state_repo_async import (
    OnboardingStateRepositoryAsync,
)
from platform.backend.core_platform.authentication.role_manager import PlatformRole


class StubRoleDetector:
    def __init__(self, context):
        self._context = context

    async def detect_role_context(self, request):
        return self._context


class StubPermissionGuard:
    async def check_endpoint_permission(self, context, path, method):
        return True


class StubMessageRouter:
    async def route_message(self, *args, **kwargs):
        return {"success": True}


def _si_context() -> HTTPRoutingContext:
    ctx = HTTPRoutingContext(user_id="si-user-wizard", platform_role=PlatformRole.SYSTEM_INTEGRATOR)
    ctx.primary_role = PlatformRole.SYSTEM_INTEGRATOR
    ctx.metadata["service_package"] = "si"
    return ctx


@pytest.fixture
async def wizard_client(tmp_path, monkeypatch):
    db_path = tmp_path / "wizard_endpoints.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    db_async._async_engine = None
    db_async._session_maker = None

    engine = init_async_engine()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    role_detector = StubRoleDetector(_si_context())
    permission_guard = StubPermissionGuard()
    message_router = StubMessageRouter()

    app = FastAPI()
    endpoints = OnboardingEndpointsV1(role_detector, permission_guard, message_router)
    app.include_router(endpoints.router, prefix="/api/v1/si")

    async with AsyncClient(app=app, base_url="http://testserver") as client:
        yield client

    await engine.dispose()


@pytest.mark.asyncio
async def test_company_profile_endpoint_persists_metadata(wizard_client: AsyncClient):
    payload = {
        "company_name": "Example Ltd",
        "contact_email": "ops@example.com",
        "industry": "Technology",
    }

    response = await wizard_client.put(
        "/api/v1/si/onboarding/wizard/company-profile", json=payload
    )

    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["data"]["metadata"]["wizard"]["company_profile"]["company_name"] == "Example Ltd"

    async for session in get_async_session():
        repo = OnboardingStateRepositoryAsync(session)
        record = await repo.fetch_state("si-user-wizard")
        assert record is not None
        wizard = record.state_metadata.get("wizard", {})
        assert wizard["company_profile"]["industry"] == "Technology"
        break


@pytest.mark.asyncio
async def test_service_selection_endpoint_preserves_profile(wizard_client: AsyncClient):
    await wizard_client.put(
        "/api/v1/si/onboarding/wizard/company-profile",
        json={"company_name": "Example Ltd"},
    )

    response = await wizard_client.put(
        "/api/v1/si/onboarding/wizard/service-selection",
        json={
            "selected_package": "hybrid",
            "integration_targets": ["odoo", "sap"],
        },
    )

    assert response.status_code == 200
    body = response.json()
    wizard_data = body["data"]["metadata"]["wizard"]
    assert wizard_data["company_profile"]["company_name"] == "Example Ltd"
    assert wizard_data["service_focus"]["integration_targets"] == ["odoo", "sap"]
    assert body["data"]["current_step"] == "company-profile"


@pytest.mark.asyncio
async def test_service_selection_idempotency_returns_cached_response(wizard_client: AsyncClient):
    payload = {
        "selected_package": "si",
        "integration_targets": ["odoo"],
    }

    headers = {"x-idempotency-key": "wizard-key-123"}
    first = await wizard_client.put(
        "/api/v1/si/onboarding/wizard/service-selection", json=payload, headers=headers
    )
    second = await wizard_client.put(
        "/api/v1/si/onboarding/wizard/service-selection", json=payload, headers=headers
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"] == second.json()["data"]


@pytest.mark.asyncio
async def test_company_profile_requires_company_name(wizard_client: AsyncClient):
    response = await wizard_client.put(
        "/api/v1/si/onboarding/wizard/company-profile",
        json={"industry": "Finance"},
    )

    assert response.status_code == 422
