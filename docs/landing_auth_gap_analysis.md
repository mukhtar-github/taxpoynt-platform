# Landing, Auth & Onboarding Gap Analysis

## Snapshot
- Landing page emphasises enterprise storytelling but overwhelms first-time users. Calls-to-action send visitors straight to detailed signup without preview of benefits for each service role.
- Authentication flow relies on a long, multi-card signup form and role redirects handled fully on the client. OAuth consent copy is generic and does not explain scopes.
- Onboarding pathways diverge immediately after signup (`/onboarding/si/*`, `/onboarding/app/*`, etc.), causing repeated styling and inconsistent milestones.

## Landing Page Gaps
- **Messaging Load**: Hero section combines multiple badges, gradients, and long paragraphs. Users have no concise “What happens next?” summary.
- **Navigation Density**: Top nav duplicates actions (“Sign In”, “Get Started”) without indicating role relevance.
- **Conversion Path**: Pricing and service modules lack quick comparison for SI vs APP vs Hybrid. The “Get Started” button always assumes subscription checkout rather than a guided questionnaire.

### Recommendations
- Introduce a simplified hero: one line value prop + single CTA leading to the unified onboarding wizard.
- Add a service comparison panel (three columns) with “Start as SI/APP/Hybrid” buttons tied to query params for the wizard.
- Reduce gradient overlays and leverage neutral backgrounds to increase readability.

## Authentication Gaps
- **Form Complexity**: `business_interface/auth/SignUpPage.tsx` mixes role selection, password rules, and marketing copy. Users must scroll to reach the actual registration button.
- **OAuth Messaging**: Backend OAuth 2.0 endpoints surface generic consent text (“TaxPoynt API Access”). Scopes for workspace management and invoice submission are not clearly described.
- **Session Handoff**: Post-login routing depends on `authService.login` returning a role; there is no server-driven `next_path`, which complicates MFA or external IdP expansion.

### Recommendations
- Replace the current signup page with the unified wizard’s first step (service choice + email capture), then defer password creation to a focused screen.
- Update OAuth consent strings to highlight: “Read organisation profile”, “Submit invoices to FIRS”, etc.
- Add a backend-provided `redirect_url` in auth responses so the frontend can simply follow the suggested path.

## Unified Visual Direction
- **Color Palette**: Use base neutrals (`#F3F4F6`, `#111827`) with a single accent (`#2563EB`) per screen. Reserve gradients for highlight cards only.
- **Typography**: Keep headings at `text-3xl` maximum in onboarding, ensure supporting text stays `text-sm`–`text-base` for readability.
- **Components**: Reuse `TaxPoyntButton` primary/outline pairings; avoid custom inline button styles.
- **Icons & Illustrations**: Swap emoji blocks for lightweight iconography or concise bullet lists to reduce visual noise.

## Implementation Priorities
1. Ship the unified onboarding wizard to centralise service selection, organisation data capture, and configuration milestones.
2. Refactor landing page CTAs to funnel directly into the wizard (`/onboarding?service=si|app|hybrid`).
3. Align auth copy and OAuth consent screens with the simplified journey; document the new style choices in the design system notes.

