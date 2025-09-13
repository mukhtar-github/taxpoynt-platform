"""
Organization Management Endpoints - API v1
==========================================
System Integrator endpoints for managing organizations and their business system connections.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse

from core_platform.authentication.role_manager import PlatformRole
from core_platform.messaging.message_router import ServiceRole, MessageRouter
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from .version_models import V1ResponseModel, V1ErrorModel, V1PaginationModel
from sqlalchemy.ext.asyncio import AsyncSession
from core_platform.data_management.db_async import get_async_session
from core_platform.data_management.repositories.firs_submission_repo_async import (
    list_recent_submissions,
    get_submission_metrics,
    list_submissions_filtered,
)
from core_platform.data_management.repositories.business_systems_repo_async import list_business_systems
from core_platform.authentication.tenant_context import set_current_tenant, clear_current_tenant

logger = logging.getLogger(__name__)


class OrganizationEndpointsV1:
    """
    Organization Management Endpoints - Version 1
    =============================================
    Handles organization lifecycle management for System Integrators including:
    - Creating and managing organizations
    - Onboarding organizations to e-invoicing
    - Managing organization business system connections
    - Organization compliance status and reporting
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(
            prefix="/organizations",
            tags=["Organizations V1"],
            dependencies=[Depends(self._require_si_role)]
        )
        self._setup_routes()
        
        logger.info("Organization Endpoints V1 initialized")
    
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
        """Setup organization management routes"""
        
        # Core Organization CRUD
        self.router.add_api_route(
            "",
            self.list_organizations,
            methods=["GET"],
            summary="List managed organizations",
            description="Get paginated list of organizations managed by this SI",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "",
            self.create_organization,
            methods=["POST"],
            summary="Create new organization",
            description="Create and onboard a new organization for e-invoicing",
            response_model=V1ResponseModel,
            status_code=201
        )
        
        self.router.add_api_route(
            "/{org_id}",
            self.get_organization,
            methods=["GET"],
            summary="Get organization details",
            description="Retrieve detailed information about a specific organization",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{org_id}",
            self.update_organization,
            methods=["PUT"],
            summary="Update organization",
            description="Update organization information and settings",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{org_id}",
            self.delete_organization,
            methods=["DELETE"],
            summary="Delete organization",
            description="Remove organization from SI management",
            response_model=V1ResponseModel
        )
        
        # Organization Business Systems
        self.router.add_api_route(
            "/{org_id}/business-systems",
            self.get_organization_business_systems,
            methods=["GET"],
            summary="Get organization's business systems",
            description="List all business systems connected to this organization",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{org_id}/business-systems/{system_type}",
            self.get_organization_business_system_by_type,
            methods=["GET"],
            summary="Get business systems by type",
            description="Get organization's business systems filtered by type (erp, crm, pos, etc.)",
            response_model=V1ResponseModel
        )
        
        # Organization Onboarding
        self.router.add_api_route(
            "/{org_id}/onboard",
            self.initiate_organization_onboarding,
            methods=["POST"],
            summary="Initiate organization onboarding",
            description="Start the e-invoicing onboarding process for an organization",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{org_id}/onboarding-status",
            self.get_onboarding_status,
            methods=["GET"],
            summary="Get onboarding status",
            description="Check the current onboarding progress for an organization",
            response_model=V1ResponseModel
        )
        
        # Organization Compliance
        self.router.add_api_route(
            "/{org_id}/compliance",
            self.get_organization_compliance,
            methods=["GET"],
            summary="Get organization compliance status",
            description="Retrieve compliance status and validation results",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{org_id}/validate-compliance",
            self.validate_organization_compliance,
            methods=["POST"],
            summary="Validate organization compliance",
            description="Run compliance validation checks for an organization",
            response_model=V1ResponseModel
        )
        
        # Organization Transactions
        self.router.add_api_route(
            "/{org_id}/transactions",
            self.get_organization_transactions,
            methods=["GET"],
            summary="Get organization transactions",
            description="Retrieve transactions for a specific organization",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{org_id}/transaction-summary",
            self.get_organization_transaction_summary,
            methods=["GET"],
            summary="Get transaction summary",
            description="Get aggregated transaction statistics for an organization",
            response_model=V1ResponseModel
        )

        # Recent submissions for an organization (async + tenant scoped)
        self.router.add_api_route(
            "/{org_id}/submissions/recent",
            self.get_org_recent_submissions,
            methods=["GET"],
            summary="Get organization's recent FIRS submissions",
            description="List recent FIRS submissions for a specific organization",
            response_model=V1ResponseModel
        )
    
    async def list_organizations(self, 
                                request: Request,
                                page: int = Query(1, ge=1, description="Page number"),
                                limit: int = Query(50, ge=1, le=1000, description="Items per page"),
                                search: Optional[str] = Query(None, description="Search organizations"),
                                status: Optional[str] = Query(None, description="Filter by status"),
                                business_system: Optional[str] = Query(None, description="Filter by business system type"),
                                context: HTTPRoutingContext = Depends(lambda: None)):
        """List organizations managed by this SI"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="list_organizations",
                payload={
                    "si_id": context.user_id,
                    "pagination": {"page": page, "limit": limit},
                    "filters": {
                        "search": search,
                        "status": status,
                        "business_system": business_system
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "organizations_listed")
        except Exception as e:
            logger.error(f"Error listing organizations in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to list organizations")

    async def get_org_recent_submissions(self,
                                         org_id: str,
                                         limit: int = Query(10, ge=1, le=100),
                                         db: AsyncSession = Depends(get_async_session)):
        """Get recent FIRS submissions for the specified organization (SI view)."""
        try:
            # Temporarily scope tenant to the specified organization for repository logic
            set_current_tenant(org_id)
            try:
                rows = await list_recent_submissions(db, limit=limit)
            finally:
                clear_current_tenant()

            payload = {
                "organization_id": org_id,
                "items": [
                    {
                        "id": str(getattr(r, "id", None)),
                        "invoice_number": getattr(r, "invoice_number", None),
                        "irn": getattr(r, "irn", None),
                        "status": getattr(r, "status", None).value if getattr(r, "status", None) else None,
                        "created_at": getattr(r, "created_at", None).isoformat() if getattr(r, "created_at", None) else None,
                    }
                    for r in rows
                ],
                "count": len(rows)
            }
            return self._create_v1_response(payload, "organization_recent_submissions_retrieved")
        except Exception as e:
            logger.error(f"Error getting recent submissions for org {org_id}: {e}")
            raise HTTPException(status_code=500, detail="Failed to get organization's recent submissions")
    
    async def create_organization(self, 
                                 request: Request,
                                 context: HTTPRoutingContext = Depends(lambda: None)):
        """Create new organization"""
        try:
            body = await request.json()
            
            # Validate required fields for v1
            required_fields = ["name", "tax_id", "email", "phone", "address"]
            missing_fields = [field for field in required_fields if field not in body]
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required fields: {', '.join(missing_fields)}"
                )
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="create_organization",
                payload={
                    "organization_data": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "organization_created", status_code=201)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating organization in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to create organization")
    
    async def get_organization(self, 
                              org_id: str,
                              context: HTTPRoutingContext = Depends(lambda: None)):
        """Get organization details"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_organization",
                payload={
                    "org_id": org_id,
                    "si_id": context.user_id,
                    "include_business_systems": True,
                    "include_compliance_status": True,
                    "api_version": "v1"
                }
            )
            
            if not result:
                raise HTTPException(status_code=404, detail="Organization not found")
            
            return self._create_v1_response(result, "organization_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting organization {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get organization")
    
    async def update_organization(self, 
                                 org_id: str,
                                 request: Request,
                                 context: HTTPRoutingContext = Depends(lambda: None)):
        """Update organization information"""
        try:
            body = await request.json()
            
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
            
            return self._create_v1_response(result, "organization_updated")
        except Exception as e:
            logger.error(f"Error updating organization {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to update organization")
    
    async def delete_organization(self, 
                                 org_id: str,
                                 context: HTTPRoutingContext = Depends(lambda: None)):
        """Delete organization"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="delete_organization",
                payload={
                    "org_id": org_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "organization_deleted")
        except Exception as e:
            logger.error(f"Error deleting organization {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete organization")
    
    async def get_organization_business_systems(self, 
                                               org_id: str,
                                               limit: int = Query(50, ge=1, le=1000),
                                               offset: int = Query(0, ge=0),
                                               db: AsyncSession = Depends(get_async_session)):
        """Get organization's business systems (async, ERP only for now)."""
        try:
            set_current_tenant(org_id)
            try:
                data = await list_business_systems(db, limit=limit, offset=offset)
            finally:
                clear_current_tenant()

            data["available_system_types"] = {
                "erp": ["sap", "oracle", "dynamics", "netsuite", "odoo"],
                "crm": ["salesforce", "hubspot", "dynamics_crm", "pipedrive", "zoho"],
                "pos": ["square", "clover", "lightspeed", "toast", "shopify_pos", "moniepoint", "opay", "palmpay"],
                "ecommerce": ["shopify", "woocommerce", "magento", "bigcommerce", "jumia"],
                "accounting": ["quickbooks", "xero", "wave", "freshbooks", "sage"],
                "inventory": ["cin7", "fishbowl", "tradegecko", "unleashed"]
            }
            return self._create_v1_response(data, "organization_business_systems_retrieved")
        except Exception as e:
            logger.error(f"Error getting organization business systems {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get organization business systems")
    
    async def get_organization_business_system_by_type(self, 
                                                      org_id: str,
                                                      system_type: str,
                                                      limit: int = Query(50, ge=1, le=1000),
                                                      offset: int = Query(0, ge=0),
                                                      db: AsyncSession = Depends(get_async_session)):
        """Get organization's business systems by type"""
        try:
            # Validate system type
            valid_types = ["erp", "crm", "pos", "ecommerce", "accounting", "inventory"]
            if system_type not in valid_types:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid system type. Must be one of: {', '.join(valid_types)}"
                )
            
            set_current_tenant(org_id)
            try:
                result = await list_business_systems(
                    db, system_type=system_type, limit=limit, offset=offset
                )
            finally:
                clear_current_tenant()
            return self._create_v1_response(result, f"organization_{system_type}_systems_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting organization {system_type} systems {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get organization {system_type} systems")
    
    async def initiate_organization_onboarding(self, 
                                              org_id: str,
                                              request: Request,
                                              context: HTTPRoutingContext = Depends(lambda: None)):
        """Initiate organization onboarding"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="initiate_organization_onboarding",
                payload={
                    "org_id": org_id,
                    "onboarding_config": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "organization_onboarding_initiated")
        except Exception as e:
            logger.error(f"Error initiating onboarding for organization {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to initiate organization onboarding")
    
    async def get_onboarding_status(self, 
                                   org_id: str,
                                   context: HTTPRoutingContext = Depends(lambda: None)):
        """Get onboarding status"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_organization_onboarding_status",
                payload={
                    "org_id": org_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "onboarding_status_retrieved")
        except Exception as e:
            logger.error(f"Error getting onboarding status for organization {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get onboarding status")
    
    async def get_organization_compliance(self, 
                                         org_id: str,
                                         context: HTTPRoutingContext = Depends(lambda: None)):
        """Get organization compliance status"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_organization_compliance",
                payload={
                    "org_id": org_id,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "organization_compliance_retrieved")
        except Exception as e:
            logger.error(f"Error getting compliance for organization {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get organization compliance")
    
    async def validate_organization_compliance(self, 
                                              org_id: str,
                                              request: Request,
                                              context: HTTPRoutingContext = Depends(lambda: None)):
        """Validate organization compliance"""
        try:
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="validate_organization_compliance",
                payload={
                    "org_id": org_id,
                    "validation_config": body,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "organization_compliance_validated")
        except Exception as e:
            logger.error(f"Error validating compliance for organization {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to validate organization compliance")
    
    async def get_organization_transactions(self, 
                                           org_id: str,
                                           request: Request,
                                           db: AsyncSession = Depends(get_async_session)):
        """Get organization transactions (submission-based list with filters)."""
        try:
            # Basic filters: status, start_date, end_date, limit
            qp = dict(request.query_params)
            status = qp.get("status")
            start_date = qp.get("start_date")
            end_date = qp.get("end_date")
            limit = int(qp.get("limit", 50))

            set_current_tenant(org_id)
            try:
                rows = await list_submissions_filtered(
                    db,
                    status=status,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                )
            finally:
                clear_current_tenant()

            payload = {
                "organization_id": org_id,
                "count": len(rows),
                "items": [
                    {
                        "invoice_number": getattr(r, "invoice_number", None),
                        "status": getattr(r, "status", None).value if getattr(r, "status", None) else None,
                        "created_at": getattr(r, "created_at", None).isoformat() if getattr(r, "created_at", None) else None,
                        "irn": getattr(r, "irn", None),
                        "total_amount": float(getattr(r, "total_amount", 0) or 0),
                        "currency": getattr(r, "currency", None),
                    }
                    for r in rows
                ],
            }
            return self._create_v1_response(payload, "organization_transactions_retrieved")
        except Exception as e:
            logger.error(f"Error getting transactions for organization {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get organization transactions")
    
    async def get_organization_transaction_summary(self, 
                                                   org_id: str,
                                                   db: AsyncSession = Depends(get_async_session)):
        """Get organization transaction summary (async, submission-based)."""
        try:
            set_current_tenant(org_id)
            try:
                metrics = await get_submission_metrics(db)
            finally:
                clear_current_tenant()
            payload = {
                "organization_id": org_id,
                "summary": {
                    "total_transmissions": metrics.get("totalTransmissions", 0),
                    "completed": metrics.get("completed", 0),
                    "failed": metrics.get("failed", 0),
                    "processing": metrics.get("processing", 0),
                    "submitted": metrics.get("submitted", 0),
                    "success_rate": metrics.get("successRate", 0.0),
                    "avg_processing_time": metrics.get("averageProcessingTime"),
                    "today": metrics.get("todayTransmissions", 0),
                },
            }
            return self._create_v1_response(payload, "organization_transaction_summary_retrieved")
        except Exception as e:
            logger.error(f"Error getting transaction summary for organization {org_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get organization transaction summary")
    
    def _create_v1_response(self, data: Dict[str, Any], action: str, status_code: int = 200) -> JSONResponse:
        """Create standardized v1 response format"""
        response_data = {
            "success": True,
            "action": action,
            "api_version": "v1",
            "timestamp": "2024-12-31T00:00:00Z",
            "data": data
        }
        
        return JSONResponse(content=response_data, status_code=status_code)


def create_organization_router(role_detector: HTTPRoleDetector,
                              permission_guard: APIPermissionGuard,
                              message_router: MessageRouter) -> APIRouter:
    """Factory function to create Organization Router"""
    org_endpoints = OrganizationEndpointsV1(role_detector, permission_guard, message_router)
    return org_endpoints.router
