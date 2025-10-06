"""
Compliance Reporting Endpoints - API v1
=======================================
Serve compliance overview metrics and reporting helpers for Access Point
Providers. These endpoints back the dashboard UI with live data sourced
from the FIRS submissions repository.
"""

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from core_platform.authentication.role_manager import PlatformRole
from core_platform.data_management.db_async import get_async_session
from core_platform.data_management.models.organization import Organization
from core_platform.data_management.repositories.firs_submission_repo_async import (
    get_compliance_metrics_data,
)
from core_platform.messaging.message_router import ServiceRole, MessageRouter
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.utils.v1_response import build_v1_response
from api_gateway.utils.error_mapping import v1_error_response
from ..version_models import V1ResponseModel

logger = logging.getLogger(__name__)


class ComplianceReportingEndpointsV1:
    """Compliance reporting endpoints for APP role."""

    ACTION_METRICS = "app_compliance_metrics_retrieved"
    ACTION_REPORT = "app_compliance_report_queued"

    def __init__(
        self,
        role_detector: HTTPRoleDetector,
        permission_guard: APIPermissionGuard,
        message_router: MessageRouter,
    ) -> None:
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(
            prefix="/compliance",
            tags=["APP Compliance Reporting V1"],
            dependencies=[Depends(self._require_app_role)],
        )

        self._setup_routes()
        logger.info("Compliance Reporting Endpoints V1 initialized")

    async def _require_app_role(self, request: Request) -> HTTPRoutingContext:
        context = await self.role_detector.detect_role_context(request)
        if not context or not context.has_role(PlatformRole.ACCESS_POINT_PROVIDER):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access Point Provider role required for v1 API",
            )
        if not await self.permission_guard.check_endpoint_permission(
            context, f"v1/app{request.url.path}", request.method
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for APP v1 endpoint",
            )
        context.metadata["api_version"] = "v1"
        context.metadata["endpoint_group"] = "app"
        return context

    def _setup_routes(self) -> None:
        self.router.add_api_route(
            "/metrics",
            self.get_compliance_metrics,
            methods=["GET"],
            summary="Get compliance dashboard metrics",
            description="Return compliance overview metrics and recent report summaries",
            response_model=V1ResponseModel,
        )

        # Backwards compatible alias for dashboard POST
        self.router.add_api_route(
            "/generate-report",
            self.generate_compliance_report,
            methods=["POST"],
            summary="Generate compliance report",
            description="Trigger compliance report generation via reporting service",
            response_model=V1ResponseModel,
        )

    async def get_compliance_metrics(
        self,
        request: Request,
        db: AsyncSession = Depends(get_async_session),
        recent_limit: int = Query(5, description="Number of recent reports to include"),
    ) -> V1ResponseModel:
        try:
            context = await self._require_app_role(request)

            sla_hours = 4
            if context.organization_id:
                org = await db.get(Organization, context.organization_id)
                if org and isinstance(org.firs_configuration, dict):
                    configured = org.firs_configuration.get("compliance_sla_hours")
                    try:
                        if configured is not None:
                            sla_hours = max(1, int(configured))
                    except (ValueError, TypeError):
                        logger.debug("Invalid compliance_sla_hours configuration for org %s", context.organization_id)

            data = await get_compliance_metrics_data(
                db,
                organization_id=context.organization_id,
                recent_limit=recent_limit,
                overdue_hours=sla_hours,
            )

            metrics = data["metrics"]
            payload = {
                "totalReports": metrics.get("totalTransmissions", 0),
                "pendingReports": data.get("pendingReports", 0),
                "overdue": data.get("overdue", 0),
                "complianceScore": round(metrics.get("successRate", 0.0), 2),
                "lastAudit": data.get("lastAcceptedAt"),
                "nextDeadline": data.get("nextDeadline"),
                "reports": data.get("reports", []),
                "slaHours": sla_hours,
                "generatedAt": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
            }

            return build_v1_response(payload, self.ACTION_METRICS)
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Error retrieving compliance metrics: %s", exc, exc_info=True)
            return v1_error_response(exc, action=self.ACTION_METRICS)

    async def generate_compliance_report(self, request: Request) -> V1ResponseModel:
        """Proxy compliance report generation to reporting services."""

        try:
            context = await self._require_app_role(request)
            body = await request.json()

            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="generate_compliance_report",
                payload={
                    "report_config": body,
                    "app_id": context.user_id,
                    "api_version": "v1",
                },
            )

            return build_v1_response(result, self.ACTION_REPORT)
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("Error generating compliance report: %s", exc, exc_info=True)
            return v1_error_response(exc, action=self.ACTION_REPORT)


def create_compliance_reporting_router(
    role_detector: HTTPRoleDetector,
    permission_guard: APIPermissionGuard,
    message_router: MessageRouter,
) -> APIRouter:
    endpoints = ComplianceReportingEndpointsV1(role_detector, permission_guard, message_router)
    return endpoints.router
