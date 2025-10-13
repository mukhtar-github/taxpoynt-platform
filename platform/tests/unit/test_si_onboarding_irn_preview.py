from datetime import datetime, timezone

from si_services.onboarding_management.onboarding_service import SIOnboardingService


def test_onboarding_irn_preview_uses_metadata(monkeypatch):
    service = SIOnboardingService()
    issued = datetime(2024, 3, 9, 12, 0, tzinfo=timezone.utc)
    monkeypatch.setattr(service, "_utc_now", lambda: issued)

    metadata = {
        "company_profile": {"firs_service_id": "svc 01"},
        "invoice_preview": {"invoice_number": "inv-123", "issued_on": "2024-03-09"},
    }

    result = service._ensure_metadata_consistency(metadata, "si")

    assert result["irn_preview"] == "INV123-SVC01000-20240309"


def test_onboarding_irn_preview_uses_defaults(monkeypatch):
    service = SIOnboardingService()
    now = datetime(2024, 1, 5, 8, 30, tzinfo=timezone.utc)
    monkeypatch.setattr(service, "_utc_now", lambda: now)

    result = service._ensure_metadata_consistency({}, "si")

    assert result["irn_preview"] == "0001-SI000000-20240105"
