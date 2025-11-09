TaxPoynt Platform — Agent Guide (AGENTS.md)

Audience: AI coding agents (Codex CLI) and contributors working in this repository. Use this as the source of truth for how to navigate the codebase, make changes safely, and validate work.

Scope: This file applies to the entire repository.


Principles For Agents
- Work surgically: keep changes minimal, focused, and consistent with existing patterns. Do not reformat whole files or refactor unrelated code.
- Preserve architecture: follow the API Gateway, versioning, and role-based routing model already in place.
- Prefer small, explicit patches: explain what you’ll do, then apply targeted edits.
- Validate locally when possible; surface clear next steps for the user to run tests or the app.
- Respect security and compliance: never print or commit secrets; keep auth, rate limiting, and security headers intact.
- Use existing abstractions: RoleDetector, PermissionGuard, VersionCoordinator, MessageRouter, and core services.
- Follow repository tooling guidelines: use ripgrep to search, read files in <=250-line chunks, and prefer `apply_patch` for edits.


Repository Overview
- Backend (FastAPI): `platform/backend`
  - API Gateway & Versioning: `api_gateway/` (role detection, permissions, routers per version & role)
  - Core Platform: `core_platform/` (security, messaging, monitoring, data models)
  - Services: `app_services/`, `si_services/`, `hybrid_services/` (registered with message router)
  - External Integrations: `external_integrations/`
  - App entrypoint: `platform/backend/main.py` (production boot + middleware + routers)
- Frontend (Next.js 14): `platform/frontend`
  - App routes: `platform/frontend/app`
  - Shared components: `platform/frontend/shared_components`
  - Starts on port 3001 (see `package.json`)
- Tests: `platform/tests` (unit/integration/e2e harness) and root live test scripts
- Deployment: Railway (backend) via `railway.toml`, Vercel (frontend) via `vercel.json`, root `Procfile` and `build.sh`


Running Locally (Dev)
- Backend
  - Minimal: `python -m uvicorn platform.backend.main:app --reload --port 8000`
  - Railway-style: `python main.py` (root) — sets `PYTHONPATH` and runs the FastAPI app
  - Docs are enabled only when `ENVIRONMENT=development`
  - Health: `GET /health` (fast, non-blocking)
- Optional Services (docker-compose)
  - `docker-compose -f docker-compose.dev.yml up -d` (Postgres on 5433, Redis on 6380)
- Frontend
  - `cd platform/frontend && npm install && npm run dev` (port 3001)
  - Ensure `NEXT_PUBLIC_API_URL` points to backend, e.g. `http://localhost:8000/api/v1`


Testing & Validation
- Prefer `platform/tests` (unit/integration/e2e) and simple health tests:
  - `python test_local_health.py` (root) or use the test runners in `platform/tests`
- Live “integration” scripts at repo root (e.g., `live_firs_*`) may hit real services and need network access. Do not run them unless explicitly asked/authorized.


Coding Standards
- Python (FastAPI)
  - Target: Python 3.11; Pydantic v1 is pinned (see `platform/backend/requirements.txt` → `pydantic==1.10.22`). Do not upgrade to v2 unless explicitly requested.
  - Use type hints and clear docstrings; keep logging informative and consistent with existing style.
  - Keep endpoints async when performing I/O; avoid blocking operations in request handlers.
  - Reuse core abstractions (security headers, rate limiter, role detection) instead of ad‑hoc implementations.
  - Return response shapes consistent with existing versioned response models where applicable.
- TypeScript/React (Next.js)
  - Use TypeScript types; keep components small and composable.
  - Respect existing structure in `app/` routes and `shared_components/`.
  - Read API base from `NEXT_PUBLIC_API_URL`; do not hardcode service URLs in components.


API Gateway & Versioning
- Main version-aware router: `platform/backend/api_gateway/main_gateway_router.py` (mounted under `/api`).
- Version coordination: `api_gateway/api_versions/version_coordinator.py`
  - v1 is STABLE; v2 is DEVELOPMENT. Deprecation/migration helpers and headers are provided.
  - To add a new version, register in `VersionCoordinator` and create the parallel `api_versions/v{N}` tree.
