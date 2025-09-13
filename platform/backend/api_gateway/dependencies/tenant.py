"""
Shared Tenant Dependency Utilities
=================================

Factory for creating a FastAPI dependency that sets the tenant ContextVar
from an HTTPRoutingContext-producing dependency (e.g., a role guard).

Usage in a router class:

    from api_gateway.dependencies.tenant import make_tenant_scope_dependency

    class SomeEndpoints:
        def __init__(...):
            self.tenant_scope = make_tenant_scope_dependency(self._require_app_role)
            self.router.add_api_route(
                ...,
                dependencies=[Depends(self.tenant_scope)]
            )
"""
from __future__ import annotations

from typing import Callable, AsyncGenerator
from fastapi import Depends

from api_gateway.role_routing.models import HTTPRoutingContext
from core_platform.authentication.tenant_context import (
    set_current_tenant,
    clear_current_tenant,
)


def make_tenant_scope_dependency(
    role_context_dependency: Callable[..., HTTPRoutingContext]
) -> Callable[..., AsyncGenerator[None, None]]:
    """Create a dependency that sets tenant from HTTPRoutingContext.

    The provided `role_context_dependency` must return an HTTPRoutingContext
    (e.g., a role guard). This dependency will set tenant_id to
    `context.organization_id` (fallback to `context.tenant_id`) for the
    duration of the request and clear it afterwards.
    """

    async def tenant_scope(
        context: HTTPRoutingContext = Depends(role_context_dependency),
    ) -> AsyncGenerator[None, None]:
        tenant = context.organization_id or context.tenant_id
        set_current_tenant(str(tenant) if tenant else None)
        try:
            yield
        finally:
            clear_current_tenant()

    return tenant_scope


__all__ = ["make_tenant_scope_dependency"]

