"""
Dashboard Endpoints - API v1
============================
Hybrid dashboard endpoints for unified metrics and analytics.
Provides consolidated view of SI and APP operations.
"""
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from fastapi import APIRouter, Request

from core_platform.authentication.role_manager import PlatformRole
from core_platform.messaging.message_router import ServiceRole, MessageRouter
from core_platform.data_management.db_async import get_async_session
from core_platform.data_management.models.organization import Organization
from core_platform.data_management.repositories.validation_batch_repo_async import (
    summarize_validation_batches,
)
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from ..si_endpoints.version_models import V1ResponseModel
from api_gateway.utils.v1_response import build_v1_response

logger = logging.getLogger(__name__)


class DashboardEndpointsV1:
    """
    Dashboard Endpoints - Version 1
    ===============================
    Provides unified dashboard data for Hybrid users:
    
    **Dashboard Capabilities:**
    - **Unified Metrics**: Combined SI and APP performance data
    - **Cross-Role Analytics**: Insights spanning multiple roles
    - **Real-time Monitoring**: Live system status and performance
    - **Activity Feeds**: Unified activity timeline across roles
    - **Health Monitoring**: System health across all integrations
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/dashboard", tags=["Hybrid Dashboard V1"])
        
        self._setup_routes()
        logger.info("Dashboard Endpoints V1 initialized")
    
    def _setup_routes(self):
        """Setup dashboard routes"""
        
        # Unified Metrics
        self.router.add_api_route(
            "/unified-metrics",
            self.get_unified_metrics,
            methods=["GET"],
            summary="Get unified dashboard metrics",
            description="Get combined metrics from SI and APP operations",
            response_model=V1ResponseModel,
        )
        
        # Activity Timeline
        self.router.add_api_route(
            "/activity-timeline",
            self.get_activity_timeline,
            methods=["GET"],
            summary="Get unified activity timeline",
            description="Get recent activities across all roles and systems",
            response_model=V1ResponseModel,
        )
        
        # System Health Overview
        self.router.add_api_route(
            "/system-health",
            self.get_system_health,
            methods=["GET"],
            summary="Get system health overview",
            description="Get health status of all connected systems",
            response_model=V1ResponseModel,
        )
        
        # Cross-Role Performance
        self.router.add_api_route(
            "/cross-role-performance",
            self.get_cross_role_performance,
            methods=["GET"],
            summary="Get cross-role performance analytics",
            description="Get performance metrics spanning SI and APP operations",
            response_model=V1ResponseModel,
        )

    async def _require_hybrid_access(self, request: Request):
        """Require hybrid access permissions"""
        return await self.permission_guard.require_permissions(
            request, 
            [PlatformRole.HYBRID], 
            "hybrid_dashboard_access"
        )
    
    def _create_v1_response(self, data: Any, operation: str) -> V1ResponseModel:
        """Create standardized V1 response"""
        return build_v1_response(data, action=f"{operation}")
    
    def _get_primary_service_role(self, context: HTTPRoutingContext) -> ServiceRole:
        """Get primary service role for hybrid operations"""
        return ServiceRole.HYBRID_SERVICES

    async def get_unified_metrics(self, request: Request) -> V1ResponseModel:
        """Get unified dashboard metrics combining SI and APP data."""

        context = await self._require_hybrid_access(request)

        si_data, si_error = await self._route_service_operation(
            context=context,
            service_role=ServiceRole.SI_SERVICES,
            operation="get_dashboard_metrics",
            payload={"user_id": context.user_id},
        )

        app_data, app_error = await self._route_service_operation(
            context=context,
            service_role=ServiceRole.APP_SERVICES,
            operation="get_dashboard_metrics",
            payload={"user_id": context.user_id},
        )

        validation_payload = await self._fetch_validation_snapshot(context)

        warnings: List[str] = [msg for msg in (si_error, app_error) if msg]
        unified_metrics = self._compose_unified_metrics(
            si_data,
            app_data,
            validation_payload,
            has_warnings=bool(warnings),
        )

        payload: Dict[str, Any] = {
            "success": not warnings,
            "data": unified_metrics,
        }
        if warnings:
            detail = "; ".join(warnings)
            payload["warnings"] = warnings
            payload["message"] = detail

        action = "unified_metrics_retrieved" if not warnings else "unified_metrics_partial"
        return self._create_v1_response(payload, action)
    
    async def get_activity_timeline(self, request: Request) -> V1ResponseModel:
        """Get unified activity timeline from all systems."""

        context = await self._require_hybrid_access(request)
        service_role = self._get_primary_service_role(context)

        data, error = await self._route_service_operation(
            context=context,
            service_role=service_role,
            operation="get_unified_activity_timeline",
            payload={"user_id": context.user_id, "limit": 20},
        )

        if error:
            logger.error("Error getting hybrid activity timeline: %s", error)
            return self._create_v1_response(
                {"success": False, "error": error, "message": error},
                "activity_timeline_failed",
            )

        timeline = data if isinstance(data, list) else data or []
        return self._create_v1_response(
            {"success": True, "data": timeline},
            "activity_timeline_retrieved",
        )

    async def get_system_health(self, request: Request) -> V1ResponseModel:
        """Get overall system health across all integrations."""

        context = await self._require_hybrid_access(request)
        service_role = self._get_primary_service_role(context)

        data, error = await self._route_service_operation(
            context=context,
            service_role=service_role,
            operation="get_system_health_overview",
            payload={"user_id": context.user_id},
        )

        if error:
            logger.error("Error getting hybrid system health: %s", error)
            return self._create_v1_response(
                {"success": False, "error": error, "message": error},
                "system_health_failed",
            )

        return self._create_v1_response(
            {"success": True, "data": data or {}},
            "system_health_retrieved",
        )

    async def get_cross_role_performance(self, request: Request) -> V1ResponseModel:
        """Get performance analytics spanning SI and APP operations."""

        context = await self._require_hybrid_access(request)
        service_role = self._get_primary_service_role(context)

        data, error = await self._route_service_operation(
            context=context,
            service_role=service_role,
            operation="get_cross_role_performance",
            payload={"user_id": context.user_id},
        )

        if error:
            logger.error("Error getting hybrid cross-role performance: %s", error)
            return self._create_v1_response(
                {"success": False, "error": error, "message": error},
                "cross_role_performance_failed",
            )

        return self._create_v1_response(
            {"success": True, "data": data or {}},
            "cross_role_performance_retrieved",
        )

    async def _route_service_operation(
        self,
        *,
        context: HTTPRoutingContext,
        service_role: ServiceRole,
        operation: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Optional[Any], Optional[str]]:
        """Invoke a service operation and return its data or an error message."""

        payload_to_send = payload.copy() if payload else {}
        tenant_id = getattr(context, "tenant_id", None) or getattr(context, "organization_id", None)
        correlation_id = getattr(context, "correlation_id", None)

        try:
            response = await self.message_router.route_message(
                service_role=service_role,
                operation=operation,
                payload=payload_to_send,
                tenant_id=tenant_id,
                correlation_id=correlation_id,
                source_service="api_gateway",
            )
        except Exception as exc:  # pragma: no cover - transport failures already logged upstream
            logger.error(
                "Hybrid dashboard %s via %s failed: %s",
                operation,
                service_role.value,
                exc,
                exc_info=True,
            )
            return None, f"{service_role.value}:{operation} request failed"

        if not isinstance(response, dict):
            logger.error(
                "Hybrid dashboard %s via %s returned invalid payload type: %s",
                operation,
                service_role.value,
                type(response),
            )
            return None, f"{service_role.value}:{operation} returned invalid payload"

        if response.get("success") is True:
            return response.get("data"), None

        if response.get("success") is False:
            error_detail = response.get("error") or response.get("message")
            data_block = response.get("data")
            if not error_detail and isinstance(data_block, dict):
                error_detail = data_block.get("error")
            return None, error_detail or f"{service_role.value}:{operation} reported failure"

        if "data" in response and "success" not in response:
            # Legacy payloads without explicit success flag
            return response["data"], None

        status_text = response.get("status")
        if status_text and str(status_text).lower() == "success":
            trimmed = {
                key: value
                for key, value in response.items()
                if key not in {"status", "operation", "message_id", "timestamp"}
            }
            if trimmed:
                return trimmed, None

        logger.error(
            "Hybrid dashboard %s via %s returned unsupported payload: %s",
            operation,
            service_role.value,
            response,
        )
        return None, f"{service_role.value}:{operation} returned unsupported payload"

    async def _fetch_validation_snapshot(self, context: HTTPRoutingContext) -> Optional[Dict[str, Any]]:
        """Fetch recent validation batches for the hybrid dashboard."""

        organization_id = getattr(context, "organization_id", None)
        if not organization_id:
            return None

        try:
            async for session in get_async_session():
                snapshot = await summarize_validation_batches(
                    session,
                    organization_id=organization_id,
                    limit=5,
                )
                if not isinstance(snapshot, dict):
                    break

                items = snapshot.get("items", [])
                recent_batches = [
                    {
                        "batchId": item.get("batchId"),
                        "status": item.get("status"),
                        "totals": item.get("totals"),
                        "createdAt": item.get("createdAt"),
                    }
                    for item in items
                ]

                sla_hours = 4
                org = await session.get(Organization, organization_id)
                if org and isinstance(org.firs_configuration, dict):
                    configured = org.firs_configuration.get("compliance_sla_hours")
                    try:
                        if configured is not None:
                            sla_hours = max(1, int(configured))
                    except (TypeError, ValueError):
                        logger.debug(
                            "Invalid compliance_sla_hours configuration for org %s",
                            organization_id,
                        )

                return {
                    "summary": snapshot.get("summary"),
                    "recentBatches": recent_batches,
                    "slaHours": sla_hours,
                }
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.error("Error fetching hybrid validation snapshot: %s", exc, exc_info=True)

        return None

    def _compose_unified_metrics(
        self,
        si_data: Optional[Dict[str, Any]],
        app_data: Optional[Dict[str, Any]],
        validation_payload: Optional[Dict[str, Any]],
        *,
        has_warnings: bool,
    ) -> Dict[str, Any]:
        """Normalise SI/APP metrics into the combined hybrid dashboard shape."""

        si_block = si_data or {}
        app_block = app_data or {}

        integrations = (si_block.get("integrations") or {}).get("overall", {})
        total_integrations = self._safe_int(integrations.get("totalSystems"))
        active_integrations = self._safe_int(integrations.get("activeSystems"))
        pending_integrations = max(total_integrations - active_integrations, 0)

        si_transactions = si_block.get("transactions") or {}
        si_success_rate = self._safe_float(si_transactions.get("successRate"))
        si_volume = self._safe_int(si_transactions.get("totalInvoices"))
        si_queue = self._safe_int(si_transactions.get("queue"))

        app_transmission = app_block.get("transmission") or {}
        total_transmissions = self._safe_int(app_transmission.get("total"))
        app_success_rate = self._safe_float(app_transmission.get("rate"))
        app_queue = self._safe_int(app_transmission.get("queue"))

        compliance_block = app_block.get("compliance") or {}
        compliance_score = self._safe_float(compliance_block.get("score"))
        if compliance_score == 0.0:
            compliance_score = self._safe_float((si_block.get("compliance") or {}).get("complianceScore"))

        performance_block = app_block.get("performance") or {}
        security_score = self._safe_float(performance_block.get("overall_score"))

        unified_success_rate = self._calculate_combined_success_rate(
            si_rate=si_success_rate,
            si_volume=si_volume,
            app_rate=app_success_rate,
            app_volume=total_transmissions,
        )

        unified_metrics = {
            "unified": {
                "totalIntegrations": total_integrations,
                "totalTransmissions": total_transmissions,
                "successRate": unified_success_rate,
                "complianceScore": compliance_score,
                "activeWorkflows": active_integrations,
            },
            "si": {
                "integrations": {
                    "active": active_integrations,
                    "pending": pending_integrations,
                },
                "processing": {
                    "rate": si_success_rate,
                    "queue": si_queue,
                },
                "analytics": {
                    "revenue": 0.0,
                    "growth": 0.0,
                },
            },
            "app": {
                "transmission": {
                    "rate": app_success_rate,
                    "queue": app_queue,
                },
                "firs": {
                    "status": compliance_block.get("status", "Unknown"),
                    "uptime": compliance_score,
                },
                "security": {
                    "score": security_score,
                    "threats": self._safe_int(len(performance_block.get("alerts", []))),
                },
            },
            "validation": validation_payload
            or {
                "summary": None,
                "recentBatches": [],
                "slaHours": None,
            },
            "dataSource": "partial" if has_warnings else "live",
            "lastUpdated": app_block.get("generated_at")
            or si_block.get("lastUpdated")
            or datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        }

        return unified_metrics

    @staticmethod
    def _safe_int(value: Any, default: int = 0) -> int:
        try:
            if value is None:
                return default
            if isinstance(value, bool):
                return int(value)
            return int(float(value))
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _safe_float(value: Any, default: float = 0.0) -> float:
        try:
            if value is None:
                return default
            if isinstance(value, bool):
                return float(value)
            return float(value)
        except (TypeError, ValueError):
            return default

    def _calculate_combined_success_rate(
        self,
        *,
        si_rate: float,
        si_volume: int,
        app_rate: float,
        app_volume: int,
    ) -> float:
        """Calculate a weighted success rate using SI and APP volumes."""

        safe_si_volume = max(si_volume, 0)
        safe_app_volume = max(app_volume, 0)
        total_volume = safe_si_volume + safe_app_volume

        if total_volume <= 0:
            return 0.0

        combined = (si_rate * safe_si_volume) + (app_rate * safe_app_volume)
        return round(combined / total_volume, 2)


def create_dashboard_router(
    role_detector: HTTPRoleDetector,
    permission_guard: APIPermissionGuard, 
    message_router: MessageRouter
) -> APIRouter:
    """Factory function to create dashboard router"""
    endpoint_handler = DashboardEndpointsV1(role_detector, permission_guard, message_router)
    return endpoint_handler.router


# Dependency injection helpers
async def _require_hybrid_access(request: Request):
    """Require hybrid access - placeholder for dependency injection"""
    pass
