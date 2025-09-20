"""
Pytest configuration for TaxPoynt Platform tests.

Sets up import path for backend modules and enables router validation env vars
so individual tests can run without manual shell exports.
"""
import os
import sys
from pathlib import Path

# Ensure backend modules are importable (api_gateway, core_platform, etc.)
BACKEND_DIR = Path(__file__).resolve().parents[1] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def pytest_configure():
    # Favor development defaults for local test runs
    os.environ.setdefault("ENVIRONMENT", "development")

    # Enable router validation by default in tests
    os.environ.setdefault("ROUTER_VALIDATE_ON_STARTUP", "true")
    os.environ.setdefault("ROUTER_FAIL_FAST_ON_STARTUP", "true")
    os.environ.setdefault("ROUTER_STRICT_OPS", "true")

