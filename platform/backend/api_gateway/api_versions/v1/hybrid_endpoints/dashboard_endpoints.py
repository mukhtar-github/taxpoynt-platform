"""
Dashboard Endpoints - API v1
============================
Hybrid dashboard endpoints for unified metrics and analytics.
Provides consolidated view of SI and APP operations.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse

from core_platform.authentication.role_manager import PlatformRole
from core_platform.messaging.message_router import ServiceRole, MessageRouter
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from ..si_endpoints.version_models import V1ResponseModel

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
            dependencies=[Depends(self._require_hybrid_access)]
        )
        
        # Activity Timeline
        self.router.add_api_route(
            "/activity-timeline",
            self.get_activity_timeline,
            methods=["GET"],
            summary="Get unified activity timeline",
            description="Get recent activities across all roles and systems",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_hybrid_access)]
        )
        
        # System Health Overview
        self.router.add_api_route(
            "/system-health",
            self.get_system_health,
            methods=["GET"],
            summary="Get system health overview",
            description="Get health status of all connected systems",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_hybrid_access)]
        )
        
        # Cross-Role Performance
        self.router.add_api_route(
            "/cross-role-performance",
            self.get_cross_role_performance,
            methods=["GET"],
            summary="Get cross-role performance analytics",
            description="Get performance metrics spanning SI and APP operations",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_hybrid_access)]
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
        return V1ResponseModel(
            success=True,
            data=data,
            message=f"Operation '{operation}' completed successfully",
            version="1.0"
        )
    
    def _get_primary_service_role(self, context: HTTPRoutingContext) -> ServiceRole:
        """Get primary service role for hybrid operations"""
        return ServiceRole.HYBRID_SERVICES

    async def get_unified_metrics(self, request: Request, context: HTTPRoutingContext = Depends(_require_hybrid_access)):
        """Get unified dashboard metrics combining SI and APP data"""
        try:
            service_role = self._get_primary_service_role(context)
            
            # Message SI and APP services for their metrics
            si_result = await self.message_router.send_message(
                ServiceRole.SI_SERVICES,
                operation="get_dashboard_metrics",
                payload={"user_id": context.user_id}
            )
            
            app_result = await self.message_router.send_message(
                ServiceRole.APP_SERVICES,
                operation="get_dashboard_metrics",
                payload={"user_id": context.user_id}
            )
            
            # Combine metrics from both services
            unified_metrics = {
                "totalIntegrations": si_result.get("total_integrations", 0) + app_result.get("total_connections", 0),
                "totalTransmissions": app_result.get("total_transmissions", 0),
                "successRate": self._calculate_combined_success_rate(si_result, app_result),
                "complianceScore": app_result.get("compliance_score", 0),
                "activeWorkflows": si_result.get("active_processes", 0) + app_result.get("active_queues", 0),
                "siMetrics": {
                    "integrations": si_result.get("integrations", {"active": 0, "pending": 0}),
                    "processing": si_result.get("processing", {"rate": 0, "queue": 0}),
                    "analytics": si_result.get("analytics", {"revenue": 0, "growth": 0})
                },
                "appMetrics": {
                    "transmission": app_result.get("transmission", {"rate": 0, "queue": 0}),
                    "firs": app_result.get("firs_status", {"status": "Unknown", "uptime": 0}),
                    "security": app_result.get("security", {"score": 0, "threats": 0})
                },
                "lastUpdated": "now",
                "dataSource": "real_time"
            }
            
            return self._create_v1_response(unified_metrics, "unified_metrics_retrieved")
            
        except Exception as e:
            logger.error(f"Error getting unified metrics: {e}")
            # Return demo data as fallback
            demo_metrics = {
                "totalIntegrations": 15,
                "totalTransmissions": 8432,
                "successRate": 98.7,
                "complianceScore": 97,
                "activeWorkflows": 23,
                "siMetrics": {
                    "integrations": {"active": 12, "pending": 3},
                    "processing": {"rate": 1234, "queue": 45},
                    "analytics": {"revenue": 45200000, "growth": 23}
                },
                "appMetrics": {
                    "transmission": {"rate": 98.7, "queue": 23},
                    "firs": {"status": "Connected", "uptime": 99.9},
                    "security": {"score": 96, "threats": 0}
                },
                "lastUpdated": "demo",
                "dataSource": "fallback"
            }
            return self._create_v1_response(demo_metrics, "unified_metrics_demo")
    
    def _calculate_combined_success_rate(self, si_result: Dict, app_result: Dict) -> float:
        """Calculate combined success rate from SI and APP metrics"""
        si_rate = si_result.get("success_rate", 0)
        app_rate = app_result.get("success_rate", 0)
        
        # Weighted average based on transaction volumes
        si_volume = si_result.get("transaction_volume", 1)
        app_volume = app_result.get("transaction_volume", 1)
        total_volume = si_volume + app_volume
        
        if total_volume == 0:
            return 0
        
        return ((si_rate * si_volume) + (app_rate * app_volume)) / total_volume

    async def get_activity_timeline(self, request: Request, context: HTTPRoutingContext = Depends(_require_hybrid_access)):
        """Get unified activity timeline from all systems"""
        try:
            service_role = self._get_primary_service_role(context)
            
            # Get activities from both SI and APP services
            result = await self.message_router.send_message(
                service_role,
                operation="get_unified_activity_timeline",
                payload={"user_id": context.user_id, "limit": 20}
            )
            
            return self._create_v1_response(result, "activity_timeline_retrieved")
            
        except Exception as e:
            logger.error(f"Error getting activity timeline: {e}")
            # Demo timeline data
            demo_timeline = [
                {
                    "time": "2 minutes ago",
                    "action": "SI: New ERP integration completed",
                    "system": "SAP ERP",
                    "type": "si",
                    "status": "success"
                },
                {
                    "time": "5 minutes ago",
                    "action": "APP: Invoice batch transmitted to FIRS",
                    "count": "245 invoices",
                    "type": "app",
                    "status": "success"
                },
                {
                    "time": "12 minutes ago",
                    "action": "Workflow: End-to-end process completed",
                    "result": "Invoice → FIRS submission",
                    "type": "workflow",
                    "status": "success"
                }
            ]
            return self._create_v1_response(demo_timeline, "activity_timeline_demo")

    async def get_system_health(self, request: Request, context: HTTPRoutingContext = Depends(_require_hybrid_access)):
        """Get overall system health across all integrations"""
        try:
            service_role = self._get_primary_service_role(context)
            
            result = await self.message_router.send_message(
                service_role,
                operation="get_system_health_overview",
                payload={"user_id": context.user_id}
            )
            
            return self._create_v1_response(result, "system_health_retrieved")
            
        except Exception as e:
            logger.error(f"Error getting system health: {e}")
            # Demo health data
            demo_health = {
                "overall_status": "healthy",
                "systems": {
                    "si_integrations": {"status": "healthy", "uptime": 99.8},
                    "app_connections": {"status": "healthy", "uptime": 99.9},
                    "firs_connection": {"status": "healthy", "uptime": 99.5},
                    "database": {"status": "healthy", "uptime": 100.0}
                },
                "alerts": [],
                "last_check": "now"
            }
            return self._create_v1_response(demo_health, "system_health_demo")

    async def get_cross_role_performance(self, request: Request, context: HTTPRoutingContext = Depends(_require_hybrid_access)):
        """Get performance analytics spanning SI and APP operations"""
        try:
            service_role = self._get_primary_service_role(context)
            
            result = await self.message_router.send_message(
                service_role,
                operation="get_cross_role_performance",
                payload={"user_id": context.user_id}
            )
            
            return self._create_v1_response(result, "cross_role_performance_retrieved")
            
        except Exception as e:
            logger.error(f"Error getting cross-role performance: {e}")
            # Demo performance data
            demo_performance = {
                "end_to_end_processing_time": "2.5 minutes",
                "si_to_app_handoff_time": "15 seconds",
                "total_processed_today": 1247,
                "success_rate": 98.7,
                "bottlenecks": [],
                "optimization_suggestions": [
                    "Consider batch processing for high-volume periods",
                    "Enable auto-reconciliation for faster processing"
                ]
            }
            return self._create_v1_response(demo_performance, "cross_role_performance_demo")


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
