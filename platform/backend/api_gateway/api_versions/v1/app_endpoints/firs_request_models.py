"""Pydantic request models for APP FIRS v1 endpoints."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, root_validator, validator


class _ExtraAllowModel(BaseModel):
    """Base model that permits additional keys without validation failures."""

    class Config:
        extra = "allow"


class GenerateInvoiceRequest(_ExtraAllowModel):
    taxpayer_id: str = Field(..., description="Taxpayer identifier associated with the invoice")
    invoice_data: Dict[str, Any] = Field(..., description="Invoice payload to transform into FIRS format")


class GenerateInvoiceBatchRequest(_ExtraAllowModel):
    invoices: List[Dict[str, Any]] = Field(..., description="Invoices to generate in a batch")


class SubmitInvoiceRequest(_ExtraAllowModel):
    taxpayer_id: str = Field(..., description="Taxpayer identifier for the submission")
    invoice_data: Dict[str, Any] = Field(..., description="Invoice payload previously generated for FIRS")
    delivery: Optional[Dict[str, Any]] = Field(None, description="Optional delivery routing metadata")


class SubmitInvoiceBatchRequest(_ExtraAllowModel):
    invoices: Optional[List[Dict[str, Any]]] = Field(
        None, description="Collection of invoices to submit"
    )
    batch_submission_data: Optional[Dict[str, Any]] = Field(
        None, description="Structured batch submission descriptor"
    )

    @root_validator
    def _ensure_batch_payload(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get("invoices") or values.get("batch_submission_data"):
            return values
        raise ValueError("Either invoices or batch_submission_data must be provided")


class UBLComplianceRequest(_ExtraAllowModel):
    document_data: Dict[str, Any] = Field(..., description="Document to validate against UBL requirements")


class UBLBatchComplianceRequest(_ExtraAllowModel):
    documents: Optional[List[Dict[str, Any]]] = Field(
        None, description="List of documents to validate"
    )
    batch: Optional[Dict[str, Any]] = Field(
        None, description="Structured batch details for validation"
    )

    @root_validator
    def _ensure_documents(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if values.get("documents"):
            return values
        batch = values.get("batch")
        if isinstance(batch, dict) and batch:
            return values
        raise ValueError("Batch validation requires documents or batch details")


class FIRSConnectionTestRequest(_ExtraAllowModel):
    api_key: str = Field(..., description="FIRS API key")
    api_secret: str = Field(..., description="FIRS API secret")
    environment: Optional[str] = Field("sandbox", description="Target environment")


class FIRSCredentialsRequest(_ExtraAllowModel):
    api_key: Optional[str] = Field(
        None,
        description="FIRS API key. Provide the full value to update; leave masked or blank to retain the current secret.",
    )
    api_secret: Optional[str] = Field(
        None,
        description="FIRS API secret. Provide the full value to update; leave masked or blank to retain the current secret.",
    )
    environment: Optional[str] = Field(
        "sandbox",
        description="Target FIRS environment (sandbox or production)",
    )
    webhook_url: Optional[str] = Field(
        None,
        description="Webhook endpoint to receive FIRS status callbacks",
    )


class FIRSAuthenticationRequest(_ExtraAllowModel):
    auth_data: Dict[str, Any] = Field(..., description="Authentication payload to forward to FIRS")

    @validator("auth_data")
    def _non_empty_auth(cls, value: Dict[str, Any]) -> Dict[str, Any]:
        if not value:
            raise ValueError("auth_data must not be empty")
        return value


class GenericValidationPayload(_ExtraAllowModel):
    """Fallback payload that only enforces non-empty request bodies."""

    @root_validator(pre=True)
    def _ensure_body(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if not values:
            raise ValueError("Request body must not be empty")
        return values


class TaxpayerCreateRequest(_ExtraAllowModel):
    name: str = Field(..., description="Display name for the taxpayer")
    tax_id: str = Field(..., description="Primary taxpayer identification number")
    contact_info: Dict[str, Any] = Field(..., description="Primary contact information payload")


class TaxpayerUpdateRequest(_ExtraAllowModel):
    name: Optional[str] = Field(None, description="Updated taxpayer name")
    contact_info: Optional[Dict[str, Any]] = Field(None, description="Updated contact information")
    status: Optional[str] = Field(None, description="Updated taxpayer status")

    @root_validator
    def _ensure_updates(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        if any(value is not None for value in values.values()):
            return values
        raise ValueError("At least one field must be provided for update")
