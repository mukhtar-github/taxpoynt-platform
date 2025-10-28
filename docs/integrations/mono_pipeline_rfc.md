# Mono Transaction Pipeline RFC (Draft)

> Draft created Day 0 – expanded during implementation.

## Objective
Describe the end-to-end pipeline for fetching financial transactions from Mono, transforming them into the TaxPoynt canonical schema, persisting them, and surfacing observability/alerting.

## Scope
- Mono REST polling (transaction history & incremental sync).
- Transformation layer + validation rules.
- Persistence & event publishing.
- Observability, alerting, retry strategy.

## Out of Scope
- Mono Connect UI changes.
- Downstream analytics dashboards (tracked separately).
- Non-banking Mono products (identity, income).

## Open Questions
- Final retention period for raw Mono payloads (currently 30 days).
- Tenant-specific rate limits from Mono dashboard.

## Next Steps
- Fill sections per Day 1–3 implementation milestones.
- Attach final sequence diagrams, component interfaces, and sample payloads.
