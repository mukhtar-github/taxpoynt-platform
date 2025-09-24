import uuid
from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from core_platform.data_management.models.base import Base
from core_platform.data_management.models.business_systems import Taxpayer, TaxpayerStatus
from core_platform.data_management.grant_tracking_repository import GrantTrackingRepository


@pytest.fixture(autouse=True)
def patch_run_executor(monkeypatch):
    """Execute repository operations synchronously for deterministic testing."""

    async def _run_immediate(self, func, *, commit: bool, **kwargs):
        return self._sync_call(func, commit=commit, kwargs=kwargs)

    monkeypatch.setattr(GrantTrackingRepository, "_run", _run_immediate)


@pytest.fixture
def grant_repo():
    """Provide an in-memory repository wired to a temporary SQLite database."""

    engine = create_engine(
        "sqlite:///:memory:",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine, future=True, expire_on_commit=False)

    class _DBLayer:
        def get_session(self):
            return SessionLocal()

    repo = GrantTrackingRepository(db_layer=_DBLayer())

    try:
        yield repo, SessionLocal
    finally:
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.mark.asyncio
async def test_register_taxpayer_updates_metadata(grant_repo):
    repo, SessionLocal = grant_repo
    organization_id = uuid.uuid4()

    with SessionLocal() as session:
        taxpayer = Taxpayer(
            organization_id=organization_id,
            tin="TIN-001",
            business_name="Test Company",
            registration_status=TaxpayerStatus.PENDING_REGISTRATION,
        )
        session.add(taxpayer)
        session.commit()
        taxpayer_id = taxpayer.id

    result = await repo.register_taxpayer(
        tenant_id=organization_id,
        organization_id=organization_id,
        taxpayer_tin="TIN-001",
        taxpayer_name="Test Company",
        taxpayer_size="large",
        sector="finance",
    )

    assert result["status"] == "success"

    with SessionLocal() as session:
        row = session.get(Taxpayer, taxpayer_id)
        grant_meta = (row.taxpayer_metadata or {}).get("grant_tracking", {})
        assert grant_meta.get("size") == "large"
        assert grant_meta.get("sector") == "finance"
        assert grant_meta.get("is_active") is True


@pytest.mark.asyncio
async def test_grant_summary_reflects_taxpayer_counts(grant_repo):
    repo, SessionLocal = grant_repo
    organization_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    with SessionLocal() as session:
        for idx in range(3):
            metadata = {
                "grant_tracking": {
                    "size": "large" if idx < 2 else "sme",
                    "sector": "finance" if idx < 2 else "retail",
                    "is_active": True,
                    "registered_at": now.isoformat(),
                    "last_transmission": (now - timedelta(days=idx)).isoformat(),
                    "transmission_count": 5,
                    "compliance_state": "compliant" if idx < 2 else "pending",
                }
            }
            session.add(
                Taxpayer(
                    organization_id=organization_id,
                    tin=f"TIN-{idx}",
                    business_name=f"Company {idx}",
                    registration_status=TaxpayerStatus.ACTIVE,
                    registration_date=now - timedelta(days=idx),
                    taxpayer_metadata=metadata,
                )
            )
        session.commit()

    summary = await repo.get_grant_summary(organization_id)

    assert summary["total_taxpayers"] == 3
    milestone_1 = summary["milestones"].get("milestone_1")
    assert milestone_1 is not None
    assert milestone_1["current_taxpayer_count"] == 3
    assert len(summary["sector_breakdown"]) >= 1


@pytest.mark.asyncio
async def test_update_taxpayer_compliance_status(grant_repo):
    repo, SessionLocal = grant_repo
    organization_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    with SessionLocal() as session:
        taxpayer = Taxpayer(
            organization_id=organization_id,
            tin="TIN-COMP",
            business_name="Compliance Test",
            registration_status=TaxpayerStatus.ACTIVE,
            registration_date=now,
            taxpayer_metadata={
                "grant_tracking": {
                    "size": "sme",
                    "sector": "services",
                    "is_active": True,
                    "registered_at": now.isoformat(),
                    "compliance_state": "pending",
                }
            },
        )
        session.add(taxpayer)
        session.commit()
        taxpayer_id = taxpayer.id

    result = await repo.update_taxpayer_compliance_status(taxpayer_id, "compliant")
    assert result["compliance_state"] == "compliant"

    with SessionLocal() as session:
        row = session.get(Taxpayer, taxpayer_id)
        grant_meta = (row.taxpayer_metadata or {}).get("grant_tracking", {})
        assert grant_meta.get("compliance_state") == "compliant"
        assert "compliance_updated_at" in grant_meta
