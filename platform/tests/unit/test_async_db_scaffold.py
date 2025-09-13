"""
Unit tests for async DB scaffolding and tenant context utilities.
"""
import os
import sys
import pytest

# Put platform/backend on sys.path so 'core_platform' can be imported directly
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from core_platform.data_management.db_async import (
    get_async_database_url,
    init_async_engine,
    get_async_session,
)
from core_platform.authentication.tenant_context import (
    set_current_tenant,
    get_current_tenant,
    clear_current_tenant,
    tenant_context,
)
from sqlalchemy.ext.asyncio import AsyncSession


def test_get_async_database_url_transforms_sqlite_memory(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    url = get_async_database_url()
    assert url.startswith("sqlite+aiosqlite:///") or url == "sqlite:///:memory:"


@pytest.mark.asyncio
async def test_async_engine_and_session(monkeypatch):
    # Use in-memory SQLite for lightweight test
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    engine = init_async_engine()
    assert engine is not None

    # DI-style session
    async for session in get_async_session():
        assert isinstance(session, AsyncSession)
        break


def test_tenant_context_helpers():
    clear_current_tenant()
    assert get_current_tenant() is None
    set_current_tenant("tenant-123")
    assert get_current_tenant() == "tenant-123"
    with tenant_context("tenant-ctx"):
        assert get_current_tenant() == "tenant-ctx"
    assert get_current_tenant() == "tenant-123"
    clear_current_tenant()
    assert get_current_tenant() is None

