import os

import pytest

from platform.backend.app_services.status_management.app_configuration import AppConfigurationStore


@pytest.fixture(autouse=True)
def clear_overrides(monkeypatch):
    monkeypatch.delenv("APP_CONFIGURATION_OVERRIDES", raising=False)


def test_snapshot_includes_environment(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "test")
    store = AppConfigurationStore()
    snapshot = store.snapshot()

    assert snapshot["configuration"]["environment"] == "test"
    assert snapshot["metadata"]["environment"] == "test"


def test_update_configuration_merges_nested(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "production")
    store = AppConfigurationStore()

    result = store.update_config({"messaging": {"ap_outbound_max_age_seconds": 42}}, actor="tester")

    assert result["configuration"]["messaging"]["ap_outbound_max_age_seconds"] == 42
    assert result["metadata"]["updated_by"] == "tester"


def test_invalid_update_raises_value_error():
    store = AppConfigurationStore()

    with pytest.raises(ValueError):
        store.update_config(["not", "a", "dict"])  # type: ignore[arg-type]


def test_overrides_loaded_from_env(monkeypatch):
    monkeypatch.setenv("APP_CONFIGURATION_OVERRIDES", "{\"features\": {\"tracking_alerts\": false}}")
    store = AppConfigurationStore()
    snapshot = store.snapshot()

    assert snapshot["configuration"]["features"]["tracking_alerts"] is False
