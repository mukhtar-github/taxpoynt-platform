"""Orchestrates paginated Mono transaction fetches with idempotency and retries."""

from __future__ import annotations

import hashlib
import logging
from time import perf_counter
from dataclasses import dataclass
from datetime import date, datetime
from typing import Awaitable, Callable, Dict, Iterable, List, Optional, Protocol
from uuid import uuid4

try:
    from platform.backend.external_integrations.connector_framework.shared_utilities.retry_manager import (
        RetryConfig,
        RetryManager,
    )
except ImportError:  # pragma: no cover - local backend execution
    from external_integrations.connector_framework.shared_utilities.retry_manager import (  # type: ignore
        RetryConfig,
        RetryManager,
    )

from .client import MonoClient
from .models import MonoTransaction, MonoTransactionsResponse
from .observability import (
    FAILURE_ALERT_THRESHOLD,
    LATENCY_ALERT_SECONDS,
    latency_sla_breached,
    reason_from_exception,
    record_stage_duration,
    record_stage_error,
    record_zero_transactions,
    register_failure,
    reset_failure,
)

logger = logging.getLogger(__name__)


class SyncStateStore(Protocol):
    """Persistence interface for Mono sync cursors and dedupe keys."""

    async def get_cursor(self, account_id: str) -> Optional[str]:
        ...

    async def set_cursor(self, account_id: str, cursor: Optional[str]) -> None:
        ...

    async def register_transaction(self, account_id: str, dedupe_key: str) -> bool:
        """Return True if the key is new, False if transaction already processed."""
        ...


@dataclass
class MonoSyncResult:
    account_id: str
    transactions: List[MonoTransaction]
    cursor: Optional[str]
    total_pages: int


class InMemorySyncStateStore:
    """Simple in-memory implementation for testing and local runs."""

    def __init__(self) -> None:
        self._cursor: Dict[str, Optional[str]] = {}
        self._dedupe: Dict[str, set[str]] = {}

    async def get_cursor(self, account_id: str) -> Optional[str]:
        return self._cursor.get(account_id)

    async def set_cursor(self, account_id: str, cursor: Optional[str]) -> None:
        self._cursor[account_id] = cursor

    async def register_transaction(self, account_id: str, dedupe_key: str) -> bool:
        bucket = self._dedupe.setdefault(account_id, set())
        if dedupe_key in bucket:
            return False
        bucket.add(dedupe_key)
        return True


