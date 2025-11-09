# Onboarding Accessibility & Responsive Notes

Date: 2025-02-14

## Screen Reader & Keyboard
- Verified that every input introduced in the Mono/Odoo lanes has an associated `<label>`. The Mono status chips and error banners use plain text so they are announced automatically.
- Mono/Odoo cards are toggled with `<button>` elements, making them reachable via keyboard and exposing their expanded state through focus. When you add new cards, keep using `button` semantics instead of raw `divs`.
- Inline status updates (Mono/Odoo summaries) are repeated as simple text nodes; if we later surface live updates, prefer `aria-live="polite"` spans.

## Responsive Layout
- Tested at 320px, 768px, and 1280px using Chrome dev tools. Both cards collapse to single-column stacks on mobile and keep their controls visible without horizontal scroll.
- Inputs for Mono (name/email/callback) and Odoo (URL/database/etc.) wrap to two columns for ≥768px and single column below.
- Preview JSON for Odoo invoices is capped at 64vh with overflow scroll to avoid pushing the CTA off-screen.

## Color Contrast
- Status chips reuse Tailwind palette tokens that meet WCAG AA (e.g., `bg-green-100 text-green-700`). If you introduce new chip colors, run them through a contrast checker.

## Testing Recommendations
- Run `npm run lint -- --file shared_components/onboarding/UnifiedOnboardingWizard.tsx` after touching the wizard.
- Manual smoke path: open `/onboarding`, tab through the Mono form, ensure focus order is predictable, then resize the viewport to confirm the cards reflow correctly.
