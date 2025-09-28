"""Certificate provider for FIRS integrations.

Provides a single place to look up the current base64-encoded certificate
used in outbound FIRS requests. The provider can source certificates from
the SI certificate lifecycle store when available and gracefully fall back
to environment variables so existing behaviour continues to work when the
store is not configured.
"""

from __future__ import annotations

import base64
import os
import threading
import time
from dataclasses import dataclass
from typing import Dict, Optional, Sequence, Tuple

try:  # Optional import – the store lives in the SI services package
    from si_services.certificate_management.certificate_store import (  # type: ignore
        CertificateStatus,
        CertificateStore,
        StoredCertificate,
    )
except Exception:  # pragma: no cover - store not always available in tests
    CertificateStore = None  # type: ignore
    CertificateStatus = None  # type: ignore
    StoredCertificate = None  # type: ignore


@dataclass
class _CacheEntry:
    value: Optional[str]
    expires_at: float


class FIRSCertificateProvider:
    """Resolve active certificates for outbound FIRS calls."""

    def __init__(
        self,
        certificate_store: Optional["CertificateStore"] = None,
        *,
        env_vars: Optional[Sequence[str]] = None,
        cache_ttl_seconds: int = 300,
        default_certificate_type: str = "signing",
    ) -> None:
        self._certificate_store = certificate_store
        self._env_vars = tuple(env_vars or ("FIRS_CERTIFICATE", "FIRS_ENCRYPTION_KEY"))
        self._cache_ttl = max(cache_ttl_seconds, 0)
        self._default_certificate_type = default_certificate_type

        self._cache_lock = threading.Lock()
        self._cache: Dict[Tuple[Optional[str], Optional[str]], _CacheEntry] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def get_active_certificate(
        self,
        organization_id: Optional[str] = None,
        certificate_type: Optional[str] = None,
    ) -> Optional[str]:
        """Return a base64 encoded certificate suitable for the FIRS header."""

        cache_key = (certificate_type or self._default_certificate_type, organization_id)
        if self._cache_ttl:
            cached = self._get_cached(cache_key)
            if cached is not None:
                return cached

        certificate = self._resolve_from_store(
            organization_id=organization_id,
            certificate_type=certificate_type,
        )
        if not certificate:
            certificate = self._resolve_from_environment()

        self._set_cached(cache_key, certificate)
        return certificate

    def refresh(
        self,
        organization_id: Optional[str] = None,
        certificate_type: Optional[str] = None,
    ) -> None:
        """Invalidate cached certificate values."""

        cache_key = (certificate_type or self._default_certificate_type, organization_id)
        with self._cache_lock:
            if cache_key in self._cache:
                del self._cache[cache_key]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_cached(self, key: Tuple[Optional[str], Optional[str]]) -> Optional[str]:
        with self._cache_lock:
            entry = self._cache.get(key)
            if not entry:
                return None
            if entry.expires_at and entry.expires_at < time.time():
                del self._cache[key]
                return None
            return entry.value

    def _set_cached(self, key: Tuple[Optional[str], Optional[str]], value: Optional[str]) -> None:
        if self._cache_ttl <= 0:
            return
        with self._cache_lock:
            self._cache[key] = _CacheEntry(value=value, expires_at=time.time() + self._cache_ttl)

    # Store resolution ---------------------------------------------------
    def _resolve_from_store(
        self,
        *,
        organization_id: Optional[str],
        certificate_type: Optional[str],
    ) -> Optional[str]:
        store = self._certificate_store
        if not store or CertificateStatus is None:
            return None

        cert_type = certificate_type or self._default_certificate_type
        try:
            certificates = store.list_certificates(
                organization_id=organization_id,
                certificate_type=cert_type,
                status=CertificateStatus.ACTIVE,
            )
        except Exception:
            return None

        if not certificates:
            return None

        # Pick the newest certificate (by updated_at) to align with rotation semantics
        latest: Optional["StoredCertificate"] = None
        for cert in certificates:
            if not latest:
                latest = cert
                continue
            try:
                current_ts = self._parse_iso_timestamp(cert.updated_at)
                latest_ts = self._parse_iso_timestamp(latest.updated_at)
                if current_ts > latest_ts:
                    latest = cert
            except Exception:
                continue

        if not latest:
            return None

        try:
            raw_certificate = store.retrieve_certificate(latest.certificate_id)
        except Exception:
            return None

        if not raw_certificate:
            return None

        if isinstance(raw_certificate, str):
            raw_certificate = raw_certificate.encode("utf-8")

        return base64.b64encode(raw_certificate).decode("ascii")

    # Environment fallback ----------------------------------------------
    def _resolve_from_environment(self) -> Optional[str]:
        for env_var in self._env_vars:
            value = os.getenv(env_var)
            if value:
                return value.strip()
        return None

    @staticmethod
    def _parse_iso_timestamp(value: str) -> float:
        from datetime import datetime

        # datetime.fromisoformat handles offsets in Python 3.11+; fallback to naive
        try:
            return datetime.fromisoformat(value).timestamp()
        except Exception:
            return 0.0


__all__ = ["FIRSCertificateProvider"]
