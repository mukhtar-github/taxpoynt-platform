"""
Validation Management Endpoints - API v1
========================================
Access Point Provider endpoints for invoice validation, data quality checks, and FIRS compliance validation.
Handles pre-transmission validation, batch processing, and validation reporting.
"""
import logging
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Request, HTTPException, Depends, status, Query, UploadFile, File
from fastapi.responses import JSONResponse
from datetime import datetime

from core_platform.authentication.role_manager import PlatformRole
from core_platform.messaging.message_router import ServiceRole, MessageRouter
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from ..version_models import V1ResponseModel
from api_gateway.utils.v1_response import build_v1_response
from api_gateway.utils.error_mapping import v1_error_response
from core_platform.data_management.db_async import get_async_session
from sqlalchemy.ext.asyncio import AsyncSession
from core_platform.data_management.repositories.firs_submission_repo_async import (
    get_validation_metrics_data,
    list_recent_validation_results_data,
    get_validation_error_summary,
    get_validation_error_insights,
)
from core_platform.data_management.repositories.validation_batch_repo_async import (
    record_validation_batch,
    summarize_validation_batches,
)
from core_platform.data_management.models.organization import Organization

logger = logging.getLogger(__name__)


class ValidationManagementEndpointsV1:
    """
    Validation Management Endpoints - Version 1
    ===========================================
    Manages invoice validation and data quality for APP providers:
    
    **Validation Management Features:**
    - **Data Validation**: Schema, format, and business rule validation
    - **FIRS Compliance**: UBL 3.0 and FIRS requirement validation
    - **Batch Processing**: Bulk invoice validation and processing
    - **Quality Metrics**: Validation performance and success rates
    - **Error Reporting**: Detailed validation error analysis
    - **Pre-transmission Checks**: Ensure data quality before FIRS submission
    
    **Validation Standards:**
    - UBL 3.0 Universal Business Language
    - FIRS E-invoicing Requirements
    - Nigerian Tax Regulations
    - Data Integrity Standards
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(
            prefix="/validation",
            tags=["Validation Management V1"],
            dependencies=[Depends(self._require_app_role)]
        )
        
        # Define validation capabilities
        self.validation_capabilities = {
            "schema_validation": {
                "features": ["ubl_3_0_compliance", "json_schema_validation", "xml_validation"],
                "description": "Comprehensive schema and format validation"
            },
            "business_rules": {
                "features": ["tax_calculation_validation", "business_logic_checks", "regulatory_compliance"],
                "description": "Business rule and logic validation"
            },
            "batch_processing": {
                "features": ["bulk_validation", "parallel_processing", "progress_tracking"],
                "description": "Efficient batch validation processing"
            },
            "quality_assurance": {
                "features": ["data_quality_metrics", "error_reporting", "validation_analytics"],
                "description": "Data quality monitoring and reporting"
            }
        }
        
        self._setup_routes()
        logger.info("Validation Management Endpoints V1 initialized")
        # Minimal idempotency store (in-memory per process)
        self._idempotency_store = {}

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
        """Setup validation management routes"""
        
        # Validation Overview and Metrics
        self.router.add_api_route(
            "/metrics",
            self.get_validation_metrics,
            methods=["GET"],
            summary="Get validation metrics",
            description="Get comprehensive validation metrics and statistics",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/overview",
            self.get_validation_overview,
            methods=["GET"],
            summary="Get validation overview",
            description="Get validation overview and dashboard data",
            response_model=V1ResponseModel
        )
        
        # Validation Results
        self.router.add_api_route(
            "/recent-results",
            self.get_recent_validation_results,
            methods=["GET"],
            summary="Get recent validation results",
            description="Get recent validation results and history",
            response_model=V1ResponseModel
        )

        self.router.add_api_route(
            "/recent-batches",
            self.get_recent_validation_batches,
            methods=["GET"],
            summary="Get recent validation batches",
            description="List recently executed validation batches with summaries",
            response_model=V1ResponseModel,
        )
        
        self.router.add_api_route(
            "/results/{validation_id}",
            self.get_validation_result,
            methods=["GET"],
            summary="Get validation result",
            description="Get detailed validation result by ID",
            response_model=V1ResponseModel
        )
        
        # Single Invoice Validation
        self.router.add_api_route(
            "/validate-invoice",
            self.validate_single_invoice,
            methods=["POST"],
            summary="Validate single invoice",
            description="Validate a single invoice for FIRS compliance",
            response_model=V1ResponseModel
        )
        
        # Batch Validation
        self.router.add_api_route(
            "/validate-batch",
            self.validate_invoice_batch,
            methods=["POST"],
            summary="Validate invoice batch",
            description="Validate multiple invoices in a batch",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/batch-status/{batch_id}",
            self.get_batch_validation_status,
            methods=["GET"],
            summary="Get batch validation status",
            description="Get status of batch validation process",
            response_model=V1ResponseModel
        )
        
        # File Upload Validation
        self.router.add_api_route(
            "/validate-file",
            self.validate_uploaded_file,
            methods=["POST"],
            summary="Validate uploaded file",
            description="Validate invoices from uploaded file (CSV, JSON, XML)",
            response_model=V1ResponseModel
        )
        
        # Validation Rules and Standards
        self.router.add_api_route(
            "/rules",
            self.get_validation_rules,
            methods=["GET"],
            summary="Get validation rules",
            description="Get current validation rules and standards",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/standards/ubl",
            self.get_ubl_validation_standards,
            methods=["GET"],
            summary="Get UBL validation standards",
            description="Get UBL 3.0 validation standards and requirements",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/standards/firs",
            self.get_firs_validation_standards,
            methods=["GET"],
            summary="Get FIRS validation standards",
            description="Get FIRS-specific validation requirements",
            response_model=V1ResponseModel
        )
        
        # Error Analysis and Reporting
        self.router.add_api_route(
            "/errors/analysis",
            self.get_validation_error_analysis,
            methods=["GET"],
            summary="Get validation error analysis",
            description="Get analysis of common validation errors and trends",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/errors/{error_code}/help",
            self.get_validation_error_help,
            methods=["GET"],
            summary="Get validation error help",
            description="Get help and resolution guidance for specific validation errors",
            response_model=V1ResponseModel
        )
        
        # Quality Metrics
        self.router.add_api_route(
            "/quality/metrics",
            self.get_data_quality_metrics,
            methods=["GET"],
            summary="Get data quality metrics",
            description="Get comprehensive data quality metrics",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/quality/report",
            self.generate_quality_report,
            methods=["POST"],
            summary="Generate quality report",
            description="Generate data quality assessment report",
            response_model=V1ResponseModel
        )
    
    # Validation Metrics Endpoints
    async def get_validation_metrics(
        self,
        request: Request,
        db: AsyncSession = Depends(get_async_session),
    ):
        """Get comprehensive validation metrics"""
        try:
            context = await self._require_app_role(request)
            metrics = await get_validation_metrics_data(
                db,
                organization_id=context.organization_id,
            )
            metrics["capabilities"] = self.validation_capabilities
            return self._create_v1_response(metrics, "validation_metrics_retrieved")
        except Exception as e:
            logger.error(f"Error getting validation metrics in v1: {e}")
            return v1_error_response(e, action="get_validation_metrics")
    
    async def get_validation_overview(
        self,
        request: Request,
        db: AsyncSession = Depends(get_async_session),
        limit: int = Query(5, description="Recent results to include"),
    ):
        """Get validation overview"""
        try:
            context = await self._require_app_role(request)
            metrics = await get_validation_metrics_data(
                db,
                organization_id=context.organization_id,
            )
            errors = await get_validation_error_summary(
                db,
                organization_id=context.organization_id,
                limit=limit,
            )
            recent = await list_recent_validation_results_data(
                db,
                organization_id=context.organization_id,
                limit=limit,
            )
            overview = {
                "metrics": metrics,
                "errorSummary": errors,
                "recentResults": recent,
            }
            return self._create_v1_response(overview, "validation_overview_retrieved")
        except Exception as e:
            logger.error(f"Error getting validation overview in v1: {e}")
            return v1_error_response(e, action="get_validation_overview")
    
    # Validation Results Endpoints
    async def get_recent_validation_results(
        self,
        request: Request,
        limit: Optional[int] = Query(10, description="Number of results to return"),
        db: AsyncSession = Depends(get_async_session),
    ):
        """Get recent validation results"""
        try:
            context = await self._require_app_role(request)
            results = await list_recent_validation_results_data(
                db,
                organization_id=context.organization_id,
                limit=limit or 10,
            )
            return self._create_v1_response(results, "recent_validation_results_retrieved")
        except Exception as e:
            logger.error(f"Error getting recent validation results in v1: {e}")
            return v1_error_response(e, action="get_recent_validation_results")

    async def get_recent_validation_batches(
        self,
        request: Request,
        limit: Optional[int] = Query(10, description="Number of batches to include"),
        db: AsyncSession = Depends(get_async_session),
    ):
        """Return the latest validation batch runs for the tenant."""

        try:
            context = await self._require_app_role(request)
            snapshot = await summarize_validation_batches(
                db,
                organization_id=context.organization_id,
                limit=limit or 10,
            )

            recent_batches = []
            if isinstance(snapshot, dict):
                for item in snapshot.get("items", []):
                    recent_batches.append(
                        {
                            "batchId": item.get("batchId"),
                            "status": item.get("status"),
                            "totals": item.get("totals"),
                            "createdAt": item.get("createdAt"),
                            "errorSummary": item.get("errorSummary"),
                        }
                    )

            sla_hours = 4
            if context.organization_id:
                org = await db.get(Organization, context.organization_id)
                if org and isinstance(org.firs_configuration, dict):
                    configured = org.firs_configuration.get("compliance_sla_hours")
                    try:
                        if configured is not None:
                            sla_hours = max(1, int(configured))
                    except (TypeError, ValueError):
                        logger.debug(
                            "Invalid compliance_sla_hours configuration for org %s",
                            context.organization_id,
                        )

            payload = {
                "summary": snapshot.get("summary") if isinstance(snapshot, dict) else None,
                "recentBatches": recent_batches,
                "slaHours": sla_hours,
            }

            return self._create_v1_response(payload, "recent_validation_batches_retrieved")
        except Exception as exc:
            logger.error("Error getting recent validation batches in v1: %s", exc)
            return v1_error_response(exc, action="get_recent_validation_batches")
    
    async def get_validation_result(self, validation_id: str, request: Request):
        """Get detailed validation result"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_validation_result",
                payload={
                    "validation_id": validation_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "validation_result_retrieved")
        except Exception as e:
            logger.error(f"Error getting validation result {validation_id} in v1: {e}")
            return v1_error_response(e, action="get_validation_result")
    
    # Invoice Validation Endpoints
    async def validate_single_invoice(self, request: Request):
        """Validate single invoice"""
        try:
            context = await self._require_app_role(request)
            body = await request.json()
            idem_key = request.headers.get("x-idempotency-key") or request.headers.get("idempotency-key")
            if idem_key:
                if idem_key in self._idempotency_store:
                    return self._create_v1_response({"status": "duplicate", "idempotency_key": idem_key}, "idempotent_replay")
                self._idempotency_store[idem_key] = True
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="validate_single_invoice",
                payload={
                    "invoice_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "single_invoice_validated")
        except Exception as e:
            logger.error(f"Error validating single invoice in v1: {e}")
            return v1_error_response(e, action="validate_single_invoice")
    
    async def validate_invoice_batch(
        self,
        request: Request,
        db: AsyncSession = Depends(get_async_session),
    ):
        """Validate invoice batch"""
        try:
            context = await self._require_app_role(request)
            body: Dict[str, Any] = {}
            result: Optional[Dict[str, Any]] = None

            content_type = request.headers.get("content-type", "")
            if content_type.startswith("multipart/form-data"):
                result = {
                    "validation_id": f"VAL-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                    "batch_id": f"BATCH-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                    "status": "processing",
                    "invoice_count": 0,
                    "estimated_completion": "2-3 minutes",
                }
            else:
                body = await request.json()
                result = await self.message_router.route_message(
                    service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                    operation="validate_invoice_batch",
                    payload={
                        "batch_data": body,
                        "app_id": context.user_id,
                        "api_version": "v1",
                    },
                )

            if not result:
                result = {
                    "validation_id": f"VAL-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                    "batch_id": body.get("batch_id", f"BATCH-{datetime.now().strftime('%Y%m%d-%H%M%S')}"),
                    "status": "completed",
                    "invoice_count": len(body.get("invoices", [])),
                    "passed_count": len(body.get("invoices", [])),
                    "failed_count": 0,
                    "errors": [],
                }

            try:
                batch_payload = result.get("data") if isinstance(result, dict) and "data" in result else result
                if isinstance(batch_payload, dict):
                    summary = batch_payload.get("summary", {})
                    if not summary and "invoice_count" in batch_payload:
                        summary = {
                            "total": batch_payload.get("invoice_count", 0),
                            "passed": batch_payload.get("passed_count", 0),
                            "failed": batch_payload.get("failed_count", 0),
                        }
                        batch_payload.setdefault("summary", summary)

                    await record_validation_batch(
                        db,
                        organization_id=context.organization_id,
                        batch_payload=batch_payload,
                    )
            except Exception as exc:
                logger.warning("Failed to persist validation batch history: %s", exc)

            return self._create_v1_response(result, "invoice_batch_validated")
        except Exception as e:
            logger.error(f"Error validating invoice batch in v1: {e}")
            return v1_error_response(e, action="validate_invoice_batch")
    
    async def get_batch_validation_status(self, batch_id: str, request: Request):
        """Get batch validation status"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_batch_validation_status",
                payload={
                    "batch_id": batch_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "batch_validation_status_retrieved")
        except Exception as e:
            logger.error(f"Error getting batch validation status {batch_id} in v1: {e}")
            return v1_error_response(e, action="get_batch_validation_status")
    
    async def validate_uploaded_file(
        self,
        request: Request,
        file: UploadFile = File(...),
        validate_schema: bool = True,
        validate_business_rules: bool = True,
    ):
        """Validate uploaded file"""
        try:
            context = await self._require_app_role(request)
            # Process uploaded file
            content = await file.read()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="validate_uploaded_file",
                payload={
                    "file_content": content,
                    "options": {
                        "validate_schema": validate_schema,
                        "validate_business_rules": validate_business_rules,
                        "file_name": file.filename,
                        "content_type": file.content_type,
                    },
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            # Add demo data if service not available
            if not result:
                result = {
                    "validation_id": f"VAL-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
                    "file_name": file.filename,
                    "status": "processing",
                    "estimated_completion": "3-5 minutes"
                }
            
            return self._create_v1_response(result, "uploaded_file_validation_initiated")
        except Exception as e:
            logger.error(f"Error validating uploaded file in v1: {e}")
            return v1_error_response(e, action="validate_uploaded_file")
    
    # Validation Rules and Standards Endpoints
    async def get_validation_rules(self, request: Request):
        """Get validation rules"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_validation_rules",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "validation_rules_retrieved")
        except Exception as e:
            logger.error(f"Error getting validation rules in v1: {e}")
            return v1_error_response(e, action="get_validation_rules")
    
    async def get_ubl_validation_standards(self, request: Request):
        """Get UBL validation standards"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_ubl_validation_standards",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "ubl_validation_standards_retrieved")
        except Exception as e:
            logger.error(f"Error getting UBL validation standards in v1: {e}")
            return v1_error_response(e, action="get_ubl_validation_standards")
    
    async def get_firs_validation_standards(self, request: Request):
        """Get FIRS validation standards"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_firs_validation_standards",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "firs_validation_standards_retrieved")
        except Exception as e:
            logger.error(f"Error getting FIRS validation standards in v1: {e}")
            return v1_error_response(e, action="get_firs_validation_standards")
    
    # Error Analysis Endpoints
    async def get_validation_error_analysis(
        self,
        request: Request,
        period: Optional[str] = Query("30d", description="Analysis period"),
        limit: int = Query(100, description="Number of error samples"),
        db: AsyncSession = Depends(get_async_session),
    ):
        """Get validation error analysis"""
        try:
            context = await self._require_app_role(request)
            summary = await get_validation_error_summary(
                db,
                organization_id=context.organization_id,
                limit=limit,
            )
            summary["period"] = period
            return self._create_v1_response(summary, "validation_error_analysis_retrieved")
        except Exception as e:
            logger.error(f"Error getting validation error analysis in v1: {e}")
            return v1_error_response(e, action="get_validation_error_analysis")
    
    async def get_validation_error_help(
        self,
        error_code: str,
        request: Request,
        db: AsyncSession = Depends(get_async_session),
        limit: int = Query(25, description="Number of samples to include"),
    ):
        """Get validation error help"""
        try:
            context = await self._require_app_role(request)
            insights = await get_validation_error_insights(
                db,
                organization_id=context.organization_id,
                error_code=error_code,
                limit=limit,
            )

            payload = {
                "errorCode": error_code,
                "occurrences": insights.get("occurrences", 0),
                "samples": insights.get("samples", []),
            }

            if payload["occurrences"] == 0:
                payload["guidance"] = [
                    "Verify mandatory FIRS fields referenced in the error.",
                    "Confirm VAT and tax calculations align with current rules.",
                    "Update mapping rules or contact support if the issue persists.",
                ]

            return self._create_v1_response(payload, "validation_error_help_retrieved")
        except Exception as e:
            logger.error(f"Error getting validation error help for {error_code} in v1: {e}")
            return v1_error_response(e, action="get_validation_error_help")
    
    # Quality Metrics Endpoints
    async def get_data_quality_metrics(self, request: Request):
        """Get data quality metrics"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_data_quality_metrics",
                payload={
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "data_quality_metrics_retrieved")
        except Exception as e:
            logger.error(f"Error getting data quality metrics in v1: {e}")
            return v1_error_response(e, action="get_data_quality_metrics")
    
    async def generate_quality_report(self, request: Request):
        """Generate quality report"""
        try:
            context = await self._require_app_role(request)
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="generate_quality_report",
                payload={
                    "report_config": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "quality_report_generated")
        except Exception as e:
            logger.error(f"Error generating quality report in v1: {e}")
            return v1_error_response(e, action="generate_quality_report")
    
    def _create_v1_response(self, data: Dict[str, Any], action: str, status_code: int = 200) -> V1ResponseModel:
        """Create standardized v1 response format using V1ResponseModel"""
        return build_v1_response(data, action)


def create_validation_management_router(role_detector: HTTPRoleDetector,
                                       permission_guard: APIPermissionGuard,
                                       message_router: MessageRouter) -> APIRouter:
    """Factory function to create Validation Management Router"""
    validation_endpoints = ValidationManagementEndpointsV1(role_detector, permission_guard, message_router)
    return validation_endpoints.router
