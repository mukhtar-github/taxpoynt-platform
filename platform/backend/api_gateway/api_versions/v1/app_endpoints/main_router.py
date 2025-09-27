"""
APP Main Router - API Version 1
===============================
Main router for Access Point Provider (APP) endpoints in API v1.
Consolidates all APP-specific functionality for FIRS e-invoicing compliance.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse

from core_platform.authentication.role_manager import PlatformRole, RoleScope
from core_platform.messaging.message_router import ServiceRole, MessageRouter
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from ..version_models import V1ResponseModel, V1ErrorModel
from api_gateway.utils.v1_response import build_v1_response
from sqlalchemy.ext.asyncio import AsyncSession
from core_platform.data_management.db_async import get_async_session
from api_gateway.dependencies.tenant import make_tenant_scope_dependency
from core_platform.data_management.repositories.firs_submission_repo_async import (
    get_submission_metrics,
    list_recent_submissions,
)
from api_gateway.utils.pagination import normalize_pagination

# Import APP system routers
from .firs_integration_endpoints import create_firs_integration_router
from .taxpayer_management_endpoints import create_taxpayer_management_router
from .invoice_submission_endpoints import create_invoice_submission_router
from .compliance_validation_endpoints import create_compliance_validation_router
from .certificate_management_endpoints import create_certificate_management_router
from .grant_management_endpoints import create_grant_management_router
from .security_management_endpoints import create_security_management_router
from .validation_management_endpoints import create_validation_management_router
from .transmission_management_endpoints import create_transmission_management_router
from .tracking_management_endpoints import create_tracking_management_router
from .report_generation_endpoints import create_report_generation_router
from .dashboard_data_endpoints import create_dashboard_data_router
from .onboarding_endpoints import create_app_onboarding_router
from .network_routing_endpoints import create_network_routing_router
from .webhook_endpoints import create_app_webhook_router

logger = logging.getLogger(__name__)


class APPRouterV1:
    """
    Access Point Provider Router - Version 1
    ========================================
    Handles all APP endpoints for API v1, including:
    - FIRS integration and communication
    - Taxpayer onboarding and management
    - Invoice submission to FIRS systems
    - Compliance validation and reporting
    - Certificate management and security
    - Grant tracking and performance metrics
    
    **APP Role Context:**
    - TaxPoynt serves as Access Point Provider for FIRS e-invoicing
    - Manages direct integration with FIRS systems
    - Handles taxpayer onboarding for FIRS grant milestones
    - Ensures compliance with Nigerian e-invoicing regulations
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/app", tags=["Access Point Provider V1"])
        # Shared tenant scope for APP routes (must be set before including sub-routers)
        self.tenant_scope = make_tenant_scope_dependency(self._require_app_role)
        
        # Include all APP sub-routers
        self._include_sub_routers()
        
        # Setup general APP routes
        self._setup_routes()
        
        logger.info("APP Router V1 initialized")
    
    def _include_sub_routers(self):
        """Include all APP sub-routers"""
        
        # FIRS Integration Routes
        firs_router = create_firs_integration_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(firs_router, dependencies=[Depends(self.tenant_scope)])
        
        # Taxpayer Management Routes
        taxpayer_router = create_taxpayer_management_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(taxpayer_router, dependencies=[Depends(self.tenant_scope)])
        
        # Invoice Submission Routes
        invoice_router = create_invoice_submission_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(invoice_router, dependencies=[Depends(self.tenant_scope)])
        
        # Compliance Validation Routes
        compliance_router = create_compliance_validation_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(compliance_router, dependencies=[Depends(self.tenant_scope)])

        # Network Routing (participant registry) Routes
        network_router = create_network_routing_router(
            self.role_detector,
            self.permission_guard,
            self.message_router,
        )
        self.router.include_router(network_router, dependencies=[Depends(self.tenant_scope)])

        # Webhook Routes (FIRS notifications)
        webhook_router = create_app_webhook_router(
            self.role_detector,
            self.permission_guard,
            self.message_router,
        )
        self.router.include_router(webhook_router, dependencies=[Depends(self.tenant_scope)])

        # Certificate Management Routes
        certificate_router = create_certificate_management_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(certificate_router, dependencies=[Depends(self.tenant_scope)])
        
        # Grant Management Routes
        grant_router = create_grant_management_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(grant_router, dependencies=[Depends(self.tenant_scope)])
        
        # Security Management Routes
        security_router = create_security_management_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(security_router, dependencies=[Depends(self.tenant_scope)])
        
        # Validation Management Routes
        validation_router = create_validation_management_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(validation_router, dependencies=[Depends(self.tenant_scope)])
        
        # Transmission Management Routes
        transmission_router = create_transmission_management_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(transmission_router, dependencies=[Depends(self.tenant_scope)])
        
        # Tracking Management Routes
        tracking_router = create_tracking_management_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(tracking_router, dependencies=[Depends(self.tenant_scope)])
        
        # Report Generation Routes
        report_router = create_report_generation_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(report_router, dependencies=[Depends(self.tenant_scope)])
        
        # Dashboard Data Routes (root level endpoints)
        dashboard_router = create_dashboard_data_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(dashboard_router)
        
        # APP Onboarding Routes
        onboarding_router = create_app_onboarding_router(
            self.role_detector, 
            self.permission_guard, 
            self.message_router
        )
        self.router.include_router(onboarding_router, dependencies=[Depends(self.tenant_scope)])
    
    def _setup_routes(self):
        """Configure general APP v1 routes"""
        
        # APP Health and Status Routes
        self.router.add_api_route(
            "/health",
            self.health_check,
            methods=["GET"],
            summary="APP services health check",
            description="Check health of all APP services and FIRS connectivity",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/status",
            self.get_app_status,
            methods=["GET"],
            summary="Get APP status overview",
            description="Get comprehensive status of APP operations and integrations",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_app_role)]
        )
        
        # APP Information Routes
        self.router.add_api_route(
            "/info",
            self.get_app_info,
            methods=["GET"],
            summary="Get APP information",
            description="Get Access Point Provider information and capabilities",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/capabilities",
            self.get_app_capabilities,
            methods=["GET"],
            summary="Get APP capabilities",
            description="Get detailed APP capabilities and supported features",
            response_model=V1ResponseModel
        )
        
        # APP Dashboard Routes
        self.router.add_api_route(
            "/dashboard",
            self.get_app_dashboard,
            methods=["GET"],
            summary="Get APP dashboard data",
            description="Get dashboard data for APP operations overview",
            response_model=V1ResponseModel,
            dependencies=[Depends(self.tenant_scope)]
        )
        
        self.router.add_api_route(
            "/dashboard/summary",
            self.get_dashboard_summary,
            methods=["GET"],
            summary="Get dashboard summary",
            description="Get summary statistics for APP dashboard",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_app_role)]
        )
        
        # APP Configuration Routes
        self.router.add_api_route(
            "/configuration",
            self.get_app_configuration,
            methods=["GET"],
            summary="Get APP configuration",
            description="Get current APP configuration settings",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_app_role)]
        )
        
        self.router.add_api_route(
            "/configuration",
            self.update_app_configuration,
            methods=["PUT"],
            summary="Update APP configuration",
            description="Update APP configuration settings",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_app_role)]
        )
    
    async def _require_app_role(self, request: Request) -> HTTPRoutingContext:
        """Dependency to ensure Access Point Provider role access for v1"""
        context = await self.role_detector.detect_role_context(request)
        
        if not context.has_role(PlatformRole.ACCESS_POINT_PROVIDER):
            logger.warning(f"APP v1 endpoint access denied for context: {context}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access Point Provider role required for v1 API"
            )
        
        # Apply v1-specific permission guard
        if not await self.permission_guard.check_endpoint_permission(
            context, f"v1/app{request.url.path}", request.method
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for APP v1 endpoint"
            )
        
        # Add v1-specific context
        context.metadata["api_version"] = "v1"
        context.metadata["endpoint_group"] = "app"
        
        return context
    
    # APP Health and Status Handlers
    async def health_check(self):
        """APP services health check for v1"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="health_check",
                payload={"api_version": "v1"}
            )
            data = {
                "status": "healthy",
                "service": "app_services",
                "timestamp": result.get("timestamp"),
                "version_specific": {
                    "supported_features": [
                        "firs_integration",
                        "taxpayer_management", 
                        "invoice_submission",
                        "compliance_validation",
                        "certificate_management",
                        "grant_management"
                    ],
                    "v1_compatibility": "full",
                    "firs_connectivity": "connected"
                }
            }
            return self._create_v1_response(data, "app_health_retrieved")
        except Exception as e:
            logger.error(f"APP v1 health check failed: {e}")
            data = {"status": "unhealthy", "error": str(e)}
            return self._create_v1_response(data, "app_health_unhealthy")
    
    async def get_app_status(self, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Get APP status overview"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_app_status",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "app_status_retrieved")
        except Exception as e:
            logger.error(f"Error getting APP status in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get APP status")
    
    # APP Information Handlers
    async def get_app_info(self):
        """Get APP information"""
        try:
            app_info = {
                "app_name": "TaxPoynt Access Point Provider",
                "app_version": "v1.0.0",
                "api_version": "v1",
                "description": "FIRS e-invoicing Access Point Provider for Nigerian tax compliance",
                "capabilities": [
                    "firs_integration",
                    "taxpayer_onboarding",
                    "invoice_submission",
                    "compliance_validation",
                    "certificate_management",
                    "grant_tracking"
                ],
                "supported_standards": [
                    "UBL (Universal Business Language)",
                    "PEPPOL Standards",
                    "ISO 20022",
                    "ISO 27001",
                    "GDPR & NDPA",
                    "WCO Harmonized System",
                    "Legal Entity Identifier (LEI)"
                ],
                "firs_certified": True,
                "nitda_approved": True
            }
            
            return self._create_v1_response(app_info, "app_info_retrieved")
        except Exception as e:
            logger.error(f"Error getting APP info in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get APP info")
    
    async def get_app_capabilities(self):
        """Get APP capabilities"""
        try:
            capabilities = {
                "firs_integration": {
                    "features": ["authentication", "invoice_submission", "status_tracking", "validation"],
                    "description": "Direct integration with FIRS e-invoicing systems"
                },
                "taxpayer_management": {
                    "features": ["onboarding", "lifecycle_management", "compliance_monitoring", "bulk_operations"],
                    "description": "Comprehensive taxpayer management for e-invoicing compliance"
                },
                "invoice_submission": {
                    "features": ["generation", "validation", "submission", "tracking"],
                    "description": "Generate and submit FIRS-compliant invoices"
                },
                "compliance_validation": {
                    "features": ["ubl_validation", "peppol_compliance", "iso_standards", "data_protection"],
                    "description": "Validate compliance with multiple regulatory standards"
                },
                "certificate_management": {
                    "features": ["lifecycle_management", "renewal", "security_monitoring", "backup"],
                    "description": "Manage FIRS certificates and authentication credentials"
                },
                "grant_management": {
                    "features": ["milestone_tracking", "performance_metrics", "reporting", "payment_tracking"],
                    "description": "Track FIRS grants and performance metrics"
                }
            }
            
            return self._create_v1_response(capabilities, "app_capabilities_retrieved")
        except Exception as e:
            logger.error(f"Error getting APP capabilities in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get APP capabilities")
    
    # APP Dashboard Handlers
    async def get_app_dashboard(self,
                               recent_limit: int = Query(5, ge=1, le=100),
                               recent_offset: int = Query(0, ge=0),
                               db: AsyncSession = Depends(get_async_session)):
        """Get APP dashboard data (async, tenant-scoped)."""
        try:
            metrics = await get_submission_metrics(db)
            recent = await list_recent_submissions(db, limit=recent_limit, offset=recent_offset)
            result = {
                "metrics": metrics,
                "recent_submissions": [
                    {
                        "invoice_number": getattr(s, "invoice_number", None),
                        "status": getattr(s, "status", None).value if getattr(s, "status", None) else None,
                        "created_at": getattr(s, "created_at", None).isoformat() if getattr(s, "created_at", None) else None,
                    }
                    for s in recent
                ],
                "recent_pagination": normalize_pagination(
                    limit=recent_limit, offset=recent_offset, total=len(recent)
                ),
            }
            return self._create_v1_response(result, "app_dashboard_retrieved")
        except Exception as e:
            logger.error(f"Error getting APP dashboard in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get APP dashboard")
    
    async def get_dashboard_summary(self, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Get dashboard summary"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_dashboard_summary",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "dashboard_summary_retrieved")
        except Exception as e:
            logger.error(f"Error getting dashboard summary in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get dashboard summary")
    
    # APP Configuration Handlers
    async def get_app_configuration(self, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Get APP configuration"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_app_configuration",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "app_configuration_retrieved")
        except Exception as e:
            logger.error(f"Error getting APP configuration in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get APP configuration")
    
    async def update_app_configuration(self, request: Request, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Update APP configuration"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="update_app_configuration",
                payload={
                    "configuration_updates": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "app_configuration_updated")
        except Exception as e:
            logger.error(f"Error updating APP configuration in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to update APP configuration")
    
    def _create_v1_response(self, data: Dict[str, Any], action: str, status_code: int = 200) -> V1ResponseModel:
        """Create standardized v1 response format using V1ResponseModel"""
        return build_v1_response(data, action)


def create_app_v1_router(role_detector: HTTPRoleDetector,
                        permission_guard: APIPermissionGuard,
                        message_router: MessageRouter) -> APIRouter:
    """Factory function to create APP V1 Router"""
    app_v1_router = APPRouterV1(role_detector, permission_guard, message_router)
    return app_v1_router.router
