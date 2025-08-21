"""
Monitoring Endpoints - API v1
=============================
Hybrid endpoints for cross-role monitoring and observability.
Handles system health, performance metrics, and alerting across roles.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse

from core_platform.authentication.role_manager import PlatformRole
from core_platform.messaging.message_router import ServiceRole, MessageRouter
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from ..version_models import V1ResponseModel

logger = logging.getLogger(__name__)


class MonitoringEndpointsV1:
    """
    Monitoring Endpoints - Version 1
    ================================
    Manages cross-role monitoring and observability:
    
    **Monitoring Capabilities:**
    - **System Health**: Monitor health across SI and APP services
    - **Performance Metrics**: Track performance across role boundaries
    - **Alert Management**: Handle alerts and notifications for all roles
    - **Audit Trails**: Track cross-role activities and compliance
    - **Resource Utilization**: Monitor resource usage across the platform
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/monitoring", tags=["Cross-Role Monitoring V1"])
        
        self._setup_routes()
        logger.info("Monitoring Endpoints V1 initialized")
    
    def _setup_routes(self):
        """Setup monitoring routes"""
        
        # System Health
        self.router.add_api_route(
            "/health/overview",
            self.get_health_overview,
            methods=["GET"],
            summary="Get health overview",
            description="Get overall system health across all roles",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_monitoring_access)]
        )
        
        # Performance Metrics
        self.router.add_api_route(
            "/metrics/performance",
            self.get_performance_metrics,
            methods=["GET"],
            summary="Get performance metrics",
            description="Get performance metrics across roles",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_monitoring_access)]
        )
        
        # Alerts
        self.router.add_api_route(
            "/alerts",
            self.list_alerts,
            methods=["GET"],
            summary="List alerts",
            description="List active alerts across the platform",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_monitoring_access)]
        )
        
        # Core Platform Metrics Routes
        self.router.add_api_route(
            "/metrics",
            self.create_metric_record,
            methods=["POST"],
            summary="Create metric record",
            description="Create a new metric record",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_monitoring_access)]
        )
        
        self.router.add_api_route(
            "/metrics",
            self.get_metrics,
            methods=["GET"],
            summary="Get metrics",
            description="Get metrics data with filtering",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_monitoring_access)]
        )
        
        self.router.add_api_route(
            "/metrics/aggregate",
            self.aggregate_metrics,
            methods=["POST"],
            summary="Aggregate metrics",
            description="Get aggregated metrics data",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_monitoring_access)]
        )
    
    async def _require_monitoring_access(self, request: Request) -> HTTPRoutingContext:
        """Require monitoring access"""
        context = await self.role_detector.detect_role_context(request)
        
        # Allow access for any valid role (monitoring is generally accessible)
        allowed_roles = {
            PlatformRole.SYSTEM_INTEGRATOR,
            PlatformRole.ACCESS_POINT_PROVIDER,
            PlatformRole.ADMINISTRATOR
        }
        
        if not any(context.has_role(role) for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access requires a valid platform role"
            )
        
        return context
    
    # =============================================================================
    # Core Platform Metrics Services
    # =============================================================================
    
    async def create_metric_record(self, request: Request, context: HTTPRoutingContext = Depends(_require_monitoring_access)):
        """Create a new metric record"""
        try:
            body = await request.json()
            service_role = self._get_primary_service_role(context)
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="create_metric_record",
                payload={
                    "user_id": context.user_id,
                    "metric_data": body,
                    "creator_role": context.primary_role
                }
            )
            return self._create_v1_response(result, "metric_record_created")
        except Exception as e:
            logger.error(f"Error creating metric record in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to create metric record")
    
    async def get_metrics(self, request: Request, context: HTTPRoutingContext = Depends(_require_monitoring_access)):
        """Get metrics data with filtering and aggregation"""
        try:
            service_role = self._get_primary_service_role(context)
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="get_metrics",
                payload={
                    "user_id": context.user_id,
                    "role": context.primary_role,
                    "filters": dict(request.query_params)
                }
            )
            return self._create_v1_response(result, "metrics_retrieved")
        except Exception as e:
            logger.error(f"Error getting metrics in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get metrics")
    
    async def aggregate_metrics(self, request: Request, context: HTTPRoutingContext = Depends(_require_monitoring_access)):
        """Get aggregated metrics data"""
        try:
            body = await request.json()
            service_role = self._get_primary_service_role(context)
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="aggregate_metrics",
                payload={
                    "user_id": context.user_id,
                    "aggregation_params": body,
                    "requester_role": context.primary_role
                }
            )
            return self._create_v1_response(result, "metrics_aggregated")
        except Exception as e:
            logger.error(f"Error aggregating metrics in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to aggregate metrics")
    
    # Enhanced monitoring implementations
    async def get_health_overview(self, context: HTTPRoutingContext = Depends(_require_monitoring_access)):
        """Get comprehensive health overview"""
        try:
            service_role = self._get_primary_service_role(context)
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="get_platform_health",
                payload={
                    "user_id": context.user_id,
                    "role": context.primary_role,
                    "detailed": True
                }
            )
            return self._create_v1_response(result, "health_overview_retrieved")
        except Exception as e:
            logger.error(f"Error getting health overview in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get health overview")
    
    async def get_performance_metrics(self, request: Request, context: HTTPRoutingContext = Depends(_require_monitoring_access)):
        """Get performance metrics"""
        try:
            service_role = self._get_primary_service_role(context)
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="get_performance_metrics",
                payload={
                    "user_id": context.user_id,
                    "role": context.primary_role,
                    "filters": dict(request.query_params)
                }
            )
            return self._create_v1_response(result, "performance_metrics_retrieved")
        except Exception as e:
            logger.error(f"Error getting performance metrics in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get performance metrics")
    
    async def list_alerts(self, request: Request, context: HTTPRoutingContext = Depends(_require_monitoring_access)):
        """List system alerts"""
        try:
            service_role = self._get_primary_service_role(context)
            result = await self.message_router.route_message(
                service_role=service_role,
                operation="list_alerts",
                payload={
                    "user_id": context.user_id,
                    "role": context.primary_role,
                    "filters": dict(request.query_params)
                }
            )
            return self._create_v1_response(result, "alerts_listed")
        except Exception as e:
            logger.error(f"Error listing alerts in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to list alerts")
    
    def _get_primary_service_role(self, context: HTTPRoutingContext) -> ServiceRole:
        """Map user role to appropriate service role"""
        if context.has_role(PlatformRole.SYSTEM_INTEGRATOR):
            return ServiceRole.SYSTEM_INTEGRATOR
        elif context.has_role(PlatformRole.ACCESS_POINT_PROVIDER):
            return ServiceRole.ACCESS_POINT_PROVIDER
        elif context.has_role(PlatformRole.ADMINISTRATOR):
            return ServiceRole.ADMINISTRATOR
        else:
            return ServiceRole.SYSTEM_INTEGRATOR  # Default
    
    def _create_v1_response(self, data: Dict[str, Any], action: str, status_code: int = 200) -> JSONResponse:
        """Create standardized v1 response format"""
        response_data = {
            "success": True,
            "action": action,
            "api_version": "v1",
            "timestamp": "2024-12-31T00:00:00Z",
            "data": data
        }
        
        return JSONResponse(content=response_data, status_code=status_code)


def create_monitoring_router(role_detector: HTTPRoleDetector,
                           permission_guard: APIPermissionGuard,
                           message_router: MessageRouter) -> APIRouter:
    """Factory function to create Monitoring Router"""
    monitoring_endpoints = MonitoringEndpointsV1(role_detector, permission_guard, message_router)
    return monitoring_endpoints.router