"""
Integration tests for SI business systems endpoints with tenant isolation.
Currently validates ERP connections list with pagination and isolation.
"""
import os
import sys
import uuid
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

CURRENT_DIR = os.path.dirname(__file__)
BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "..", "backend"))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from api_gateway.api_versions.v1.si_endpoints.organization_endpoints import OrganizationEndpointsV1
from api_gateway.role_routing.models import HTTPRoutingContext
from core_platform.data_management.db_async import init_async_engine
from core_platform.data_management.models.base import Base
from core_platform.data_management.models.organization import Organization
from core_platform.data_management.models.business_systems import (
    ERPConnection, ERPProvider, SyncStatus
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
async def test_si_business_systems_erp_pagination_and_isolation(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///:memory:")
    engine = init_async_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    org1 = Organization(id=uuid.uuid4(), name="Org 1")
    org2 = Organization(id=uuid.uuid4(), name="Org 2")

    async for db in get_async_session():
        db: AsyncSession
        db.add_all([org1, org2])
        await db.flush()
        # ERP connections for org1
        for i in range(3):
            db.add(ERPConnection(
                organization_id=org1.id,
                si_id=uuid.uuid4(),
                provider=ERPProvider.ODOO,
                system_name=f"Odoo-{i}",
                status=SyncStatus.COMPLETED,
            ))
        # ERP connection for org2 (should not appear)
        db.add(ERPConnection(
            organization_id=org2.id,
            si_id=uuid.uuid4(),
            provider=ERPProvider.SAP,
            system_name="SAP-01",
            status=SyncStatus.PENDING,
        ))
        await db.commit()
        break

    app = FastAPI()
    endpoints = OrganizationEndpointsV1(StubRoleDetector(), StubPermissionGuard(), message_router=None)
    app.include_router(endpoints.router, prefix="/api/v1/si")
    client = TestClient(app)

    # Full list (erp default) for org1
    r1 = client.get(f"/api/v1/si/organizations/{org1.id}/business-systems")
    assert r1.status_code == 200
    body1 = r1.json()
    assert body1["success"] is True
    assert body1["data"]["count"] == 3
    assert all(item["system_name"].startswith("Odoo-") for item in body1["data"]["items"])

    # Paged list (limit=2, offset=1)
    r2 = client.get(f"/api/v1/si/organizations/{org1.id}/business-systems?limit=2&offset=1")
    assert r2.status_code == 200
    body2 = r2.json()
    assert body2["success"] is True
    assert len(body2["data"]["items"]) == 2

    # Ensure isolation: listing org2 yields only its own
    r3 = client.get(f"/api/v1/si/organizations/{org2.id}/business-systems")
    assert r3.status_code == 200
    body3 = r3.json()
    assert body3["data"]["count"] == 1
    assert body3["data"]["items"][0]["system_name"] == "SAP-01"

