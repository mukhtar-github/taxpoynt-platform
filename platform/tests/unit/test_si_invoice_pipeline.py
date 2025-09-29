"""Unit tests covering SI invoice generation pipeline integration and certificate operations."""

import os
import sys
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from uuid import uuid4

import pytest


def _ensure_backend_path() -> None:
    """Add the backend directory to sys.path for module imports."""

    current_dir = os.path.dirname(__file__)
    backend_dir = os.path.abspath(os.path.join(current_dir, "..", "..", "backend"))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)


_ensure_backend_path()

def _stub_legacy_app_modules() -> None:
    """Provide minimal stubs for legacy `app.*` imports used by certificate services."""

    import types

    if "app" in sys.modules:
        return

    app_module = types.ModuleType("app")
    app_module.__path__ = []
    sys.modules["app"] = app_module

    # app.models.certificate
    models_module = types.ModuleType("app.models")
    models_module.__path__ = []
    sys.modules["app.models"] = models_module

    certificate_module = types.ModuleType("app.models.certificate")
    certificate_module.__path__ = []  # pragma: no cover - namespace marker

    class Certificate:  # pylint: disable=too-few-public-methods
        pass

    class CertificateRevocation:  # pylint: disable=too-few-public-methods
        pass

    class CertificateType:  # pylint: disable=too-few-public-methods
        pass

    class CertificateStatus:  # pylint: disable=too-few-public-methods
        ACTIVE = "active"

    certificate_module.Certificate = Certificate
    certificate_module.CertificateRevocation = CertificateRevocation
    certificate_module.CertificateType = CertificateType
    certificate_module.CertificateStatus = CertificateStatus

    models_module.certificate = certificate_module
    app_module.models = models_module
    sys.modules["app.models.certificate"] = certificate_module

    # app.models.certificate_request
    certificate_request_module = types.ModuleType("app.models.certificate_request")
    certificate_request_module.__path__ = []  # pragma: no cover - namespace marker

    class CertificateRequest:  # pylint: disable=too-few-public-methods
        def __init__(self, **kwargs):  # pragma: no cover - minimal stub
            for key, value in kwargs.items():
                setattr(self, key, value)

    class CertificateRequestStatus:  # pylint: disable=too-few-public-methods
        PENDING = "pending"
        APPROVED = "approved"
        REJECTED = "rejected"

    class CertificateRequestType:  # pylint: disable=too-few-public-methods
        SIGNING = "signing"
        ENCRYPTION = "encryption"

    certificate_request_module.CertificateRequest = CertificateRequest
    certificate_request_module.CertificateRequestStatus = CertificateRequestStatus
    certificate_request_module.CertificateRequestType = CertificateRequestType
    models_module.certificate_request = certificate_request_module
    sys.modules["app.models.certificate_request"] = certificate_request_module

    # app.schemas.certificate
    schemas_module = types.ModuleType("app.schemas")
    schemas_module.__path__ = []
    sys.modules["app.schemas"] = schemas_module

    certificate_request_schema_module = types.ModuleType("app.schemas.certificate_request")
    certificate_request_schema_module.__path__ = []  # pragma: no cover

    class CertificateRequestCreate:  # pylint: disable=too-few-public-methods
        def __init__(self, **kwargs):  # pragma: no cover - data container
            for key, value in kwargs.items():
                setattr(self, key, value)

    class CertificateRequestUpdate:  # pylint: disable=too-few-public-methods
        def __init__(self, **kwargs):  # pragma: no cover - data container
            for key, value in kwargs.items():
                setattr(self, key, value)

    certificate_request_schema_module.CertificateRequestCreate = CertificateRequestCreate
    certificate_request_schema_module.CertificateRequestUpdate = CertificateRequestUpdate
    schemas_module.certificate_request = certificate_request_schema_module
    sys.modules["app.schemas.certificate_request"] = certificate_request_schema_module

    certificate_schema_module = types.ModuleType("app.schemas.certificate")
    certificate_schema_module.__path__ = []  # pragma: no cover

    class CertificateCreate:  # pylint: disable=too-few-public-methods
        pass

    class CertificateUpdate:  # pylint: disable=too-few-public-methods
        pass

    class CertificateVerification:  # pylint: disable=too-few-public-methods
        pass

    class CertificateRequestCreate:  # pylint: disable=too-few-public-methods
        pass

    class CertificateRequestUpdate:  # pylint: disable=too-few-public-methods
        pass

    certificate_schema_module.CertificateCreate = CertificateCreate
    certificate_schema_module.CertificateUpdate = CertificateUpdate
    certificate_schema_module.CertificateVerification = CertificateVerification
    certificate_schema_module.CertificateRequestCreate = CertificateRequestCreate
    certificate_schema_module.CertificateRequestUpdate = CertificateRequestUpdate

    schemas_module.certificate = certificate_schema_module
    app_module.schemas = schemas_module
    sys.modules["app.schemas.certificate"] = certificate_schema_module

    # app.services.key_service
    services_module = types.ModuleType("app.services")
    services_module.__path__ = []
    sys.modules["app.services"] = services_module

    key_service_module = types.ModuleType("app.services.key_service")
    key_service_module.__path__ = []  # pragma: no cover

    class KeyManagementService:  # pylint: disable=too-few-public-methods
        def encrypt_data(self, data, context=None):  # pragma: no cover - deterministic stub
            return "stub-key", data

    key_service_module.KeyManagementService = KeyManagementService
    services_module.key_service = key_service_module
    app_module.services = services_module
    sys.modules["app.services.key_service"] = key_service_module

    # app.utils.encryption
    utils_module = types.ModuleType("app.utils")
    utils_module.__path__ = []
    sys.modules["app.utils"] = utils_module

    encryption_module = types.ModuleType("app.utils.encryption")
    encryption_module.__path__ = []  # pragma: no cover

    def encrypt_field(value, *_args, **_kwargs):  # pragma: no cover - identity stub
        return value

    def decrypt_field(value, *_args, **_kwargs):  # pragma: no cover - identity stub
        return value

    encryption_module.encrypt_field = encrypt_field
    encryption_module.decrypt_field = decrypt_field
    utils_module.encryption = encryption_module
    app_module.utils = utils_module
    sys.modules["app.utils.encryption"] = encryption_module

    # app.core.config
    core_module = types.ModuleType("app.core")
    core_module.__path__ = []
    sys.modules["app.core"] = core_module

    config_module = types.ModuleType("app.core.config")

    class _Settings:  # pylint: disable=too-few-public-methods
        def __init__(self) -> None:
            self.environment = "test"

    config_module.settings = _Settings()
    core_module.config = config_module
    app_module.core = core_module
    sys.modules["app.core.config"] = config_module


