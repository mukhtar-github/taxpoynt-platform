import asyncio
import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from platform.backend.core_platform.data_management.models.base import BaseModel
from platform.backend.core_platform.data_management.models.banking import (
    BankingConnection,
    BankAccount,
    BankTransaction as ORMTransaction,
)
from platform.backend.core_platform.services.banking_ingestion_service import BankingIngestionService
from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.models import (
    MonoTransaction,
    MonoTransactionType,
)
from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.pipeline import MonoTransactionPipeline
from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.transaction_sync import MonoSyncResult
from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.transformer import MonoTransactionTransformer


@pytest.mark.asyncio
async def test_pipeline_persists_transactions_and_emits_events():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    events = []

    async def emitter(name, payload):
        events.append((name, payload))

    async with async_session() as session:
        connection_id = uuid.uuid4()
        account_id = uuid.uuid4()
        session.add(
            BankingConnection(
                id=connection_id,
                si_id=uuid.uuid4(),
                provider="mono",
                provider_connection_id="mono-conn",
            )
        )
        session.add(
            BankAccount(
                id=account_id,
                connection_id=connection_id,
                provider_account_id="provider-1",
                account_number="0123456789",
                account_name="Test Account",
                account_type="savings",
                bank_name="Test Bank",
                bank_code="999",
                currency="NGN",
            )
        )
        await session.commit()

    transactions = [
        MonoTransaction(
            id="tx-1",
            amount=15000,
            date="2024-05-01",
            narration="POS",
            type=MonoTransactionType.CREDIT,
            category="pos",
            balance=115000,
        ),
        MonoTransaction(
            id="tx-2",
            amount=5000,
            date="2024-05-02",
            narration="Fee",
            type=MonoTransactionType.DEBIT,
            category="fee",
            balance=110000,
        ),
    ]

    class StubSyncService:
        async def sync_account(self, account_id, **kwargs):
            return MonoSyncResult(account_id=account_id, transactions=transactions, cursor=None, total_pages=1)

    async with async_session() as session:
        ingestion = BankingIngestionService(session, emitter)
        transformer = MonoTransactionTransformer()
        pipeline = MonoTransactionPipeline(StubSyncService(), transformer, ingestion, emitter)

        result = await pipeline.run(
            account_id="mono-account",
            account_number="0123456789",
            provider_account_id="provider-1",
            connection_db_id=connection_id,
            account_db_id=account_id,
        )

        # Run a second time to ensure duplicates detected
        result_repeat = await pipeline.run(
            account_id="mono-account",
            account_number="0123456789",
            provider_account_id="provider-1",
            connection_db_id=connection_id,
            account_db_id=account_id,
        )

        await session.commit()

    async with async_session() as session:
        rows = await session.execute(select(ORMTransaction.provider_transaction_id))
        assert {row[0] for row in rows} == {"tx-1", "tx-2"}

    assert result.inserted_count == 2
    assert result_repeat.inserted_count == 0
    assert result_repeat.duplicate_count == 2

    bank_events = [payload for name, payload in events if name == "bank.transactions.ingested"]
    pipeline_events = [payload for name, payload in events if name == "mono.pipeline.completed"]

    assert bank_events
    assert pipeline_events
    last_pipeline = pipeline_events[-1]
    assert last_pipeline["persisted"] >= 0
    assert set(last_pipeline.keys()) == {"account_id", "synced_transactions", "persisted", "duplicates", "correlation_id"}
