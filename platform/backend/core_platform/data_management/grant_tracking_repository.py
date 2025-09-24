"""
Grant Tracking Repository for FIRS Milestone Management.
=======================================================

Provides grant/milestone analytics derived from taxpayer onboarding data.
The implementation operates on the synchronous SQLAlchemy session exposed by
``database_init.DatabaseInitializer`` and returns asynchronous-friendly
interfaces for the rest of the application.
"""

from __future__ import annotations

import asyncio
import logging
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid4

from sqlalchemy.orm import Session

from .models.business_systems import Taxpayer, TaxpayerStatus

logger = logging.getLogger(__name__)


class MilestoneType(Enum):
    """FIRS milestone types."""

    MILESTONE_1 = "milestone_1"  # 20 taxpayers, 80% active
    MILESTONE_2 = "milestone_2"  # 40 taxpayers, Large + SME
    MILESTONE_3 = "milestone_3"  # 60 taxpayers, cross-sector
    MILESTONE_4 = "milestone_4"  # 80 taxpayers, sustained compliance
    MILESTONE_5 = "milestone_5"  # 100 taxpayers, full validation


class TaxpayerSize(Enum):
    """Taxpayer size classification."""

    LARGE = "large"  # Large taxpayers
    SME = "sme"  # Small and Medium Enterprises


@dataclass
class MilestoneDefinition:
    """FIRS milestone definition with requirements."""

    milestone_type: MilestoneType
    taxpayer_threshold: int
    requirements: Dict[str, Any]
    grant_amount: float
    description: str


@dataclass
class MilestoneProgress:
    """Milestone progress tracking."""

    id: UUID
    tenant_id: UUID
    organization_id: UUID
    milestone_type: MilestoneType
    target_date: datetime
    current_taxpayer_count: int
    required_taxpayer_count: int
    large_taxpayer_count: int
    sme_taxpayer_count: int
    sector_count: int
    required_sectors: int
    transmission_rate: float
    required_transmission_rate: float
    compliance_sustained: bool
    validation_completed: bool
    achievement_date: Optional[datetime] = None
    grant_claimed: bool = False
    grant_amount: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime = datetime.now(timezone.utc)
    updated_at: datetime = datetime.now(timezone.utc)


