"""
V1 Error Mapping Utility
========================

Centralized helpers to translate repository/service exceptions
into stable V1ErrorModel envelopes with consistent HTTP status codes.
"""
from __future__ import annotations

import logging
from typing import Dict, Any, Tuple
from fastapi.responses import JSONResponse

from ..api_versions.v1.si_endpoints.version_models import V1ErrorModel

# Repository exceptions
try:
    from core_platform.data_management.repository_base import (
        RepositoryError,
        EntityNotFoundError,
        DuplicateEntityError,
    )
except Exception:  # pragma: no cover - defensive import for partial envs
    class RepositoryError(Exception):
        pass
    class EntityNotFoundError(RepositoryError):
        pass
    class DuplicateEntityError(RepositoryError):
        pass

logger = logging.getLogger(__name__)


def map_exception_to_v1_error(exc: Exception, *, action: str = "operation_failed") -> Tuple[V1ErrorModel, int]:
    """Map known exceptions to V1ErrorModel + HTTP status code.

    - EntityNotFoundError -> 404 NOT_FOUND
    - DuplicateEntityError -> 409 CONFLICT
    - RepositoryError      -> 500 REPOSITORY_ERROR
    - ValueError           -> 400 VALIDATION_ERROR
    - PermissionError      -> 403 FORBIDDEN
    - default              -> 500 INTERNAL_ERROR
    """
    error_code = "INTERNAL_ERROR"
    status_code = 500
    details: Dict[str, Any] = {}

    if isinstance(exc, EntityNotFoundError):
        error_code = "NOT_FOUND"
        status_code = 404
    elif isinstance(exc, DuplicateEntityError):
        error_code = "CONFLICT"
        status_code = 409
    elif isinstance(exc, RepositoryError):
        error_code = "REPOSITORY_ERROR"
        status_code = 500
    elif isinstance(exc, ValueError):
        error_code = "VALIDATION_ERROR"
        status_code = 400
    elif isinstance(exc, PermissionError):
        error_code = "FORBIDDEN"
        status_code = 403

    # Provide a concise message; avoid leaking internals
    message = str(exc) or error_code.replace("_", " ").title()

    model = V1ErrorModel(
        success=False,
        error=message,
        error_code=error_code,
        details={"action": action} if action else None,
    )
    return model, status_code


def v1_error_response(exc: Exception, *, action: str = "operation_failed") -> JSONResponse:
    """Build a JSONResponse for an exception using V1ErrorModel mapping."""
    model, status_code = map_exception_to_v1_error(exc, action=action)
    try:
        # Minimal structured log
        logger.warning(
            "V1 error response: code=%s status=%s action=%s message=%s",
            model.error_code, status_code, action, model.error,
        )
    except Exception:
        pass
    return JSONResponse(status_code=status_code, content=model.dict())


__all__ = ["map_exception_to_v1_error", "v1_error_response"]

