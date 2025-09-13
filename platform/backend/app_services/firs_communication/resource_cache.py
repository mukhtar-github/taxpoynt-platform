"""
FIRS Resource Cache
===================
In-memory cache with TTL for FIRS static resources:
- currencies
- invoice-types
- services-codes
- vat-exemptions

Provides simple get/refresh helpers and returns shaped payloads.
"""
import time
from typing import Any, Dict, Optional

from .firs_http_client import FIRSHttpClient


class FIRSResourceCache:
    def __init__(self, client: Optional[FIRSHttpClient] = None, ttl_seconds: int = 3600):
        self.client = client or FIRSHttpClient()
        self.ttl = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        # cache entry shape: {"data": <payload>, "ts": epoch}

    def _is_fresh(self, key: str) -> bool:
        entry = self._cache.get(key)
        if not entry:
            return False
        return (time.time() - entry.get("ts", 0)) < self.ttl

    def _set(self, key: str, data: Any):
        self._cache[key] = {"data": data, "ts": time.time()}

    def _get(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        return entry.get("data") if entry else None

    async def get_resources(self) -> Dict[str, Any]:
        # Returns all resources, fetching missing/stale as needed
        out: Dict[str, Any] = {}
        for key in ("currencies", "invoice-types", "services-codes", "vat-exemptions"):
            if not self._is_fresh(key):
                await self.refresh_resource(key)
            out[key] = self._get(key)
        return out

    async def refresh_all(self) -> Dict[str, Any]:
        for key in ("currencies", "invoice-types", "services-codes", "vat-exemptions"):
            await self.refresh_resource(key)
        return await self.get_resources()

    async def refresh_resource(self, resource: str) -> Dict[str, Any]:
        # Fetch single resource from FIRS
        res = await self.client.get_resource(resource)
        if res.get("success"):
            # Store the 'data' field from FIRS response directly
            self._set(resource, res.get("data"))
        else:
            # Preserve any previous cache on failure
            # Attach error to a meta field for callers if needed
            self._set(resource, {"error": res.get("error"), "status_code": res.get("status_code")})
        return {resource: self._get(resource)}

