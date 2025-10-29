import asyncio
from datetime import date

import pytest

from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.transaction_sync import (
    InMemorySyncStateStore,
    MonoSyncResult,
    MonoTransactionSyncService,
)
from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.exceptions import MonoConnectionError
from platform.backend.external_integrations.connector_framework.shared_utilities.retry_manager import RetryConfig, RetryManager


class RecordingEmitter:
    def __init__(self) -> None:
        self.events = []

    async def __call__(self, name: str, payload):
        self.events.append((name, payload))


class StubMonoClient:
    def __init__(self, responses):
        self.responses = responses
        self.calls = []

    async def get(self, path: str, params=None):
        cursor = params.get("cursor") if params else None
        key = cursor or "initial"
        self.calls.append((path, params))
        return self.responses[key]


@pytest.mark.asyncio
async def test_sync_account_paginates_and_deduplicates():
    responses = {
        "initial": {
            "paging": {"next": "cursor-2"},
            "data": [
                {
                    "id": "tx-1",
                    "amount": 10000,
                    "date": "2024-05-01",
                    "narration": "POS Purchase",
                    "type": "credit",
                    "category": "pos",
                    "balance": 500000,
                },
                {
                    "id": "tx-2",
                    "amount": 25000,
                    "date": "2024-05-01",
                    "narration": "Transfer",
                    "type": "debit",
                    "category": "transfer",
                    "balance": 475000,
                },
            ],
        },
        "cursor-2": {
            "paging": {},
            "data": [
                {
                    "id": "tx-2",
                    "amount": 25000,
                    "date": "2024-05-01",
                    "narration": "Duplicate",
                    "type": "debit",
                    "category": "transfer",
                    "balance": 475000,
                },
                {
                    "id": "tx-3",
                    "amount": 3000,
                    "date": "2024-05-02",
                    "narration": "SMS Charge",
                    "type": "debit",
                    "category": "fee",
                    "balance": 472000,
                },
            ],
        },
    }

    client = StubMonoClient(responses)
    store = InMemorySyncStateStore()
    emitter = RecordingEmitter()
    retry_manager = RetryManager(RetryConfig(max_attempts=2, enable_jitter=False, initial_delay_seconds=0.01))
    service = MonoTransactionSyncService(client, store, emitter, retry_manager=retry_manager)

    result = await service.sync_account("acc-123")

    assert isinstance(result, MonoSyncResult)
    assert result.total_pages == 2
    assert [tx.id for tx in result.transactions] == ["tx-1", "tx-2", "tx-3"]
    assert emitter.events[0][0] == "mono.fetch.started"
    assert emitter.events[-1][0] == "mono.fetch.completed"
    assert await store.get_cursor("acc-123") is None

    # Second run should skip duplicates due to idempotency guard
    result_repeat = await service.sync_account("acc-123")
    assert result_repeat.transactions == []


@pytest.mark.asyncio
async def test_sync_account_uses_existing_cursor():
    responses = {
        "existing-cursor": {
            "paging": {},
            "data": [
                {
                    "id": "tx-9",
                    "amount": 1200,
                    "date": "2024-06-01",
                    "narration": "Interest",
                    "type": "credit",
                    "category": "interest",
                    "balance": 600000,
                }
            ],
        }
    }

    client = StubMonoClient(responses)
    store = InMemorySyncStateStore()
    await store.set_cursor("acc-001", "existing-cursor")
    emitter = RecordingEmitter()
    service = MonoTransactionSyncService(client, store, emitter)

    result = await service.sync_account("acc-001")

    assert [tx.id for tx in result.transactions] == ["tx-9"]
    assert client.calls[0][1]["cursor"] == "existing-cursor"


@pytest.mark.asyncio
async def test_sync_account_retries_on_failure():
    class FlakyClient(StubMonoClient):
        def __init__(self, responses):
            super().__init__(responses)
            self.fail_first = True

        async def get(self, path: str, params=None):
            if self.fail_first:
                self.fail_first = False
                raise MonoConnectionError("temporary failure")
            return await super().get(path, params)

    responses = {
        "initial": {
            "paging": {},
            "data": [
                {
                    "id": "tx-10",
                    "amount": 100,
                    "date": "2024-07-01",
                    "narration": "ATM",
                    "type": "debit",
                    "category": "cash",
                    "balance": 400000,
                }
            ],
        }
    }

    client = FlakyClient(responses)
    store = InMemorySyncStateStore()
    emitter = RecordingEmitter()
    retry_manager = RetryManager(
        RetryConfig(max_attempts=2, enable_jitter=False, initial_delay_seconds=0.0, retryable_exceptions=[MonoConnectionError])
    )
    service = MonoTransactionSyncService(client, store, emitter, retry_manager=retry_manager)

    result = await service.sync_account("acc-999")

    assert [tx.id for tx in result.transactions] == ["tx-10"]
    assert len(client.calls) == 1  # actual successful call recorded after retry
