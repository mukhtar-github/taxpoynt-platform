"""
Compliance and Reporting Endpoints - API v1
============================================
System Integrator endpoints for compliance validation and reporting.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse

from core_platform.messaging.message_router import ServiceRole, MessageRouter
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from .version_models import V1ResponseModel
from api_gateway.utils.v1_response import build_v1_response
from core_platform.authentication.role_manager import PlatformRole

logger = logging.getLogger(__name__)


class ComplianceEndpointsV1:
    """Compliance and Reporting Endpoints - Version 1"""
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(
            prefix="/compliance",
            tags=["Compliance V1"],
            dependencies=[Depends(self._require_si_role)]
        )
        
        self._setup_routes()
        logger.info("Compliance Endpoints V1 initialized")
    
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
        """Setup compliance and reporting routes"""
        
        self.router.add_api_route(
            "/validate",
            self.validate_compliance,
            methods=["POST"],
            summary="Validate compliance",
            description="Validate transaction or data compliance",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/reports/onboarding",
            self.get_onboarding_report,
            methods=["GET"],
            summary="Get onboarding report",
            description="Generate organization onboarding report",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/reports/transactions",
            self.get_transaction_compliance_report,
            methods=["GET"],
            summary="Get transaction compliance report",
            description="Generate transaction compliance report",
            response_model=V1ResponseModel
        )
    
    # Routed implementations
    async def validate_compliance(
        self,
        request: Request,
        organization_id: Optional[str] = Query(None, description="Scope validation by organization ID"),
        context: HTTPRoutingContext = Depends(self._require_si_role),
    ):
        """Validate compliance via validation services"""
        try:
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="check_kyc_compliance",
                payload={
                    "validation_payload": body,
                    "si_id": context.user_id,
                    "api_version": "v1",
                    "organization_id": organization_id,
                }
            )
            return self._create_v1_response(result, "compliance_validated")
        except Exception as e:
            logger.error(f"Error validating compliance in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to validate compliance")
    
    async def get_onboarding_report(
        self,
        request: Request,
        organization_id: Optional[str] = Query(None, description="Scope report by organization ID"),
        context: HTTPRoutingContext = Depends(self._require_si_role),
    ):
        """Get onboarding report via reporting services"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="generate_onboarding_report",
                payload={
                    "si_id": context.user_id,
                    "api_version": "v1",
                    "organization_id": organization_id,
                }
            )
            return self._create_v1_response(result, "onboarding_report_generated")
        except Exception as e:
            logger.error(f"Error generating onboarding report in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate onboarding report")

    async def get_transaction_compliance_report(
        self,
        request: Request,
        organization_id: Optional[str] = Query(None, description="Scope report by organization ID"),
        start_date: Optional[str] = Query(None, description="Start date (ISO 8601)"),
        end_date: Optional[str] = Query(None, description="End date (ISO 8601)"),
        include_metrics: bool = Query(True, description="Include metrics breakdowns (daily counts, status histogram)"),
        context: HTTPRoutingContext = Depends(self._require_si_role),
    ):
        """Get transaction compliance report via reporting services"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="generate_transaction_compliance_report",
                payload={
                    "si_id": context.user_id,
                    "api_version": "v1",
                    "organization_id": organization_id,
                    "start_date": start_date,
                    "end_date": end_date,
                    "include_metrics": include_metrics,
                }
            )
            return self._create_v1_response(result, "compliance_report_generated")
        except Exception as e:
            logger.error(f"Error generating transaction compliance report in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate transaction compliance report")
    
    def _create_v1_response(self, data: Dict[str, Any], action: str, status_code: int = 200) -> V1ResponseModel:
        """Create standardized v1 response format using V1ResponseModel"""
        return build_v1_response(data, action)


def create_compliance_router(role_detector: HTTPRoleDetector,
                            permission_guard: APIPermissionGuard,
                            message_router: MessageRouter) -> APIRouter:
    """Factory function to create Compliance Router"""
    compliance_endpoints = ComplianceEndpointsV1(role_detector, permission_guard, message_router)
    return compliance_endpoints.router
