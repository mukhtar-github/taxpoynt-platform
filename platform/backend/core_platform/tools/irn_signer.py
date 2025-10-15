#!/usr/bin/env python3
"""
Utility CLI for producing FIRS-compliant IRN signing payloads.

Workflow:
    1. Read the downloaded `crypto_keys.txt` bundle (contains `public_key` and `certificate` fields).
    2. Generate a canonical IRN from invoice details and append a UNIX timestamp.
    3. Encrypt the payload `{ "irn": "<IRN.timestamp>", "certificate": "<certificate>" }`
       with the supplied public key (RSA-OAEP SHA256).
    4. Emit artefacts (PEM files, encrypted blob, JSON summary) and optionally a QR code
       representing the base64-encoded ciphertext.

Example:
    python -m core_platform.tools.irn_signer \\
        --keys crypto_keys.txt \\
        --invoice-number INV001 \\
        --service-id 94ND90NR \\
        --issue-date 2024-11-05 \\
        --output-dir ./irn_output
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Sequence

# Ensure we can import the canonical IRN helper without relying on PYTHONPATH setup.
REPO_ROOT = Path(__file__).resolve().parents[3]
BACKEND_ROOT = REPO_ROOT / "platform" / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

from core_platform.security.irn_signing import (  # noqa: E402
    SignedIRNResult,
    generate_signed_irn,
    load_crypto_bundle,
)


def save_outputs(
    output_dir: Path,
    result: SignedIRNResult,
    qr_output: Optional[Path],
) -> None:
    """Write artefacts to disk."""
    output_dir.mkdir(parents=True, exist_ok=True)

    (output_dir / "crypto_bundle.json").write_text(json.dumps(result.bundle.as_dict(), indent=2), encoding="utf-8")
    (output_dir / "public_key.pem").write_bytes(result.public_key_pem)
    (output_dir / "certificate.der").write_bytes(result.certificate_bytes)
    (output_dir / "payload.json").write_bytes(result.payload_bytes)
    (output_dir / "encrypted.bin").write_bytes(result.encrypted_bytes)
    (output_dir / "encrypted_base64.txt").write_text(result.encrypted_base64, encoding="utf-8")

    metadata = dict(result.metadata)
    metadata["qr_output"] = str(qr_output) if qr_output else None
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    if qr_output and result.qr_png_bytes is not None:
        qr_output.parent.mkdir(parents=True, exist_ok=True)
        qr_output.write_bytes(result.qr_png_bytes)
        return


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate encrypted IRN signing payloads.")
    parser.add_argument("--keys", required=True, type=Path, help="Path to crypto_keys.txt bundle.")
    parser.add_argument("--invoice-number", required=True, help="Invoice number from the accounting system.")
    parser.add_argument("--service-id", required=True, help="FIRS Service ID assigned to the taxpayer.")
    parser.add_argument(
        "--issue-date",
        required=False,
        default=datetime.utcnow().strftime("%Y-%m-%d"),
        help="Invoice issue date (YYYY-MM-DD). Defaults to today.",
    )
    parser.add_argument(
        "--timestamp",
        type=int,
        help="Optional UNIX timestamp to append to the IRN. Defaults to the current time.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./irn_signing_output"),
        help="Directory to write artefacts (default: ./irn_signing_output).",
    )
    parser.add_argument(
        "--qr-output",
        type=Path,
        help="Optional path to write a QR PNG of the encrypted payload.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Hide informational output (errors will still be raised).",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = parse_args(argv)

    bundle = load_crypto_bundle(args.keys)
    result = generate_signed_irn(
        bundle=bundle,
        invoice_number=args.invoice_number,
        service_id=args.service_id,
        issued_on=args.issue_date,
        timestamp=args.timestamp,
        include_qr=bool(args.qr_output),
    )

    save_outputs(args.output_dir, result, args.qr_output)

    if not args.quiet:
        print("IRN signing artefacts generated:")
        print(f"  IRN with timestamp : {result.irn_with_timestamp}")
        print(f"  Payload path       : {args.output_dir / 'payload.json'}")
        print(f"  Encrypted (base64) : {args.output_dir / 'encrypted_base64.txt'}")
        if args.qr_output:
            print(f"  QR code PNG        : {args.qr_output}")

    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
