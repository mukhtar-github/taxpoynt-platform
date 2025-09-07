from fastapi import APIRouter, Depends, HTTPException, Query, Path # type: ignore
from sqlalchemy.orm import Session # type: ignore
from datetime import datetime
from typing import List, Optional # type: ignore
import logging # type: ignore
from uuid import UUID

from app.api.deps import get_db, get_current_active_user # type: ignore
from app.models.user import User
from app.schemas.irn import (
    IRNGenerateRequest,
    IRNBatchGenerateRequest,
    IRNResponse,
    IRNBatchResponse,
    IRNStatusUpdate,
    IRNMetricsResponse,
    OdooIRNGenerateRequest,
    IRNValidationResponse
)
from app.crud import irn as crud_irn
from app.crud import integration as crud_integration
from app.crud import organization as crud_organization
from app.services import odoo_service

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/generate", response_model=IRNResponse, status_code=201)
def generate_irn(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    request: IRNGenerateRequest
):
    """
    Generate a single IRN for an invoice.
    
    Follows FIRS format: InvoiceNumber-ServiceID-YYYYMMDD
    
    Returns:
        IRNResponse: The generated IRN with metadata
    """
    # Get the integration
    integration = crud_integration.get_integration_by_id(db, request.integration_id)
    if not integration:
        raise HTTPException(
            status_code=404,
            detail="Integration not found"
        )
    
    # Verify user has access to this integration
    if integration.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this integration"
        )
    
    # Get organization for service ID
    organization = crud_organization.get_organization_by_id(db, current_user.organization_id)
    if not organization or not organization.firs_service_id:
        logger.warning(f"Organization {current_user.organization_id} missing FIRS service ID")
        # For POC, use a placeholder service ID if not set
        service_id = "94ND90NR"
    else:
        service_id = organization.firs_service_id
    
    try:
        # Create IRN record
        irn_record = crud_irn.create_irn(db, request, service_id)
        return irn_record
    except HTTPException as e:
        # Pass through HTTPExceptions
        raise e
    except Exception as e:
        logger.error(f"Error generating IRN: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate IRN: {str(e)}"
        )


@router.post("/generate-batch", response_model=IRNBatchResponse, status_code=201)
def generate_batch_irn(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    request: IRNBatchGenerateRequest
):
    """
    Generate multiple IRNs in a batch.
    
    Handles up to 100 invoice numbers in a single request and processes them
    in a batch operation. Failed invoice numbers will be reported with error details.
    
    Returns:
        IRNBatchResponse: The generated IRNs with counts and any failures
    """
    # Get the integration
    integration = crud_integration.get_integration_by_id(db, request.integration_id)
    if not integration:
        raise HTTPException(
            status_code=404,
            detail="Integration not found"
        )
    
    # Verify user has access to this integration
    if integration.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this integration"
        )
    
    # Get organization for service ID
    organization = crud_organization.get_organization_by_id(db, current_user.organization_id)
    if not organization or not organization.firs_service_id:
        logger.warning(f"Organization {current_user.organization_id} missing FIRS service ID")
        # For POC, use a placeholder service ID if not set
        service_id = "94ND90NR"
    else:
        service_id = organization.firs_service_id
    
    try:
        # Generate IRNs for each invoice number
        successful_records, failed_invoices = crud_irn.create_batch_irn(
            db, 
            request.integration_id, 
            request.invoice_numbers, 
            service_id, 
            request.timestamp
        )
        
        return {
            "irns": successful_records,
            "count": len(successful_records),
            "failed_count": len(failed_invoices),
            "failed_invoices": failed_invoices if failed_invoices else None
        }
    except HTTPException as e:
        # Pass through HTTPExceptions
        raise e
    except Exception as e:
        logger.error(f"Error generating batch IRNs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate batch IRNs: {str(e)}"
        )


@router.get("/{irn}", response_model=IRNResponse)
def get_irn_details(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    irn: str = Path(..., description="IRN to retrieve")
):
    """
    Get IRN details and validate its format.
    
    Returns:
        IRNResponse: The IRN details
    """
    irn_record = crud_irn.get_irn_by_value(db, irn)
    if not irn_record:
        raise HTTPException(
            status_code=404,
            detail="IRN not found"
        )
    
    # Verify user has access to this IRN's integration
    integration = crud_integration.get_integration_by_id(db, UUID(irn_record.integration_id))
    if integration and integration.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this IRN"
        )
    
    # Check if IRN is expired
    if irn_record.valid_until < datetime.now() and irn_record.status != "expired":
        try:
            irn_record = crud_irn.update_irn_status(db, irn, "expired")
        except HTTPException as e:
            logger.warning(f"Failed to update expired IRN status: {str(e)}")
    
    return irn_record


