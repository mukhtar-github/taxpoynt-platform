from datetime import datetime

import pytest

from core_platform.utils.irn_helper import (
    IRNGenerationError,
    generate_canonical_irn,
)


def test_generate_canonical_irn_basic():
    result = generate_canonical_irn("INV-001", "svc-01", "2024-06-05")
    assert result == "INV001-SVC01000-20240605"


def test_generate_canonical_irn_strips_invalid_characters():
    result = generate_canonical_irn("ACME invoice #12", "svc id@", datetime(2024, 7, 9))
    assert result == "ACMEINVOICE12-SVCID000-20240709"


def test_generate_canonical_irn_numeric_padding():
    result = generate_canonical_irn("7", "svc", datetime(2024, 1, 5))
    assert result == "7-SVC00000-20240105"


def test_generate_canonical_irn_invalid_date_raises():
    with pytest.raises(IRNGenerationError):
        generate_canonical_irn("INV-001", "svc", "not-a-date")
