"""
SI HTTP Helper
==============
Thin wrapper for message router calls that maps common exceptions to
specific HTTP status codes to avoid repetitive try/except blocks in
endpoint handlers.
"""
from __future__ import annotations

from typing import Any, Dict
from fastapi import HTTPException


def _map_error_code_to_status(code: str) -> int:
    c = (code or "").lower()
    if c in ("not_found", "missing", "404"):
        return 404
    if c in ("validation_error", "unprocessable_entity", "422"):
        return 422
    if c in ("conflict", "409"):
        return 409
    if c in ("forbidden", "permission_denied", "403"):
        return 403
    if c in ("unauthorized", "401"):
        return 401
    return 502


async def route_or_http(
    message_router: Any,
    *,
    service_role: Any,
    operation: str,
    payload: Dict[str, Any],
    expect_success: bool = True,
) -> Dict[str, Any]:
    """Route a message via the MessageRouter or raise an HTTPException with a specific code.

    Maps common exceptions to:
    - ValueError -> 400 Bad Request
    - PermissionError -> 403 Forbidden
    - KeyError -> 404 Not Found
    - TimeoutError -> 504 Gateway Timeout
    - Other exceptions -> 502 Bad Gateway
    """
    try:
        result = await message_router.route_message(
            service_role=service_role,
            operation=operation,
            payload=payload,
        )
        # Optionally interpret standard result envelope and raise HTTPException on failures
        if expect_success and isinstance(result, dict) and result.get("success") is False:
            err = result.get("error")
            if isinstance(err, dict):
                code = err.get("code") or err.get("error_code") or "upstream_error"
                status = _map_error_code_to_status(code)
                msg = err.get("message") or code
                raise HTTPException(status_code=status, detail=msg)
            elif isinstance(err, str):
                status = _map_error_code_to_status(err)
                raise HTTPException(status_code=status, detail=err)
            else:
                raise HTTPException(status_code=502, detail="Upstream error")
        return result
    except HTTPException:
        # Respect explicit HTTPExceptions thrown upstream
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=403, detail=str(e))
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TimeoutError:
        raise HTTPException(status_code=504, detail="Upstream timeout")
    except Exception as e:
        # Generic upstream error
        raise HTTPException(status_code=502, detail=str(e) or "Upstream error")
