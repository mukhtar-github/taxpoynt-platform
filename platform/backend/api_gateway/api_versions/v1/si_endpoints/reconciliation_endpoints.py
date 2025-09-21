"""
Auto-Reconciliation Configuration Endpoints - API v1
===================================================
System Integrator endpoints for managing auto-reconciliation rules and transaction categorization.
Integrates with the Universal Transaction Processor for real-time transaction processing.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status
from fastapi.responses import JSONResponse
from datetime import datetime

from core_platform.authentication.role_manager import PlatformRole
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


class ReconciliationEndpointsV1:
    """
    Auto-Reconciliation Configuration Endpoints - Version 1
    =======================================================
    Manages auto-reconciliation rules and transaction categorization for System Integrators.
    
    **Key Features:**
    - Transaction categorization rules management
    - Auto-detection keyword configuration
    - Matching criteria setup (amount tolerance, date range)
    - Integration with Universal Transaction Processor
    - Real-time rule updates for live transaction processing
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(
            prefix="/reconciliation",
            tags=["Auto-Reconciliation V1"],
            dependencies=[Depends(self._require_si_role)]
        )
        
        self._setup_routes()
        logger.info("Auto-Reconciliation Endpoints V1 initialized")
    
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
        """Setup auto-reconciliation management routes"""
        
        # Configuration Management
        self.router.add_api_route(
            "/configuration",
            self.save_reconciliation_configuration,
            methods=["POST"],
            summary="Save reconciliation configuration",
            description="Save auto-reconciliation rules and transaction categorization settings",
            response_model=V1ResponseModel,
            status_code=201
        )
        
        self.router.add_api_route(
            "/configuration",
            self.get_reconciliation_configuration,
            methods=["GET"],
            summary="Get reconciliation configuration",
            description="Retrieve current auto-reconciliation configuration",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/configuration",
            self.update_reconciliation_configuration,
            methods=["PUT"],
            summary="Update reconciliation configuration",
            description="Update auto-reconciliation rules and settings",
            response_model=V1ResponseModel
        )
        
        # Category Rules Management
        self.router.add_api_route(
            "/categories",
            self.list_transaction_categories,
            methods=["GET"],
            summary="List transaction categories",
            description="Get all configured transaction categories with auto-detection rules",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/categories",
            self.create_transaction_category,
            methods=["POST"],
            summary="Create transaction category",
            description="Create new transaction category with auto-detection keywords",
            response_model=V1ResponseModel,
            status_code=201
        )
        
        self.router.add_api_route(
            "/categories/{category_id}",
            self.update_transaction_category,
            methods=["PUT"],
            summary="Update transaction category",
            description="Update transaction category settings and keywords",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/categories/{category_id}",
            self.delete_transaction_category,
            methods=["DELETE"],
            summary="Delete transaction category",
            description="Remove transaction category from auto-reconciliation",
            response_model=V1ResponseModel
        )
        
        # Pattern Matching Integration
        self.router.add_api_route(
            "/patterns/test",
            self.test_pattern_matching,
            methods=["POST"],
            summary="Test pattern matching",
            description="Test auto-detection patterns against sample transactions",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/patterns/statistics",
            self.get_pattern_statistics,
            methods=["GET"],
            summary="Get pattern matching statistics",
            description="Get performance statistics for auto-reconciliation patterns",
            response_model=V1ResponseModel
        )
        
        # Universal Transaction Processor Integration
        self.router.add_api_route(
            "/processor/status",
            self.get_processor_integration_status,
            methods=["GET"],
            summary="Get processor integration status",
            description="Check Universal Transaction Processor integration status",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/processor/sync",
            self.sync_with_transaction_processor,
            methods=["POST"],
            summary="Sync with transaction processor",
            description="Synchronize reconciliation rules with Universal Transaction Processor",
            response_model=V1ResponseModel
        )

    # Configuration Management Endpoints
    async def save_reconciliation_configuration(self,
                                              request: Request,
                                              db: AsyncSession = Depends(get_async_session),
                                              context: HTTPRoutingContext = Depends(lambda: None)):
        """Save auto-reconciliation configuration"""
        try:
            context = await self._require_si_role(request)
            config_data = await request.json()
            
            # Validate configuration structure
            required_fields = ["rules", "matchingCriteria", "categoryRules", "organizationId"]
            missing_fields = [field for field in required_fields if field not in config_data]
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required fields: {', '.join(missing_fields)}"
                )
            
            # Route to SI services for processing and storage
            # Idempotency
            idem_key = request.headers.get("x-idempotency-key") or request.headers.get("idempotency-key")
            if idem_key:
                req_hash = IdempotencyStore.compute_request_hash(config_data)
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
                    return self._create_v1_response(stored, "reconciliation_configuration_saved", status_code=stored_code or 201)

            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="save_reconciliation_configuration",
                payload={
                    "configuration": config_data,
                    "si_id": context.user_id,
                    "organization_id": config_data["organizationId"],
                    "api_version": "v1"
                }
            )
            
            # Update Universal Transaction Processor with new rules
            await self._update_transaction_processor_rules(config_data, context.user_id)
            
            if idem_key:
                await IdempotencyStore.finalize_success(
                    db,
                    requester_id=str(context.user_id) if context and context.user_id else None,
                    key=idem_key,
                    response=result,
                    status_code=201,
                )
            return self._create_v1_response(result, "reconciliation_configuration_saved", status_code=201)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error saving reconciliation configuration in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to save reconciliation configuration")

    async def get_reconciliation_configuration(self,
                                             request: Request,
                                             context: HTTPRoutingContext = Depends(lambda: None)):
        """Get current reconciliation configuration"""
        try:
            context = await self._require_si_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_reconciliation_configuration",
                payload={
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "reconciliation_configuration_retrieved")
            
        except Exception as e:
            logger.error(f"Error getting reconciliation configuration in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get reconciliation configuration")

    async def update_reconciliation_configuration(self,
                                                request: Request,
                                                db: AsyncSession = Depends(get_async_session),
                                                context: HTTPRoutingContext = Depends(lambda: None)):
        """Update reconciliation configuration"""
        try:
            context = await self._require_si_role(request)
            updates = await request.json()
            
            idem_key = request.headers.get("x-idempotency-key") or request.headers.get("idempotency-key")
            if idem_key:
                req_hash = IdempotencyStore.compute_request_hash(updates)
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
                    return self._create_v1_response(stored, "reconciliation_configuration_updated", status_code=stored_code or 200)

            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="update_reconciliation_configuration",
                payload={
                    "updates": updates,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            # Sync changes with Universal Transaction Processor
            await self._update_transaction_processor_rules(updates, context.user_id)
            
            if idem_key:
                await IdempotencyStore.finalize_success(
                    db,
                    requester_id=str(context.user_id) if context and context.user_id else None,
                    key=idem_key,
                    response=result,
                    status_code=200,
                )
            return self._create_v1_response(result, "reconciliation_configuration_updated")
            
        except Exception as e:
            logger.error(f"Error updating reconciliation configuration in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to update reconciliation configuration")

    # Category Management Endpoints
    async def list_transaction_categories(self,
                                        request: Request,
                                        context: HTTPRoutingContext = Depends(lambda: None)):
        """List all transaction categories"""
        try:
            context = await self._require_si_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="list_transaction_categories",
                payload={
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "transaction_categories_listed")
            
        except Exception as e:
            logger.error(f"Error listing transaction categories in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to list transaction categories")

    async def create_transaction_category(self,
                                        request: Request,
                                        db: AsyncSession = Depends(get_async_session),
                                        context: HTTPRoutingContext = Depends(lambda: None)):
        """Create new transaction category"""
        try:
            context = await self._require_si_role(request)
            category_data = await request.json()
            
            # Validate category data
            required_fields = ["name", "keywords", "color"]
            missing_fields = [field for field in required_fields if field not in category_data]
            if missing_fields:
                raise HTTPException(
                    status_code=400,
                    detail=f"Missing required fields: {', '.join(missing_fields)}"
                )
            
            idem_key = request.headers.get("x-idempotency-key") or request.headers.get("idempotency-key")
            if idem_key:
                req_hash = IdempotencyStore.compute_request_hash(category_data)
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
                    return self._create_v1_response(stored, "transaction_category_created", status_code=stored_code or 201)

            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="create_transaction_category",
                payload={
                    "category_data": category_data,
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
                    status_code=201,
                )
            return self._create_v1_response(result, "transaction_category_created", status_code=201)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error creating transaction category in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to create transaction category")

    async def update_transaction_category(self,
                                        category_id: str,
                                        request: Request,
                                        db: AsyncSession = Depends(get_async_session),
                                        context: HTTPRoutingContext = Depends(lambda: None)):
        """Update transaction category"""
        try:
            context = await self._require_si_role(request)
            updates = await request.json()
            
            idem_key = request.headers.get("x-idempotency-key") or request.headers.get("idempotency-key")
            if idem_key:
                composite = {"category_id": category_id, "updates": updates}
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
                    return self._create_v1_response(stored, "transaction_category_updated", status_code=stored_code or 200)

            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="update_transaction_category",
                payload={
                    "category_id": category_id,
                    "updates": updates,
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
            return self._create_v1_response(result, "transaction_category_updated")
            
        except Exception as e:
            logger.error(f"Error updating transaction category {category_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to update transaction category")

    async def delete_transaction_category(self,
                                        category_id: str,
                                        request: Request,
                                        db: AsyncSession = Depends(get_async_session),
                                        context: HTTPRoutingContext = Depends(lambda: None)):
        """Delete transaction category"""
        try:
            context = await self._require_si_role(request)
            idem_key = request.headers.get("x-idempotency-key") or request.headers.get("idempotency-key")
            if idem_key:
                req_hash = IdempotencyStore.compute_request_hash({"category_id": category_id})
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
                    return self._create_v1_response(stored, "transaction_category_deleted", status_code=stored_code or 200)

            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="delete_transaction_category",
                payload={
                    "category_id": category_id,
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
            return self._create_v1_response(result, "transaction_category_deleted")
            
        except Exception as e:
            logger.error(f"Error deleting transaction category {category_id} in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to delete transaction category")

    # Pattern Matching Integration
    async def test_pattern_matching(self,
                                  request: Request,
                                  context: HTTPRoutingContext = Depends(lambda: None)):
        """Test pattern matching against sample transactions"""
        try:
            context = await self._require_si_role(request)
            test_data = await request.json()
            
            # Validate test data
            if "sample_transactions" not in test_data:
                raise HTTPException(
                    status_code=400,
                    detail="Missing sample_transactions in request"
                )
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="test_pattern_matching",
                payload={
                    "test_data": test_data,
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "pattern_matching_tested")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error testing pattern matching in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to test pattern matching")

    async def get_pattern_statistics(self,
                                   request: Request,
                                   context: HTTPRoutingContext = Depends(lambda: None)):
        """Get pattern matching performance statistics"""
        try:
            context = await self._require_si_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_pattern_statistics",
                payload={
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "pattern_statistics_retrieved")
            
        except Exception as e:
            logger.error(f"Error getting pattern statistics in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get pattern statistics")

    # Universal Transaction Processor Integration
    async def get_processor_integration_status(self,
                                             request: Request,
                                             context: HTTPRoutingContext = Depends(lambda: None)):
        """Get Universal Transaction Processor integration status"""
        try:
            context = await self._require_si_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="get_processor_integration_status",
                payload={
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "processor_integration_status_retrieved")
            
        except Exception as e:
            logger.error(f"Error getting processor integration status in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to get processor integration status")

    async def sync_with_transaction_processor(self,
                                            request: Request,
                                            context: HTTPRoutingContext = Depends(lambda: None)):
        """Sync reconciliation rules with Universal Transaction Processor"""
        try:
            context = await self._require_si_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="sync_with_transaction_processor",
                payload={
                    "si_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "processor_sync_completed")
            
        except Exception as e:
            logger.error(f"Error syncing with transaction processor in v1: {e}")
            raise HTTPException(status_code=500, detail="Failed to sync with transaction processor")

    # Helper Methods
    async def _update_transaction_processor_rules(self, config_data: Dict[str, Any], si_id: str):
        """Update Universal Transaction Processor with new reconciliation rules"""
        try:
            # Extract pattern matching rules for the universal processor
            pattern_rules = []
            
            # Convert category rules to pattern matching format
            for category in config_data.get("categoryRules", []):
                if category.get("enabled", False):
                    pattern_rules.append({
                        "category_id": category["id"],
                        "category_name": category["name"],
                        "keywords": category.get("keywords", []),
                        "pattern_type": "keyword_matching",
                        "confidence_threshold": 0.8
                    })
            
            # Update the Universal Transaction Processor
            await self.message_router.route_message(
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                operation="update_universal_processor_patterns",
                payload={
                    "si_id": si_id,
                    "pattern_rules": pattern_rules,
                    "matching_criteria": config_data.get("matchingCriteria", {}),
                    "api_version": "v1"
                }
            )
            
            logger.info(f"Updated Universal Transaction Processor with {len(pattern_rules)} pattern rules")
            
        except Exception as e:
            logger.warning(f"Failed to update Universal Transaction Processor: {e}")
            # Don't fail the main operation if processor update fails

    def _create_v1_response(self, data: Dict[str, Any], action: str, status_code: int = 200) -> V1ResponseModel:
        """Create standardized v1 response format using V1ResponseModel"""
        return build_v1_response(data, action)


def create_reconciliation_router(role_detector: HTTPRoleDetector,
                               permission_guard: APIPermissionGuard,
                               message_router: MessageRouter) -> APIRouter:
    """Factory function to create Reconciliation Router"""
    reconciliation_endpoints = ReconciliationEndpointsV1(role_detector, permission_guard, message_router)
    return reconciliation_endpoints.router
