"""Tests for the legacy IRNGenerator FIRS-compliant fallback."""

from datetime import datetime
from importlib import util
from pathlib import Path

import pytest

from core_platform.config import feature_flags

BASE_DIR = Path(__file__).resolve().parents[2] / "backend/si_services/irn_qr_generation"


def _load_module(name: str, filename: str):
    spec = util.spec_from_file_location(name, BASE_DIR / filename)
    module = util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


irn_generator_module = _load_module("irn_generator", "irn_generator.py")
irn_validator_module = _load_module("irn_validator", "irn_validator.py")

IRNGenerator = irn_generator_module.IRNGenerator
IRNValidator = irn_validator_module.IRNValidator
ValidationLevel = irn_validator_module.ValidationLevel


@pytest.fixture(autouse=True)
def clear_feature_flag_cache():
    feature_flags.get_feature_flags.cache_clear()
    yield
    feature_flags.get_feature_flags.cache_clear()


@pytest.fixture
def local_irn_mode(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("FIRS_REMOTE_IRN", "false")
    feature_flags.get_feature_flags.cache_clear()
    yield
    monkeypatch.delenv("FIRS_REMOTE_IRN", raising=False)
    feature_flags.get_feature_flags.cache_clear()


def test_generate_irn_uses_firs_format(local_irn_mode):
    generator = IRNGenerator(secret_key="test-secret")
    invoice_data = {
        "invoice_number": "INV-001",
        "service_id": "94ND90NR",
        "invoice_date": "2024-11-05",
        "total_amount": "150.00",
    }

    irn_value, verification_code, final_hash = generator.generate_irn(invoice_data)

    prefix, service_id, date_part = irn_value.rsplit('-', 2)
    assert prefix == "INV001"
    assert service_id == "94ND90NR"
    assert date_part == "20241105"
    assert len(verification_code) == 8
    assert len(final_hash) == 64

    validator = IRNValidator()
    result = validator.validate_irn(irn_value, verification_code=verification_code, validation_level=ValidationLevel.BASIC)
    assert result.is_valid


def test_generate_simple_irn_respects_format(local_irn_mode):
    generator = IRNGenerator(secret_key="test-secret")
    irn_value = generator.generate_simple_irn("ORD-42")

    prefix, service_id, date_part = irn_value.rsplit('-', 2)
    assert prefix == "ORD42"
    assert service_id == "SVC00001"
    datetime.strptime(date_part, "%Y%m%d")


def test_generate_irn_ignores_remote_flag(monkeypatch):
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.setenv("FIRS_REMOTE_IRN", "true")
    feature_flags.get_feature_flags.cache_clear()

    generator = IRNGenerator(secret_key="test-secret")

    irn_value, verification_code, _ = generator.generate_irn(
        {"invoice_number": "INV1001", "service_id": "ABCDEFGH", "invoice_date": "2024-02-10"}
    )

    assert irn_value.startswith("INV1001-ABCDEFGH-")
    assert len(verification_code) == 8
