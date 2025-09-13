"""
Integration tests for SI organization endpoints using FastAPI TestClient.
Validates the async recent submissions and transaction summary endpoints.
"""
import os
import sys
import uuid
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Put platform/backend on sys.path
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from api_gateway.api_versions.v1.si_endpoints.organization_endpoints import OrganizationEndpointsV1
from api_gateway.role_routing.models import HTTPRoutingContext
from core_platform.data_management.db_async import init_async_engine
from core_platform.data_management.models.base import Base
from core_platform.data_management.models.organization import Organization
from core_platform.data_management.models.firs_submission import (
    FIRSSubmission,
    SubmissionStatus,
    ValidationStatus,
    InvoiceType,
)
from sqlalchemy.ext.asyncio import AsyncSession
from core_platform.data_management.db_async import get_async_session


class StubRoleDetector:
    async def detect_role_context(self, request):
        from core_platform.authentication.role_manager import PlatformRole
        return HTTPRoutingContext(
            user_id="user-si",
            platform_role=PlatformRole.SYSTEM_INTEGRATOR,
        )


class StubPermissionGuard:
    async def check_endpoint_permission(self, context, route, method):
        return True


@pytest.mark.asyncio
async def test_si_org_recent_and_summary_integration(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    engine = init_async_engine()

    # Create schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Prepare sample data (two orgs for isolation)
    org = Organization(id=uuid.uuid4(), name="Org SI")
    org2 = Organization(id=uuid.uuid4(), name="Other Org")
    async for db in get_async_session():
        db: AsyncSession
        db.add_all([org, org2])
        await db.flush()
        s1 = FIRSSubmission(
            id=uuid.uuid4(),
            organization_id=org.id,
            invoice_number="S-1",
            invoice_type=InvoiceType.STANDARD_INVOICE,
            status=SubmissionStatus.ACCEPTED,
            validation_status=ValidationStatus.VALID,
            invoice_data={"s": 1},
            total_amount=150,
            currency="NGN",
        )
        db.add(s1)
        # Submission for other org (should not appear)
        s_other = FIRSSubmission(
            id=uuid.uuid4(),
            organization_id=org2.id,
            invoice_number="X-1",
            invoice_type=InvoiceType.STANDARD_INVOICE,
            status=SubmissionStatus.SUBMITTED,
            validation_status=ValidationStatus.VALID,
            invoice_data={"s": 9},
            total_amount=999,
            currency="NGN",
        )
        db.add(s_other)
        await db.commit()
        break

    app = FastAPI()
    rd = StubRoleDetector()
    guard = StubPermissionGuard()
    endpoints = OrganizationEndpointsV1(rd, guard, message_router=None)
    app.include_router(endpoints.router, prefix="/api/v1/si")

    client = TestClient(app)

    # Recent submissions
    r1 = client.get(f"/api/v1/si/organizations/{org.id}/submissions/recent")
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["success"] is True
    assert body1["data"]["count"] == 1
    # Ensure only org's invoices returned
    assert all(item["invoice_number"].startswith("S-") for item in body1["data"]["items"])

    # Summary
    r2 = client.get(f"/api/v1/si/organizations/{org.id}/transaction-summary")
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["success"] is True
    assert body2["data"]["summary"]["total_transmissions"] >= 1
