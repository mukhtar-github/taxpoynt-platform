"""
ERP System Integration Endpoints - API v1
==========================================
System Integrator endpoints for Enterprise Resource Planning system integrations.
Covers: SAP, Oracle, Microsoft Dynamics, NetSuite, Odoo
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
from ..version_models import V1ResponseModel
from api_gateway.utils.v1_response import build_v1_response

logger = logging.getLogger(__name__)


class ERPEndpointsV1:
    """
    ERP System Integration Endpoints - Version 1
    ============================================
    Manages ERP system integrations for System Integrators:
    
    **Available ERP Systems:**
    - **SAP**: Enterprise-grade ERP with OData API integration
    - **Oracle**: Comprehensive business suite with REST APIs
    - **Microsoft Dynamics**: Cloud and on-premise ERP solutions
    - **NetSuite**: Cloud-based ERP platform
    - **Odoo**: Open-source business management suite
    
    **ERP Features:**
    - Invoice data extraction and processing
    - Customer and vendor management
    - Product catalog synchronization
    - Financial data integration
    - Real-time data synchronization
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/erp", tags=["ERP Systems V1"])
        
        # Available ERP systems from actual implementation
        self.erp_systems = {
            "sap": {
                "name": "SAP ERP",
                "description": "Enterprise-grade ERP with OData API integration",
                "auth_methods": ["oauth2", "basic_auth"],
                "data_types": ["invoices", "customers", "vendors", "products", "financial_data"],
                "api_type": "odata",
                "documentation": "/docs/integrations/erp/sap"
            },
            "oracle": {
                "name": "Oracle ERP Cloud",
                "description": "Comprehensive business suite with REST APIs",
                "auth_methods": ["oauth2", "jwt"],
                "data_types": ["invoices", "customers", "vendors", "products", "financial_data"],
                "api_type": "rest",
                "documentation": "/docs/integrations/erp/oracle"
            },
            "dynamics": {
                "name": "Microsoft Dynamics",
                "description": "Cloud and on-premise ERP solutions",
                "auth_methods": ["oauth2", "azure_ad"],
                "data_types": ["invoices", "customers", "vendors", "products", "financial_data"],
                "api_type": "rest",
                "documentation": "/docs/integrations/erp/dynamics"
            },
            "netsuite": {
                "name": "NetSuite ERP",
                "description": "Cloud-based comprehensive ERP platform",
                "auth_methods": ["oauth2", "token_based"],
                "data_types": ["invoices", "customers", "vendors", "products", "financial_data"],
                "api_type": "rest",
                "documentation": "/docs/integrations/erp/netsuite"
            },
            "odoo": {
                "name": "Odoo",
                "description": "Open-source business management suite",
                "auth_methods": ["api_key", "session_auth"],
                "data_types": ["invoices", "customers", "vendors", "products", "financial_data"],
                "api_type": "xmlrpc",
                "documentation": "/docs/integrations/erp/odoo"
            }
        }
        
        self._setup_routes()
        logger.info("ERP Endpoints V1 initialized")
    
    def _setup_routes(self):
        """Setup ERP system integration routes"""
        guard_deps: List[Any] = [Depends(self._ensure_context)]
        
        # ERP System Discovery
        self.router.add_api_route(
            "/available",
            self.get_available_erp_systems,
            methods=["GET"],
            summary="Get available ERP systems",
            description="List all ERP systems available for integration",
            response_model=V1ResponseModel,
            dependencies=guard_deps,
        )
        
        # ERP Connection Management
        self.router.add_api_route(
            "/connections",
            self.list_erp_connections,
            methods=["GET"],
            summary="List ERP connections",
            description="Get all ERP system connections for the SI",
            response_model=V1ResponseModel,
            dependencies=guard_deps,
        )
        
        self.router.add_api_route(
            "/connections",
            self.create_erp_connection,
            methods=["POST"],
            summary="Create ERP connection",
            description="Create new ERP system connection",
            response_model=V1ResponseModel,
            status_code=201,
            dependencies=guard_deps,
        )
        
        self.router.add_api_route(
            "/connections/{connection_id}",
            self.get_erp_connection,
            methods=["GET"],
            summary="Get ERP connection",
            description="Get specific ERP connection details",
            response_model=V1ResponseModel,
            dependencies=guard_deps,
        )
        
        self.router.add_api_route(
            "/connections/{connection_id}",
            self.update_erp_connection,
            methods=["PUT"],
            summary="Update ERP connection",
            description="Update ERP connection configuration",
            response_model=V1ResponseModel,
            dependencies=guard_deps,
        )
        
        self.router.add_api_route(
            "/connections/{connection_id}",
            self.delete_erp_connection,
            methods=["DELETE"],
            summary="Delete ERP connection",
            description="Remove ERP connection",
            response_model=V1ResponseModel,
            dependencies=guard_deps,
        )
        
        # ERP Connection Testing
        self.router.add_api_route(
            "/connections/{connection_id}/test",
            self.test_erp_connection,
            methods=["POST"],
            summary="Test ERP connection",
            description="Test connectivity and authentication for ERP connection",
            response_model=V1ResponseModel,
            dependencies=guard_deps,
        )
        
        self.router.add_api_route(
            "/connections/{connection_id}/health",
            self.get_erp_connection_health,
            methods=["GET"],
            summary="Get ERP connection health",
            description="Get detailed health status of ERP connection",
            response_model=V1ResponseModel,
            dependencies=guard_deps,
        )
        
        # ERP Data Synchronization
        self.router.add_api_route(
            "/connections/{connection_id}/sync",
            self.sync_erp_data,
            methods=["POST"],
            summary="Sync ERP data",
            description="Synchronize data from ERP system",
            response_model=V1ResponseModel,
            dependencies=guard_deps,
        )
        
        self.router.add_api_route(
            "/connections/{connection_id}/sync-status",
            self.get_erp_sync_status,
            methods=["GET"],
            summary="Get ERP sync status",
            description="Get status of ERP data synchronization",
            response_model=V1ResponseModel,
            dependencies=guard_deps,
        )
        
        # ERP Data Extraction
        self.router.add_api_route(
            "/connections/{connection_id}/invoices",
            self.get_erp_invoices,
            methods=["GET"],
            summary="Get ERP invoices",
            description="Extract invoices from ERP system",
            response_model=V1ResponseModel,
            dependencies=guard_deps,
        )
        
        self.router.add_api_route(
            "/connections/{connection_id}/customers",
            self.get_erp_customers,
            methods=["GET"],
            summary="Get ERP customers",
            description="Extract customers from ERP system",
            response_model=V1ResponseModel,
            dependencies=guard_deps,
        )
        
        self.router.add_api_route(
            "/connections/{connection_id}/products",
            self.get_erp_products,
            methods=["GET"],
            summary="Get ERP products",
            description="Extract products from ERP system",
            response_model=V1ResponseModel,
            dependencies=guard_deps,
        )
        
        self.router.add_api_route(
            "/connections/{connection_id}/financial-data",
            self.get_erp_financial_data,
            methods=["GET"],
            summary="Get ERP financial data",
            description="Extract financial data from ERP system",
            response_model=V1ResponseModel,
            dependencies=guard_deps,
        )
        
        # ERP Schema and Mapping
        self.router.add_api_route(
            "/{erp_system}/schema",
            self.get_erp_schema,
            methods=["GET"],
            summary="Get ERP schema",
            description="Get data schema for specific ERP system",
            response_model=V1ResponseModel,
            dependencies=guard_deps,
        )
        
        self.router.add_api_route(
            "/connections/{connection_id}/field-mapping",
            self.get_erp_field_mapping,
            methods=["GET"],
            summary="Get ERP field mapping",
            description="Get field mapping configuration for ERP connection",
            response_model=V1ResponseModel,
            dependencies=guard_deps,
        )
        
        self.router.add_api_route(
            "/connections/{connection_id}/field-mapping",
            self.update_erp_field_mapping,
            methods=["PUT"],
            summary="Update ERP field mapping",
            description="Update field mapping configuration for ERP connection",
            response_model=V1ResponseModel,
            dependencies=guard_deps,
        )
        
        # Bulk Operations
        self.router.add_api_route(
            "/bulk/test-connections",
            self.bulk_test_erp_connections,
            methods=["POST"],
            summary="Bulk test ERP connections",
            description="Test multiple ERP connections at once",
            response_model=V1ResponseModel,
            dependencies=guard_deps,
        )
        
        self.router.add_api_route(
            "/bulk/sync-data",
            self.bulk_sync_erp_data,
            methods=["POST"],
            summary="Bulk sync ERP data",
            description="Synchronize data from multiple ERP systems",
            response_model=V1ResponseModel,
            dependencies=guard_deps,
        )

        # Test fetch paths (Odoo → FIRS transform) for pre‑submission validation
        self.router.add_api_route(
            "/odoo/test-fetch-invoices",
            self.test_fetch_invoices,
            methods=["POST"],
            summary="Test-fetch specific Odoo invoices",
            description="Fetch and transform specific Odoo invoices via SI to FIRS-compliant payloads",
            response_model=V1ResponseModel,
            dependencies=guard_deps,
        )
        self.router.add_api_route(
            "/odoo/test-fetch-batch",
            self.test_fetch_invoice_batch,
            methods=["POST"],
            summary="Test-fetch Odoo invoice batch",
            description="Fetch and transform a batch of Odoo invoices via SI to FIRS-compliant payloads",
            response_model=V1ResponseModel,
            dependencies=guard_deps,
        )

    async def _require_si_role(self, request: Request) -> HTTPRoutingContext:
        """Ensure System Integrator role access for v1 SI endpoints."""
        context = await self.role_detector.detect_role_context(request)
        if not context or not await self.permission_guard.check_endpoint_permission(
            context, f"v1/si{request.url.path}", request.method
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions for SI v1 endpoint")
        context.metadata["api_version"] = "v1"
        context.metadata["endpoint_group"] = "si"
        return context

    async def _get_si_context(self, request: Request) -> HTTPRoutingContext:
        """Fetch SI routing context from request state with fallback detection."""
        context = getattr(request.state, "routing_context", None)
        if isinstance(context, HTTPRoutingContext):
            return context
        return await self._require_si_role(request)

    async def _ensure_context(self, request: Request) -> HTTPRoutingContext:
        """Ensure routing context is present when used as a dependency."""
        return await self._get_si_context(request)
    
    # ERP System Discovery
    async def get_available_erp_systems(self, context: Optional[HTTPRoutingContext] = Depends(lambda: None)):
        """Get available ERP systems"""
        try:
            result = {
                "erp_systems": self.erp_systems,
                "total_count": len(self.erp_systems),
                "system_names": list(self.erp_systems.keys()),
                "supported_features": [
                    "invoice_data_extraction",
                    "customer_management",
                    "product_synchronization", 
                    "financial_data_integration",
                    "real_time_sync",
                    "field_mapping_customization"
                ]
            }
            
            return self._create_v1_response(result, "available_erp_systems_retrieved")
        except Exception as e:
            logger.error(f"Error getting available ERP systems in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to get available ERP systems")
    
    # ERP Connection Management
    async def list_erp_connections(self, 
                                  request: Request,
                                  organization_id: Optional[str] = Query(None, description="Filter by organization"),
                                  erp_system: Optional[str] = Query(None, description="Filter by ERP system"),
                                  status: Optional[str] = Query(None, description="Filter by connection status"),
                                  context: Optional[HTTPRoutingContext] = Depends(lambda: None)):
        """List ERP connections"""
        try:
            context = context or await self._get_si_context(request)
            # Validate ERP system if provided
            if erp_system and erp_system not in self.erp_systems:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid ERP system. Available: {', '.join(self.erp_systems.keys())}"
                )
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="list_erp_connections",
                payload={
                    "si_id": context.user_id,
                    "filters": {
                        "organization_id": organization_id,
                        "erp_system": erp_system,
                        "status": status
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "erp_connections_listed")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error listing ERP connections in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to list ERP connections")
    
    async def create_erp_connection(self, 
                                   request: Request,
                                   context: Optional[HTTPRoutingContext] = Depends(lambda: None)):
        """Create ERP connection"""
        try:
            context = context or await self._get_si_context(request)
            body = await request.json()
            
            # Validate required fields
            required_fields = ["erp_system", "organization_id", "connection_config"]
            missing_fields = [field for field in required_fields if field not in body]
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required fields: {', '.join(missing_fields)}"
                )
            
            # Validate ERP system
            if body["erp_system"] not in self.erp_systems:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid ERP system. Available: {', '.join(self.erp_systems.keys())}"
                )
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="create_erp_connection",
                payload={
                    "connection_data": body,
                    "si_id": context.user_id,
                    "system_type": "erp",
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "erp_connection_created", status_code=201)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating ERP connection in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to create ERP connection")
    
    async def get_erp_connection(self, 
                                connection_id: str,
                                request: Request,
                                context: Optional[HTTPRoutingContext] = Depends(lambda: None)):
        """Get ERP connection"""
        try:
            context = context or await self._get_si_context(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_erp_connection",
                payload={
                    "connection_id": connection_id,
                    "si_id": context.user_id,
                    "include_schema": True,
                    "include_mapping": True,
                    "api_version": "v1"
                }
            )
            
            if not result:
                raise HTTPException(status_code=404, detail="ERP connection not found")
            
            return self._create_v1_response(result, "erp_connection_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting ERP connection {connection_id} in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to get ERP connection")
    
    # Placeholder implementations for remaining endpoints
    async def update_erp_connection(self, connection_id: str, request: Request, context: Optional[HTTPRoutingContext] = Depends(lambda: None)):
        try:
            context = context or await self._get_si_context(request)
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="update_erp_connection",
                payload={
                    "connection_id": connection_id,
                    "connection_data": body,
                    "si_id": context.user_id,
                    "api_version": "v1",
                },
            )
            return self._create_v1_response(result, "erp_connection_updated")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating ERP connection {connection_id} in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to update ERP connection")

    async def delete_erp_connection(self, connection_id: str, request: Request):
        try:
            context = await self._get_si_context(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="delete_erp_connection",
                payload={
                    "connection_id": connection_id,
                    "si_id": context.user_id,
                    "api_version": "v1",
                },
            )
            return self._create_v1_response(result, "erp_connection_deleted")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error deleting ERP connection {connection_id} in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to delete ERP connection")
    
    async def test_erp_connection(self, connection_id: str, request: Request):
        try:
            context = await self._get_si_context(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="test_erp_connection",
                payload={
                    "connection_id": connection_id,
                    "si_id": context.user_id,
                    "api_version": "v1",
                },
            )
            return self._create_v1_response(result, "erp_connection_tested")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error testing ERP connection {connection_id} in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to test ERP connection")
    
    async def get_erp_connection_health(self, connection_id: str, request: Request, context: Optional[HTTPRoutingContext] = Depends(lambda: None)):
        try:
            context = context or await self._get_si_context(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_erp_connection_health",
                payload={
                    "connection_id": connection_id,
                    "si_id": context.user_id,
                    "api_version": "v1",
                },
            )
            return self._create_v1_response(result, "erp_connection_health_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting ERP connection health for {connection_id} in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to get ERP connection health")
    
    async def sync_erp_data(self, connection_id: str, request: Request, context: Optional[HTTPRoutingContext] = Depends(lambda: None)):
        try:
            context = context or await self._get_si_context(request)
            body = await request.json()
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Failed to parse sync payload for {connection_id}: {exc}")
            body = {}

        payload = {
            "connection_id": connection_id,
            "data_type": body.get("data_type", "invoices"),
            "options": body.get("options") or {},
            "force": bool(body.get("force", False)),
            "si_id": context.user_id if context else None,
        }

        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="sync_erp_data",
                payload=payload,
            )
            return self._create_v1_response(result, "erp_data_sync_initiated")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error syncing ERP data for {connection_id}: {e}")
            raise HTTPException(status_code=502, detail="Failed to queue ERP data sync")

    async def get_erp_sync_status(self, connection_id: str, request: Request, context: Optional[HTTPRoutingContext] = Depends(lambda: None)):
        try:
            context = context or await self._get_si_context(request)
        except HTTPException:
            raise
        except Exception:
            context = None

        try:
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_erp_sync_status",
                payload={
                    "connection_id": connection_id,
                    "si_id": context.user_id if context else None,
                },
            )
            return self._create_v1_response(result, "erp_sync_status_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrieving ERP sync status for {connection_id}: {e}")
            raise HTTPException(status_code=502, detail="Failed to retrieve ERP sync status")
    
    async def get_erp_invoices(self, connection_id: str, request: Request, context: Optional[HTTPRoutingContext] = Depends(lambda: None)):
        """Get ERP invoices - placeholder"""
        return self._create_v1_response({"invoices": []}, "erp_invoices_retrieved")
    
    async def get_erp_customers(self, connection_id: str, request: Request, context: Optional[HTTPRoutingContext] = Depends(lambda: None)):
        """Get ERP customers - placeholder"""
        return self._create_v1_response({"customers": []}, "erp_customers_retrieved")
    
    async def get_erp_products(self, connection_id: str, request: Request, context: Optional[HTTPRoutingContext] = Depends(lambda: None)):
        """Get ERP products - placeholder"""
        return self._create_v1_response({"products": []}, "erp_products_retrieved")
    
    async def get_erp_financial_data(self, connection_id: str, request: Request, context: Optional[HTTPRoutingContext] = Depends(lambda: None)):
        """Get ERP financial data - placeholder"""
        return self._create_v1_response({"financial_data": []}, "erp_financial_data_retrieved")
    
    async def get_erp_schema(self, erp_system: str, context: Optional[HTTPRoutingContext] = Depends(lambda: None)):
        """Get ERP schema - placeholder"""
        if erp_system not in self.erp_systems:
            raise HTTPException(status_code=404, detail="ERP system not found")
        return self._create_v1_response({"schema": {}}, "erp_schema_retrieved")
    
    async def get_erp_field_mapping(self, connection_id: str, context: Optional[HTTPRoutingContext] = Depends(lambda: None)):
        """Get ERP field mapping - placeholder"""
        return self._create_v1_response({"field_mapping": {}}, "erp_field_mapping_retrieved")
    
    async def update_erp_field_mapping(self, connection_id: str, request: Request, context: Optional[HTTPRoutingContext] = Depends(lambda: None)):
        """Update ERP field mapping - placeholder"""
        return self._create_v1_response({"connection_id": connection_id}, "erp_field_mapping_updated")
    
    async def bulk_test_erp_connections(self, request: Request, context: Optional[HTTPRoutingContext] = Depends(lambda: None)):
        try:
            context = context or await self._get_si_context(request)
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="bulk_test_erp_connections",
                payload={
                    "connection_ids": body.get("connection_ids") or [],
                    "options": body.get("options") or {},
                    "si_id": context.user_id,
                },
            )
            return self._create_v1_response(result, "bulk_erp_connection_tests_initiated")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error bulk testing ERP connections: {e}")
            raise HTTPException(status_code=502, detail="Failed to bulk test ERP connections")
    
    async def bulk_sync_erp_data(self, request: Request, context: Optional[HTTPRoutingContext] = Depends(lambda: None)):
        try:
            context = context or await self._get_si_context(request)
            body = await request.json()
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="bulk_sync_erp_data",
                payload={
                    "connection_ids": body.get("connection_ids") or [],
                    "data_type": body.get("data_type", "invoices"),
                    "options": body.get("options") or {},
                    "si_id": context.user_id,
                },
            )
            return self._create_v1_response(result, "bulk_erp_data_sync_initiated")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error bulk syncing ERP data: {e}")
            raise HTTPException(status_code=502, detail="Failed to bulk sync ERP data")

    # Test-fetch helpers (routes above)
    async def test_fetch_invoices(self, request: Request):
        try:
            context = await self._get_si_context(request)
            body = await request.json()
            invoice_ids = body.get("invoice_ids") or []
            if not isinstance(invoice_ids, list) or not invoice_ids:
                raise HTTPException(status_code=400, detail="invoice_ids must be a non-empty list")
            payload = {
                "invoice_ids": invoice_ids,
                "odoo_config": body.get("odoo_config") or {},
                "transform": bool(body.get("transform", True)),
                "target_format": body.get("target_format", "UBL_BIS_3.0"),
            }
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="fetch_odoo_invoices_for_firs",
                payload=payload,
            )
            # Attach summary
            data = result.get("data") if isinstance(result, dict) else {}
            if isinstance(data, dict):
                data["fetched_count"] = len(data.get("invoices") or [])
            return self._create_v1_response(result, "odoo_invoices_fetched_for_firs")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error test-fetching invoices: {e}")
            raise HTTPException(status_code=502, detail="Failed to test-fetch invoices")

    async def test_fetch_invoice_batch(self, request: Request):
        try:
            context = await self._get_si_context(request)
            body = await request.json()
            payload = {
                "batch_size": int(body.get("batch_size", 50)),
                "include_attachments": bool(body.get("include_attachments", False)),
                "odoo_config": body.get("odoo_config") or {},
                "transform": bool(body.get("transform", True)),
                "target_format": body.get("target_format", "UBL_BIS_3.0"),
            }
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="fetch_odoo_invoice_batch_for_firs",
                payload=payload,
            )
            data = result.get("data") if isinstance(result, dict) else {}
            if isinstance(data, dict):
                data["fetched_count"] = len(data.get("invoices") or [])
            return self._create_v1_response(result, "odoo_invoice_batch_fetched_for_firs")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error test-fetching invoice batch: {e}")
            raise HTTPException(status_code=502, detail="Failed to test-fetch invoice batch")
    
    def _create_v1_response(self, data: Dict[str, Any], action: str, status_code: int = 200) -> V1ResponseModel:
        """Create standardized v1 response format"""
        return build_v1_response(data, action)


def create_erp_router(role_detector: HTTPRoleDetector,
                     permission_guard: APIPermissionGuard,
                     message_router: MessageRouter) -> APIRouter:
    """Factory function to create ERP Router"""
    erp_endpoints = ERPEndpointsV1(role_detector, permission_guard, message_router)
    return erp_endpoints.router
