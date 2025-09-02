"""
APP Onboarding Management Endpoints - API v1
============================================
Access Point Provider endpoints for user onboarding state management and progress tracking.
Provides centralized onboarding state synchronization for APP users.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from fastapi import APIRouter, Request, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from core_platform.authentication.role_manager import PlatformRole
from core_platform.messaging.message_router import ServiceRole, MessageRouter
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from ..version_models import V1ResponseModel

logger = logging.getLogger(__name__)


class APPOnboardingStateRequest(BaseModel):
    """Request model for updating APP onboarding state"""
    current_step: str
    completed_steps: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class APPOnboardingStateResponse(BaseModel):
    """Response model for APP onboarding state"""
    user_id: str
    current_step: str
    completed_steps: List[str]
    has_started: bool
    is_complete: bool
    last_active_date: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class APPOnboardingEndpointsV1:
    """
    APP onboarding state management endpoints for Access Point Providers.
    Handles APP-specific onboarding flow: business verification, FIRS integration setup, compliance settings.
    """

    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/onboarding", tags=["APP Onboarding Management"])
        
        # Track endpoints for monitoring
        self.endpoint_stats = {
            "total_requests": 0,
            "get_state_requests": 0,
            "update_state_requests": 0,
            "reset_state_requests": 0
        }
        
        self._setup_routes()

        logger.info("APP Onboarding Endpoints V1 initialized")
    
    def _setup_routes(self):
        """Setup APP onboarding state management routes"""
        
        # Get current onboarding state
        self.router.add_api_route(
            "/state",
            self.get_onboarding_state,
            methods=["GET"],
            summary="Get current APP onboarding state",
            description="Retrieve the current onboarding progress and state for the authenticated APP user",
            response_model=V1ResponseModel
        )
        
        # Update onboarding state
        self.router.add_api_route(
            "/state",
            self.update_onboarding_state,
            methods=["PUT"],
            summary="Update APP onboarding state",
            description="Update the current APP onboarding step and progress",
            response_model=V1ResponseModel
        )
        
        # Complete specific onboarding step
        self.router.add_api_route(
            "/state/step/{step_name}/complete",
            self.complete_onboarding_step,
            methods=["POST"],
            summary="Mark APP onboarding step as complete",
            description="Mark a specific APP onboarding step as completed",
            response_model=V1ResponseModel
        )
        
        # Mark entire onboarding as complete
        self.router.add_api_route(
            "/complete",
            self.complete_onboarding,
            methods=["POST"],
            summary="Complete APP onboarding",
            description="Mark the entire APP onboarding process as complete",
            response_model=V1ResponseModel
        )
        
        # Reset onboarding state (for testing/re-onboarding)
        self.router.add_api_route(
            "/state/reset",
            self.reset_onboarding_state,
            methods=["DELETE"],
            summary="Reset APP onboarding state",
            description="Reset APP onboarding state to start over (admin/testing only)",
            response_model=V1ResponseModel
        )
        
        # Get onboarding analytics for APP user
        self.router.add_api_route(
            "/analytics",
            self.get_onboarding_analytics,
            methods=["GET"],
            summary="Get APP onboarding analytics",
            description="Get detailed analytics about APP onboarding progress and completion",
            response_model=V1ResponseModel
        )

        # APP-specific business verification status
        self.router.add_api_route(
            "/business-verification",
            self.get_business_verification_status,
            methods=["GET"],
            summary="Get business verification status",
            description="Get the status of business verification for APP onboarding",
            response_model=V1ResponseModel
        )

        # APP-specific FIRS integration setup status
        self.router.add_api_route(
            "/firs-integration",
            self.get_firs_integration_status,
            methods=["GET"],
            summary="Get FIRS integration status",
            description="Get the status of FIRS integration setup for APP onboarding",
            response_model=V1ResponseModel
        )

    # Core APP Onboarding State Management
    async def get_onboarding_state(self, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get current onboarding state for the authenticated APP user"""
        try:
            self.endpoint_stats["get_state_requests"] += 1
            self.endpoint_stats["total_requests"] += 1
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_onboarding_state",
                payload={
                    "user_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "app_onboarding_state_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting APP onboarding state in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get APP onboarding state")

    async def update_onboarding_state(self,
                                      request: Request,
                                      context: HTTPRoutingContext = Depends(lambda: None)):
        """Update APP onboarding state with new progress"""
        try:
            self.endpoint_stats["update_state_requests"] += 1
            self.endpoint_stats["total_requests"] += 1
            
            body = await request.json()
            
            # Validate required fields
            required_fields = ["current_step"]
            missing_fields = [field for field in required_fields if field not in body]
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required fields: {', '.join(missing_fields)}"
                )
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="update_onboarding_state",
                payload={
                    "user_id": context.user_id,
                    "onboarding_data": body,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "app_onboarding_state_updated")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating APP onboarding state in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to update APP onboarding state")

    async def complete_onboarding_step(self,
                                       step_name: str,
                                       request: Request,
                                       context: HTTPRoutingContext = Depends(lambda: None)):
        """Mark a specific APP onboarding step as complete"""
        try:
            body = await request.json() if hasattr(request, 'json') else {}
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="complete_onboarding_step",
                payload={
                    "user_id": context.user_id,
                    "step_name": step_name,
                    "metadata": body.get("metadata", {}),
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "app_onboarding_step_completed")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error completing APP onboarding step in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to complete APP onboarding step")

    async def complete_onboarding(self,
                                  request: Request,
                                  context: HTTPRoutingContext = Depends(lambda: None)):
        """Mark entire APP onboarding as complete"""
        try:
            body = await request.json() if hasattr(request, 'json') else {}
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="complete_onboarding",
                payload={
                    "user_id": context.user_id,
                    "completion_metadata": body.get("metadata", {}),
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "app_onboarding_completed")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error completing APP onboarding in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to complete APP onboarding")

    async def reset_onboarding_state(self, context: HTTPRoutingContext = Depends(lambda: None)):
        """Reset APP onboarding state (admin/testing only)"""
        try:
            self.endpoint_stats["reset_state_requests"] += 1
            self.endpoint_stats["total_requests"] += 1
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="reset_onboarding_state",
                payload={
                    "user_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "app_onboarding_state_reset")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error resetting APP onboarding state in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to reset APP onboarding state")

    async def get_onboarding_analytics(self, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get APP onboarding analytics and progress insights"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_onboarding_analytics",
                payload={
                    "user_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "app_onboarding_analytics_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting APP onboarding analytics in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get APP onboarding analytics")

    # APP-Specific Onboarding Status Endpoints
    async def get_business_verification_status(self, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get business verification status for APP onboarding"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_business_verification_status",
                payload={
                    "user_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "business_verification_status_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting business verification status in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get business verification status")

    async def get_firs_integration_status(self, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get FIRS integration setup status for APP onboarding"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_integration_status",
                payload={
                    "user_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_integration_status_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting FIRS integration status in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get FIRS integration status")

    def _create_v1_response(self, data: Any, message: str, status_code: int = 200) -> V1ResponseModel:
        """Create standardized V1 response"""
        return V1ResponseModel(
            success=True,
            message=message,
            data=data,
            version="v1",
            timestamp=datetime.utcnow().isoformat()
        )


def create_app_onboarding_router(
    role_detector: HTTPRoleDetector,
    permission_guard: APIPermissionGuard,
    message_router: MessageRouter
) -> APIRouter:
    """Factory function to create APP onboarding management router"""
    endpoints = APPOnboardingEndpointsV1(role_detector, permission_guard, message_router)
    return endpoints.router
