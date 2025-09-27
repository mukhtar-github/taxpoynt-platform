# IRN Submission & Persistence

## Overview

The IRN workflow now relies on FIRS as the single issuer of Invoice Reference Numbers (IRNs), Cryptographic Stamp Identifiers (CSIDs), and QR payloads. Rather than synthesising identifiers locally, the platform signs invoices, submits them to FIRS, and then persists the identifiers returned by the API. This guarantees regulatory alignment and prevents mismatches between SI-generated artefacts and the FIRS system of record.

## End-to-End Flow

1. **Prepare invoice payload** – map ERP data to the FIRS UBL structure and run validation.
2. **Apply digital signatures** – generate XAdES/PAdES signatures before transmitting (MoSCoW "Digital Signature" requirement).
3. **Submit to FIRS** – call `IRNGenerationService.request_irn_from_firs`, which authenticates, sends the invoice, and normalises the FIRS response.
4. **Persist identifiers** – store IRN/CSID/QR metadata in `firs_submissions`, update SI↔APP correlation records, and surface identifiers back to the ERP connector.
5. **Propagate downstream** – APP transmission and queue services always read identifiers from persistence rather than expecting them in the request payload.

## Key Components

| Component | Responsibility |
| --- | --- |
| `si_services.irn_qr_generation.irn_generation_service.IRNGenerationService` | Provides `request_irn_from_firs`, handling authentication, submission, and persistence. |
| `core_platform.data_management.repositories.firs_submission_repo_async` | Persists FIRS responses (IRN, CSID, QR payload, stamp metadata) and exposes query helpers. |
| `hybrid_services.correlation_management.si_app_correlation_service` | Synchronises SI↔APP correlation records with the stored identifiers and FIRS status. |
| `app_services.transmission.transmission_service.TransmissionService` | Resolves identifiers from storage when transmitting to buyers or re-querying status. |

## Legacy Helpers

`IRNGenerator`, `BulkProcessor`, and related utilities remain in the tree for offline analysis and historical compatibility. When `FIRS_REMOTE_IRN` is enabled (the default), these helpers raise errors to prevent accidental local IRN synthesis.

## Testing

Integration coverage lives in `platform/tests/integration/test_si_firs_submission.py`, which mocks the FIRS client, exercises `request_irn_from_firs`, and asserts that IRN/CSID/QR identifiers and correlations are persisted. Additional fast-path tests can load `firs_submissions` records directly to verify identifier propagation.

## Operational Notes

- Always enable `FIRS_REMOTE_IRN` in production environments to enforce remote issuance.
- Pre-submission signatures satisfy non-repudiation requirements; do not overwrite FIRS stamps with SI-generated equivalents.
- When replaying historical invoices, resolve identifiers from storage before attempting downstream transmission or buyer notification.
