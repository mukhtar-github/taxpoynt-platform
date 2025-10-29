# Day 9 – Feedback Buffer Notes

## QA / UAT Feedback Addressed
- Added account-aware panels in `monitoring/grafana/dashboards/mono_pipeline.json`: account filter variable, Markdown header, and Loki-backed “Alerts & Events” stream for quick correlation.
- Prometheus alert rules now scope to `provider="mono"` and respect per-account latency / zero-transaction labels (`monitoring/prometheus_rules/mono_pipeline_alerts.yml`).
- Mono observability helpers emit metrics with an `account_id` label (Mono API id for sync, canonical `account_db_id` for transform/persist) to support finer-grained dashboards.

## Operational Checklist
- When publishing the updated dashboard, ensure Grafana has `prometheus` and `loki` data sources with UIDs matching provisioning (`prometheus`, `loki`).
- After Prometheus reload, confirm alerts appear under `/alerts` with the new label dimensions.
- For staging validation, re-run `./live_mono_staging_smoke_test.py` and verify panels refresh when filtering by the target account.

## Rollback / Release Confirmation
- Release window & rollback flow documented in `docs/integrations/mono_day8_staging_dry_run.md#7-release-schedule--rollback-confirmation`.
- No schema changes introduced today; dashboard + alert updates can be reverted by restoring prior JSON/YAML if necessary.
