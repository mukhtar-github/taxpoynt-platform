"""Mono REST client with retry, backoff, and observability hooks."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Dict, Optional

import httpx

from core_platform.monitoring.prometheus_integration import get_prometheus_integration

from .exceptions import (
    MonoAuthenticationError,
    MonoConnectionError,
    MonoRateLimitError,
)

logger = logging.getLogger(__name__)

TokenGetter = Callable[[], Awaitable[str]]
TokenRefresher = Callable[[], Awaitable[str]]


@dataclass
class MonoClientConfig:
    """Configuration bundle for :class:`MonoClient`."""

    base_url: str
    secret_key: str
    app_id: str
    request_timeout: float = 30.0
    max_retries: int = 3
    backoff_factor: float = 1.5
    rate_limit_per_minute: int = 60
    metrics_service_role: str = "mono_open_banking"


class MonoClient:
    """HTTP client used by Mono integration components."""

    def __init__(
        self,
        config: MonoClientConfig,
        *,
        http_client: Optional[httpx.AsyncClient] = None,
        access_token_getter: Optional[TokenGetter] = None,
        access_token_refresher: Optional[TokenRefresher] = None,
    ) -> None:
        self._config = config
        self._access_token_getter = access_token_getter
        self._access_token_refresher = access_token_refresher
        self._cached_token: Optional[str] = None

        if http_client is None:
            headers = {
                "mono-sec-key": config.secret_key,
                "Content-Type": "application/json",
                "User-Agent": "TaxPoynt-MonoClient/1.0",
            }
            http_client = httpx.AsyncClient(base_url=config.base_url, headers=headers, timeout=config.request_timeout)
            self._owns_client = True
        else:
            self._owns_client = False
        self._client = http_client

        self._request_timestamps: list[float] = []

    async def __aenter__(self) -> "MonoClient":  # pragma: no cover - syntactic sugar
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - syntactic sugar
        await self.aclose()

    async def aclose(self) -> None:
        if self._owns_client:
            await self._client.aclose()

    async def get(self, path: str, *, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        response = await self._request("GET", path, params=params)
        return response.json()

    async def post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = await self._request("POST", path, json=payload)
        return response.json()

    async def delete(self, path: str) -> Dict[str, Any]:
        response = await self._request("DELETE", path)
        return response.json() if response.content else {}

    async def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        self._enforce_rate_limit()

        attempt = 0
        backoff = self._config.backoff_factor
        last_error: Optional[Exception] = None

        while attempt <= self._config.max_retries:
            attempt += 1
            headers = await self._build_headers()
            start = time.perf_counter()
            try:
                response = await self._client.request(method, path, params=params, json=json, headers=headers)
            except httpx.HTTPError as exc:  # network problem
                last_error = MonoConnectionError(details={"reason": str(exc)})
                await self._record_metrics(method, path, "network_error", time.perf_counter() - start)
                break

            duration = time.perf_counter() - start
            status = response.status_code
            await self._record_metrics(method, path, str(status), duration)

            if status == 401 and self._access_token_refresher:
                logger.info("Mono API returned 401 – attempting token refresh", extra={"path": path})
                try:
                    self._cached_token = await self._access_token_refresher()
                except Exception as exc:  # pragma: no cover - depends on external refresh logic
                    raise MonoAuthenticationError("Token refresh failed", details={"reason": str(exc)}) from exc
                continue

            if status == 429:
                retry_after = int(response.headers.get("Retry-After", "60"))
                if attempt > self._config.max_retries:
                    raise MonoRateLimitError(details={"retry_after": retry_after})
                logger.warning(
                    "Mono rate limit hit", extra={"retry_after": retry_after, "attempt": attempt, "path": path}
                )
                await asyncio.sleep(retry_after)
                continue

            if status >= 500:
                if attempt > self._config.max_retries:
                    raise MonoConnectionError(
                        message="Mono server error",
                        status_code=status,
                        details=self._safe_json(response),
                    )
                await asyncio.sleep(backoff)
                backoff *= self._config.backoff_factor
                continue

            if status >= 400:
                if status == 401:
                    raise MonoAuthenticationError(details={"path": path})
                raise MonoConnectionError(
                    message="Mono request failed",
                    status_code=status,
                    details=self._safe_json(response),
                )

            return response

        raise last_error or MonoConnectionError("Mono request failed after retries")

    async def _build_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {"mono-sec-key": self._config.secret_key, "x-mono-app": self._config.app_id}
        if self._access_token_getter:
            if self._cached_token is None:
                self._cached_token = await self._access_token_getter()
            headers["Authorization"] = f"Bearer {self._cached_token}"
        return headers

    def _enforce_rate_limit(self) -> None:
        now = time.monotonic()
        window = 60.0
        self._request_timestamps = [ts for ts in self._request_timestamps if now - ts <= window]
        if len(self._request_timestamps) >= self._config.rate_limit_per_minute:
            raise MonoRateLimitError(details={"retry_after": 60})
        self._request_timestamps.append(now)

    async def _record_metrics(self, method: str, path: str, status: str, duration: float) -> None:
        prom = get_prometheus_integration()
        if not prom:
            return
        try:
            prom.record_metric(
                "taxpoynt_http_requests_total",
                1,
                {
                    "method": method,
                    "endpoint": path,
                    "status_code": status,
                    "service_role": self._config.metrics_service_role,
                },
            )
            prom.record_metric(
                "taxpoynt_http_request_duration_seconds",
                duration,
                {
                    "method": method,
                    "endpoint": path,
                    "service_role": self._config.metrics_service_role,
                },
            )
        except Exception:  # pragma: no cover - metrics failures shouldn't break calls
            logger.debug("Failed to record Mono metrics", exc_info=True)

    @staticmethod
    def _safe_json(response: httpx.Response) -> Dict[str, Any]:
        try:
            return response.json()
        except Exception:
            return {"body": response.text[:512]}


__all__ = ["MonoClient", "MonoClientConfig"]
