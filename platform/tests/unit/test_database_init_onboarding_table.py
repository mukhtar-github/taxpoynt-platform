"""Tests for ensuring onboarding_states table existence during DB init."""

import pytest
from sqlalchemy import create_engine, inspect

from platform.backend.core_platform.data_management.database_init import (
    _ensure_onboarding_table,
)
from platform.backend.core_platform.data_management.models.onboarding_state import (
    OnboardingStateORM,
)


def _create_engine(url: str):
    return create_engine(url)


@pytest.mark.parametrize("database_url_provider", [
    lambda tmp: "sqlite:///:memory:",
    lambda tmp: f"sqlite:///{tmp/'onboarding_test.db'}",
])
def test_ensure_onboarding_table_creates_table(database_url_provider, tmp_path):
    """Fallback helper should create onboarding_states table when missing."""
    engine = _create_engine(database_url_provider(tmp_path))

    inspector = inspect(engine)
    table_name = OnboardingStateORM.__tablename__
    if inspector.has_table(table_name):  # pragma: no cover - defensive cleanup
        OnboardingStateORM.__table__.drop(bind=engine)

    created = _ensure_onboarding_table(engine)
    assert created is True
    assert inspect(engine).has_table(table_name)

    # Second invocation should be a no-op but succeed
    assert _ensure_onboarding_table(engine) is True

    engine.dispose()
