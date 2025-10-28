# Business Email Enforcement

The registration flow now blocks sign-ups that use consumer/free email domains by default. This keeps the SI onboarding workspace focused on verified business contacts while still allowing controlled overrides.

## Default Policy

- **Mode:** `strict` (deny common consumer domains unless explicitly allowlisted).
- **Source list:** `platform/shared_config/free_email_domains.json`.
- **Frontend hint:** The signup form surfaces a “use your business email” error before the request is submitted.

## Backend Configuration

| Variable | Purpose | Notes |
|----------|---------|-------|
| `BUSINESS_EMAIL_POLICY_MODE` | `strict` (default), `disabled`, or `allowlist_only`. | `strict` blocks known free domains; `disabled` turns validation off; `allowlist_only` accepts **only** domains listed in the allowlist. |
| `BUSINESS_EMAIL_DENYLIST` | Comma/whitespace separated domains to block. | Appended to the default denylist. Supports wildcard entries such as `*.example`. |
| `BUSINESS_EMAIL_DENYLIST_PATH` | Optional path to a newline-separated or JSON domain list. | Useful for loading a file produced by an automated feed. |
| `BUSINESS_EMAIL_ALLOWLIST` | Comma/whitespace separated domains to always allow. | Overrides the denylist (e.g., trusted partners). |
| `BUSINESS_EMAIL_ALLOWLIST_PATH` | Optional file path for allowlisted domains. | Same format as the denylist path. |

## Frontend Configuration

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_BUSINESS_EMAIL_POLICY_MODE` | Mirrors backend mode to keep messaging aligned. |
| `NEXT_PUBLIC_BUSINESS_EMAIL_DENYLIST` | Extra domains to block client-side. |
| `NEXT_PUBLIC_BUSINESS_EMAIL_ALLOWLIST` | Domains exempt from blocking on the client. |

> The frontend never enforces a stricter policy than the backend—it only provides immediate feedback. Always configure the backend variables as the source of truth.

## Operational Recommendations

1. **Keep the denylist fresh:** feed `BUSINESS_EMAIL_DENYLIST_PATH` from the same job that manages disposable-domain intelligence.
2. **Controlled bypass:** grant temporary access by adding domains to the allowlist and reviewing them weekly.
3. **Monitoring:** add registration metrics segmented by domain pattern to confirm legitimate leads are unaffected.
