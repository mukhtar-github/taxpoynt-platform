"""
QR Signing Service
==================

Provides helper routines for:
- Loading cryptographic keys from the FIRS `crypto_keys.txt` bundle.
- Encrypting QR payloads with the public key.
- Generating QR data/strings using the existing QRCodeGenerator.

The module exposes both a reusable service class for application code and a
small CLI utility (see bottom of file) for local testing.
"""

from __future__ import annotations

import argparse
import base64
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import load_pem_public_key

from .qr_code_generator import QRCodeGenerator

logger = logging.getLogger(__name__)


@dataclass
class QREncryptionResult:
    qr_data: Dict[str, Any]
    qr_string: str
    encrypted_payload: str
    encryption_metadata: Dict[str, Any]


class QRSigningService:
    """Generate and encrypt QR payloads using the FIRS public key bundle."""

    def __init__(self, *, key_path: Optional[Path] = None, public_key_pem: Optional[str] = None) -> None:
        self._key_path = Path(key_path) if key_path else None
        self._public_key_pem = public_key_pem
        self._public_key: Optional[rsa.RSAPublicKey] = None
        self.qr_generator = QRCodeGenerator()

    def generate_signed_qr(
        self,
        *,
        irn: str,
        verification_code: str,
        invoice_data: Dict[str, Any],
        qr_format: str = "json",
    ) -> Optional[QREncryptionResult]:
        """
        Generate QR artifacts and encrypt them using the configured public key.

        Returns ``None`` when the public key could not be loaded.
        """
        public_key = self._load_public_key()
        if public_key is None:
            logger.warning("QR signing skipped; public key unavailable")
            return None

        verification_code = verification_code or self._derive_verification_code(irn, invoice_data)

        qr_data = self.qr_generator.generate_qr_data(irn, verification_code, invoice_data)
        qr_string = self.qr_generator.generate_qr_string(irn, verification_code, invoice_data, format_type=qr_format)

        payload = {
            "irn": irn,
            "verification_code": verification_code,
            "qr_format": qr_format,
            "qr_string": qr_string,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")

        max_len = public_key.key_size // 8 - 2 * hashes.SHA256().digest_size - 2
        digest_only = False
        if len(payload_bytes) > max_len:
            digest = hashes.Hash(hashes.SHA256())
            digest.update(payload_bytes)
            payload_bytes = digest.finalize()
            digest_only = True

        encrypted_payload = base64.b64encode(
            public_key.encrypt(
                payload_bytes,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
        ).decode("utf-8")

        encryption_metadata = {
            "algorithm": "RSA-OAEP-SHA256",
            "key_source": str(self._key_path) if self._key_path else "inline",
            "payload_version": "1.0",
            "payload_created_at": payload["timestamp"],
            "payload_digest_only": digest_only,
        }

        if digest_only:
            encryption_metadata["payload_digest"] = base64.b64encode(payload_bytes).decode("utf-8")

        return QREncryptionResult(
            qr_data=qr_data,
            qr_string=qr_string,
            encrypted_payload=encrypted_payload,
            encryption_metadata=encryption_metadata,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _load_public_key(self) -> Optional[rsa.RSAPublicKey]:
        if self._public_key is not None:
            return self._public_key

        pem_bytes = None
        if self._public_key_pem:
            pem_bytes = self._public_key_pem.encode("utf-8")
        elif self._key_path and self._key_path.exists():
            pem_bytes = self._extract_public_key_from_bundle(self._key_path)

        if not pem_bytes:
            return None

        try:
            self._public_key = load_pem_public_key(pem_bytes)  # type: ignore[assignment]
        except ValueError as exc:
            logger.error("Failed to load public key: %s", exc)
            return None

        return self._public_key

    @staticmethod
    def _extract_public_key_from_bundle(path: Path) -> Optional[bytes]:
        """Extract the public key block from crypto_keys.txt."""
        try:
            contents = path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.error("Unable to read crypto keys bundle (%s): %s", path, exc)
            return None

        start = contents.find("-----BEGIN PUBLIC KEY-----")
        end = contents.find("-----END PUBLIC KEY-----")
        if start == -1 or end == -1:
            logger.error("Public key block not found in %s", path)
            return None

        end += len("-----END PUBLIC KEY-----")
        return contents[start:end].encode("utf-8")

    @staticmethod
    def _derive_verification_code(irn: str, invoice_data: Dict[str, Any]) -> str:
        material = json.dumps({"irn": irn, "invoice": invoice_data}, sort_keys=True).encode("utf-8")
        digest = hashes.Hash(hashes.SHA256())
        digest.update(material)
        return base64.b32encode(digest.finalize())[:10].decode("utf-8")


# ----------------------------------------------------------------------
# CLI utility
# ----------------------------------------------------------------------
def _cli() -> None:
    parser = argparse.ArgumentParser(description="Generate and encrypt QR payloads for FIRS testing.")
    parser.add_argument("--keys", type=Path, required=True, help="Path to crypto_keys.txt")
    parser.add_argument("--irn", required=True, help="Invoice Reference Number")
    parser.add_argument("--verification-code", default="", help="Verification code associated with the IRN")
    parser.add_argument("--invoice-number", required=True, help="Invoice number")
    parser.add_argument("--issued-on", required=True, help="Invoice issue date (YYYY-MM-DD)")
    parser.add_argument("--format", default="json", choices=("json", "compact", "url"), help="QR output format")
    args = parser.parse_args()

    invoice_payload = {
        "invoice_number": args.invoice_number,
        "invoice_date": args.issued_on,
        "total_amount": 0,
        "currency": "NGN",
        "customer_name": "",
        "customer_tax_id": "",
    }

    service = QRSigningService(key_path=args.keys)
    result = service.generate_signed_qr(
        irn=args.irn,
        verification_code=args.verification_code,
        invoice_data=invoice_payload,
        qr_format=args.format,
    )

    if result is None:
        print("Unable to sign payload – ensure crypto_keys.txt contains a public key.")
        return

    output = {
        "qr_data": result.qr_data,
        "qr_string": result.qr_string,
        "encrypted_payload": result.encrypted_payload,
        "encryption_metadata": result.encryption_metadata,
    }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":  # pragma: no cover - manual utility
    _cli()