@router.get("/", response_model=List[IRNResponse])
def list_irns(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    integration_id: UUID = Query(..., description="Integration ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=100, description="Maximum number of records to return")
):
    """
    List IRNs for a specific integration with pagination.
    
    Returns:
        List[IRNResponse]: List of IRN records
    """
    # Verify integration exists
    integration = crud_integration.get_integration_by_id(db, integration_id)
    if not integration:
        raise HTTPException(
            status_code=404,
            detail="Integration not found"
        )
    
    # Verify user has access to this integration
    if integration.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this integration"
        )
    
    irn_records = crud_irn.get_irns_by_integration(db, integration_id, skip, limit)
    return irn_records


@router.post("/{irn}/status", response_model=IRNResponse)
def update_irn_status(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    irn: str = Path(..., description="IRN to update"),
    status_update: IRNStatusUpdate
):
    """
    Update the status of an IRN (used, unused, expired).
    
    Returns:
        IRNResponse: The updated IRN
    """
    # Verify IRN exists
    irn_record = crud_irn.get_irn_by_value(db, irn)
    if not irn_record:
        raise HTTPException(
            status_code=404,
            detail="IRN not found"
        )
    
    # Verify user has access to this IRN's integration
    integration = crud_integration.get_integration_by_id(db, UUID(irn_record.integration_id))
    if integration and integration.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to update this IRN"
        )
    
    try:
        # Update status
        updated_irn = crud_irn.update_irn_status(
            db, 
            irn, 
            status_update.status, 
            status_update.invoice_id
        )
        
        return updated_irn
    except HTTPException as e:
        # Pass through HTTPExceptions
        raise e
    except Exception as e:
        logger.error(f"Error updating IRN status: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update IRN status: {str(e)}"
        )


@router.get("/metrics/{integration_id}", response_model=IRNMetricsResponse)
def get_irn_metrics(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    integration_id: Optional[UUID] = Path(None, description="Optional integration ID to filter metrics")
):
    """
    Get IRN usage metrics (counts by status, recent IRNs).
    
    Returns:
        IRNMetricsResponse: Metrics about IRN usage
    """
    # If integration ID provided, verify access
    if integration_id:
        integration = crud_integration.get_integration_by_id(db, integration_id)
        if integration and integration.organization_id != current_user.organization_id:
            raise HTTPException(
                status_code=403,
                detail="Not authorized to access this integration's metrics"
            )
    
    try:
        metrics = crud_irn.get_irn_metrics(db, integration_id)
        return metrics
    except HTTPException as e:
        # Pass through HTTPExceptions
        raise e
    except Exception as e:
        logger.error(f"Error retrieving IRN metrics: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve IRN metrics: {str(e)}"
        )


