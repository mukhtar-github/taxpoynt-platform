"""
IRN signing helpers.

Provides reusable utilities for generating canonical IRNs, encrypting the
FIRS payload, and optionally producing QR artefacts. The functions here are
shared by both runtime services and the operator CLI.
"""

from __future__ import annotations

import base64
import json
import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Dict, Optional, Tuple

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from core_platform.utils.irn_helper import generate_canonical_irn

__all__ = [
    "CryptoBundle",
    "SignedIRNResult",
    "load_crypto_bundle",
    "decode_public_key",
    "decode_certificate",
    "generate_irn_with_timestamp",
    "create_payload",
    "encrypt_payload",
    "generate_signed_irn",
    "generate_signed_irn_from_path",
    "generate_qr_png",
]


@dataclass
class CryptoBundle:
    """Parsed crypto bundle components."""

    public_key_b64: str
    certificate_b64: str

    def as_dict(self) -> Dict[str, str]:
        return {
            "public_key": self.public_key_b64,
            "certificate": self.certificate_b64,
        }


@dataclass
class SignedIRNResult:
    """Result of building and encrypting a signing payload."""

    bundle: CryptoBundle
    public_key_pem: bytes
    certificate_bytes: bytes
    irn_with_timestamp: str
    timestamp: int
    payload_bytes: bytes
    encrypted_bytes: bytes
    encrypted_base64: str
    metadata: Dict[str, object]
    qr_png_bytes: Optional[bytes] = None


def load_crypto_bundle(path: Path) -> CryptoBundle:
    """Load the crypto bundle JSON from `crypto_keys.txt`."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise FileNotFoundError(f"Crypto bundle not found at {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Expected JSON in {path}, but parsing failed") from exc

    try:
        public_key = data["public_key"]
        certificate = data["certificate"]
    except KeyError as exc:
        raise ValueError("crypto_keys bundle must contain 'public_key' and 'certificate' fields") from exc

    if not isinstance(public_key, str) or not isinstance(certificate, str):
        raise ValueError("'public_key' and 'certificate' must be base64-encoded strings")

    return CryptoBundle(public_key, certificate)


def decode_public_key(bundle: CryptoBundle) -> bytes:
    """Return the PEM-encoded public key bytes."""
    pem_bytes = base64.b64decode(bundle.public_key_b64)
    if b"BEGIN PUBLIC KEY" not in pem_bytes:
        raise ValueError("Decoded public key does not contain a PEM header")
    return pem_bytes


def decode_certificate(bundle: CryptoBundle) -> bytes:
    """Return the raw certificate bytes (base64-decoded)."""
    return base64.b64decode(bundle.certificate_b64)


def generate_irn_with_timestamp(
    invoice_number: str,
    service_id: str,
    issued_on: str,
    timestamp: Optional[int] = None,
) -> Tuple[str, int]:
    """
    Build the canonical IRN and append a UNIX timestamp.

    Returns:
        tuple: (irn_with_timestamp, timestamp_used)
    """
    canonical_irn = generate_canonical_irn(
        invoice_number=invoice_number,
        service_id=service_id,
        issued_on=issued_on,
    )
    ts = int(timestamp if timestamp is not None else time.time())
    return f"{canonical_irn}.{ts}", ts


def create_payload(irn_with_ts: str, certificate_b64: str) -> bytes:
    """Build the JSON payload to encrypt."""
    payload = {
        "irn": irn_with_ts,
        "certificate": certificate_b64,
    }
    return json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def encrypt_payload(public_key_pem: bytes, payload: bytes) -> bytes:
    """Encrypt the payload using RSA OAEP SHA256."""
    public_key = serialization.load_pem_public_key(public_key_pem)
    return public_key.encrypt(
        payload,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )


def generate_qr_png(encrypted_b64: str) -> bytes:
    """Render a QR code PNG for the encrypted payload."""
    try:
        import qrcode
    except ImportError as exc:  # pragma: no cover - optional dependency
        raise RuntimeError(
            "The 'qrcode' package is required to generate QR images. Install with `pip install qrcode[pil]`."
        ) from exc

    image = qrcode.make(encrypted_b64)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def generate_signed_irn(
    *,
    bundle: CryptoBundle,
    invoice_number: str,
    service_id: str,
    issued_on: str,
    timestamp: Optional[int] = None,
    include_qr: bool = False,
) -> SignedIRNResult:
    """Produce encrypted IRN artefacts from an in-memory bundle."""
    public_key_pem = decode_public_key(bundle)
    certificate_bytes = decode_certificate(bundle)

    irn_with_timestamp, timestamp_value = generate_irn_with_timestamp(
        invoice_number=invoice_number,
        service_id=service_id,
        issued_on=issued_on,
        timestamp=timestamp,
    )
    payload_bytes = create_payload(irn_with_timestamp, bundle.certificate_b64)
    encrypted_bytes = encrypt_payload(public_key_pem, payload_bytes)
    encrypted_b64 = base64.b64encode(encrypted_bytes).decode("utf-8")

    metadata = {
        "invoiceNumber": invoice_number,
        "serviceId": service_id,
        "issueDate": issued_on,
        "timestamp": timestamp_value,
        "irnWithTimestamp": irn_with_timestamp,
        "encrypted_base64_length": len(encrypted_b64),
    }

    qr_png_bytes = generate_qr_png(encrypted_b64) if include_qr else None

    return SignedIRNResult(
        bundle=bundle,
        public_key_pem=public_key_pem,
        certificate_bytes=certificate_bytes,
        irn_with_timestamp=irn_with_timestamp,
        timestamp=timestamp_value,
        payload_bytes=payload_bytes,
        encrypted_bytes=encrypted_bytes,
        encrypted_base64=encrypted_b64,
        metadata=metadata,
        qr_png_bytes=qr_png_bytes,
    )


def generate_signed_irn_from_path(
    *,
    bundle_path: Path,
    invoice_number: str,
    service_id: str,
    issued_on: str,
    timestamp: Optional[int] = None,
    include_qr: bool = False,
) -> SignedIRNResult:
    """Load a crypto bundle from disk and produce encrypted artefacts."""
    bundle = load_crypto_bundle(bundle_path)
    return generate_signed_irn(
        bundle=bundle,
        invoice_number=invoice_number,
        service_id=service_id,
        issued_on=issued_on,
        timestamp=timestamp,
        include_qr=include_qr,
    )
