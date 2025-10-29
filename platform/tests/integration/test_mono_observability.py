"""Synthetic observability tests for the Mono banking pipeline."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List, Tuple

import pytest

from platform.backend.external_integrations.connector_framework.shared_utilities.retry_manager import (
    RetryConfig,
    RetryManager,
)
from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono import (
    observability as mono_observability,
)
from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.exceptions import (
    MonoConnectionError,
)
from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.models import (
    MonoTransaction,
    MonoTransactionType,
)
from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.pipeline import (
    MonoTransactionPipeline,
)
from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.transaction_sync import (
    InMemorySyncStateStore,
    MonoSyncResult,
    MonoTransactionSyncService,
)
from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.transformer import (
    MonoTransactionTransformer,
)
from platform.backend.core_platform.services.banking_ingestion_service import BankingIngestionResult


class PrometheusStub:
    """Capture Prometheus registrations and metric writes."""

    def __init__(self) -> None:
        self.registered: List[str] = []
        self.calls: List[Tuple[str, float, Dict[str, str]]] = []

    def register_metric(self, metric_definition) -> None:
        self.registered.append(metric_definition.name)

    def record_metric(self, name: str, value: float, labels: Dict[str, str]) -> None:
        self.calls.append((name, value, labels))


class RecordingEmitter:
    """Store emitted events for assertions."""

    def __init__(self) -> None:
        self.events: List[Tuple[str, Dict[str, Any]]] = []

    async def __call__(self, name: str, payload: Dict[str, Any]) -> None:
        self.events.append((name, payload))


@pytest.fixture()
def prom_stub(monkeypatch):
    """Patch Mono observability helpers to use an in-memory Prometheus stub."""

    stub = PrometheusStub()
    monkeypatch.setattr(
        "platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.observability.get_prometheus_integration",
        lambda: stub,
    )
    monkeypatch.setattr(mono_observability, "_METRICS_REGISTERED", False)
    monkeypatch.setattr(mono_observability, "_FAILURE_COUNTS", defaultdict(int))
    return stub


@pytest.mark.asyncio
async def test_mono_sync_zero_transactions_records_metrics_and_event(prom_stub):
    """AAA: zero-transaction sync should emit metrics and alert event."""
    emitter = RecordingEmitter()

    class EmptyClient:
        async def get(self, path, params=None):
            return {"paging": {}, "data": []}

    service = MonoTransactionSyncService(EmptyClient(), InMemorySyncStateStore(), emitter)

    result = await service.sync_account("acc-zero", correlation_id="corr-zero")
    assert result.transactions == []

    metric_names = [name for name, _, _ in prom_stub.calls]
    assert "taxpoynt_mono_pipeline_stage_seconds" in metric_names
    zero_records = [call for call in prom_stub.calls if call[0] == "taxpoynt_mono_pipeline_zero_transactions_total"]
    assert zero_records, "Zero transaction counter should be recorded"
    assert zero_records[-1][1] == 1

    event_names = [name for name, _ in emitter.events]
    assert "mono.fetch.zero_transactions" in event_names
    completed_payload = next(payload for name, payload in emitter.events if name == "mono.fetch.completed")
    assert completed_payload["transactions_fetched"] == 0


@pytest.mark.asyncio
async def test_mono_sync_failure_triggers_threshold_alert(prom_stub):
    """AAA: repeated failures should emit failure metrics and threshold alert."""
    emitter = RecordingEmitter()

    class FailingClient:
        async def get(self, path, params=None):
            raise MonoConnectionError("boom")

    retry_manager = RetryManager(
        RetryConfig(
            max_attempts=1,
            initial_delay_seconds=0.0,
            enable_jitter=False,
            retryable_exceptions=[MonoConnectionError],
        )
    )
    service = MonoTransactionSyncService(FailingClient(), InMemorySyncStateStore(), emitter, retry_manager=retry_manager)

    for attempt in range(mono_observability.FAILURE_ALERT_THRESHOLD):
        with pytest.raises(MonoConnectionError):
            await service.sync_account("acc-fail", correlation_id="corr-fail")

    failure_events = [payload for name, payload in emitter.events if name == "mono.fetch.failed"]
    assert failure_events, "Failure events should be emitted"
    assert failure_events[-1]["failures"] >= mono_observability.FAILURE_ALERT_THRESHOLD

    error_metrics = [call for call in prom_stub.calls if call[0] == "taxpoynt_mono_pipeline_errors_total"]
    assert error_metrics, "Error counter should record failures"
    assert error_metrics[-1][2]["stage"] == "sync"
    assert error_metrics[-1][2]["reason"] == "MonoConnectionError"


@pytest.mark.asyncio
async def test_mono_pipeline_records_transform_and_persist_metrics(prom_stub):
    """AAA: pipeline stages should record transform/persist timings."""
    emitter = RecordingEmitter()

    mono_transactions = [
        MonoTransaction(
            id="tx-001",
            amount=1000,
            date="2024-08-01",
            narration="POS",
            type=MonoTransactionType.CREDIT,
            category="pos",
            balance=5000,
        )
    ]

    class StubSyncService:
        async def sync_account(self, account_id, **kwargs):
            return MonoSyncResult(account_id=account_id, transactions=mono_transactions, cursor=None, total_pages=1)

    class StubIngestionService:
        async def ingest_transactions(self, connection_db_id, account_db_id, transactions):
            inserted = len(transactions)
            return BankingIngestionResult(account_id=str(account_db_id), inserted_count=inserted, duplicate_count=0)

    pipeline = MonoTransactionPipeline(
        StubSyncService(),
        MonoTransactionTransformer(),
        StubIngestionService(),
        emitter,
    )

    result = await pipeline.run(
        account_id="mono-account",
        account_number="0123456789",
        provider_account_id="provider-1",
        connection_db_id="conn-1",
        account_db_id="acct-1",
    )

    assert result.inserted_count == 1

    stage_calls = [labels["stage"] for name, _, labels in prom_stub.calls if name == "taxpoynt_mono_pipeline_stage_seconds"]
    assert "transform" in stage_calls
    assert "persist" in stage_calls

    pipeline_events = [payload for name, payload in emitter.events if name == "mono.pipeline.completed"]
    assert pipeline_events, "Pipeline completion event expected"
    assert "correlation_id" in pipeline_events[0]