@router.post("/expire-outdated", response_model=dict)
def expire_outdated_irns(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update all expired but not marked IRNs to expired status.
    This is typically called by a scheduled job, but can be manually triggered.
    
    Admin access required.
    
    Returns:
        dict: Count of updated IRNs
    """
    # Check if user has admin rights
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )
    
    try:
        updated_count = crud_irn.expire_outdated_irns(db)
        return {"updated_count": updated_count}
    except HTTPException as e:
        # Pass through HTTPExceptions
        raise e
    except Exception as e:
        logger.error(f"Error expiring outdated IRNs: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to expire outdated IRNs: {str(e)}"
        )


@router.post("/odoo/generate", response_model=IRNResponse, status_code=201)
def generate_irn_for_odoo_invoice(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    request: OdooIRNGenerateRequest
):
    """
    Generate an IRN for a specific Odoo invoice.
    
    Takes an Odoo invoice ID and generates an IRN for it. The invoice data is
    fetched from the Odoo instance and stored with the IRN.
    
    Returns:
        IRNResponse: The generated IRN with metadata
    """
    # Get the integration
    integration = crud_integration.get_integration_by_id(db, request.integration_id)
    if not integration:
        raise HTTPException(
            status_code=404,
            detail="Integration not found"
        )
    
    # Verify user has access to this integration
    if integration.organization_id != current_user.organization_id:
        raise HTTPException(
            status_code=403,
            detail="Not authorized to access this integration"
        )
    
    # Verify this is an Odoo integration
    if integration.integration_type != "odoo":
        raise HTTPException(
            status_code=400,
            detail="This endpoint can only be used with Odoo integrations"
        )
    
    # Get organization for service ID
    organization = crud_organization.get_organization_by_id(db, current_user.organization_id)
    if not organization or not organization.firs_service_id:
        logger.warning(f"Organization {current_user.organization_id} missing FIRS service ID")
        # For POC, use a placeholder service ID if not set
        service_id = "94ND90NR"
    else:
        service_id = organization.firs_service_id
    
    try:
        # Extract Odoo config from integration
        odoo_config = integration.config
        
        # Generate IRN for Odoo invoice
        result = odoo_service.generate_irn_for_odoo_invoice(
            config=odoo_config,
            invoice_id=request.odoo_invoice_id,
            integration_id=str(integration.id),
            service_id=service_id,
            user_id=str(current_user.id)
        )
        
        if not result["success"]:
            raise HTTPException(
                status_code=422,
                detail=result["message"]
            )
        
        # Get the created IRN record
        irn_record = crud_irn.get_irn_by_value(db, result["details"]["irn"])
        if not irn_record:
            raise HTTPException(
                status_code=500,
                detail="IRN was generated but could not be retrieved"
            )
        
        return irn_record
        
    except HTTPException as e:
        # Pass through HTTPExceptions
        raise e
    except Exception as e:
        logger.error(f"Error generating IRN for Odoo invoice: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate IRN for Odoo invoice: {str(e)}"
        )


@router.get("/validate/{irn}", response_model=IRNValidationResponse)
def validate_irn(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    irn: str = Path(..., description="IRN to validate")
):
    """
    Validate an IRN and retrieve its status.
    
    This endpoint validates the IRN and updates its status if required
    (e.g., if it's expired). It also records the validation attempt.
    
    Returns:
        IRNValidationResponse: The validation result
    """
    try:
        # Call the validation service
        result = odoo_service.validate_irn(irn)
        
        # Add user who performed the validation
        if "request_data" not in result.get("details", {}):
            if "details" not in result:
                result["details"] = {}
            result["details"]["validated_by"] = str(current_user.id)
        
        return result
        
    except HTTPException as e:
        # Pass through HTTPExceptions
        raise e
    except Exception as e:
        logger.error(f"Error validating IRN: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate IRN: {str(e)}"
        )


@router.get("/odoo/{odoo_invoice_id}", response_model=List[IRNResponse])
def get_irns_for_odoo_invoice(
    *,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    odoo_invoice_id: int = Path(..., description="Odoo invoice ID to look up")
):
    """
    Get all IRNs associated with a specific Odoo invoice.
    
    Returns:
        List[IRNResponse]: The list of IRNs for the specified Odoo invoice
    """
    try:
        # Get IRNs for the Odoo invoice
        result = odoo_service.get_irn_for_odoo_invoice(odoo_invoice_id)
        
        if not result["success"]:
            if result["details"].get("error_type") == "NotFound":
                raise HTTPException(
                    status_code=404,
                    detail=result["message"]
                )
            else:
                raise HTTPException(
                    status_code=422,
                    detail=result["message"]
                )
        
        # Get the IRN records from the database for proper formatting
        irn_records = []
        for irn_data in result["details"]["irn_records"]:
            irn_record = crud_irn.get_irn_by_value(db, irn_data["irn"])
            if irn_record:
                # Check if user has access to this IRN's integration
                integration = crud_integration.get_integration_by_id(db, UUID(irn_record.integration_id))
                if integration and integration.organization_id == current_user.organization_id:
                    irn_records.append(irn_record)
        
        return irn_records
        
    except HTTPException as e:
        # Pass through HTTPExceptions
        raise e
    except Exception as e:
        logger.error(f"Error retrieving IRNs for Odoo invoice: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve IRNs for Odoo invoice: {str(e)}"
        )