"""App configuration store for status management service.

Provides an in-memory configuration snapshot seeded from environment
variables while allowing runtime updates via the status service
operations. The store keeps metadata about when and by whom the
configuration was updated to surface richer information to the
main APP routes.
"""
from __future__ import annotations

import json
import os
from copy import deepcopy
from datetime import datetime, timezone
from typing import Any, Dict, Optional


def _utc_now_iso() -> str:
    """Return the current UTC time in ISO-8601 format."""

    return datetime.now(timezone.utc).isoformat()


def _safe_json_loads(raw: Optional[str]) -> Dict[str, Any]:
    """Parse a JSON string if provided, otherwise return an empty dict."""

    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}


class AppConfigurationStore:
    """Lightweight configuration provider for APP status endpoints."""

    def __init__(self, bootstrap_overrides: Optional[Dict[str, Any]] = None) -> None:
        self._config: Dict[str, Any] = self._load_defaults()
        if bootstrap_overrides:
            self._merge_dict(self._config, bootstrap_overrides)
        self._metadata: Dict[str, Any] = {
            "updated_at": None,
            "updated_by": None,
            "source": "bootstrap",
        }

    def _load_defaults(self) -> Dict[str, Any]:
        """Load configuration defaults from environment variables."""

        env = os.getenv("ENVIRONMENT", "development")
        firs_env = os.getenv("FIRS_ENVIRONMENT", "sandbox")
        api_base = os.getenv("APP_API_BASE_URL")
        outbound_threshold = os.getenv("AP_OUTBOUND_MAX_AGE_SECONDS", "0")
        strict_ops = os.getenv("ROUTER_STRICT_OPS", "false").lower() in {"1", "true", "yes"}
        validate_startup = os.getenv("ROUTER_VALIDATE_ON_STARTUP", "false").lower() in {"1", "true", "yes"}

        defaults: Dict[str, Any] = {
            "environment": env,
            "firs_environment": firs_env,
            "api": {
                "base_url": api_base,
                "docs_enabled": env == "development",
            },
            "routing": {
                "strict_operations": strict_ops,
                "validate_on_startup": validate_startup,
            },
            "messaging": {
                "ap_outbound_max_age_seconds": float(outbound_threshold or 0),
            },
            "features": {
                "tracking_alerts": True,
                "self_service_configuration": True,
            },
        }

        overrides = _safe_json_loads(os.getenv("APP_CONFIGURATION_OVERRIDES"))
        if overrides:
            self._merge_dict(defaults, overrides)

        return defaults

    def snapshot(self) -> Dict[str, Any]:
        """Return the current configuration and metadata."""

        return {
            "configuration": deepcopy(self._config),
            "metadata": {
                **self._metadata,
                "generated_at": _utc_now_iso(),
                "environment": os.getenv("ENVIRONMENT", "development"),
            },
        }

    def update_config(self, updates: Dict[str, Any], actor: Optional[str] = None) -> Dict[str, Any]:
        """Merge updates into the configuration and return a fresh snapshot."""

        if not isinstance(updates, dict):
            raise ValueError("Configuration updates must be a dictionary")

        self._merge_dict(self._config, updates)
        self._metadata["updated_at"] = _utc_now_iso()
        if actor:
            self._metadata["updated_by"] = actor

        return self.snapshot()

    @staticmethod
    def _merge_dict(target: Dict[str, Any], incoming: Dict[str, Any]) -> None:
        """Recursively merge ``incoming`` into ``target``."""

        for key, value in incoming.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                AppConfigurationStore._merge_dict(target[key], value)  # type: ignore[index]
            else:
                target[key] = value


__all__ = ["AppConfigurationStore"]

