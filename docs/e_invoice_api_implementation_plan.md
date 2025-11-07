# e-invoice-api – Incremental Implementation Plan

This document outlines a day-by-day delivery plan for standing up the new **e-invoice-api** repository using the provided DDD-friendly scaffold. Each task group is sized so it can be tackled in its own feature branch (e.g., `feat/<module-name>`), reviewed via PR, and merged independently.

The plan assumes we are migrating capabilities from the existing `platform/backend` codebase into the new structure while modernising around the new boundaries.

---

## Guiding Principles
- **DDD alignment:** Keep bounded contexts (invoicing, compliance, onboarding) isolated; domain logic lives in `contexts/<context>/domain`.
- **Foundation first:** Phases 0–3 must leave a production-ready skeleton (settings, security, middleware, DB/migrations, CI) before any context work merges.
- **Incremental vertical slices:** Each branch delivers a cohesive slice—domain → application → infrastructure → API—with passing tests and docs.
- **Shared services early:** Messaging, observability, and background job scaffolds should exist before contexts depend on them.
- **Platform compatibility checklist:** Every merge checks auth/tenant hooks, observability metrics, messaging, and migrations.
- **Configuration-first:** Secrets remain out of repo; use `config/settings.example.env` + Pydantic Settings for environment parity.
- **Telemetry/security parity:** Carry across JWT, permission guards, observability hooks from the source repo early in the migration.
- **Testing mirrors structure:** Unit tests under `tests/unit/...`, integration/end-to-end under `tests/integration` and `tests/e2e`.

---

## Phase 0 – Preparation (Day 0)✅
**Branch:** `feat/bootstrap-repo`
- Initialise repository using scaffold (directories, placeholder files, `.editorconfig`, `.gitignore`, `pyproject.toml` with tooling stub).
- Add CONTRIBUTING + ADR template in `docs/`.
- Set up base CI workflow (`infra/ci/github-actions.yaml`) running lint + tests.
- Provide README baseline covering project purpose, architecture, branch strategy.
- Acceptance:
  - `uv/poetry/pip install` (or chosen tool) works.
  - `pytest` (empty) + `ruff`/`black`/`mypy` placeholders pass.

---

## Phase 1 – Platform Core (Days 1–2)✅
### Day 1 – Settings & Infrastructure Primitives
**Branch:** `feat/core-settings`
- Implement `src/qorebox_einvoice/core/settings.py` with Pydantic Settings (env layering, Secrets support).
- Populate `config/settings.example.env`, `config/logging.yaml`, `config/telemetry.toml`.
- Port existing logging initialisation utilities.
- Tests: unit tests for settings loader (env precedence, default values).

### Day 2 – Security & Auth Foundations✅
**Branch:** `feat/core-security`
- Migrate JWT manager, permission guard, tenant context helpers into `core/security` and `core/auth`.
- Provide FastAPI dependency placeholders (`app/dependencies.py`) for tenant + role detection.
- Add unit tests for token creation/validation, permission guard behaviour.

---

## Phase 2 – HTTP Edge + Middleware (Days 3–4)
### Day 3 – FastAPI Composition Root✅
**Branch:** `feat/app-main`
- Implement `src/qorebox_einvoice/app/main.py` with `create_app()`, basic middleware chain (CORS, rate limiting placeholder, telemetry stub).
- Wire health route under `app/routes/v1/health.py`.
- Add `scripts/smoke_health.py`.
- Tests: integration test hitting `/health` using `TestClient`.

### Day 4 – Middleware & Dependency Wiring✅
**Branch:** `feat/app-middleware`
- Port middleware implementations (idempotency, observability, request context).
- Implement dependency providers (db session stub, auth).
- Update main to include middleware ordering tests.
- Add integration test ensuring security headers & request id middleware.

---

## Phase 3 – Data Access & Persistence (Days 5–6)
### Day 5 – Database Layer & Migrations✅
**Branch:** `feat/db-alembic`
- Configure SQLAlchemy engine factory, session management inside `core/db` (or `core/utils/db.py`).
- Set up Alembic env + initial migration.
- `scripts/bootstrap_db.py` to run migrations locally.
- Tests: integration test verifying connection + basic migration runs in SQLite/Postgres (CI-friendly).

### Day 6 – Shared Repository + Value Objects✅
**Branch:** `feat/core-shared`
- Port shared DTOs, identifiers, value objects.
- Implement base repository interfaces (async) for reuse across contexts.
- Unit tests for value objects and repository protocol conformance (via fakes).

