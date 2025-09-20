"""
Onboarding Management Endpoints - API v1
========================================
System Integrator endpoints for onboarding state management and progress tracking.
Provides centralized onboarding state synchronization across devices and sessions.
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
from api_gateway.utils.v1_response import build_v1_response

logger = logging.getLogger(__name__)


class OnboardingStateRequest(BaseModel):
    """Request model for updating onboarding state"""
    current_step: str
    completed_steps: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class OnboardingStateResponse(BaseModel):
    """Response model for onboarding state"""
    user_id: str
    current_step: str
    completed_steps: List[str]
    has_started: bool
    is_complete: bool
    last_active_date: str
    metadata: Dict[str, Any]
    created_at: str
    updated_at: str


class OnboardingEndpointsV1:
    """
    Onboarding state management endpoints for System Integrators.
    Handles onboarding progress tracking, state synchronization, and resumption.
    """

    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(
            prefix="/onboarding",
            tags=["SI Onboarding Management"],
            dependencies=[Depends(self._require_si_role)]
        )
        
        # Track endpoints for monitoring
        self.endpoint_stats = {
            "total_requests": 0,
            "get_state_requests": 0,
            "update_state_requests": 0,
            "reset_state_requests": 0
        }
        
        self._setup_routes()

        logger.info("Onboarding Endpoints V1 initialized")
    
    async def _require_si_role(self, request: Request) -> HTTPRoutingContext:
        """Ensure System Integrator role access for v1 SI endpoints."""
        context = await self.role_detector.detect_role_context(request)
        if not context or not context.has_role(PlatformRole.SYSTEM_INTEGRATOR):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="System Integrator role required for v1 API")
        if not await self.permission_guard.check_endpoint_permission(
            context, f"v1/si{request.url.path}", request.method
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions for SI v1 endpoint")
        context.metadata["api_version"] = "v1"
        context.metadata["endpoint_group"] = "si"
        return context

    def _setup_routes(self):
        """Setup onboarding state management routes"""
        
        # Get current onboarding state
        self.router.add_api_route(
            "/state",
            self.get_onboarding_state,
            methods=["GET"],
            summary="Get current onboarding state",
            description="Retrieve the current onboarding progress and state for the authenticated user",
            response_model=V1ResponseModel
        )
        
        # Update onboarding state
        self.router.add_api_route(
            "/state",
            self.update_onboarding_state,
            methods=["PUT"],
            summary="Update onboarding state",
            description="Update the current onboarding step and progress",
            response_model=V1ResponseModel
        )
        
        # Complete specific onboarding step
        self.router.add_api_route(
            "/state/step/{step_name}/complete",
            self.complete_onboarding_step,
            methods=["POST"],
            summary="Mark onboarding step as complete",
            description="Mark a specific onboarding step as completed",
            response_model=V1ResponseModel
        )
        
        # Mark entire onboarding as complete
        self.router.add_api_route(
            "/complete",
            self.complete_onboarding,
            methods=["POST"],
            summary="Complete onboarding",
            description="Mark the entire onboarding process as complete",
            response_model=V1ResponseModel
        )
        
        # Reset onboarding state (for testing/re-onboarding)
        self.router.add_api_route(
            "/state/reset",
            self.reset_onboarding_state,
            methods=["DELETE"],
            summary="Reset onboarding state",
            description="Reset onboarding state to start over (admin/testing only)",
            response_model=V1ResponseModel
        )
        
        # Get onboarding analytics for user
        self.router.add_api_route(
            "/analytics",
            self.get_onboarding_analytics,
            methods=["GET"],
            summary="Get onboarding analytics",
            description="Get detailed analytics about onboarding progress and completion",
            response_model=V1ResponseModel
        )

    # Core Onboarding State Management
    async def get_onboarding_state(self, context: HTTPRoutingContext = Depends(self._require_si_role)):
        """Get current onboarding state for the authenticated user"""
        try:
            self.endpoint_stats["get_state_requests"] += 1
            self.endpoint_stats["total_requests"] += 1
            
            # Provide mock onboarding state while message router is being set up
            mock_result = {
                "current_step": "welcome",
                "completed_steps": [],
                "progress": 0,
                "total_steps": 5,
                "steps": {
                    "welcome": {"status": "current", "title": "Welcome to TaxPoynt"},
                    "business_info": {"status": "pending", "title": "Business Information"},
                    "banking_setup": {"status": "pending", "title": "Banking Integration"},
                    "testing": {"status": "pending", "title": "Test Integration"},
                    "complete": {"status": "pending", "title": "Go Live"}
                },
                "next_action": "Complete business information setup"
            }
            
            return self._create_v1_response(mock_result, "onboarding_state_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting onboarding state in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to get onboarding state")

    async def update_onboarding_state(self,
                                      request: Request,
                                      context: HTTPRoutingContext = Depends(self._require_si_role)):
        """Update onboarding state with new progress"""
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
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="update_onboarding_state",
                payload={
                    "user_id": context.user_id,
                    "onboarding_data": body,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "onboarding_state_updated")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating onboarding state in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to update onboarding state")

    async def complete_onboarding_step(self,
                                       step_name: str,
                                       request: Request,
                                       context: HTTPRoutingContext = Depends(self._require_si_role)):
        """Mark a specific onboarding step as complete"""
        try:
            body = await request.json() if hasattr(request, 'json') else {}
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="complete_onboarding_step",
                payload={
                    "user_id": context.user_id,
                    "step_name": step_name,
                    "metadata": body.get("metadata", {}),
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "onboarding_step_completed")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error completing onboarding step in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to complete onboarding step")

    async def complete_onboarding(self,
                                  request: Request,
                                  context: HTTPRoutingContext = Depends(self._require_si_role)):
        """Mark entire onboarding as complete"""
        try:
            body = await request.json() if hasattr(request, 'json') else {}
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="complete_onboarding",
                payload={
                    "user_id": context.user_id,
                    "completion_metadata": body.get("metadata", {}),
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "onboarding_completed")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error completing onboarding in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to complete onboarding")

    async def reset_onboarding_state(self, context: HTTPRoutingContext = Depends(self._require_si_role)):
        """Reset onboarding state (admin/testing only)"""
        try:
            self.endpoint_stats["reset_state_requests"] += 1
            self.endpoint_stats["total_requests"] += 1
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="reset_onboarding_state",
                payload={
                    "user_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "onboarding_state_reset")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error resetting onboarding state in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to reset onboarding state")

    async def get_onboarding_analytics(self, context: HTTPRoutingContext = Depends(self._require_si_role)):
        """Get onboarding analytics and progress insights"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_onboarding_analytics",
                payload={
                    "user_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "onboarding_analytics_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting onboarding analytics in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to get onboarding analytics")

    def _create_v1_response(self, data: Any, message: str, status_code: int = 200) -> V1ResponseModel:
        """Create standardized V1 response"""
        return build_v1_response(data, action=message)


def create_onboarding_router(
    role_detector: HTTPRoleDetector,
    permission_guard: APIPermissionGuard,
    message_router: MessageRouter
) -> APIRouter:
    """Factory function to create onboarding management router"""
    endpoints = OnboardingEndpointsV1(role_detector, permission_guard, message_router)
    return endpoints.router