_stub_legacy_app_modules()


def _stub_si_certificate_legacy_modules() -> None:
    """Provide stubs for legacy SI certificate modules imported during setup."""

    import types

    legacy_module_name = "si_services.certificate_management.digital_certificate_service_legacy"
    if legacy_module_name not in sys.modules:
        legacy_module = types.ModuleType(legacy_module_name)

        class DigitalCertificateService:  # pylint: disable=too-few-public-methods
            pass

        legacy_module.DigitalCertificateService = DigitalCertificateService
        sys.modules[legacy_module_name] = legacy_module


_stub_si_certificate_legacy_modules()

from si_services import SIServiceRegistry  # noqa: E402
from si_services import __init__ as si_services_module  # noqa: E402
from si_services.firs_integration import (  # noqa: E402
    comprehensive_invoice_generator as gen_module,
)
from si_services.firs_integration.comprehensive_invoice_generator import (  # noqa: E402
    BusinessTransactionData,
    ComprehensiveFIRSInvoiceGenerator,
    DataSourceType,
    FIRSInvoiceGenerationRequest,
)


class DummyFormatter:
    """Minimal formatter stub for generator dependencies."""

    def __init__(self) -> None:
        self.supplier_info = {"name": "Test Supplier"}


class DummyDBSession:
    """AsyncSession stub capturing added submissions during tests."""

    def __init__(self) -> None:
        self.added = []

    def add(self, obj) -> None:  # pragma: no cover - simple capture
        self.added.append(obj)

    async def commit(self) -> None:  # pragma: no cover - no-op
        return None


class StubCorrelationService:
    async def create_correlation(self, **kwargs) -> None:  # pragma: no cover - no-op
        return None


