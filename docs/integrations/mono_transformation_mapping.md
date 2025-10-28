# Mono → Canonical Transaction Mapping (Day 1)

| Mono Field | Canonical Field | Notes |
|------------|-----------------|-------|
| `id` | `BankTransaction.id` | Primary idempotency key (string). |
| `account.id` | `provider_account_id` | Stored alongside `account_number` for traceability. |
| `account.account_number` | `account_number` | Normalised to remove whitespace. |
| `amount` | `amount` | Absolute decimal value; `transaction_type` derived from sign. |
| `currency` | `currency` | Uppercased ISO 4217. |
| `type` (`credit`/`debit`) | `transaction_type` | Combined with `amount` validator. |
| `status` | `status` | `pending`/`completed`/`reversed` supported. |
| `balance` | `ledger_info.ledger_balance` | Optional ledger snapshot. |
| `narration` | `narration` | Long-form description preserved. |
| `description` | `description` | Short description; defaults to narration when missing. |
| `meta.counterparty.name` | `counterparty.name` | Counterparty details nested under `Counterparty`. |
| `meta.counterparty.account_number` | `counterparty.account_number` | |
| `meta.tags` | `tags` | Lowercased and deduplicated. |
| `date` | `transaction_date` | Parsed as aware UTC datetime. |
| `value_date` | `value_date` | Optional, falls back to `transaction_date`. |
| `meta.is_reversal` | `is_reversal` | Falls back to Mono `status == "reversed"`. |
| `meta.original_transaction_id` | `original_transaction_id` | Stored when Mono supplies reversal reference. |

## Edge Cases

- **Reversals**: when Mono surfaces `meta.is_reversal` or `status == "reversed"`, mark `is_reversal=True` and retain `original_transaction_id` for linkage.
- **Split Transactions**: aggregated transactions (e.g., multiple POS legs) carry `meta.split_group_id`; downstream reconciliation uses metadata to collapse/expand without altering the canonical schema.
- **Zero-Amount Holds**: Mono occasionally emits pending holds with `amount = 0`. These are only accepted when `meta.is_hold = true` to avoid polluting workflows.
- **Currency Overrides**: if Mono omits currency, default to account currency captured during account discovery.

## Validation Rules

1. `amount` must be non-negative `Decimal`; sign set via `transaction_type`.
2. `currency` must be a 3-letter alphabetic code (uppercase enforced).
3. `status` constrained to `completed|pending|reversed`.
4. `tags` normalised to lowercase, non-empty strings.
5. Zero-amount transactions require `metadata.is_hold = true`.
6. Duplicate detection uses composite `(id, provider_account_id, transaction_date)` until canonical persistence is finalised.

## Operation Naming

- Fetch: `mono.fetch_transactions`
- Transform: `mono.transform_transaction`

These identifiers appear in message router metadata and observability logs.
