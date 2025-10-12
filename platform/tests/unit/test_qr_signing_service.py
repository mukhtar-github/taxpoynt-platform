import base64
from pathlib import Path

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from si_services.irn_qr_generation.qr_signing_service import QRSigningService


def _generate_public_key_bundle(tmp_path: Path) -> Path:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    bundle = tmp_path / "crypto_keys.txt"
    bundle.write_bytes(b"some header\n" + public_pem + b"\nsome footer\n")
    return bundle


def test_qr_signing_service_generates_metadata(tmp_path):
    bundle_path = _generate_public_key_bundle(tmp_path)
    service = QRSigningService(key_path=bundle_path)

    result = service.generate_signed_qr(
        irn="INV-SVC-001-20240101",
        verification_code="",
        invoice_data={
            "invoice_number": "INV-001",
            "invoice_date": "2024-01-01",
            "total_amount": 1000,
            "currency": "NGN",
        },
    )

    assert result is not None
    assert "key_source" in result.encryption_metadata
    assert base64.b64decode(result.encrypted_payload)
    assert result.qr_data["irn"] == "INV-SVC-001-20240101"
    assert result.qr_data["verification_code"]
    assert result.encryption_metadata["algorithm"] == "RSA-OAEP-SHA256"
    assert "payload_digest_only" in result.encryption_metadata
