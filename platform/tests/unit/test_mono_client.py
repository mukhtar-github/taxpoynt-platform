import asyncio
from decimal import Decimal

import pytest
import httpx

from platform.backend.external_integrations.financial_systems.banking.open_banking.providers.mono.client import (
    MonoClient,
    MonoClientConfig,
)


@pytest.mark.asyncio
async def test_mono_client_get_success(monkeypatch):
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["mono-sec-key"] == "secret"
        assert request.headers["x-mono-app"] == "app"
        return httpx.Response(200, json={"status": "ok"})

    transport = httpx.MockTransport(handler)
    cfg = MonoClientConfig(base_url="https://mono.test", secret_key="secret", app_id="app")
    async with MonoClient(cfg, http_client=httpx.AsyncClient(transport=transport, base_url=cfg.base_url)) as client:
        payload = await client.get("/ping")
    assert payload == {"status": "ok"}


@pytest.mark.asyncio
async def test_mono_client_refreshes_token(monkeypatch):
    calls = {"count": 0}

    async def handler(request: httpx.Request) -> httpx.Response:
        calls["count"] += 1
        if calls["count"] == 1:
            assert request.headers.get("Authorization") == "Bearer old"
            return httpx.Response(401)
        assert request.headers.get("Authorization") == "Bearer new"
        return httpx.Response(200, json={"hello": "world"})

    transport = httpx.MockTransport(handler)
    cfg = MonoClientConfig(base_url="https://mono.test", secret_key="secret", app_id="app")

    async def get_token():
        return "old"

    async def refresh_token(_: str = ""):
        return "new"

    async with MonoClient(
        cfg,
        http_client=httpx.AsyncClient(transport=transport, base_url=cfg.base_url),
        access_token_getter=get_token,
        access_token_refresher=lambda: refresh_token(),
    ) as client:
        data = await client.get("/resource")

    assert data == {"hello": "world"}
    assert calls["count"] == 2


@pytest.mark.asyncio
async def test_mono_client_handles_rate_limit(monkeypatch):
    responses = iter([
        httpx.Response(429, headers={"Retry-After": "0"}),
        httpx.Response(200, json={"result": True}),
    ])

    async def handler(request: httpx.Request) -> httpx.Response:
        return next(responses)

    transport = httpx.MockTransport(handler)
    cfg = MonoClientConfig(base_url="https://mono.test", secret_key="secret", app_id="app", max_retries=2)

    async with MonoClient(cfg, http_client=httpx.AsyncClient(transport=transport, base_url=cfg.base_url)) as client:
        payload = await client.get("/transactions")

    assert payload == {"result": True}


@pytest.mark.asyncio
async def test_mono_client_raises_after_server_errors():
    async def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"message": "error"})

    transport = httpx.MockTransport(handler)
    cfg = MonoClientConfig(base_url="https://mono.test", secret_key="secret", app_id="app", max_retries=1)

    async with MonoClient(cfg, http_client=httpx.AsyncClient(transport=transport, base_url=cfg.base_url)) as client:
        with pytest.raises(Exception):
            await client.get("/transactions")


@pytest.mark.asyncio
async def test_mono_client_contract_headers():
    async def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["mono-sec-key"] == "secret"
        assert request.headers["x-mono-app"] == "app"
        return httpx.Response(200, json={"ok": True})

    transport = httpx.MockTransport(handler)
    cfg = MonoClientConfig(base_url="https://mono.test", secret_key="secret", app_id="app")

    async with MonoClient(cfg, http_client=httpx.AsyncClient(transport=transport, base_url=cfg.base_url)) as client:
        await client.get("/health")
