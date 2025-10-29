"""Mono end-to-end pipeline wiring sync, transform, and persistence."""

from __future__ import annotations

import logging
from typing import Optional

from core_platform.models.transaction import BankTransaction

from .transformer import MonoTransactionTransformer
from .transaction_sync import MonoTransactionSyncService
from core_platform.services.banking_ingestion_service import BankingIngestionService, BankingIngestionResult

logger = logging.getLogger(__name__)


class MonoTransactionPipeline:
    """Coordinates syncing, transforming, and persisting Mono transactions."""

    def __init__(
        self,
        sync_service: MonoTransactionSyncService,
        transformer: MonoTransactionTransformer,
        ingestion_service: BankingIngestionService,
        event_emitter,
    ) -> None:
        self._sync_service = sync_service
        self._transformer = transformer
        self._ingestion_service = ingestion_service
        self._event_emitter = event_emitter

    async def run(
        self,
        account_id: str,
        *,
        account_number: str,
        provider_account_id: Optional[str],
        connection_db_id,
        account_db_id,
    ) -> BankingIngestionResult:
        sync_result = await self._sync_service.sync_account(account_id)

        canonical: list[BankTransaction] = []
        for mono_tx in sync_result.transactions:
            payload = mono_tx.dict()
            tx = self._transformer.transform(
                payload,
                account_number=account_number,
                provider_account_id=provider_account_id,
            )
            canonical.append(tx)

        ingestion_result = await self._ingestion_service.ingest_transactions(
            connection_db_id,
            account_db_id,
            canonical,
        )

        await self._emit(
            "mono.pipeline.completed",
            {
                "account_id": account_id,
                "synced_transactions": len(sync_result.transactions),
                "persisted": ingestion_result.inserted_count,
                "duplicates": ingestion_result.duplicate_count,
            },
        )

        return ingestion_result

    async def _emit(self, event: str, payload: dict) -> None:
        try:
            await self._event_emitter(event, payload)
        except Exception:  # pragma: no cover
            logger.debug("Mono pipeline event emission failed", exc_info=True)


__all__ = ["MonoTransactionPipeline"]
