"""
Compliance Validation Endpoints - API v1
========================================
Access Point Provider endpoints for validating compliance with FIRS and regulatory standards.
Handles UBL, PEPPOL, ISO standards validation and regulatory compliance checking.
"""
import logging
from typing import Dict, Any, List, Optional

from fastapi import APIRouter, Request, HTTPException, Depends, status, Query, Path
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from core_platform.authentication.role_manager import PlatformRole
from core_platform.messaging.message_router import ServiceRole, MessageRouter
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from ..version_models import V1ResponseModel
from api_gateway.utils.v1_response import build_v1_response
from api_gateway.utils.error_mapping import v1_error_response
from .firs_request_models import (
    UBLComplianceRequest,
    UBLBatchComplianceRequest,
    GenericValidationPayload,
)

logger = logging.getLogger(__name__)


class ComplianceValidationEndpointsV1:
    """
    Compliance Validation Endpoints - Version 1
    ===========================================
    Manages compliance validation for FIRS and regulatory standards:
    
    **Compliance Standards Validation:**
    - **UBL (Universal Business Language)**: Invoice format standardization and validation
    - **PEPPOL Standards**: Invoice safety compliance for international transactions
    - **ISO 20022**: Financial messaging standards validation
    - **ISO 27001**: Information security management compliance
    - **GDPR & NDPA**: Data protection compliance validation
    - **WCO Harmonized System**: Product classification validation
    - **Legal Entity Identifier (LEI)**: Entity identification validation
    """
    
    def __init__(self, 
                 role_detector: HTTPRoleDetector,
                 permission_guard: APIPermissionGuard,
                 message_router: MessageRouter):
        self.role_detector = role_detector
        self.permission_guard = permission_guard
        self.message_router = message_router
        self.router = APIRouter(
            prefix="/compliance",
            tags=["Compliance Validation V1"],
            dependencies=[Depends(self._require_app_role)]
        )
        
        # Define compliance standards
        self.compliance_standards = {
            "ubl": {
                "name": "Universal Business Language",
                "description": "Invoice format standardization and validation",
                "features": ["format_validation", "schema_compliance", "business_rules"]
            },
            "peppol": {
                "name": "PEPPOL Standards",
                "description": "Invoice safety compliance for international transactions",
                "features": ["safety_validation", "international_compliance", "interoperability"]
            },
            "iso20022": {
                "name": "ISO 20022",
                "description": "Financial messaging standards validation",
                "features": ["message_validation", "financial_standards", "data_integrity"]
            },
            "iso27001": {
                "name": "ISO 27001",
                "description": "Information security management compliance",
                "features": ["security_validation", "risk_assessment", "control_verification"]
            },
            "gdpr_ndpa": {
                "name": "GDPR & NDPA",
                "description": "Data protection compliance validation",
                "features": ["privacy_validation", "consent_management", "data_protection"]
            },
            "wco_hs": {
                "name": "WCO Harmonized System",
                "description": "Product classification validation",
                "features": ["classification_validation", "hs_code_verification", "product_compliance"]
            },
            "lei": {
                "name": "Legal Entity Identifier",
                "description": "Entity identification validation",
                "features": ["entity_validation", "lei_verification", "identity_compliance"]
            }
        }
        
        self._setup_routes()
        logger.info("Compliance Validation Endpoints V1 initialized")
    
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
        """Setup compliance validation routes"""
        
        # Compliance Standards Information
        self.router.add_api_route(
            "/standards",
            self.get_compliance_standards,
            methods=["GET"],
            summary="Get supported compliance standards",
            description="Get all supported compliance standards and their features",
            response_model=V1ResponseModel
        )
        
        # UBL Validation Routes
        self.router.add_api_route(
            "/ubl/validate",
            self.validate_ubl_compliance,
            methods=["POST"],
            summary="Validate UBL compliance",
            description="Validate Universal Business Language compliance",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/ubl/validate-batch",
            self.validate_ubl_batch,
            methods=["POST"],
            summary="Validate UBL batch compliance",
            description="Validate multiple documents for UBL compliance",
            response_model=V1ResponseModel
        )
        
        # PEPPOL Validation Routes
        self.router.add_api_route(
            "/peppol/validate",
            self.validate_peppol_compliance,
            methods=["POST"],
            summary="Validate PEPPOL compliance",
            description="Validate PEPPOL standards compliance",
            response_model=V1ResponseModel
        )
        
        # ISO Standards Validation Routes
        self.router.add_api_route(
            "/iso20022/validate",
            self.validate_iso20022_compliance,
            methods=["POST"],
            summary="Validate ISO 20022 compliance",
            description="Validate financial messaging standards compliance",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/iso27001/validate",
            self.validate_iso27001_compliance,
            methods=["POST"],
            summary="Validate ISO 27001 compliance",
            description="Validate information security management compliance",
            response_model=V1ResponseModel
        )
        
        # Data Protection Validation Routes
        self.router.add_api_route(
            "/gdpr-ndpa/validate",
            self.validate_data_protection_compliance,
            methods=["POST"],
            summary="Validate GDPR/NDPA compliance",
            description="Validate data protection compliance",
            response_model=V1ResponseModel
        )
        
        # Product Classification Validation Routes
        self.router.add_api_route(
            "/wco-hs/validate",
            self.validate_product_classification,
            methods=["POST"],
            summary="Validate product classification",
            description="Validate WCO Harmonized System product classification",
            response_model=V1ResponseModel
        )
        
        # Entity Validation Routes
        self.router.add_api_route(
            "/lei/validate",
            self.validate_lei_compliance,
            methods=["POST"],
            summary="Validate LEI compliance",
            description="Validate Legal Entity Identifier compliance",
            response_model=V1ResponseModel
        )
        
        # Comprehensive Compliance Validation
        self.router.add_api_route(
            "/validate-comprehensive",
            self.validate_comprehensive_compliance,
            methods=["POST"],
            summary="Comprehensive compliance validation",
            description="Validate against all applicable compliance standards",
            response_model=V1ResponseModel
        )
        
        # Compliance Reports
        self.router.add_api_route(
            "/reports/generate",
            self.generate_compliance_report,
            methods=["POST"],
            summary="Generate compliance report",
            description="Generate detailed compliance validation report",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/reports/list",
            self.list_compliance_reports,
            methods=["GET"],
            summary="List compliance reports",
            description="List all generated compliance reports",
            response_model=V1ResponseModel
        )
        
        self.router.add_api_route(
            "/reports/{report_id}",
            self.get_compliance_report,
            methods=["GET"],
            summary="Get compliance report",
            description="Get specific compliance validation report",
            response_model=V1ResponseModel
        )
    
    # Compliance Standards Information
    async def get_compliance_standards(self, request: Request):
        """Get supported compliance standards"""
        try:
            await self._require_app_role(request)
            result = {
                "compliance_standards": self.compliance_standards,
                "total_standards": len(self.compliance_standards),
                "categories": ["format_standards", "security_standards", "data_protection", "classification", "entity_validation"]
            }
            
            return self._create_v1_response(result, "compliance_standards_retrieved")
        except Exception as e:
            logger.error(f"Error getting compliance standards in v1: {e}")
            return v1_error_response(e, action="get_compliance_standards")
    
    # UBL Validation Endpoints
    async def validate_ubl_compliance(self, request: Request):
        """Validate UBL compliance"""
        try:
            context = await self._require_app_role(request)
            raw_body = await request.json()
            try:
                payload = UBLComplianceRequest.parse_obj(raw_body)
            except ValidationError as exc:
                return v1_error_response(ValueError(str(exc)), action="validate_ubl_compliance")

            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="validate_ubl_compliance",
                payload={
                    "validation_data": payload.dict(exclude_none=True),
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "ubl_compliance_validated")
        except Exception as e:
            logger.error(f"Error validating UBL compliance in v1: {e}")
            return v1_error_response(e, action="validate_ubl_compliance")
    
    async def validate_ubl_batch(self, request: Request):
        """Validate UBL batch compliance"""
        try:
            context = await self._require_app_role(request)
            raw_body = await request.json()
            try:
                payload = UBLBatchComplianceRequest.parse_obj(raw_body)
            except ValidationError as exc:
                return v1_error_response(ValueError(str(exc)), action="validate_ubl_batch_compliance")

            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="validate_ubl_batch",
                payload={
                    "batch_validation_data": payload.dict(exclude_none=True),
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "ubl_batch_compliance_validated")
        except Exception as e:
            logger.error(f"Error validating UBL batch compliance in v1: {e}")
            return v1_error_response(e, action="validate_ubl_batch_compliance")
    
    # PEPPOL Validation Endpoints
    async def validate_peppol_compliance(self, request: Request):
        """Validate PEPPOL compliance"""
        try:
            context = await self._require_app_role(request)
            raw_body = await request.json()
            try:
                payload = GenericValidationPayload.parse_obj(raw_body)
            except ValidationError as exc:
                return v1_error_response(ValueError(str(exc)), action="validate_peppol_compliance")

            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="validate_peppol_compliance",
                payload={
                    "validation_data": payload.dict(exclude_none=True),
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "peppol_compliance_validated")
        except Exception as e:
            logger.error(f"Error validating PEPPOL compliance in v1: {e}")
            return v1_error_response(e, action="validate_peppol_compliance")
    
    # ISO Standards Validation Endpoints
    async def validate_iso20022_compliance(self, request: Request):
        """Validate ISO 20022 compliance"""
        try:
            context = await self._require_app_role(request)
            raw_body = await request.json()
            try:
                payload = GenericValidationPayload.parse_obj(raw_body)
            except ValidationError as exc:
                return v1_error_response(ValueError(str(exc)), action="validate_iso20022_compliance")

            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="validate_iso20022_compliance",
                payload={
                    "validation_data": payload.dict(exclude_none=True),
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "iso20022_compliance_validated")
        except Exception as e:
            logger.error(f"Error validating ISO 20022 compliance in v1: {e}")
            return v1_error_response(e, action="validate_iso20022_compliance")
    
    async def validate_iso27001_compliance(self, request: Request):
        """Validate ISO 27001 compliance"""
        try:
            context = await self._require_app_role(request)
            raw_body = await request.json()
            try:
                payload = GenericValidationPayload.parse_obj(raw_body)
            except ValidationError as exc:
                return v1_error_response(ValueError(str(exc)), action="validate_iso27001_compliance")

            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="validate_iso27001_compliance",
                payload={
                    "validation_data": payload.dict(exclude_none=True),
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "iso27001_compliance_validated")
        except Exception as e:
            logger.error(f"Error validating ISO 27001 compliance in v1: {e}")
            return v1_error_response(e, action="validate_iso27001_compliance")
    
    # Data Protection Validation Endpoints
    async def validate_data_protection_compliance(self, request: Request):
        """Validate GDPR/NDPA compliance"""
        try:
            context = await self._require_app_role(request)
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="validate_data_protection_compliance",
                payload={
                    "validation_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "data_protection_compliance_validated")
        except Exception as e:
            logger.error(f"Error validating data protection compliance in v1: {e}")
            return v1_error_response(e, action="validate_data_protection_compliance")
    
    # Product Classification Validation Endpoints
    async def validate_product_classification(self, request: Request):
        """Validate product classification"""
        try:
            context = await self._require_app_role(request)
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="validate_product_classification",
                payload={
                    "validation_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "product_classification_validated")
        except Exception as e:
            logger.error(f"Error validating product classification in v1: {e}")
            return v1_error_response(e, action="validate_product_classification")
    
    # Entity Validation Endpoints
    async def validate_lei_compliance(self, request: Request):
        """Validate LEI compliance"""
        try:
            context = await self._require_app_role(request)
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="validate_lei_compliance",
                payload={
                    "validation_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "lei_compliance_validated")
        except Exception as e:
            logger.error(f"Error validating LEI compliance in v1: {e}")
            return v1_error_response(e, action="validate_lei_compliance")
    
    # Comprehensive Compliance Validation
    async def validate_comprehensive_compliance(self, request: Request):
        """Comprehensive compliance validation"""
        try:
            context = await self._require_app_role(request)
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="validate_comprehensive_compliance",
                payload={
                    "validation_data": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "comprehensive_compliance_validated")
        except Exception as e:
            logger.error(f"Error validating comprehensive compliance in v1: {e}")
            return v1_error_response(e, action="validate_comprehensive_compliance")
    
    # Compliance Report Endpoints
    async def generate_compliance_report(self, request: Request):
        """Generate compliance report"""
        try:
            context = await self._require_app_role(request)
            body = await request.json()
            
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="generate_compliance_report",
                payload={
                    "report_config": body,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "compliance_report_generated")
        except Exception as e:
            logger.error(f"Error generating compliance report in v1: {e}")
            return v1_error_response(e, action="generate_compliance_report")
    
    async def list_compliance_reports(self, 
                                    request: Request,
                                    standard: Optional[str] = Query(None, description="Filter by compliance standard"),
                                    status: Optional[str] = Query(None, description="Filter by report status")):
        """List compliance reports"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="list_compliance_reports",
                payload={
                    "app_id": context.user_id,
                    "filters": {
                        "standard": standard,
                        "status": status
                    },
                    "api_version": "v1"
                }
            )
            
            return self._create_v1_response(result, "compliance_reports_listed")
        except Exception as e:
            logger.error(f"Error listing compliance reports in v1: {e}")
            return v1_error_response(e, action="list_compliance_reports")
    
    async def get_compliance_report(self, report_id: str, request: Request):
        """Get compliance report"""
        try:
            context = await self._require_app_role(request)
            result = await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation="get_compliance_report",
                payload={
                    "report_id": report_id,
                    "app_id": context.user_id,
                    "api_version": "v1"
                }
            )
            
            if not result:
                raise HTTPException(status_code=404, detail="Compliance report not found")
            
            return self._create_v1_response(result, "compliance_report_retrieved")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error getting compliance report {report_id} in v1: {e}")
            return v1_error_response(e, action="get_compliance_report")
    
    def _create_v1_response(self, data: Dict[str, Any], action: str, status_code: int = 200) -> V1ResponseModel:
        """Create standardized v1 response format using V1ResponseModel"""
        return build_v1_response(data, action)


def create_compliance_validation_router(role_detector: HTTPRoleDetector,
                                       permission_guard: APIPermissionGuard,
                                       message_router: MessageRouter) -> APIRouter:
    """Factory function to create Compliance Validation Router"""
    compliance_endpoints = ComplianceValidationEndpointsV1(role_detector, permission_guard, message_router)
    return compliance_endpoints.router
