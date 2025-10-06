import pytest

from platform.backend.app_services.onboarding_management.app_onboarding_service import (
    APPOnboardingService,
)
from sqlalchemy.ext.asyncio import AsyncEngine

from platform.backend.core_platform.data_management import db_async
from platform.backend.core_platform.data_management.db_async import get_async_session, init_async_engine
from platform.backend.core_platform.data_management.repositories.onboarding_state_repo_async import (
    OnboardingStateRepositoryAsync,
)
from platform.backend.core_platform.data_management.models.base import Base


@pytest.mark.asyncio
async def test_app_onboarding_service_persists_state(tmp_path, monkeypatch):
    db_path = tmp_path / "app_onboarding_state.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite+aiosqlite:///{db_path}")
    db_async._async_engine = None
    db_async._session_maker = None

    engine: AsyncEngine = init_async_engine()
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    service = APPOnboardingService()

    # Initialize state
    state_resp = await service.handle_operation(
        "get_onboarding_state",
        {"user_id": "user-123", "api_version": "v1"},
    )
    assert state_resp["success"] is True

    # Complete a step and ensure persistence reflects it
    await service.handle_operation(
        "complete_onboarding_step",
        {
            "user_id": "user-123",
            "step_name": "business_verification",
            "metadata": {"note": "docs uploaded"},
        },
    )

    async for session in get_async_session():
        repo = OnboardingStateRepositoryAsync(session)
        record = await repo.fetch_state("user-123")
        assert record is not None
        assert "business_verification" in (record.completed_steps or [])
        assert record.state_metadata.get("business_verification_status") == "completed"
        break

    # Verify analytics data includes progress metadata
    state_resp = await service.handle_operation(
        "get_onboarding_state",
        {"user_id": "user-123", "api_version": "v1"},
    )
    progress = state_resp["data"]["progress"]
    assert progress["completed"] >= 1
    assert progress["current_step"] in service.default_steps["app"]
