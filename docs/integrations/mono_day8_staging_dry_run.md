# Day 8 – Mono Staging Dry Run

## Objectives
- Validate Mono sandbox credentials in a staging deployment.
- Exercise the end-to-end fetch → transform → persist pipeline against real data.
- Confirm dashboards and alert rules reflect pipeline activity.
- Capture smoke test + data integrity evidence before production launch.

---

## 1. Deploy to Staging
1. **Set environment variables** (Railway / staging host):
   - `MONO_SECRET_KEY`, `MONO_APP_ID`, `MONO_PUBLIC_KEY` (sandbox values)
   - `MONO_WEBHOOK_SECRET`, `MONO_VERIFY_WEBHOOKS=true`
   - `MONO_RATE_LIMIT_PER_MINUTE` (optional override, default 60)
   - `MONO_DEFAULT_TRANSACTION_LIMIT` (optional, default 50)
   - `MONO_ENVIRONMENT=sandbox`
   - `MONO_TRANSACTIONS_ENABLED=true` (staging only during dry run)
   - `ROUTER_VALIDATE_ON_STARTUP=true` and `ROUTER_FAIL_FAST_ON_STARTUP=true` (ensures service metadata alignment)
   - Standard DB/env secrets (`DATABASE_URL`, `REDIS_URL`, `JWT_SECRET_KEY`, etc.)

2. **Prometheus/Grafana update**
   - Mount `monitoring/prometheus.yml` and `monitoring/prometheus_rules/mono_pipeline_alerts.yml`.
   - Provision dashboard JSONs under `/var/lib/grafana/dashboards` including:
     - `monitoring/grafana/dashboards/queue_sla.json`
     - `monitoring/grafana/dashboards/mono_pipeline.json`
   - Reload Prometheus (`SIGHUP` or container restart) to pick up new alert rules.

3. **Webhooks**
   - Configure Mono dashboard to point to `https://<staging-domain>/api/v1/webhooks/mono/integrations/mono/webhook`.
   - Verify webhook secret matches `MONO_WEBHOOK_SECRET`.

---

## 2. Execute Smoke Test
1. SSH into the staging application container (Python virtualenv activated).
2. Run the live smoke script with staging credentials:

```bash
DATABASE_URL="postgresql+asyncpg://..." \
MONO_API_ACCOUNT_ID="acc_sandbox_123" \
MONO_PROVIDER_ACCOUNT_ID="provider-1" \
MONO_ACCOUNT_NUMBER="0123456789" \
MONO_SECRET_KEY="sk_test..." \
MONO_APP_ID="app_test..." \
./live_mono_staging_smoke_test.py
```

Optional overrides:
- `MONO_ACCOUNT_DB_ID`, `MONO_CONNECTION_DB_ID` (UUIDs) if multiple accounts share the same provider id.
- `MONO_BASE_URL` (defaults to `https://api.withmono.com`).
- `MONO_PAGE_LIMIT` to throttle page size.

3. Expected output:
   - JSON events for `mono.fetch.started/completed`, `mono.pipeline.completed`.
   - Canonical transaction summary with non-zero counts.
   - No unhandled exceptions in stdout/stderr.

---

## 3. Data Integrity Checks
1. **Canonical totals**
   - Post-run, the script prints aggregated totals for the target `BankAccount`.
   - Cross-check balances by running:
     ```sql
     SELECT SUM(amount) AS total_amount, COUNT(*) AS txn_count
     FROM core_bank_transactions
     WHERE account_id = '<MONO_ACCOUNT_DB_ID>';
     ```
2. **Mono raw comparison**
   - From Mono dashboard or a direct API call, export the same date range.
   - Ensure `Σ amount` and record counts align (allowing for kobo vs naira conversion).

3. **Duplicate guard**
   - Re-run the smoke script; `inserted_count` should be 0 and `duplicate_count` should match prior insertions.

---

## 4. Observability Validation
1. **Grafana panels** (`Mono Banking Pipeline` dashboard):
   - `Pipeline Stage P95 Latency` shows recent sync run.
   - `Sync Failure Burndown` remains flat (no spikes).
   - `Zero Transaction Runs` increments only when expected (e.g., empty cursors).

2. **Alert Manager / Prometheus**
   - `MonoPipelineHighFailureRate` remains inactive (confirm in Prometheus `/alerts` UI).
   - Temporarily set `MONO_PAGE_LIMIT=1` and re-run to check histogram updates.

3. **Logs**
   - Tail application logs for correlation ids (`mono-sync-*`, `mono-pipeline-*`) to verify structured logging.

---

## 5. Manual Smoke Tests
- `GET /api/v1/si/banking/open-banking` (with SI auth headers) – list connections.
- `POST /api/v1/si/banking/open-banking/mono/link` – ensure widget link generation still succeeds.
- `POST /api/v1/si/banking/open-banking/mono/callback` (sandbox payload) – confirm webhook handler processes signatures.

---

## 6. Sign-off Checklist
- [ ] Smoke script completes with non-zero `inserted_count`.
- [ ] Canonical totals match Mono source data.
- [ ] Grafana panels reflect the dry-run with fresh timestamps.
- [ ] No alerts firing in Prometheus/Alertmanager.
- [ ] Security review reconfirmed (secrets in vault, webhook verification on).
- [ ] Runbook updated with any staging-specific notes.

---

## 7. Release Schedule & Rollback Confirmation
- **Release window:** Target production push on Wednesday @ 09:00–11:00 WAT with ops + support on standby.
- **Pre-release checkpoint:** Re-run the smoke script within 2 hours of cutover and archive the JSON/SQL summaries.
- **Rollback ready:** Follow RFC rollback sequence (VersionCoordinator flag → deployment rollback → clear `mono.fetch.*` dead letters → targeted health checks). Validate that engineering + platform ops have access to required feature flags and secrets management prior to launch.
