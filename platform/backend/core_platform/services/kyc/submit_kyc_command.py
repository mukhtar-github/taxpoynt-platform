"""
SubmitKYCCommand
================

Background helper that fetches company information from Dojah after email
verification, encrypts the raw payload, and persists a normalized company
profile on the onboarding state metadata.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, AsyncIterator, Awaitable, Callable, Dict, Optional, Tuple

import httpx

from core_platform.data_management.db_async import get_async_session
from core_platform.data_management.repositories.onboarding_state_repo_async import (
    OnboardingStateRepositoryAsync,
)
from core_platform.security import get_jwt_manager

logger = logging.getLogger(__name__)


@dataclass
class SubmitKYCCommandConfig:
    """Runtime configuration for Dojah lookups."""

    api_key: Optional[str]
    app_id: Optional[str]
    base_url: str
    lookup_path: str
    http_method: str
    timeout_seconds: float
    fallback_country: str

    @classmethod
    def from_env(cls) -> "SubmitKYCCommandConfig":
        return cls(
            api_key=os.getenv("DOJAH_API_KEY"),
            app_id=os.getenv("DOJAH_APP_ID"),
            base_url=os.getenv("DOJAH_BASE_URL", "https://api.dojah.io"),
            lookup_path=os.getenv("DOJAH_COMPANY_LOOKUP_PATH", "/api/v1/kyc/company"),
            http_method=os.getenv("DOJAH_LOOKUP_METHOD", "GET").upper(),
            timeout_seconds=float(os.getenv("DOJAH_TIMEOUT_SECONDS", "10")),
            fallback_country=os.getenv("DOJAH_FALLBACK_COUNTRY", "Nigeria"),
        )

    @property
    def is_enabled(self) -> bool:
        return bool(self.api_key)

    @property
    def endpoint(self) -> str:
        if self.lookup_path.startswith(("http://", "https://")):
            return self.lookup_path
        return f"{self.base_url.rstrip('/')}/{self.lookup_path.lstrip('/')}"


Fetcher = Callable[[SubmitKYCCommandConfig, Dict[str, str]], Awaitable[Optional[Dict[str, Any]]]]
SessionProvider = Callable[[], AsyncIterator[Any]]
RepoFactory = Callable[[Any], OnboardingStateRepositoryAsync]


class SubmitKYCCommand:
    """Coordinates Dojah lookups and onboarding metadata persistence."""

    def __init__(
        self,
        config: Optional[SubmitKYCCommandConfig] = None,
        *,
        session_provider: Optional[SessionProvider] = None,
        repo_factory: Optional[RepoFactory] = None,
        fetcher: Optional[Fetcher] = None,
    ) -> None:
        self._config = config or SubmitKYCCommandConfig.from_env()
        self._session_provider = session_provider or get_async_session
        self._repo_factory = repo_factory or (lambda session: OnboardingStateRepositoryAsync(session))
        self._fetcher = fetcher or self._fetch_from_dojah
        self._jwt_manager = None

    async def execute(
        self,
        *,
        user_id: str,
        service_package: Optional[str],
        tin: Optional[str] = None,
        rc_number: Optional[str] = None,
        email: Optional[str] = None,
    ) -> None:
        """Fetch company info from Dojah and persist onboarding metadata."""
        identifier, secondary_identifier = self._resolve_identifier(tin, rc_number)
        if not identifier:
            logger.debug("SubmitKYCCommand skipped for %s (no TIN/RC provided)", user_id)
            return

        if not self._config.is_enabled:
            logger.debug("SubmitKYCCommand skipped for %s (Dojah disabled)", user_id)
            return

        params: Dict[str, str] = {identifier["type"]: identifier["value"]}
        if secondary_identifier:
            params[secondary_identifier["type"]] = secondary_identifier["value"]
        if email:
            params["email"] = email

        raw_payload = await self._fetcher(self._config, params)
        if not raw_payload:
            logger.info(
                "SubmitKYCCommand: no Dojah match for %s (%s)",
                identifier["value"],
                identifier["type"],
            )
            return

        normalization = self._normalize_company_profile(
            raw_payload,
            identifier,
            secondary_identifier,
        )
        if not normalization:
            logger.info("SubmitKYCCommand: unable to normalize Dojah payload for %s", user_id)
            return

        company_profile, profile_details = normalization
        await self._persist_company_profile(
            user_id=user_id,
            service_package=service_package or "si",
            company_profile=company_profile,
            profile_details=profile_details,
            raw_payload=raw_payload,
        )

    def _resolve_identifier(
        self, tin: Optional[str], rc_number: Optional[str]
    ) -> Tuple[Optional[Dict[str, str]], Optional[Dict[str, str]]]:
        def _sanitize(value: Optional[str]) -> Optional[str]:
            if not value:
                return None
            token = value.strip()
            return token or None

        tin_value = _sanitize(tin)
        rc_value = _sanitize(rc_number)

        if tin_value:
            primary = {"type": "tin", "value": tin_value}
            secondary = {"type": "rc_number", "value": rc_value} if rc_value else None
            return primary, secondary
        if rc_value:
            primary = {"type": "rc_number", "value": rc_value}
            secondary = None
            return primary, secondary
        return None, None

    async def _fetch_from_dojah(
        self, config: SubmitKYCCommandConfig, params: Dict[str, str]
    ) -> Optional[Dict[str, Any]]:
        """Call Dojah's company lookup endpoint."""
        headers = {
            "Authorization": f"Bearer {config.api_key}",
            "x-api-key": config.api_key or "",
        }
        if config.app_id:
            headers["AppId"] = config.app_id
            headers["x-app-id"] = config.app_id

        timeout = httpx.Timeout(config.timeout_seconds)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                method = config.http_method or "GET"
                if method == "POST":
                    response = await client.post(config.endpoint, headers=headers, json=params)
                else:
                    response = await client.get(config.endpoint, headers=headers, params=params)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPStatusError as exc:
            logger.warning(
                "Dojah lookup failed (%s): %s",
                exc.response.status_code,
                exc.response.text,
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Dojah lookup error: %s", exc, exc_info=True)
        return None

    def _normalize_company_profile(
        self,
        payload: Dict[str, Any],
        identifier: Dict[str, str],
        secondary_identifier: Optional[Dict[str, str]],
    ) -> Optional[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """Transform Dojah's payload into the wizard's company profile schema."""
        data = self._extract_entity(payload)
        if not isinstance(data, dict):
            return None

        def pick(*keys: str) -> Optional[Any]:
            for key in keys:
                if not key:
                    continue
                value = data.get(key)
                if value not in (None, ""):
                    return value
            return None

        registered_name = pick("company_name", "registered_name", "entity_name", "name")
        industry = pick("industry", "sector", "business_type") or ""
        status = pick("status", "company_status", "registration_status")
        country = pick("country", "country_of_operation") or self._config.fallback_country
        address = pick("registered_address", "address", "head_office_address")
        directors = data.get("directors")
        if not isinstance(directors, list):
            directors = []

        team_size = pick("employee_count", "team_size", "staff_strength")
        team_size_str = str(team_size) if team_size not in (None, "") else ""

        company_profile = {
            "companyName": registered_name or "",
            "industry": industry or "",
            "teamSize": team_size_str,
            "country": str(country) if country else self._config.fallback_country,
        }

        details: Dict[str, Any] = {
            "source": "dojah",
            "verified_at": self._now_iso(),
            "status": status,
            "address": address,
            "country": company_profile["country"],
            "directors": directors,
            "identifier": {
                identifier["type"]: identifier["value"],
            },
            "registration_date": pick("registration_date", "incorporation_date"),
            "raw_keys": sorted(list(data.keys())),
        }

        tin_value = pick("tin", "tax_identification_number")
        if tin_value:
            details.setdefault("tin", str(tin_value))
        rc_value = pick("rc_number", "rc", "registration_number")
        if rc_value:
            details.setdefault("rc_number", str(rc_value))

        if secondary_identifier:
            details["identifier"][secondary_identifier["type"]] = secondary_identifier["value"]

        return company_profile, details

    def _extract_entity(self, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        for key in ("entity", "result", "data", "company"):
            value = payload.get(key)
            if isinstance(value, dict):
                return value
        return payload if isinstance(payload, dict) else None

    async def _persist_company_profile(
        self,
        *,
        user_id: str,
        service_package: str,
        company_profile: Dict[str, Any],
        profile_details: Dict[str, Any],
        raw_payload: Dict[str, Any],
    ) -> None:
        encrypted_payload = self._encrypt_payload(raw_payload)
        fetched_at = profile_details.get("verified_at", self._now_iso())

        async for session in self._session_provider():
            repo = self._repo_factory(session)
            record = await repo.ensure_state(user_id, service_package)

            metadata = dict(record.state_metadata or {})
            metadata["company_profile"] = company_profile

            details_snapshot = dict(metadata.get("company_profile_details") or {})
            details_snapshot.update(profile_details)
            details_snapshot["source"] = "dojah"
            details_snapshot["verified_at"] = fetched_at
            metadata["company_profile_details"] = details_snapshot

            kyc_records = dict(metadata.get("kyc_records") or {})
            kyc_records["dojah"] = {
                "provider": "dojah",
                "fetched_at": fetched_at,
                "identifier": profile_details.get("identifier"),
                "encrypted_payload": encrypted_payload,
                "status": profile_details.get("status"),
            }
            metadata["kyc_records"] = kyc_records

            record.state_metadata = metadata
            now = datetime.now(timezone.utc)
            record.updated_at = now
            record.last_active_date = now

            await repo.persist(record)
            break

    def _encrypt_payload(self, payload: Dict[str, Any]) -> Optional[str]:
        try:
            manager = self._jwt_manager or get_jwt_manager()
            self._jwt_manager = manager
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("JWT manager unavailable for payload encryption: %s", exc)
            return None

        try:
            serialized = json.dumps(payload, separators=(",", ":"), ensure_ascii=False)
            return manager.encrypt_sensitive_data(serialized)
        except Exception as exc:
            logger.warning("Failed to encrypt Dojah payload: %s", exc)
            return None

    @staticmethod
    def _now_iso() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

