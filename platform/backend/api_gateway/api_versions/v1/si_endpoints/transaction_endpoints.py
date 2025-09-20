"""
Transaction Processing Endpoints - API v1
==========================================
System Integrator endpoints for transaction processing and management.
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
from sqlalchemy.ext.asyncio import AsyncSession
from core_platform.data_management.db_async import get_async_session
from core_platform.data_management.repositories.firs_submission_repo_async import (
    list_submissions_filtered,
)
from api_gateway.utils.pagination import normalize_pagination
from core_platform.authentication.tenant_context import set_current_tenant, clear_current_tenant

logger = logging.getLogger(__name__)


class TransactionEndpointsV1:
    """Transaction Processing Endpoints - Version 1"""
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(prefix="/transactions", tags=["Transactions V1"])
        
        self._setup_routes()
        logger.info("Transaction Endpoints V1 initialized")
    
    def _setup_routes(self):
        """Setup transaction processing routes"""
        
        self.router.add_api_route(
            "",
            self.list_transactions,
            methods=["GET"],
            summary="List transactions",
            description="Get processed transactions",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/process",
            self.process_transaction_batch,
            methods=["POST"],
            summary="Process transaction batch",
            description="Process batch of transactions for e-invoicing",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{transaction_id}",
            self.get_transaction,
            methods=["GET"],
            summary="Get transaction",
            description="Get specific transaction details",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/{transaction_id}/status",
            self.get_transaction_status,
            methods=["GET"],
            summary="Get transaction status",
            description="Get transaction processing status",
            response_model=V1ResponseModel
        )
    
    # Read-heavy endpoint migrated to async DB
    async def list_transactions(
        self,
        request: Request,
        org_id: Optional[str] = Query(None, description="Scope by organization ID (optional)"),
        status: Optional[str] = Query(None, description="Filter by submission status"),
        start_date: Optional[str] = Query(None, description="Filter by start date (ISO)"),
        end_date: Optional[str] = Query(None, description="Filter by end date (ISO)"),
        limit: int = Query(50, ge=1, le=1000, description="Items per page"),
        offset: int = Query(0, ge=0, description="Offset for pagination"),
        db: AsyncSession = Depends(get_async_session),
    ):
        """List transmissions/transactions (async, optionally tenant-scoped)."""
        try:
            if org_id:
                set_current_tenant(org_id)
            try:
                rows = await list_submissions_filtered(
                    db,
                    status=status,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit,
                    offset=offset,
                )
            finally:
                if org_id:
                    clear_current_tenant()

            payload = {
                "count": len(rows),
                "items": [
                    {
                        "invoice_number": getattr(r, "invoice_number", None),
                        "status": getattr(r, "status", None).value if getattr(r, "status", None) else None,
                        "created_at": getattr(r, "created_at", None).isoformat() if getattr(r, "created_at", None) else None,
                        "irn": getattr(r, "irn", None),
                        "total_amount": float(getattr(r, "total_amount", 0) or 0),
                        "currency": getattr(r, "currency", None),
                        "organization_id": str(getattr(r, "organization_id", "")) if getattr(r, "organization_id", None) else None,
                    }
                    for r in rows
                ],
                "pagination": normalize_pagination(limit=limit, offset=offset, total=len(rows)),
            }
            return self._create_v1_response(payload, "transactions_listed")
        except Exception as e:
            logger.error(f"Error listing transactions in v1: {e}")
            raise HTTPException(status_code=502, detail="Failed to list transactions")
    
    async def process_transaction_batch(self, request: Request, context: HTTPRoutingContext = Depends(self._require_si_role)):
        """Process transaction batch"""
        return self._create_v1_response({"batch_id": "batch_123"}, "transaction_batch_processed")
    
    async def get_transaction(self, transaction_id: str, context: HTTPRoutingContext = Depends(self._require_si_role)):
        """Get transaction"""
        return self._create_v1_response({"transaction_id": transaction_id}, "transaction_retrieved")
    
    async def get_transaction_status(self, transaction_id: str, context: HTTPRoutingContext = Depends(self._require_si_role)):
        """Get transaction status"""
        return self._create_v1_response({"status": "processed"}, "transaction_status_retrieved")
    
    def _create_v1_response(self, data: Dict[str, Any], action: str, status_code: int = 200) -> V1ResponseModel:
        """Create standardized v1 response format"""
        return build_v1_response(data, action)


def create_transaction_router(role_detector: HTTPRoleDetector,
                             permission_guard: APIPermissionGuard,
                             message_router: MessageRouter) -> APIRouter:
    """Factory function to create Transaction Router"""
    transaction_endpoints = TransactionEndpointsV1(role_detector, permission_guard, message_router)
    return transaction_endpoints.router
