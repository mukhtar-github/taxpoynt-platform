# IRN Generation

The latest guidance from FIRS requires **System Integrators (SIs)** to generate the Invoice Reference Number (IRN) locally before transmitting an invoice for clearance. FIRS still validates and stamps the invoice, but the canonical IRN value is now computed by the SI using three inputs supplied by the taxpayer and FIRS credentials.

## Required Inputs

| Field | Source | Format | Notes |
| --- | --- | --- | --- |
| Invoice Number | Taxpayer invoicing/ERP system | Alphanumeric (no special characters) | Example: `INV001`, `INVOICE123` |
| Service ID | Assigned by FIRS during enablement | Alphanumeric, 8 characters | Example: `94ND90NR` |
| Datestamp | Invoice issue date | `YYYYMMDD` | Example: `20240611` |

The IRN is the concatenation of these components:

```
{InvoiceNumber}-{ServiceID}-{YYYYMMDD}
```

Example:

```
INV001-94ND90NR-20240611
```

## Platform Responsibilities

* Validate inputs against format constraints (no special characters, 8 character service IDs, valid dates).
* Generate the IRN deterministically using the taxpayer-provided values.
* Persist the generated IRN alongside any verification codes or hashes required for downstream QR/key signing.
* Forward the generated IRN to FIRS during clearance. FIRS remains the source of truth for validation responses and cryptographic stamps, but **does not** assign a new IRN.

## Implications for Integrations

* The legacy `FIRS_REMOTE_IRN` feature flag is deprecated. All environments – including production – generate IRNs locally using the rules above.
* Any previous logic that bypassed local IRN generation (waiting for FIRS to assign the IRN) must be removed or migrated to the new flow.
* Downstream services (QR signing, invoice validation, ERP connectors) should expect IRNs with the `{InvoiceNumber}-{ServiceID}-{YYYYMMDD}` pattern and avoid attempting to recompute or alter the value.
