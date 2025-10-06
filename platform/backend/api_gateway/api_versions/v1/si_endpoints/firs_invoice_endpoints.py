"""
FIRS Invoice Generation API Endpoints for SI Role
=================================================
Comprehensive API endpoints for generating FIRS-compliant invoices
from aggregated business and financial system data.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Depends, status, Request
from pydantic import BaseModel, validator
from sqlalchemy.ext.asyncio import AsyncSession

# Use async DB session dependency for SI endpoints
from core_platform.data_management.db_async import get_async_session
from api_gateway.role_routing.models import HTTPRoutingContext
from api_gateway.role_routing.role_detector import HTTPRoleDetector
from api_gateway.role_routing.permission_guard import APIPermissionGuard
from core_platform.authentication.role_manager import PlatformRole
from api_gateway.api_versions.v1.si_endpoints.version_models import V1ResponseModel
from api_gateway.utils.v1_response import build_v1_response
from si_services.firs_integration.comprehensive_invoice_generator import (
    ComprehensiveFIRSInvoiceGenerator,
    FIRSInvoiceGenerationRequest,
    DataSourceType
)
from external_integrations.financial_systems.banking.open_banking.invoice_automation.firs_formatter import FIRSFormatter
from sqlalchemy import select
from core_platform.data_management.models.organization import Organization

logger = logging.getLogger(__name__)


# Request/Response Models
class TransactionFilterRequest(BaseModel):
    """Request model for filtering business transactions."""
    source_types: Optional[List[str]] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    firs_status: Optional[str] = None
    min_amount: Optional[float] = None
    max_amount: Optional[float] = None
    payment_status: Optional[str] = None


class BusinessTransactionResponse(BaseModel):
    """Response model for business transaction data."""
    id: str
    source_type: str
    source_name: str
    transaction_id: str
    date: datetime
    customer_name: str
    customer_email: Optional[str]
    amount: float
    currency: str
    description: str
    tax_amount: float
    payment_status: str
    payment_method: Optional[str]
    firs_status: str
    confidence: float
    irn: Optional[str] = None


class FIRSInvoiceGenerationRequestAPI(BaseModel):
    """API request model for FIRS invoice generation."""
    transaction_ids: List[str]
    invoice_type: str = "standard"
    consolidate: bool = False
    include_digital_signature: bool = True
    customer_overrides: Optional[Dict[str, str]] = None

    @validator('invoice_type')
    def validate_invoice_type(cls, v):
        valid_types = ['standard', 'credit_note', 'debit_note']
        if v not in valid_types:
            raise ValueError(f'Invoice type must be one of: {valid_types}')
        return v


class FIRSInvoiceResponse(BaseModel):
    """Response model for generated FIRS invoice."""
    irn: str
    invoice_number: str
    customer_name: str
    total_amount: float
    tax_amount: float
    currency: str
    invoice_date: str
    status: str
    source_count: int
    signature: Optional[Dict[str, Any]] = None
    validation_status: Optional[str] = None
    warnings: Optional[List[str]] = None


class FIRSInvoiceGenerationResponse(BaseModel):
    """Response model for FIRS invoice generation."""
    success: bool
    invoices: List[FIRSInvoiceResponse]
    total_amount: float
    errors: List[str]
    warnings: List[str]
    generation_stats: Dict[str, Any]


class ConnectedSourceResponse(BaseModel):
    """Response model for connected data sources."""
    id: str
    type: str
    name: str
    status: str
    last_sync: str
    record_count: int


def create_firs_invoice_router(
    role_detector: HTTPRoleDetector,
    permission_guard: APIPermissionGuard,
) -> APIRouter:
    """Create and configure the FIRS invoice generation router."""
    router = APIRouter(
        prefix="/firs/invoices",
        tags=["FIRS Invoice Generation"],
    )

    async def _require_si_role(role_detector: HTTPRoleDetector, permission_guard: APIPermissionGuard, request: Request) -> HTTPRoutingContext:
        context = await role_detector.detect_role_context(request)
        if not context or not context.has_role(PlatformRole.SYSTEM_INTEGRATOR):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="System Integrator role required for v1 API")
        if not await permission_guard.check_endpoint_permission(
            context, f"v1/si{request.url.path}", request.method
        ):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions for SI v1 endpoint")
        context.metadata["api_version"] = "v1"
        context.metadata["endpoint_group"] = "si"
        return context

    # Closure dependency so FastAPI treats Request properly (no query param named 'request')
    async def require_si_role(request: Request) -> HTTPRoutingContext:
        return await _require_si_role(role_detector, permission_guard, request)


    @router.get(
        "/sources",
        response_model=V1ResponseModel,
        summary="Get connected data sources",
        description="Retrieve all connected business and financial systems available for invoice generation"
    )
    async def get_connected_sources(
        context: HTTPRoutingContext = Depends(require_si_role),
        db: AsyncSession = Depends(get_async_session)
    ):
        """Get all connected data sources for the organization."""
        try:
            # Verify SI role
            # Role already enforced by dependency

            # Mock connected sources (in real implementation, query from database)
            sources = [
                {
                    "id": "sap-erp",
                    "type": "erp",
                    "name": "SAP ERP",
                    "status": "connected",
                    "last_sync": "5 minutes ago",
                    "record_count": 1456
                },
                {
                    "id": "odoo-erp",
                    "type": "erp",
                    "name": "Odoo ERP",
                    "status": "connected",
                    "last_sync": "12 minutes ago",
                    "record_count": 758
                },
                {
                    "id": "salesforce-crm",
                    "type": "crm",
                    "name": "Salesforce CRM",
                    "status": "connected",
                    "last_sync": "8 minutes ago",
                    "record_count": 234
                },
                {
                    "id": "square-pos",
                    "type": "pos",
                    "name": "Square POS",
                    "status": "connected",
                    "last_sync": "3 minutes ago",
                    "record_count": 89
                },
                {
                    "id": "shopify-pos",
                    "type": "pos",
                    "name": "Shopify POS",
                    "status": "connected",
                    "last_sync": "7 minutes ago",
                    "record_count": 56
                },
                {
                    "id": "shopify-store",
                    "type": "ecommerce",
                    "name": "Shopify Store",
                    "status": "connected",
                    "last_sync": "4 minutes ago",
                    "record_count": 342
                },
                {
                    "id": "mono-banking",
                    "type": "banking",
                    "name": "Mono Banking",
                    "status": "connected",
                    "last_sync": "2 minutes ago",
                    "record_count": 2456
                },
                {
                    "id": "paystack",
                    "type": "payment",
                    "name": "Paystack",
                    "status": "connected",
                    "last_sync": "1 minute ago",
                    "record_count": 1234
                },
                {
                    "id": "flutterwave",
                    "type": "payment",
                    "name": "Flutterwave",
                    "status": "connected",
                    "last_sync": "6 minutes ago",
                    "record_count": 567
                }
            ]

            return build_v1_response(
                data={"sources": sources},
                action="get_connected_sources"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get connected sources: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve connected sources"
            )

    @router.post(
        "/transactions/search",
        response_model=V1ResponseModel,
        summary="Search business transactions",
        description="Search and filter business transactions from all connected systems"
    )
    async def search_business_transactions(
        filters: TransactionFilterRequest,
        context: HTTPRoutingContext = Depends(require_si_role),
        db: AsyncSession = Depends(get_async_session)
    ):
        """Search business transactions across all connected systems."""
        try:
            # Verify SI role
            # Role already enforced by dependency

            # Initialize FIRS generator
            firs_formatter = FIRSFormatter(supplier_info={"name": "TaxPoynt User"})
            generator = ComprehensiveFIRSInvoiceGenerator(db, firs_formatter)

            # Set date range
            date_range = None
            if filters.date_from and filters.date_to:
                date_range = (filters.date_from, filters.date_to)

            # Get aggregated transaction data
            transactions = await generator.aggregate_business_data(
                organization_id=context.organization_id,
                date_range=date_range
            )

            # Apply filters
            filtered_transactions = []
            for txn in transactions:
                # Source type filter
                if filters.source_types and txn.source_type.value not in filters.source_types:
                    continue
                
                # Amount filter
                if filters.min_amount and float(txn.amount) < filters.min_amount:
                    continue
                if filters.max_amount and float(txn.amount) > filters.max_amount:
                    continue
                
                # Payment status filter
                if filters.payment_status and txn.payment_status != filters.payment_status:
                    continue

                # Convert to response format
                transaction_response = BusinessTransactionResponse(
                    id=txn.id,
                    source_type=txn.source_type.value,
                    source_name=txn.source_id.replace('_', ' ').title(),
                    transaction_id=txn.transaction_id,
                    date=txn.date,
                    customer_name=txn.customer_name,
                    customer_email=txn.customer_email,
                    amount=float(txn.amount),
                    currency=txn.currency,
                    description=txn.description,
                    tax_amount=float(txn.tax_amount),
                    payment_status=txn.payment_status,
                    payment_method=txn.payment_method,
                    firs_status="not_generated",  # Default status
                    confidence=txn.confidence,
                    irn=None
                )
                filtered_transactions.append(transaction_response)

            return build_v1_response(
                data={
                    "transactions": [txn.dict() for txn in filtered_transactions],
                    "total_count": len(filtered_transactions),
                    "filters_applied": filters.dict()
                },
                action="search_business_transactions"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to search transactions: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to search business transactions"
            )

    @router.post(
        "/generate",
        response_model=V1ResponseModel,
        summary="Generate FIRS-compliant invoices",
        description="Generate FIRS-compliant invoices from selected business transactions"
    )
    async def generate_firs_invoices(
        request: FIRSInvoiceGenerationRequestAPI,
        context: HTTPRoutingContext = Depends(require_si_role),
        db: AsyncSession = Depends(get_async_session)
    ):
        """Generate FIRS-compliant invoices from business transaction data."""
        try:
            # Verify SI role
            # Role already enforced by dependency

            if not request.transaction_ids:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="At least one transaction ID is required"
                )

            # Initialize FIRS generator
            # Load organization details for supplier info
            if not context.organization_id:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization context required")

            try:
                org_uuid = UUID(str(context.organization_id))
            except Exception:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid organization ID in context")

            org_name = "TaxPoynt Organization"
            org_email = ""
            org_tin = ""
            org_phone = ""
            org_address = ""
            org_reg = ""

            org_result = await db.execute(select(Organization).where(Organization.id == org_uuid))
            organization = org_result.scalar_one_or_none()
            if organization:
                org_name = organization.display_name or organization.name or org_name
                org_email = organization.email or ""
                org_tin = organization.tin or ""
                org_phone = organization.phone or ""
                org_address = organization.address or ""
                org_reg = organization.rc_number or ""

            firs_formatter = FIRSFormatter(
                supplier_info={
                    "name": org_name,
                    "address": org_address,
                    "tin": org_tin,
                    "phone": org_phone,
                    "email": org_email,
                    "business_registration": org_reg,
                }
            )
            generator = ComprehensiveFIRSInvoiceGenerator(db, firs_formatter)

            # Create generation request
            generation_request = FIRSInvoiceGenerationRequest(
                organization_id=org_uuid,
                transaction_ids=request.transaction_ids,
                invoice_type=request.invoice_type,
                consolidate=request.consolidate,
                include_digital_signature=request.include_digital_signature,
                customer_overrides=request.customer_overrides
            )

            # Generate invoices
            result = await generator.generate_firs_invoices(generation_request)

            if not result.success:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invoice generation failed: {'; '.join(result.errors)}"
                )

            # Convert to response format
            invoice_responses = []
            for invoice in result.invoices:
                invoice_response = FIRSInvoiceResponse(
                    irn=invoice['irn'],
                    invoice_number=invoice['invoice_number'],
                    customer_name=invoice['customer']['name'],
                    total_amount=invoice['total_amount'],
                    tax_amount=invoice['tax_amount'],
                    currency=invoice['currency'],
                    invoice_date=invoice['invoice_date'],
                    status="generated",
                    source_count=invoice.get('source_data', {}).get('transaction_count', 1),
                    signature=invoice.get('signature'),
                    validation_status=invoice.get('validation_status'),
                    warnings=invoice.get('warnings') or None,
                )
                invoice_responses.append(invoice_response)

            # Get generation statistics
            stats = await generator.get_generation_statistics()

            response_data = FIRSInvoiceGenerationResponse(
                success=True,
                invoices=invoice_responses,
                total_amount=float(result.total_amount),
                errors=result.errors,
                warnings=result.warnings,
                generation_stats=stats
            )

            wrapped = {
                "success": True,
                "data": response_data.dict()
            }

            return build_v1_response(wrapped, "generate_firs_invoices")

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to generate FIRS invoices: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to generate FIRS invoices"
            )

    @router.get(
        "/sample-data",
        response_model=V1ResponseModel,
        summary="Get sample invoice data",
        description="Get sample invoice data for testing FIRS generation"
    )
    async def get_sample_invoice_data(
        context: HTTPRoutingContext = Depends(require_si_role),
        db: AsyncSession = Depends(get_async_session)
    ):
        """Get sample invoice data for testing FIRS generation."""
        try:
            # Verify SI role
            # Role already enforced by dependency

            # Sample data representing different business systems
            sample_transactions = [
                {
                    "id": "sample-erp-001",
                    "source_type": "erp",
                    "source_name": "SAP ERP",
                    "transaction_id": "SAP-INV-2024-1456",
                    "date": "2024-01-15T10:30:00Z",
                    "customer_name": "Acme Corporation Ltd",
                    "customer_email": "finance@acmecorp.ng",
                    "amount": 2500000.0,
                    "currency": "NGN",
                    "description": "Software License and Support Services",
                    "line_items": [
                        {
                            "description": "Software License (Annual)",
                            "quantity": 1,
                            "unit_price": 2000000.0,
                            "total": 2000000.0,
                            "tax_rate": 7.5,
                            "tax_amount": 150000.0
                        },
                        {
                            "description": "Support Services",
                            "quantity": 1,
                            "unit_price": 350000.0,
                            "total": 350000.0,
                            "tax_rate": 7.5,
                            "tax_amount": 26250.0
                        }
                    ],
                    "tax_amount": 176250.0,
                    "payment_status": "paid",
                    "payment_method": "Bank Transfer",
                    "confidence": 98.7
                },
                {
                    "id": "sample-crm-001",
                    "source_type": "crm",
                    "source_name": "Salesforce CRM",
                    "transaction_id": "SF-DEAL-789",
                    "date": "2024-01-15T14:45:00Z",
                    "customer_name": "Lagos Business Solutions",
                    "customer_email": "procurement@lbs.ng",
                    "amount": 1800000.0,
                    "currency": "NGN",
                    "description": "Business Consulting Services",
                    "line_items": [
                        {
                            "description": "Strategy Consulting",
                            "quantity": 40,
                            "unit_price": 35000.0,
                            "total": 1400000.0,
                            "tax_rate": 7.5,
                            "tax_amount": 105000.0
                        },
                        {
                            "description": "Implementation Support",
                            "quantity": 8,
                            "unit_price": 50000.0,
                            "total": 400000.0,
                            "tax_rate": 7.5,
                            "tax_amount": 30000.0
                        }
                    ],
                    "tax_amount": 135000.0,
                    "payment_status": "paid",
                    "payment_method": "Paystack",
                    "confidence": 96.8
                },
                {
                    "id": "sample-pos-001",
                    "source_type": "pos",
                    "source_name": "Square POS",
                    "transaction_id": "SQ-SALE-456",
                    "date": "2024-01-15T16:20:00Z",
                    "customer_name": "Walk-in Customer",
                    "amount": 125000.0,
                    "currency": "NGN",
                    "description": "Retail Sale - Electronics",
                    "line_items": [
                        {
                            "description": "Wireless Headphones",
                            "quantity": 2,
                            "unit_price": 45000.0,
                            "total": 90000.0,
                            "tax_rate": 7.5,
                            "tax_amount": 6750.0
                        },
                        {
                            "description": "Phone Case",
                            "quantity": 1,
                            "unit_price": 35000.0,
                            "total": 35000.0,
                            "tax_rate": 7.5,
                            "tax_amount": 2625.0
                        }
                    ],
                    "tax_amount": 9375.0,
                    "payment_status": "paid",
                    "payment_method": "Card Payment",
                    "confidence": 99.2
                },
                {
                    "id": "sample-ecommerce-001",
                    "source_type": "ecommerce",
                    "source_name": "Shopify Store",
                    "transaction_id": "SHOP-ORD-123",
                    "date": "2024-01-15T11:15:00Z",
                    "customer_name": "Online Customer",
                    "customer_email": "customer@email.com",
                    "amount": 89500.0,
                    "currency": "NGN",
                    "description": "E-commerce Order",
                    "line_items": [
                        {
                            "description": "Product Bundle",
                            "quantity": 1,
                            "unit_price": 75000.0,
                            "total": 75000.0,
                            "tax_rate": 7.5,
                            "tax_amount": 5625.0
                        },
                        {
                            "description": "Shipping Fee",
                            "quantity": 1,
                            "unit_price": 14500.0,
                            "total": 14500.0,
                            "tax_rate": 7.5,
                            "tax_amount": 1087.5
                        }
                    ],
                    "tax_amount": 6712.5,
                    "payment_status": "paid",
                    "payment_method": "Flutterwave",
                    "confidence": 94.5
                },
                {
                    "id": "sample-banking-001",
                    "source_type": "banking",
                    "source_name": "Mono Banking",
                    "transaction_id": "MONO-TXN-890",
                    "date": "2024-01-15T09:30:00Z",
                    "customer_name": "Direct Bank Transfer Customer",
                    "amount": 450000.0,
                    "currency": "NGN",
                    "description": "Service Payment via Bank Transfer",
                    "line_items": [
                        {
                            "description": "Professional Services",
                            "quantity": 1,
                            "unit_price": 419000.0,
                            "total": 419000.0,
                            "tax_rate": 7.5,
                            "tax_amount": 31425.0
                        }
                    ],
                    "tax_amount": 31425.0,
                    "payment_status": "paid",
                    "payment_method": "Bank Transfer",
                    "confidence": 87.3
                }
            ]

            return build_v1_response(
                data={
                    "sample_transactions": sample_transactions,
                    "total_count": len(sample_transactions),
                    "total_amount": sum(txn["amount"] for txn in sample_transactions),
                    "note": "This is sample data for testing FIRS invoice generation"
                },
                action="get_sample_invoice_data"
            )

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to get sample data: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve sample invoice data"
            )

    return router
