from typing import Any, Dict

import pytest

from core_platform.services.kyc.submit_kyc_command import (
    SubmitKYCCommand,
    SubmitKYCCommandConfig,
)


class FakeRecord:
    def __init__(self) -> None:
        self.state_metadata: Dict[str, Any] = {}
        self.service_package = "si"
        self.updated_at = None
        self.last_active_date = None


class FakeRepo:
    def __init__(self) -> None:
        self.record = FakeRecord()
        self.persist_calls = 0

    async def ensure_state(self, user_id: str, service_package: str) -> FakeRecord:
        return self.record

    async def persist(self, record: FakeRecord) -> FakeRecord:
        self.persist_calls += 1
        return record


@pytest.mark.asyncio
async def test_submit_kyc_command_persists_dojah_metadata(monkeypatch):
    fake_repo = FakeRepo()

    async def session_provider():
        yield object()

    async def fake_fetcher(config: SubmitKYCCommandConfig, params: Dict[str, str]):
        assert params["tin"] == "1234567890"
        return {
            "data": {
                "company_name": "Acme Fintech Ltd",
                "industry": "Finance",
                "status": "active",
                "country": "Nigeria",
                "registered_address": "123 Victoria Island",
                "directors": ["Ade", "Tolu"],
                "employee_count": 25,
                "tin": "1234567890",
                "rc_number": "RC-000111",
            }
        }

    class StubJWTManager:
        def encrypt_sensitive_data(self, value: str) -> str:
            return f"enc::{value}"

    monkeypatch.setattr(
        "core_platform.services.kyc.submit_kyc_command.get_jwt_manager",
        lambda: StubJWTManager(),
    )

    config = SubmitKYCCommandConfig(
        api_key="key",
        app_id=None,
        base_url="https://example.com",
        lookup_path="/mock",
        http_method="GET",
        timeout_seconds=5,
        fallback_country="Nigeria",
    )

    command = SubmitKYCCommand(
        config=config,
        session_provider=session_provider,
        repo_factory=lambda _session: fake_repo,
        fetcher=fake_fetcher,
    )

    await command.execute(
        user_id="user-1",
        service_package="si",
        tin="1234567890",
        rc_number="RC-000111",
        email="founder@example.com",
    )

    assert fake_repo.persist_calls == 1
    metadata = fake_repo.record.state_metadata
    assert metadata["company_profile"]["companyName"] == "Acme Fintech Ltd"
    assert metadata["company_profile"]["country"] == "Nigeria"
    assert metadata["company_profile_details"]["tin"] == "1234567890"
    assert metadata["kyc_records"]["dojah"]["encrypted_payload"].startswith("enc::")