- Role-specific routers (v1):
  - SI endpoints under `/api/v1/si/...` in `api_versions/v1/si_endpoints`
  - APP endpoints under `/api/v1/app/...` in `api_versions/v1/app_endpoints`
  - Hybrid endpoints under `/api/v1/hybrid/...` in `api_versions/v1/hybrid_endpoints`
- Role detection & guard: use `HTTPRoleDetector` and `APIPermissionGuard` dependencies for protected routes.


Security & Compliance
- JWT: provided by `core_platform/security/jwt_manager.py`; auth endpoints live in `api_gateway/role_routing/auth_router.py` (DB wired via `auth_database.py`).
- Rate Limiting & Security Headers: wired in `platform/backend/main.py` via `initialize_rate_limiter` and `initialize_security_headers`.
- CORS: configured first in `platform/backend/main.py` — maintain ordering to avoid preflight issues.
- Do not expose secrets or raw exceptions; keep error handling aligned with Phase 6 error management.


Messaging & Services
- Message Router: Redis-backed in `core_platform/messaging/redis_message_router.py`. Use `register_service(...)` with a callback for operations.
- APP/SI/Hybrid services register their capabilities in `app_services/__init__.py`, `si_services/__init__.py`, `hybrid_services/__init__.py`.
- Callbacks must return a consistent dict: `{ "operation": str, "success": bool, "data"|"error": ... }`.
- Fault Tolerance: Circuit breakers, retry manager, and dead letter handling are available. Prefer using them for external calls and critical operations.

Router Operation Validation
- Strict runtime check: set `ROUTER_STRICT_OPS=true` to make the MessageRouter raise on any `route_message` call whose `operation` is not advertised by a registered service. Default is warn-only.
- Startup validation: set `ROUTER_VALIDATE_ON_STARTUP=true` to scan mounted API handlers and check that every static `operation="..."` used in handlers is advertised by at least one service. Set `ROUTER_FAIL_FAST_ON_STARTUP=true` to raise during startup when mismatches are found (recommended for CI).
- Notes:
  - Validation is best-effort (regex over handler source). Dynamic operation names are ignored.
  - Keep service metadata (`metadata={"operations": [...]}` in `register_service`) in sync with any new/renamed handler ops to avoid warnings/errors.


Database
- SQLAlchemy models in `core_platform/data_management/models/*` (e.g., `user.py`, `organization.py`).
- Auth DB helper: `api_gateway/role_routing/auth_database.py` (uses Postgres via `DATABASE_URL` with SQLite fallback). For simple user/org changes, prefer aligning with existing model fields.
- For schema changes, coordinate with Alembic or the established migration helpers; keep runtime migrations safe and idempotent.


Observability
- Middleware: `core_platform/monitoring/fastapi_middleware.py` (Prometheus metrics, OpenTelemetry traces).
- If you add new critical endpoint groups (e.g., new business areas), update `business_patterns` if helpful for tracing/metrics labeling.


Frontend Integration
- API base URL comes from `NEXT_PUBLIC_API_URL` (see `vercel.json` rewrites for production).
- Keep role-based UI separation: app/si/business/hybrid interfaces and `shared_components`.
- Avoid embedding backend secrets or internal logic client-side.


Deployment
- Backend: Railway (`railway.toml`, `Procfile`, `build.sh`); do not change deployment commands or healthcheck paths unless asked.
- Frontend: Vercel (`vercel.json`); rewrites `/api/*` to the backend. Keep these stable unless requested.


Common Tasks (How-To)
- Add a new SI endpoint (v1)
  1) Pick the right module under `api_versions/v1/si_endpoints/` or add one if needed.
  2) Define an async route handler with `Depends(self._require_si_role)` or appropriate guard.
  3) If it calls a service, route via the MessageRouter to the correct service callback.
  4) Return response using existing v1 response model patterns (see `version_models.py`).
 5) Add the route to `main_router.py` for SI if it belongs in the main grouping.

