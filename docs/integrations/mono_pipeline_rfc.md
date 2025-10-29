# Mono Transaction Pipeline RFC (Draft)

> Draft created Day 0 – expanded during implementation.

## Objective
Describe the end-to-end pipeline for fetching financial transactions from Mono, transforming them into the TaxPoynt canonical schema, persisting them, and surfacing observability/alerting.

## Scope
- Mono REST polling (transaction history & incremental sync).
- Transformation layer + validation rules.
- Persistence & event publishing.
- Observability, alerting, retry strategy.

## Out of Scope
- Mono Connect UI changes.
- Downstream analytics dashboards (tracked separately).
- Non-banking Mono products (identity, income).

## Open Questions
- Final retention period for raw Mono payloads (currently 30 days).
- Tenant-specific rate limits from Mono dashboard.

## Next Steps
- Fill sections per Day 1–3 implementation milestones.
- Attach final sequence diagrams, component interfaces, and sample payloads.

## Day 2 Notes
- `MonoClient` wrapper introduced with built-in rate limiting, exponential backoff, and Prometheus instrumentation (service role `mono_open_banking`).
- Token loading delegated to `SecretBackedMonoTokenProvider`, enabling retrieval from the configuration management secrets service and pluggable refresh callbacks.
- Operation identifiers (`mono.fetch_transactions`, `mono.transform_transaction`) published in `operations.py` to keep retry manager and message router naming consistent.
- Day 3 introduced `MonoTransactionSyncService`, which orchestrates paginated fetches using the shared retry manager, idempotency guard, and synthetic fetch started/completed events.
- Day 5 wired `MonoTransactionPipeline` with the new ingestion service, persisting canonical records and emitting `bank.transactions.ingested` / `mono.pipeline.completed` events.

## Day 6–7 Updates (Observability, QA, and Handoff)
- Prometheus helpers (`observability.py`) now register Mono-specific histograms and counters:
  - `taxpoynt_mono_pipeline_stage_seconds` captures sync/transform/persist latency with outcome labels.
  - `taxpoynt_mono_pipeline_errors_total` counts failures by stage + exception class.
  - `taxpoynt_mono_pipeline_zero_transactions_total` tracks empty result sets for early warning.
- `MonoTransactionSyncService` and `MonoTransactionPipeline` propagate correlation IDs, emit structured events (`mono.fetch.failed`, `mono.fetch.latency_sla_exceeded`, `mono.fetch.zero_transactions`) and reset failure counters after successful runs.
- Alert thresholds: latency SLA >2s (warn + event), failure streak ≥5 (error + escalation payload).
- Regression coverage:
  - `platform/tests/unit/test_mono_transaction_sync.py`
  - `platform/tests/integration/test_mono_observability.py`
  - `platform/tests/integration/test_mono_pipeline_persistence.py`
  - Onboarding guardrails (`platform/tests/unit/test_auth_registration_verification_contracts.py`, `platform/tests/unit/test_onboarding_endpoints_contracts.py`, `platform/tests/integration/test_onboarding_regression.py`)

### Troubleshooting Playbook
| Symptom | Likely Cause | Diagnostic Steps | Mitigation |
| --- | --- | --- | --- |
| `mono.fetch.failed` events with increasing `failures` | Mono API outage / credential issues | Check Prometheus `taxpoynt_mono_pipeline_errors_total` labels, verify token freshness via secrets service | Rotate tokens, enable backoff override, notify Mono support if persistent |
| `mono.fetch.zero_transactions` trends | Account disconnected or wrong cursor window | Inspect account state in TaxPoynt admin and Mono dashboard, ensure cursor wasn’t advanced manually | Trigger manual resync with adjusted date range, confirm webhook connectivity |
| Latency alerts (`mono.fetch.latency_sla_exceeded`) | Slow downstream persistence or Mono latency spikes | Compare latency histogram across stages, review DB write metrics | Scale ingestion workers, enable shard-specific retry, tune AsyncSession pool |
| Missing metrics | Prometheus integration not initialised | Verify `get_prometheus_integration()` is configured at startup | Re-enable Prometheus init in `main.py` or fall back to MetricsAggregator |

### Rollback Strategy
1. Disable Mono ingestion from the VersionCoordinator feature flag (halts scheduled sync jobs).
2. Revert deployment to pre-Day6 build; failure counters reset automatically.
3. Manually clear queued `mono.fetch.*` events from the message router dead-letter queue (if present).
4. Run health checks:
   - `pytest -q platform/tests/unit/test_mono_transaction_sync.py -k "not observability"`
   - Smoke ingest via staging account to confirm canonical persistence.

### Monitoring Window Plan
- 2-hour hypercare window post-release with Mono dashboards + Prometheus live charts for:
  - Stage latency histogram P95
  - Failure streak counter per account
  - Zero-transaction counter deltas
- Synthetic fetch every 30 minutes using sandbox credentials; raise PagerDuty if two consecutive failures.

### Security Review Summary
- PII still resides only in encrypted Postgres (AES-256 at rest); canonical transactions include masked account numbers.
- Mono API secrets stored in the configuration service; runtime tokens kept in memory for ≤60 minutes.
- Webhook signature verification remains enabled (HMAC SHA-512 using `MONO_WEBHOOK_SECRET`); no changes required.
- Observability payloads scrub account identifiers before logging (correlation IDs are opaque UUIDs).

## Day 8 – Staging Dry Run
- Staging playbook recorded in `docs/integrations/mono_day8_staging_dry_run.md` covering deployment, smoke scripts, dashboard validation, and sign-off checklist.
- Live runner script `./live_mono_staging_smoke_test.py` executes the full pipeline using staging credentials, persists canonical records, and prints integrity summaries.
- Prometheus alert rules (`monitoring/prometheus_rules/mono_pipeline_alerts.yml`) and Grafana dashboard (`monitoring/grafana/dashboards/mono_pipeline.json`) wired for latency/failure/zero-transaction monitoring.

## Day 9 – Feedback Buffer
- Dashboard tweaks incorporate account-level filtering, Markdown context, and Loki log streaming for `mono-pipeline` events.
- Prometheus alert rules now scope to `provider="mono"` and leverage the new `account_id` label emitted by the observability helpers.
- Additional notes and operational reminders captured in `docs/integrations/mono_day9_feedback_buffer.md`.
