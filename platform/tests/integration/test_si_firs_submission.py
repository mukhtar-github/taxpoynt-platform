"""Integration tests for SI FIRS submission persistence."""

import os
import sys
import types
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from types import MethodType, SimpleNamespace

import pytest


def _ensure_legacy_app_stubs() -> None:
    """Provide placeholder modules for legacy `app.*` imports used in SI services."""

    if "app" in sys.modules:
        return

    app_module = types.ModuleType("app")
    sys.modules["app"] = app_module

    # app.core.config.settings
    core_module = types.ModuleType("app.core")
    services_module = types.ModuleType("app.services")
    config_module = types.ModuleType("app.core.config")
    sys.modules["app.core"] = core_module
    sys.modules["app.services"] = services_module
    sys.modules["app.core.config"] = config_module
    app_module.core = core_module
    core_module.config = config_module
    config_module.settings = SimpleNamespace()

    # app.models.*
    models_module = types.ModuleType("app.models")
    sys.modules["app.models"] = models_module
    app_module.models = models_module

    irn_models_module = types.ModuleType("app.models.irn")
    sys.modules["app.models.irn"] = irn_models_module
    models_module.irn = irn_models_module

    class _Placeholder:
        def __init__(self, **kwargs):
            for key, value in kwargs.items():
                setattr(self, key, value)

    irn_models_module.IRNRecord = _Placeholder
    irn_models_module.InvoiceData = _Placeholder
    irn_models_module.IRNValidationRecord = _Placeholder
    irn_models_module.IRNStatus = _Placeholder

    user_module = types.ModuleType("app.models.user")
    sys.modules["app.models.user"] = user_module
    models_module.user = user_module
    user_module.User = _Placeholder

    organization_module = types.ModuleType("app.models.organization")
    sys.modules["app.models.organization"] = organization_module
    models_module.organization = organization_module
    organization_module.Organization = _Placeholder

    # app.schemas.irn
    schemas_module = types.ModuleType("app.schemas")
    sys.modules["app.schemas"] = schemas_module
    app_module.schemas = schemas_module

    irn_schema_module = types.ModuleType("app.schemas.irn")
    sys.modules["app.schemas.irn"] = irn_schema_module
    schemas_module.irn = irn_schema_module
    irn_schema_module.IRNCreate = _Placeholder
    irn_schema_module.IRNBatchGenerateRequest = _Placeholder

    # app.cache.irn_cache
    cache_module = types.ModuleType("app.cache")
    sys.modules["app.cache"] = cache_module
    app_module.cache = cache_module

    irn_cache_module = types.ModuleType("app.cache.irn_cache")
    sys.modules["app.cache.irn_cache"] = irn_cache_module
    cache_module.irn_cache = irn_cache_module

    class _DummyCache:
        def get(self, *_args, **_kwargs):
            return None

        def set(self, *_args, **_kwargs):
            return None

    irn_cache_module.IRNCache = _DummyCache

    firs_si_module = types.ModuleType("app.services.firs_si")
    sys.modules["app.services.firs_si"] = firs_si_module
    services_module.firs_si = firs_si_module

    firs_service_module = types.ModuleType("app.services.firs_si.irn_generation_service")
    sys.modules["app.services.firs_si.irn_generation_service"] = firs_service_module
    firs_si_module.irn_generation_service = firs_service_module

    odoo_module = types.ModuleType("app.services.firs_si.odoo_service")
    sys.modules["app.services.firs_si.odoo_service"] = odoo_module
    firs_si_module.odoo_service = odoo_module

    comprehensive_module = types.ModuleType("app.services.firs_si.comprehensive_invoice_generator")
    sys.modules[
        "app.services.firs_si.comprehensive_invoice_generator"
    ] = comprehensive_module
    firs_si_module.comprehensive_invoice_generator = comprehensive_module

    def _noop(*_args, **_kwargs):
        return None

    firs_service_module.generate_irn = _noop
    firs_service_module.get_irn_expiration_date = _noop
    firs_service_module.create_validation_record = _noop

    odoo_module.fetch_odoo_invoices = _noop
    odoo_module.initialize_odoo_connection = _noop

    comprehensive_module.ComprehensiveInvoiceGenerator = _Placeholder


_ensure_legacy_app_stubs()


# Ensure backend package is on path when tests execute standalone
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from core_platform.data_management.db_async import get_async_session, init_async_engine
from core_platform.data_management.models.base import Base
from core_platform.data_management.models.organization import Organization
from core_platform.data_management.models.firs_submission import (
    FIRSSubmission,
    InvoiceType,
    SubmissionStatus,
    ValidationStatus,
)
from core_platform.data_management.models.si_app_correlation import (
    CorrelationStatus,
    SIAPPCorrelation,
)
from si_services.irn_qr_generation.irn_generation_service import IRNGenerationService
import si_services.irn_qr_generation.irn_generation_service as irn_service_module


