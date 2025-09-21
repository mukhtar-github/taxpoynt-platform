"""
Base HTTP Connector with Retries
================================
Reusable async HTTP base class for external connectors (CRM/POS/etc.).
Wraps httpx calls with the shared RetryManager for resilient networking.
"""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import httpx

from .shared_utilities.retry_manager import (
    RetryManager,
    RetryConfig,
    RetryStrategy,
    RetryCondition,
)


logger = logging.getLogger(__name__)


class BaseHTTPConnector:
    """Async base connector that provides retry-wrapped HTTP methods."""

    def __init__(
        self,
        *,
        base_url: str,
        default_headers: Optional[Dict[str, str]] = None,
        timeout_seconds: float = 30.0,
        retry_config: Optional[RetryConfig] = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.headers = default_headers or {}
        self.timeout = timeout_seconds
        self.client = httpx.AsyncClient(timeout=self.timeout, headers=self.headers)
        self.retry_config = retry_config or RetryConfig(
            max_attempts=3,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            initial_delay_seconds=0.5,
            max_delay_seconds=5.0,
            retry_condition=RetryCondition.ON_STATUS_CODE,
            retryable_status_codes=[408, 425, 429, 500, 502, 503, 504],
            enable_metrics=False,
        )
        self.retry_manager = RetryManager(self.retry_config)

    async def close(self) -> None:
        try:
            await self.client.aclose()
        except Exception:
            pass

    async def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        url = f"{self.base_url}{path}"

        async def _op():
            return await self.client.request(method, url, **kwargs)

        # Execute with retry manager
        result = await self.retry_manager.execute_async(
            operation_name=f"http_{method.lower()}",
            operation=_op,
        )
        return result

    async def get(self, path: str, params: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        return await self._request("GET", path, params=params, headers=headers)

    async def post(self, path: str, json: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        return await self._request("POST", path, json=json, headers=headers)

    async def put(self, path: str, json: Optional[Dict[str, Any]] = None, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        return await self._request("PUT", path, json=json, headers=headers)

    async def delete(self, path: str, headers: Optional[Dict[str, str]] = None) -> httpx.Response:
        return await self._request("DELETE", path, headers=headers)

