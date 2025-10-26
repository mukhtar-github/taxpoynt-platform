from datetime import datetime, timezone

from si_services.onboarding_management.onboarding_service import (
    SIOnboardingService,
    OnboardingState,
)


def _make_state(
    *,
    current_step: str,
    completed_steps: list[str],
    metadata: dict | None = None,
) -> OnboardingState:
    now = datetime(2024, 1, 1, tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")
    return OnboardingState(
        user_id="user-123",
        service_package="si",
        current_step=current_step,
        completed_steps=completed_steps,
        has_started=True,
        is_complete=False,
        last_active_date=now,
        metadata=metadata or {},
        created_at=now,
        updated_at=now,
    )


def test_checklist_marks_alias_steps_complete_when_canonical_done():
    service = SIOnboardingService()
    state = _make_state(
        current_step="company-profile",
        completed_steps=["service-selection"],
    )

    checklist = service._build_checklist(state, "si")  # type: ignore[attr-defined]
    foundation = checklist["phases"][0]

    assert foundation["id"] == "service-foundation"
    statuses = {step["id"]: step["status"] for step in foundation["steps"]}
    assert statuses["service-selection"] == "complete"
    assert statuses["organization_setup"] == "complete"
    assert foundation["status"] == "in_progress"
    assert checklist["current_phase"] == "service-foundation"


def test_checklist_completes_phases_when_all_steps_done():
    service = SIOnboardingService()
    state = _make_state(
        current_step="launch",
        completed_steps=[
            "service-selection",
            "company-profile",
            "system-connectivity",
            "review",
        ],
    )

    checklist = service._build_checklist(state, "si")  # type: ignore[attr-defined]
    phases = checklist["phases"]

    assert phases[0]["status"] == "complete"
    assert phases[1]["status"] == "complete"
    assert phases[2]["status"] == "in_progress"
    assert checklist["summary"]["completed_phases"] == ["service-foundation", "integration-readiness"]
