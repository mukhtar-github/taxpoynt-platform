"""
Integration tests for APP tracking endpoints using FastAPI TestClient.

Spins up a minimal app instance with the TrackingManagementEndpointsV1
router, overrides role detection/permissions, and uses an in-memory
SQLite database to validate AsyncSession + tenant scoping.
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

from api_gateway.api_versions.v1.app_endpoints.tracking_management_endpoints import TrackingManagementEndpointsV1
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
        return HTTPRoutingContext(
            user_id="user-app",
            organization_id=str(self.org_id),
        )


class StubPermissionGuard:
    async def check_endpoint_permission(self, context, route, method):
        return True


@pytest.mark.asyncio
async def test_app_tracking_recent_and_metrics_integration(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    engine = init_async_engine()

    # Create schema
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Prepare sample data
    org = Organization(id=uuid.uuid4(), name="Org Test")
    async for db in get_async_session():
        db: AsyncSession
        db.add(org)
        await db.flush()
        s1 = FIRSSubmission(
            id=uuid.uuid4(),
            organization_id=org.id,
            invoice_number="A-1",
            invoice_type=InvoiceType.STANDARD_INVOICE,
            status=SubmissionStatus.SUBMITTED,
            validation_status=ValidationStatus.VALID,
            invoice_data={"x": 1},
            total_amount=100,
            currency="NGN",
        )
        s2 = FIRSSubmission(
            id=uuid.uuid4(),
            organization_id=org.id,
            invoice_number="A-2",
            invoice_type=InvoiceType.STANDARD_INVOICE,
            status=SubmissionStatus.ACCEPTED,
            validation_status=ValidationStatus.VALID,
            invoice_data={"x": 2},
            total_amount=200,
            currency="NGN",
        )
        db.add_all([s1, s2])
        await db.commit()
        break

    # Build app with router
    app = FastAPI()
    rd = StubRoleDetector()
    rd.org_id = org.id
    guard = StubPermissionGuard()
    endpoints = TrackingManagementEndpointsV1(rd, guard, message_router=None)  # message_router not used in async handlers
    app.include_router(endpoints.router, prefix="/api/v1/app")

    client = TestClient(app)

    # Recent submissions
    r1 = client.get("/api/v1/app/tracking/submissions/recent")
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["success"] is True
    assert body1["data"]["count"] == 2
    assert "pagination" in body1["data"]

    # Offset pagination
    r1b = client.get("/api/v1/app/tracking/submissions/recent?limit=1&offset=1")
    assert r1b.status_code == 200
    body1b = r1b.json()
    assert body1b["success"] is True
    assert body1b["data"]["count"] == 1
    assert body1b["data"]["pagination"]["limit"] == 1

    # Metrics
    r2 = client.get("/api/v1/app/tracking/metrics")
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["success"] is True
    assert body2["data"]["totalTransmissions"] == 2
    assert body2["data"]["completed"] == 1
