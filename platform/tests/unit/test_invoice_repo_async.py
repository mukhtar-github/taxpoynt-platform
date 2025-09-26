"""Unit tests for the async invoice repository helpers."""

import os
import sys
import uuid
from datetime import datetime, timezone

import pytest


CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core_platform.data_management.db_async import init_async_engine, get_async_session
from core_platform.data_management.models.base import Base
from core_platform.data_management.models.organization import Organization
from core_platform.data_management.models.firs_submission import (
    FIRSSubmission,
    SubmissionStatus,
    ValidationStatus,
    InvoiceType,
)
from core_platform.data_management.models.si_app_correlation import (
    SIAPPCorrelation,
    CorrelationStatus,
)
from core_platform.data_management.repositories import invoice_repo_async as invoice_repo
from core_platform.data_management import db_async


async def _create_minimal_schema(engine) -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Organization.__table__.create, checkfirst=True)
        await conn.run_sync(FIRSSubmission.__table__.create, checkfirst=True)
        await conn.run_sync(SIAPPCorrelation.__table__.create, checkfirst=True)


async def _dispose_async_engine(engine) -> None:
    try:
        await engine.dispose()
    except Exception:
        pass
    db_async._async_engine = None
    db_async._session_maker = None


@pytest.mark.asyncio
async def test_get_invoice_record_from_submission(monkeypatch):
    db_path = os.path.join(CURRENT_DIR, "invoice_repo_test1.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    engine = init_async_engine()

    await _create_minimal_schema(engine)

    org_id = uuid.uuid4()
    submission_id = uuid.uuid4()
    invoice_payload = {
        "invoiceNumber": "INV-1001",
        "totalAmount": "500.00",
        "currency": "NGN",
        "items": [{"description": "Service", "amount": 500}],
        "irn": "IRN-12345",
    }

    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with SessionLocal() as db:
        db: AsyncSession
        db.add(
            Organization(id=org_id, name="Repo Org"),
        )
        await db.flush()

        submission = FIRSSubmission(
            id=submission_id,
            organization_id=org_id,
            invoice_number="INV-1001",
            invoice_type=InvoiceType.STANDARD_INVOICE,
            status=SubmissionStatus.SUBMITTED,
            validation_status=ValidationStatus.VALID,
            invoice_data=invoice_payload,
            total_amount=500,
            currency="NGN",
            created_at=datetime.now(timezone.utc),
            irn="IRN-12345",
        )
        db.add(submission)
        await db.commit()

        record = await invoice_repo.get_invoice_record(
            db,
            organization_id=str(org_id),
            invoice_number="INV-1001",
        )
        assert record is not None
        assert record.invoice_number == "INV-1001"
        assert record.irn == "IRN-12345"
        assert record.invoice_data["totalAmount"] == "500.00"

    await _dispose_async_engine(engine)


@pytest.mark.asyncio
async def test_get_invoice_record_from_correlation(monkeypatch):
    db_path = os.path.join(CURRENT_DIR, "invoice_repo_test2.db")
    if os.path.exists(db_path):
        os.remove(db_path)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    engine = init_async_engine()

    await _create_minimal_schema(engine)

    org_id = uuid.uuid4()
    correlation_id = "COR-ABC123"
    invoice_payload = {
        "invoiceNumber": "INV-2002",
        "totalAmount": "250.00",
        "currency": "NGN",
    }

    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False)
    async with SessionLocal() as db:
        db: AsyncSession
        db.add(Organization(id=org_id, name="Correlation Org"))
        await db.flush()

        correlation = SIAPPCorrelation(
            correlation_id=correlation_id,
            organization_id=org_id,
            si_invoice_id="SI-2002",
            si_transaction_ids=["TX-1"],
            irn="IRN-98765",
            si_generated_at=datetime.now(timezone.utc),
            invoice_number="INV-2002",
            total_amount=250,
            currency="NGN",
            customer_name="Test Customer",
            invoice_data=invoice_payload,
            current_status=CorrelationStatus.SI_GENERATED,
        )
        db.add(correlation)
        await db.commit()

        record = await invoice_repo.get_invoice_record(
            db,
            organization_id=str(org_id),
            invoice_number="INV-2002",
        )
        assert record is not None
        assert record.source == "si_correlation"
        assert record.invoice_data["invoiceNumber"] == "INV-2002"
        assert record.irn == "IRN-98765"

    await _dispose_async_engine(engine)
