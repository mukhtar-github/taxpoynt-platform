# Day 8 Launch Readiness Plan

## 1. Feedback & Micro-interactions
- Verification CTA copy locked: "Verify email and continue" (matches regression suite).
- Checklist badge: "Verify account — Email confirmed and terms accepted" shows once analytics confirms completion.
- Autosave chip: ensured status chip remains visible after verification (no flicker during regression).

## 2. Observability Dashboards
- Prometheus dashboard panels validated via synthetic FIRS request (taxpoynt_http_requests_total, taxpoynt_http_request_duration_seconds).
- Alert thresholds: FIRS latency >2s triggers warning; synthetic tests confirm metric ingestion.
- OpenTelemetry traces confirm span metadata (`taxpoynt.service_role`, `taxpoynt.business_operation`).

## 3. Monitoring Windows
- **Primary launch window**: Tuesday 19:00 UTC (2 hr dedicated monitoring).
- **Extended observation**: follow-up 24 hr window with hourly checks.
- **On-call rotation**: Observability channel notified; pager escalation path documented in runbook.

## 4. Rollback Strategy
- Deploy is reversible via Vercel preview; fallback to last stable commit (tag `onboarding-v1.6`).
- Disable onboarding feature flag `ONBOARDING_V2_ENABLED=false` to revert UI quickly.
- Prometheus alert `taxpoynt_http_request_latency_high` set to WARN after 5 mins >2s; rapid rollback triggered if CRITICAL for 10 mins.

## 5. Sign-off Checklist
- [x] Regression suites green (pytest integration + unit).
- [x] Observability synthetic checks executed (`platform/tests/integration/test_observability_synthetic.py`).
- [x] Docs/release notes updated (Day 7 & Day 8).
- [x] Rollback + monitoring windows logged here and in release notes.