---

## Phase 4 – Invoicing Context (Days 7–9)
### Day 7 – Domain Model & Events
**Branch:** `feat/context-invoicing-domain`
- Port aggregate roots (Invoice, LineItem, etc.), value objects, domain events.
- Implement domain services (e.g., invoice total calculations).
- Tests: pure unit tests covering entities/events/services.
- **Platform checklist:** run full test suite; confirm logging/auth/migrations unaffected.

### Day 8 – Application Layer
**Branch:** `feat/context-invoicing-app`
- Implement commands, queries, handlers orchestrating domain logic.
- Add DTOs mapping HTTP payloads to domain commands.
- Tests: application layer unit tests using in-memory repositories.
- **Platform checklist:** exercise dependency wiring; ensure message bus hooks compile (even if stubbed).

### Day 9 – Infrastructure Ports
**Branch:** `feat/context-invoicing-infra`
- Implement SQLAlchemy repositories, mappers, external clients (e.g., FIRS adapter) within `contexts/invoicing/infrastructure`.
- Wire repository implementations into dependency injection.
- Integration tests: repository persistence roundtrips against test DB; HTTP contract tests for FIRS mock client.
- **Platform checklist:** verify metrics/logging for new routes; rerun lint/tests before merge.

---

## Phase 5 – Additional Contexts (Days 10–12)
### Day 10 – Compliance Context
**Branch:** `feat/context-compliance`
- Mirror Day 7–9 steps for compliance (domain → application → infrastructure).
- Focus on validation rules, audit logging, compliance event publishing.
- Include tests for regulatory workflows.
- **Platform checklist:** ensure compliance routes respect auth/tenant + observability.

### Day 11 – Onboarding & Checklist Flows
**Branch:** `feat/context-onboarding`
- Port onboarding state machine, metadata, analytics emission.
- Implement API routes under `app/routes/v1/onboarding.py`.
- Tests: integration tests covering sign-up → checklist retrieval using message bus fakes.
- **Platform checklist:** confirm analytics events flow through telemetry pipeline.

### Day 12 – Cross-Context Services
**Branch:** `feat/services-orchestrators`
- Migrate background jobs, orchestrators, message consumers interacting across contexts.
- Ensure consistent telemetry + retry strategy (reuse core/messaging abstractions).
- Tests: service-level unit tests with mocks for context boundaries.
- **Platform checklist:** verify background jobs integrate with shared messaging/observability.

---

## Phase 6 – Messaging & Observability (Days 13–14)
### Day 13 – Message Bus & Event Consumers
**Branch:** `feat/core-messaging`
- Port Redis/Kafka message bus abstractions, event bus, message router.
- Update contexts to publish/subscribe via shared bus.
- Integration test using embedded Redis or in-memory broker.
- **Platform checklist:** confirm existing contexts integrate with the bus without regressions.

### Day 14 – Observability & Alerting
**Branch:** `feat/core-observability`
- Implement unified logging/tracing/metrics initialisation (OpenTelemetry exporters, Prometheus collectors).
- Update `config/telemetry.toml` with dashboards/alert references.
- `scripts/verify_release.py` ensures telemetry endpoints respond.
- Tests: smoke tests verifying metrics endpoint and trace exporters configuration.
- **Platform checklist:** rerun regression suite; double-check dashboards/alerts.

---

## Phase 7 – Release Hardening & Platform Audits (Days 15–16)
### Day 15 – API Surface & Documentation
**Branch:** `feat/docs-api`
- Generate OpenAPI docs, update README with runbooks, add ADRs for contexts.
- Document branch/PR workflow and deployment checklist.
- Add `scripts/release_notes.py` template.
- **Platform checklist:** ensure docs capture configuration/feature flags introduced so far.

### Day 16 – Final QA & Cutover Prep
**Branch:** `feat/release-readiness`
- Run full test suite, load test critical endpoints, verify observability dashboards in staging.
- Ensure `config/settings.example.env` matches production requirements.
- Prepare migration playbook to cut over from legacy monolith to new service.
- **Platform checklist:** perform dependency audit, security scan, confirm rollback steps documented.

---

