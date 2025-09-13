"""
Unit test for async FIRS submission repository with tenant scoping.
"""
import os
import sys
import uuid
import pytest
from datetime import datetime, timezone

# Put platform/backend on sys.path so 'core_platform' can be imported directly
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from core_platform.data_management.db_async import init_async_engine, get_async_session
from core_platform.data_management.models.base import Base
from core_platform.data_management.models.organization import Organization
from core_platform.data_management.models.firs_submission import (
    FIRSSubmission,
    SubmissionStatus,
    ValidationStatus,
    InvoiceType,
)
from core_platform.authentication.tenant_context import (
    set_current_tenant,
    clear_current_tenant,
)
from core_platform.data_management.repositories.firs_submission_repo_async import (
    list_recent_submissions,
)


@pytest.mark.asyncio
async def test_list_recent_submissions_scoped_to_tenant(monkeypatch):
    # Use in-memory DB
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    engine = init_async_engine()

    # Create schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Prepare data
    org1 = Organization(id=uuid.uuid4(), name="Org One")
    org2 = Organization(id=uuid.uuid4(), name="Org Two")

    async for db in get_async_session():
        # Insert organizations and submissions
        db: AsyncSession
        db.add_all([org1, org2])
        await db.flush()

        sub1 = FIRSSubmission(
            id=uuid.uuid4(),
            organization_id=org1.id,
            invoice_number="INV-001",
            invoice_type=InvoiceType.STANDARD_INVOICE,
            status=SubmissionStatus.SUBMITTED,
            validation_status=ValidationStatus.VALID,
            invoice_data={"a": 1},
            total_amount=100,
            currency="NGN",
            customer_name="A",
            created_at=datetime.now(timezone.utc),
        )
        sub2 = FIRSSubmission(
            id=uuid.uuid4(),
            organization_id=org1.id,
            invoice_number="INV-002",
            invoice_type=InvoiceType.STANDARD_INVOICE,
            status=SubmissionStatus.ACCEPTED,
            validation_status=ValidationStatus.VALID,
            invoice_data={"a": 2},
            total_amount=200,
            currency="NGN",
            customer_name="B",
            created_at=datetime.now(timezone.utc),
        )
        sub3 = FIRSSubmission(
            id=uuid.uuid4(),
            organization_id=org2.id,
            invoice_number="INV-003",
            invoice_type=InvoiceType.STANDARD_INVOICE,
            status=SubmissionStatus.SUBMITTED,
            validation_status=ValidationStatus.VALID,
            invoice_data={"a": 3},
            total_amount=300,
            currency="NGN",
            customer_name="C",
            created_at=datetime.now(timezone.utc),
        )
        db.add_all([sub1, sub2, sub3])
        await db.commit()

        # Tenant scoping via context: org1 only
        set_current_tenant(str(org1.id))
        rows = await list_recent_submissions(db, limit=10)
        clear_current_tenant()

        assert len(rows) == 2
        invs = sorted([r.invoice_number for r in rows])
        assert invs == ["INV-001", "INV-002"]

        # Override tenant: org2
        rows2 = await list_recent_submissions(db, limit=10, organization_id=str(org2.id))
        assert len(rows2) == 1
        assert rows2[0].invoice_number == "INV-003"
        break

