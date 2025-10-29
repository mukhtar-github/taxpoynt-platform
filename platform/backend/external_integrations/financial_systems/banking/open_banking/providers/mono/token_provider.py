"""Token provider utilities for Mono integration."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Awaitable, Callable, Dict, Optional

from hybrid_services.configuration_management import ConfigurationManagementService


@dataclass
class MonoTokenBundle:
    """Access token payload fetched from secrets manager."""

    access_token: str
    refresh_token: Optional[str] = None
    expires_at: Optional[datetime] = None

    @classmethod
    def from_dict(cls, payload: Dict[str, Any]) -> "MonoTokenBundle":
        expires_at = None
        if payload.get("expires_at"):
            expires_at = datetime.fromisoformat(payload["expires_at"])
        return cls(
            access_token=payload["access_token"],
            refresh_token=payload.get("refresh_token"),
            expires_at=expires_at,
        )


MonoRefreshCallback = Callable[[Optional[MonoTokenBundle]], Awaitable[MonoTokenBundle]]


class SecretBackedMonoTokenProvider:
    """Loads Mono OAuth tokens from the configuration management secrets service."""

    def __init__(
        self,
        config_service: ConfigurationManagementService,
        secret_id: str,
        refresh_callback: MonoRefreshCallback,
    ) -> None:
        self._service = config_service
        self._secret_id = secret_id
        self._refresh_callback = refresh_callback
        self._bundle: Optional[MonoTokenBundle] = None
        self._lock = asyncio.Lock()

    async def get_access_token(self) -> str:
        async with self._lock:
            if not self._bundle or self._is_expired(self._bundle):
                await self._load_bundle()
            return self._bundle.access_token  # type: ignore[union-attr]

    async def refresh_access_token(self) -> str:
        async with self._lock:
            new_bundle = await self._refresh_callback(self._bundle)
            self._bundle = new_bundle
            return new_bundle.access_token

    async def _load_bundle(self) -> None:
        response = await self._service.handle_platform_configuration(
            operation="manage_secret",
            action="get",
            secret_id=self._secret_id,
        )
        payload = response.get("value") or {}
        self._bundle = MonoTokenBundle.from_dict(payload)

    @staticmethod
    def _is_expired(bundle: MonoTokenBundle) -> bool:
        if bundle.expires_at is None:
            return False
        return bundle.expires_at <= datetime.utcnow() + timedelta(minutes=5)


__all__ = ["SecretBackedMonoTokenProvider", "MonoTokenBundle", "MonoRefreshCallback"]
