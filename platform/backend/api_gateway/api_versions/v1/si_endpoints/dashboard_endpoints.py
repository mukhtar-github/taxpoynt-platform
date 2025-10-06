"""
SI Dashboard Endpoints - API v1
================================
Aggregated metrics for System Integrator dashboards. Provides summarized
integration, financial, and transmission data so the frontend can replace
demo placeholders with live values.
"""

import logging
import uuid
from datetime import datetime
from typing import Any, Dict, Iterable, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from core_platform.authentication.role_manager import PlatformRole
from core_platform.data_management.db_async import get_async_session
from core_platform.data_management.models.firs_submission import (
    FIRSSubmission,
    SubmissionStatus,
)
from core_platform.data_management.models.integration import (
    Integration,
    IntegrationStatus,
    IntegrationType,
)
from core_platform.data_management.models.organization import Organization
from core_platform.data_management.repositories.validation_batch_repo_async import (
    summarize_validation_batches,
)
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.utils.error_mapping import v1_error_response
from api_gateway.utils.v1_response import build_v1_response
from ..version_models import V1ResponseModel

logger = logging.getLogger(__name__)


ERP_TYPES = {
    IntegrationType.ODOO,
    IntegrationType.SAP,
    IntegrationType.QUICKBOOKS,
    IntegrationType.XERO,
    IntegrationType.ORACLE_ERP,
    IntegrationType.MICROSOFT_DYNAMICS,
}

CRM_TYPES = {
    IntegrationType.SALESFORCE,
    IntegrationType.HUBSPOT,
    IntegrationType.ZOHO_CRM,
    IntegrationType.MICROSOFT_CRM,
}

POS_TYPES = {
    IntegrationType.SQUARE,
    IntegrationType.SHOPIFY,
    IntegrationType.CLOVER,
}

ECOMMERCE_TYPES = {
    IntegrationType.SHOPIFY,
}

BANKING_TYPES = {
    IntegrationType.MONO,
    IntegrationType.OKRA,
    IntegrationType.PLAID,
}

PAYMENT_TYPES = {
    IntegrationType.PAYSTACK,
    IntegrationType.FLUTTERWAVE,
    IntegrationType.MONIEPOINT,
    IntegrationType.INTERSWITCH,
}


