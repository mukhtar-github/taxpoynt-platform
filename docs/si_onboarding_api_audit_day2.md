# SI Onboarding – Day 2 Data & API Contract Audit

This audit builds on the UX direction captured in `docs/si_onboarding_ux_day1.md` and the current implementation review (see Touchpoint Review and Backend/Data Notes). It catalogues the existing onboarding payloads, verifies how the backend service can support a consolidated contract, and proposes version-aware adjustments plus test coverage.

---

## 1. Frontend Payload Inventory

Source references: `platform/frontend/shared_components/services/onboardingApi.ts`, `platform/frontend/si_interface/workflows/erp_onboarding.tsx`.

| Endpoint | Method | Primary Consumer | Request Payload | Response Shape (observed) | Notes |
|----------|--------|------------------|-----------------|---------------------------|-------|
| `/si/onboarding/state` | `GET` | `onboardingApi.getOnboardingState()` | – | `{ user_id, current_step, completed_steps, has_started, is_complete, last_active_date, metadata, created_at, updated_at }` | Front-end falls back to local storage when request fails; metadata blob includes `expected_steps`, `step_definitions`, and ERP snapshots. |
| `/si/onboarding/state` | `PUT` | `onboardingApi.updateOnboardingState()` | `{ current_step, completed_steps?, metadata? }` | Same shape as GET response | Wizard autosave posts on every major interaction, resulting in large `metadata` payloads (organization profile, ERP configuration, compliance toggles). |
| `/si/onboarding/state/step/{step}` | `POST` | `onboardingApi.completeOnboardingStep()` | `{ metadata? }` | Mirrors state response | Used sparingly in UI; metadata records per-step completion timestamps. |
| `/si/onboarding/complete` | `POST` | `onboardingApi.completeOnboarding()` | `{ metadata? }` | State response with `is_complete` true | Triggers dashboard redirect. |
| `/si/onboarding/state/reset` | `DELETE` | `onboardingApi.resetOnboardingState()` | – | `{ message }` (ignored) | Utility in QA / admin flows. |
| `/si/onboarding/analytics` | `GET` | `onboardingApi.getOnboardingAnalytics()` | – | `{ user_id, status, analytics { ... }, timeline { ... } }` | Dashboard widgets consume completion percentage, stale detection, and next-step guidance. |

### Metadata Content (frontend expectations)
- `metadata.service_package`: matches role (`"si"` default).
- `metadata.expected_steps`: array the UI uses for progress bars.
- `metadata.step_definitions`: dictionary with `title`, `description`, `success_criteria`.
- `metadata.erp_onboarding`: snapshot of organization profile, ERP configuration, compliance notes.
- `metadata.completion`: optional block with `completed_at` timestamp.

---

## 2. Backend Alignment (SIOnboardingService)

Relevant file: `platform/backend/si_services/onboarding_management/onboarding_service.py`.

- Canonical phases are already defined: `service-selection`, `company-profile`, `system-connectivity`, `review`, `launch`.
- Package flows (`PACKAGE_FLOWS`) map service packages to ordered arrays of canonical steps.
- `STEP_DEFINITIONS` includes titles/descriptions aligned with the Day 1 UX plan.
- Metadata normalization occurs via `_ensure_metadata_consistency`, allowing us to reorganize payloads without losing historical keys.
- The service persists everything through `OnboardingStateRepositoryAsync`, meaning a consolidated contract can remain a single table/database row.
- The router (`platform/backend/api_gateway/api_versions/v1/si_endpoints/onboarding_endpoints.py`) already forwards `service_package` and `api_version` metadata, so we can add an opt-in contract flag without breaking routing.

**Conclusion:** We can consolidate “company” and “compliance” fields within a single wizard payload while maintaining canonical steps. Legacy step IDs (`organization_setup`, etc.) surface only in UI, so backend can accept both sets via normalization.

---

## 3. Proposed Contract Adjustments

### 3.1 Consolidated Payload (wizard)
Introduce the following optional blocks inside `metadata` while keeping existing keys:

```json
{
  "current_step": "system-connectivity",
  "completed_steps": ["service-selection", "company-profile"],
  "metadata": {
    "service_package": "si",
    "expected_steps": ["service-selection", "company-profile", "system-connectivity", "review", "launch"],
    "step_definitions": { "...": { "title": "...", "description": "...", "success_criteria": "..." } },
    "wizard": {
      "company_profile": {
        "company_name": "Example Ltd",
        "rc_number": "RC123456",
        "tin": "01234567-0001"
      },
      "service_focus": {
        "selected_package": "si",
        "integration_targets": ["odoo", "sap"]
      },
      "system_connectivity": {
        "connections": [
          { "id": "conn-001", "type": "odoo", "status": "pending" }
        ],
        "mapping_progress": { "customers": true, "products": false }
      }
    }
  }
}
```

