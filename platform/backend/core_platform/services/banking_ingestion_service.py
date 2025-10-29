"""Service for persisting canonical bank transactions and emitting events."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core_platform.data_management.models.banking import BankTransaction as ORMTransaction
from core_platform.models.transaction import BankTransaction

logger = logging.getLogger(__name__)


@dataclass
class BankingIngestionResult:
    account_id: str
    inserted_count: int
    duplicate_count: int


class BankingIngestionService:
    """Persists canonical bank transactions for Mono/Stitch connectors."""

    def __init__(self, session: AsyncSession, event_emitter) -> None:
        self._session = session
        self._event_emitter = event_emitter

    async def ingest_transactions(
        self,
        connection_db_id,
        account_db_id,
        transactions: Iterable[BankTransaction],
    ) -> BankingIngestionResult:
        inserted = 0
        duplicates = 0
        orm_objects: List[ORMTransaction] = []

        for tx in transactions:
            if await self._transaction_exists(tx.id, account_db_id):
                duplicates += 1
                continue
            orm_objects.append(self._to_orm(connection_db_id, account_db_id, tx))

        if orm_objects:
            self._session.add_all(orm_objects)
            await self._session.flush()
            inserted = len(orm_objects)

        await self._emit(
            "bank.transactions.ingested",
            {
                "connection_id": str(connection_db_id),
                "account_id": str(account_db_id),
                "inserted": inserted,
                "duplicates": duplicates,
            },
        )

        return BankingIngestionResult(account_id=str(account_db_id), inserted_count=inserted, duplicate_count=duplicates)

    async def _transaction_exists(self, provider_transaction_id: str, account_db_id) -> bool:
        stmt = select(ORMTransaction.id).where(
            ORMTransaction.provider_transaction_id == provider_transaction_id,
            ORMTransaction.account_id == account_db_id,
        )
        result = await self._session.execute(stmt.limit(1))
        return result.scalar_one_or_none() is not None

    @staticmethod
    def _to_orm(connection_db_id, account_db_id, tx: BankTransaction) -> ORMTransaction:
        counterparty = tx.counterparty or None
        return ORMTransaction(
            connection_id=connection_db_id,
            account_id=account_db_id,
            provider_transaction_id=tx.id,
            transaction_reference=tx.transaction_reference or tx.id,
            transaction_type=tx.transaction_type.upper(),
            amount=tx.amount,
            currency=tx.currency,
            description=tx.description,
            narration=tx.narration,
            transaction_date=tx.transaction_date,
            value_date=tx.value_date,
            balance_after=tx.balance_after,
            counterparty_name=counterparty.name if counterparty else None,
            counterparty_account=counterparty.account_number if counterparty else None,
            counterparty_bank=counterparty.bank_name if counterparty else None,
            transaction_metadata=tx.metadata,
        )

    async def _emit(self, event: str, payload: dict) -> None:
        try:
            await self._event_emitter(event, payload)
        except Exception:  # pragma: no cover
            logger.debug("Failed to emit ingestion event", exc_info=True)


__all__ = ["BankingIngestionService", "BankingIngestionResult"]
