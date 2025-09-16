"""
APP Tenant Scope Middleware
==========================

Optional middleware that sets the tenant ContextVar for APP routes (/api/v1/app/*)
based on the HTTPRoutingContext placed on request.state by authentication middleware.

It is safe to use alongside the route-level dependency-based tenant scoping and is
designed to be non-intrusive: if no routing context is present, it does nothing.
"""
from __future__ import annotations

from typing import Optional
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from core_platform.authentication.tenant_context import (
    set_current_tenant,
    clear_current_tenant,
)


class TenantScopeMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path: str = str(request.url.path)
        applied = False
        try:
            if path.startswith("/api/v1/app") or path.startswith("/api/v1/si"):
                ctx = getattr(request.state, "routing_context", None)
                tenant = None
                if ctx:
                    tenant = getattr(ctx, "organization_id", None) or getattr(ctx, "tenant_id", None)
                # For SI routes, allow query param fallback (org_id)
                if not tenant and path.startswith("/api/v1/si"):
                    tenant = request.query_params.get("org_id")
                if tenant:
                    set_current_tenant(str(tenant))
                    applied = True
            response = await call_next(request)
            return response
        finally:
            if applied:
                clear_current_tenant()
