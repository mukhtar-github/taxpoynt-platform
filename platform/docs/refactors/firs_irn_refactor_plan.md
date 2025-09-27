# FIRS IRN & Cryptographic Stamp Alignment Plan

## Context

- FIRS is the system of record for Invoice Reference Numbers (IRN) and cryptographic stamps.
- Current platform still materialises IRNs (and surrogate stamps) locally across SI/APP flows.
- Objective: strip local synthesis, submit invoices without `irn`, persist FIRS-issued `irn`/`csid`/`qr`, and update downstream consumers.

## Inventory – Local IRN/Stamp Touchpoints

| Area | Module / Asset | Current Behaviour | Refactor Need |
| --- | --- | --- | --- |
| **SI Services** | `si_services/irn_qr_generation/irn_generator.py` | Generates IRN + verification code locally | Retire module; replace with FIRS response handling |
| | `irn_generation_service.py` | Exposes `generate_irn`, registers duplicates, caches verification code | Remove generation, keep duplicate detection on invoice hash, ingest remote IRN/CSID/QR |
| | `bulk_irn_service.py`, `bulk_processor.py` | Bulk-create IRNs for queued invoices | Convert to bulk submission (no IRN) and persist returned identifiers |
| | ERP adapters (`erp_integration_service.py`, `odoo_service.py`, `firs_si_erp_integration_service.py`, `firs_integration/comprehensive_invoice_generator.py`) | Call local generator before transmission | Submit without IRN; update to consume FIRS-issued identifiers |
| | Legacy (`irn_generation_service_legacy.py`, archived scripts) | Legacy reference to generation helpers | Mark deprecated; adjust references/tests |
| **APP Services** | `app_services/__init__.py` | Message router expects IRN in payloads | Make IRN optional pre-submit, required post-response; route FIRS data |
| | `firs_communication/request_builder.py` | Builds IRN generation requests | Remove generation flows; focus on validation only |
| | `firs_communication/response_parser.py` | Parses locally generated IRN responses | Update to parse FIRS-issued IRN/CSID/QR |
| | `transmission/transmission_service.py` | Relies on provided IRN for transmissions | Accept operations without IRN until FIRS-stage complete |
| **Hybrid / Core** | `hybrid_services/correlation_management/*` | Correlates submissions via SI-provided IRN | Delay correlation until FIRS IRN available; support interim correlation keys |
| | `core_platform/data_management/models/repositories` | Store `irn` only; no CSID/QR columns | Add fields for `csid`, `qr_payload`, `firs_stamp_metadata` |
| | Queue payloads (`queue_data/*.json`, workers) | Place IRN on enqueue | Adjust schema: optional IRN until FIRS returns |
| **Tests & Docs** | `platform/tests/**/*`, `scripts/firs_api_tester*.py` | Use local IRN generator helper | Replace with fixtures mocking FIRS responses |
| | Documentation (`docs/firs_integration/*`, `docs/compliance/*`) | Reference local generation | Update to remote-issued narrative |

## Target Behaviour

1. **Submission:** send invoice payload without `irn`; include legally required signature artefacts (SI must sign pre-clearance).
2. **Response Handling:** capture IRN, CSID, QR (and any stamp metadata) returned by FIRS sign/transmit endpoints.
3. **Persistence:** store returned values in FIRS submission storage, caches, and correlation tables.
4. **Propagation:** route returned identifiers to APP/Hybrid services, update downstream documents, notify ERP connectors.
5. **Validation:** where IRN is currently validated/constructed, switch to verifying presence/format from FIRS responses.

### End-to-End Flow (Target)

```
ERP → SI Adapter → (Pre-submission signing: XAdES/PAdES w/ stored certificate)
    → APP gateway → FIRS (validate / sign / transmit)
    → FIRS response (IRN, CSID, QR, stamp metadata)
    → APP persistence (FIRSSubmission, correlation) → SI callback
    → ERP confirmation (includes IRN/CSID/QR payload)
```

Key implications:

- SI-generated QR/verification codes become transitional only (to be removed once FIRS QR persisted).
- Duplicate detection should track invoice hash without assuming IRN availability.
- Message router contracts must allow `irn` to transition from optional (pre-submit) to required (post-response).

### Data Model Updates (preliminary)

- `firs_submission` / related ORM models: ensure columns for `irn`, `csid`, `qr_payload`, `firs_response_raw`, `signature_metadata`.
- Correlation tables (APP↔SI) should reference FIRS-issued IRN and include status timestamps.
- Queue payload schema: mark `irn` as optional on enqueue, required on completion event.

### Digital Signature Responsibilities

- Maintain SI-side certificate vault (`certificate_store`) for pre-submission document signing.
- Implement/validate XAdES for XML and PAdES for PDF before transmission; store signature audit trail alongside submission.
- Upon receiving FIRS cryptographic stamp, persist separately for buyer authentication; do **not** replace FIRS stamp with SI signature.

## Proposed Refactor Phases

### Phase 0 – Readiness✅

- Confirm DB schema supports (`irn`, `csid`, `qr`) storage; introduce migrations if fields missing.
- Snapshot current behaviour in regression tests (transmission, SI integration, hybrid correlations).

**Status:**

