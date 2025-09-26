"""
Certificate Management Endpoints - API v1
==========================================
Access Point Provider endpoints for managing FIRS certificates and authentication.
Handles certificate lifecycle, renewal, and security management.
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


class CertificateManagementEndpointsV1:
    """
    Certificate Management Endpoints - Version 1
    =============================================
    Manages FIRS certificates and authentication credentials:
    
    **Certificate Management Features:**
    - **Certificate Lifecycle**: Create, renew, revoke, and manage certificates
    - **Authentication Management**: Handle FIRS authentication credentials
    - **Security Monitoring**: Monitor certificate health and security status
    - **Compliance Tracking**: Ensure certificate compliance with FIRS requirements
    - **Automated Renewal**: Handle automated certificate renewal processes
    - **Backup and Recovery**: Manage certificate backup and recovery procedures
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(
            prefix="/certificates",
            tags=["Certificate Management V1"],
            dependencies=[Depends(self._require_app_role)]
        )
        
        self._setup_routes()
        logger.info("Certificate Management Endpoints V1 initialized")
    
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
        """Setup certificate management routes"""
        
        # Certificate Overview Routes
        self.router.add_api_route(
            "/overview",
            self.get_certificate_overview,
            methods=["GET"],
            summary="Get certificate overview",
            description="Get overview of all managed certificates",
            response_model=V1ResponseModel
        )
        
        # Certificate Lifecycle Routes
        self.router.add_api_route(
            "",
            self.list_certificates,
            methods=["GET"],
            summary="List certificates",
            description="List all FIRS certificates",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "",
            self.create_certificate,
            methods=["POST"],
            summary="Create certificate",
            description="Create new FIRS certificate",
            response_model=V1ResponseModel,
            status_code=201
        )
        
        self.router.add_api_route(
            "/{certificate_id}",
            self.get_certificate,
            methods=["GET"],
            summary="Get certificate details",
            description="Get detailed information about a specific certificate",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{certificate_id}",
            self.update_certificate,
            methods=["PUT"],
            summary="Update certificate",
            description="Update certificate information and settings",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{certificate_id}",
            self.delete_certificate,
            methods=["DELETE"],
            summary="Delete certificate",
            description="Remove certificate (revoke)",
            response_model=V1ResponseModel
        )
        
        # Certificate Renewal Routes
        self.router.add_api_route(
            "/{certificate_id}/renew",
            self.renew_certificate,
            methods=["POST"],
            summary="Renew certificate",
            description="Renew expiring certificate",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{certificate_id}/renewal-status",
            self.get_renewal_status,
            methods=["GET"],
            summary="Get renewal status",
            description="Get certificate renewal status",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/expiring",
            self.list_expiring_certificates,
            methods=["GET"],
            summary="List expiring certificates",
            description="List certificates that are expiring soon",
            response_model=V1ResponseModel
        )
        
        # Certificate Security Routes
        self.router.add_api_route(
            "/{certificate_id}/security-status",
            self.get_certificate_security_status,
            methods=["GET"],
            summary="Get certificate security status",
            description="Get security status and health of certificate",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{certificate_id}/validate",
            self.validate_certificate,
            methods=["POST"],
            summary="Validate certificate",
            description="Validate certificate integrity and authenticity",
            response_model=V1ResponseModel
        )
        
        # Certificate Backup Routes
        self.router.add_api_route(
            "/{certificate_id}/backup",
            self.backup_certificate,
            methods=["POST"],
            summary="Backup certificate",
            description="Create secure backup of certificate",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{certificate_id}/restore",
            self.restore_certificate,
            methods=["POST"],
            summary="Restore certificate",
            description="Restore certificate from backup",
            response_model=V1ResponseModel
        )
    
    # Certificate Overview Endpoints
    async def get_certificate_overview(self, request: Request):
        """Get certificate overview"""
        try:
            context = await self._require_app_role(request)
            org_id = str(context.organization_id) if context.organization_id else None
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_certificate_overview",
                payload={
                    "app_id": context.user_id,
                    "organization_id": org_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "certificate_overview_retrieved")
        except Exception as e:
            logger.error(f"Error getting certificate overview in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get certificate overview")
    
    # Certificate Lifecycle Endpoints
    async def list_certificates(self, 
                              request: Request,
                              status: Optional[str] = Query(None, description="Filter by certificate status")):
        """List certificates"""
        try:
            context = await self._require_app_role(request)
            org_id = str(context.organization_id) if context.organization_id else None
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="list_certificates",
                payload={
                    "app_id": context.user_id,
                    "organization_id": org_id,
                    "filters": {
                        "status": status,
                        "organization_id": org_id,
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "certificates_listed")
        except Exception as e:
            logger.error(f"Error listing certificates in v1: {e}")
            return v1_error_response(e, action="list_certificates")
    
    async def create_certificate(self, request: Request):
        """Create certificate"""
        try:
            context = await self._require_app_role(request)
            body = await request.json()
            org_id = str(context.organization_id) if context.organization_id else None
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="create_certificate",
                payload={
                    "certificate_data": body,
                    "app_id": context.user_id,
                    "organization_id": org_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "certificate_created", status_code=201)
        except Exception as e:
            logger.error(f"Error creating certificate in v1: {e}")
            return v1_error_response(e, action="create_certificate")
    
    async def get_certificate(self, certificate_id: str, request: Request):
        """Get certificate details"""
        try:
            context = await self._require_app_role(request)
            org_id = str(context.organization_id) if context.organization_id else None
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_certificate",
                payload={
                    "certificate_id": certificate_id,
                    "app_id": context.user_id,
                    "organization_id": org_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "certificate_retrieved")
        except Exception as e:
            logger.error(f"Error getting certificate {certificate_id} in v1: {e}")
            return v1_error_response(e, action="get_certificate")
    
    async def update_certificate(self, certificate_id: str, request: Request):
        """Update certificate"""
        try:
            context = await self._require_app_role(request)
            body = await request.json()
            org_id = str(context.organization_id) if context.organization_id else None
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="update_certificate",
                payload={
                    "certificate_id": certificate_id,
                    "updates": body,
                    "app_id": context.user_id,
                    "organization_id": org_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "certificate_updated")
        except Exception as e:
            logger.error(f"Error updating certificate {certificate_id} in v1: {e}")
            return v1_error_response(e, action="update_certificate")
    
    async def delete_certificate(self, certificate_id: str, request: Request):
        """Delete certificate (revoke)"""
        try:
            context = await self._require_app_role(request)
            org_id = str(context.organization_id) if context.organization_id else None
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="delete_certificate",
                payload={
                    "certificate_id": certificate_id,
                    "app_id": context.user_id,
                    "organization_id": org_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "certificate_deleted")
        except Exception as e:
            logger.error(f"Error deleting certificate {certificate_id} in v1: {e}")
            return v1_error_response(e, action="delete_certificate")
    
    # Certificate Renewal Endpoints
    async def renew_certificate(self, certificate_id: str, request: Request):
        """Renew certificate"""
        try:
            context = await self._require_app_role(request)
            org_id = str(context.organization_id) if context.organization_id else None
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="renew_certificate",
                payload={
                    "certificate_id": certificate_id,
                    "app_id": context.user_id,
                    "organization_id": org_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "certificate_renewed")
        except Exception as e:
            logger.error(f"Error renewing certificate {certificate_id} in v1: {e}")
            return v1_error_response(e, action="renew_certificate")
    
    async def get_renewal_status(self, certificate_id: str, request: Request):
        """Get renewal status"""
        try:
            context = await self._require_app_role(request)
            org_id = str(context.organization_id) if context.organization_id else None
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_renewal_status",
                payload={
                    "certificate_id": certificate_id,
                    "app_id": context.user_id,
                    "organization_id": org_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "renewal_status_retrieved")
        except Exception as e:
            logger.error(f"Error getting renewal status {certificate_id} in v1: {e}")
            return v1_error_response(e, action="get_renewal_status")
    
    async def list_expiring_certificates(self, 
                                       request: Request,
                                       days_ahead: Optional[int] = Query(30, description="Days ahead to check for expiration")):
        """List expiring certificates"""
        try:
            context = await self._require_app_role(request)
            org_id = str(context.organization_id) if context.organization_id else None
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="list_expiring_certificates",
                payload={
                    "app_id": context.user_id,
                    "days_ahead": days_ahead,
                    "organization_id": org_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "expiring_certificates_listed")
        except Exception as e:
            logger.error(f"Error listing expiring certificates in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to list expiring certificates")
    
    # Placeholder implementations for remaining endpoints
    async def get_certificate_security_status(self, certificate_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get certificate security status - placeholder"""
        return self._create_v1_response({"security_status": "secure"}, "certificate_security_status_retrieved")
    
    async def validate_certificate(self, certificate_id: str, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Validate certificate - placeholder"""
        return self._create_v1_response({"validation_result": "valid"}, "certificate_validated")
    
    async def backup_certificate(self, certificate_id: str, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Backup certificate - placeholder"""
        return self._create_v1_response({"backup_id": "backup_123"}, "certificate_backed_up")
    
    async def restore_certificate(self, certificate_id: str, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Restore certificate - placeholder"""
        return self._create_v1_response({"restore_id": "restore_123"}, "certificate_restored")
    
    def _create_v1_response(self, data: Dict[str, Any], action: str, status_code: int = 200) -> V1ResponseModel:
        """Create standardized v1 response format using V1ResponseModel"""
        return build_v1_response(data, action)


def create_certificate_management_router(role_detector: HTTPRoleDetector,
                                        permission_guard: APIPermissionGuard,
                                        message_router: MessageRouter) -> APIRouter:
    """Factory function to create Certificate Management Router"""
    certificate_endpoints = CertificateManagementEndpointsV1(role_detector, permission_guard, message_router)
    return certificate_endpoints.router
