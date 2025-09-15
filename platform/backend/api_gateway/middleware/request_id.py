"""
X-Request-ID Middleware
=======================

Ensures every request has an X-Request-ID header and propagates it to the response.
Adds `request.state.request_id` for downstream handlers and services.
"""
from __future__ import annotations

import uuid
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        req_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        # Attach to state
        setattr(request.state, "request_id", req_id)
        # Continue
        response = await call_next(request)
        # Propagate to response
        response.headers["X-Request-ID"] = req_id
        return response