### 3.2 Legacy Compatibility
Maintain support for requests using legacy step IDs and metadata keys:
- Accept `organization_setup`, `compliance_verification`, etc., and map to canonical IDs in service layer.
- Preserve `metadata.erp_onboarding` but treat it as read-only; populate new `metadata.wizard` for consolidated UI.
- Continue returning `completed_steps` array even when canonical phases collapse multiple legacy steps.

### 3.3 Analytics Extension
Augment analytics payload with optional `phase_breakdown`:

```json
"analytics": {
  "completion_percentage": 60.0,
  "phase_breakdown": [
    { "phase": "service-selection", "status": "complete" },
    { "phase": "company-profile", "status": "complete" },
    { "phase": "system-connectivity", "status": "in_progress" },
    { "phase": "review", "status": "pending" },
    { "phase": "launch", "status": "pending" }
  ],
  "expected_completion": { "next_steps": ["review"], "estimated_remaining_time": "2 steps remaining" }
}
```

---

## 4. Versioning & Gateway Strategy

- **Contract negotiation:** introduce optional request header `X-Onboarding-Contract: consolidated-v1`. Absence of header keeps legacy behaviour; presence enables canonical mapping and `metadata.wizard`.
- **API gateway compliance:** The router already sets `context.metadata["api_version"] = "v1"`. We can add a dependency that inspects the header and appends `context.metadata["contract_version"]`.
- **Roll-out sequence:**
  1. Deploy service updates accepting both legacy and canonical payloads.
  2. Update contract tests (see section 5) to cover both variants.
  3. Release frontend toggled via env flag or header to target consolidated mode.
  4. Monitor analytics to ensure `phase_breakdown` consumption is stable.
- **Deprecation plan:** After adoption, surface warnings (e.g., response meta -> `"meta": {"warning": "legacy contract deprecated Q4"}`) when header missing.

---

## 5. Test Coverage Additions

Implemented in `platform/tests/unit/test_onboarding_endpoints_contracts.py`:

1. **Canonical Phase Payload (AAA)**  
   - Arrange message router response containing consolidated metadata (`metadata.wizard`).  
   - Act perform `GET /api/v1/si/onboarding/state`.  
   - Assert response exposes canonical `current_step`, expected steps, and wizard block untouched.

2. **Legacy Step Guard**  
   - Arrange router response using legacy IDs (`organization_setup`).  
   - Act same GET request.  
   - Assert legacy fields pass through, ensuring backward compatibility.

3. **Update State – Consolidated Request**  
   - Arrange stubbed success payload.  
   - Act `PUT /api/v1/si/onboarding/state` with canonical `current_step` and consolidated metadata.  
   - Assert router receives payload unchanged (verifies gateway path).

4. **Update State – Legacy Request**  
   - Arrange stubbed success payload.  
   - Act `PUT` with legacy step names.  
   - Assert router still receives legacy identifiers, guarding support for existing clients.

These tests leverage the existing stubs and maintain isolation, satisfying the `Guide_to_Writing_Robust_Tests.md` AAA structure and preparing the codebase for the phased rollout.

---

## 6. Next Actions

- Socialize this audit with backend/API stakeholders for contract approval.  
- Implement header detection + payload normalization in the service layer.  
- Use analytics `phase_breakdown` to power the checklist visual described in Day 1 UX documentation.

_Prepared for Day 2 goals: data audit, contract planning, and test scaffolding._ 

---

## 7. Day 7 Validation Summary

- End-to-end pytest scenario (`platform/tests/integration/test_onboarding_regression.py::test_onboarding_flow_covers_signup_wizard_and_checklist`) exercises the full sign-up → verification → checklist flow using the production routers and records telemetry emission of `si_onboarding.email_verified` and `si_onboarding.terms_confirmed`.
- Legacy nine-step identifiers are now guarded by `test_legacy_nine_step_names_redirect_to_canonical_flow`, which asserts that any `organization_setup`/`compliance_verification` payloads are canonicalised to the new wizard steps before persistence.
- Telemetry hooks were reviewed: analytics events are routed through the message router, and the tests capture the emitted batches to ensure they align with the analytics plan.
- Coverage captured locally via `pytest -q platform/tests/integration/test_onboarding_regression.py`.

---

## 8. Day 8 Launch-Readiness Buffer

- Synthetic observability request (`platform/tests/integration/test_observability_synthetic.py`) confirmed Prometheus counters (`taxpoynt_http_requests_total`, `taxpoynt_http_request_duration_seconds`) and FIRS latency hooks populate as expected.
- Dashboard review: Prometheus & OpenTelemetry dashboards display updated spans with `taxpoynt.service_role` and `taxpoynt.business_operation` attributes observed during synthetic run.
- Rollback & monitoring windows recorded in `docs/launch_plan_day8.md`; release artefacts noted in `docs/release_notes_day8.md`.
