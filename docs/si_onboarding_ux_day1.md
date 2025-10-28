# SI Onboarding UX Redesign – Day 1 Deliverables

Context target: **System Integrator onboarding** refresh aligned with the progressive three-phase journey. This document captures the UX artifacts required for Day 1: storyboard, information architecture, low-fidelity wireframes with copy/states, and the testing hooks that will guide engineering validation.

---

## 1. Progressive Storyboard (Three Phases)

| Phase | Screen / Touchpoint | User Goal | Key Actions & Feedback | Telemetry Hooks |
|-------|---------------------|-----------|------------------------|-----------------|
| Entry & Account Creation | Marketing landing → Auth (SSO or email) | Understand value and create an account quickly | Primary CTA “Get Started”; sign-in / sign-up tabs; minimal fields (name, work email, password, optional role) | `onboarding.entry.cta_clicked`, `auth.signup.success`, `auth.signup.abandon` |
| Guided Company Setup | In-product wizard (Step 1: Company Profile → Step 2: Service Focus → Step 3: Connect Systems) | Provide essentials without friction and reach first aha moment | Step indicator + percent; autosave banner; contextual help; skip options for advanced setup | `wizard.step_viewed`, `wizard.step_saved`, `wizard.skip_used` |
| Activation & Checklist | SI Dashboard landing with “Complete Your Setup” sidebar | See progress, finish remaining tasks, access value-driving features | Checklist grouped by canonical phases; inline completion toasts; tooltip tour; callout for first invoice | `checklist.phase_completed`, `tooltip.opened`, `invoice.first_submitted` |

---

## 2. Updated Information Architecture (IA)

```
SI Onboarding
└── Entry Gateway (public)
    ├── Landing CTA (GET /si/onboarding/start)
    └── Auth Modal / Page
        ├── Sign In
        └── Create Account
└── Authenticated Wizard (app shell)
    ├── Wizard Container (/si/onboarding/wizard)
    │   ├── Step 1 – Company Profile
    │   ├── Step 2 – Service Focus
    │   └── Step 3 – System Connectivity
    └── Support Views
        ├── Save Confirmation Toast
        ├── Skip & Resume Dialog
        └── Help Drawer (FAQs / Support)
└── Dashboard Experience
    ├── Overview Screen (/si/dashboard)
    │   ├── Setup Checklist Sidebar
    │   ├── Hero Metric Tiles (Connected Systems, Compliance Status)
    │   └── Recent Activity Feed
    └── Guidance Layer
        ├── Contextual Tooltips
        └── “Need Assistance?” quick action
```

---

## 3. Low-Fidelity Wireframes & Interaction States

### 3.1 Wizard Frame (applies to all three steps)

```
┌───────────────────────────────────────────────┐
│  TaxPoynt SI Onboarding                      x│
│  Step 1 of 3 · Company Profile   33% ███░░░░  │
├───────────────────────────────────────────────┤
│  Heading: “Let’s confirm your company info”   │
│  Subcopy: “We’ll reuse this for compliance     │
│  and invoicing. You can edit later.”          │
│                                               │
│  [Form Stack]                                 │
│   - Company Name           [_____________]    │
│   - CAC / RC Number        [_____________]    │
│   - Tax Identification No. [_____________]    │
│   - Business Email         [_____________]    │
│   - Industry               [Select v]         │
│                                               │
│  Inline Help: “Why we ask for this” (tooltip) │
│  Autosave Chip: “Saved · 2s ago”              │
│                                               │
│  Primary: Continue →                          │
│  Secondary: Save & Exit                       │
│  Tertiary: Skip for Now                       │
└───────────────────────────────────────────────┘
States:
- Loading: skeleton form fields, disabled actions.
- Save success: autosave chip updates, toast “Details saved”.
- Validation error: inline field message, summary banner.
- Skip: confirmation modal with reminder copy.
```

### 3.2 Dashboard Checklist Sidebar

