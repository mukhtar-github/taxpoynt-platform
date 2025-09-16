Tenant Scoping Overview
=======================

This platform uses a per-request tenant context to enforce data isolation across APP and SI routes. The context is stored in a ContextVar and consumed by async repositories to apply organization-level filters.

Key Components
- Middleware: `api_gateway.middleware.tenant_scope.TenantScopeMiddleware`
  - Sets tenant context for `/api/v1/app/*` from `request.state.routing_context`.
  - Also supports `/api/v1/si/*` and will fall back to the `org_id` query parameter if no tenant is present in the routing context.
- Dependency: `api_gateway.dependencies.tenant.make_tenant_scope_dependency`
  - Factory to create a route-level dependency that sets the tenant context using an APP role guard. This is attached to all APP sub-routers.
- Repositories: Async repositories under `core_platform.data_management.repositories.*_async.py`
  - Read tenant via `core_platform.authentication.tenant_context.get_current_tenant()` and apply a filter to `organization_id`.

SI Routes and org_id
- For SI routes, if the authentication layer does not populate a tenant in `request.state.routing_context`, the middleware will read `org_id` from the query string (e.g., `/api/v1/si/organizations?org_id=<UUID>`).
- Handlers that explicitly scope the tenant via `set_current_tenant(...)` remain compatible; the middleware is non-intrusive and clears the context after the request.

MultiTenantManager Alignment
- On startup, `core_platform.data_management.multi_tenant_manager.initialize_tenant_manager(...)` is invoked and stored on `app.state.tenant_manager`.
- The tenant dependency will attempt to align that manager by calling `set_tenant_context(...)` when both tenant and organization IDs can be parsed.

Overriding org_id Behavior (SI)
- To override or restrict `org_id` usage:
  - Validate `org_id` in your route (e.g., ensure it matches the authenticated SI’s managed organizations) before performing reads.
  - Alternatively, add a small SI-specific dependency that sets tenant strictly from your own authorization logic and ignores query params.

Notes
- To deactivate SI query parameter fallback globally, remove the fallback logic in `TenantScopeMiddleware` or introduce an env flag to guard it.
- For APP routes, use `make_tenant_scope_dependency` at router include sites (already wired) for consistent behavior.
