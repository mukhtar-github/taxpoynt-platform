"""Mono end-to-end pipeline wiring sync, transform, and persistence."""

from __future__ import annotations

import logging
from time import perf_counter
from typing import Optional
from uuid import uuid4

from core_platform.models.transaction import BankTransaction

from .transformer import MonoTransactionTransformer
from .transaction_sync import MonoTransactionSyncService
from core_platform.services.banking_ingestion_service import BankingIngestionService, BankingIngestionResult
from .observability import record_stage_duration, record_stage_error, reason_from_exception

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
        correlation_id = f"mono-pipeline-{uuid4().hex}"
        account_label = str(account_db_id)
        logger.info(
            "Mono transaction pipeline started",
            extra={
                "account_id": account_id,
                "account_db_id": account_label,
                "correlation_id": correlation_id,
            },
        )

        try:
            sync_result = await self._sync_service.sync_account(account_id, correlation_id=correlation_id)
        except Exception:
            logger.exception(
                "Mono transaction pipeline aborted during sync",
                extra={"account_id": account_id, "account_db_id": account_label, "correlation_id": correlation_id},
            )
            raise

        canonical: list[BankTransaction] = []
        transform_started_at = perf_counter()
        try:
            for mono_tx in sync_result.transactions:
                payload = mono_tx.dict()
                tx = self._transformer.transform(
                    payload,
                    account_number=account_number,
                    provider_account_id=provider_account_id,
                )
                canonical.append(tx)
        except Exception as exc:
            duration = perf_counter() - transform_started_at
            record_stage_duration("transform", "error", duration, account_id=account_label)
            record_stage_error("transform", reason_from_exception(exc), account_id=account_label)
            logger.exception(
                "Mono transaction transformation failed",
                extra={
                    "account_id": account_id,
                    "account_db_id": account_label,
                    "correlation_id": correlation_id,
                },
            )
            raise

        transform_duration = perf_counter() - transform_started_at
        record_stage_duration("transform", "success", transform_duration, account_id=account_label)

        persist_started_at = perf_counter()
        try:
            ingestion_result = await self._ingestion_service.ingest_transactions(
                connection_db_id,
                account_db_id,
                canonical,
            )
        except Exception as exc:
            duration = perf_counter() - persist_started_at
            record_stage_duration("persist", "error", duration, account_id=account_label)
            record_stage_error("persist", reason_from_exception(exc), account_id=account_label)
            logger.exception(
                "Mono transaction persistence failed",
                extra={
                    "account_id": account_id,
                    "account_db_id": account_label,
                    "correlation_id": correlation_id,
                },
            )
            raise
        persist_duration = perf_counter() - persist_started_at
        record_stage_duration("persist", "success", persist_duration, account_id=account_label)

        await self._emit(
            "mono.pipeline.completed",
            {
                "account_id": account_id,
                "account_db_id": account_label,
                "synced_transactions": len(sync_result.transactions),
                "persisted": ingestion_result.inserted_count,
                "duplicates": ingestion_result.duplicate_count,
                "correlation_id": correlation_id,
            },
        )
        logger.info(
            "Mono transaction pipeline completed",
            extra={
                "account_id": account_id,
                "account_db_id": account_label,
                "correlation_id": correlation_id,
                "synced_transactions": len(sync_result.transactions),
                "persisted": ingestion_result.inserted_count,
                "duplicates": ingestion_result.duplicate_count,
                "transform_duration": transform_duration,
                "persist_duration": persist_duration,
            },
        )

        return ingestion_result

    async def _emit(self, event: str, payload: dict) -> None:
        try:
            await self._event_emitter(event, payload)
        except Exception:  # pragma: no cover
            logger.debug("Mono pipeline event emission failed", exc_info=True)


__all__ = ["MonoTransactionPipeline"]
