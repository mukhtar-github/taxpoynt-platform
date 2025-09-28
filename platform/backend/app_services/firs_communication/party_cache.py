"""Caching helpers for FIRS party lookups and TIN verification."""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional


def _seconds_from_minutes(minutes: float) -> float:
    return max(0.0, minutes * 60.0)


@dataclass
class CacheEntry:
    data: Any
    expires_at: float
    etag: Optional[str] = None
    last_modified: Optional[float] = None

    def is_fresh(self) -> bool:
        return time.time() < self.expires_at


class PartyCache:
    """TTL cache for party lookups keyed by party ID."""

    def __init__(self, ttl_minutes: float = 30.0):
        self.ttl_seconds = _seconds_from_minutes(ttl_minutes)
        self._entries: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    async def get(self, party_id: str, *, allow_stale: bool = False) -> Optional[Any]:
        async with self._lock:
            entry = self._entries.get(party_id)
            if not entry:
                return None
            if entry.is_fresh():
                return entry.data
            if allow_stale:
                return entry.data
            return None

    async def set(self, party_id: str, payload: Any, *, ttl_override: Optional[float] = None) -> None:
        expires_at = time.time() + (ttl_override or self.ttl_seconds)
        async with self._lock:
            self._entries[party_id] = CacheEntry(data=payload, expires_at=expires_at)

    async def is_fresh(self, party_id: str) -> bool:
        async with self._lock:
            entry = self._entries.get(party_id)
            return bool(entry and entry.is_fresh())

    async def get_or_set(self, party_id: str, loader) -> Any:
        cached = await self.get(party_id)
        if cached is not None:
            return cached
        payload = await loader()
        await self.set(party_id, payload)
        return payload

    async def invalidate(self, party_id: str) -> None:
        async with self._lock:
            self._entries.pop(party_id, None)


class TINCache:
    """Cache for TIN verification results with TTL and optional grace period."""

    def __init__(self, ttl_minutes: float = 15.0):
        self.ttl_seconds = _seconds_from_minutes(ttl_minutes)
        self._entries: Dict[str, CacheEntry] = {}
        self._lock = asyncio.Lock()

    @staticmethod
    def _normalize_key(tin: str, extra: Optional[str] = None) -> str:
        base = tin.strip().upper()
        if extra:
            return f"{base}:{extra.strip().upper()}"
        return base

    async def get(self, tin: str, *, extra: Optional[str] = None, allow_stale: bool = False) -> Optional[Any]:
        key = self._normalize_key(tin, extra)
        async with self._lock:
            entry = self._entries.get(key)
            if not entry:
                return None
            if entry.is_fresh():
                return entry.data
            if allow_stale:
                return entry.data
            return None

    async def set(self, tin: str, payload: Any, *, extra: Optional[str] = None, ttl_override: Optional[float] = None) -> None:
        key = self._normalize_key(tin, extra)
        expires_at = time.time() + (ttl_override or self.ttl_seconds)
        async with self._lock:
            self._entries[key] = CacheEntry(data=payload, expires_at=expires_at)

    async def is_fresh(self, tin: str, *, extra: Optional[str] = None) -> bool:
        key = self._normalize_key(tin, extra)
        async with self._lock:
            entry = self._entries.get(key)
            return bool(entry and entry.is_fresh())

    async def invalidate(self, tin: str, *, extra: Optional[str] = None) -> None:
        key = self._normalize_key(tin, extra)
        async with self._lock:
            self._entries.pop(key, None)
