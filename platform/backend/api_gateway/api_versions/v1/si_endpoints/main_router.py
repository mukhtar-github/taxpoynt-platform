"""
SI Main Router - API Version 1
==============================
Main router for System Integrator endpoints in API v1.
Consolidates all SI-specific functionality into a single versioned router.
Professional business system integration architecture.
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from core_platform.data_management.db_async import get_async_session
from core_platform.idempotency.store import IdempotencyStore
from fastapi.responses import JSONResponse

from core_platform.authentication.role_manager import PlatformRole, RoleScope
from core_platform.messaging.message_router import ServiceRole, MessageRouter
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from ..version_models import V1ResponseModel, V1ErrorModel
from api_gateway.utils.v1_response import build_v1_response

# Import business system routers  
from .organization_endpoints import create_organization_router
from .business_endpoints import (
    create_erp_router,
    create_crm_router, 
    create_pos_router,
    create_ecommerce_router,
    create_accounting_router,
    create_inventory_router
)
from .financial_endpoints import (
    create_banking_router,
    create_payment_processor_router,
    create_validation_router
)
from .transaction_endpoints import create_transaction_router
from .compliance_endpoints import create_compliance_router
from .firs_invoice_endpoints import create_firs_invoice_router
from .sdk_management_endpoints import create_sdk_management_router
from .onboarding_endpoints import create_onboarding_router
from .utils.si_observability import install_si_instrumentation
from .utils.si_errors import build_error_response

logger = logging.getLogger(__name__)


class SIRouterV1:
    """
    System Integrator Router - Version 1
    ====================================
    Handles all System Integrator endpoints for API v1, including:
    - Organization management and onboarding
    - ERP/CRM/POS system integrations
    - Transaction processing and validation
    - Compliance checking and reporting
    - Health monitoring and status
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/si", tags=["System Integrator V1"])
        self._setup_routes()
        self._include_sub_routers()
        # Attach SI metrics middleware and error handler (best-effort; router may not support these)
        install_si_instrumentation(self.router)
        try:
            if hasattr(self.router, "add_exception_handler"):
                self.router.add_exception_handler(Exception, self._si_exception_handler)  # type: ignore[attr-defined]
        except Exception:
            pass
        
        logger.info("SI Router V1 initialized")
    
    def _setup_routes(self):
        """Configure all SI v1 routes"""
        
        # Organization Management Routes
        self.router.add_api_route(
            "/organizations",
            self.list_organizations,
            methods=["GET"],
            summary="List managed organizations",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/organizations/{org_id}",
            self.get_organization,
            methods=["GET"],
            summary="Get organization details",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/organizations",
            self.create_organization,
            methods=["POST"],
            summary="Create new organization",
            response_model=V1ResponseModel,
            status_code=201,
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/organizations/{org_id}",
            self.update_organization,
            methods=["PUT"],
            summary="Update organization",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        # Business System Integration Routes
        # ERP/CRM/POS endpoints handled by business system sub-routers
        
        # Invoice Forwarding Routes (kept — bridge to APP)
        # SI → APP Invoice Forwarding (CRITICAL BRIDGE)
        self.router.add_api_route(
            "/invoices/forward-to-app",
            self.forward_invoices_to_app,
            methods=["POST"],
            summary="Forward generated invoices to APP for FIRS submission",
            description="Send SI-generated invoices to APP for FIRS transmission",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        self.router.add_api_route(
            "/invoices/batch/forward-to-app",
            self.forward_invoice_batch_to_app,
            methods=["POST"],
            summary="Forward invoice batch to APP for FIRS submission",
            description="Send batch of SI-generated invoices to APP for FIRS transmission",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
        
        # Note: Transaction, Compliance, Invoice generation and Data routes
        # are provided by their dedicated sub-routers; duplicates removed here.
        
        # Health and Monitoring Routes
        self.router.add_api_route(
            "/health",
            self.health_check,
            methods=["GET"],
            summary="SI services health check",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/status/integrations",
            self.get_integration_status,
            methods=["GET"],
            summary="Get integration status overview",
            response_model=V1ResponseModel,
            dependencies=[Depends(self._require_si_role)]
        )
    
    def _include_sub_routers(self):
        """Include all SI sub-routers"""
        
        # FIRS Invoice Generation Routes
        firs_invoice_router = create_firs_invoice_router(
            self.role_detector,
            self.permission_guard,
        )
        self.router.include_router(firs_invoice_router, tags=["FIRS Invoice Generation"])
        
        # SDK Management Routes
        sdk_management_router = create_sdk_management_router(
            self.role_detector,
            self.permission_guard,
            self.message_router
        )
        self.router.include_router(sdk_management_router, tags=["SDK Management"])
        
        # Financial System Integration Routes
        banking_router = create_banking_router(
            self.role_detector,
            self.permission_guard,
            self.message_router
        )
        self.router.include_router(banking_router, tags=["Banking Integrations V1"])
        
        payment_processor_router = create_payment_processor_router(
            self.role_detector,
            self.permission_guard,
            self.message_router
        )
        self.router.include_router(payment_processor_router, tags=["Payment Processors V1"])
        
        validation_router = create_validation_router(
            self.role_detector,
            self.permission_guard,
            self.message_router
        )
        self.router.include_router(validation_router, tags=["Financial Validation V1"])
        
        # Auto-Reconciliation Routes
        try:
            from .reconciliation_endpoints import create_reconciliation_router
            reconciliation_router = create_reconciliation_router(
                self.role_detector,
                self.permission_guard,
                self.message_router
            )
            self.router.include_router(reconciliation_router, tags=["Auto-Reconciliation V1"])
            logger.info("✅ Auto-Reconciliation endpoints connected to SI router")
        except ImportError as e:
            logger.warning(f"⚠️  Could not import reconciliation endpoints: {e}")
        
        # Compliance and Reporting Routes
        try:
            compliance_router = create_compliance_router(
                self.role_detector,
                self.permission_guard,
                self.message_router,
            )
            self.router.include_router(compliance_router, tags=["Compliance V1"])
            logger.info("✅ Compliance endpoints connected to SI router")
        except Exception as e:
            logger.warning(f"⚠️  Could not include compliance endpoints: {e}")

        # Onboarding Management Routes
        onboarding_router = create_onboarding_router(
            self.role_detector,
            self.permission_guard,
            self.message_router
        )
        self.router.include_router(onboarding_router, tags=["Onboarding Management V1"])
        
        logger.info("SI sub-routers included successfully")

    async def _si_exception_handler(self, request: Request, exc: Exception):
        """Return standardized V1ErrorModel for unhandled exceptions."""
        return build_error_response(request, exc)
    
    async def _require_si_role(self, request: Request) -> HTTPRoutingContext:
        """Dependency to ensure System Integrator role access for v1"""
        context = await self.role_detector.detect_role_context(request)
        
        if not context.has_role(PlatformRole.SYSTEM_INTEGRATOR):
            logger.warning(f"SI v1 endpoint access denied for context: {context}")
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="System Integrator role required for v1 API"
            )
        
        # Apply v1-specific permission guard
        if not await self.permission_guard.check_endpoint_permission(
            context, f"v1/si{request.url.path}", request.method
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions for SI v1 endpoint"
            )
        
        # Add v1-specific context
        context.metadata["api_version"] = "v1"
        context.metadata["endpoint_group"] = "si"
        
        return context
    
    # Organization Management Handlers
    async def list_organizations(self, request: Request):
        """List all organizations managed by this SI"""
        try:
            context = await self._require_si_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="list_organizations",
                payload={
                    "si_id": context.user_id,
                    "filters": dict(request.query_params),
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "organizations_listed")
        except Exception as e:
            logger.error(f"Error listing organizations in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to list organizations")
    
    async def get_organization(self, org_id: str, request: Request):
        """Get specific organization details"""
        try:
            context = await self._require_si_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_organization",
                payload={
                    "org_id": org_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "organization_retrieved")
        except Exception as e:
            logger.error(f"Error getting organization {org_id} in v1: {e}")
            raise HTTPException(status_code=404, detail="Organization not found")
    
    async def create_organization(self, request: Request, db: AsyncSession = Depends(get_async_session)):
        """Create new organization under SI management"""
        try:
            context = await self._require_si_role(request)
            body = await request.json()
            # Idempotency
            idem_key = request.headers.get("x-idempotency-key") or request.headers.get("idempotency-key")
            if idem_key:
                req_hash = IdempotencyStore.compute_request_hash(body)
                exists, stored, stored_code, conflict = await IdempotencyStore.try_begin(
                    db,
                    requester_id=str(context.user_id) if context and context.user_id else None,
                    key=idem_key,
                    method=request.method,
                    endpoint=str(request.url.path),
                    request_hash=req_hash,
                )
                if conflict:
                    raise HTTPException(status_code=409, detail="Idempotency key reuse with different request body")
                if exists and stored is not None:
                    return self._create_v1_response(stored, "organization_created", status_code=stored_code or 201)
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="create_organization",
                payload={
                    "organization_data": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            # Save idempotent result
            if idem_key:
                await IdempotencyStore.finalize_success(
                    db,
                    requester_id=str(context.user_id) if context and context.user_id else None,
                    key=idem_key,
                    response=result,
                    status_code=201,
                )
            return self._create_v1_response(result, "organization_created", status_code=201)
        except Exception as e:
            logger.error(f"Error creating organization in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to create organization")
    
    async def update_organization(self, org_id: str, request: Request, db: AsyncSession = Depends(get_async_session)):
        """Update organization information"""
        try:
            context = await self._require_si_role(request)
            body = await request.json()
            idem_key = request.headers.get("x-idempotency-key") or request.headers.get("idempotency-key")
            if idem_key:
                composite = {"org_id": org_id, "updates": body}
                req_hash = IdempotencyStore.compute_request_hash(composite)
                exists, stored, stored_code, conflict = await IdempotencyStore.try_begin(
                    db,
                    requester_id=str(context.user_id) if context and context.user_id else None,
                    key=idem_key,
                    method=request.method,
                    endpoint=str(request.url.path),
                    request_hash=req_hash,
                )
                if conflict:
                    raise HTTPException(status_code=409, detail="Idempotency key reuse with different request body")
                if exists and stored is not None:
                    return self._create_v1_response(stored, "organization_updated", status_code=stored_code or 200)
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="update_organization",
                payload={
                    "org_id": org_id,
                    "updates": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            if idem_key:
                await IdempotencyStore.finalize_success(
                    db,
                    requester_id=str(context.user_id) if context and context.user_id else None,
                    key=idem_key,
                    response=result,
                    status_code=200,
                )
            return self._create_v1_response(result, "organization_updated")
        except Exception as e:
            logger.error(f"Error updating organization {org_id} in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to update organization")
    
    # Integration Management Handlers (abbreviated for brevity - similar pattern)
    # Health and utility handlers
    async def health_check(self):
        """SI services health check for v1"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="health_check",
                payload={"api_version": "v1"}
            )
            
            return JSONResponse(content={
                "status": "healthy",
                "service": "si_services",
                "api_version": "v1",
                "timestamp": result.get("timestamp"),
                "version_specific": {
                    "supported_features": [
                        "organization_management",
                        "erp_integration", 
                        "transaction_processing",
                        "compliance_validation"
                    ],
                    "v1_compatibility": "full"
                }
            })
        except Exception as e:
            logger.error(f"SI v1 health check failed: {e}")
            return JSONResponse(
                content={
                    "status": "unhealthy",
                    "api_version": "v1",
                    "error": str(e)
                },
                status_code=503
            )
    
    # Additional handlers removed (now provided by sub-routers)
    
    async def get_integration_status(
        self,
        request: Request,
        db: AsyncSession = Depends(get_async_session),
    ):
        """Get comprehensive integration status (SI)"""
        try:
            # Enforce SI guard explicitly here
            await self._require_si_role(request)
            # Use modern integration management service via message router
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="monitor_health",
                payload={"api_version": "v1"}
            )
            return self._create_v1_response(result, "integration_status_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting integration status in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to get integration status")
    
    # CRITICAL BRIDGE: SI → APP Invoice Forwarding
    async def forward_invoices_to_app(self, request: Request):
        """
        Forward generated invoices to APP for FIRS submission.
        
        This is the critical bridge between SI (invoice generation) and APP (FIRS submission).
        Uses the existing APP FIRS communication service infrastructure.
        """
        try:
            # Enforce SI guard
            context = await self._require_si_role(request)
            body = await request.json()
            
            # Validate required fields
            required_fields = ["invoice_ids"]
            missing_fields = [field for field in required_fields if field not in body]
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required fields: {', '.join(missing_fields)}"
                )
            
            # Route to APP FIRS service using existing infrastructure
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="receive_invoices_from_si",
                payload={
                    "invoice_ids": body["invoice_ids"],
                    "si_user_id": context.user_id,
                    "submission_options": body.get("submission_options", {
                        "environment": "sandbox",
                        "auto_submit": True,
                        "validate_first": True
                    })
                }
            )
            
            return self._create_v1_response(result, "invoices_forwarded_to_app")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error forwarding invoices to APP: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to forward invoices to APP"
            )
    
    async def forward_invoice_batch_to_app(self, request: Request):
        """
        Forward invoice batch to APP for FIRS submission.
        
        Uses the existing APP FIRS communication service infrastructure.
        """
        try:
            # Enforce SI guard
            context = await self._require_si_role(request)
            body = await request.json()
            
            # Validate required fields
            required_fields = ["batch_id"]
            missing_fields = [field for field in required_fields if field not in body]
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required fields: {', '.join(missing_fields)}"
                )
            
            # Route to APP FIRS service using existing infrastructure
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="receive_invoice_batch_from_si",
                payload={
                    "batch_id": body["batch_id"],
                    "si_user_id": context.user_id,
                    "batch_options": body.get("batch_options", {
                        "environment": "sandbox",
                        "auto_submit": True,
                        "validate_batch": True,
                        "batch_size": body.get("batch_size", 50)
                    })
                }
            )
            
            return self._create_v1_response(result, "invoice_batch_forwarded_to_app")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error forwarding invoice batch to APP: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to forward invoice batch to APP"
            )
    
    def _create_v1_response(self, data: Dict[str, Any], action: str, status_code: int = 200) -> V1ResponseModel:
        """Create standardized v1 response format"""
        return build_v1_response(data, action)


def create_si_v1_router(role_detector: HTTPRoleDetector,
                       permission_guard: APIPermissionGuard,
                       message_router: MessageRouter) -> APIRouter:
    """Factory function to create SI V1 Router"""
    si_v1_router = SIRouterV1(role_detector, permission_guard, message_router)
    return si_v1_router.router
