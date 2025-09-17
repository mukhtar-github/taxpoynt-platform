import sys
from pathlib import Path
import pytest

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.mark.asyncio
async def test_reconciliation_repo_lifecycle():
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from core_platform.data_management.models.base import BaseModel
    from core_platform.data_management.repositories.reconciliation_repo_async import save_config, get_config, update_config

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    async with SessionLocal() as db:
        si = "00000000-0000-0000-0000-000000000001"
        # Save
        first = await save_config(db, si_id=si, organization_id=None, config={"rules": [1]})
        assert first["id"]

        # Get
        got = await get_config(db, si_id=si, organization_id=None)
        assert got and got["config"]["rules"] == [1]

        # Update
        upd = await update_config(db, si_id=si, organization_id=None, updates={"rules": [1, 2]})
        assert upd and upd["config"]["rules"] == [1, 2]

