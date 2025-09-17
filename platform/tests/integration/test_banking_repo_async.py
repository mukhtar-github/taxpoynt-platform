import os
import sys
import asyncio
from pathlib import Path

import pytest

# Ensure backend modules are importable
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.mark.asyncio
async def test_banking_repo_crud_cycle():
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from core_platform.data_management.models.base import BaseModel
    from core_platform.data_management.repositories.banking_repo_async import (
        create_banking_connection,
        get_banking_connection,
        list_banking_connections,
        update_banking_connection,
        delete_banking_connection,
    )

    # In-memory async SQLite
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    async with SessionLocal() as db:
        # Create
        created = await create_banking_connection(
            db,
            si_id="00000000-0000-0000-0000-000000000001",
            organization_id=None,
            provider="mono",
            provider_connection_id="pc_123",
            status="pending",
            metadata={"env": "sandbox"},
        )
        await db.commit()
        assert created["id"]

        # Get
        got = await get_banking_connection(db, created["id"])
        assert got and got["provider"] == "mono"

        # List
        listed = await list_banking_connections(db, si_id="00000000-0000-0000-0000-000000000001")
        assert listed["count"] == 1

        # Update
        updated = await update_banking_connection(db, created["id"], {"status": "connected"})
        await db.commit()
        assert updated and updated["status"] == "connected"

        # Delete
        ok = await delete_banking_connection(db, created["id"])
        await db.commit()
        assert ok

        # Verify deletion
        got2 = await get_banking_connection(db, created["id"])
        assert got2 is None

