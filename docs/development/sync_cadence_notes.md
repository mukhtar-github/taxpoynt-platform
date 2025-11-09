# Sync Cadence Notes

## Current State (Dev / Staging)
- Mono and Odoo integrations run strictly on-demand when the user launches the consent widget or clicks the "Test selected invoices" / "Run sandbox batch" buttons.
- No cron jobs, background workers, or interval polling trigger automatic data pulls. This keeps dev/staging lightweight and avoids accidental load on partners.

## Production Plan (Not Yet Implemented)
- Target cadence: 15-minute interval for banking feeds and ERP polling once the production go-live checklist approves automated transmission.
- Implementation outline:
  1. Introduce `BANK_SYNC_INTERVAL_MINUTES` + `ERP_SYNC_INTERVAL_MINUTES` env vars (default `0` meaning disabled).
  2. Extend the existing task runner to enqueue connector-specific jobs when the interval is >0.
  3. Surface the next scheduled pull timestamp in the onboarding summary chips so users know when background syncing is active.

## Action Items Before Enabling Background Sync
- Validate Mono + Odoo rate limits and ensure retries use exponential backoff.
- Add kill-switch env vars plus monitoring alerts for missed syncs.
- Update onboarding + dashboard copy to explain the new cadence.

Until these items ship, **do not** add timers or background jobs—keep the pulls manual.
