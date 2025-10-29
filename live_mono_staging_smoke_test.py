#!/usr/bin/env python3
"""
Live Mono Staging Smoke Test
============================

Runs the Mono transaction pipeline end-to-end against a staging deployment.

Prerequisites:
  - Deploy backend to staging with valid Mono sandbox credentials.
  - Ensure DATABASE_URL points to the staging database (async driver).
  - Provide Mono identifiers via environment variables:
      MONO_API_ACCOUNT_ID            → Mono account id used for /transactions API (e.g. acc_123)
      MONO_PROVIDER_ACCOUNT_ID       → Provider account id stored in BankAccount table
      MONO_ACCOUNT_NUMBER            → Bank account number (for enrichment)
      MONO_SECRET_KEY / MONO_APP_ID  → Sandbox API credentials
      MONO_BASE_URL                  → (optional) defaults to https://api.withmono.com
      MONO_PAGE_LIMIT                → (optional) page size, default 100

  - Optional overrides:
      MONO_ACCOUNT_DB_ID             → UUID of BankAccount row (auto-resolves if omitted)
      MONO_CONNECTION_DB_ID          → UUID of BankingConnection row (auto-resolves if omitted)

Usage:
    DATABASE_URL=postgresql+asyncpg://... \
    MONO_API_ACCOUNT_ID=acc_123 \
    MONO_PROVIDER_ACCOUNT_ID=provider-1 \
    MONO_ACCOUNT_NUMBER=0123456789 \
    MONO_SECRET_KEY=sk_test \
    MONO_APP_ID=app_test \
    ./live_mono_staging_smoke_test.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from platform.backend.core_platform.data_management.models.banking import (
    BankAccount,
    BankingConnection,
    BankTransaction as ORMTransaction,
)
from platform.backend.core_platform.services.banking_ingestion_service import BankingIngestionService
from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.client import (
    MonoClient,
    MonoClientConfig,
)
from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.pipeline import (
    MonoTransactionPipeline,
)
from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.transaction_sync import (
    InMemorySyncStateStore,
    MonoTransactionSyncService,
)
from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.transformer import (
    MonoTransactionTransformer,
)


class StdoutEmitter:
    """Simple event emitter that prints JSON payloads to stdout."""

    async def __call__(self, name: str, payload: Dict[str, Any]) -> None:
        timestamp = datetime.now(timezone.utc).isoformat()
        data = {"ts": timestamp, "event": name, "payload": payload}
        print(json.dumps(data, indent=2, default=str))


def get_env(name: str, *, required: bool = True, default: Optional[str] = None) -> str:
    value = os.getenv(name, default)
    if required and not value:
        print(f"❌ Required environment variable missing: {name}", file=sys.stderr)
        sys.exit(1)
    return value or ""


async def resolve_account_metadata(session: AsyncSession) -> tuple[uuid.UUID, uuid.UUID, str]:
    """Resolve connection/account ids using provider account id if explicit ids are not supplied."""
    provider_account_id = get_env("MONO_PROVIDER_ACCOUNT_ID")
    account_id_env = os.getenv("MONO_ACCOUNT_DB_ID")
    connection_id_env = os.getenv("MONO_CONNECTION_DB_ID")

    if account_id_env and connection_id_env:
        return uuid.UUID(connection_id_env), uuid.UUID(account_id_env), provider_account_id

    stmt = (
        select(BankAccount.id, BankAccount.connection_id)
        .where(BankAccount.provider_account_id == provider_account_id)
        .limit(1)
    )
    result = await session.execute(stmt)
    row = result.first()
    if not row:
        print(
            "❌ Unable to locate BankAccount with provider_account_id="
            f"{provider_account_id}. Provide MONO_ACCOUNT_DB_ID and MONO_CONNECTION_DB_ID explicitly.",
            file=sys.stderr,
        )
        sys.exit(1)
    account_db_id, connection_db_id = row
    return uuid.UUID(str(connection_db_id)), uuid.UUID(str(account_db_id)), provider_account_id


async def fetch_connection(session: AsyncSession, connection_id: uuid.UUID) -> BankingConnection:
    stmt = select(BankingConnection).where(BankingConnection.id == connection_id).limit(1)
    result = await session.execute(stmt)
    conn = result.scalar_one_or_none()
    if not conn:
        print(f"❌ BankingConnection {connection_id} not found in database.", file=sys.stderr)
        sys.exit(1)
    return conn


async def summarize_transactions(session: AsyncSession, account_id: uuid.UUID) -> Dict[str, Any]:
    stmt = select(
        func.count(ORMTransaction.id),
        func.sum(ORMTransaction.amount),
        func.min(ORMTransaction.transaction_date),
        func.max(ORMTransaction.transaction_date),
    ).where(ORMTransaction.account_id == account_id)
    count, total_amount, min_date, max_date = (await session.execute(stmt)).one()
    return {
        "transaction_count": int(count or 0),
        "total_amount": int(total_amount or 0),
        "first_transaction_date": min_date.isoformat() if min_date else None,
        "last_transaction_date": max_date.isoformat() if max_date else None,
    }


async def run_pipeline() -> None:
    database_url = get_env("DATABASE_URL")
    mono_secret = get_env("MONO_SECRET_KEY")
    mono_app_id = get_env("MONO_APP_ID")
    mono_account_number = get_env("MONO_ACCOUNT_NUMBER")
    mono_api_account_id = get_env("MONO_API_ACCOUNT_ID")

    engine = create_async_engine(database_url, echo=False)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    emitter = StdoutEmitter()
    state_store = InMemorySyncStateStore()

    page_size = int(os.getenv("MONO_PAGE_LIMIT", "100"))
    mono_client = MonoClient(
        MonoClientConfig(
            base_url=os.getenv("MONO_BASE_URL", "https://api.withmono.com"),
            secret_key=mono_secret,
            app_id=mono_app_id,
            rate_limit_per_minute=int(os.getenv("MONO_RATE_LIMIT_PER_MINUTE", "60")),
            request_timeout=float(os.getenv("MONO_REQUEST_TIMEOUT", "30")),
        )
    )

    transformer = MonoTransactionTransformer()

    async with session_factory() as session:
        connection_db_id, account_db_id, provider_account_id = await resolve_account_metadata(session)
        connection_row = await fetch_connection(session, connection_db_id)

        ingestion_service = BankingIngestionService(session, emitter)
        sync_service = MonoTransactionSyncService(
            mono_client,
            state_store,
            emitter,
            page_size=page_size,
        )
        pipeline = MonoTransactionPipeline(sync_service, transformer, ingestion_service, emitter)

        print("🚀 Starting Mono pipeline dry run…")
        result = await pipeline.run(
            account_id=mono_api_account_id,
            account_number=mono_account_number,
            provider_account_id=provider_account_id,
            connection_db_id=connection_db_id,
            account_db_id=account_db_id,
        )
        await session.commit()

        print("✅ Pipeline completed:")
        print(json.dumps(asdict(result), indent=2, default=str))

        summary = await summarize_transactions(session, account_db_id)
        print("📊 Canonical transaction summary:")
        print(json.dumps(summary, indent=2, default=str))

        print("🏦 Connection context:")
        print(json.dumps({"connection": connection_row.provider, "connection_id": str(connection_db_id)}, indent=2))


def main() -> None:
    try:
        asyncio.run(run_pipeline())
    except KeyboardInterrupt:
        print("Interrupted by user", file=sys.stderr)
        sys.exit(1)
    except Exception as exc:  # pragma: no cover - live script
        print(f"❌ Mono staging smoke test failed: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
