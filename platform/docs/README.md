# TaxPoynt Platform — Developer Docs (Starter)

This folder holds shared developer documentation and canonical samples to align SI → HYBRID → APP → FIRS flows.

## Canonical Samples
- Odoo account.move style invoice sample: `samples/odoo_invoice_sample.json`

## SI Test Routes (Validate Fetch + Transform)
Use these to verify Odoo credentials and the SI transformation output before any APP submission.

- `POST /api/v1/si/erp/odoo/test-fetch-invoices`
  - Body keys: `invoice_ids[]`, `odoo_config{ url, database, username, auth_method, api_key|password }`, `transform` (default true), `target_format` (default `UBL_BIS_3.0`).
- `POST /api/v1/si/erp/odoo/test-fetch-batch`
  - Body keys: `batch_size`, `include_attachments`, `odoo_config{...}`, `transform`, `target_format`.

Both routes return `data.invoices` already in the APP‑ready payload shape for signing/transmission.

## Optional: Seed Odoo With Demo Data (Dev Only)
- `POST /api/v1/hybrid/demo/seed-odoo`
  - Set `DEMO_SEEDER_ENABLED=true` and Odoo env: `ODOO_URL`, `ODOO_DB`, `ODOO_USERNAME`, `ODOO_API_KEY|ODOO_PASSWORD`.
  - Helper implementation: `platform/backend/api_gateway/api_versions/v1/hybrid_endpoints/demo_endpoints.py`

## End-to-End Flow (High Level)
- SI fetches + transforms invoices (single source of truth)
- HYBRID coordinates/correlates
- APP persists + signs + transmits to FIRS

## Architecture Decisions (From Requirements)
- QR/CSID ownership: FIRS generates IRN, CSID, and QR. We never pre‑embed QR before FIRS approval.
- SI responsibilities: retrieve from ERP, map to UBL (55 mandatory fields), validate, and digitally sign (ECDSA/XAdES). Output an APP‑ready payload.
- APP responsibilities: validate shape + signature, transmit to FIRS (MBS), poll/receive IRN/CSID/QR, persist, and deliver to buyer’s AP (four‑corner). APP does not re‑transform.
- HYBRID role: correlation, cross‑role coordination, guardrails (rate limits, permissions), and analytics hooks.

## MVP Work Plan (MoSCoW → Concrete Tasks)
Target: Certification‑ready MVP aligned with APP/SI MUST‑HAVEs.

1) SI UBL completeness + schema validation (MUST)
- Expand Odoo → FIRS transformer to cover all 55 mandatory fields.
- Add strict UBL 3.0/BIS Billing validation (reject with actionable errors).
- Output canonical APP‑signing payload (already shaped) with versioning.

2) SI Digital signature (MUST)
- Implement ECDSA signing for XML/JSON; integrate certificate storage (si_services.certificate_management).
- Produce: { signature, signature_algorithm, certificate_id, signed_at }.
- Add “validate_signature” SI op for APP pre‑submission checks.

3) APP transmission + status polling (MUST)
- Enhance TransmissionService to: validate → sign (if needed) → transmit.
- Persist IRN, CSID, QR in FIRSSubmission (add columns if absent) and expose retrieval.
- Add polling/confirm endpoints and background task for 2–4 hour SLA.

4) HYBRID correlation (MUST)
- Ensure correlation events: APP_RECEIVED → APP_SUBMITTING → APP_SUBMITTED → FIRS_RESPONSE with metadata.
- Surface correlation summaries (counts, pending, SLA breaches).

5) B2C reporting (MUST)
- Add APP job + endpoint to aggregate B2C and submit within 24h; persist report artifacts and status.

6) Security controls (MUST→SHOULD)
- OAuth 2.0 for API access; keep JWT for internal hops. Enforce TLS 1.3, rate limits, service quotas.
- Certificate pinning for FIRS where applicable; key rotation procedures in docs.

7) Queue execution (SHOULD)
- Wire a worker/consumer for `firs_submissions_high` to process send/poll tasks reliably with retries and DLQ.

8) Monitoring + KPIs (MUST)
- Business KPIs: throughput, success rate, latency, SLA breaches, B2C compliance. Add Prometheus metrics/labels, and traces on critical spans.

9) Four‑corner minimal registry (MUST baseline)
- Add participant registry (buyer/supplier AP discovery) and minimal routing rules; store‑and‑forward semantics for offline APs.

10) Documentation + test harness (MUST)
- Publish SI/APP contracts and examples (shapes for input/output).
- CI checks: schema validation, signature verification, sample transform tests.

## API Contracts (Canonical)
- SI → APP (submit)
  - Payload: compliant invoice + { signature, certificate_id, version }
  - Optional: attachments metadata
- APP → FIRS (transmit)
  - Payload per FIRS MBS contract, with our request id + tenant/trace metadata
- FIRS → APP (callback/poll)
  - Response: { IRN, CSID, QR, status, message }
- APP → SI (post‑approval)
  - Update: final status + IRN/CSID/QR for downstream PDF/archival

## Validation & Ops Playbook
- Enable `ROUTER_VALIDATE_ON_STARTUP=true` for op‑to‑service checks; `ROUTER_FAIL_FAST_ON_STARTUP=true` in CI.
- Use the test routes to verify SI connections and transforms before live submissions.
- Queue health: monitor `firs_submissions_high` metrics and DLQ counts.
- Idempotency: use invoice_number/org_id as dedup keys in APP persistence.

## Acceptance Criteria (MVP)
- UBL conformity: 100% of 55 mandatory fields validated and present; signing via ECDSA with verifiable signature.
- Transmission success: >98% successful, <5s local E2E latency for enqueue, IRN/CSID/QR received within expected FIRS window.
- B2C reporting: 100% compliance within 24h.
- Observability: KPIs exposed and alerting for SLA breaches.

## Immediate Next Steps (Do Now)
- Validate SI transform with your Odoo via:
  - `POST /api/v1/si/erp/odoo/test-fetch-invoices`
  - `POST /api/v1/si/erp/odoo/test-fetch-batch`
- Confirm which fields remain to reach the “55 mandatory” set; open SI backlog to fill gaps.
- Approve schema for FIRSSubmission additions (IRN, CSID, QR) if missing.
- Decide OAuth 2.0 provider and scopes; stage rollout in non‑prod.
