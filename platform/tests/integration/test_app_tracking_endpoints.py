"""
Integration tests for APP tracking endpoints using FastAPI TestClient.

Spins up a minimal app instance with the TrackingManagementEndpointsV1
router, overrides role detection/permissions, and uses an in-memory
SQLite database to validate AsyncSession + tenant scoping.
"""
import os
import sys
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport

# Put platform/backend on sys.path
CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from api_gateway.api_versions.v1.app_endpoints.tracking_management_endpoints import TrackingManagementEndpointsV1
from api_gateway.role_routing.models import HTTPRoutingContext
from core_platform.authentication.role_manager import PlatformRole
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
from core_platform.data_management.repositories.firs_submission_repo_async import get_submission_by_id


class StubRoleDetector:
    async def detect_role_context(self, request):
        return HTTPRoutingContext(
            user_id="user-app",
            organization_id=str(self.org_id),
            platform_role=PlatformRole.ACCESS_POINT_PROVIDER,
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
    accepted_submission_id = None
    rejected_submission_id = None
    org = Organization(id=uuid.uuid4(), name="Org Test")
    async for db in get_async_session():
        db: AsyncSession
        db.add(org)
        await db.flush()
        now = datetime.now(timezone.utc)
        rejected_submission = FIRSSubmission(
            id=uuid.uuid4(),
            organization_id=org.id,
            invoice_number="A-1",
            invoice_type=InvoiceType.STANDARD_INVOICE,
            status=SubmissionStatus.REJECTED,
            validation_status=ValidationStatus.INVALID,
            invoice_data={"x": 1},
            total_amount=100,
            currency="NGN",
            submitted_at=now - timedelta(hours=4),
            rejected_at=now - timedelta(hours=3),
            firs_message="Schema validation failed",
            error_details={
                "tracking_alerts": {
                    "submission_rejected": {
                        "acknowledged": False,
                    }
                }
            },
        )
        accepted_submission = FIRSSubmission(
            id=uuid.uuid4(),
            organization_id=org.id,
            invoice_number="A-2",
            invoice_type=InvoiceType.STANDARD_INVOICE,
            status=SubmissionStatus.ACCEPTED,
            validation_status=ValidationStatus.VALID,
            invoice_data={"x": 2},
            total_amount=200,
            currency="NGN",
            submitted_at=now - timedelta(hours=2),
            accepted_at=now - timedelta(hours=1),
            firs_response={"status": "accepted", "message": "Processed"},
            firs_submission_id="FIRS-12345",
            firs_status_code="200",
        )
        db.add_all([rejected_submission, accepted_submission])
        accepted_submission_id = str(accepted_submission.id)
        rejected_submission_id = str(rejected_submission.id)
        await db.commit()
        break

    # Build app with router
    app = FastAPI()
    rd = StubRoleDetector()
    rd.org_id = org.id
    guard = StubPermissionGuard()
    endpoints = TrackingManagementEndpointsV1(rd, guard, message_router=None)  # message_router not used in async handlers
    app.include_router(endpoints.router, prefix="/api/v1/app")

    assert accepted_submission_id is not None
    assert rejected_submission_id is not None

    transport = ASGITransport(app=app)
    default_headers = {
        "X-Platform-User-Id": "user-app",
        "X-Platform-Roles": "access_point_provider",
    }
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Recent submissions
        r1 = await client.get("/api/v1/app/tracking/submissions/recent", headers=default_headers)
        assert r1.status_code == 200
        body1 = r1.json()
        assert body1["success"] is True
        assert body1["data"]["count"] == 2
        assert "pagination" in body1["data"]

        # Offset pagination
        r1b = await client.get(
            "/api/v1/app/tracking/submissions/recent",
            params={"limit": 1, "offset": 1},
            headers=default_headers,
        )
        assert r1b.status_code == 200
        body1b = r1b.json()
        assert body1b["success"] is True
        assert body1b["data"]["count"] == 1
        assert body1b["data"]["pagination"]["limit"] == 1

        # Metrics
        r2 = await client.get("/api/v1/app/tracking/metrics", headers=default_headers)
        assert r2.status_code == 200
        body2 = r2.json()
        assert body2["success"] is True
        assert body2["data"]["totalTransmissions"] == 2
        assert body2["data"]["completed"] == 1

        # Overview derives data from repository helpers
        r_overview = await client.get("/api/v1/app/tracking/overview", headers=default_headers)
        assert r_overview.status_code == 200
        overview_body = r_overview.json()
        assert overview_body["success"] is True
        overview_payload = overview_body["data"]["data"]
        assert overview_payload["metrics"]["totalTransmissions"] == 2
        assert overview_payload["status_distribution"]["rejected"] == 1

        # FIRS responses listing should surface accepted submission payload
        r_responses = await client.get("/api/v1/app/tracking/firs-responses", headers=default_headers)
        assert r_responses.status_code == 200
        responses_body = r_responses.json()
        responses_payload = responses_body["data"]["data"]
        assert responses_payload["count"] == 1
        assert responses_payload["responses"][0]["firs_status_code"] == "200"

        # Response detail should match submission payload
        detail_url = f"/api/v1/app/tracking/firs-responses/{accepted_submission_id}"
        r_detail = await client.get(detail_url, headers=default_headers)
        assert r_detail.status_code == 200
        detail_body = r_detail.json()
        detail_payload = detail_body["data"]["data"]
        assert detail_payload["firs_submission_id"] == "FIRS-12345"

        # Active alerts should include the rejected submission
        r_alerts = await client.get(
            "/api/v1/app/tracking/alerts",
            params={"include_acknowledged": "false"},
            headers=default_headers,
        )
        assert r_alerts.status_code == 200
        alerts_body = r_alerts.json()
        alerts_payload = alerts_body["data"]["data"]
        assert alerts_payload["count"] == 1
        alert_entry = alerts_payload["alerts"][0]
        assert alert_entry["submission_id"] == rejected_submission_id
        assert alert_entry["acknowledged"] is False

        # Acknowledge the alert and verify persistence
        ack_url = f"/api/v1/app/tracking/alerts/{alert_entry['alert_id']}/acknowledge"
        r_ack = await client.post(ack_url, json={"acknowledged_by": "tester"}, headers=default_headers)
        assert r_ack.status_code == 200
        ack_body = r_ack.json()
        ack_payload = ack_body["data"]["data"]
        assert ack_payload["acknowledged"] is True
        assert ack_payload["acknowledged_by"] == "tester"

        # Alerts endpoint should now reflect the acknowledged state
        r_alerts_refresh = await client.get(
            "/api/v1/app/tracking/alerts",
            headers=default_headers,
        )
        assert r_alerts_refresh.status_code == 200
        refreshed_payload = r_alerts_refresh.json()["data"]["data"]
        assert refreshed_payload["count"] == 1
        refreshed_alert = refreshed_payload["alerts"][0]
        assert refreshed_alert["submission_id"] == rejected_submission_id
        assert refreshed_alert["acknowledged"] is True

    async for db in get_async_session():
        db: AsyncSession
        refreshed_submission = await get_submission_by_id(
            db,
            submission_id=rejected_submission_id,
            organization_id=org.id,
        )
        assert refreshed_submission is not None
        tracking_alerts = (refreshed_submission.error_details or {}).get("tracking_alerts", {})
        assert tracking_alerts.get("submission_rejected", {}).get("acknowledged") is True
        break
