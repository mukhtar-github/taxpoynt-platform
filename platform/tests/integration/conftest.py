"""Pytest fixtures for FIRS integration tests.

Provides lightweight configuration and sample data fixtures so the
integration suite can run regardless of external environment setup.
When the FIRS integration flag is disabled, tests will skip before
attempting any network activity.
"""

from __future__ import annotations

import asyncio
import inspect
import os
from typing import Dict, Any

import pytest

from platform.tests.fixtures.firs_sample_data import FIRS_COMPLIANT_INVOICE


def pytest_configure(config: pytest.Config) -> None:
    """Register custom markers used across integration tests."""

    config.addinivalue_line("markers", "integration: marks integration-level tests")
    config.addinivalue_line("markers", "firs: marks tests that exercise FIRS/FRC integration")
    config.addinivalue_line("markers", "external: marks tests that call external services")
    config.addinivalue_line("markers", "slow: marks tests expected to run slowly")


_FIRS_INTEGRATION_ENABLED = os.getenv("ENABLE_FIRS_INTEGRATION_TESTS", "false").lower() in {"1", "true", "yes"}


@pytest.fixture(scope="session")
def firs_test_config() -> Dict[str, Any]:
    """Return runtime toggles for FIRS integration tests.

    Controlled via `ENABLE_FIRS_INTEGRATION_TESTS`; defaults to disabled so the
    suite skips gracefully unless a real environment has been provisioned.
    """

    return {
        "enable_firs_integration": _FIRS_INTEGRATION_ENABLED,
        "base_url": os.getenv("FIRS_TEST_BASE_URL", ""),
        "api_key": os.getenv("FIRS_TEST_API_KEY", ""),
    }


@pytest.fixture(scope="session")
def firs_endpoints(firs_test_config: Dict[str, Any]) -> Dict[str, str]:
    """Derive FIRS endpoint URLs used by integration tests.

    Defaults to placeholder endpoints to avoid None lookups when tests are
    skipped. When a base URL is configured, concrete endpoints are generated.
    """

    base = firs_test_config.get("base_url") or "http://localhost:8000/api/v1/firs"
    return {
        "health_check": f"{base}/health",
        "firs_config": f"{base}/config",
        "submit_invoice": f"{base}/invoices",
    }


@pytest.fixture(scope="session")
def sample_invoice_data() -> Dict[str, Any]:
    """Provide a representative FIRS-compliant invoice payload for tests."""

    return FIRS_COMPLIANT_INVOICE


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    """Skip FIRS integration tests unless explicitly enabled."""

    if _FIRS_INTEGRATION_ENABLED:
        return

    skip_marker = pytest.mark.skip(reason="FIRS integration tests disabled (set ENABLE_FIRS_INTEGRATION_TESTS=true to enable)")
    for item in items:
        if "firs" in item.keywords:
            item.add_marker(skip_marker)


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem: pytest.Function) -> bool | None:
    """Execute async test functions via event loop when integration tests run."""

    if not inspect.iscoroutinefunction(pyfuncitem.obj):
        return None

    loop = asyncio.new_event_loop()
    try:
        asyncio.set_event_loop(loop)
        loop.run_until_complete(pyfuncitem.obj(**pyfuncitem.funcargs))
    finally:
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.close()
        asyncio.set_event_loop(None)
    return True
