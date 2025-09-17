import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timezone

import pytest

BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.mark.asyncio
async def test_unified_payment_transactions_via_router(tmp_path):
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select

    # Use a file-backed sqlite DB so sessions share state
    db_path = tmp_path / "unified_tx.db"
    url = f"sqlite+aiosqlite:///{db_path}"

    # Initialize the global async engine used by callbacks
    from core_platform.data_management.db_async import init_async_engine, get_async_session
    from core_platform.data_management.models.base import BaseModel
    from core_platform.data_management.models.payment import (
        PaymentConnection, PaymentConnectionStatus, PaymentProvider, PaymentTransaction, PaymentStatus
    )

    engine = init_async_engine(url)
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    # Seed one connection + some transactions
    async for db in get_async_session():
        assert isinstance(db, AsyncSession)
        conn = PaymentConnection(
            si_id="00000000-0000-0000-0000-000000000001",
            provider=PaymentProvider.PAYSTACK,
            status=PaymentConnectionStatus.CONNECTED,
            provider_connection_id="demo-paystack-conn",
        )
        db.add(conn)
        await db.commit()
        await db.refresh(conn)

        for i in range(3):
            txn = PaymentTransaction(
                connection_id=conn.id,
                provider=conn.provider,
                provider_transaction_id=f"paystack-txn-{i+1}",
                amount=str(1000 * (i + 1)),
                currency="NGN",
                status=PaymentStatus.COMPLETED,
                occurred_at=datetime.now(timezone.utc),
            )
            db.add(txn)
        await db.commit()

    # Route message through SI services
    from core_platform.messaging.message_router import MessageRouter, ServiceRole
    from si_services import SIServiceRegistry

    router = MessageRouter()
    reg = SIServiceRegistry(router)
    await reg.initialize_services()

    res = await router.route_message(
        service_role=ServiceRole.SYSTEM_INTEGRATOR,
        operation="get_unified_payment_transactions",
        payload={"si_id": "00000000-0000-0000-0000-000000000001", "limit": 50}
    )

    assert res.get("success") is True
    data = res.get("data") or {}
    items = data.get("items") or []
    assert len(items) >= 3

