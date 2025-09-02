"""
Analytics Endpoints - API v1
============================

Endpoints for collecting and analyzing onboarding analytics data.
Provides comprehensive insights into user behavior, completion rates, and performance metrics.

Features:
- Event collection and processing
- Real-time metrics calculation
- Dashboard data aggregation
- Performance analytics
- User segmentation
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from fastapi import APIRouter, Request, HTTPException, Depends, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core_platform.messaging.message_router import ServiceRole, MessageRouter
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from .version_models import V1ResponseModel

logger = logging.getLogger(__name__)


class OnboardingEvent(BaseModel):
    """Onboarding analytics event model"""
    eventType: str = Field(..., description="Type of event (step_start, step_complete, etc.)")
    stepId: str = Field(..., description="Step identifier")
    userId: str = Field(..., description="User identifier")
    userRole: str = Field(..., description="User role (si, app, hybrid)")
    timestamp: str = Field(..., description="Event timestamp")
    sessionId: str = Field(..., description="Session identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional event metadata")


class AnalyticsEventBatch(BaseModel):
    """Batch of analytics events"""
    events: List[OnboardingEvent] = Field(..., description="List of events")
    timestamp: str = Field(..., description="Batch timestamp")


class MetricsRequest(BaseModel):
    """Request for analytics metrics"""
    start: str = Field(..., description="Start date (ISO format)")
    end: str = Field(..., description="End date (ISO format)")
    role: Optional[str] = Field(None, description="Filter by user role")
    stepId: Optional[str] = Field(None, description="Filter by step ID")


class AnalyticsEndpointsV1:
    """
    Analytics endpoints for onboarding data collection and analysis.
    """

    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/analytics", tags=["Analytics V1"])
        
        # Track endpoint usage
        self.endpoint_stats = {
            "total_events_received": 0,
            "total_batches_processed": 0,
            "metrics_requests": 0,
            "dashboard_requests": 0
        }
        
        self._setup_routes()

        logger.info("Analytics Endpoints V1 initialized")
    
    def _setup_routes(self):
        """Setup analytics routes"""
        
        # Collect onboarding events
        self.router.add_api_route(
            "/onboarding",
            self.collect_events,
            methods=["POST"],
            summary="Collect onboarding analytics events",
            description="Submit a batch of onboarding analytics events for processing",
            response_model=V1ResponseModel
        )
        
        # Get onboarding metrics
        self.router.add_api_route(
            "/onboarding/metrics",
            self.get_metrics,
            methods=["GET"],
            summary="Get onboarding analytics metrics",
            description="Retrieve aggregated analytics metrics for onboarding flows",
            response_model=V1ResponseModel
        )
        
        # Get dashboard data
        self.router.add_api_route(
            "/onboarding/dashboard",
            self.get_dashboard_data,
            methods=["GET"],
            summary="Get real-time dashboard data",
            description="Get real-time analytics data for onboarding dashboard",
            response_model=V1ResponseModel
        )
        
        # Get user journey analytics
        self.router.add_api_route(
            "/onboarding/journey/{user_id}",
            self.get_user_journey,
            methods=["GET"],
            summary="Get user journey analytics",
            description="Get detailed analytics for a specific user's onboarding journey",
            response_model=V1ResponseModel
        )
        
        # Get step performance analytics
        self.router.add_api_route(
            "/onboarding/steps/{step_id}/performance",
            self.get_step_performance,
            methods=["GET"],
            summary="Get step performance analytics",
            description="Get detailed performance analytics for a specific onboarding step",
            response_model=V1ResponseModel
        )
        
        # Get funnel analysis
        self.router.add_api_route(
            "/onboarding/funnel",
            self.get_funnel_analysis,
            methods=["GET"],
            summary="Get onboarding funnel analysis",
            description="Get conversion funnel analysis for onboarding flows",
            response_model=V1ResponseModel
        )

    async def collect_events(self, request: Request):
        """Collect and process onboarding analytics events"""
        try:
            self.endpoint_stats["total_batches_processed"] += 1
            
            body = await request.json()
            event_batch = AnalyticsEventBatch(**body)
            
            # Update stats
            self.endpoint_stats["total_events_received"] += len(event_batch.events)
            
            # Process events through message router
            result = await self.message_router.route_message(
                service_role=ServiceRole.ANALYTICS,
                operation="process_onboarding_events",
                payload={
                    "events": [event.dict() for event in event_batch.events],
                    "batch_timestamp": event_batch.timestamp,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "events_processed")
            
        except Exception as e:
            logger.error(f"Error collecting analytics events: {e}")
            raise HTTPException(status_code=500, detail="Failed to process analytics events")

    async def get_metrics(self,
                         start: str = Query(..., description="Start date (ISO format)"),
                         end: str = Query(..., description="End date (ISO format)"),
                         role: Optional[str] = Query(None, description="Filter by user role"),
                         step_id: Optional[str] = Query(None, description="Filter by step ID")):
        """Get aggregated onboarding analytics metrics"""
        try:
            self.endpoint_stats["metrics_requests"] += 1
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ANALYTICS,
                operation="get_onboarding_metrics",
                payload={
                    "start_date": start,
                    "end_date": end,
                    "role_filter": role,
                    "step_filter": step_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "metrics_retrieved")
            
        except Exception as e:
            logger.error(f"Error getting analytics metrics: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve analytics metrics")

    async def get_dashboard_data(self):
        """Get real-time dashboard analytics data"""
        try:
            self.endpoint_stats["dashboard_requests"] += 1
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ANALYTICS,
                operation="get_dashboard_data",
                payload={
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "dashboard_data_retrieved")
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")

    async def get_user_journey(self, user_id: str):
        """Get detailed analytics for a specific user's onboarding journey"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ANALYTICS,
                operation="get_user_journey",
                payload={
                    "user_id": user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "user_journey_retrieved")
            
        except Exception as e:
            logger.error(f"Error getting user journey for {user_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve user journey")

    async def get_step_performance(self, step_id: str,
                                  role: Optional[str] = Query(None, description="Filter by user role"),
                                  days: int = Query(30, description="Number of days to analyze")):
        """Get detailed performance analytics for a specific onboarding step"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ANALYTICS,
                operation="get_step_performance",
                payload={
                    "step_id": step_id,
                    "role_filter": role,
                    "days": days,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "step_performance_retrieved")
            
        except Exception as e:
            logger.error(f"Error getting step performance for {step_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve step performance")

    async def get_funnel_analysis(self,
                                 role: Optional[str] = Query(None, description="Filter by user role"),
                                 days: int = Query(30, description="Number of days to analyze")):
        """Get conversion funnel analysis for onboarding flows"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ANALYTICS,
                operation="get_funnel_analysis",
                payload={
                    "role_filter": role,
                    "days": days,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "funnel_analysis_retrieved")
            
        except Exception as e:
            logger.error(f"Error getting funnel analysis: {e}")
            raise HTTPException(status_code=500, detail="Failed to retrieve funnel analysis")

    def _create_v1_response(self, data: Any, message: str, status_code: int = 200) -> V1ResponseModel:
        """Create standardized V1 response"""
        return V1ResponseModel(
            success=True,
            message=message,
            data=data,
            version="v1",
            timestamp=datetime.utcnow().isoformat()
        )


def create_analytics_router(
    role_detector: HTTPRoleDetector,
    permission_guard: APIPermissionGuard,
    message_router: MessageRouter
) -> APIRouter:
    """Factory function to create analytics router"""
    endpoints = AnalyticsEndpointsV1(role_detector, permission_guard, message_router)
    return endpoints.router
