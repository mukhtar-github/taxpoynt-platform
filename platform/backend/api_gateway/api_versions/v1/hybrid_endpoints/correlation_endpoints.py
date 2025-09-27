"""
SI-APP Correlation API Endpoints
===============================
API endpoints for managing SI-APP correlations and status synchronization.
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, status, Request, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from core_platform.data_management.db_async import get_async_session
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from core_platform.authentication.role_manager import PlatformRole
from hybrid_services.correlation_management.si_app_correlation_service import SIAPPCorrelationService
from core_platform.data_management.models.si_app_correlation import CorrelationStatus

logger = logging.getLogger(__name__)


# Request/Response Models
class CorrelationUpdateRequest(BaseModel):
    """Request model for updating correlation status."""
    status: str = Field(..., description="New correlation status")
    app_submission_id: Optional[str] = Field(None, description="APP submission ID")
    firs_response_id: Optional[str] = Field(None, description="FIRS response ID")
    firs_status: Optional[str] = Field(None, description="FIRS status")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    response_data: Optional[Dict[str, Any]] = Field(None, description="Full response data")
    identifiers: Optional[Dict[str, Any]] = Field(None, description="Normalized identifiers extracted from FIRS response")


class CorrelationResponse(BaseModel):
    """Response model for correlation data."""
    id: str
    correlation_id: str
    organization_id: str
    si_invoice_id: str
    app_submission_id: Optional[str]
    irn: str
    current_status: str
    last_status_update: str
    invoice_number: str
    total_amount: float
    currency: str
    customer_name: str
    processing_duration: int
    is_complete: bool
    is_successful: bool
    retry_count: str
    firs_status: Optional[str]


class CorrelationListResponse(BaseModel):
    """Response model for correlation list."""
    correlations: List[CorrelationResponse]
    total_count: int
    page: int
    page_size: int


class CorrelationStatsResponse(BaseModel):
    """Response model for correlation statistics."""
    total_correlations: int
    status_breakdown: Dict[str, int]
    success_rate: float
    average_processing_time: float
    period_days: int


def create_correlation_router(
    role_detector: HTTPRoleDetector,
    permission_guard: APIPermissionGuard,
) -> APIRouter:
    """Create and configure the correlation management router."""
    router = APIRouter(
        prefix="/correlations",
        tags=["SI-APP Correlations"],
        dependencies=[]  # Role checks will be done per endpoint
    )

    async def _require_hybrid_role(request: Request) -> HTTPRoutingContext:
        """Require hybrid role for correlation management."""
        context = await role_detector.detect_role_context(request)
        if not context or not context.has_role(PlatformRole.HYBRID):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hybrid role required")
        if not await permission_guard.check_endpoint_permission(
            context, f"v1/hybrid{request.url.path}", request.method
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return context

    async def _require_app_role(request: Request) -> HTTPRoutingContext:
        """Require APP role for status updates."""
        context = await role_detector.detect_role_context(request)
        if not context or not context.has_role(PlatformRole.ACCESS_POINT_PROVIDER):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="APP role required")
        if not await permission_guard.check_endpoint_permission(
            context, f"v1/app{request.url.path}", request.method
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return context

    async def _require_si_role(request: Request) -> HTTPRoutingContext:
        """Require SI role for correlation queries."""
        context = await role_detector.detect_role_context(request)
        if not context or not context.has_role(PlatformRole.SYSTEM_INTEGRATOR):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="SI role required")
        if not await permission_guard.check_endpoint_permission(
            context, f"v1/si{request.url.path}", request.method
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return context

    @router.get(
        "/",
        response_model=CorrelationListResponse,
        summary="Get correlations",
        description="Get correlations for organization with optional filtering"
    )
    async def get_correlations(
        status_filter: Optional[str] = Query(None, description="Filter by status"),
        page: int = Query(1, ge=1, description="Page number"),
        page_size: int = Query(50, ge=1, le=100, description="Page size"),
        context: HTTPRoutingContext = Depends(_require_hybrid_role),
        db: AsyncSession = Depends(get_async_session)
    ):
        """Get correlations for the organization."""
        try:
            correlation_service = SIAPPCorrelationService(db)
            
            # Parse status filter
            correlation_status = None
            if status_filter:
                try:
                    correlation_status = CorrelationStatus(status_filter.lower())
                except ValueError:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Invalid status: {status_filter}"
                    )
            
            # Get correlations
            offset = (page - 1) * page_size
            correlations = await correlation_service.get_organization_correlations(
                organization_id=context.organization_id,
                status=correlation_status,
                limit=page_size,
                offset=offset
            )
            
            # Convert to response format
            correlation_responses = []
            for correlation in correlations:
                correlation_responses.append(CorrelationResponse(**correlation.to_dict()))
            
            return CorrelationListResponse(
                correlations=correlation_responses,
                total_count=len(correlation_responses),  # In real implementation, get total count separately
                page=page,
                page_size=page_size
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting correlations: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get correlations"
            )

    @router.get(
        "/{correlation_id}",
        response_model=CorrelationResponse,
        summary="Get correlation by ID",
        description="Get detailed correlation information by correlation ID"
    )
    async def get_correlation(
        correlation_id: str,
        context: HTTPRoutingContext = Depends(_require_hybrid_role),
        db: AsyncSession = Depends(get_async_session)
    ):
        """Get correlation by ID."""
        try:
            correlation_service = SIAPPCorrelationService(db)
            correlation = await correlation_service.get_correlation_by_id(correlation_id)
            
            if not correlation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Correlation not found"
                )
            
            # Check organization access
            if correlation.organization_id != context.organization_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied"
                )
            
            return CorrelationResponse(**correlation.to_dict())
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting correlation {correlation_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get correlation"
            )

    @router.post(
        "/irn/{irn}/app-received",
        summary="Update correlation - APP received",
        description="Update correlation status when APP receives invoice from SI"
    )
    async def update_app_received(
        irn: str,
        request: CorrelationUpdateRequest,
        context: HTTPRoutingContext = Depends(_require_app_role),
        db: AsyncSession = Depends(get_async_session)
    ):
        """Update correlation when APP receives invoice from SI."""
        try:
            correlation_service = SIAPPCorrelationService(db)
            
            success = await correlation_service.update_app_received(
                irn=irn,
                app_submission_id=request.app_submission_id or f"APP-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
                metadata=request.metadata
            )
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Correlation not found for IRN"
                )
            
            return {"success": True, "message": "Correlation updated - APP received"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating APP received for IRN {irn}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update correlation"
            )

    @router.post(
        "/irn/{irn}/app-submitting",
        summary="Update correlation - APP submitting",
        description="Update correlation status when APP starts submitting to FIRS"
    )
    async def update_app_submitting(
        irn: str,
        request: CorrelationUpdateRequest,
        context: HTTPRoutingContext = Depends(_require_app_role),
        db: AsyncSession = Depends(get_async_session)
    ):
        """Update correlation when APP starts submitting to FIRS."""
        try:
            correlation_service = SIAPPCorrelationService(db)
            
            success = await correlation_service.update_app_submitting(
                irn=irn,
                metadata=request.metadata
            )
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Correlation not found for IRN"
                )
            
            return {"success": True, "message": "Correlation updated - APP submitting"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating APP submitting for IRN {irn}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update correlation"
            )

    @router.post(
        "/irn/{irn}/app-submitted",
        summary="Update correlation - APP submitted",
        description="Update correlation status when APP completes submission to FIRS"
    )
    async def update_app_submitted(
        irn: str,
        request: CorrelationUpdateRequest,
        context: HTTPRoutingContext = Depends(_require_app_role),
        db: AsyncSession = Depends(get_async_session)
    ):
        """Update correlation when APP completes submission to FIRS."""
        try:
            correlation_service = SIAPPCorrelationService(db)
            
            success = await correlation_service.update_app_submitted(
                irn=irn,
                metadata=request.metadata
            )
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Correlation not found for IRN"
                )
            
            return {"success": True, "message": "Correlation updated - APP submitted"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating APP submitted for IRN {irn}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update correlation"
            )

    @router.post(
        "/irn/{irn}/firs-response",
        summary="Update correlation - FIRS response",
        description="Update correlation status based on FIRS response"
    )
    async def update_firs_response(
        irn: str,
        request: CorrelationUpdateRequest,
        context: HTTPRoutingContext = Depends(_require_app_role),
        db: AsyncSession = Depends(get_async_session)
    ):
        """Update correlation with FIRS response information."""
        try:
            # Validate required fields for FIRS response
            if not request.firs_status:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="FIRS status is required"
                )
            
            correlation_service = SIAPPCorrelationService(db)
            
            success = await correlation_service.update_firs_response(
                irn=irn,
                firs_response_id=request.firs_response_id,
                firs_status=request.firs_status,
                response_data=request.response_data,
                identifiers=request.identifiers
            )
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Correlation not found for IRN"
                )
            
            return {"success": True, "message": f"Correlation updated - FIRS response: {request.firs_status}"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error updating FIRS response for IRN {irn}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to update correlation"
            )

    @router.get(
        "/statistics",
        response_model=CorrelationStatsResponse,
        summary="Get correlation statistics",
        description="Get correlation statistics for the organization"
    )
    async def get_correlation_statistics(
        days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
        context: HTTPRoutingContext = Depends(_require_hybrid_role),
        db: AsyncSession = Depends(get_async_session)
    ):
        """Get correlation statistics."""
        try:
            correlation_service = SIAPPCorrelationService(db)
            
            stats = await correlation_service.get_correlation_statistics(
                organization_id=context.organization_id,
                days=days
            )
            
            return CorrelationStatsResponse(**stats)
            
        except Exception as e:
            logger.error(f"Error getting correlation statistics: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get correlation statistics"
            )

    @router.get(
        "/pending",
        response_model=List[CorrelationResponse],
        summary="Get pending correlations",
        description="Get correlations pending APP processing"
    )
    async def get_pending_correlations(
        limit: int = Query(100, ge=1, le=500, description="Maximum number of correlations to return"),
        context: HTTPRoutingContext = Depends(_require_app_role),
        db: AsyncSession = Depends(get_async_session)
    ):
        """Get correlations pending APP processing."""
        try:
            correlation_service = SIAPPCorrelationService(db)
            
            correlations = await correlation_service.get_pending_correlations(limit=limit)
            
            # Filter by organization
            org_correlations = [
                correlation for correlation in correlations 
                if correlation.organization_id == context.organization_id
            ]
            
            correlation_responses = []
            for correlation in org_correlations:
                correlation_responses.append(CorrelationResponse(**correlation.to_dict()))
            
            return correlation_responses
            
        except Exception as e:
            logger.error(f"Error getting pending correlations: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get pending correlations"
            )

    @router.post(
        "/{correlation_id}/retry",
        summary="Retry failed correlation",
        description="Retry a failed correlation"
    )
    async def retry_correlation(
        correlation_id: str,
        context: HTTPRoutingContext = Depends(_require_hybrid_role),
        db: AsyncSession = Depends(get_async_session)
    ):
        """Retry a failed correlation."""
        try:
            correlation_service = SIAPPCorrelationService(db)
            
            success = await correlation_service.retry_failed_correlation(correlation_id)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot retry correlation (not found or max retries exceeded)"
                )
            
            return {"success": True, "message": "Correlation queued for retry"}
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error retrying correlation {correlation_id}: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retry correlation"
            )

    return router
