import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from platform.backend.core_platform.data_management.models.base import Base
from platform.backend.core_platform.data_management.repositories.onboarding_state_repo_async import (
    OnboardingStateRepositoryAsync,
)


@pytest_asyncio.fixture
async def async_session(tmp_path):
    db_path = tmp_path / "onboarding_repo.db"
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}")
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)

    SessionLocal = sessionmaker(
        bind=engine, expire_on_commit=False, class_=AsyncSession
    )

    async with SessionLocal() as session:
        yield session

    await engine.dispose()


@pytest.mark.asyncio
async def test_ensure_state_initializes_defaults(async_session: AsyncSession):
    repo = OnboardingStateRepositoryAsync(async_session)

    record = await repo.ensure_state("user-ensure-1", "si")

    assert record.service_package == "si"
    assert record.current_step == "service-selection"
    metadata = record.state_metadata
    assert metadata["expected_steps"][0] == "service-selection"
    assert "wizard" not in metadata


@pytest.mark.asyncio
async def test_upsert_wizard_section_persists_profile(async_session: AsyncSession):
    repo = OnboardingStateRepositoryAsync(async_session)
    await repo.ensure_state("user-profile-1", "si")

    await repo.upsert_wizard_section(
        "user-profile-1",
        "si",
        section="company_profile",
        payload={"company_name": "Example Ltd"},
        current_step="company-profile",
    )

    record = await repo.fetch_state("user-profile-1")
    assert record is not None
    assert record.current_step == "company-profile"
    wizard = record.state_metadata.get("wizard", {})
    assert wizard["company_profile"]["company_name"] == "Example Ltd"


@pytest.mark.asyncio
async def test_upsert_wizard_section_merges_sections(async_session: AsyncSession):
    repo = OnboardingStateRepositoryAsync(async_session)
    await repo.ensure_state("user-merge-1", "si")

    await repo.upsert_wizard_section(
        "user-merge-1",
        "si",
        section="company_profile",
        payload={"company_name": "Example Ltd"},
        current_step="company-profile",
    )

    await repo.upsert_wizard_section(
        "user-merge-1",
        "si",
        section="service_focus",
        payload={"selected_package": "hybrid"},
        current_step="service-selection",
    )

    record = await repo.fetch_state("user-merge-1")
    wizard = record.state_metadata.get("wizard", {})
    assert wizard["company_profile"]["company_name"] == "Example Ltd"
    assert wizard["service_focus"]["selected_package"] == "hybrid"


@pytest.mark.asyncio
async def test_upsert_wizard_section_rejects_unknown_section(async_session: AsyncSession):
    repo = OnboardingStateRepositoryAsync(async_session)
    await repo.ensure_state("user-bad-section", "si")

    with pytest.raises(ValueError):
        await repo.upsert_wizard_section(
            "user-bad-section",
            "si",
            section="unsupported",
            payload={},
            current_step="service-selection",
        )