@pytest.mark.asyncio
async def test_individual_invoice_pipeline_merges_transformation(monkeypatch):
    """The generator should surface transformation output and warnings in responses."""

    # Patch correlation service constructor before instantiation
    monkeypatch.setattr(gen_module, "SIAPPCorrelationService", lambda db: StubCorrelationService())

    # Avoid connector initialization side effects
    dummy_connector = lambda *args, **kwargs: SimpleNamespace()
    monkeypatch.setattr(gen_module, "SAPConnector", dummy_connector)
    monkeypatch.setattr(gen_module, "OdooConnector", dummy_connector)
    monkeypatch.setattr(gen_module, "MonoConnector", dummy_connector)
    monkeypatch.setattr(gen_module, "PaystackConnector", dummy_connector)

    # Track UBL payload used by the transformer
    ubl_inputs: SimpleNamespace = SimpleNamespace(payload=None)

    def fake_transform_to_ubl(payload, source_format="odoo"):
        ubl_inputs.payload = payload
        return {"ubl": True}

    def fake_transform_to_firs(_ubl_payload):
        return {"firs": True}

    def fake_validate(_ubl_payload):
        return True, []

    monkeypatch.setattr(gen_module.schema_transformer, "transform_to_ubl_invoice", fake_transform_to_ubl)
    monkeypatch.setattr(gen_module.schema_transformer, "transform_to_firs_format", fake_transform_to_firs)
    monkeypatch.setattr(gen_module.ubl_validator, "validate_ubl_document", fake_validate)

    async def fake_run_pipeline(self, base_invoice, source_context):
        return {
            "success": True,
            "warnings": ["transform warn"],
            "errors": [],
            "erp_system": "odoo",
            "metadata": {"foo": "bar"},
            "processing_time": 0.42,
            "normalized_invoice": {
                "total_amount": 200.0,
                "tax_amount": 10.0,
                "currency_code": "NGN",
                "invoice_number": "INV-merged",
                "customer_name": "Normalized Customer",
            },
        }

    async def fake_generate_irn(self, transaction, organization_id, is_consolidated=False):
        return "IRN001"

    async def fake_get_org(self, organization_id):  # pragma: no cover - not exercised further
        return None

    monkeypatch.setattr(ComprehensiveFIRSInvoiceGenerator, "_run_transformation_pipeline", fake_run_pipeline)
    monkeypatch.setattr(ComprehensiveFIRSInvoiceGenerator, "_generate_irn", fake_generate_irn)
    monkeypatch.setattr(ComprehensiveFIRSInvoiceGenerator, "_get_organization_profile", fake_get_org)

    generator = ComprehensiveFIRSInvoiceGenerator(DummyDBSession(), DummyFormatter())

    transaction = BusinessTransactionData(
        id="txn-1",
        source_type=DataSourceType.ERP,
        source_id="odoo",
        transaction_id="TXN-001",
        date=datetime.utcnow(),
        customer_name="Customer A",
        customer_email="customer@example.com",
        customer_tin="TIN001",
        amount=Decimal("110.0"),
        currency="NGN",
        description="Invoice",
        line_items=[
            {
                "name": "Item",
                "quantity": 1,
                "price_unit": 100,
                "price_subtotal": 100,
                "tax_rate": 10,
            }
        ],
        tax_amount=Decimal("10.0"),
        vat_rate=Decimal("10.0"),
        payment_status="paid",
        payment_method="card",
        confidence=99.0,
        raw_data={"raw": True},
    )

    request = FIRSInvoiceGenerationRequest(
        organization_id=uuid4(),
        transaction_ids=[transaction.id],
        include_digital_signature=False,
    )

    result = await generator._generate_individual_invoice(transaction, request)

    assert result["total_amount"] == 200.0
    assert result["warnings"] == ["transform warn"]
    assert result["transformation_pipeline"]["metadata"] == {"foo": "bar"}
    assert result["transformation_pipeline"]["erp_system"] == "odoo"
    assert result["validation_status"] == "valid"
    assert ubl_inputs.payload["amount_total"] == 200.0


@pytest.mark.asyncio
async def test_certificate_callback_verifies_signature(monkeypatch):
    """The certificate callback should invoke verify_signature and surface its result."""

    verify_calls = []

    class StubAsyncSessionIterator:
        def __aiter__(self):
            async def _gen():
                yield SimpleNamespace()

            return _gen()

    class StubCertificateService:
        def __init__(self, db=None):
            self.db = db

        async def generate_certificate(self, **_kwargs):  # pragma: no cover
            return "stub", "-----BEGIN CERTIFICATE-----"

        async def revoke_certificate(self, *_args, **_kwargs):  # pragma: no cover
            return True

        def renew_certificate(self, *_args, **_kwargs):  # pragma: no cover
            return "stub", True

        def validate_certificate(self, *_args, **_kwargs):  # pragma: no cover
            return {"is_valid": True}

        def get_certificate_status(self, *_args, **_kwargs):  # pragma: no cover
            return {"status": "active"}

    class StubDigitalCertificateService:
        def verify_signature(self, data, signature_info, certificate_id=None):
            verify_calls.append((data, signature_info, certificate_id))
            return {"is_valid": True, "extra": "ok"}

    monkeypatch.setattr(
        "core_platform.data_management.db_async.get_async_session",
        lambda: StubAsyncSessionIterator(),
    )
    monkeypatch.setattr(
        "si_services.certificate_management.certificate_service.CertificateService",
        StubCertificateService,
    )
    monkeypatch.setattr(
        "si_services.certificate_management.digital_certificate_service.DigitalCertificateService",
        StubDigitalCertificateService,
    )

    registry = SIServiceRegistry(message_router=SimpleNamespace())
    cert_callback = registry._create_certificate_callback({})

    payload = {
        "certificate_id": "cert-123",
        "data": {"foo": "bar"},
        "signature_info": {"signature": "abc"},
    }

    result = await cert_callback("verify_signature", payload)

    assert result["success"] is True
    assert result["data"]["is_valid"] is True
    assert verify_calls[0][0] == '{"foo":"bar"}'
    assert verify_calls[0][2] == "cert-123"