class MonoTransactionSyncService:
    """Coordinates fetching paginated Mono transactions with retry + idempotency."""

    def __init__(
        self,
        mono_client: MonoClient,
        state_store: SyncStateStore,
        event_emitter: Callable[[str, Dict[str, object]], Awaitable[None]],
        *,
        retry_manager: Optional[RetryManager] = None,
        page_size: int = 100,
    ) -> None:
        self._client = mono_client
        self._state_store = state_store
        self._event_emitter = event_emitter
        self._page_size = page_size
        self._retry_manager = retry_manager or RetryManager(
            RetryConfig(
                max_attempts=3,
                initial_delay_seconds=1.0,
                enable_jitter=False,
                retryable_exceptions=[Exception],
            )
        )

    async def sync_account(
        self,
        account_id: str,
        *,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        correlation_id: Optional[str] = None,
    ) -> MonoSyncResult:
        correlation = correlation_id or f"mono-sync-{uuid4().hex}"
        cursor = await self._state_store.get_cursor(account_id)
        await self._emit(
            "mono.fetch.started",
            {"account_id": account_id, "cursor": cursor, "correlation_id": correlation},
        )
        logger.info(
            "Mono transaction sync started",
            extra={"account_id": account_id, "cursor": cursor, "correlation_id": correlation},
        )

        aggregated: List[MonoTransaction] = []
        page = 0
        next_cursor = cursor
        fetch_started_at = perf_counter()

        try:
            while True:
                params = self._build_query(next_cursor, start_date, end_date)

                async def _operation() -> MonoTransactionsResponse:
                    return await self._fetch_transactions(account_id, params)

                response = await self._retry_manager.execute_with_retry(
                    _operation,
                    operation_name="mono.fetch_transactions",
                )
                page += 1

                for transaction in response.data:
                    dedupe_key = self._make_dedupe_key(transaction)
                    if not await self._state_store.register_transaction(account_id, dedupe_key):
                        continue
                    aggregated.append(transaction)

                next_cursor = self._extract_next_cursor(response.paging)
                if not next_cursor:
                    break
        except Exception as exc:
            duration = perf_counter() - fetch_started_at
            record_stage_duration("sync", "error", duration, account_id=account_id)
            record_stage_error("sync", reason_from_exception(exc), account_id=account_id)
            failures = register_failure(account_id)
            await self._emit(
                "mono.fetch.failed",
                {
                    "account_id": account_id,
                    "cursor": next_cursor,
                    "correlation_id": correlation,
                    "failures": failures,
                    "threshold": FAILURE_ALERT_THRESHOLD,
                    "duration": duration,
                    "reason": reason_from_exception(exc),
                },
            )
            if failures >= FAILURE_ALERT_THRESHOLD:
                logger.error(
                    "Mono transaction sync consecutive failure threshold breached",
                    extra={
                        "account_id": account_id,
                        "correlation_id": correlation,
                        "failures": failures,
                        "threshold": FAILURE_ALERT_THRESHOLD,
                    },
                )
            else:
                logger.warning(
                    "Mono transaction sync failed",
                    extra={"account_id": account_id, "correlation_id": correlation, "failures": failures},
                )
            raise

        await self._state_store.set_cursor(account_id, next_cursor)
        duration = perf_counter() - fetch_started_at
        record_stage_duration("sync", "success", duration, account_id=account_id)
        reset_failure(account_id)

        if latency_sla_breached(duration):
            await self._emit(
                "mono.fetch.latency_sla_exceeded",
                {
                    "account_id": account_id,
                    "duration": duration,
                    "threshold": LATENCY_ALERT_SECONDS,
                    "correlation_id": correlation,
                },
            )
            logger.warning(
                "Mono transaction sync latency SLA breached",
                extra={"account_id": account_id, "correlation_id": correlation, "duration": duration},
            )

        if not aggregated:
            record_zero_transactions(account_id=account_id)
            await self._emit(
                "mono.fetch.zero_transactions",
                {
                    "account_id": account_id,
                    "correlation_id": correlation,
                    "cursor": next_cursor,
                    "duration": duration,
                },
            )
            logger.warning(
                "Mono transaction sync completed with zero transactions",
                extra={"account_id": account_id, "correlation_id": correlation},
            )

        await self._emit(
            "mono.fetch.completed",
            {
                "account_id": account_id,
                "cursor": next_cursor,
                "transactions_fetched": len(aggregated),
                "pages": page,
                "duration": duration,
                "correlation_id": correlation,
            },
        )
        logger.info(
            "Mono transaction sync completed",
            extra={
                "account_id": account_id,
                "correlation_id": correlation,
                "transactions_fetched": len(aggregated),
                "pages": page,
                "cursor": next_cursor,
            },
        )

        return MonoSyncResult(account_id=account_id, transactions=aggregated, cursor=next_cursor, total_pages=page)

    async def _fetch_transactions(self, account_id: str, params: Dict[str, object]) -> MonoTransactionsResponse:
        response = await self._client.get(f"/v2/accounts/{account_id}/transactions", params=params)
        return MonoTransactionsResponse(**response)

    def _build_query(
        self,
        cursor: Optional[str],
        start_date: Optional[date],
        end_date: Optional[date],
    ) -> Dict[str, object]:
        params: Dict[str, object] = {"paginate": True, "limit": self._page_size}
        if cursor:
            params["cursor"] = cursor
        else:
            if start_date:
                params["start"] = start_date.isoformat()
            if end_date:
                params["end"] = end_date.isoformat()
        return params

    @staticmethod
    def _extract_next_cursor(paging: Dict[str, object]) -> Optional[str]:
        if not paging:
            return None
        for key in ("next", "cursor", "next_cursor"):
            value = paging.get(key)
            if isinstance(value, str) and value:
                return value
        links = paging.get("links") if isinstance(paging.get("links"), dict) else None
        if links and isinstance(links.get("next"), str):
            return links["next"]
        # Fallback: finite pages scenario
        current = paging.get("page")
        total = paging.get("pages")
        if isinstance(current, int) and isinstance(total, int) and current < total:
            return str(current + 1)
        return None

    async def _emit(self, event: str, payload: Dict[str, object]) -> None:
        try:
            await self._event_emitter(event, payload)
        except Exception:  # pragma: no cover - emission failures shouldn't break sync
            logger.debug("Mono event emission failed", exc_info=True)

    @staticmethod
    def _make_dedupe_key(transaction: MonoTransaction) -> str:
        raw = "|".join(
            [
                transaction.id,
                str(transaction.amount),
                transaction.date.isoformat(),
                transaction.type,
            ]
        )
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()


__all__ = [
    "MonoTransactionSyncService",
    "MonoSyncResult",
    "SyncStateStore",
    "InMemorySyncStateStore",
]
