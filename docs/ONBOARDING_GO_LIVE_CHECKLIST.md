# Onboarding Go-Live Checklist

This checklist captures every runtime toggle that must be set before enabling the streamlined onboarding flow in production. Apply these values to the deployment environment (Railway for the backend, Vercel for the frontend) rather than committing them to git.

## 1. Global Runtime Baseline
- `ENVIRONMENT=production`
- `DEMO_MODE=false`
- `ROUTER_VALIDATE_ON_STARTUP=true` and `ROUTER_FAIL_FAST_ON_STARTUP=true` (recommended for CI/CD)

## 2. Backend Environment Variables
- `DOJAH_API_KEY=<live Dojah API token>`
- `DOJAH_APP_ID=<live Dojah app id>`
- `DOJAH_BASE_URL=https://api.dojah.io` (override only if Dojah supplies a new host)
- `DOJAH_COMPANY_LOOKUP_PATH=/api/v1/kyc/company`
- `DOJAH_LOOKUP_METHOD=GET`
- `DOJAH_TIMEOUT_SECONDS=10`
- `DOJAH_FALLBACK_COUNTRY=Nigeria`
- **Do not set** `DOJAH_STUB_PATH` in production (leave it completely unset)
- `EMAIL_VERIFICATION_MODE=strict`
- `EMAIL_VERIFICATION_BYPASS=false`
- `ALLOW_DEV_EMAIL_FALLBACK=false`
- `SMTP_HOST=smtp.gmail.com`
- `SMTP_PORT=587`
- `SMTP_USERNAME=noreply@taxpoynt.com`
- `SMTP_PASSWORD=<gmail app password>`
- `SMTP_TLS=true`
- `EMAILS_FROM_EMAIL=noreply@taxpoynt.com`
- `EMAILS_FROM_NAME=TaxPoynt Platform`
- `SENDGRID_API_KEY=<sendgrid api key>` (enables API-based delivery; falls back to SMTP if unset)

## 3. Frontend Environment Variables
- `NEXT_PUBLIC_API_URL=https://<railway-backend-domain>/api/v1`
- `NEXT_PUBLIC_EMAIL_VERIFICATION_MODE=strict`
- `NEXT_PUBLIC_EMAIL_VERIFICATION_BYPASS=false`
- Remove any leftover `NEXT_PUBLIC_DOJAH_*` keys unless a UI component explicitly consumes them.

## 4. Deployment / Validation Steps
1. **Rebuild & redeploy** backend + frontend after saving the variables above.
2. **Health checks**
   - `GET /health` on the backend
   - `npm run lint && npm run build` inside `platform/frontend`
3. **Manual onboarding test**
   - Register a new SI user via `/auth/signup`.
   - Confirm verification email is delivered from `noreply@taxpoynt.com`.
   - Enter the received OTP on `/auth/verify-email` (strict mode should require the real code).
   - After verification, ensure the wizard reaches the service selection screen and the onboarding state updates once every step.
4. **Dojah enrichment check**
   - Complete the company profile (TIN/RC) and watch backend logs for `SubmitKYCCommand` messages.
   - Confirm metadata in Redis/PostgreSQL includes the normalized company profile (no stub warning should appear).
5. **Telemetry & rate limits**
   - Inspect monitoring dashboards to ensure no new 429/500 spikes.
   - If using `ROUTER_STRICT_OPS`, ensure onboarding operations are registered.

Document any deviations (e.g., temporary relaxed email verification) directly in Railway/Vercel notes so they can be reverted after testing.
