import sys
from pathlib import Path
import pytest

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.mark.asyncio
async def test_payment_repo_crud_and_webhooks():
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from core_platform.data_management.models.base import BaseModel
    from core_platform.data_management.repositories.payment_repo_async import (
        create_connection, get_connection, list_connections, update_connection, delete_connection, register_webhook, list_webhooks
    )

    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    async with SessionLocal() as db:
        # Create connection
        created = await create_connection(
            db,
            si_id="00000000-0000-0000-0000-000000000001",
            organization_id=None,
            provider="paystack",
            provider_connection_id="pc-1",
            status="pending",
            metadata={"env": "sandbox"},
        )
        assert created["id"]

        # Get
        got = await get_connection(db, created["id"])
        assert got and got["provider"] == "paystack"

        # List
        lst = await list_connections(db, si_id="00000000-0000-0000-0000-000000000001")
        assert lst["count"] == 1

        # Update
        upd = await update_connection(db, created["id"], {"status": "connected", "account_reference": "acct-1"})
        assert upd and upd["status"] == "connected"

        # Webhook
        wh = await register_webhook(
            db,
            si_id="00000000-0000-0000-0000-000000000001",
            provider="paystack",
            endpoint_url="https://example.test/webhook",
            connection_id=created["id"],
            secret="sec",
            metadata={"note": "test"},
        )
        assert wh["endpoint_url"].startswith("https://")

        wh_list = await list_webhooks(db, si_id="00000000-0000-0000-0000-000000000001", provider="paystack")
        assert wh_list["count"] == 1

        # Delete
        ok = await delete_connection(db, created["id"])
        assert ok is True

