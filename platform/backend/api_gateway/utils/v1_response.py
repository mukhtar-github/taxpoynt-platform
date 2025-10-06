"""
V1 Response Helper
==================

Provides a single helper to build V1ResponseModel instances to keep
responses consistent and eliminate hardcoded timestamps.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from ..api_versions.v1.si_endpoints.version_models import V1ResponseModel


def build_v1_response(payload: Any, action: str) -> V1ResponseModel:
    """Create a standardized V1ResponseModel.

    When the payload is a dict returned from a service callback, we extract the
    canonical fields (success/data/error/etc.) so consumers see the expected
    domain object shape and the success flag reflects the underlying result.
    """

    success = True
    data = payload
    meta: Optional[Dict[str, Any]] = None

    if isinstance(payload, dict):
        if isinstance(payload.get("success"), bool):
            success = payload["success"]

        extra_fields: Dict[str, Any] = {
            key: value for key, value in payload.items() if key not in {"success", "data"}
        }

        if "data" in payload:
            data = payload["data"]
            if extra_fields:
                meta = extra_fields
        elif not success and "error" in payload:
            data = {"error": payload["error"]}
            if "error" in extra_fields:
                extra_fields.pop("error")
            if extra_fields:
                meta = extra_fields
        else:
            # No dedicated data payload; fall back to the remaining fields
            data = extra_fields or payload

    return V1ResponseModel(success=success, action=action, data=data, meta=meta)


__all__ = ["build_v1_response"]
