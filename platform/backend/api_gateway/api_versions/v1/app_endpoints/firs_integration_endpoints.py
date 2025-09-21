"""
FIRS Integration Endpoints - API v1
===================================
Access Point Provider endpoints for direct FIRS system integration.
Handles communication with FIRS e-invoicing infrastructure.
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
from api_gateway.utils.pagination import normalize_pagination

logger = logging.getLogger(__name__)


class FIRSIntegrationEndpointsV1:
    """
    FIRS Integration Endpoints - Version 1
    ======================================
    Manages direct integration with FIRS e-invoicing systems:
    
    **FIRS Integration Features:**
    - **Authentication**: FIRS API authentication and token management
    - **Invoice Submission**: Submit invoices directly to FIRS systems
    - **Status Tracking**: Track invoice processing status in FIRS
    - **Compliance Validation**: Validate invoices against FIRS rules
    - **Certificate Management**: Handle FIRS certificates and credentials
    - **System Health**: Monitor FIRS system availability and performance
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(
            prefix="/firs",
            tags=["FIRS Integration V1"],
            dependencies=[Depends(self._require_app_role)]
        )
        
        # Define FIRS integration capabilities
        self.firs_capabilities = {
            "authentication": {
                "features": ["oauth2_flow", "token_management", "certificate_auth"],
                "description": "FIRS API authentication and credential management"
            },
            "invoice_submission": {
                "features": ["individual_submission", "batch_submission", "real_time_processing"],
                "description": "Submit invoices to FIRS e-invoicing systems"
            },
            "validation": {
                "features": ["schema_validation", "business_rules", "compliance_check"],
                "description": "Validate invoices against FIRS requirements"
            },
            "tracking": {
                "features": ["submission_status", "processing_status", "error_tracking"],
                "description": "Track invoice processing in FIRS systems"
            }
        }
        
        self._setup_routes()
        logger.info("FIRS Integration Endpoints V1 initialized")
    
    async def _require_app_role(self, request: Request) -> HTTPRoutingContext:
        """Local guard to enforce Access Point Provider role and permissions."""
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
        """Setup FIRS integration routes"""
        
        # FIRS System Information
        self.router.add_api_route(
            "/system/info",
            self.get_firs_system_info,
            methods=["GET"],
            summary="Get FIRS system information",
            description="Get FIRS e-invoicing system information and capabilities",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/system/health",
            self.check_firs_system_health,
            methods=["GET"],
            summary="Check FIRS system health",
            description="Check FIRS system availability and performance",
            response_model=V1ResponseModel
        )
        
        # FIRS Authentication Routes
        self.router.add_api_route(
            "/auth/authenticate",
            self.authenticate_with_firs,
            methods=["POST"],
            summary="Authenticate with FIRS",
            description="Authenticate TaxPoynt APP with FIRS systems",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/auth/refresh-token",
            self.refresh_firs_token,
            methods=["POST"],
            summary="Refresh FIRS authentication token",
            description="Refresh authentication token for FIRS integration",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/auth/status",
            self.get_firs_auth_status,
            methods=["GET"],
            summary="Get FIRS authentication status",
            description="Get current FIRS authentication status and token validity",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/test-connection",
            self.test_firs_connection,
            methods=["POST"],
            summary="Test FIRS connection",
            description="Test connection to FIRS with provided credentials",
            response_model=V1ResponseModel
        )
        
        # Invoice Submission Routes
        self.router.add_api_route(
            "/invoices/submit",
            self.submit_invoice_to_firs,
            methods=["POST"],
            summary="Submit invoice to FIRS",
            description="Submit individual invoice to FIRS e-invoicing system",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/invoices/submit-batch",
            self.submit_invoice_batch_to_firs,
            methods=["POST"],
            summary="Submit invoice batch to FIRS",
            description="Submit multiple invoices to FIRS in a single batch",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/invoices/{submission_id}/status",
            self.get_firs_submission_status,
            methods=["GET"],
            summary="Get FIRS submission status",
            description="Get processing status of invoice submission in FIRS",
            response_model=V1ResponseModel
        )

        # Transmit (mirror FIRS) - POST transmit
        self.router.add_api_route(
            "/invoices/transmit/{irn}",
            self.transmit_firs_invoice,
            methods=["POST"],
            summary="Transmit invoice by IRN",
            description="Transmit an already signed invoice to FIRS by IRN (mirrors FIRS POST /invoice/transmit/{IRN})",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_app_role)]
        )

        # Confirm receipt (mirror FIRS) - PATCH transmit
        self.router.add_api_route(
            "/invoices/transmit/{irn}",
            self.confirm_firs_receipt,
            methods=["PATCH"],
            summary="Confirm receipt for transmitted invoice",
            description="Confirm receipt for transmitted invoice (mirrors FIRS PATCH /invoice/transmit/{IRN})",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_app_role)]
        )

        # FIRS Transmit Route (mirror FIRS MBS Transmit)
        self.router.add_api_route(
            "/invoices/transmit/{irn}",
            self.transmit_firs_invoice,
            methods=["POST"],
            summary="Transmit invoice by IRN",
            description="Transmit an already signed invoice to FIRS by IRN (mirrors FIRS POST /invoice/transmit/{IRN})",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_app_role)]
        )
        
        self.router.add_api_route(
            "/invoices/submissions",
            self.list_firs_submissions,
            methods=["GET"],
            summary="List FIRS submissions",
            description="List all invoice submissions to FIRS",
            response_model=V1ResponseModel
        )
        
        # Invoice Validation Routes
        self.router.add_api_route(
            "/validation/validate-invoice",
            self.validate_invoice_for_firs,
            methods=["POST"],
            summary="Validate invoice for FIRS",
            description="Validate invoice against FIRS compliance rules",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_app_role)]
        )
        
        self.router.add_api_route(
            "/validation/validate-batch",
            self.validate_invoice_batch_for_firs,
            methods=["POST"],
            summary="Validate invoice batch for FIRS",
            description="Validate multiple invoices against FIRS compliance rules",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_app_role)]
        )
        
        self.router.add_api_route(
            "/validation/rules",
            self.get_firs_validation_rules,
            methods=["GET"],
            summary="Get FIRS validation rules",
            description="Get current FIRS validation rules and compliance requirements",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_app_role)]
        )

        # Resource Cache Refresh (all)
        self.router.add_api_route(
            "/validation/refresh",
            self.refresh_firs_resources,
            methods=["POST"],
            summary="Refresh FIRS resources cache",
            description="Refresh cached FIRS resources (currencies, invoice-types, services-codes, vat-exemptions)",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_app_role)]
        )

        # Resource Cache Refresh (single)
        self.router.add_api_route(
            "/validation/refresh/{resource}",
            self.refresh_firs_resource,
            methods=["POST"],
            summary="Refresh a specific FIRS resource",
            description="Refresh a single cached FIRS resource by key",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_app_role)]
        )
        
        # Certificate Management Routes
        self.router.add_api_route(
            "/certificates/list",
            self.list_firs_certificates,
            methods=["GET"],
            summary="List FIRS certificates",
            description="List all FIRS certificates and their status",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/certificates/{certificate_id}",
            self.get_firs_certificate,
            methods=["GET"],
            summary="Get FIRS certificate",
            description="Get specific FIRS certificate details",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/certificates/renew/{certificate_id}",
            self.renew_firs_certificate,
            methods=["POST"],
            summary="Renew FIRS certificate",
            description="Renew expiring FIRS certificate",
            response_model=V1ResponseModel
        )
        
        # FIRS Reporting Routes (Required for FIRS Certification)
        self.router.add_api_route(
            "/reporting/generate",
            self.generate_firs_report,
            methods=["POST"],
            summary="Generate FIRS reports",
            description="Generate compliance and submission reports for FIRS",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/reporting/dashboard",
            self.get_firs_reporting_dashboard,
            methods=["GET"],
            summary="Get FIRS reporting dashboard",
            description="Get FIRS-specific reporting dashboard with compliance metrics",
            response_model=V1ResponseModel
        )
        
        # FIRS Invoice Update Routes (Required for FIRS Certification)
        self.router.add_api_route(
            "/update/invoice",
            self.update_firs_invoice,
            methods=["PUT"],
            summary="Update FIRS invoice",
            description="Update submitted invoice in FIRS system",
            response_model=V1ResponseModel
        )
        
        # Error and Log Management Routes
        self.router.add_api_route(
            "/errors/list",
            self.get_firs_errors,
            methods=["GET"],
            summary="Get FIRS integration errors",
            description="Get errors from FIRS integration attempts",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/logs/integration",
            self.get_firs_integration_logs,
            methods=["GET"],
            summary="Get FIRS integration logs",
            description="Get logs from FIRS integration activities",
            response_model=V1ResponseModel
        )
    
    # FIRS System Information Endpoints
    async def get_firs_system_info(self, request: Request):
        """Get FIRS system information"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_system_info",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            # Add capabilities information
            result["capabilities"] = self.firs_capabilities
            
            return self._create_v1_response(result, "firs_system_info_retrieved")
        except Exception as e:
            logger.error(f"Error getting FIRS system info in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get FIRS system info")
    
    async def check_firs_system_health(self, request: Request):
        """Check FIRS system health"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="check_firs_system_health",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_system_health_checked")
        except Exception as e:
            logger.error(f"Error checking FIRS system health in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to check FIRS system health")
    
    # FIRS Authentication Endpoints
    async def authenticate_with_firs(self, request: Request):
        """Authenticate with FIRS"""
        try:
            context = await self._require_app_role(request)
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="authenticate_with_firs",
                payload={
                    "auth_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_authentication_completed")
        except Exception as e:
            logger.error(f"Error authenticating with FIRS in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to authenticate with FIRS")
    
    async def refresh_firs_token(self, request: Request):
        """Refresh FIRS authentication token"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="refresh_firs_token",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_token_refreshed")
        except Exception as e:
            logger.error(f"Error refreshing FIRS token in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to refresh FIRS token")
    
    async def test_firs_connection(self, request: Request):
        """Test FIRS connection with provided credentials"""
        try:
            context = await self._require_app_role(request)
            body = await request.json()
            
            # Validate required fields
            if not body.get('api_key') or not body.get('api_secret'):
                raise HTTPException(status_code=400, detail="API key and secret are required")
            
            # Test connection to FIRS
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="test_firs_connection",
                payload={
                    "credentials": {
                        "api_key": body.get('api_key'),
                        "api_secret": body.get('api_secret'),
                        "environment": body.get('environment', 'sandbox')
                    },
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_connection_tested")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error testing FIRS connection in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to test FIRS connection")
    
    async def get_firs_auth_status(self, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Get FIRS authentication status"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_auth_status",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_auth_status_retrieved")
        except Exception as e:
            logger.error(f"Error getting FIRS auth status in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get FIRS auth status")
    
    # Invoice Submission Endpoints
    async def submit_invoice_to_firs(self, request: Request, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Submit invoice to FIRS"""
        try:
            body = await request.json()
            
            # Validate required fields
            required_fields = ["invoice_data", "taxpayer_id"]
            missing_fields = [field for field in required_fields if field not in body]
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required fields: {', '.join(missing_fields)}"
                )
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="submit_invoice_to_firs",
                payload={
                    "submission_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "invoice_submitted_to_firs")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error submitting invoice to FIRS in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to submit invoice to FIRS")
    
    async def submit_invoice_batch_to_firs(self, request: Request, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Submit invoice batch to FIRS"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="submit_invoice_batch_to_firs",
                payload={
                    "batch_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "invoice_batch_submitted_to_firs")
        except Exception as e:
            logger.error(f"Error submitting invoice batch to FIRS in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to submit invoice batch to FIRS")
    
    async def get_firs_submission_status(self, submission_id: str, request: Request):
        """Get FIRS submission status"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_submission_status",
                payload={
                    "submission_id": submission_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_submission_status_retrieved")
        except Exception as e:
            logger.error(f"Error getting FIRS submission status {submission_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get FIRS submission status")

    async def transmit_firs_invoice(self, irn: str, request: Request):
        """Transmit invoice by IRN (mirrors FIRS MBS transmit endpoint)."""
        try:
            # Optional payload passthrough for future flags
            body = {}
            try:
                body = await request.json()
            except Exception:
                body = {}

            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="transmit_firs_invoice",
                payload={
                    "irn": irn,
                    "options": body or {},
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )

            return self._create_v1_response(result, "firs_invoice_transmitted")
        except Exception as e:
            logger.error(f"Error transmitting FIRS invoice {irn} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to transmit FIRS invoice")

    async def confirm_firs_receipt(self, irn: str, request: Request):
        """Confirm receipt for transmitted invoice (mirror PATCH transmit)."""
        try:
            body = {}
            try:
                body = await request.json()
            except Exception:
                body = {}

            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="confirm_firs_receipt",
                payload={
                    "irn": irn,
                    "options": body or {},
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )

            return self._create_v1_response(result, "firs_receipt_confirmed")
        except Exception as e:
            logger.error(f"Error confirming receipt for FIRS invoice {irn} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to confirm FIRS invoice receipt")
    
    async def list_firs_submissions(self, 
                                  request: Request,
                                  status: Optional[str] = Query(None, description="Filter by submission status"),
                                  start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
                                  end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
                                  limit: int = Query(50, ge=1, le=1000),
                                  offset: int = Query(0, ge=0)):
        """List FIRS submissions"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="list_firs_submissions",
                payload={
                    "app_id": context.user_id,
                    "filters": {
                        "status": status,
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "pagination": {"limit": limit, "offset": offset},
                    "api_version": "v1"
                }
            )
            # Attach pagination meta
            try:
                items = result.get("items") or result.get("data") or []
                total = result.get("total") or result.get("count") or (len(items) if isinstance(items, list) else 0)
                result["pagination"] = normalize_pagination(limit=limit, offset=offset, total=total)
            except Exception:
                pass
            return self._create_v1_response(result, "firs_submissions_listed")
        except Exception as e:
            logger.error(f"Error listing FIRS submissions in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to list FIRS submissions")
    
    # Invoice Validation Endpoints
    async def validate_invoice_for_firs(self, request: Request, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Validate invoice for FIRS"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="validate_invoice_for_firs",
                payload={
                    "validation_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "invoice_validated_for_firs")
        except Exception as e:
            logger.error(f"Error validating invoice for FIRS in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to validate invoice for FIRS")
    
    async def validate_invoice_batch_for_firs(self, request: Request, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Validate invoice batch for FIRS"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="validate_invoice_batch_for_firs",
                payload={
                    "batch_validation_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "invoice_batch_validated_for_firs")
        except Exception as e:
            logger.error(f"Error validating invoice batch for FIRS in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to validate invoice batch for FIRS")
    
    async def get_firs_validation_rules(self, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Get FIRS validation rules"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_validation_rules",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_validation_rules_retrieved")
        except Exception as e:
            logger.error(f"Error getting FIRS validation rules in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get FIRS validation rules")

    async def refresh_firs_resources(self, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Refresh all cached FIRS resources (currencies/types/codes/exemptions)."""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="refresh_firs_resources",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            return self._create_v1_response(result, "firs_resources_refreshed")
        except Exception as e:
            logger.error(f"Error refreshing FIRS resources in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to refresh FIRS resources")

    async def refresh_firs_resource(self, resource: str, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Refresh a specific cached FIRS resource by key."""
        try:
            if resource not in ("currencies", "invoice-types", "services-codes", "vat-exemptions"):
                raise HTTPException(status_code=400, detail="invalid_resource")
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="refresh_firs_resource",
                payload={
                    "resource": resource,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            return self._create_v1_response(result, "firs_resource_refreshed")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error refreshing FIRS resource {resource} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to refresh FIRS resource")
    
    # Certificate Management Endpoints
    async def list_firs_certificates(self, context: HTTPRoutingContext = Depends(_require_app_role)):
        """List FIRS certificates"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="list_firs_certificates",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_certificates_listed")
        except Exception as e:
            logger.error(f"Error listing FIRS certificates in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to list FIRS certificates")
    
    async def get_firs_certificate(self, certificate_id: str, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Get FIRS certificate"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_certificate",
                payload={
                    "certificate_id": certificate_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_certificate_retrieved")
        except Exception as e:
            logger.error(f"Error getting FIRS certificate {certificate_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get FIRS certificate")
    
    async def renew_firs_certificate(self, certificate_id: str, request: Request, context: HTTPRoutingContext = Depends(_require_app_role)):
        """Renew FIRS certificate"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="renew_firs_certificate",
                payload={
                    "certificate_id": certificate_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_certificate_renewed")
        except Exception as e:
            logger.error(f"Error renewing FIRS certificate {certificate_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to renew FIRS certificate")
    
    # Error and Log Management Endpoints
    async def get_firs_errors(self, 
                            request: Request,
                            error_type: Optional[str] = Query(None, description="Filter by error type"),
                            start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
                            end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
                            context: HTTPRoutingContext = Depends(_require_app_role)):
        """Get FIRS integration errors"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_errors",
                payload={
                    "app_id": context.user_id,
                    "filters": {
                        "error_type": error_type,
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_errors_retrieved")
        except Exception as e:
            logger.error(f"Error getting FIRS errors in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get FIRS errors")
    
    async def get_firs_integration_logs(self, 
                                      request: Request,
                                      log_level: Optional[str] = Query(None, description="Filter by log level"),
                                      start_date: Optional[str] = Query(None, description="Start date (YYYY-MM-DD)"),
                                      end_date: Optional[str] = Query(None, description="End date (YYYY-MM-DD)"),
                                      context: HTTPRoutingContext = Depends(_require_app_role)):
        """Get FIRS integration logs"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_integration_logs",
                payload={
                    "app_id": context.user_id,
                    "filters": {
                        "log_level": log_level,
                        "start_date": start_date,
                        "end_date": end_date
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_integration_logs_retrieved")
        except Exception as e:
            logger.error(f"Error getting FIRS integration logs in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get FIRS integration logs")
    
    # FIRS Reporting Endpoints (Required for FIRS Certification)
    async def generate_firs_report(self, request: Request):
        """Generate FIRS reports"""
        try:
            context = await self._require_app_role(request)
            body = await request.json()
            
            # Validate required fields for report generation
            required_fields = ["report_type", "date_range"]
            missing_fields = [field for field in required_fields if field not in body]
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required fields: {', '.join(missing_fields)}"
                )
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="generate_firs_report",
                payload={
                    "report_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_report_generated")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error generating FIRS report in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate FIRS report")
    
    async def get_firs_reporting_dashboard(self, request: Request):
        """Get FIRS reporting dashboard"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_reporting_dashboard",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            # Add FIRS-specific dashboard metrics
            from datetime import datetime
            result["firs_metrics"] = {
                "total_submissions": result.get("total_submissions", 0),
                "successful_submissions": result.get("successful_submissions", 0),
                "failed_submissions": result.get("failed_submissions", 0),
                "pending_submissions": result.get("pending_submissions", 0),
                "compliance_rate": result.get("compliance_rate", "100%"),
                "last_sync": result.get("last_sync", datetime.utcnow().isoformat())
            }
            
            return self._create_v1_response(result, "firs_reporting_dashboard_retrieved")
        except Exception as e:
            logger.error(f"Error getting FIRS reporting dashboard in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get FIRS reporting dashboard")
    
    # FIRS Invoice Update Endpoints (Required for FIRS Certification)
    async def update_firs_invoice(self, request: Request):
        """Update FIRS invoice"""
        try:
            context = await self._require_app_role(request)
            body = await request.json()
            
            # Validate required fields for invoice update
            required_fields = ["invoice_id", "update_data"]
            missing_fields = [field for field in required_fields if field not in body]
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required fields: {', '.join(missing_fields)}"
                )
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="update_firs_invoice",
                payload={
                    "invoice_update": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_invoice_updated")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating FIRS invoice in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to update FIRS invoice")
    
    def _create_v1_response(self, data: Dict[str, Any], action: str, status_code: int = 200) -> V1ResponseModel:
        """Create standardized v1 response format using V1ResponseModel"""
        return build_v1_response(data, action)


def create_firs_integration_router(role_detector: HTTPRoleDetector,
                                  permission_guard: APIPermissionGuard,
                                  message_router: MessageRouter) -> APIRouter:
    """Factory function to create FIRS Integration Router"""
    firs_endpoints = FIRSIntegrationEndpointsV1(role_detector, permission_guard, message_router)
    return firs_endpoints.router
