"""
Async DB Scaffolding
====================

Lightweight helpers to initialize an SQLAlchemy AsyncEngine and yield
AsyncSession instances for FastAPI dependency injection, without changing
existing sync code paths. This is scaffolding only — no behavioral changes.

Usage (FastAPI dependency):

    from core_platform.data_management.db_async import get_async_session

    async def handler(db: AsyncSession = Depends(get_async_session)):
        ...

Environment:
- DATABASE_URL (sync or async) — e.g.,
  - Postgres sync: postgresql://user:pass@host:5432/db
  - Postgres async: postgresql+asyncpg://user:pass@host:5432/db
  - SQLite sync: sqlite:///./app.db
  - SQLite async: sqlite+aiosqlite:///./app.db

If a sync URL is provided, it will be transformed to the appropriate async
driver automatically.
"""
from __future__ import annotations

import os
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_async_engine: Optional[AsyncEngine] = None
_session_maker: Optional[async_sessionmaker[AsyncSession]] = None


def _normalize_to_async_url(url: str) -> str:
    """Convert a sync DATABASE_URL to an async-capable URL if needed.

    - postgresql:// → postgresql+asyncpg://
    - postgres://   → postgresql+asyncpg:// (Heroku-style)
    - sqlite:///    → sqlite+aiosqlite:///
    - Already async (contains '+') → returned unchanged
    """
    if "+" in url:
        return url
    lower = url.lower()
    if lower.startswith("postgres://"):
        return "postgresql+asyncpg://" + url.split("://", 1)[1]
    if lower.startswith("postgresql://"):
        return "postgresql+asyncpg://" + url.split("://", 1)[1]
    if lower.startswith("sqlite:///"):
        return "sqlite+aiosqlite://" + url.split(":///", 1)[1]
    return url


def get_async_database_url() -> str:
    """Return an async driver URL suitable for SQLAlchemy AsyncEngine.

    Reads DATABASE_URL and transforms it to async form if necessary.
    Falls back to an in-memory SQLite URL for development if unset.
    """
    raw = os.getenv("DATABASE_URL") or "sqlite:///:memory:"
    return _normalize_to_async_url(raw)


def init_async_engine(url: Optional[str] = None, echo: bool = False) -> AsyncEngine:
    """Initialize (or return existing) AsyncEngine and sessionmaker.

    This is idempotent — the first call creates global engine/sessionmaker;
    subsequent calls return the existing engine.
    """
    global _async_engine, _session_maker
    if _async_engine is not None and _session_maker is not None:
        return _async_engine

    db_url = _normalize_to_async_url(url) if url else get_async_database_url()
    _async_engine = create_async_engine(db_url, echo=echo, future=True)
    _session_maker = async_sessionmaker(
        bind=_async_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )
    return _async_engine


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an AsyncSession.

    It initializes the async engine on first use in-process.
    """
    global _session_maker
    if _session_maker is None:
        init_async_engine()
    assert _session_maker is not None
    async with _session_maker() as session:  # type: ignore[call-arg]
        yield session


__all__ = [
    "AsyncEngine",
    "AsyncSession",
    "get_async_database_url",
    "init_async_engine",
    "get_async_session",
]