- Schema check (2025-XX-XX): `firs_submissions` table contains `irn` but lacks `csid`, `qr_payload`, `firs_stamp_metadata` columns → migration required.
- Recommended baseline regressions prior to flag enablement:
  - `platform/tests/integration/test_firs_connectivity.py`
  - `platform/tests/integration/firs_integration_tests.py`
  - `platform/tests/unit/test_app_firs_transmit_routing.py`
  - `platform/tests/unit/test_correlation_endpoints.py`
- Capture artefacts (logs, DB snapshots) for above suites to compare post-refactor behaviour.

### Phase 1 – Input Payload Clean-up✅

- Update SI invoice builders to omit `irn` pre-submission.
- Guard against legacy helpers injecting IRN (raise warnings / feature flags).

### Phase 2 – Response Capture✅

- Extend `FIRSHttpClient` / `FIRSAPIClient` wrappers to normalise FIRS response structure (IRN + stamp).
- Update SI submission flow (`submit_irn_to_firs`) to persist FIRS-issued identifiers.
- Wire captured values into repositories and message payloads.

Implement these fixes:✅
" 
### Phase 3 – Downstream Consumers

- Rework APP `transmission_service`, hybrid correlation callbacks, and queue processors to rely on stored FIRS identifiers.
- Remove/localise legacy IRN generators; replace tests with fixtures using mocked FIRS responses.
"

Implement these fixes:✅
"
### Phase 4 – Cleanup & Docs

- Delete deprecated generator modules (after replacements validated).
- Update documentation (`architecture`, `compliance`, `integration guides`) to describe new flow.
- Ensure MoSCoW “Digital Signature” requirements reference pre-submission signing (XAdES/PAdES) while IRN/stamp remain post-submission artefacts.
"

## Risks & Mitigations

- **Database impact:** ensure migrations deployed safely; avoid null IRN expectation in existing queries.
- **Backward compatibility:** expose feature flag / staged rollout (e.g., `FIRS_REMOTE_IRN=true`).
- **Test coverage:** augment integration tests with mocked FIRS responses returning IRN/CSID/QR.
- **Operational visibility:** add logging/metrics when FIRS identifiers ingested.

## Next Actions

1. Produce dependency matrix (code/tests) with owners + impact sizing.
2. Draft API contract for “FIRS submission result” (IRN, CSID, QR, status).
3. Prepare migration scripts / feature flag design.
4. Execute Phase 1 changes behind flag and validate end-to-end in sandbox.

## Execution Roadmap (Draft)

| Sprint | Focus | Key Deliverables | Validation |
| --- | --- | --- | --- |
| S1 | Dependency confirmation & feature flag scaffold | Dependency matrix, `FIRS_REMOTE_IRN` flag, sandbox test plan | Unit tests pass, dry-run with mocked FIRS responses |
| S2 | Phase 1 deployment (payload clean-up) | Updated SI builders, guardrails for legacy IRN helpers | Regression tests, ERP sandbox submit without IRN |
| S3 | Phase 2 rollout (response capture & persistence) | Extended FIRS client, repository changes, migration scripts | DB migration in staging, replay tests with recorded FIRS responses |
| S4 | Phase 3 downstream updates | Message router adjustments, hybrid correlation updates, queue schema revisions | End-to-end workflow in staging, buyer notification smoke test |
| S5 | Phase 4 cleanup & docs | Removal of legacy generators, documentation refresh, final sign-off | Production readiness review, monitoring dashboards updated |

## Feature Flag & Migration Scaffolding

### Feature Flag Proposal

- **Name:** `FIRS_REMOTE_IRN`
- **Location:** centralized settings (APP + SI environments). Expose via environment variable with default `false` to maintain backwards compatibility.
- **Scope:**
  - SI submission services choose between local IRN flow (current) and remote FIRS flow (new).
  - APP message-router ops treat `irn` as optional when flag enabled.
  - Tests gain ability to exercise both paths (parametrized fixtures).
- **Implementation Sketch:**
  - Add property to settings module (`settings.enable_firs_remote_irn`).
  - Wrap existing generator entry points with guard rails; log warning if legacy path triggered while flag enabled.
  - Wiring: propagate flag through dependency injection (SI services, APP registry).

### Schema Readiness Review

| Table/Model | Current Fields | Gap |
| --- | --- | --- |
| `firs_submissions` (`FIRSSubmission`) | `irn`, `firs_response`, totals | Missing `csid`, `qr_payload`, `firs_stamp_hash`, `signature_metadata` |
| `si_app_correlation` (hybrid) | `irn`, status, metadata | Need nullable IRN support + new columns for `csid`, `qr` |
| Queue payloads (`queue_data`) | Expect `irn` | Update schema to allow `irn=None` pre-response |

**Action:** design Alembic migration adding columns (`csid`, `csid_hash`, `qr_payload`, `firs_stamp_metadata`, `firs_received_at`) with appropriate indexes; stage in S3.

### Testing Safeguards

- Record baseline regression (current local IRN path) before enabling flag.
- Introduce FIRS response fixtures (IRN + CSID + QR) to support deterministic unit/integration tests under new flow.
- Plan blue/green rollout: enable flag in staging, monitor queue health, promote to production after verifying ingestion metrics.
