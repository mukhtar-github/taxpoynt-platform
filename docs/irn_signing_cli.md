# IRN Signing CLI

The repository now includes a helper utility that automates the end-to-end IRN signing workflow described in the updated FIRS guidance. The CLI reads the `crypto_keys.txt` bundle, generates the canonical IRN with a UNIX timestamp, encrypts the payload with the supplied public key, and emits ready-to-share artefacts.

## Quick Start

```bash
python -m core_platform.tools.irn_signer \
  --keys ./crypto_keys.txt \
  --invoice-number INV001 \
  --service-id 94ND90NR \
  --issue-date 2024-11-05 \
  --output-dir ./irn_output \
  --qr-output ./irn_output/irn_payload.png
```

This produces:

- `public_key.pem` – decoded PEM public key  
- `certificate.der` – decoded certificate bytes  
- `payload.json` – JSON payload `{ "irn": "<IRN.timestamp>", "certificate": "<base64>" }`  
- `encrypted.bin` / `encrypted_base64.txt` – encrypted payload (binary + Base64)  
- `metadata.json` – summary metadata (IRN, timestamp, output locations)  
- Optional QR PNG when `--qr-output` is provided (requires `pip install qrcode[pil]`)

## Options

| Option | Description |
| --- | --- |
| `--keys` | Path to the downloaded `crypto_keys.txt`. |
| `--invoice-number` | Raw invoice number from the taxpayer system. |
| `--service-id` | FIRS service ID (8 characters). |
| `--issue-date` | Invoice issue date in `YYYY-MM-DD` format (defaults to today). |
| `--timestamp` | Optional UNIX timestamp. If omitted, the current time is used. |
| `--output-dir` | Directory for artefacts (`./irn_signing_output` by default). |
| `--qr-output` | Optional PNG path for the Base64 QR image (requires `qrcode` package). |
| `--quiet` | Suppress informational output. |

## Behaviour Notes

- The script uses the canonical helper to normalise invoice numbers and service IDs.  
- The encrypted payload uses RSA OAEP with SHA-256, matching the OpenSSL command sequence documented earlier.  
- Artefacts are deterministic apart from the RSA encryption randomness; `encrypted_base64.txt` is the value to embed in the QR code.

## Backend Integration

- The System Integrator invoice flow loads the same helper (`core_platform.security.irn_signing`) whenever `FIRS_CRYPTO_KEYS_PATH` is configured.  
- Generated invoices now include an `irn_signature` block with the encrypted payload, timestamped IRN, certificate reference, and signing metadata.  
- Operators can still run the CLI for parity tests or to regenerate artefacts manually; the backend no longer shells out to OpenSSL.

## Manual Workflow Reference

For teams that need the raw commands (e.g., air-gapped validation), this mirrors the automated steps:

| Action | Command |
| --- | --- |
| View bundle | `cat crypto_keys.txt` |
| Extract public key | `jq -r '.public_key' crypto_keys.txt > public_key.txt` |
| Decode public key | `openssl base64 -d -in public_key.txt -out public_key.pem` |
| Extract certificate | `jq -r '.certificate' crypto_keys.txt > certificate.txt && openssl base64 -d -in certificate.txt -out certificate.der` |
| Build payload | `jq --arg irn YOUR_IRN '{ irn: $irn, certificate: .certificate }' crypto_keys.txt > payload.json` |
| Encrypt payload | `openssl pkeyutl -encrypt -inkey public_key.pem -pubin -in payload.json -out encrypted.bin` |
| Base64 encode | `base64 -i encrypted.bin -o encrypted_base64.txt` |
| Generate QR (optional) | `qrencode -o qr_code.png -t PNG < encrypted_base64.txt` |

## Testing

Unit tests live in `platform/tests/unit/test_irn_signer.py`. They cover bundle parsing, IRN generation, and encryption/decryption using in-memory RSA keys.
