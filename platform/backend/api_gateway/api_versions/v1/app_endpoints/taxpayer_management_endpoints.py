"""
Taxpayer Management Endpoints - API v1
======================================
Access Point Provider endpoints for managing taxpayers in FIRS e-invoicing system.
Handles taxpayer onboarding, lifecycle management, and FIRS grant tracking.
"""
import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Request, HTTPException, Depends, status, Query, Path
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from core_platform.authentication.role_manager import PlatformRole
from core_platform.messaging.message_router import ServiceRole, MessageRouter
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from ..version_models import V1ResponseModel
from api_gateway.utils.v1_response import build_v1_response
from api_gateway.utils.error_mapping import v1_error_response
from .firs_request_models import (
    TaxpayerCreateRequest,
    TaxpayerUpdateRequest,
)

logger = logging.getLogger(__name__)


class TaxpayerManagementEndpointsV1:
    """
    Taxpayer Management Endpoints - Version 1
    ==========================================
    Manages taxpayer lifecycle for FIRS e-invoicing compliance:
    
    **Taxpayer Management Features:**
    - **Onboarding**: Register taxpayers for e-invoicing compliance
    - **Lifecycle Management**: Manage taxpayer status and information
    - **Grant Tracking**: Track FIRS grant milestones based on taxpayer onboarding
    - **Compliance Status**: Monitor taxpayer compliance with e-invoicing requirements
    - **Document Management**: Handle taxpayer documentation and certificates
    - **Bulk Operations**: Handle bulk taxpayer operations efficiently
    
    **FIRS Grant Context:**
    - TaxPoynt receives FIRS grants based on successful taxpayer onboarding
    - Grant milestones are tied to TaxPoynt's performance in onboarding organizations
    - Organizations are taxpayers being onboarded, not grant recipients
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(
            prefix="/taxpayers",
            tags=["Taxpayer Management V1"],
            dependencies=[Depends(self._require_app_role)]
        )
        
        # Define taxpayer management capabilities
        self.taxpayer_capabilities = {
            "onboarding": {
                "features": ["individual_onboarding", "bulk_onboarding", "automated_workflows"],
                "description": "Register and onboard taxpayers for e-invoicing compliance"
            },
            "lifecycle": {
                "features": ["status_management", "profile_updates", "deactivation"],
                "description": "Manage taxpayer lifecycle and status changes"
            },
            "compliance": {
                "features": ["compliance_monitoring", "requirement_tracking", "violation_management"],
                "description": "Monitor and manage taxpayer compliance status"
            },
            "grant_tracking": {
                "features": ["milestone_tracking", "performance_metrics", "reporting"],
                "description": "Track FIRS grant milestones based on taxpayer onboarding"
            }
        }
        
        self._setup_routes()
        logger.info("Taxpayer Management Endpoints V1 initialized")
    
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
        """Setup taxpayer management routes"""
        
        # Taxpayer Overview and Statistics
        self.router.add_api_route(
            "/overview",
            self.get_taxpayer_overview,
            methods=["GET"],
            summary="Get taxpayer overview",
            description="Get overview and statistics of managed taxpayers",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/statistics",
            self.get_taxpayer_statistics,
            methods=["GET"],
            summary="Get taxpayer statistics",
            description="Get detailed statistics on taxpayer onboarding and compliance",
            response_model=V1ResponseModel
        )
        
        # Frontend compatibility endpoint - maps to statistics
        self.router.add_api_route(
            "/metrics",
            self.get_taxpayer_metrics,
            methods=["GET"],
            summary="Get taxpayer metrics",
            description="Get taxpayer metrics (frontend compatibility endpoint)",
            response_model=V1ResponseModel
        )
        
        # Individual Taxpayer Management
        self.router.add_api_route(
            "",
            self.list_taxpayers,
            methods=["GET"],
            summary="List taxpayers",
            description="List all taxpayers managed by TaxPoynt APP",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "",
            self.create_taxpayer,
            methods=["POST"],
            summary="Create taxpayer",
            description="Register new taxpayer for e-invoicing compliance",
            response_model=V1ResponseModel,
            status_code=201
        )
        
        self.router.add_api_route(
            "/{taxpayer_id}",
            self.get_taxpayer,
            methods=["GET"],
            summary="Get taxpayer details",
            description="Get detailed information about a specific taxpayer",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{taxpayer_id}",
            self.update_taxpayer,
            methods=["PUT"],
            summary="Update taxpayer",
            description="Update taxpayer information and settings",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{taxpayer_id}",
            self.delete_taxpayer,
            methods=["DELETE"],
            summary="Delete taxpayer",
            description="Remove taxpayer from management (deactivate)",
            response_model=V1ResponseModel
        )
        
        # Frontend compatibility endpoint - status updates
        self.router.add_api_route(
            "/{taxpayer_id}/status",
            self.update_taxpayer_status,
            methods=["POST"],
            summary="Update taxpayer status",
            description="Update taxpayer status (frontend compatibility endpoint)",
            response_model=V1ResponseModel
        )
        
        # Taxpayer Onboarding Routes
        self.router.add_api_route(
            "/{taxpayer_id}/onboard",
            self.onboard_taxpayer,
            methods=["POST"],
            summary="Onboard taxpayer",
            description="Complete taxpayer onboarding process for e-invoicing",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{taxpayer_id}/onboarding-status",
            self.get_taxpayer_onboarding_status,
            methods=["GET"],
            summary="Get taxpayer onboarding status",
            description="Get current onboarding status and progress",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/bulk-onboard",
            self.bulk_onboard_taxpayers,
            methods=["POST"],
            summary="Bulk onboard taxpayers",
            description="Onboard multiple taxpayers in a single operation",
            response_model=V1ResponseModel
        )
        
        # Taxpayer Compliance Management
        self.router.add_api_route(
            "/{taxpayer_id}/compliance",
            self.get_taxpayer_compliance_status,
            methods=["GET"],
            summary="Get taxpayer compliance status",
            description="Get current compliance status for taxpayer",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{taxpayer_id}/compliance/update",
            self.update_taxpayer_compliance_status,
            methods=["POST"],
            summary="Update taxpayer compliance status",
            description="Update compliance status based on recent activities",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/compliance/non-compliant",
            self.list_non_compliant_taxpayers,
            methods=["GET"],
            summary="List non-compliant taxpayers",
            description="List taxpayers who are not meeting compliance requirements",
            response_model=V1ResponseModel
        )
        
        # Taxpayer Document Management
        self.router.add_api_route(
            "/{taxpayer_id}/documents",
            self.list_taxpayer_documents,
            methods=["GET"],
            summary="List taxpayer documents",
            description="List all documents for a taxpayer",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{taxpayer_id}/documents",
            self.upload_taxpayer_document,
            methods=["POST"],
            summary="Upload taxpayer document",
            description="Upload document for taxpayer",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{taxpayer_id}/documents/{document_id}",
            self.get_taxpayer_document,
            methods=["GET"],
            summary="Get taxpayer document",
            description="Get specific document for taxpayer",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{taxpayer_id}/documents/{document_id}",
            self.delete_taxpayer_document,
            methods=["DELETE"],
            summary="Delete taxpayer document",
            description="Remove document for taxpayer",
            response_model=V1ResponseModel
        )
        
        # Grant Tracking Routes
        self.router.add_api_route(
            "/grant-tracking/milestones",
            self.get_grant_milestones,
            methods=["GET"],
            summary="Get FIRS grant milestones",
            description="Get current FIRS grant milestones and progress",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/grant-tracking/performance",
            self.get_onboarding_performance,
            methods=["GET"],
            summary="Get onboarding performance metrics",
            description="Get performance metrics for taxpayer onboarding",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/grant-tracking/report",
            self.generate_grant_tracking_report,
            methods=["POST"],
            summary="Generate grant tracking report",
            description="Generate report for FIRS grant tracking",
            response_model=V1ResponseModel
        )
        
        # Bulk Operations Routes
        self.router.add_api_route(
            "/bulk/import",
            self.bulk_import_taxpayers,
            methods=["POST"],
            summary="Bulk import taxpayers",
            description="Import multiple taxpayers from external source",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/bulk/export",
            self.bulk_export_taxpayers,
            methods=["POST"],
            summary="Bulk export taxpayers",
            description="Export taxpayer data for reporting or backup",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/bulk/update-status",
            self.bulk_update_taxpayer_status,
            methods=["POST"],
            summary="Bulk update taxpayer status",
            description="Update status for multiple taxpayers",
            response_model=V1ResponseModel
        )
    
    # Taxpayer Overview Endpoints
    async def get_taxpayer_overview(self, request: Request):
        """Get taxpayer overview"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_taxpayer_overview",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            # Add capabilities information
            result["capabilities"] = self.taxpayer_capabilities
            
            return self._create_v1_response(result, "taxpayer_overview_retrieved")
        except Exception as e:
            logger.error(f"Error getting taxpayer overview in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get taxpayer overview")
    
    async def get_taxpayer_statistics(self, 
                                    request: Request,
                                    period: Optional[str] = Query("30d", description="Statistics period")):
        """Get taxpayer statistics"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_taxpayer_statistics",
                payload={
                    "app_id": context.user_id,
                    "period": period,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "taxpayer_statistics_retrieved")
        except Exception as e:
            logger.error(f"Error getting taxpayer statistics in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get taxpayer statistics")
    
    # Individual Taxpayer Management Endpoints
    async def list_taxpayers(self, 
                            request: Request,
                            status: Optional[str] = Query(None, description="Filter by taxpayer status"),
                            compliance_status: Optional[str] = Query(None, description="Filter by compliance status"),
                            onboarding_status: Optional[str] = Query(None, description="Filter by onboarding status"),
                            ):
        """List taxpayers"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="list_taxpayers",
                payload={
                    "app_id": context.user_id,
                    "filters": {
                        "status": status,
                        "compliance_status": compliance_status,
                        "onboarding_status": onboarding_status
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "taxpayers_listed")
        except Exception as e:
            logger.error(f"Error listing taxpayers in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to list taxpayers")
    
    async def create_taxpayer(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Create taxpayer"""
        try:
            context = context or await self._require_app_role(request)
            raw_body = await request.json()
            try:
                payload = TaxpayerCreateRequest.parse_obj(raw_body)
            except ValidationError as exc:
                return v1_error_response(ValueError(str(exc)), action="create_taxpayer")
            body = payload.dict(exclude_none=True)

            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="create_taxpayer",
                payload={
                    "taxpayer_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "taxpayer_created", status_code=201)
        except Exception as e:
            logger.error(f"Error creating taxpayer in v1: {e}")
            return v1_error_response(e, action="create_taxpayer")
    
    async def get_taxpayer(self, taxpayer_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get taxpayer details"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_taxpayer",
                payload={
                    "taxpayer_id": taxpayer_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            if not result:
                raise HTTPException(status_code=404, detail="Taxpayer not found")
            
            return self._create_v1_response(result, "taxpayer_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting taxpayer {taxpayer_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get taxpayer")
    
    async def update_taxpayer(self, taxpayer_id: str, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Update taxpayer"""
        try:
            context = context or await self._require_app_role(request)
            raw_body = await request.json()
            try:
                payload = TaxpayerUpdateRequest.parse_obj(raw_body)
            except ValidationError as exc:
                return v1_error_response(ValueError(str(exc)), action="update_taxpayer")
            body = payload.dict(exclude_none=True)

            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="update_taxpayer",
                payload={
                    "taxpayer_id": taxpayer_id,
                    "updates": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "taxpayer_updated")
        except Exception as e:
            logger.error(f"Error updating taxpayer {taxpayer_id} in v1: {e}")
            return v1_error_response(e, action="update_taxpayer")
    
    async def delete_taxpayer(self, taxpayer_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Delete taxpayer (deactivate)"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="delete_taxpayer",
                payload={
                    "taxpayer_id": taxpayer_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "taxpayer_deleted")
        except Exception as e:
            logger.error(f"Error deleting taxpayer {taxpayer_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete taxpayer")
    
    # Taxpayer Onboarding Endpoints
    async def onboard_taxpayer(self, taxpayer_id: str, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Onboard taxpayer"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="onboard_taxpayer",
                payload={
                    "taxpayer_id": taxpayer_id,
                    "onboarding_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "taxpayer_onboarded")
        except Exception as e:
            logger.error(f"Error onboarding taxpayer {taxpayer_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to onboard taxpayer")
    
    async def get_taxpayer_onboarding_status(self, taxpayer_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get taxpayer onboarding status"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_taxpayer_onboarding_status",
                payload={
                    "taxpayer_id": taxpayer_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "taxpayer_onboarding_status_retrieved")
        except Exception as e:
            logger.error(f"Error getting taxpayer onboarding status {taxpayer_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get taxpayer onboarding status")
    
    async def bulk_onboard_taxpayers(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Bulk onboard taxpayers"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="bulk_onboard_taxpayers",
                payload={
                    "bulk_onboarding_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "bulk_taxpayer_onboarding_initiated")
        except Exception as e:
            logger.error(f"Error bulk onboarding taxpayers in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to bulk onboard taxpayers")
    
    # Taxpayer Compliance Management Endpoints
    async def get_taxpayer_compliance_status(self, taxpayer_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get taxpayer compliance status"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_taxpayer_compliance_status",
                payload={
                    "taxpayer_id": taxpayer_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "taxpayer_compliance_status_retrieved")
        except Exception as e:
            logger.error(f"Error getting taxpayer compliance status {taxpayer_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get taxpayer compliance status")
    
    async def update_taxpayer_compliance_status(self, taxpayer_id: str, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Update taxpayer compliance status"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="update_taxpayer_compliance_status",
                payload={
                    "taxpayer_id": taxpayer_id,
                    "compliance_update": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "taxpayer_compliance_status_updated")
        except Exception as e:
            logger.error(f"Error updating taxpayer compliance status {taxpayer_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to update taxpayer compliance status")
    
    async def list_non_compliant_taxpayers(self, 
                                         request: Request,
                                         violation_type: Optional[str] = Query(None, description="Filter by violation type")):
        """List non-compliant taxpayers"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="list_non_compliant_taxpayers",
                payload={
                    "app_id": context.user_id,
                    "filters": {
                        "violation_type": violation_type
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "non_compliant_taxpayers_listed")
        except Exception as e:
            logger.error(f"Error listing non-compliant taxpayers in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to list non-compliant taxpayers")
    
    # Grant Tracking Endpoints
    async def get_grant_milestones(self, request: Request):
        """Get FIRS grant milestones"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_grant_milestones",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "grant_milestones_retrieved")
        except Exception as e:
            logger.error(f"Error getting grant milestones in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get grant milestones")
    
    async def get_onboarding_performance(self, 
                                       request: Request,
                                       period: Optional[str] = Query("30d", description="Performance period")):
        """Get onboarding performance metrics"""
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
            raise HTTPException(status_code=500, detail="Failed to get onboarding performance")
    
    async def generate_grant_tracking_report(self, request: Request):
        """Generate grant tracking report"""
        try:
            context = await self._require_app_role(request)
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="generate_grant_tracking_report",
                payload={
                    "report_config": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "grant_tracking_report_generated")
        except Exception as e:
            logger.error(f"Error generating grant tracking report in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate grant tracking report")
    
    # Placeholder implementations for remaining endpoints
    async def list_taxpayer_documents(self, taxpayer_id: str):
        """List taxpayer documents - placeholder"""
        return self._create_v1_response({"documents": []}, "taxpayer_documents_listed")

    async def upload_taxpayer_document(self, taxpayer_id: str, request: Request):
        """Upload taxpayer document - placeholder"""
        return self._create_v1_response({"document_id": "doc_123"}, "taxpayer_document_uploaded")

    async def get_taxpayer_document(self, taxpayer_id: str, document_id: str):
        """Get taxpayer document - placeholder"""
        return self._create_v1_response({"document_id": document_id}, "taxpayer_document_retrieved")

    async def delete_taxpayer_document(self, taxpayer_id: str, document_id: str):
        """Delete taxpayer document - placeholder"""
        return self._create_v1_response({"document_id": document_id}, "taxpayer_document_deleted")

    async def bulk_import_taxpayers(self, request: Request):
        """Bulk import taxpayers - placeholder"""
        return self._create_v1_response({"import_id": "import_123"}, "bulk_taxpayer_import_initiated")

    async def bulk_export_taxpayers(self, request: Request):
        """Bulk export taxpayers - placeholder"""
        return self._create_v1_response({"export_id": "export_123"}, "bulk_taxpayer_export_initiated")

    async def bulk_update_taxpayer_status(self, request: Request):
        """Bulk update taxpayer status - placeholder"""
        return self._create_v1_response({"update_id": "update_123"}, "bulk_taxpayer_status_update_initiated")
    
    # Frontend Compatibility Endpoints
    async def get_taxpayer_metrics(self, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get taxpayer metrics (frontend compatibility endpoint)"""
        try:
            # This maps to the statistics endpoint for frontend compatibility
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_taxpayer_statistics",
                payload={
                    "app_id": context.user_id,
                    "period": "current",
                    "api_version": "v1"
                }
            )
            
            # Add demo data if service not available
            if not result:
                result = {
                    "total": 1247,
                    "active": 1180,
                    "pending": 45,
                    "suspended": 22,
                    "onboardedThisMonth": 89,
                    "complianceRate": 96.2
                }
            
            return self._create_v1_response(result, "taxpayer_metrics_retrieved")
        except Exception as e:
            logger.error(f"Error getting taxpayer metrics in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get taxpayer metrics")
    
    async def update_taxpayer_status(self, taxpayer_id: str, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Update taxpayer status (frontend compatibility endpoint)"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="update_taxpayer",
                payload={
                    "taxpayer_id": taxpayer_id,
                    "updates": {"status": body.get("status"), "reason": body.get("reason", "Status updated via API")},
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "taxpayer_status_updated")
        except Exception as e:
            logger.error(f"Error updating taxpayer status {taxpayer_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to update taxpayer status")
    
    def _create_v1_response(self, data: Dict[str, Any], action: str, status_code: int = 200) -> V1ResponseModel:
        """Create standardized v1 response format using V1ResponseModel"""
        return build_v1_response(data, action)


def create_taxpayer_management_router(role_detector: HTTPRoleDetector,
                                     permission_guard: APIPermissionGuard,
                                     message_router: MessageRouter) -> APIRouter:
    """Factory function to create Taxpayer Management Router"""
    taxpayer_endpoints = TaxpayerManagementEndpointsV1(role_detector, permission_guard, message_router)
    return taxpayer_endpoints.router
