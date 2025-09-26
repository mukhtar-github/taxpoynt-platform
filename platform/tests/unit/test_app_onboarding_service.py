import json

import pytest

from platform.backend.app_services.onboarding_management.app_onboarding_service import (
    APPOnboardingService,
)


@pytest.mark.asyncio
async def test_app_onboarding_service_persists_state(tmp_path, monkeypatch):
    store_path = tmp_path / "app_onboarding_state.json"
    monkeypatch.setenv("APP_ONBOARDING_STATE_STORE", str(store_path))

    service = APPOnboardingService()

    # Initialize state
    state_resp = await service.handle_operation(
        "get_onboarding_state",
        {"user_id": "user-123", "api_version": "v1"},
    )
    assert state_resp["success"] is True
    assert store_path.exists()

    # Complete a step and ensure persistence reflects it
    await service.handle_operation(
        "complete_onboarding_step",
        {
            "user_id": "user-123",
            "step_name": "business_verification",
            "metadata": {"note": "docs uploaded"},
        },
    )

    data = json.loads(store_path.read_text())
    assert "user-123" in data
    persisted = data["user-123"]
    assert "business_verification" in persisted["completed_steps"]

    # Verify analytics data includes progress metadata
    state_resp = await service.handle_operation(
        "get_onboarding_state",
        {"user_id": "user-123", "api_version": "v1"},
    )
    progress = state_resp["data"]["progress"]
    assert progress["completed"] >= 1
    assert progress["current_step"] in service.default_steps["app"]