@pytest.mark.asyncio
async def test_request_irn_from_firs_persists_identifiers(monkeypatch):
    monkeypatch.setenv("FIRS_REMOTE_IRN", "true")
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    engine = init_async_engine()

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    org_id = uuid.uuid4()
    initial_irn = "LOCAL-IRN-001"

    submission_id = None
    correlation_id = None

    async for session in get_async_session():
        organization = Organization(id=org_id, name="Test Org")
        session.add(organization)

        submission = FIRSSubmission(
            id=uuid.uuid4(),
            organization_id=org_id,
            invoice_number="INV-001",
            invoice_type=InvoiceType.STANDARD_INVOICE,
            irn=initial_irn,
            status=SubmissionStatus.PENDING,
            validation_status=ValidationStatus.PENDING,
            invoice_data={"invoice_number": "INV-001"},
            total_amount=Decimal("150.00"),
            currency="NGN",
        )

        correlation = SIAPPCorrelation(
            id=uuid.uuid4(),
            organization_id=org_id,
            si_invoice_id="INV-001",
            si_transaction_ids=["TX-001"],
            irn=initial_irn,
            si_generated_at=datetime.now(timezone.utc),
            invoice_number="INV-001",
            total_amount=Decimal("150.00"),
            currency="NGN",
            customer_name="Jane Doe",
        )

        session.add_all([submission, correlation])
        await session.commit()

        submission_id = submission.id
        correlation_id = correlation.id
        break

    class _DummyAuthManager:
        def __init__(self, *args, **kwargs):
            self.args = args
            self.kwargs = kwargs

    monkeypatch.setattr(irn_service_module, "AuthenticationManager", _DummyAuthManager)

    service = IRNGenerationService()

    async def fake_authenticate(self, environment="sandbox", credentials=None):
        return {
            "success": True,
            "environment": environment,
            "auth_data": {"token": "demo"},
            "session_id": "sess-demo",
            "expires_at": datetime.now(timezone.utc).isoformat(),
            "authenticated_at": datetime.now(timezone.utc).isoformat(),
        }

    service.authenticate_with_firs = MethodType(fake_authenticate, service)

    class StubAuthService:
        async def submit_irn(self, irn_value, invoice_data, auth_data, environment):
            return SimpleNamespace(
                success=True,
                response_data={
                    "submissionId": "FIRS-12345",
                    "status": "ACCEPTED",
                    "irn": "REMOTE-IRN-999",
                    "csid": "CSID-XYZ",
                    "csidHash": "HASH-123",
                    "qr": {"payload": "encoded"},
                },
                error_message=None,
                error_code=None,
            )

    service.firs_auth_service = StubAuthService()

    invoice_payload = {
        "invoice_number": "INV-001",
        "organization_id": str(org_id),
    }

    async for session in get_async_session():
        result = await service.request_irn_from_firs(
            irn_value=initial_irn,
            invoice_data=invoice_payload,
            environment="sandbox",
            organization_id=str(org_id),
            db_session=session,
        )
        await session.commit()
        break

    assert result["success"] is True
    assert result["identifiers"]["irn"] == "REMOTE-IRN-999"
    assert result["identifiers"]["csid"] == "CSID-XYZ"

    async for session in get_async_session():
        updated_submission = await session.get(FIRSSubmission, submission_id)
        updated_correlation = await session.get(SIAPPCorrelation, correlation_id)
        break

    assert updated_submission is not None
    assert updated_submission.irn == "REMOTE-IRN-999"
    assert updated_submission.csid == "CSID-XYZ"
    assert updated_submission.csid_hash == "HASH-123"
    assert updated_submission.qr_payload == {"payload": "encoded"}
    assert updated_submission.status == SubmissionStatus.ACCEPTED
    assert updated_submission.firs_submission_id == "FIRS-12345"
    assert updated_submission.firs_response["identifiers"]["irn"] == "REMOTE-IRN-999"
    assert updated_submission.invoice_data["irn"] == "REMOTE-IRN-999"
    assert updated_submission.firs_received_at is not None

    assert updated_correlation is not None
    assert updated_correlation.irn == "REMOTE-IRN-999"
    assert updated_correlation.firs_status.lower() == "accepted"
    assert updated_correlation.current_status == CorrelationStatus.FIRS_ACCEPTED
    assert updated_correlation.firs_response_id == "FIRS-12345"
    assert updated_correlation.firs_response_data["identifiers"]["irn"] == "REMOTE-IRN-999"
    correlation_metadata = updated_correlation.submission_metadata or {}
    assert correlation_metadata.get("identifiers", {}).get("csid") == "CSID-XYZ"
