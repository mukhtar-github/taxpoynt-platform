"""
SI Observability Utilities
==========================
Prometheus metrics and helpers to instrument SI v1 endpoints with per-op
latency and success/error counters.
"""
from __future__ import annotations

import time
from typing import Optional
from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse
from prometheus_client import Counter, Histogram


SI_REQUEST_LATENCY_SECONDS = Histogram(
    "si_request_latency_seconds",
    "SI request latency in seconds",
    labelnames=("method", "path", "action", "status_code"),
)

SI_REQUESTS_TOTAL = Counter(
    "si_requests_total",
    "Total SI requests",
    labelnames=("method", "path", "action", "status_code"),
)

SI_ERRORS_TOTAL = Counter(
    "si_errors_total",
    "Total SI errors",
    labelnames=("method", "path", "action", "status_code", "error_code"),
)


def _extract_action(req: Request, resp: Optional[Response] = None) -> str:
    # Try to extract from response payload if present
    try:
        if isinstance(resp, JSONResponse) and isinstance(resp.body, (bytes, bytearray)):
            # Avoid parsing heavy bodies; fall back to route path
            pass
    except Exception:
        pass
    # Fallback to route pattern or handler name
    try:
        route = req.scope.get("route")
        if route and getattr(route, "name", None):
            return str(route.name)
        if route and getattr(route, "path", None):
            return str(route.path)
    except Exception:
        pass
    return req.url.path


def install_si_instrumentation(router: APIRouter) -> None:
    """Attach lightweight instrumentation where supported.

    APIRouter in FastAPI does not expose a .middleware decorator. When running in
    contexts that only provide routers (like unit tests), this becomes a no-op.
    """
    if not hasattr(router, "middleware"):
        # No router-level middleware support; skip instrumentation
        return
    try:
        @router.middleware("http")  # type: ignore[attr-defined]
        async def _si_metrics_middleware(request: Request, call_next):  # type: ignore
            start = time.perf_counter()
            method = request.method
            path = request.url.path
            action = _extract_action(request)
            status_code = "500"
            resp: Response
            try:
                resp = await call_next(request)
                status_code = str(resp.status_code)
                return resp
            finally:
                dur = max(0.0, time.perf_counter() - start)
                SI_REQUEST_LATENCY_SECONDS.labels(method, path, action, status_code).observe(dur)
                SI_REQUESTS_TOTAL.labels(method, path, action, status_code).inc()
    except Exception:
        # Best-effort instrumentation; never break router creation
        return