class SIDashboardEndpointsV1:
    """Dashboard endpoints for System Integrator role."""

    ACTION_NAME = "si_dashboard_metrics_retrieved"

    def __init__(
        self,
        role_detector: HTTPRoleDetector,
        permission_guard: APIPermissionGuard,
    ) -> None:
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.router = APIRouter(
            prefix="/dashboard",
            tags=["SI Dashboard V1"],
            dependencies=[Depends(self._require_si_role)],
        )

        self._setup_routes()
        logger.info("SI Dashboard Endpoints V1 initialized")

    async def _require_si_role(self, request: Request) -> HTTPRoutingContext:
        context = await self.role_detector.detect_role_context(request)
        if not context or not context.has_role(PlatformRole.SYSTEM_INTEGRATOR):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="System Integrator role required for v1 API",
            )
        if not await self.permission_guard.check_endpoint_permission(
            context, f"v1/si{request.url.path}", request.method
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for SI v1 endpoint",
            )
        context.metadata["api_version"] = "v1"
        context.metadata["endpoint_group"] = "si"
        return context

    def _setup_routes(self) -> None:
        self.router.add_api_route(
            "/metrics",
            self.get_dashboard_metrics,
            methods=["GET"],
            summary="Get SI dashboard metrics",
            description="Provide aggregated metrics for the System Integrator dashboard",
            response_model=V1ResponseModel,
        )

    async def get_dashboard_metrics(self, request: Request) -> V1ResponseModel:
        try:
            context = await self._require_si_role(request)
            async for session in get_async_session():
                metrics = await self._build_metrics_snapshot(
                    session,
                    getattr(context, "organization_id", None),
                )
                return self._create_v1_response(metrics, self.ACTION_NAME)
            raise RuntimeError("Database session unavailable")
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Error generating SI dashboard metrics: %s", exc, exc_info=True)
            return v1_error_response(exc, action=self.ACTION_NAME)

    async def _build_metrics_snapshot(
        self,
        session: AsyncSession,
        organization_id: Optional[str],
    ) -> Dict[str, Any]:
        org_uuid: Optional[uuid.UUID] = None
        if organization_id:
            try:
                org_uuid = uuid.UUID(str(organization_id))
            except Exception:
                org_uuid = None

        integration_counts_stmt = (
            select(
                Integration.integration_type,
                Integration.status,
                func.count().label("count"),
            )
            .group_by(Integration.integration_type, Integration.status)
        )
        if org_uuid:
            integration_counts_stmt = integration_counts_stmt.where(
                Integration.organization_id == org_uuid
            )
        integration_counts = await session.execute(integration_counts_stmt)

        integration_rows_stmt = (
            select(Integration)
            .order_by(Integration.last_sync_at.desc().nullslast())
            .limit(25)
        )
        if org_uuid:
            integration_rows_stmt = integration_rows_stmt.where(
                Integration.organization_id == org_uuid
            )
        integration_rows = await session.execute(integration_rows_stmt)

        integration_stats = self._summarize_integrations(
            integration_counts.fetchall(), integration_rows.scalars()
        )

        submission_counts_stmt = (
            select(FIRSSubmission.status, func.count().label("count"))
            .group_by(FIRSSubmission.status)
        )
        if org_uuid:
            submission_counts_stmt = submission_counts_stmt.where(
                FIRSSubmission.organization_id == org_uuid
            )
        submission_counts = await session.execute(submission_counts_stmt)
        submission_stats = self._summarize_submissions(submission_counts.fetchall())

        validation_payload = None
        if org_uuid:
            snapshot = await summarize_validation_batches(
                session,
                organization_id=org_uuid,
                limit=5,
            )
            if isinstance(snapshot, dict):
                raw_items = snapshot.get("items", [])
                recent_batches = [
                    {
                        "batchId": item.get("batchId"),
                        "status": item.get("status"),
                        "totals": item.get("totals"),
                        "createdAt": item.get("createdAt"),
                    }
                    for item in raw_items
                ]
                sla_hours = 4
                org = await session.get(Organization, org_uuid)
                if org and isinstance(org.firs_configuration, dict):
                    configured = org.firs_configuration.get("compliance_sla_hours")
                    try:
                        if configured is not None:
                            sla_hours = max(1, int(configured))
                    except (TypeError, ValueError):
                        logger.debug(
                            "Invalid compliance_sla_hours configuration for org %s", org_uuid
                        )

                validation_payload = {
                    "summary": snapshot.get("summary"),
                    "recentBatches": recent_batches,
                    "slaHours": sla_hours,
                }

        metrics: Dict[str, Any] = {
            "integrations": integration_stats["categories"],
            "financial": integration_stats["financial"],
            "transactions": submission_stats["transactions"],
            "reconciliation": submission_stats["reconciliation"],
            "compliance": submission_stats["compliance"],
            "lastUpdated": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        }

        if validation_payload:
            metrics["validation"] = validation_payload

        return metrics

    def _summarize_integrations(
        self,
        counts: Iterable[Tuple[IntegrationType, IntegrationStatus, int]],
        rows: Iterable[Integration],
    ) -> Dict[str, Any]:
        categories = {
            "erp": {"total": 0, "active": 0, "systems": []},
            "crm": {"total": 0, "active": 0, "systems": []},
            "pos": {"total": 0, "active": 0, "systems": []},
            "ecommerce": {"total": 0, "active": 0, "systems": []},
            "overall": {
                "totalSystems": 0,
                "activeSystems": 0,
                "overallHealthScore": 100.0,
            },
        }

        financial = {
            "banking": {"connected": 0, "providers": []},
            "payments": {"connected": 0, "providers": []},
        }

        for integration_type, status, count in counts:
            mapped = self._map_integration_type(integration_type)
            if not mapped:
                continue

            categories[mapped]["total"] += count
            categories["overall"]["totalSystems"] += count

            if status == IntegrationStatus.ACTIVE:
                categories[mapped]["active"] += count
                categories["overall"]["activeSystems"] += count

            if integration_type in BANKING_TYPES:
                financial["banking"]["connected"] += count if status == IntegrationStatus.ACTIVE else 0
            if integration_type in PAYMENT_TYPES:
                financial["payments"]["connected"] += count if status == IntegrationStatus.ACTIVE else 0

        provider_tracker = {
            "banking": set(),
            "payments": set(),
        }

        for integration in rows:
            mapped = self._map_integration_type(integration.integration_type)
            if not mapped:
                continue

            system_snapshot = {
                "name": integration.name,
                "status": integration.status.value,
                "lastSync": self._format_datetime(integration.last_sync_at),
            }
            categories[mapped]["systems"].append(system_snapshot)

            if integration.integration_type in BANKING_TYPES:
                provider_tracker["banking"].add(integration.name)
            if integration.integration_type in PAYMENT_TYPES:
                provider_tracker["payments"].add(integration.name)

        financial["banking"]["providers"] = sorted(provider_tracker["banking"])
        financial["payments"]["providers"] = sorted(provider_tracker["payments"])

        categories["overall"]["overallHealthScore"] = self._calculate_health_score(
            categories["overall"]["activeSystems"],
            categories["overall"]["totalSystems"],
        )

        return {"categories": categories, "financial": financial}

    def _summarize_submissions(
        self, counts: Iterable[Tuple[SubmissionStatus, int]]
    ) -> Dict[str, Any]:
        totals: Dict[SubmissionStatus, int] = {status: 0 for status in SubmissionStatus}
        for status, count in counts:
            totals[status] = count

        total = sum(totals.values())
        success = sum(
            totals[status]
            for status in (SubmissionStatus.SUBMITTED, SubmissionStatus.ACCEPTED)
        )
        pending = sum(
            totals[status]
            for status in (SubmissionStatus.PENDING, SubmissionStatus.PROCESSING)
        )
        failed = sum(
            totals[status]
            for status in (SubmissionStatus.REJECTED, SubmissionStatus.FAILED)
        )

        success_rate = 0.0
        if total:
            success_rate = round((success / total) * 100, 1)

        transactions = {
            "totalInvoices": total,
            "autoSubmitted": success,
            "manualReview": failed,
            "queue": pending,
            "successRate": success_rate,
        }

        reconciliation = {
            "autoReconciled": success,
            "pending": pending,
            "exceptions": failed,
            "successRate": success_rate,
        }

        compliance = {
            "complianceScore": success_rate,
            "invoicesGenerated": total,
            "pendingSubmissions": pending,
            "auditsPassed": success,
        }

        return {
            "transactions": transactions,
            "reconciliation": reconciliation,
            "compliance": compliance,
        }

    @staticmethod
    def _map_integration_type(
        integration_type: IntegrationType,
    ) -> Optional[str]:
        if integration_type in ERP_TYPES:
            return "erp"
        if integration_type in CRM_TYPES:
            return "crm"
        if integration_type in POS_TYPES:
            return "pos"
        if integration_type in ECOMMERCE_TYPES:
            return "ecommerce"
        return None

    @staticmethod
    def _format_datetime(value: Optional[datetime]) -> Optional[str]:
        if not value:
            return None
        return value.replace(microsecond=0).isoformat() + "Z"

    @staticmethod
    def _calculate_health_score(active: int, total: int) -> float:
        if total <= 0:
            return 100.0
        return round((active / total) * 100, 1)

    def _create_v1_response(self, data: Dict[str, Any], action: str) -> V1ResponseModel:
        return build_v1_response(self._make_json_safe(data), action)

    def _make_json_safe(self, value: Any) -> Any:
        if isinstance(value, datetime):
            return value.replace(microsecond=0).isoformat() + "Z"
        if isinstance(value, list):
            return [self._make_json_safe(item) for item in value]
        if isinstance(value, dict):
            return {key: self._make_json_safe(val) for key, val in value.items()}
        return value


def create_si_dashboard_router(
    role_detector: HTTPRoleDetector,
    permission_guard: APIPermissionGuard,
) -> APIRouter:
    endpoints = SIDashboardEndpointsV1(role_detector, permission_guard)
    return endpoints.router