class GrantTrackingRepository:
    """Repository that derives grant/milestone analytics from taxpayer data."""

    # FIRS milestone definitions
    MILESTONE_DEFINITIONS: Dict[MilestoneType, MilestoneDefinition] = {
        MilestoneType.MILESTONE_1: MilestoneDefinition(
            milestone_type=MilestoneType.MILESTONE_1,
            taxpayer_threshold=20,
            requirements={
                "transmission_rate": 80.0,
                "active_taxpayers": True,
                "timeframe_months": 6,
            },
            grant_amount=50_000.0,
            description="20 taxpayers with 80% transmission rate",
        ),
        MilestoneType.MILESTONE_2: MilestoneDefinition(
            milestone_type=MilestoneType.MILESTONE_2,
            taxpayer_threshold=40,
            requirements={
                "large_taxpayers": True,
                "sme_taxpayers": True,
                "transmission_rate": 80.0,
            },
            grant_amount=100_000.0,
            description="40 taxpayers with Large + SME representation",
        ),
        MilestoneType.MILESTONE_3: MilestoneDefinition(
            milestone_type=MilestoneType.MILESTONE_3,
            taxpayer_threshold=60,
            requirements={
                "cross_sector": True,
                "min_sectors": 2,
                "transmission_rate": 80.0,
            },
            grant_amount=200_000.0,
            description="60 taxpayers with cross-sector representation",
        ),
        MilestoneType.MILESTONE_4: MilestoneDefinition(
            milestone_type=MilestoneType.MILESTONE_4,
            taxpayer_threshold=80,
            requirements={
                "sustained_compliance": True,
                "compliance_period_months": 6,
                "transmission_rate": 80.0,
            },
            grant_amount=400_000.0,
            description="80 taxpayers with sustained compliance",
        ),
        MilestoneType.MILESTONE_5: MilestoneDefinition(
            milestone_type=MilestoneType.MILESTONE_5,
            taxpayer_threshold=100,
            requirements={
                "full_validation": True,
                "transmission_rate": 80.0,
                "all_previous_milestones": True,
            },
            grant_amount=800_000.0,
            description="100 taxpayers with full validation",
        ),
    }

    def __init__(self, db_layer: Optional[Any] = None, cache_manager: Optional[Any] = None):
        from .database_init import get_database  # Local import to avoid cycles

        if db_layer is None:
            db_layer = get_database()

        if db_layer is None or not hasattr(db_layer, "get_session"):
            raise RuntimeError("GrantTrackingRepository requires a database layer with get_session().")

        self.db_layer = db_layer
        self.cache_manager = cache_manager

    # ------------------------------------------------------------------
    # Public API (asynchronous wrappers around synchronous DB operations)
    # ------------------------------------------------------------------

    async def register_taxpayer(
        self,
        tenant_id: str | UUID,
        organization_id: str | UUID,
        taxpayer_tin: str,
        taxpayer_name: str,
        taxpayer_size: str | TaxpayerSize,
        sector: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Register/update taxpayer grant metadata."""

        return await self._run(
            self._register_taxpayer_sync,
            commit=True,
            tenant_id=tenant_id,
            organization_id=organization_id,
            taxpayer_tin=taxpayer_tin,
            taxpayer_name=taxpayer_name,
            taxpayer_size=taxpayer_size,
            sector=sector,
        )

    async def update_taxpayer_profile(
        self,
        taxpayer_id: str | UUID,
        updates: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Update grant-related taxpayer metadata."""

        return await self._run(
            self._update_taxpayer_profile_sync,
            commit=True,
            taxpayer_id=taxpayer_id,
            updates=updates,
        )

    async def deactivate_taxpayer(self, taxpayer_id: str | UUID) -> bool:
        """Mark taxpayer as inactive for grant calculations."""

        return await self._run(
            self._deactivate_taxpayer_sync,
            commit=True,
            taxpayer_id=taxpayer_id,
        )

    async def update_taxpayer_compliance_status(
        self,
        taxpayer_id: str | UUID,
        compliance_state: str,
    ) -> Optional[Dict[str, Any]]:
        """Persist compliance status for grant analytics."""

        return await self._run(
            self._update_compliance_state_sync,
            commit=True,
            taxpayer_id=taxpayer_id,
            compliance_state=compliance_state,
        )

    async def get_taxpayer_onboarding_status(
        self,
        tenant_id: str | UUID,
        taxpayer_id: str | UUID,
    ) -> Optional[Dict[str, Any]]:
        """Return onboarding/grant status for a specific taxpayer."""

        return await self._run(
            self._get_taxpayer_onboarding_status_sync,
            commit=False,
            tenant_id=tenant_id,
            taxpayer_id=taxpayer_id,
        )

    async def get_grant_summary(self, tenant_id: str | UUID) -> Dict[str, Any]:
        """Return grant overview and milestone summary for tenant."""

        stats = await self._collect_stats_async(tenant_id)
        progress = self._build_milestone_progress(stats)
        summary = self._build_grant_summary(stats, progress)
        return summary

    async def get_milestone_progress(self, tenant_id: str | UUID) -> Dict[str, Any]:
        """Return per-milestone progress for tenant."""

        stats = await self._collect_stats_async(tenant_id)
        return self._build_milestone_progress(stats)

    async def get_milestone_details(
        self,
        tenant_id: str | UUID,
        milestone: str,
    ) -> Optional[Dict[str, Any]]:
        """Return details for a single milestone."""

        progress = await self.get_milestone_progress(tenant_id)
        return progress.get(milestone)

    async def get_taxpayer_analytics(self, tenant_id: str | UUID) -> Dict[str, Any]:
        """Return analytics used by dashboards (sector mix, trends, etc)."""

        stats = await self._collect_stats_async(tenant_id)
        progress = self._build_milestone_progress(stats)
        summary = self._build_grant_summary(stats, progress)
        analytics = {
            "tenant_id": str(stats["tenant_id"]),
            "generated_at": stats["generated_at"].isoformat(),
            "total_taxpayers": stats["totals"]["total_taxpayers"],
            "active_taxpayers": stats["totals"]["active_taxpayers"],
            "large_taxpayers": stats["totals"]["large_taxpayers"],
            "sme_taxpayers": stats["totals"]["sme_taxpayers"],
            "transmission_rate": stats["totals"]["transmission_rate"],
            "compliance_rate": stats["totals"]["compliance_rate"],
            "sector_breakdown": [
                {"sector": sector, "count": count}
                for sector, count in sorted(stats["sector_counts"].items())
            ],
            "onboarding_status": stats["onboarding_status_counts"],
            "monthly_trends": stats["monthly_trends"],
            "non_compliant_count": len(stats["non_compliant_taxpayers"]),
            "milestones": summary["milestones"],
        }
        return analytics

    async def get_performance_metrics(self, tenant_id: str | UUID) -> Dict[str, Any]:
        """Return compact performance metrics for dashboards."""

        stats = await self._collect_stats_async(tenant_id)
        progress = self._build_milestone_progress(stats)
        summary = self._build_grant_summary(stats, progress)
        metrics = {
            "tenant_id": str(stats["tenant_id"]),
            "generated_at": stats["generated_at"].isoformat(),
            "total_taxpayers": stats["totals"]["total_taxpayers"],
            "progress_percentage": summary["progress_percentage"],
            "transmission_rate": stats["totals"]["transmission_rate"],
            "compliance_rate": stats["totals"]["compliance_rate"],
            "achieved_grants": summary["achieved_grants"],
            "pending_grants": summary["pending_grants"],
            "next_milestone": summary["next_milestone"],
        }
        return metrics

    async def get_performance_trends(self, tenant_id: str | UUID) -> List[Dict[str, Any]]:
        """Return onboarding trends over time."""

        stats = await self._collect_stats_async(tenant_id)
        return stats["monthly_trends"]

    async def list_non_compliant_taxpayers(self, tenant_id: str | UUID) -> List[Dict[str, Any]]:
        """Return taxpayers currently flagged as non-compliant."""

        stats = await self._collect_stats_async(tenant_id)
        return stats["non_compliant_taxpayers"]

    async def get_upcoming_milestones(self, tenant_id: str | UUID) -> List[Dict[str, Any]]:
        """Return milestones that are still pending."""

        stats = await self._collect_stats_async(tenant_id)
        progress = self._build_milestone_progress(stats)
        upcoming = []
        for milestone, data in progress.items():
            if not data.get("achievement_date"):
                upcoming.append(
                    {
                        "milestone": milestone,
                        "requirements": self._milestone_requirements(milestone),
                        "current_taxpayer_count": data["current_taxpayer_count"],
                        "required_taxpayer_count": data["required_taxpayer_count"],
                    }
                )
        return upcoming

    async def get_current_grant_status(self, tenant_id: str | UUID) -> Dict[str, Any]:
        """Return a concise grant status summary."""

        summary = await self.get_grant_summary(tenant_id)
        return {
            "tenant_id": summary["tenant_id"],
            "generated_at": summary["generated_at"],
            "next_milestone": summary["next_milestone"],
            "progress_percentage": summary["progress_percentage"],
            "achieved_grants": summary["achieved_grants"],
            "pending_grants": summary["pending_grants"],
        }

    async def generate_grant_report(self, tenant_id: str | UUID) -> Dict[str, Any]:
        """Generate a consolidated grant tracking report."""

        stats = await self._collect_stats_async(tenant_id)
        progress = self._build_milestone_progress(stats)
        summary = self._build_grant_summary(stats, progress)
        analytics = await self.get_taxpayer_analytics(tenant_id)

        report_id = f"grant-report-{int(datetime.now(timezone.utc).timestamp())}"
        report = {
            "report_id": report_id,
            "tenant_id": summary["tenant_id"],
            "generated_at": summary["generated_at"],
            "summary": summary,
            "milestones": progress,
            "analytics": analytics,
        }
        return report

    async def list_grant_reports(self, tenant_id: str | UUID) -> List[Dict[str, Any]]:
        """Return available grant reports (currently only live snapshot)."""

        summary = await self.get_grant_summary(tenant_id)
        return [
            {
                "report_id": "grant-report-current",
                "tenant_id": summary["tenant_id"],
                "generated_at": summary["generated_at"],
                "next_milestone": summary["next_milestone"],
                "progress_percentage": summary["progress_percentage"],
            }
        ]

    async def get_grant_report(self, tenant_id: str | UUID, report_id: str) -> Dict[str, Any]:
        """Retrieve a grant report by id."""

        if report_id == "grant-report-current":
            progress = await self.get_milestone_progress(tenant_id)
            summary = await self.get_grant_summary(tenant_id)
            analytics = await self.get_taxpayer_analytics(tenant_id)
            return {
                "report_id": report_id,
                "tenant_id": summary["tenant_id"],
                "generated_at": summary["generated_at"],
                "summary": summary,
                "milestones": progress,
                "analytics": analytics,
            }
        # Fallback: regenerate a fresh report
        return await self.generate_grant_report(tenant_id)

    async def get_taxpayer_statistics(
        self,
        tenant_id: str | UUID,
        period: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Return taxpayer statistics for dashboards (period placeholder for API compatibility)."""

        stats = await self._collect_stats_async(tenant_id)
        return {
            "tenant_id": str(stats["tenant_id"]),
            "generated_at": stats["generated_at"].isoformat(),
            "period": period or "30d",
            "total_taxpayers": stats["totals"]["total_taxpayers"],
            "active_taxpayers": stats["totals"]["active_taxpayers"],
            "large_taxpayers": stats["totals"]["large_taxpayers"],
            "sme_taxpayers": stats["totals"]["sme_taxpayers"],
            "transmission_rate": stats["totals"]["transmission_rate"],
            "compliance_rate": stats["totals"]["compliance_rate"],
            "sector_breakdown": [
                {"sector": sector, "count": count}
                for sector, count in sorted(stats["sector_counts"].items())
            ],
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _collect_stats_async(self, tenant_id: str | UUID) -> Dict[str, Any]:
        return await self._run(self._collect_stats_sync, commit=False, tenant_id=tenant_id)

    async def _run(self, func, *, commit: bool, **kwargs):
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,
            lambda: self._sync_call(func, commit=commit, kwargs=kwargs),
        )

    # The ``kwargs`` indirection keeps ``run_in_executor`` signatures simple.
    def _sync_call(self, func, *, commit: bool, kwargs: Dict[str, Any]):
        session = self._acquire_session()
        try:
            result = func(session, **kwargs)
            if commit:
                session.commit()
            return result
        except Exception as exc:  # pragma: no cover - safety fallback
            session.rollback()
            logger.error("Grant tracking repository call failed: %s", exc, exc_info=True)
            raise
        finally:
            session.close()

    def _acquire_session(self) -> Session:
        session = self.db_layer.get_session()
        if not isinstance(session, Session):
            raise RuntimeError("GrantTrackingRepository expects a synchronous SQLAlchemy Session")
        return session

    # -----------------------
    # Synchronous operations
    # -----------------------

    def _register_taxpayer_sync(
        self,
        session: Session,
        *,
        tenant_id: str | UUID,
        organization_id: str | UUID,
        taxpayer_tin: str,
        taxpayer_name: str,
        taxpayer_size: str | TaxpayerSize,
        sector: Optional[str] = None,
    ) -> Dict[str, Any]:
        tenant_uuid = self._to_uuid(tenant_id)
        size_value = (
            taxpayer_size.value
            if isinstance(taxpayer_size, TaxpayerSize)
            else str(taxpayer_size or TaxpayerSize.SME.value).lower()
        )

        taxpayer = (
            session.query(Taxpayer)
            .filter(Taxpayer.organization_id == tenant_uuid)
            .filter(Taxpayer.tin == taxpayer_tin)
            .first()
        )

        if not taxpayer:
            return {"status": "error", "message": "taxpayer_not_found"}

        metadata = dict(taxpayer.taxpayer_metadata or {})
        grant_meta = dict(metadata.get("grant_tracking") or {})

        grant_meta.update(
            {
                "size": size_value,
                "sector": sector or grant_meta.get("sector") or taxpayer.sector or "unspecified",
                "label": taxpayer_name,
                "is_active": True,
                "registered_at": grant_meta.get("registered_at")
                or datetime.now(timezone.utc).isoformat(),
                "transmission_count": grant_meta.get("transmission_count", 0),
                "compliance_state": grant_meta.get("compliance_state", "in_progress"),
            }
        )

        metadata["grant_tracking"] = grant_meta
        taxpayer.taxpayer_metadata = metadata

        logger.debug("Registered taxpayer %s for grant tracking", taxpayer_tin)

        return {"status": "success", "taxpayer_id": str(taxpayer.id)}

    def _update_taxpayer_profile_sync(
        self,
        session: Session,
        *,
        taxpayer_id: str | UUID,
        updates: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        taxpayer = (
            session.query(Taxpayer)
            .filter(Taxpayer.id == self._to_uuid(taxpayer_id))
            .first()
        )
        if not taxpayer:
            return None

        metadata = dict(taxpayer.taxpayer_metadata or {})
        grant_meta = dict(metadata.get("grant_tracking") or {})

        if "sector" in updates and updates["sector"]:
            grant_meta["sector"] = updates["sector"]
        if "taxpayer_size" in updates and updates["taxpayer_size"]:
            grant_meta["size"] = str(updates["taxpayer_size"]).lower()
        if "validation_completed" in updates:
            grant_meta["validation_completed"] = bool(updates["validation_completed"])
        if "onboarding_status" in updates:
            grant_meta["onboarding_status"] = updates["onboarding_status"]
        if "grant_tracking" in updates and isinstance(updates["grant_tracking"], dict):
            grant_meta.update(updates["grant_tracking"])

        metadata["grant_tracking"] = grant_meta
        taxpayer.taxpayer_metadata = metadata

        session.add(taxpayer)

        return {
            "taxpayer_id": str(taxpayer.id),
            "grant_tracking": grant_meta,
        }

    def _deactivate_taxpayer_sync(
        self,
        session: Session,
        *,
        taxpayer_id: str | UUID,
    ) -> bool:
        taxpayer = (
            session.query(Taxpayer)
            .filter(Taxpayer.id == self._to_uuid(taxpayer_id))
            .first()
        )
        if not taxpayer:
            return False

        metadata = dict(taxpayer.taxpayer_metadata or {})
        grant_meta = dict(metadata.get("grant_tracking") or {})
        grant_meta["is_active"] = False
        metadata["grant_tracking"] = grant_meta
        metadata["deleted"] = True
        taxpayer.taxpayer_metadata = metadata
        session.add(taxpayer)
        return True

    def _update_compliance_state_sync(
        self,
        session: Session,
        *,
        taxpayer_id: str | UUID,
        compliance_state: str,
    ) -> Optional[Dict[str, Any]]:
        taxpayer = (
            session.query(Taxpayer)
            .filter(Taxpayer.id == self._to_uuid(taxpayer_id))
            .first()
        )
        if not taxpayer:
            return None

        metadata = dict(taxpayer.taxpayer_metadata or {})
        grant_meta = dict(metadata.get("grant_tracking") or {})
        grant_meta["compliance_state"] = compliance_state
        grant_meta["compliance_updated_at"] = datetime.now(timezone.utc).isoformat()
        metadata["grant_tracking"] = grant_meta
        taxpayer.taxpayer_metadata = metadata
        session.add(taxpayer)
        return {
            "taxpayer_id": str(taxpayer.id),
            "compliance_state": compliance_state,
        }

    def _get_taxpayer_onboarding_status_sync(
        self,
        session: Session,
        *,
        tenant_id: str | UUID,
        taxpayer_id: str | UUID,
    ) -> Optional[Dict[str, Any]]:
        taxpayer = (
            session.query(Taxpayer)
            .filter(Taxpayer.organization_id == self._to_uuid(tenant_id))
            .filter(Taxpayer.id == self._to_uuid(taxpayer_id))
            .first()
        )
        if not taxpayer:
            return None

        metadata = dict(taxpayer.taxpayer_metadata or {})
        grant_meta = dict(metadata.get("grant_tracking") or {})
        status = grant_meta.get("onboarding_status")
        if not status:
            if taxpayer.registration_status == TaxpayerStatus.ACTIVE:
                status = "active"
            elif taxpayer.registration_status == TaxpayerStatus.PENDING_REGISTRATION:
                status = "in_progress"
            else:
                status = (taxpayer.registration_status.value if taxpayer.registration_status else "unknown")

        return {
            "taxpayer_id": str(taxpayer.id),
            "status": status,
            "metadata": grant_meta,
        }

    def _collect_stats_sync(
        self,
        session: Session,
        *,
        tenant_id: str | UUID,
    ) -> Dict[str, Any]:
        tenant_uuid = self._to_uuid(tenant_id)
        rows: List[Taxpayer] = (
            session.query(Taxpayer)
            .filter(Taxpayer.organization_id == tenant_uuid)
            .all()
        )

        now = datetime.now(timezone.utc)
        cutoff_active = now - timedelta(days=30)

        totals = {
            "total_taxpayers": 0,
            "active_taxpayers": 0,
            "large_taxpayers": 0,
            "sme_taxpayers": 0,
            "transmission_rate": 0.0,
            "compliance_rate": 0.0,
            "active_transmissions": 0,
            "sustained_compliance_count": 0,
            "validation_completed": 0,
            "compliant_taxpayers": 0,
        }

        sector_counts: Dict[str, int] = defaultdict(int)
        onboarding_status_counts: Dict[str, int] = defaultdict(int)
        monthly_trends_map: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"month": "", "onboarded": 0, "large": 0, "sme": 0})
        non_compliant_records: List[Dict[str, Any]] = []
        taxpayer_records: List[Dict[str, Any]] = []

        for row in rows:
            metadata = dict(row.taxpayer_metadata or {})
            grant_meta = dict(metadata.get("grant_tracking") or {})

            deleted = metadata.get("deleted", False)
            is_active = grant_meta.get("is_active", True) and not deleted
            registration_status = row.registration_status.value if row.registration_status else None

            if not deleted:
                totals["total_taxpayers"] += 1

            size = str(grant_meta.get("size") or TaxpayerSize.SME.value).lower()
            if size == TaxpayerSize.LARGE.value:
                totals["large_taxpayers"] += 1
            else:
                totals["sme_taxpayers"] += 1

            sector = grant_meta.get("sector") or row.sector or "unspecified"
            sector_counts[sector] += 1

            onboarding_status = grant_meta.get("onboarding_status")
            if not onboarding_status:
                if registration_status == TaxpayerStatus.ACTIVE.value:
                    onboarding_status = "active"
                elif registration_status == TaxpayerStatus.PENDING_REGISTRATION.value:
                    onboarding_status = "in_progress"
                else:
                    onboarding_status = registration_status or "unknown"
            onboarding_status_counts[onboarding_status] += 1

            last_transmission_raw = grant_meta.get("last_transmission")
            last_transmission = self._parse_datetime(last_transmission_raw)
            transmission_count = int(grant_meta.get("transmission_count", 0) or 0)

            if is_active:
                totals["active_taxpayers"] += 1
            if last_transmission and last_transmission >= cutoff_active:
                totals["active_transmissions"] += 1

            compliance_state = str(grant_meta.get("compliance_state", "unknown")).lower()
            if compliance_state in {"compliant", "sustained", "active"}:
                totals["compliant_taxpayers"] += 1
            else:
                non_compliant_records.append(
                    {
                        "id": str(row.id),
                        "tin": row.tin,
                        "business_name": row.business_name,
                        "sector": sector,
                        "compliance_state": compliance_state,
                        "registration_status": registration_status,
                        "last_transmission": last_transmission.isoformat() if last_transmission else None,
                    }
                )

            if compliance_state == "sustained":
                totals["sustained_compliance_count"] += 1

            if grant_meta.get("validation_completed"):
                totals["validation_completed"] += 1

            registration_date = row.registration_date or self._parse_datetime(grant_meta.get("registered_at"))
            if registration_date is None:
                registration_date = now

            month_key = registration_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0, tzinfo=timezone.utc if registration_date.tzinfo else None)
            month_label = month_key.isoformat()
            monthly_entry = monthly_trends_map[month_label]
            monthly_entry["month"] = month_label
            monthly_entry["onboarded"] += 1
            if size == TaxpayerSize.LARGE.value:
                monthly_entry["large"] += 1
            else:
                monthly_entry["sme"] += 1

            taxpayer_records.append(
                {
                    "id": str(row.id),
                    "tin": row.tin,
                    "business_name": row.business_name,
                    "sector": sector,
                    "size": size,
                    "is_active": is_active,
                    "registration_status": registration_status,
                    "registration_date": registration_date.isoformat() if registration_date else None,
                    "last_transmission": last_transmission.isoformat() if last_transmission else None,
                    "transmission_count": transmission_count,
                    "compliance_state": compliance_state,
                    "onboarding_status": onboarding_status,
                    "grant_metadata": grant_meta,
                }
            )

        totals["transmission_rate"] = (
            (totals["active_transmissions"] / totals["total_taxpayers"]) * 100
            if totals["total_taxpayers"]
            else 0.0
        )
        totals["compliance_rate"] = (
            (totals["compliant_taxpayers"] / totals["total_taxpayers"]) * 100
            if totals["total_taxpayers"]
            else 0.0
        )

        stats = {
            "tenant_id": tenant_uuid,
            "generated_at": datetime.now(timezone.utc),
            "totals": totals,
            "sector_counts": dict(sector_counts),
            "onboarding_status_counts": dict(onboarding_status_counts),
            "monthly_trends": sorted(monthly_trends_map.values(), key=lambda item: item["month"]),
            "non_compliant_taxpayers": non_compliant_records,
            "taxpayer_records": taxpayer_records,
        }
        return stats

    def _build_milestone_progress(self, stats: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        tenant_id: UUID = stats["tenant_id"]
        totals = stats["totals"]
        sector_count = len(stats["sector_counts"])
        transmission_rate = totals["transmission_rate"]
        sustained_compliance = (
            totals["sustained_compliance_count"] >= max(1, int(totals["total_taxpayers"] * 0.8))
        )
        validation_completed = totals["validation_completed"] >= max(1, totals["total_taxpayers"])

        progress: Dict[str, Dict[str, Any]] = {}
        now = datetime.now(timezone.utc)

        for milestone_type, definition in self.MILESTONE_DEFINITIONS.items():
            achieved = False
            if milestone_type == MilestoneType.MILESTONE_1:
                achieved = (
                    totals["total_taxpayers"] >= definition.taxpayer_threshold
                    and transmission_rate >= definition.requirements.get("transmission_rate", 80.0)
                )
            elif milestone_type == MilestoneType.MILESTONE_2:
                achieved = (
                    totals["total_taxpayers"] >= definition.taxpayer_threshold
                    and totals["large_taxpayers"] > 0
                    and totals["sme_taxpayers"] > 0
                )
            elif milestone_type == MilestoneType.MILESTONE_3:
                required_sectors = definition.requirements.get("min_sectors", 2)
                achieved = (
                    totals["total_taxpayers"] >= definition.taxpayer_threshold
                    and sector_count >= required_sectors
                )
            elif milestone_type == MilestoneType.MILESTONE_4:
                achieved = (
                    totals["total_taxpayers"] >= definition.taxpayer_threshold
                    and sustained_compliance
                )
            elif milestone_type == MilestoneType.MILESTONE_5:
                achieved = (
                    totals["total_taxpayers"] >= definition.taxpayer_threshold
                    and validation_completed
                )

            milestone_progress = MilestoneProgress(
                id=uuid4(),
                tenant_id=tenant_id,
                organization_id=tenant_id,
                milestone_type=milestone_type,
                target_date=now + timedelta(days=180),
                current_taxpayer_count=totals["total_taxpayers"],
                required_taxpayer_count=definition.taxpayer_threshold,
                large_taxpayer_count=totals["large_taxpayers"],
                sme_taxpayer_count=totals["sme_taxpayers"],
                sector_count=sector_count,
                required_sectors=definition.requirements.get("min_sectors", 1),
                transmission_rate=transmission_rate,
                required_transmission_rate=definition.requirements.get("transmission_rate", 80.0),
                compliance_sustained=sustained_compliance,
                validation_completed=validation_completed,
                achievement_date=now if achieved else None,
                grant_claimed=False,
                grant_amount=definition.grant_amount if achieved else None,
            )

            progress_dict = asdict(milestone_progress)
            for key in ("target_date", "achievement_date", "created_at", "updated_at"):
                if progress_dict.get(key):
                    progress_dict[key] = progress_dict[key].isoformat()

            progress[milestone_type.value] = progress_dict

        return progress

    def _build_grant_summary(
        self,
        stats: Dict[str, Any],
        progress: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        totals = stats["totals"]
        generated_at = stats["generated_at"].isoformat()

        achieved_count = sum(1 for item in progress.values() if item.get("achievement_date"))
        total_milestones = len(progress) or 1
        achieved_grants = sum(
            definition.grant_amount
            for milestone, definition in self.MILESTONE_DEFINITIONS.items()
            if progress.get(milestone.value, {}).get("achievement_date")
        )
        total_grants = sum(definition.grant_amount for definition in self.MILESTONE_DEFINITIONS.values())

        next_milestone = None
        for milestone in self.MILESTONE_DEFINITIONS.keys():
            if not progress.get(milestone.value, {}).get("achievement_date"):
                next_milestone = milestone.value
                break

        summary = {
            "tenant_id": str(stats["tenant_id"]),
            "generated_at": generated_at,
            "total_taxpayers": totals["total_taxpayers"],
            "active_taxpayers": totals["active_taxpayers"],
            "large_taxpayers": totals["large_taxpayers"],
            "sme_taxpayers": totals["sme_taxpayers"],
            "transmission_rate": totals["transmission_rate"],
            "compliance_rate": totals["compliance_rate"],
            "achieved_grants": achieved_grants,
            "pending_grants": max(total_grants - achieved_grants, 0.0),
            "progress_percentage": (achieved_count / total_milestones) * 100,
            "next_milestone": next_milestone,
            "milestones": progress,
            "sector_breakdown": [
                {"sector": sector, "count": count}
                for sector, count in sorted(stats["sector_counts"].items())
            ],
        }

        return summary

    def _milestone_requirements(self, milestone: str) -> Dict[str, Any]:
        try:
            milestone_enum = MilestoneType(milestone)
        except ValueError:
            return {}
        definition = self.MILESTONE_DEFINITIONS.get(milestone_enum)
        if not definition:
            return {}
        return {
            "taxpayer_threshold": definition.taxpayer_threshold,
            **definition.requirements,
        }

    # -----------------------
    # Utility helpers
    # -----------------------

    @staticmethod
    def _to_uuid(value: str | UUID) -> UUID:
        if isinstance(value, UUID):
            return value
        return UUID(str(value))

    @staticmethod
    def _parse_datetime(value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        try:
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            return None


__all__ = [
    "GrantTrackingRepository",
    "MilestoneType",
    "MilestoneDefinition",
    "MilestoneProgress",
    "TaxpayerSize",
]

