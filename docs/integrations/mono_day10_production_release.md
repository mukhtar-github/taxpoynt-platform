# Day 10 – Mono Production Release

## Feature Flag Strategy
- **Toggle:** `MONO_TRANSACTIONS_ENABLED`
  - Default: `false`
  - Deployment: Enable on production hosts once staging validation completes.
  - Behaviour: When disabled, the `sync_banking_transactions` operation returns a deferred response with enablement guidance. When enabled, the Mono pipeline executes end-to-end (fetch → transform → persist) using live credentials.

## Deployment Checklist
1. **Pre-flight**
   - Ensure `MONO_SECRET_KEY`, `MONO_APP_ID`, and related Mono env vars are populated in production.
   - Provision Prometheus/Grafana changes (Day 9 dashboard + alert updates).
   - Confirm webhook endpoint `https://<prod-domain>/api/v1/webhooks/mono/integrations/mono/webhook` is registered in Mono console with the correct signing secret.

2. **Rolling Release**
   - Deploy backend build with the Day 6–9 changes.
   - Flip `MONO_TRANSACTIONS_ENABLED=true` on a single production instance (canary) and monitor for 15 minutes.
   - Gradually roll out the flag across all instances; keep the flag value stored in configuration management for quick rollback.

3. **Monitoring Window** (2 hours post-flag)
   - Metrics: `taxpoynt_mono_pipeline_stage_seconds`, `taxpoynt_mono_pipeline_errors_total`, `taxpoynt_mono_pipeline_zero_transactions_total` (filter by `account_id`).
   - Alerts: Ensure `MonoPipelineHighFailureRate`, `MonoPipelineLatencySLA`, and `MonoPipelineZeroTransactions` remain inactive.
   - Logs: Tail Loki for `mono-pipeline` to confirm correlation IDs and event flow.

4. **Data Verification**
   - Run `./live_mono_staging_smoke_test.py` (with production credentials) against a low-volume account to confirm persistence.
   - Execute SQL spot-checks comparing Mono totals to canonical totals.

## Legacy Pipeline Retirement
- The previous stubbed `sync_banking_transactions` response is removed; feature flag now controls access to the live Mono pipeline.
- Documentation and runbooks updated (Day 8–9 notes).
- Any cron jobs or automation targeting legacy endpoints should be repointed to call the new flag-driven workflow.

## Rollback Procedure
1. Toggle `MONO_TRANSACTIONS_ENABLED=false` (immediately halts new sync attempts).
2. Revert to last known-good build if required.
3. Inspect Prometheus alerts and clear any residual `mono.fetch.*` dead-letter events.
4. Communicate rollback status to support/ops teams; capture incident notes for retrospectives.
