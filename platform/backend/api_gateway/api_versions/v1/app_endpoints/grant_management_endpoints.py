"""
Grant Management Endpoints - API v1
===================================
Access Point Provider endpoints for managing FIRS grants and performance tracking.
Handles grant milestones, performance metrics, and reporting for FIRS compliance.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status, Query, Path
from fastapi.responses import JSONResponse

from core_platform.authentication.role_manager import PlatformRole
from core_platform.messaging.message_router import ServiceRole, MessageRouter
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from ..version_models import V1ResponseModel
from api_gateway.utils.v1_response import build_v1_response
from api_gateway.utils.error_mapping import v1_error_response

logger = logging.getLogger(__name__)


class GrantManagementEndpointsV1:
    """
    Grant Management Endpoints - Version 1
    ======================================
    Manages FIRS grants and performance tracking for TaxPoynt APP:
    
    **Grant Management Features:**
    - **Milestone Tracking**: Track FIRS grant milestones and progress
    - **Performance Metrics**: Monitor onboarding performance and KPIs
    - **Grant Reporting**: Generate reports for FIRS grant compliance
    - **Payment Tracking**: Track grant payments and disbursements
    - **Compliance Monitoring**: Ensure compliance with grant requirements
    - **Performance Analytics**: Analyze performance trends and insights
    
    **FIRS Grant Context:**
    - TaxPoynt receives grants from FIRS based on taxpayer onboarding performance
    - Grant milestones are tied to successful taxpayer onboarding metrics
    - Organizations onboarded are the basis for grant milestone achievements
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(
            prefix="/grants",
            tags=["Grant Management V1"],
            dependencies=[Depends(self._require_app_role)]
        )
        
        self._setup_routes()
        logger.info("Grant Management Endpoints V1 initialized")
    
    async def _require_app_role(self, request: Request) -> HTTPRoutingContext:
        context = await self.role_detector.detect_role_context(request)
        if not context or not context.has_role(PlatformRole.ACCESS_POINT_PROVIDER):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access Point Provider role required for v1 API")
        if not await self.permission_guard.check_endpoint_permission(
            context, f"v1/app{request.url.path}", request.method
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions for APP v1 endpoint")
        context.metadata["api_version"] = "v1"
        context.metadata["endpoint_group"] = "app"
        return context
    
    def _setup_routes(self):
        """Setup grant management routes"""
        
        # Grant Overview Routes
        self.router.add_api_route(
            "/overview",
            self.get_grant_overview,
            methods=["GET"],
            summary="Get grant overview",
            description="Get overview of all FIRS grants and current status",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/current-status",
            self.get_current_grant_status,
            methods=["GET"],
            summary="Get current grant status",
            description="Get current FIRS grant status and progress",
            response_model=V1ResponseModel
        )
        
        # Milestone Management Routes
        self.router.add_api_route(
            "/milestones",
            self.list_grant_milestones,
            methods=["GET"],
            summary="List grant milestones",
            description="List all FIRS grant milestones and their status",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/milestones/{milestone_id}",
            self.get_milestone_details,
            methods=["GET"],
            summary="Get milestone details",
            description="Get detailed information about a specific milestone",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/milestones/{milestone_id}/progress",
            self.get_milestone_progress,
            methods=["GET"],
            summary="Get milestone progress",
            description="Get progress towards a specific milestone",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/milestones/upcoming",
            self.get_upcoming_milestones,
            methods=["GET"],
            summary="Get upcoming milestones",
            description="Get milestones that are approaching or due soon",
            response_model=V1ResponseModel
        )
        
        # Performance Metrics Routes
        self.router.add_api_route(
            "/performance/metrics",
            self.get_performance_metrics,
            methods=["GET"],
            summary="Get performance metrics",
            description="Get key performance indicators for grant compliance",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/performance/onboarding",
            self.get_onboarding_performance,
            methods=["GET"],
            summary="Get onboarding performance",
            description="Get taxpayer onboarding performance metrics",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/performance/trends",
            self.get_performance_trends,
            methods=["GET"],
            summary="Get performance trends",
            description="Get performance trends and analytics over time",
            response_model=V1ResponseModel
        )
        
        # Grant Reporting Routes
        self.router.add_api_route(
            "/reports/generate",
            self.generate_grant_report,
            methods=["POST"],
            summary="Generate grant report",
            description="Generate detailed grant performance report",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/reports/list",
            self.list_grant_reports,
            methods=["GET"],
            summary="List grant reports",
            description="List all generated grant reports",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/reports/{report_id}",
            self.get_grant_report,
            methods=["GET"],
            summary="Get grant report",
            description="Get specific grant performance report",
            response_model=V1ResponseModel
        )
        
        # Payment Tracking Routes
        self.router.add_api_route(
            "/payments",
            self.list_grant_payments,
            methods=["GET"],
            summary="List grant payments",
            description="List all FIRS grant payments received",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/payments/{payment_id}",
            self.get_payment_details,
            methods=["GET"],
            summary="Get payment details",
            description="Get details of a specific grant payment",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/payments/expected",
            self.get_expected_payments,
            methods=["GET"],
            summary="Get expected payments",
            description="Get expected grant payments based on performance",
            response_model=V1ResponseModel
        )
        
        # Compliance Monitoring Routes
        self.router.add_api_route(
            "/compliance/status",
            self.get_grant_compliance_status,
            methods=["GET"],
            summary="Get grant compliance status",
            description="Get current compliance status with grant requirements",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/compliance/requirements",
            self.get_grant_requirements,
            methods=["GET"],
            summary="Get grant requirements",
            description="Get all FIRS grant requirements and obligations",
            response_model=V1ResponseModel
        )
    
    # Grant Overview Endpoints
    async def get_grant_overview(self, request: Request):
        """Get grant overview"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_grant_overview",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "grant_overview_retrieved")
        except Exception as e:
            logger.error(f"Error getting grant overview in v1: {e}")
            return v1_error_response(e, action="get_grant_overview")
    
    async def get_current_grant_status(self, request: Request):
        """Get current grant status"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_current_grant_status",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "current_grant_status_retrieved")
        except Exception as e:
            logger.error(f"Error getting current grant status in v1: {e}")
            return v1_error_response(e, action="get_current_grant_status")
    
    # Milestone Management Endpoints
    async def list_grant_milestones(self, 
                                  request: Request,
                                  status: Optional[str] = Query(None, description="Filter by milestone status")):
        """List grant milestones"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="list_grant_milestones",
                payload={
                    "app_id": context.user_id,
                    "filters": {
                        "status": status
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "grant_milestones_listed")
        except Exception as e:
            logger.error(f"Error listing grant milestones in v1: {e}")
            return v1_error_response(e, action="list_grant_milestones")
    
    async def get_milestone_details(self, milestone_id: str, request: Request):
        """Get milestone details"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_milestone_details",
                payload={
                    "milestone_id": milestone_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "milestone_details_retrieved")
        except Exception as e:
            logger.error(f"Error getting milestone details {milestone_id} in v1: {e}")
            return v1_error_response(e, action="get_milestone_details")
    
    async def get_milestone_progress(self, milestone_id: str, request: Request):
        """Get milestone progress"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_milestone_progress",
                payload={
                    "milestone_id": milestone_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "milestone_progress_retrieved")
        except Exception as e:
            logger.error(f"Error getting milestone progress {milestone_id} in v1: {e}")
            return v1_error_response(e, action="get_milestone_progress")
    
    async def get_upcoming_milestones(self, 
                                    request: Request,
                                    days_ahead: Optional[int] = Query(30, description="Days ahead to check for milestones")):
        """Get upcoming milestones"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_upcoming_milestones",
                payload={
                    "app_id": context.user_id,
                    "days_ahead": days_ahead,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "upcoming_milestones_retrieved")
        except Exception as e:
            logger.error(f"Error getting upcoming milestones in v1: {e}")
            return v1_error_response(e, action="get_upcoming_milestones")
    
    # Performance Metrics Endpoints
    async def get_performance_metrics(self, 
                                    request: Request,
                                    period: Optional[str] = Query("30d", description="Metrics period")):
        """Get performance metrics"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_performance_metrics",
                payload={
                    "app_id": context.user_id,
                    "period": period,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "performance_metrics_retrieved")
        except Exception as e:
            logger.error(f"Error getting performance metrics in v1: {e}")
            return v1_error_response(e, action="get_performance_metrics")
    
    async def get_onboarding_performance(self, 
                                       request: Request,
                                       period: Optional[str] = Query("30d", description="Performance period")):
        """Get onboarding performance"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_onboarding_performance",
                payload={
                    "app_id": context.user_id,
                    "period": period,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "onboarding_performance_retrieved")
        except Exception as e:
            logger.error(f"Error getting onboarding performance in v1: {e}")
            return v1_error_response(e, action="get_onboarding_performance")
    
    async def get_performance_trends(self, 
                                   request: Request,
                                   period: Optional[str] = Query("90d", description="Trends period")):
        """Get performance trends"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_performance_trends",
                payload={
                    "app_id": context.user_id,
                    "period": period,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "performance_trends_retrieved")
        except Exception as e:
            logger.error(f"Error getting performance trends in v1: {e}")
            return v1_error_response(e, action="get_performance_trends")
    
    # Grant Reporting Endpoints
    async def generate_grant_report(self, request: Request):
        """Generate grant report"""
        try:
            context = await self._require_app_role(request)
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="generate_grant_report",
                payload={
                    "report_config": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "grant_report_generated")
        except Exception as e:
            logger.error(f"Error generating grant report in v1: {e}")
            return v1_error_response(e, action="generate_grant_report")
    
    async def list_grant_reports(self, 
                               request: Request,
                               report_type: Optional[str] = Query(None, description="Filter by report type")):
        """List grant reports"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="list_grant_reports",
                payload={
                    "app_id": context.user_id,
                    "filters": {
                        "report_type": report_type
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "grant_reports_listed")
        except Exception as e:
            logger.error(f"Error listing grant reports in v1: {e}")
            return v1_error_response(e, action="list_grant_reports")
    
    async def get_grant_report(self, report_id: str, request: Request):
        """Get grant report"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_grant_report",
                payload={
                    "report_id": report_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "grant_report_retrieved")
        except Exception as e:
            logger.error(f"Error getting grant report {report_id} in v1: {e}")
            return v1_error_response(e, action="get_grant_report")
    
    # Placeholder implementations for remaining endpoints
    async def list_grant_payments(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """List grant payments - placeholder"""
        return self._create_v1_response({"payments": []}, "grant_payments_listed")
    
    async def get_payment_details(self, payment_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get payment details - placeholder"""
        return self._create_v1_response({"payment_id": payment_id}, "payment_details_retrieved")
    
    async def get_expected_payments(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get expected payments - placeholder"""
        return self._create_v1_response({"expected_payments": []}, "expected_payments_retrieved")
    
    async def get_grant_compliance_status(self, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get grant compliance status - placeholder"""
        return self._create_v1_response({"compliance_status": "compliant"}, "grant_compliance_status_retrieved")
    
    async def get_grant_requirements(self, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get grant requirements - placeholder"""
        return self._create_v1_response({"requirements": []}, "grant_requirements_retrieved")
    
    def _create_v1_response(self, data: Dict[str, Any], action: str, status_code: int = 200) -> V1ResponseModel:
        """Create standardized v1 response format using V1ResponseModel"""
        return build_v1_response(data, action)


def create_grant_management_router(role_detector: HTTPRoleDetector,
                                  permission_guard: APIPermissionGuard,
                                  message_router: MessageRouter) -> APIRouter:
    """Factory function to create Grant Management Router"""
    grant_endpoints = GrantManagementEndpointsV1(role_detector, permission_guard, message_router)
    return grant_endpoints.router
