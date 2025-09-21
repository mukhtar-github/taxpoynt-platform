"""
CRM System Integration Endpoints - API v1
==================================================
System Integrator endpoints for CRM system integrations.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status, Query
from fastapi.responses import JSONResponse

from core_platform.messaging.message_router import ServiceRole, MessageRouter
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from ..version_models import V1ResponseModel
from api_gateway.utils.v1_response import build_v1_response
from core_platform.data_management.db_async import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from core_platform.idempotency.store import IdempotencyStore

logger = logging.getLogger(__name__)


class CRMEndpointsV1:
    """CRM System Integration Endpoints - Version 1"""
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/crm", tags=["CRM Systems V1"], dependencies=[Depends(self._require_si_role)])
        
        self.crm_systems = ["salesforce", "hubspot", "dynamics_crm", "pipedrive", "zoho"]
        
        self._setup_routes()
        logger.info("CRM Endpoints V1 initialized")
    
    def _setup_routes(self):
        """Setup CRM system integration routes"""
        
        self.router.add_api_route(
            "/available",
            self.get_available_crm_systems,
            methods=["GET"],
            summary="Get available CRM systems",
            description="List all CRM systems available for integration",
            response_model=V1ResponseModel
        )
        
        # Odoo-first CRM list (opportunities)
        self.router.add_api_route(
            "/opportunities",
            self.list_crm_opportunities,
            methods=["GET"],
            summary="List CRM opportunities (Odoo)",
            description="List CRM opportunities from Odoo",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/connections",
            self.create_crm_connection,
            methods=["POST"],
            summary="Create CRM connection",
            description="Create new CRM system connection",
            response_model=V1ResponseModel,
            status_code=201
        )
        
        self.router.add_api_route(
            "/connections/{connection_id}",
            self.get_crm_connection,
            methods=["GET"],
            summary="Get CRM connection",
            description="Get specific CRM connection details",
            response_model=V1ResponseModel
        )
        self.router.add_api_route(
            "/opportunities/{opportunity_id}",
            self.get_crm_opportunity,
            methods=["GET"],
            summary="Get CRM opportunity",
            description="Get a single CRM opportunity from Odoo",
            response_model=V1ResponseModel
        )

        # Write operations (optional)
        self.router.add_api_route(
            "/opportunities",
            self.create_crm_opportunity,
            methods=["POST"],
            summary="Create CRM opportunity",
            description="Create an Odoo CRM opportunity",
            response_model=V1ResponseModel,
            status_code=201
        )

        self.router.add_api_route(
            "/opportunities/{opportunity_id}",
            self.update_crm_opportunity,
            methods=["PUT"],
            summary="Update CRM opportunity",
            description="Update an Odoo CRM opportunity",
            response_model=V1ResponseModel
        )
    
    async def _require_si_role(self, request: Request) -> HTTPRoutingContext:
        context = await self.role_detector.detect_role_context(request)
        if not context or not await self.permission_guard.check_endpoint_permission(context, f"v1/si{request.url.path}", request.method):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions for SI v1 endpoint")
        return context
    
    # Placeholder implementations
    async def get_available_crm_systems(self, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get available CRM systems"""
        return self._create_v1_response({"systems": self.crm_systems}, "available_crm_systems_retrieved")
    
    async def list_crm_opportunities(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """List Odoo CRM opportunities (SI → Odoo)"""
        try:
            params = dict(request.query_params)
            limit = int(params.get("limit", 50))
            offset = int(params.get("offset", 0))
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_crm_opportunities",
                payload={
                    "limit": limit,
                    "offset": offset,
                    "api_version": "v1"
                }
            )
            return self._create_v1_response(result, "crm_opportunities_listed")
        except Exception as e:
            logger.error(f"Error listing CRM opportunities: {e}")
            raise HTTPException(status_code=502, detail="Failed to list CRM opportunities")
    
    async def create_crm_connection(self, request: Request, context: HTTPRoutingContext = Depends(lambda: None)):
        """Create CRM connection"""
        return self._create_v1_response({"connection_id": "crm_123"}, "crm_connection_created", status_code=201)
    
    async def get_crm_connection(self, connection_id: str, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get CRM connection"""
        return self._create_v1_response({"connection_id": connection_id}, "crm_connection_retrieved")
    
    async def get_crm_opportunity(self, opportunity_id: int, context: HTTPRoutingContext = Depends(lambda: None)):
        """Get an Odoo CRM opportunity"""
        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_crm_opportunity",
                payload={
                    "opportunity_id": int(opportunity_id),
                    "api_version": "v1"
                }
            )
            if not (result and result.get('data')):
                raise HTTPException(status_code=404, detail="Opportunity not found")
            return self._create_v1_response(result, "crm_opportunity_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting CRM opportunity {opportunity_id}: {e}")
            raise HTTPException(status_code=502, detail="Failed to get CRM opportunity")

    # Write operations with idempotency
    async def create_crm_opportunity(self, request: Request, db: AsyncSession = Depends(get_async_session), context: HTTPRoutingContext = Depends(lambda: None)):
        try:
            body = await request.json()
            idem_key = request.headers.get("x-idempotency-key") or request.headers.get("idempotency-key")
            if idem_key:
                req_hash = IdempotencyStore.compute_request_hash(body)
                exists, stored, stored_code, conflict = await IdempotencyStore.try_begin(
                    db,
                    requester_id=str(getattr(context, 'user_id', None)) if context else None,
                    key=idem_key,
                    method=request.method,
                    endpoint=str(request.url.path),
                    request_hash=req_hash,
                )
                if conflict:
                    raise HTTPException(status_code=409, detail="Idempotency key reuse with different request body")
                if exists and stored is not None:
                    return self._create_v1_response(stored, "crm_opportunity_created", status_code=stored_code or 201)

            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="create_crm_opportunity",
                payload={
                    "data": body,
                    "correlation_id": request.headers.get("x-correlation-id") or request.headers.get("correlation-id"),
                    "api_version": "v1"
                }
            )
            if idem_key:
                await IdempotencyStore.finalize_success(
                    db,
                    requester_id=str(getattr(context, 'user_id', None)) if context else None,
                    key=idem_key,
                    response=result,
                    status_code=201,
                )
            return self._create_v1_response(result, "crm_opportunity_created", status_code=201)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating CRM opportunity: {e}")
            raise HTTPException(status_code=502, detail="Failed to create CRM opportunity")

    async def update_crm_opportunity(self, opportunity_id: int, request: Request, db: AsyncSession = Depends(get_async_session), context: HTTPRoutingContext = Depends(lambda: None)):
        try:
            body = await request.json()
            idem_key = request.headers.get("x-idempotency-key") or request.headers.get("idempotency-key")
            if idem_key:
                composite = {"opportunity_id": int(opportunity_id), "updates": body}
                req_hash = IdempotencyStore.compute_request_hash(composite)
                exists, stored, stored_code, conflict = await IdempotencyStore.try_begin(
                    db,
                    requester_id=str(getattr(context, 'user_id', None)) if context else None,
                    key=idem_key,
                    method=request.method,
                    endpoint=str(request.url.path),
                    request_hash=req_hash,
                )
                if conflict:
                    raise HTTPException(status_code=409, detail="Idempotency key reuse with different request body")
                if exists and stored is not None:
                    return self._create_v1_response(stored, "crm_opportunity_updated", status_code=stored_code or 200)

            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="update_crm_opportunity",
                payload={
                    "opportunity_id": int(opportunity_id),
                    "updates": body,
                    "correlation_id": request.headers.get("x-correlation-id") or request.headers.get("correlation-id"),
                    "api_version": "v1"
                }
            )
            if idem_key:
                await IdempotencyStore.finalize_success(
                    db,
                    requester_id=str(getattr(context, 'user_id', None)) if context else None,
                    key=idem_key,
                    response=result,
                    status_code=200,
                )
            return self._create_v1_response(result, "crm_opportunity_updated")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating CRM opportunity {opportunity_id}: {e}")
            raise HTTPException(status_code=502, detail="Failed to update CRM opportunity")
    
    def _create_v1_response(self, data: Dict[str, Any], action: str, status_code: int = 200) -> V1ResponseModel:
        """Create standardized v1 response format"""
        return build_v1_response(data, action)


def create_crm_router(role_detector: HTTPRoleDetector,
                     permission_guard: APIPermissionGuard,
                     message_router: MessageRouter) -> APIRouter:
    """Factory function to create CRM Router"""
    crm_endpoints = CRMEndpointsV1(role_detector, permission_guard, message_router)
    return crm_endpoints.router
