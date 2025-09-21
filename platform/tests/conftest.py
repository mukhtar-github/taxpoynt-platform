"""
Pytest configuration for TaxPoynt Platform tests.

Sets up import path for backend modules and enables router validation env vars
so individual tests can run without manual shell exports.
"""
import os
import sys
import importlib
import importlib.machinery
import types
from pathlib import Path

# Ensure backend modules are importable (api_gateway, core_platform, etc.)
TESTS_DIR = Path(__file__).resolve().parents[0]
PROJECT_ROOT = TESTS_DIR.parents[1]
PLATFORM_DIR = PROJECT_ROOT / "platform"
BACKEND_DIR = PLATFORM_DIR / "backend"

# Extend stdlib platform module into a package so project imports coexist
stdlib_platform = importlib.import_module("platform")
platform_package = types.ModuleType("platform")
platform_package.__dict__.update(stdlib_platform.__dict__)
platform_package.__path__ = [str(PLATFORM_DIR)]
platform_package.__file__ = getattr(stdlib_platform, "__file__", None)
spec = importlib.machinery.ModuleSpec(
    name="platform",
    loader=None,
    origin=getattr(stdlib_platform, "__file__", "stdlib"),
    is_package=True,
)
spec.submodule_search_locations = [str(PLATFORM_DIR)]
platform_package.__spec__ = spec
sys.modules["platform"] = platform_package

for path in (PROJECT_ROOT, PLATFORM_DIR, BACKEND_DIR):
    path_str = str(path)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)


def pytest_configure():
    # Favor development defaults for local test runs
    os.environ.setdefault("ENVIRONMENT", "development")

    # Enable router validation by default in tests
    os.environ.setdefault("ROUTER_VALIDATE_ON_STARTUP", "true")
    os.environ.setdefault("ROUTER_FAIL_FAST_ON_STARTUP", "true")
    os.environ.setdefault("ROUTER_STRICT_OPS", "true")
