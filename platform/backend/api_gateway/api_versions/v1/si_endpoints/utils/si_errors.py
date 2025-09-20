"""
SI Error Mapping Utilities
==========================
Helpers to standardize error responses for SI v1 using V1ErrorModel and
to map exceptions into error codes and proper HTTP status.
"""
from __future__ import annotations

from typing import Any, Dict
from fastapi import Request
from fastapi.responses import JSONResponse
from fastapi import HTTPException

from ..version_models import V1ErrorModel
from .si_observability import SI_ERRORS_TOTAL


def map_exception_to_error(exc: Exception) -> Dict[str, Any]:
    if isinstance(exc, HTTPException):
        code = {
            400: "bad_request",
            401: "unauthorized",
            403: "forbidden",
            404: "not_found",
            409: "conflict",
            422: "validation_error",
        }.get(exc.status_code, "http_error")
        return {"error_code": code, "status_code": exc.status_code, "message": str(exc.detail or "HTTP error")}
    # Default internal error
    return {"error_code": "internal_error", "status_code": 500, "message": str(exc) or "Internal server error"}


def build_error_response(request: Request, exc: Exception) -> JSONResponse:
    mapped = map_exception_to_error(exc)
    model = V1ErrorModel(
        success=False,
        error=mapped["message"],
        error_code=mapped["error_code"],
    )
    # Observe error
    try:
        action = request.url.path
        SI_ERRORS_TOTAL.labels(request.method, request.url.path, action, str(mapped["status_code"]), mapped["error_code"]).inc()
    except Exception:
        pass
    return JSONResponse(status_code=mapped["status_code"], content=model.dict())

