"""
Tracking Management Endpoints - API v1
======================================
Access Point Provider endpoints for real-time tracking of invoice transmission status and FIRS responses.
Handles status monitoring, real-time updates, and transmission progress tracking.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse
from datetime import datetime

from core_platform.authentication.role_manager import PlatformRole
from core_platform.messaging.message_router import ServiceRole, MessageRouter
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from ..version_models import V1ResponseModel
from sqlalchemy.ext.asyncio import AsyncSession
from core_platform.data_management.db_async import get_async_session
from api_gateway.dependencies.tenant import make_tenant_scope_dependency
from core_platform.data_management.repositories.firs_submission_repo_async import (
    list_recent_submissions,
    get_submission_metrics,
    list_submissions_filtered,
    get_submission_by_id,
)
from api_gateway.utils.pagination import normalize_pagination
from core_platform.data_management.models.firs_submission import FIRSSubmission
from prometheus_client import Counter

logger = logging.getLogger(__name__)


class TrackingManagementEndpointsV1:
    """
    Tracking Management Endpoints - Version 1
    ==========================================
    Manages real-time tracking of invoice transmissions for APP providers:
    
    **Tracking Management Features:**
    - **Real-time Status**: Live transmission status monitoring
    - **Progress Tracking**: Detailed progress tracking for batch processing
    - **FIRS Response Tracking**: Monitor FIRS acknowledgments and responses
    - **Performance Metrics**: Transmission performance and timing metrics
    - **Alert Management**: Real-time alerts for transmission issues
    - **Historical Analysis**: Transmission trends and analytics
    
    **Tracking Capabilities:**
    - Real-time status updates
    - Progress monitoring for large batches
    - FIRS response correlation
    - Performance analytics
    - Issue detection and alerting
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/tracking", tags=["Tracking Management V1"])
        
        # Define tracking capabilities
        self.tracking_capabilities = {
            "real_time_monitoring": {
                "features": ["live_status_updates", "progress_tracking", "completion_monitoring"],
                "description": "Real-time monitoring of transmission status and progress"
            },
            "firs_response_tracking": {
                "features": ["acknowledgment_tracking", "response_correlation", "status_mapping"],
                "description": "Track FIRS responses and acknowledgments"
            },
            "performance_analytics": {
                "features": ["timing_analysis", "throughput_metrics", "success_rates"],
                "description": "Performance analytics and metrics tracking"
            },
            "alert_management": {
                "features": ["real_time_alerts", "threshold_monitoring", "notification_system"],
                "description": "Alert management for transmission issues"
            }
        }
        
        # Shared tenant scope dependency (uses APP role guard)
        self.tenant_scope = make_tenant_scope_dependency(self._require_app_role)

        self._setup_routes()
        logger.info("Tracking Management Endpoints V1 initialized")
        # Metrics: count recent submissions requests
        self.metric_recent_submissions_total = Counter(
            "app_recent_submissions_requests_total",
            "Total recent submissions requests",
            registry=None,
        )

    async def _require_app_role(self, request: Request) -> HTTPRoutingContext:
        """Enforce APP role and permissions for v1 APP tracking routes."""
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
        """Setup tracking management routes"""
        
        # Tracking Overview and Metrics
        self.router.add_api_route(
            "/metrics",
            self.get_tracking_metrics,
            methods=["GET"],
            summary="Get tracking metrics",
            description="Get comprehensive tracking metrics and statistics",
            response_model=V1ResponseModel,
            dependencies=[Depends(self.tenant_scope)]
        )

        # Recent submissions (async + tenant scoped)
        self.router.add_api_route(
            "/submissions/recent",
            self.get_recent_submissions,
            methods=["GET"],
            summary="Get recent FIRS submissions",
            description="List recent FIRS submissions for the current tenant (APP)",
            response_model=V1ResponseModel,
            dependencies=[Depends(self.tenant_scope)]
        )

        # Filtered submissions (async + tenant scoped)
        self.router.add_api_route(
            "/submissions",
            self.get_submissions,
            methods=["GET"],
            summary="List submissions with filters",
            description="List FIRS submissions for the current tenant with filters and pagination",
            response_model=V1ResponseModel,
            dependencies=[Depends(self.tenant_scope)]
        )

        # Submission detail (async + tenant scoped)
        self.router.add_api_route(
            "/submissions/{submission_id}",
            self.get_submission,
            methods=["GET"],
            summary="Get submission by ID",
            description="Get a single submission for the current tenant by ID",
            response_model=V1ResponseModel,
            dependencies=[Depends(self.tenant_scope)]
        )
        
        self.router.add_api_route(
            "/overview",
            self.get_tracking_overview,
            methods=["GET"],
            summary="Get tracking overview",
            description="Get tracking overview and dashboard data",
            response_model=V1ResponseModel
        )
        
        # Transmission Status Tracking
        self.router.add_api_route(
            "/transmissions",
            self.get_transmission_statuses,
            methods=["GET"],
            summary="Get transmission statuses",
            description="Get current status of all transmissions",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/transmissions/{transmission_id}",
            self.get_transmission_tracking,
            methods=["GET"],
            summary="Get transmission tracking",
            description="Get detailed tracking information for specific transmission",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/transmissions/{transmission_id}/progress",
            self.get_transmission_progress,
            methods=["GET"],
            summary="Get transmission progress",
            description="Get real-time progress of transmission",
            response_model=V1ResponseModel
        )
        
        # Real-time Updates
        self.router.add_api_route(
            "/live-updates",
            self.get_live_updates,
            methods=["GET"],
            summary="Get live updates",
            description="Get real-time updates for active transmissions",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/status-changes",
            self.get_recent_status_changes,
            methods=["GET"],
            summary="Get recent status changes",
            description="Get recent status changes across all transmissions",
            response_model=V1ResponseModel
        )
        
        # FIRS Response Tracking
        self.router.add_api_route(
            "/firs-responses",
            self.get_firs_responses,
            methods=["GET"],
            summary="Get FIRS responses",
            description="Get FIRS acknowledgments and responses",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/firs-responses/{transmission_id}",
            self.get_firs_response_details,
            methods=["GET"],
            summary="Get FIRS response details",
            description="Get detailed FIRS response for specific transmission",
            response_model=V1ResponseModel
        )
        
        # Performance Analytics
        self.router.add_api_route(
            "/performance/metrics",
            self.get_performance_metrics,
            methods=["GET"],
            summary="Get performance metrics",
            description="Get transmission performance metrics and analytics",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/performance/trends",
            self.get_performance_trends,
            methods=["GET"],
            summary="Get performance trends",
            description="Get transmission performance trends over time",
            response_model=V1ResponseModel
        )
        
        # Alerts and Notifications
        self.router.add_api_route(
            "/alerts",
            self.get_active_alerts,
            methods=["GET"],
            summary="Get active alerts",
            description="Get current active alerts and issues",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/alerts/{alert_id}/acknowledge",
            self.acknowledge_alert,
            methods=["POST"],
            summary="Acknowledge alert",
            description="Acknowledge and resolve alert",
            response_model=V1ResponseModel
        )

    def _to_submission_dict(self, s: FIRSSubmission) -> Dict[str, Any]:
        return {
            "id": str(getattr(s, "id", None)),
            "organization_id": str(getattr(s, "organization_id", "")) if getattr(s, "organization_id", None) else None,
            "invoice_number": getattr(s, "invoice_number", None),
            "irn": getattr(s, "irn", None),
            "status": getattr(s, "status", None).value if getattr(s, "status", None) else None,
            "validation_status": getattr(s, "validation_status", None).value if getattr(s, "validation_status", None) else None,
            "total_amount": float(getattr(s, "total_amount", 0) or 0),
            "currency": getattr(s, "currency", None),
            "created_at": getattr(s, "created_at", None).isoformat() if getattr(s, "created_at", None) else None,
            "submitted_at": getattr(s, "submitted_at", None).isoformat() if getattr(s, "submitted_at", None) else None,
        }

    async def get_recent_submissions(self,
                                    limit: int = Query(10, ge=1, le=100),
                                    offset: int = Query(0, ge=0),
                                    db: AsyncSession = Depends(get_async_session)):
        try:
            self.metric_recent_submissions_total.inc()
            rows = await list_recent_submissions(db, limit=limit, offset=offset)
            payload = {
                "items": [self._to_submission_dict(r) for r in rows],
                "count": len(rows),
                "pagination": normalize_pagination(limit=limit, offset=offset, total=len(rows))
            }
            return self._create_v1_response(payload, "recent_submissions_retrieved")
        except Exception as e:
            logger.error(f"Error getting recent submissions: {e}")
            raise HTTPException(status_code=500, detail="Failed to get recent submissions")

    async def get_submissions(
        self,
        status: Optional[str] = Query(None, description="Filter by submission status"),
        start_date: Optional[str] = Query(None, description="Start date (ISO)")
        ,
        end_date: Optional[str] = Query(None, description="End date (ISO)"),
        limit: int = Query(50, ge=1, le=1000),
        offset: int = Query(0, ge=0),
        db: AsyncSession = Depends(get_async_session),
    ):
        """List submissions with filters (async, tenant scoped via dependency)."""
        try:
            rows = await list_submissions_filtered(
                db,
                status=status,
                start_date=start_date,
                end_date=end_date,
                limit=limit,
                offset=offset,
            )
            payload = {
                "items": [self._to_submission_dict(r) for r in rows],
                "count": len(rows),
                "pagination": normalize_pagination(limit=limit, offset=offset, total=len(rows)),
            }
            return self._create_v1_response(payload, "submissions_listed")
        except Exception as e:
            logger.error(f"Error listing submissions: {e}")
            raise HTTPException(status_code=500, detail="Failed to list submissions")

    async def get_submission(
        self,
        submission_id: str,
        db: AsyncSession = Depends(get_async_session),
    ):
        """Get a single submission (async, tenant scoped via dependency)."""
        try:
            row = await get_submission_by_id(db, submission_id=submission_id)
            if not row:
                raise HTTPException(status_code=404, detail="Submission not found")
            return self._create_v1_response(self._to_submission_dict(row), "submission_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting submission {submission_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get submission")
        
        # Search and Filtering
        self.router.add_api_route(
            "/search",
            self.search_transmissions,
            methods=["GET"],
            summary="Search transmissions",
            description="Search transmissions by various criteria",
            response_model=V1ResponseModel
        )
        
        # Batch Operations
        self.router.add_api_route(
            "/batch-status",
            self.get_batch_status_summary,
            methods=["GET"],
            summary="Get batch status summary",
            description="Get status summary for multiple batches",
            response_model=V1ResponseModel
        )
    
    # Tracking Metrics Endpoints
    async def get_tracking_metrics(self, db: AsyncSession = Depends(get_async_session)):
        """Get comprehensive tracking metrics (async, tenant-scoped)."""
        try:
            metrics = await get_submission_metrics(db)
            metrics["capabilities"] = self.tracking_capabilities
            return self._create_v1_response(metrics, "tracking_metrics_retrieved")
        except Exception as e:
            logger.error(f"Error getting tracking metrics in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get tracking metrics")
    
    async def get_tracking_overview(self, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get tracking overview"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_tracking_overview",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "tracking_overview_retrieved")
        except Exception as e:
            logger.error(f"Error getting tracking overview in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get tracking overview")
    
    # Transmission Status Tracking
    async def get_transmission_statuses(self, 
                                      status: Optional[str] = Query(None, description="Filter by status"),
                                      limit: Optional[int] = Query(50, description="Number of transmissions to return"),
                                      context: HTTPRoutingContext = Depends(lambda: None)):
        """Get current status of all transmissions"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_transmission_statuses",
                payload={
                    "status": status,
                    "limit": limit,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            # Add demo data if service not available
            if not result:
                result = [
                    {
                        "id": "TX-2024-001",
                        "batchId": "BATCH-2024-015",
                        "submittedAt": "2024-01-15 14:30:00",
                        "status": "accepted",
                        "invoiceCount": 156,
                        "processedCount": 156,
                        "acceptedCount": 156,
                        "rejectedCount": 0,
                        "firsResponse": {
                            "acknowledgeId": "ACK-FIRS-2024-001",
                            "responseDate": "2024-01-15 14:32:15",
                            "message": "All invoices processed successfully"
                        }
                    },
                    {
                        "id": "TX-2024-002",
                        "batchId": "BATCH-2024-014",
                        "submittedAt": "2024-01-15 13:45:00",
                        "status": "processing",
                        "invoiceCount": 89,
                        "processedCount": 67,
                        "acceptedCount": 67,
                        "rejectedCount": 0
                    }
                ]
            
            return self._create_v1_response(result, "transmission_statuses_retrieved")
        except Exception as e:
            logger.error(f"Error getting transmission statuses in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get transmission statuses")
    
    async def get_transmission_tracking(self, transmission_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get detailed tracking information for specific transmission"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_transmission_tracking",
                payload={
                    "transmission_id": transmission_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "transmission_tracking_retrieved")
        except Exception as e:
            logger.error(f"Error getting transmission tracking {transmission_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get transmission tracking")
    
    async def get_transmission_progress(self, transmission_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get real-time progress of transmission"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_transmission_progress",
                payload={
                    "transmission_id": transmission_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "transmission_progress_retrieved")
        except Exception as e:
            logger.error(f"Error getting transmission progress {transmission_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get transmission progress")
    
    # Real-time Updates
    async def get_live_updates(self, 
                             since: Optional[str] = Query(None, description="Get updates since timestamp"),
                             context: HTTPRoutingContext = Depends(lambda: None)):
        """Get real-time updates for active transmissions"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_live_updates",
                payload={
                    "since": since,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "live_updates_retrieved")
        except Exception as e:
            logger.error(f"Error getting live updates in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get live updates")
    
    async def get_recent_status_changes(self, 
                                      hours: Optional[int] = Query(24, description="Hours of status changes to retrieve"),
                                      context: HTTPRoutingContext = Depends(lambda: None)):
        """Get recent status changes across all transmissions"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_recent_status_changes",
                payload={
                    "hours": hours,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "recent_status_changes_retrieved")
        except Exception as e:
            logger.error(f"Error getting recent status changes in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get recent status changes")
    
    # FIRS Response Tracking
    async def get_firs_responses(self, 
                               status: Optional[str] = Query(None, description="Filter by response status"),
                               limit: Optional[int] = Query(50, description="Number of responses to return"),
                               context: HTTPRoutingContext = Depends(lambda: None)):
        """Get FIRS acknowledgments and responses"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_responses",
                payload={
                    "status": status,
                    "limit": limit,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_responses_retrieved")
        except Exception as e:
            logger.error(f"Error getting FIRS responses in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get FIRS responses")
    
    async def get_firs_response_details(self, transmission_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get detailed FIRS response for specific transmission"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_response_details",
                payload={
                    "transmission_id": transmission_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_response_details_retrieved")
        except Exception as e:
            logger.error(f"Error getting FIRS response details {transmission_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get FIRS response details")
    
    # Performance Analytics
    async def get_performance_metrics(self, 
                                    period: Optional[str] = Query("24h", description="Metrics period"),
                                    context: HTTPRoutingContext = Depends(lambda: None)):
        """Get transmission performance metrics"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_performance_metrics",
                payload={
                    "period": period,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "performance_metrics_retrieved")
        except Exception as e:
            logger.error(f"Error getting performance metrics in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get performance metrics")
    
    async def get_performance_trends(self, 
                                   period: Optional[str] = Query("7d", description="Trends period"),
                                   context: HTTPRoutingContext = Depends(lambda: None)):
        """Get transmission performance trends"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_performance_trends",
                payload={
                    "period": period,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "performance_trends_retrieved")
        except Exception as e:
            logger.error(f"Error getting performance trends in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get performance trends")
    
    # Alerts and Notifications
    async def get_active_alerts(self, 
                              severity: Optional[str] = Query(None, description="Filter by alert severity"),
                              context: HTTPRoutingContext = Depends(lambda: None)):
        """Get current active alerts"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_active_alerts",
                payload={
                    "severity": severity,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "active_alerts_retrieved")
        except Exception as e:
            logger.error(f"Error getting active alerts in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get active alerts")
    
    async def acknowledge_alert(self, alert_id: str, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Acknowledge and resolve alert"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="acknowledge_alert",
                payload={
                    "alert_id": alert_id,
                    "acknowledgment_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "alert_acknowledged")
        except Exception as e:
            logger.error(f"Error acknowledging alert {alert_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to acknowledge alert")
    
    # Search and Filtering
    async def search_transmissions(self, 
                                 query: str = Query(..., description="Search query"),
                                 filter_type: Optional[str] = Query("all", description="Search filter type"),
                                 limit: Optional[int] = Query(20, description="Number of results to return"),
                                 context: HTTPRoutingContext = Depends(lambda: None)):
        """Search transmissions by various criteria"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="search_transmissions",
                payload={
                    "query": query,
                    "filter_type": filter_type,
                    "limit": limit,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "transmissions_searched")
        except Exception as e:
            logger.error(f"Error searching transmissions in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to search transmissions")
    
    # Batch Operations
    async def get_batch_status_summary(self, 
                                     batch_ids: List[str] = Query(..., description="List of batch IDs"),
                                     context: HTTPRoutingContext = Depends(lambda: None)):
        """Get status summary for multiple batches"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_batch_status_summary",
                payload={
                    "batch_ids": batch_ids,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "batch_status_summary_retrieved")
        except Exception as e:
            logger.error(f"Error getting batch status summary in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get batch status summary")
    
    def _create_v1_response(self, data: Dict[str, Any], action: str, status_code: int = 200) -> V1ResponseModel:
        """Create standardized v1 response format using V1ResponseModel"""
        from api_gateway.utils.v1_response import build_v1_response
        return build_v1_response(data, action)


def create_tracking_management_router(role_detector: HTTPRoleDetector,
                                     permission_guard: APIPermissionGuard,
                                     message_router: MessageRouter) -> APIRouter:
    """Factory function to create Tracking Management Router"""
    tracking_endpoints = TrackingManagementEndpointsV1(role_detector, permission_guard, message_router)
    return tracking_endpoints.router