## Ongoing Maintenance Tasks
- **CI Enhancements:** Add lint, type-check stages, caching.
- **Code Quality:** Adopt pre-commit hooks mirroring fast feedback loops.
- **Performance Benchmarks:** Introduce Locust or k6 scenarios under `tests/performance`.
- **Security Review:** Integrate dependency scanning (e.g., GitHub Dependabot, pip-audit).
- **Quarterly hardening branches:** schedule `feat/platform-hardening` after major milestones to reconcile dependencies, refresh infra configs, and address tech debt.

---

## Major Functional Domains Migration

### System Integrator (SI) Integrations
- **Day 17 – SI Banking & Open Banking**
  - **Branch:** `feat/si-banking`
  - Port Mono/Stitch integration services and external ERP/Odoo connectors into `contexts/onboarding` or dedicated `contexts/si_integrations`.
  - Implement message bus handlers, webhook routers, and cursor persistence mirroring existing logic.
  - Tests: unit for SI services, integration hitting `/routes/v1/si/...`.
  - **Platform checklist:** confirm feature flags, logging, and observability coverage.

- **Day 18 – SI Onboarding + Analytics**
  - **Branch:** `feat/si-onboarding`
  - Move onboarding analytics emission, checklist state, and message router registrations.
  - Ensure `shared/event_bus.py` is leveraged for cross-service notifications.
  - **Platform checklist:** validate analytics events reach telemetry pipeline; rerun regression suite.

- **Day 19 – SI Reporting & Subscription**
  - **Branch:** `feat/si-reporting`
  - Port SI dashboards/reporting services, audit logs, and regulator exports.
  - Tests: repository + API contract tests; ensure Prometheus counters wired.
  - **Platform checklist:** verify audit logs, dashboards, and SI routes respect auth/tenant boundaries.

### APP Transmission Services
- **Day 20 – Transmission Core**
  - **Branch:** `feat/app-transmission-core`
  - Migrate APP transmission command handlers, FIRS submission workflows, and retry logic.
  - Wire FastAPI routes under `app/routes/v1/app/transmission.py`.
  - Tests: integration tests with fake FIRS endpoints, ensuring analytics events emitted.
  - **Platform checklist:** confirm rate limiting, messaging, and observability hooks updated.

- **Day 21 – Transmission Observability & Rate Limits**
  - **Branch:** `feat/app-transmission-observability`
  - Port transmission-specific metrics, alerts, and rate limit middleware.
  - Add smoke script in `scripts/verify_transmission.py`.
  - **Platform checklist:** ensure alerts fire in staging; update docs with new dashboards.

### Hybrid Shared Operations
- **Day 22 – Hybrid Aggregation Services**
  - **Branch:** `feat/hybrid-aggregation`
  - Move hybrid analytics aggregation, unified dashboards, and multi-context orchestration.
  - Ensure background jobs (Celery/RQ) reflect new package layout under `background/`.
  - **Platform checklist:** run end-to-end tests spanning SI + APP + Hybrid flows.

- **Day 23 – Shared Messaging & Tenant Context**
  - **Branch:** `feat/hybrid-shared-context`
  - Finalise shared abstractions consumed by SI/APP/Hybrid services (message router adapters, tenant policies).
  - Tests: integration ensuring tenant-aware routing across contexts.
  - **Platform checklist:** confirm tenant policies and message routing consistent post-refactor.

- **Day 24 – Final Domain Parity Review**
  - **Branch:** `feat/domain-parity-review`
  - Run diff between legacy platform and new repo; fill any gaps (edge cases, fallback routes).
  - Prepare cutover checklist for Hybrid shared operations.
  - **Platform checklist:** consolidate outstanding issues, confirm rollback paths, tag release candidate.

### Additional Modules (post-core)
- External integrations (ERP/Odoo, payroll, third-party tax services).
- Admin/support tooling (audit replay, maintenance endpoints).
- Legacy shims & shared utilities (feature flags, DAL helpers) to retire once parity confirmed.
- Schedule follow-on branches once primary contexts are stable.

---

## Branch Workflow Summary
1. `git checkout -b feat/<task-name>`
2. Implement scoped changes + tests.
3. Update docs/ADR if architectural impact.
4. `poetry run pytest` / `uv run pytest` + lint locally.
5. Push, open PR referencing this plan section.
6. After review, merge to main. Tag release candidates per milestone if desired.

---

This plan can be adjusted as we learn more during migration, but following the phases ensures the new API evolves in well-tested, reviewable increments that respect the DDD scaffold. Adapt the daily cadence as team capacity dictates while keeping branch scopes tight and observable.
