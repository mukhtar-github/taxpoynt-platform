"""
Unit test to enforce standardized DB DI in FastAPI handlers.
Ensures API gateway endpoint modules do not import deprecated sync
session dependencies for request handling.
"""
import os
import sys


def test_no_deprecated_sync_db_dependency_in_handlers():
    # Ensure repo root/backend on sys.path
    CURRENT_DIR = os.path.dirname(__file__)
    BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "backend"))
    if BACKEND_DIR not in sys.path:
        sys.path.insert(0, BACKEND_DIR)

    root = os.path.join(BACKEND_DIR, "api_gateway", "api_versions")
    assert os.path.isdir(root), f"Missing api_versions directory: {root}"

    banned_imports = [
        "from core_platform.data_management.connection_pool import get_db_session",
        "from core_platform.data_management.database_init import get_db_session",
    ]

    offenders = []
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            path = os.path.join(dirpath, fn)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                for needle in banned_imports:
                    if needle in content:
                        offenders.append((path, needle))

    assert not offenders, (
        "Found deprecated DB DI in API handlers: "
        + ", ".join([f"{p} -> {n}" for p, n in offenders])
    )