- Unified onboarding QA expectations:
  - Run the Playwright suite (`RUN_ONBOARDING_E2E=true PLAYWRIGHT_BASE_URL=http://localhost:3001 npx playwright test platform/tests/e2e/onboarding/si_onboarding.spec.ts`) whenever you touch signup/email/Dojah/Mono/Odoo flows. The spec exercises signup → email verification → Dojah hydrate → Mono consent → Odoo demo connection; Mono steps auto-skip when credentials are unavailable, but you should supply them for full coverage.
  - Keep the wizard collapsible (Mono + Odoo cards). Updates must continue persisting `banking_connections.mono` and `erp_connections.odoo` metadata so telemetry + auto-completion of the `system-connectivity` step stay accurate.
  - We intentionally keep Mono/Odoo extraction on-demand in development/staging; **do not** add a background 15-minute scheduler until the production go-live doc requests it. Capture any cadence proposals in `docs/development/sync_cadence_notes.md`.
  - After launch, `/dashboard/si` must show the hero with the “Next pull: Manual (Run now)” controls and chip helpers sourced from the stored Mono/Odoo metadata. The Playwright spec now asserts hero visibility plus chip copy after onboarding.
  - Keep the hero chip controls accessible: preserve the existing `aria-live` helper text, descriptive `aria-label` on the “Run now” buttons, and the current focus order (chip card → manual pull button → hero CTAs).
- Accessibility/responsive notes for the Mono/Odoo UI live in `docs/ONBOARDING_ACCESSIBILITY_NOTES.md`. Review them before altering card layouts or status chips to keep the new flows screen-reader friendly.

- Register a new APP service
  1) Implement the service logic (or wrap an external client) in `app_services/...`.
  2) In `app_services/__init__.py`, initialize and register via `message_router.register_service` with metadata and a callback.
  3) Ensure the callback returns the standard `{operation, success, data|error}` shape and uses retry/circuit breaker if calling external APIs.

- Add a new API version (v2+)
  1) Create `api_gateway/api_versions/v2/...` mirroring v1 structure.
  2) Register version info and routing in `VersionCoordinator` (status, rate limits, router modules).
  3) If deprecating older versions, set deprecation in `VersionCoordinator` to surface headers and migration guidance.


Pitfalls & Gotchas
- CORS must be added first (already correctly placed in `platform/backend/main.py`). Don’t move it behind other middleware.
- Pydantic v1 is required; don’t mix v2 APIs.
- API docs are disabled in production; develop with `ENVIRONMENT=development` if you need Swagger locally.
- Messaging (Redis) and DB may be unavailable in some dev runs; code should degrade gracefully (already handled by Phase 6 patterns).
- Live tests at root require network; avoid running them in restricted sandboxes.


Sensitive Files & Env
- `.env` exists locally — never commit secrets from it. Prefer env vars for config.
- Redis URL (`REDIS_URL`) and Database URL (`DATABASE_URL`) should be injected by the environment in production.


Agent Tooling Reminders (Codex CLI)
- Before shell/tool calls, send a brief preamble summarizing your next action.
- Use `update_plan` for multi-step work; keep one step `in_progress` at a time.
- Use `rg` for searching and read files in chunks up to ~250 lines.
- Use `apply_patch` for edits (don’t attempt to write files via ad‑hoc shell redirection in restricted environments).
- Don’t run networked or destructive commands without approval; prefer proposing changes and asking to run tests.


Quality Checklist Before Finishing
- Changes are minimal, scoped, and follow existing structure and naming.
- Security middleware (JWT/rate limiting/security headers) remains intact.
- New endpoints are mounted under the correct version/role router and protected appropriately.
- Logging is informative; errors route through existing error management where relevant.
- Any new service is registered with the MessageRouter and returns the standard callback shape.
- Local instructions to run/validate are included in your final message to the user if useful.
- If you added or changed route operations, ensure service metadata includes them; enable `ROUTER_VALIDATE_ON_STARTUP=true` locally to sanity-check mappings.

