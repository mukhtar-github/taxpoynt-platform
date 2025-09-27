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
import hashlib
from typing import Any, Dict, Optional

from .firs_http_client import FIRSHttpClient


class FIRSResourceCache:
    def __init__(self, client: Optional[FIRSHttpClient] = None, ttl_seconds: int = 3600):
        self.client = client or FIRSHttpClient()
        self.ttl = ttl_seconds
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._etag_index: Dict[str, str] = {}
        self._last_modified_index: Dict[str, float] = {}
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

    def get_resource_etag(self, key: str) -> Optional[str]:
        return self._etag_index.get(key)

    def get_resource_last_modified(self, key: str) -> Optional[float]:
        return self._last_modified_index.get(key)

    def _update_metadata(self, key: str, payload: Any) -> None:
        try:
            import json
            serialized = json.dumps(payload, sort_keys=True, default=str)
        except Exception:
            serialized = str(payload)
        digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
        self._etag_index[key] = digest
        self._last_modified_index[key] = time.time()

    def get_combined_etag(self) -> Optional[str]:
        if not self._etag_index:
            return None
        concat = ''.join(sorted(self._etag_index.values()))
        return hashlib.sha256(concat.encode("utf-8")).hexdigest()

    def get_last_modified(self) -> Optional[float]:
        if not self._last_modified_index:
            return None
        return max(self._last_modified_index.values())

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
            payload = res.get("data")
            self._set(resource, payload)
            self._update_metadata(resource, payload)
        else:
            # Preserve any previous cache on failure
            # Attach error to a meta field for callers if needed
            self._set(resource, {"error": res.get("error"), "status_code": res.get("status_code")})
        return {resource: self._get(resource)}

