import base64
import json
from pathlib import Path

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from core_platform.security import irn_signing


def _make_bundle(tmp_path: Path, public_key_pem: bytes, certificate_bytes: bytes) -> Path:
    bundle = {
        "public_key": base64.b64encode(public_key_pem).decode("utf-8"),
        "certificate": base64.b64encode(certificate_bytes).decode("utf-8"),
    }
    bundle_path = tmp_path / "crypto_keys.txt"
    bundle_path.write_text(json.dumps(bundle), encoding="utf-8")
    return bundle_path


def test_generate_irn_with_timestamp():
    irn_with_ts, ts = irn_signing.generate_irn_with_timestamp("INV-001", "svc-01", "2024-06-05", timestamp=1700000000)
    assert ts == 1700000000
    assert irn_with_ts == "INV001-SVC01000-20240605.1700000000"


def test_round_trip_encryption(tmp_path):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    certificate_bytes = b"dummy-certificate"

    bundle_path = _make_bundle(tmp_path, public_pem, certificate_bytes)

    bundle = irn_signing.load_crypto_bundle(bundle_path)
    decoded_public = irn_signing.decode_public_key(bundle)
    assert decoded_public == public_pem

    decoded_cert = irn_signing.decode_certificate(bundle)
    assert decoded_cert == certificate_bytes

    irn_with_ts, ts = irn_signing.generate_irn_with_timestamp("INV-123", "service01", "2024-01-15", timestamp=1700001234)
    payload = irn_signing.create_payload(irn_with_ts, bundle.certificate_b64)
    encrypted = irn_signing.encrypt_payload(decoded_public, payload)

    decrypted = private_key.decrypt(
        encrypted,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )

    decoded_payload = json.loads(decrypted.decode("utf-8"))
    assert decoded_payload["irn"] == "INV123-SERVICE01-20240115.1700001234"
    assert decoded_payload["certificate"] == bundle.certificate_b64
    assert ts == 1700001234


def test_generate_signed_irn(tmp_path):
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    certificate_bytes = b"dummy-certificate"

    bundle_path = _make_bundle(tmp_path, public_pem, certificate_bytes)
    bundle = irn_signing.load_crypto_bundle(bundle_path)

    result = irn_signing.generate_signed_irn(
        bundle=bundle,
        invoice_number="INV-456",
        service_id="service02",
        issued_on="2024-02-20",
        timestamp=1700004000,
    )

    assert result.irn_with_timestamp == "INV456-SERVICE02-20240220.1700004000"
    assert result.metadata["irnWithTimestamp"] == result.irn_with_timestamp
    assert result.metadata["invoiceNumber"] == "INV-456"
    assert result.qr_png_bytes is None

    decrypted = private_key.decrypt(
        result.encrypted_bytes,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None,
        ),
    )
    payload = json.loads(decrypted.decode("utf-8"))
    assert payload["irn"] == result.irn_with_timestamp
    assert payload["certificate"] == bundle.certificate_b64


def test_load_crypto_bundle_missing_fields(tmp_path):
    path = tmp_path / "crypto_keys.txt"
    path.write_text(json.dumps({"public_key": "abc"}), encoding="utf-8")
    with pytest.raises(ValueError):
        irn_signing.load_crypto_bundle(path)