Async DB + Tenant Context (Scaffold)
- Async DB sessions: use `core_platform.data_management.db_async.get_async_session` as a FastAPI dependency to obtain an `AsyncSession`.
  - Initializes an async engine lazily with `DATABASE_URL` (auto-converted to async drivers: `postgresql+asyncpg`, `sqlite+aiosqlite`).
  - Keep legacy sync code paths unchanged; migrate endpoints/services incrementally.
- Tenant context: use `core_platform.authentication.tenant_context` helpers to propagate a per-request `tenant_id`.
  - `set_current_tenant`, `get_current_tenant`, `tenant_context(...)`, `apply_tenant_from_obj(...)`.
  - Set from routing context at request entry; repositories may read it to apply row-level filtering.
- Migration guidance:
  - Start with non-critical endpoints; avoid mixing sync/async DB usage in the same handler.
  - Do not introduce implicit commits in dependencies; manage transactions explicitly as needed.

When to use `db_async.py` vs `database_abstraction.py`
- Use `db_async.py` (AsyncSession DI) for new or migrated async FastAPI handlers and repositories. It provides minimal, lightweight async engine/session helpers.
- Use `database_abstraction.py` (sync DAL) in legacy sync code paths or scripts that already depend on the sync session model. Do not try to intermix sync and async sessions within the same handler.
- Long term, prefer migrating read-heavy endpoints to async for better concurrency, while leaving complex write paths on sync DAL until fully planned migration.

Shared Tenant Dependency
- To reuse tenant scoping across APP routers, use `api_gateway/dependencies/tenant.py`:
  - `make_tenant_scope_dependency(self._require_app_role)` returns a dependency that sets the tenant from `HTTPRoutingContext`.
  - Attach to routes: `dependencies=[Depends(self.tenant_scope)]`.


Database DI Policy (FastAPI Handlers)
- Use `core_platform.data_management.db_async.get_async_session` for all FastAPI handlers. This yields an `AsyncSession` and initializes an async engine lazily from `DATABASE_URL`.
- Do NOT import or depend on these in handlers (deprecated for request-time DI):
  - `core_platform.data_management.connection_pool.get_db_session`
  - `core_platform.data_management.database_init.get_db_session`
- Sync sessions remain supported for non-HTTP/internal services and background tasks that already use the sync DAL.
- Tests enforce this policy: `platform/tests/unit/test_di_standardization.py` scans handler modules for deprecated DI imports.
- Migrations: For PostgreSQL, Alembic runs at startup; `create_all` is gated to dev/test. Control with:
  - `ALEMBIC_RUN_ON_STARTUP=true|false` (default true)
  - `ALEMBIC_MIGRATIONS_PATH` (override scripts path)


Boot & Health Flow (DB + Observability)
- Single DB init path
  - The app initializes DB via `database_init.initialize_database()` inside `main.initialize_services`. Do not add separate `connection_pool.initialize_connection_pool()` calls during startup.
  - For FastAPI handlers, keep using async DI (`db_async.get_async_session`). Sync `get_db_session` helpers remain for non‑HTTP/background jobs only.

- Health checks (unified)
  - The async health checker prefers the `database_init` path for DB health via `get_database().health_check()`. It only falls back to a lightweight `SELECT 1` using `connection_pool.get_db_session()` if `database_init` is not available. This keeps health status aligned with the actual session provider.

- Observability
  - Observability is initialized once via `core_platform.monitoring.setup_production_observability(...)` from `main.initialize_services`.
  - `ObservabilityMiddleware` provides request‑level metrics/tracing and does not duplicate the Phase 4 initialization.

- Quick references
  - Startup: `platform/backend/main.py`
  - DB init: `platform/backend/core_platform/data_management/database_init.py`
  - Async DI: `platform/backend/core_platform/data_management/db_async.py`
  - Health checker: `platform/backend/core_platform/messaging/async_health_checker.py`
  - `ALLOW_CREATE_ALL=true|false` (dev-only fallback in non-dev envs)
