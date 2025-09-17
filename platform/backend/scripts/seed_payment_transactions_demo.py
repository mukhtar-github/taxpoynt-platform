#!/usr/bin/env python3
"""
Seed Demo Payment Transactions
=============================

Seeds payment_connections and payment_transactions with demo data for testing
unified payment transaction endpoints.

Usage:
  python platform/backend/scripts/seed_payment_transactions_demo.py \
    --si-id 00000000-0000-0000-0000-000000000001 \
    --provider paystack \
    --count 20

Requires DATABASE_URL to be set. Creates tables if missing.
"""
from __future__ import annotations

import os
import sys
import argparse
import asyncio
from datetime import datetime, timezone, timedelta
from pathlib import Path
import random

# Ensure backend modules are importable
BACKEND_DIR = Path(__file__).resolve().parents[2]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


async def seed_demo(si_id: str, provider: str, count: int, org_id: str | None) -> None:
    from sqlalchemy.ext.asyncio import async_sessionmaker
    from core_platform.data_management.db_async import init_async_engine
    from core_platform.data_management.models.base import BaseModel
    from core_platform.data_management.models.payment import (
        PaymentProvider,
        PaymentConnection,
        PaymentConnectionStatus,
        PaymentTransaction,
        PaymentStatus,
    )
    from sqlalchemy import select

    engine = init_async_engine()
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)

    # Ensure tables exist
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    async with SessionLocal() as db:
        # Find or create a connection
        row = (
            await db.execute(
                select(PaymentConnection).where(
                    PaymentConnection.si_id == si_id,
                    PaymentConnection.provider == PaymentProvider(provider),
                )
            )
        ).scalars().first()

        if not row:
            row = PaymentConnection(
                si_id=si_id,
                organization_id=org_id,
                provider=PaymentProvider(provider),
                status=PaymentConnectionStatus.CONNECTED,
                provider_connection_id=f"demo-{provider}-conn",
                account_reference=f"acct-{random.randint(1000,9999)}",
                connection_metadata={"seeded": True},
            )
            db.add(row)
            await db.commit()
            await db.refresh(row)

        # Insert transactions
        base_time = datetime.now(timezone.utc)
        for i in range(count):
            txn = PaymentTransaction(
                connection_id=row.id,
                provider=row.provider,
                provider_transaction_id=f"{provider}-txn-{i+1:04d}",
                amount=str(round(random.uniform(1000, 500000), 2)),
                currency="NGN",
                status=PaymentStatus.COMPLETED,
                occurred_at=base_time - timedelta(minutes=i * 5),
                transaction_metadata={"seeded": True, "note": f"demo {i+1}"},
            )
            db.add(txn)
        await db.commit()

    print(f"✅ Seeded {count} transactions for provider={provider} si_id={si_id}")


async def main():
    parser = argparse.ArgumentParser(description="Seed demo payment transactions")
    parser.add_argument("--si-id", required=True, help="System Integrator ID (UUID)")
    parser.add_argument("--provider", default="paystack", choices=[
        "paystack", "moniepoint", "opay", "palmpay", "interswitch", "flutterwave", "stripe"
    ])
    parser.add_argument("--count", type=int, default=20, help="Number of transactions to seed")
    parser.add_argument("--organization-id", default=None, help="Organization UUID (optional)")
    args = parser.parse_args()

    if not os.getenv("DATABASE_URL"):
        print("ERROR: DATABASE_URL is not set.")
        sys.exit(1)

    await seed_demo(args.si_id, args.provider, args.count, args.organization_id)


if __name__ == "__main__":
    asyncio.run(main())