```
┌─────────────────────────────┐
│ Complete Your Setup (60%)   │
│ ─────────────────────────   │
│ ● Phase 1 · Service Selection│
│   ✓ Confirmed                │
│ ● Phase 2 · Company Profile │
│   ▸ “Add compliance contact” │
│ ● Phase 3 · System Connect   │
│   ○ “Link ERP credentials”   │
│ ● Phase 4 · Review           │
│   ○ “Verify launch checklist”│
│ ● Phase 5 · Launch           │
│   ○ “Invite your finance team”│
│                             │
│ Need assistance? Chat now → │
└─────────────────────────────┘
States:
- Collapsed (icon-only) for smaller viewports.
- Completed phase shows green check and timestamp tooltip.
- Hover displays quick action button “Open task”.
```

### 3.3 Contextual Tooltip Pattern

```
Trigger: Info icon next to sensitive field (e.g., FIRS API key).
Tooltip Content:
  Title: “Why we need your FIRS API key”
  Body: “We use this to validate invoices before submission. Stored securely and never shared.”
  CTA: “Learn more” → compliance docs.
States:
- Keyboard focusable (tab / shift-tab).
- Dismissible via ESC or click-away.
```

Validated Copy Deck (key highlights):
- CTA labels: “Continue”, “Save & Exit”, “Skip for now (I’ll finish later)”.
- Empty states: “No ERP connections yet — let’s link your first system.”
- Error messaging: “We couldn’t reach the ERP service. Recheck the host URL or retry in a minute.”
- Success toast: “Company profile saved. Next up: choose your service focus.”

---

## 4. UX Spec Review Checklist

- **User Goal Alignment:** Each screen contains a clear primary heading and CTA that maps to a specific onboarding milestone.
- **Progress Feedback:** Step indicator and checklist percentages update after every successful save.
- **Accessibility:** Keyboard traversal covers form fields, buttons, skip, and tooltips; ARIA labels are defined for progress and checklist items.
- **Copy Consistency:** Terminology matches backend canonical phases (“service selection”, “system connectivity”, “launch”).
- **State Coverage:** Designs include loading, success, error, and skip states; every error provides actionable guidance.
- **Persistence Signals:** Autosave chip or toast is present wherever data writes occur.
- **Support Path:** Help drawer/chat CTA is visible from wizard and dashboard.

Use this checklist during design reviews and again before handoff to engineering.

---

## 5. Interaction Scenarios → Future Frontend Tests

1. **Happy Path Completion**  
   Arrange new SI user with no onboarding state.  
   Act complete steps 1–3 sequentially.  
   Assert progress reaches 100%, checklist marks all phases, user lands on dashboard.

2. **Skip & Resume**  
   Arrange state saved after Step 1.  
   Act trigger “Skip for now” at Step 2, later reopen wizard from dashboard.  
   Assert wizard resumes at Step 2 with saved data intact.

3. **Autosave Failure Recovery**  
   Arrange backend returns 503 on update.  
   Act user edits field and pauses.  
   Assert inline banner shows retry guidance, autosave chip indicates failure state, Retry button works.

4. **Checklist Reordering Guard**  
   Arrange backend analytics returns phases out of order.  
   Act render dashboard checklist.  
   Assert UI enforces canonical order and highlights data inconsistency via neutral tooltip.

5. **Tooltip Accessibility**  
   Arrange focus on info icon via keyboard.  
   Act press Enter to open, ESC to close.  
   Assert focus stays on trigger, tooltip is removed from DOM after dismiss.

6. **Fallback Analytics Handling**  
   Arrange service router unavailable → fallback payload.  
   Act load dashboard.  
   Assert UI displays fallback badge and prompts user to retry without blocking wizard access.

These scenarios will inform component tests (React Testing Library), integration tests with mocked APIs, and contract tests for checklist data once implementation begins.

---

_Prepared for Day 1 deliverables. Subsequent work will iterate on fidelity, asset design, and engineering integration._

---

### Day 7 UX Note – Final Copy & Checklist Surfacing

- Finalise the verification step copy as: **“Verify email and continue”** with supporting checklist chip (“Saved at HH:MM”) so messaging matches the automated regression flow.
- Checklist summary highlights the **“Verify account”** item as complete once the analytics hook reports `si_onboarding.email_verified`; the widget text now reads: _“Verify account — Email confirmed and terms accepted.”_
- Release note call-out: include “Guided onboarding copy polished for verification & checklist handoff” in the Day 7 change log.
