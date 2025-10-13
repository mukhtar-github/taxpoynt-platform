"""
Comprehensive FIRS Invoice Generator
====================================
Aggregates data from business systems (ERP, CRM, POS, E-commerce) and 
financial systems (Banking, Payment processors) to generate FIRS-compliant invoices.

This service implements the complete data convergence strategy for
SI (System Integrator) role invoice generation.
"""

import asyncio
import copy
import logging
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Any, Optional, Tuple
from uuid import UUID, uuid4
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

# Fixed imports - use relative imports instead of platform.backend
from core_platform.data_management.models.firs_submission import (
    FIRSSubmission, SubmissionStatus, ValidationStatus
)
from hybrid_services.correlation_management.si_app_correlation_service import SIAPPCorrelationService
from core_platform.data_management.models.organization import Organization
from external_integrations.financial_systems.banking.open_banking.invoice_automation.firs_formatter import (
    FIRSFormatter, FormattingResult
)
from core_platform.utils.irn_helper import (
    IRNGenerationError,
    generate_canonical_irn,
)
from si_services.schema_compliance.schema_transformer import schema_transformer
from si_services.schema_compliance.ubl_validator import ubl_validator
from si_services.certificate_management.digital_certificate_service import DigitalCertificateService
from si_services.transformation import (
    TransformationConfig,
    TransformationOrchestrator,
    ERPSystem,
)
from si_services.irn_qr_generation.qr_signing_service import QRSigningService, QREncryptionResult
# Conditional import for unified Odoo connector (org-scoped support)
try:
    from external_integrations.business_systems.odoo.unified_connector import OdooUnifiedConnector
except Exception:
    OdooUnifiedConnector = None
# Conditional imports for connectors (graceful failure for missing connectors)
try:
    from external_integrations.business_systems.erp.sap_connector import SAPConnector  # legacy path
except Exception:
    try:
        from external_integrations.business_systems.erp.sap.connector import SAPConnector  # current path
    except Exception:
        SAPConnector = None

try:
    from external_integrations.business_systems.erp.odoo_connector import OdooConnector  # legacy path
except Exception:
    try:
        from external_integrations.business_systems.erp.odoo.connector import OdooConnector  # current path
    except Exception:
        OdooConnector = None

# Purged US-centric connectors (Salesforce, Square, Shopify) for Nigerian deployments

try:
    from external_integrations.financial_systems.banking.mono_connector import MonoConnector  # legacy path
except Exception:
    try:
        from external_integrations.financial_systems.banking.open_banking.providers.mono.connector import MonoConnector
    except Exception:
        MonoConnector = None

try:
    from external_integrations.financial_systems.payments.paystack_connector import PaystackConnector  # legacy path
except Exception:
    try:
        from external_integrations.financial_systems.payments.nigerian_processors.paystack.connector import PaystackConnector
    except Exception:
        PaystackConnector = None

logger = logging.getLogger(__name__)


# Optional: universal processor (feature-flagged)
try:
    from core_platform.transaction_processing import (
        get_transaction_processing_service,
        initialize_transaction_processing_service,
        ConnectorType,
    )
    from core_platform.transaction_processing.models.universal_transaction import UniversalTransaction
    from core_platform.transaction_processing.models.universal_processed_transaction import ProcessingStatus
except Exception:
    get_transaction_processing_service = None  # type: ignore
    initialize_transaction_processing_service = None  # type: ignore
    ConnectorType = None  # type: ignore
    UniversalTransaction = None  # type: ignore
    ProcessingStatus = None  # type: ignore


class DataSourceType(str, Enum):
    """Types of data sources for invoice generation."""
    ERP = "erp"
    CRM = "crm"
    POS = "pos"
    ECOMMERCE = "ecommerce"
    BANKING = "banking"
    PAYMENT = "payment"


class TransactionConfidence(str, Enum):
    """Confidence levels for auto-reconciled transactions."""
    HIGH = "high"      # 95%+
    MEDIUM = "medium"  # 85-94%
    LOW = "low"        # <85%


@dataclass
class BusinessTransactionData:
    """Unified transaction data structure from any business system."""
    id: str
    source_type: DataSourceType
    source_id: str
    transaction_id: str
    date: datetime
    customer_name: str
    customer_email: Optional[str]
    customer_tin: Optional[str]
    amount: Decimal
    currency: str
    description: str
    line_items: List[Dict[str, Any]]
    tax_amount: Decimal
    vat_rate: Decimal
    payment_status: str
    payment_method: Optional[str]
    confidence: float
    raw_data: Dict[str, Any]


@dataclass
class FIRSInvoiceGenerationRequest:
    """Request for generating FIRS-compliant invoices."""
    organization_id: UUID
    transaction_ids: List[str]
    invoice_type: str = "standard"
    consolidate: bool = False
    include_digital_signature: bool = True
    customer_overrides: Optional[Dict[str, str]] = None


@dataclass
class FIRSInvoiceGenerationResult:
    """Result of FIRS invoice generation."""
    success: bool
    invoices: List[Dict[str, Any]]
    errors: List[str]
    warnings: List[str]
    total_amount: Decimal
    irns_generated: List[str]


class ComprehensiveFIRSInvoiceGenerator:
    """
    Comprehensive FIRS invoice generator that aggregates data from
    all connected business and financial systems.
    """

    def __init__(
        self,
        db_session: AsyncSession,
        firs_formatter: FIRSFormatter
    ):
        self.db = db_session
        self.firs_formatter = firs_formatter
        self.correlation_service = SIAPPCorrelationService(db_session)
        self.transformation_orchestrator = TransformationOrchestrator()
        
        # Initialize connectors for all supported systems (graceful handling of missing connectors)
        self.connectors = {
            DataSourceType.ERP: {
                'sap': SAPConnector() if SAPConnector else None,
                'odoo': OdooConnector() if OdooConnector else None
            },
            DataSourceType.CRM: {},
            DataSourceType.POS: {},
            DataSourceType.ECOMMERCE: {},
            DataSourceType.BANKING: {
                'mono': MonoConnector() if MonoConnector else None
            },
            DataSourceType.PAYMENT: {
                'paystack': PaystackConnector() if PaystackConnector else None,
                'flutterwave': None  # To be implemented
            }
        }

        self.stats = {
            'transactions_processed': 0,
            'invoices_generated': 0,
            'total_amount_processed': Decimal('0'),
            'errors_encountered': 0
        }

        # Initialize Odoo unified connector from env if available
        self.odoo_unified = None
        if OdooUnifiedConnector:
            try:
                self.odoo_unified = OdooUnifiedConnector.from_env()
                if self.odoo_unified and not self.odoo_unified.available():
                    self.odoo_unified = None
            except Exception as e:
                logger.debug(f"OdooUnifiedConnector initialization skipped: {e}")

        # Org-scoped connector cache
        self._odoo_by_org: Dict[str, Any] = {}
        self.certificate_service = DigitalCertificateService()
        key_path_env = os.getenv("FIRS_CRYPTO_KEYS_PATH")
        self.qr_signing_service = QRSigningService(
            key_path=Path(key_path_env).expanduser() if key_path_env else None
        )
        self._organization_cache: Dict[str, Organization] = {}
        self._signing_certificate_cache: Dict[str, Optional[str]] = {}

    async def _get_odoo_unified(self, organization_id: UUID):
        """Return an OdooUnifiedConnector for the given organization, preferring org config over env.
        Caches per-org connector for reuse within this generator instance.
        """
        if not OdooUnifiedConnector:
            return None
        key = str(organization_id)
        if key in self._odoo_by_org:
            return self._odoo_by_org[key]

        try:
            org_result = await self.db.execute(select(Organization).where(Organization.id == organization_id))
            org = org_result.scalar_one_or_none()
            cfg = None
            if org and org.firs_configuration and isinstance(org.firs_configuration, dict):
                # Accept nested 'odoo' or 'odoo_config' blocks or flat keys
                if 'odoo' in org.firs_configuration and isinstance(org.firs_configuration['odoo'], dict):
                    cfg = org.firs_configuration['odoo']
                elif 'odoo_config' in org.firs_configuration and isinstance(org.firs_configuration['odoo_config'], dict):
                    cfg = org.firs_configuration['odoo_config']
                else:
                    cfg = org.firs_configuration
            if cfg:
                url = cfg.get('url') or cfg.get('host') or cfg.get('api_url') or os.getenv('ODOO_URL') or os.getenv('ODOO_API_URL')
                # Normalize host-only values into full https URL if needed
                if url and not url.startswith('http'):
                    url = f"https://{url}"
                db = cfg.get('db') or cfg.get('database') or os.getenv('ODOO_DB') or os.getenv('ODOO_DATABASE')
                username = cfg.get('username') or os.getenv('ODOO_USERNAME')
                api_key = cfg.get('api_key') or os.getenv('ODOO_API_KEY')
                password = cfg.get('password') or os.getenv('ODOO_PASSWORD')
                verify_ssl = bool(cfg.get('verify_ssl', True))
                timeout = int(cfg.get('timeout', os.getenv('ODOO_TIMEOUT') or 120))
                company_id = cfg.get('company_id') or os.getenv('ODOO_COMPANY_ID')
                company_id = int(company_id) if isinstance(company_id, (int, str)) and str(company_id).isdigit() else None
                if url and db and username and (api_key or password):
                    connector = OdooUnifiedConnector(url=url, db=db, username=username, api_key=api_key, password=password, verify_ssl=verify_ssl, timeout=timeout, company_id=company_id)
                    if connector.available():
                        self._odoo_by_org[key] = connector
                        return connector
        except Exception as e:
            logger.debug(f"Org-scoped Odoo config not available for {organization_id}: {e}")

        # Fallback to env-level connector
        self._odoo_by_org[key] = self.odoo_unified
        return self.odoo_unified

    async def _get_organization_profile(self, organization_id: UUID) -> Optional[Organization]:
        """Fetch organization details with simple caching."""

        cache_key = str(organization_id)
        if cache_key in self._organization_cache:
            return self._organization_cache[cache_key]

        result = await self.db.execute(select(Organization).where(Organization.id == organization_id))
        organization = result.scalar_one_or_none()
        if organization:
            self._organization_cache[cache_key] = organization
        return organization

    async def _get_signing_certificate_id(self, organization: Optional[Organization]) -> Optional[str]:
        """Resolve the certificate ID used for digital signing."""

        cache_key = str(organization.id) if organization else "default"
        if cache_key in self._signing_certificate_cache:
            return self._signing_certificate_cache[cache_key]

        certificate_id: Optional[str] = None
        if organization and organization.firs_configuration and isinstance(organization.firs_configuration, dict):
            certificate_id = organization.firs_configuration.get("signing_certificate_id") or organization.firs_configuration.get("certificate_id")

        if not certificate_id:
            certificate_id = os.getenv("SI_SIGNING_CERTIFICATE_ID")

        self._signing_certificate_cache[cache_key] = certificate_id
        return certificate_id

    def _safe_decimal(self, value: Any, default: Decimal = Decimal('0')) -> Decimal:
        """Convert arbitrary inputs to Decimal with graceful fallback."""

        try:
            if value is None:
                return default
            return Decimal(str(value))
        except (ArithmeticError, ValueError, TypeError):
            return default

    def _infer_vat_rate(
        self,
        line_items: List[Dict[str, Any]],
        tax_amount: Decimal,
        subtotal: Decimal,
        fallback: Decimal = Decimal('7.5')
    ) -> Decimal:
        """Infer VAT rate from line items or totals."""

        for item in line_items or []:
            candidate = item.get("tax_rate") or item.get("vat_rate")
            if candidate is None:
                continue
            candidate_decimal = self._safe_decimal(candidate, fallback)
            if candidate_decimal > 0:
                return candidate_decimal

        if subtotal > 0:
            derived = (tax_amount / subtotal) * Decimal('100')
            if derived > 0:
                return derived

        return fallback

    def _build_supplier_payload(self, organization: Optional[Organization]) -> Dict[str, Any]:
        """Create supplier structure expected by the schema transformer."""

        name = organization.display_name if organization else self.firs_formatter.supplier_info.get("name", "Unknown Supplier")
        tax_id = None
        registration = None
        phone = None
        email = None
        street = None
        city = None
        state = None
        postal_code = None
        country = "Nigeria"
        country_code = "NG"

        if organization:
            tax_id = organization.tin or organization.vat_number
            registration = organization.rc_number
            phone = organization.phone
            email = organization.email
            street = organization.address
            city = organization.city
            state = organization.state
            postal_code = organization.postal_code
            if organization.country:
                country = organization.country

        return {
            "name": name,
            "vat": tax_id,
            "company_registry": registration,
            "phone": phone,
            "email": email,
            "street": street,
            "street2": None,
            "city": city,
            "zip": postal_code,
            "state_id": {"name": state} if state else {},
            "country_id": {"code": country_code, "name": country},
        }

    def _build_customer_payload(self, customer: Dict[str, Any]) -> Dict[str, Any]:
        """Create customer structure for the transformer."""

        name = customer.get("name") or customer.get("customer_name") or "Unknown Customer"
        street = customer.get("street") or customer.get("address")
        city = customer.get("city")
        state = customer.get("state")
        postal_code = customer.get("postal_code")
        country_code = customer.get("country_code") or "NG"
        country_name = customer.get("country") or "Nigeria"

        return {
            "name": name,
            "vat": customer.get("tin") or customer.get("customer_tin"),
            "phone": customer.get("phone") or customer.get("telephone"),
            "email": customer.get("email"),
            "street": street,
            "street2": customer.get("street2"),
            "city": city,
            "zip": postal_code,
            "state_id": {"name": state} if state else {},
            "country_id": {"code": country_code, "name": country_name},
        }

    def _build_invoice_lines_payload(
        self,
        line_items: List[Dict[str, Any]],
        currency: str,
        vat_rate: Decimal,
        total_tax_amount: Decimal
    ) -> List[Dict[str, Any]]:
        """Convert internal line items into a structure compatible with the transformer."""

        if not line_items:
            return []

        count = len(line_items)
        fallback_tax = total_tax_amount / count if count else Decimal('0')
        transformed: List[Dict[str, Any]] = []

        for item in line_items:
            quantity = self._safe_decimal(item.get("quantity") or item.get("qty") or 1, Decimal('1'))
            subtotal = self._safe_decimal(
                item.get("subtotal")
                or item.get("line_total")
                or item.get("amount")
                or item.get("net_amount"),
                Decimal('0'),
            )
            tax_amount = self._safe_decimal(item.get("tax_amount"), fallback_tax)
            line_total = subtotal + tax_amount
            unit_price = self._safe_decimal(item.get("unit_price"), Decimal('0'))
            if unit_price == 0 and quantity > 0:
                unit_price = line_total / quantity

            item_name = item.get("name") or item.get("description") or "Line item"
            description = item.get("description") or item_name
            tax_rate = self._safe_decimal(
                item.get("tax_rate") or item.get("vat_rate"),
                vat_rate,
            )

            transformed.append(
                {
                    "quantity": float(quantity if quantity > 0 else Decimal('1')),
                    "price_unit": float(unit_price),
                    "price_subtotal": float(subtotal),
                    "product_id": {"name": item_name},
                    "name": description,
                    "invoice_line_tax_ids": {
                        "amount": float(tax_amount),
                        "currency_id": {"name": currency},
                        "tax_id": {
                            "amount": float(tax_rate),
                            "name": item.get("tax_code") or "VAT",
                        },
                    },
                    "uom_id": {"name": item.get("unit_code") or item.get("uom") or "EA"},
                }
            )

        return transformed

    def _prepare_ubl_source(
        self,
        invoice_data: Dict[str, Any],
        organization: Optional[Organization]
    ) -> Dict[str, Any]:
        """Prepare source payload for the schema transformer from aggregated invoice data."""

        currency = invoice_data.get("currency", "NGN")
        subtotal = self._safe_decimal(invoice_data.get("subtotal"), Decimal('0'))
        tax_amount = self._safe_decimal(invoice_data.get("tax_amount"), Decimal('0'))
        total_amount = self._safe_decimal(invoice_data.get("total_amount"), subtotal + tax_amount)
        vat_rate = self._infer_vat_rate(invoice_data.get("line_items", []), tax_amount, subtotal)

        supplier = self._build_supplier_payload(organization)
        customer = self._build_customer_payload(invoice_data.get("customer", {}))
        line_payloads = self._build_invoice_lines_payload(
            invoice_data.get("line_items", []),
            currency,
            vat_rate,
            tax_amount,
        )

        source_payload: Dict[str, Any] = {
            "number": invoice_data.get("invoice_number"),
            "date_invoice": invoice_data.get("invoice_date"),
            "date_due": invoice_data.get("due_date"),
            "currency_id": {"name": currency},
            "amount_untaxed": float(subtotal),
            "amount_tax": float(tax_amount),
            "amount_total": float(total_amount),
            "company_id": supplier,
            "partner_id": customer,
            "invoice_line_ids": line_payloads,
            "tax_line_ids": [
                {
                    "base": float(subtotal),
                    "amount": float(tax_amount),
                    "currency_id": {"name": currency},
                    "tax_id": {
                        "name": "VAT",
                        "amount": float(vat_rate),
                    },
                }
            ],
        }

        return source_payload

    def _infer_erp_system(self, transaction: Optional[BusinessTransactionData]) -> ERPSystem:
        """Infer the ERP system for a transaction for transformation configuration."""

        if not transaction:
            return ERPSystem.GENERIC

        if transaction.source_type == DataSourceType.ERP:
            source_id = (transaction.source_id or "").lower()
            if "odoo" in source_id:
                return ERPSystem.ODOO
            if "sap" in source_id:
                return ERPSystem.SAP
            if "quickbook" in source_id:
                return ERPSystem.QUICKBOOKS
            if "sage" in source_id:
                return ERPSystem.SAGE

        return ERPSystem.GENERIC

    async def _run_transformation_pipeline(
        self,
        base_invoice: Dict[str, Any],
        source_context: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        """Execute the transformation orchestrator to obtain normalized invoice data."""

        if not self.transformation_orchestrator or not source_context:
            return None

        transaction: Optional[BusinessTransactionData] = source_context.get("transaction")
        if not transaction:
            transactions: List[BusinessTransactionData] = source_context.get("transactions", [])  # type: ignore[arg-type]
            if transactions:
                transaction = transactions[0]

        if not transaction:
            return None

        erp_payload: Dict[str, Any]
        if isinstance(transaction.raw_data, dict) and transaction.raw_data:
            erp_payload = transaction.raw_data
        else:
            erp_payload = base_invoice

        erp_system = self._infer_erp_system(transaction)

        config = TransformationConfig(
            source_erp_system=erp_system,
            target_currency=base_invoice.get("currency", "NGN"),
            target_country="Nigeria",
            strict_validation=False,
        )

        try:
            result = await self.transformation_orchestrator.transform_invoice(erp_payload, config)
        except Exception as exc:
            logger.warning(
                "Transformation pipeline execution failed for %s: %s",
                erp_system.value,
                exc,
            )
            return {
                "success": False,
                "erp_system": erp_system.value,
                "warnings": [],
                "errors": [str(exc)],
                "metadata": {"failure_stage": "pipeline_execution"},
                "processing_time": 0.0,
                "normalized_invoice": None,
            }

        return {
            "success": result.success,
            "erp_system": erp_system.value,
            "warnings": result.warnings or [],
            "errors": result.errors or [],
            "metadata": result.metadata,
            "processing_time": result.processing_time,
            "normalized_invoice": result.transformed_data,
        }

    def _hydrate_invoice_from_normalized(
        self,
        base_invoice: Dict[str, Any],
        normalized: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Merge normalized invoice data into the working invoice payload when available."""

        if not normalized:
            return base_invoice

        invoice = copy.deepcopy(base_invoice)

        if normalized.get("invoice_number"):
            invoice["invoice_number"] = normalized["invoice_number"]
        if normalized.get("invoice_date"):
            invoice["invoice_date"] = normalized["invoice_date"]
        if normalized.get("due_date"):
            invoice["due_date"] = normalized["due_date"]

        currency_code = normalized.get("currency_code")
        if currency_code:
            invoice["currency"] = currency_code

        total_amount = normalized.get("total_amount")
        tax_amount = normalized.get("tax_amount")
        if total_amount is not None:
            invoice["total_amount"] = float(total_amount)
        if tax_amount is not None:
            invoice["tax_amount"] = float(tax_amount)
        if total_amount is not None and tax_amount is not None:
            invoice["subtotal"] = float(total_amount) - float(tax_amount)
        elif total_amount is not None and invoice.get("tax_amount") is not None:
            invoice["subtotal"] = float(total_amount) - float(invoice["tax_amount"])
        elif tax_amount is not None and invoice.get("total_amount") is not None:
            invoice["subtotal"] = float(invoice["total_amount"]) - float(tax_amount)

        customer_info = invoice.get("customer", {}).copy()
        if normalized.get("customer_name"):
            customer_info.setdefault("name", normalized["customer_name"])
        if normalized.get("customer_tin"):
            customer_info.setdefault("tin", normalized["customer_tin"])
        invoice["customer"] = customer_info

        normalized_lines = normalized.get("line_items")
        if normalized_lines and not invoice.get("line_items"):
            converted_lines: List[Dict[str, Any]] = []
            for line in normalized_lines:
                converted_lines.append(
                    {
                        "name": line.get("description") or line.get("item") or "Line Item",
                        "description": line.get("description"),
                        "quantity": line.get("quantity", 0),
                        "price_unit": line.get("unit_price", 0),
                        "price_subtotal": line.get("total", 0),
                        "tax_rate": line.get("tax_rate"),
                    }
                )
            invoice["line_items"] = converted_lines

        return invoice

    async def _process_invoice_pipeline(
        self,
        invoice_data: Dict[str, Any],
        organization: Optional[Organization],
        include_signature: bool,
        source_context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[
        Dict[str, Any],
        Dict[str, Any],
        Optional[Dict[str, Any]],
        bool,
        List[Dict[str, Any]],
        List[str],
        Dict[str, Any],
    ]:
        """Run mapping, validation, and optional signing for an invoice payload."""

        working_invoice = copy.deepcopy(invoice_data)
        transformation_summary = await self._run_transformation_pipeline(working_invoice, source_context)

        if transformation_summary is None:
            transformation_summary = {
                "success": None,
                "warnings": [],
                "errors": [],
                "erp_system": None,
                "metadata": None,
                "processing_time": 0.0,
                "normalized_invoice": None,
            }

        normalized_invoice = transformation_summary.pop("normalized_invoice", None)
        working_invoice = self._hydrate_invoice_from_normalized(working_invoice, normalized_invoice)

        pipeline_warnings: List[str] = []
        summary_warnings = transformation_summary.get("warnings") or []
        if summary_warnings:
            pipeline_warnings.extend(summary_warnings)

        summary_errors = transformation_summary.get("errors") or []
        if summary_errors and transformation_summary.get("success") is False:
            pipeline_warnings.extend([f"Transformation error: {err}" for err in summary_errors if err])

        source_payload = self._prepare_ubl_source(working_invoice, organization)
        ubl_invoice = schema_transformer.transform_to_ubl_invoice(source_payload)
        firs_invoice = schema_transformer.transform_to_firs_format(ubl_invoice)
        is_valid, validation_errors = ubl_validator.validate_ubl_document(ubl_invoice)

        signature_info: Optional[Dict[str, Any]] = None

        if include_signature:
            if is_valid:
                certificate_id = await self._get_signing_certificate_id(organization)
                if certificate_id:
                    try:
                        signature_info = self.certificate_service.sign_invoice_document(
                            ubl_invoice,
                            certificate_id=certificate_id,
                        )
                    except Exception as exc:
                        pipeline_warnings.append(f"Digital signature failed: {exc}")
                else:
                    pipeline_warnings.append("Signing certificate not configured for organization")
            else:
                pipeline_warnings.append("Invoice failed validation; skipping digital signature")

        transformation_summary["invoice_payload"] = copy.deepcopy(working_invoice)

        return (
            ubl_invoice,
            firs_invoice,
            signature_info,
            is_valid,
            validation_errors,
            pipeline_warnings,
            transformation_summary,
        )

    async def aggregate_business_data(
        self,
        organization_id: UUID,
        date_range: Optional[Tuple[datetime, datetime]] = None
    ) -> List[BusinessTransactionData]:
        """
        Aggregate transaction data from all connected business and financial systems.
        
        Args:
            organization_id: Organization ID
            date_range: Optional date range for transactions
            
        Returns:
            List of unified transaction data
        """
        logger.info(f"Aggregating business data for organization {organization_id}")
        
        if not date_range:
            # Default to last 30 days
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=30)
            date_range = (start_date, end_date)

        all_transactions = []

        # Aggregate from ERP systems
        erp_transactions = await self._aggregate_erp_data(organization_id, date_range)
        all_transactions.extend(erp_transactions)

        # Aggregate from CRM systems
        crm_transactions = await self._aggregate_crm_data(organization_id, date_range)
        all_transactions.extend(crm_transactions)

        # Aggregate from POS systems
        pos_transactions = await self._aggregate_pos_data(organization_id, date_range)
        all_transactions.extend(pos_transactions)

        # Aggregate from E-commerce systems
        ecom_transactions = await self._aggregate_ecommerce_data(organization_id, date_range)
        all_transactions.extend(ecom_transactions)

        # Aggregate from Banking systems
        banking_transactions = await self._aggregate_banking_data(organization_id, date_range)
        all_transactions.extend(banking_transactions)

        # Aggregate from Payment processors
        payment_transactions = await self._aggregate_payment_data(organization_id, date_range)
        all_transactions.extend(payment_transactions)

        # Cross-reference and reconcile transactions
        reconciled_transactions = await self._cross_reference_transactions(all_transactions)

        logger.info(f"Aggregated {len(reconciled_transactions)} transactions from {len(all_transactions)} raw transactions")
        return reconciled_transactions

    async def _aggregate_erp_data(
        self,
        organization_id: UUID,
        date_range: Tuple[datetime, datetime]
    ) -> List[BusinessTransactionData]:
        """Aggregate data from ERP systems (SAP, Odoo, etc.)."""
        transactions = []

        # SAP ERP Data
        try:
            sap_connector = self.connectors[DataSourceType.ERP]['sap']
            if sap_connector is not None:
                sap_invoices = await sap_connector.get_invoices_by_date_range(
                    organization_id, date_range[0], date_range[1]
                )
            else:
                logger.debug("SAP connector not available, skipping SAP data aggregation")
                sap_invoices = []
            
            for invoice in sap_invoices:
                transaction = BusinessTransactionData(
                    id=f"sap-{invoice['id']}",
                    source_type=DataSourceType.ERP,
                    source_id="sap",
                    transaction_id=invoice['invoice_number'],
                    date=invoice['invoice_date'],
                    customer_name=invoice['customer']['name'],
                    customer_email=invoice['customer'].get('email'),
                    customer_tin=invoice['customer'].get('tin'),
                    amount=Decimal(str(invoice['total_amount'])),
                    currency=invoice.get('currency', 'NGN'),
                    description=invoice['description'],
                    line_items=invoice['line_items'],
                    tax_amount=Decimal(str(invoice['tax_amount'])),
                    vat_rate=Decimal(str(invoice.get('vat_rate', 7.5))),
                    payment_status=invoice.get('payment_status', 'pending'),
                    payment_method=invoice.get('payment_method'),
                    confidence=98.5,  # High confidence for ERP data
                    raw_data=invoice
                )
                transactions.append(transaction)

        except Exception as e:
            logger.error(f"Failed to aggregate SAP data: {e}")

        # Odoo ERP Data
        try:
            odoo_connector = self.connectors[DataSourceType.ERP]['odoo']
            if odoo_connector is not None:
                odoo_invoices = await odoo_connector.get_invoices_by_date_range(
                    organization_id, date_range[0], date_range[1]
                )
            else:
                logger.debug("Odoo connector not available, skipping Odoo data aggregation")
                odoo_invoices = []
            
            for invoice in odoo_invoices:
                transaction = BusinessTransactionData(
                    id=f"odoo-{invoice['id']}",
                    source_type=DataSourceType.ERP,
                    source_id="odoo",
                    transaction_id=invoice['name'],
                    date=invoice['invoice_date'],
                    customer_name=invoice['partner_id']['name'],
                    customer_email=invoice['partner_id'].get('email'),
                    customer_tin=invoice['partner_id'].get('vat'),
                    amount=Decimal(str(invoice['amount_total'])),
                    currency=invoice.get('currency_id', {}).get('name', 'NGN'),
                    description=invoice.get('name', 'Odoo Invoice'),
                    line_items=invoice['invoice_line_ids'],
                    tax_amount=Decimal(str(invoice['amount_tax'])),
                    vat_rate=Decimal('7.5'),
                    payment_status=invoice.get('payment_state', 'not_paid'),
                    payment_method=None,
                    confidence=96.8,
                    raw_data=invoice
                )
                transactions.append(transaction)

        except Exception as e:
            logger.error(f"Failed to aggregate Odoo data: {e}")

        # Odoo ERP Data via unified connector (org-scoped)
        try:
            odoo_conn = await self._get_odoo_unified(organization_id)
            if odoo_conn is not None:
                odoo_invoices = await odoo_conn.get_invoices_by_date_range(date_range[0], date_range[1])
            else:
                odoo_invoices = []
            for inv in odoo_invoices:
                inv_date = inv.get('invoice_date')
                if isinstance(inv_date, str):
                    try:
                        inv_dt = datetime.fromisoformat(inv_date)
                    except Exception:
                        inv_dt = datetime.utcnow()
                else:
                    inv_dt = inv_date or datetime.utcnow()
                transaction = BusinessTransactionData(
                    id=f"odoo-{inv['id']}",
                    source_type=DataSourceType.ERP,
                    source_id="odoo",
                    transaction_id=inv.get('invoice_number') or inv.get('name') or str(inv['id']),
                    date=inv_dt,
                    customer_name=(inv.get('customer') or {}).get('name') or "Customer",
                    customer_email=None,
                    customer_tin=None,
                    amount=Decimal(str(inv.get('total_amount') or 0)),
                    currency=inv.get('currency', 'NGN'),
                    description=inv.get('description') or 'Odoo Invoice',
                    line_items=inv.get('line_items') or [],
                    tax_amount=Decimal(str(inv.get('tax_amount') or 0)),
                    vat_rate=Decimal('7.5'),
                    payment_status=inv.get('payment_status') or 'posted',
                    payment_method=None,
                    confidence=96.0,
                    raw_data=inv
                )
                transactions.append(transaction)
        except Exception as e:
            logger.error(f"Failed to aggregate Odoo ERP data: {e}")

        return transactions

    async def _aggregate_crm_data(
        self,
        organization_id: UUID,
        date_range: Tuple[datetime, datetime]
    ) -> List[BusinessTransactionData]:
        """Aggregate data from CRM systems (Salesforce, HubSpot, etc.)."""
        transactions = []

        # Salesforce CRM Data
        try:
            sf_connector = self.connectors[DataSourceType.CRM]['salesforce']
            if sf_connector is not None:
                sf_deals = await sf_connector.get_closed_deals_by_date_range(
                    organization_id, date_range[0], date_range[1]
                )
            else:
                logger.debug("Salesforce connector not available, skipping Salesforce data aggregation")
                sf_deals = []
            
            for deal in sf_deals:
                if deal.get('amount') and deal.get('stage') == 'Closed Won':
                    transaction = BusinessTransactionData(
                        id=f"sf-{deal['id']}",
                        source_type=DataSourceType.CRM,
                        source_id="salesforce",
                        transaction_id=deal['name'],
                        date=deal['close_date'],
                        customer_name=deal['account']['name'],
                        customer_email=deal.get('contact', {}).get('email'),
                        customer_tin=deal.get('account', {}).get('tax_id'),
                        amount=Decimal(str(deal['amount'])),
                        currency='NGN',
                        description=deal['description'] or deal['name'],
                        line_items=[{
                            'description': deal['name'],
                            'quantity': 1,
                            'unit_price': float(deal['amount']),
                            'total': float(deal['amount']),
                            'tax_rate': 7.5,
                            'tax_amount': float(deal['amount']) * 0.075
                        }],
                        tax_amount=Decimal(str(deal['amount'])) * Decimal('0.075'),
                        vat_rate=Decimal('7.5'),
                        payment_status='pending',
                        payment_method=None,
                        confidence=94.2,
                        raw_data=deal
                    )
                    transactions.append(transaction)

        except Exception as e:
            logger.error(f"Failed to aggregate Salesforce data: {e}")

        # Odoo CRM Data via unified connector (org-scoped)
        try:
            odoo_conn = await self._get_odoo_unified(organization_id)
            if odoo_conn is not None:
                odoo_opps = await odoo_conn.get_opportunities_by_date_range(date_range[0], date_range[1])
            else:
                odoo_opps = []
            for deal in odoo_opps:
                close_date = deal.get('close_date')
                if isinstance(close_date, str):
                    try:
                        crm_dt = datetime.fromisoformat(close_date)
                    except Exception:
                        crm_dt = datetime.utcnow()
                else:
                    crm_dt = close_date or datetime.utcnow()
                transaction = BusinessTransactionData(
                    id=f"odoo-crm-{deal['id']}",
                    source_type=DataSourceType.CRM,
                    source_id="odoo",
                    transaction_id=deal.get('name') or str(deal['id']),
                    date=crm_dt,
                    customer_name=(deal.get('account') or {}).get('name') or "CRM Customer",
                    customer_email=None,
                    customer_tin=None,
                    amount=Decimal(str(deal.get('amount') or 0)),
                    currency='NGN',
                    description=deal.get('name') or 'CRM Opportunity',
                    line_items=[{
                        'description': deal.get('name'),
                        'quantity': 1,
                        'unit_price': float(deal.get('amount') or 0),
                        'total': float(deal.get('amount') or 0),
                        'tax_rate': 7.5,
                        'tax_amount': float(deal.get('amount') or 0) * 0.075
                    }],
                    tax_amount=Decimal(str(deal.get('amount') or 0)) * Decimal('0.075'),
                    vat_rate=Decimal('7.5'),
                    payment_status='pending',
                    payment_method=None,
                    confidence=93.0,
                    raw_data=deal
                )
                transactions.append(transaction)
        except Exception as e:
            logger.error(f"Failed to aggregate Odoo CRM data: {e}")

        return transactions

    async def _aggregate_pos_data(
        self,
        organization_id: UUID,
        date_range: Tuple[datetime, datetime]
    ) -> List[BusinessTransactionData]:
        """Aggregate data from POS systems (Odoo POS via unified connector)."""
        transactions = []


        # Odoo POS Data via unified connector (org-scoped)
        try:
            odoo_conn = await self._get_odoo_unified(organization_id)
            if odoo_conn is not None:
                odoo_pos = await odoo_conn.get_pos_orders_by_date_range(date_range[0], date_range[1])
            else:
                odoo_pos = []
            for order in odoo_pos:
                pos_date = order.get('date_order')
                if isinstance(pos_date, str):
                    try:
                        pos_dt = datetime.fromisoformat(pos_date.replace('Z', '+00:00'))
                    except Exception:
                        pos_dt = datetime.utcnow()
                else:
                    pos_dt = pos_date or datetime.utcnow()
                transaction = BusinessTransactionData(
                    id=f"odoo-pos-{order['id']}",
                    source_type=DataSourceType.POS,
                    source_id="odoo_pos",
                    transaction_id=order.get('transaction_id') or str(order['id']),
                    date=pos_dt,
                    customer_name=order.get('customer_name') or 'POS Customer',
                    customer_email=None,
                    customer_tin=None,
                    amount=Decimal(str(order.get('amount') or 0)),
                    currency=order.get('currency', 'NGN'),
                    description=order.get('name') or 'POS Order',
                    line_items=[],
                    tax_amount=Decimal(str(order.get('tax_amount') or 0)),
                    vat_rate=Decimal('7.5'),
                    payment_status=order.get('payment_status') or 'paid',
                    payment_method=order.get('payment_method') or 'POS',
                    confidence=95.0,
                    raw_data=order
                )
                transactions.append(transaction)
        except Exception as e:
            logger.error(f"Failed to aggregate Odoo POS data: {e}")

        return transactions

    async def _aggregate_ecommerce_data(
        self,
        organization_id: UUID,
        date_range: Tuple[datetime, datetime]
    ) -> List[BusinessTransactionData]:
        """Aggregate data from E-commerce systems (Odoo website/e‑commerce via unified connector)."""
        transactions = []


        # Odoo eCommerce Data via unified connector (org-scoped)
        try:
            odoo_conn = await self._get_odoo_unified(organization_id)
            if odoo_conn is not None:
                odoo_so = await odoo_conn.get_online_orders_by_date_range(date_range[0], date_range[1])
            else:
                odoo_so = []
            for order in odoo_so:
                so_date = order.get('date_order')
                if isinstance(so_date, str):
                    try:
                        so_dt = datetime.fromisoformat(so_date.replace('Z', '+00:00'))
                    except Exception:
                        so_dt = datetime.utcnow()
                else:
                    so_dt = so_date or datetime.utcnow()
                transaction = BusinessTransactionData(
                    id=f"odoo-ecom-{order['id']}",
                    source_type=DataSourceType.ECOMMERCE,
                    source_id="odoo_ecommerce",
                    transaction_id=order.get('transaction_id') or str(order['id']),
                    date=so_dt,
                    customer_name=order.get('customer_name') or 'Online Customer',
                    customer_email=None,
                    customer_tin=None,
                    amount=Decimal(str(order.get('amount') or 0)),
                    currency=order.get('currency', 'NGN'),
                    description=order.get('name') or 'Online Order',
                    line_items=[],
                    tax_amount=Decimal(str(order.get('tax_amount') or 0)),
                    vat_rate=Decimal('7.5'),
                    payment_status=order.get('payment_status') or 'paid',
                    payment_method=order.get('payment_method') or 'Online',
                    confidence=95.0,
                    raw_data=order
                )
                transactions.append(transaction)
        except Exception as e:
            logger.error(f"Failed to aggregate Odoo eCommerce data: {e}")

        return transactions

    async def _aggregate_banking_data(
        self,
        organization_id: UUID,
        date_range: Tuple[datetime, datetime]
    ) -> List[BusinessTransactionData]:
        """Aggregate data from Banking systems (Mono Open Banking, etc.)."""
        transactions = []

        # Mono Banking Data
        try:
            mono_connector = self.connectors[DataSourceType.BANKING]['mono']
            if mono_connector is not None:
                mono_transactions = await mono_connector.get_transactions_by_date_range(
                    organization_id, date_range[0], date_range[1]
                )
            else:
                logger.debug("Mono connector not available, skipping Mono banking data aggregation")
                mono_transactions = []
            
            for txn in mono_transactions:
                if txn.get('type') == 'credit' and txn.get('amount', 0) > 0:
                    transaction = BusinessTransactionData(
                        id=f"mono-{txn['_id']}",
                        source_type=DataSourceType.BANKING,
                        source_id="mono",
                        transaction_id=txn['_id'],
                        date=txn['date'],
                        customer_name=txn.get('narration', 'Bank Transfer Customer'),
                        customer_email=None,
                        customer_tin=None,
                        amount=Decimal(str(txn['amount'])),
                        currency='NGN',
                        description=txn.get('narration', 'Bank Transfer Payment'),
                        line_items=[{
                            'description': txn.get('narration', 'Service Payment'),
                            'quantity': 1,
                            'unit_price': float(txn['amount']) / 1.075,  # Remove VAT to get base
                            'total': float(txn['amount']) / 1.075,
                            'tax_rate': 7.5,
                            'tax_amount': float(txn['amount']) * 0.075 / 1.075
                        }],
                        tax_amount=Decimal(str(txn['amount'])) * Decimal('0.075') / Decimal('1.075'),
                        vat_rate=Decimal('7.5'),
                        payment_status='paid',
                        payment_method='Bank Transfer',
                        confidence=87.3,  # Lower confidence for banking transactions
                        raw_data=txn
                    )
                    transactions.append(transaction)

        except Exception as e:
            logger.error(f"Failed to aggregate Mono banking data: {e}")

        return transactions

    async def _aggregate_payment_data(
        self,
        organization_id: UUID,
        date_range: Tuple[datetime, datetime]
    ) -> List[BusinessTransactionData]:
        """Aggregate data from Payment processors (Paystack, Flutterwave, etc.)."""
        transactions = []

        # Paystack Payment Data
        try:
            paystack_connector = self.connectors[DataSourceType.PAYMENT]['paystack']
            if paystack_connector is not None:
                paystack_transactions = await paystack_connector.get_successful_transactions_by_date_range(
                    organization_id, date_range[0], date_range[1]
                )
            else:
                logger.debug("Paystack connector not available, skipping Paystack data aggregation")
                paystack_transactions = []
            
            for txn in paystack_transactions:
                if txn.get('status') == 'success':
                    transaction = BusinessTransactionData(
                        id=f"paystack-{txn['id']}",
                        source_type=DataSourceType.PAYMENT,
                        source_id="paystack",
                        transaction_id=txn['reference'],
                        date=txn['created_at'],
                        customer_name=txn['customer']['email'],  # Use email as name
                        customer_email=txn['customer']['email'],
                        customer_tin=None,
                        amount=Decimal(str(txn['amount'])) / 100,  # Paystack uses kobo
                        currency=txn['currency'],
                        description=txn.get('metadata', {}).get('description', 'Online Payment'),
                        line_items=[{
                            'description': 'Payment Processor Transaction',
                            'quantity': 1,
                            'unit_price': float(txn['amount']) / 100 / 1.075,
                            'total': float(txn['amount']) / 100 / 1.075,
                            'tax_rate': 7.5,
                            'tax_amount': float(txn['amount']) / 100 * 0.075 / 1.075
                        }],
                        tax_amount=Decimal(str(txn['amount'])) / 100 * Decimal('0.075') / Decimal('1.075'),
                        vat_rate=Decimal('7.5'),
                        payment_status='paid',
                        payment_method='Paystack',
                        confidence=92.5,
                        raw_data=txn
                    )
                    transactions.append(transaction)

        except Exception as e:
            logger.error(f"Failed to aggregate Paystack data: {e}")

        return transactions

    async def _cross_reference_transactions(
        self,
        transactions: List[BusinessTransactionData]
    ) -> List[BusinessTransactionData]:
        """
        Cross-reference transactions from different sources to eliminate duplicates
        and improve data quality.
        """
        # Group transactions by amount and date for potential matching
        grouped_transactions = {}
        
        for txn in transactions:
            # Create a key based on amount and date (within same day)
            key = (
                txn.amount,
                txn.date.date(),
                txn.customer_name.lower().strip() if txn.customer_name else ""
            )
            
            if key not in grouped_transactions:
                grouped_transactions[key] = []
            grouped_transactions[key].append(txn)

        reconciled = []
        
        for group in grouped_transactions.values():
            if len(group) == 1:
                # Single transaction, no duplicates
                reconciled.append(group[0])
            else:
                # Multiple transactions with same amount/date - choose best quality
                best_transaction = max(group, key=lambda t: t.confidence)
                
                # Merge data from other sources if beneficial
                for other_txn in group:
                    if other_txn != best_transaction:
                        # Add payment confirmation if available
                        if (other_txn.source_type in [DataSourceType.BANKING, DataSourceType.PAYMENT] 
                            and other_txn.payment_status == 'paid'):
                            best_transaction.payment_status = 'paid'
                            best_transaction.payment_method = other_txn.payment_method
                            # Increase confidence due to payment confirmation
                            best_transaction.confidence = min(99.9, best_transaction.confidence + 5.0)

                reconciled.append(best_transaction)

        logger.info(f"Cross-referenced {len(transactions)} transactions into {len(reconciled)} reconciled transactions")
        return reconciled

    def _map_connector_type(self, txn: BusinessTransactionData):
        """Map BusinessTransactionData to universal ConnectorType."""
        if not ConnectorType:
            raise RuntimeError("Universal processor not available")
        s = (txn.source_type.value or "").lower()
        sid = (txn.source_id or "").lower()
        if s == "erp":
            if "odoo" in sid:
                return ConnectorType.ERP_ODOO
            if "sap" in sid:
                return ConnectorType.ERP_SAP
            return ConnectorType.ERP_ODOO
        if s == "crm":
            if "odoo" in sid:
                return ConnectorType.CRM_ODOO
            # Default to Odoo CRM profile in Nigerian deployments
            return ConnectorType.CRM_ODOO
        if s == "pos":
            if "odoo" in sid:
                return ConnectorType.POS_ODOO
            return ConnectorType.POS_ECOMMERCE
        if s == "ecommerce":
            if "odoo" in sid:
                return ConnectorType.ECOMMERCE_ODOO
            # Default to Odoo e‑commerce profile in Nigerian deployments
            return ConnectorType.ECOMMERCE_ODOO
        if s == "banking":
            return ConnectorType.BANKING_OPEN_BANKING
        if s == "payment":
            if "paystack" in sid:
                return ConnectorType.PAYMENT_PAYSTACK
            return ConnectorType.PAYMENT_FLUTTERWAVE
        return ConnectorType.ERP_ODOO

    def _to_universal_txn(self, txn: BusinessTransactionData):
        """Convert BusinessTransactionData to UniversalTransaction."""
        if not UniversalTransaction:
            raise RuntimeError("Universal processor not available")
        meta_kwargs = {
            'erp_metadata': {},
            'crm_metadata': {},
            'pos_metadata': {},
            'ecommerce_metadata': {},
            'banking_metadata': {},
        }
        bucket = txn.source_type.value
        if bucket == 'erp':
            meta_kwargs['erp_metadata'] = {'transaction_id': txn.transaction_id}
        elif bucket == 'crm':
            meta_kwargs['crm_metadata'] = {'transaction_id': txn.transaction_id}
        elif bucket == 'pos':
            meta_kwargs['pos_metadata'] = {'transaction_id': txn.transaction_id}
        elif bucket == 'ecommerce':
            meta_kwargs['ecommerce_metadata'] = {'transaction_id': txn.transaction_id}
        elif bucket == 'banking':
            meta_kwargs['banking_metadata'] = {'transaction_id': txn.transaction_id}

        return UniversalTransaction(
            id=txn.id,
            amount=float(txn.amount),
            currency=txn.currency or 'NGN',
            date=txn.date,
            description=txn.description or (txn.source_id or 'Transaction'),
            account_number=txn.customer_tin or None,
            reference=txn.transaction_id,
            category=bucket,
            source_system=bucket,
            source_connector=txn.source_id or 'unknown',
            raw_data=txn.raw_data or {},
            **meta_kwargs
        )

    async def generate_firs_invoices(
        self,
        request: FIRSInvoiceGenerationRequest
    ) -> FIRSInvoiceGenerationResult:
        """
        Generate FIRS-compliant invoices from aggregated business data.
        
        Args:
            request: Invoice generation request
            
        Returns:
            Invoice generation result
        """
        logger.info(f"Generating FIRS invoices for {len(request.transaction_ids)} transactions")

        try:
            # Get aggregated transaction data
            all_transactions = await self.aggregate_business_data(request.organization_id)
            
            # Filter for requested transactions
            selected_transactions = [
                txn for txn in all_transactions 
                if txn.id in request.transaction_ids
            ]

            if not selected_transactions:
                return FIRSInvoiceGenerationResult(
                    success=False,
                    invoices=[],
                    errors=["No transactions found for the provided IDs"],
                    warnings=[],
                    total_amount=Decimal('0'),
                    irns_generated=[]
                )

            # Optional: route through universal processing pipeline (feature-flagged)
            use_universal = str(os.getenv("USE_UNIVERSAL_PROCESSOR", "false")).lower() in ("1", "true", "yes", "on")
            if use_universal and UniversalTransaction and ConnectorType and (get_transaction_processing_service or initialize_transaction_processing_service):
                try:
                    svc = get_transaction_processing_service() if get_transaction_processing_service else None  # type: ignore
                    if svc is None and initialize_transaction_processing_service:
                        svc = initialize_transaction_processing_service()  # type: ignore
                    if svc and hasattr(svc, "process_mixed_batch"):
                        mixed = []
                        for t in selected_transactions:
                            try:
                                mixed.append((self._to_universal_txn(t), self._map_connector_type(t)))
                            except Exception as e:
                                logger.debug(f"Universal mapping skipped for {t.id}: {e}")
                        if mixed:
                            results = await svc.process_mixed_batch(mixed)  # type: ignore[attr-defined]
                            allowed_ids = set()
                            for r in (results or []):
                                try:
                                    if r.success and r.processed_transaction and (
                                        r.processed_transaction.status == ProcessingStatus.READY_FOR_INVOICE
                                        or r.processed_transaction.processing_metadata.validation_passed
                                    ):
                                        allowed_ids.add(r.transaction_id)
                                except Exception:
                                    continue
                            if allowed_ids:
                                before = len(selected_transactions)
                                selected_transactions = [t for t in selected_transactions if t.id in allowed_ids]
                                logger.info(f"Universal processing filtered {before} → {len(selected_transactions)} transactions ready for invoice")
                except Exception as e:
                    logger.warning(f"Universal processor path skipped due to error: {e}")

            invoices = []
            irns_generated = []
            errors = []
            warnings = []
            total_amount = Decimal('0')

            if request.consolidate and len(selected_transactions) > 1:
                # Generate single consolidated invoice
                invoice_result = await self._generate_consolidated_invoice(
                    selected_transactions, request
                )
                invoices.append(invoice_result)
                warnings.extend(invoice_result.get('warnings', []))
                captured_irn = invoice_result.get('irn')
                if captured_irn:
                    irns_generated.append(captured_irn)
                total_amount += Decimal(str(invoice_result['total_amount']))
            else:
                # Generate individual invoices
                for transaction in selected_transactions:
                    try:
                        invoice_result = await self._generate_individual_invoice(
                            transaction, request
                        )
                        invoices.append(invoice_result)
                        warnings.extend(invoice_result.get('warnings', []))
                        captured_irn = invoice_result.get('irn')
                        if captured_irn:
                            irns_generated.append(captured_irn)
                        total_amount += Decimal(str(invoice_result['total_amount']))
                    except Exception as e:
                        error_msg = f"Failed to generate invoice for transaction {transaction.id}: {e}"
                        errors.append(error_msg)
                        logger.error(error_msg)

            # Update statistics
            self.stats['transactions_processed'] += len(selected_transactions)
            self.stats['invoices_generated'] += len(invoices)
            self.stats['total_amount_processed'] += total_amount
            if errors:
                self.stats['errors_encountered'] += len(errors)

            return FIRSInvoiceGenerationResult(
                success=len(invoices) > 0,
                invoices=invoices,
                errors=errors,
                warnings=warnings,
                total_amount=total_amount,
                irns_generated=irns_generated
            )

        except Exception as e:
            error_msg = f"Failed to generate FIRS invoices: {e}"
            logger.error(error_msg)
            return FIRSInvoiceGenerationResult(
                success=False,
                invoices=[],
                errors=[error_msg],
                warnings=[],
                total_amount=Decimal('0'),
                irns_generated=[]
            )

    async def _generate_individual_invoice(
        self,
        transaction: BusinessTransactionData,
        request: FIRSInvoiceGenerationRequest
    ) -> Dict[str, Any]:
        """Generate individual FIRS invoice from transaction data."""
        
        # Generate IRN (Invoice Reference Number)
        irn = await self._generate_irn(transaction, request.organization_id)
        
        # Create FIRS-compliant invoice data
        invoice_data = {
            'invoice_number': f"TXP-{transaction.transaction_id}",
            'invoice_date': transaction.date.isoformat(),
            'due_date': (transaction.date + timedelta(days=30)).isoformat(),
            'customer': {
                'name': transaction.customer_name,
                'email': transaction.customer_email,
                'tin': transaction.customer_tin
            },
            'line_items': transaction.line_items,
            'subtotal': float(transaction.amount - transaction.tax_amount),
            'tax_amount': float(transaction.tax_amount),
            'total_amount': float(transaction.amount),
            'currency': transaction.currency,
            'payment_status': transaction.payment_status,
            'source_data': {
                'source_type': transaction.source_type.value,
                'source_id': transaction.source_id,
                'transaction_id': transaction.transaction_id,
                'confidence': transaction.confidence
            }
        }

        if irn:
            invoice_data['irn'] = irn

        organization = await self._get_organization_profile(request.organization_id)
        (
            ubl_invoice,
            firs_invoice,
            signature_info,
            is_valid,
            validation_errors,
            pipeline_warnings,
            transformation_summary,
        ) = await self._process_invoice_pipeline(
            invoice_data,
            organization,
            request.include_digital_signature,
            {"transaction": transaction},
        )

        pipeline_invoice = transformation_summary.get("invoice_payload") if transformation_summary else None
        response_payload = copy.deepcopy(pipeline_invoice) if pipeline_invoice else dict(invoice_data)
        response_payload.update(
            {
                'ubl_document': ubl_invoice,
                'firs_document': firs_invoice,
                'signature': signature_info,
                'validation_errors': validation_errors,
                'warnings': pipeline_warnings,
                'validation_status': 'valid' if is_valid else 'invalid',
            }
        )

        if transformation_summary:
            response_payload['transformation_pipeline'] = {
                'success': transformation_summary.get('success'),
                'erp_system': transformation_summary.get('erp_system'),
                'warnings': transformation_summary.get('warnings', []),
                'errors': transformation_summary.get('errors', []),
                'metadata': transformation_summary.get('metadata'),
                'processing_time': transformation_summary.get('processing_time'),
            }

        qr_signature = self._generate_qr_signature_metadata(
            irn,
            invoice_data,
            invoice_data.get('verification_code', ''),
        )

        if qr_signature:
            invoice_data.setdefault('qr_signature', {
                'qr_string': qr_signature.qr_string,
                'encrypted_payload': qr_signature.encrypted_payload,
                'encryption_metadata': qr_signature.encryption_metadata,
            })
            invoice_data['qr_signature']['qr_data'] = qr_signature.qr_data
            invoice_data['verification_code'] = qr_signature.qr_data.get('verification_code', '')

        qr_signature = self._generate_qr_signature_metadata(
            irn,
            invoice_data,
            invoice_data.get('verification_code', ''),
        )

        if qr_signature:
            invoice_data.setdefault('qr_signature', {
                'qr_string': qr_signature.qr_string,
                'encrypted_payload': qr_signature.encrypted_payload,
                'encryption_metadata': qr_signature.encryption_metadata,
            })
            invoice_data['qr_signature']['qr_data'] = qr_signature.qr_data
            invoice_data['verification_code'] = qr_signature.qr_data.get('verification_code', '')

        submission_payload = {
            'source_invoice': invoice_data,
            'ubl_document': ubl_invoice,
            'firs_document': firs_invoice,
            'signature': signature_info,
            'transformation_pipeline': response_payload.get('transformation_pipeline'),
        }

        if qr_signature:
            submission_payload['pre_submission_signature'] = {
                'encrypted_payload': qr_signature.encrypted_payload,
                'encryption_metadata': qr_signature.encryption_metadata,
                'qr_data': qr_signature.qr_data,
            }

        if qr_signature:
            submission_payload['pre_submission_signature'] = {
                'encrypted_payload': qr_signature.encrypted_payload,
                'encryption_metadata': qr_signature.encryption_metadata,
                'qr_data': qr_signature.qr_data,
            }

        validation_status = ValidationStatus.VALID if is_valid else ValidationStatus.INVALID

        # Save to database
        firs_submission = FIRSSubmission(
            organization_id=request.organization_id,
            invoice_number=invoice_data['invoice_number'],
            irn=irn,
            status=SubmissionStatus.PENDING,
            validation_status=validation_status,
            invoice_data=submission_payload,
            original_data=transaction.raw_data,
            total_amount=transaction.amount,
            currency=transaction.currency,
            customer_name=transaction.customer_name,
            customer_email=transaction.customer_email,
            customer_tin=transaction.customer_tin
        )

        firs_submission.subtotal = Decimal(str(invoice_data['subtotal']))
        firs_submission.tax_amount = Decimal(str(invoice_data['tax_amount']))

        if not is_valid:
            firs_submission.error_details = {'validation_errors': validation_errors}

        self.db.add(firs_submission)
        await self.db.commit()

        # Create SI-APP correlation for status tracking
        if irn and is_valid:
            try:
                await self.correlation_service.create_correlation(
                    organization_id=request.organization_id,
                    si_invoice_id=invoice_data['invoice_number'],
                    si_transaction_ids=[transaction.id],
                    irn=irn,
                    invoice_number=invoice_data['invoice_number'],
                    total_amount=float(transaction.amount),
                    currency=transaction.currency,
                    customer_name=transaction.customer_name,
                    customer_email=transaction.customer_email,
                    customer_tin=transaction.customer_tin,
                    invoice_data=response_payload
                )
                logger.info(f"Created SI-APP correlation for IRN {irn}")
            except Exception as e:
                logger.warning(f"Failed to create SI-APP correlation for IRN {irn}: {e}")
                # Don't fail the invoice generation if correlation creation fails

        if not is_valid:
            detail = (
                validation_errors[0].get('message')
                if validation_errors and isinstance(validation_errors[0], dict)
                else validation_errors[0]
                if validation_errors
                else "Unknown validation error"
            )
            raise ValueError(f"UBL validation failed: {detail}")

        return response_payload

    async def _generate_consolidated_invoice(
        self,
        transactions: List[BusinessTransactionData],
        request: FIRSInvoiceGenerationRequest
    ) -> Dict[str, Any]:
        """Generate consolidated FIRS invoice from multiple transactions."""
        
        # Use first transaction for customer details (can be overridden)
        primary_transaction = transactions[0]
        
        # Generate IRN for consolidated invoice
        irn = await self._generate_irn(primary_transaction, request.organization_id, is_consolidated=True)
        
        # Aggregate all line items
        all_line_items = []
        total_amount = Decimal('0')
        total_tax = Decimal('0')
        
        for txn in transactions:
            all_line_items.extend(txn.line_items)
            total_amount += txn.amount
            total_tax += txn.tax_amount

        subtotal = total_amount - total_tax

        # Create consolidated invoice data
        invoice_data = {
            'invoice_number': f"TXP-CONSOLIDATED-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            'invoice_date': datetime.utcnow().isoformat(),
            'due_date': (datetime.utcnow() + timedelta(days=30)).isoformat(),
            'customer': {
                'name': request.customer_overrides.get('customer_name', primary_transaction.customer_name) if request.customer_overrides else primary_transaction.customer_name,
                'email': request.customer_overrides.get('customer_email', primary_transaction.customer_email) if request.customer_overrides else primary_transaction.customer_email,
                'tin': primary_transaction.customer_tin
            },
            'line_items': all_line_items,
            'subtotal': float(total_amount - total_tax),
            'tax_amount': float(total_tax),
            'total_amount': float(total_amount),
            'currency': primary_transaction.currency,
            'consolidated_from': [txn.id for txn in transactions],
            'source_data': {
                'consolidation': True,
                'transaction_count': len(transactions),
                'source_types': list(set(txn.source_type.value for txn in transactions)),
                'average_confidence': sum(txn.confidence for txn in transactions) / len(transactions)
            }
        }

        if irn:
            invoice_data['irn'] = irn

        organization = await self._get_organization_profile(request.organization_id)
        (
            ubl_invoice,
            firs_invoice,
            signature_info,
            is_valid,
            validation_errors,
            pipeline_warnings,
            transformation_summary,
        ) = await self._process_invoice_pipeline(
            invoice_data,
            organization,
            request.include_digital_signature,
            {"transactions": transactions},
        )

        pipeline_invoice = transformation_summary.get("invoice_payload") if transformation_summary else None
        response_payload = copy.deepcopy(pipeline_invoice) if pipeline_invoice else dict(invoice_data)
        response_payload.update(
            {
                'ubl_document': ubl_invoice,
                'firs_document': firs_invoice,
                'signature': signature_info,
                'validation_errors': validation_errors,
                'warnings': pipeline_warnings,
                'validation_status': 'valid' if is_valid else 'invalid',
            }
        )

        if transformation_summary:
            response_payload['transformation_pipeline'] = {
                'success': transformation_summary.get('success'),
                'erp_system': transformation_summary.get('erp_system'),
                'warnings': transformation_summary.get('warnings', []),
                'errors': transformation_summary.get('errors', []),
                'metadata': transformation_summary.get('metadata'),
                'processing_time': transformation_summary.get('processing_time'),
            }

        submission_payload = {
            'source_invoice': invoice_data,
            'ubl_document': ubl_invoice,
            'firs_document': firs_invoice,
            'signature': signature_info,
            'transformation_pipeline': response_payload.get('transformation_pipeline'),
        }

        validation_status = ValidationStatus.VALID if is_valid else ValidationStatus.INVALID

        # Save to database
        firs_submission = FIRSSubmission(
            organization_id=request.organization_id,
            invoice_number=invoice_data['invoice_number'],
            irn=irn,
            status=SubmissionStatus.PENDING,
            validation_status=validation_status,
            invoice_data=submission_payload,
            original_data={'consolidated_transactions': [txn.raw_data for txn in transactions]},
            total_amount=total_amount,
            currency=primary_transaction.currency,
            customer_name=invoice_data['customer']['name'],
            customer_email=invoice_data['customer']['email'],
            customer_tin=invoice_data['customer']['tin']
        )

        firs_submission.subtotal = subtotal
        firs_submission.tax_amount = total_tax

        if not is_valid:
            firs_submission.error_details = {'validation_errors': validation_errors}

        self.db.add(firs_submission)
        await self.db.commit()

        # Create SI-APP correlation for consolidated invoice
        if irn and is_valid:
            try:
                await self.correlation_service.create_correlation(
                    organization_id=request.organization_id,
                    si_invoice_id=invoice_data['invoice_number'],
                    si_transaction_ids=[txn.id for txn in transactions],
                    irn=irn,
                    invoice_number=invoice_data['invoice_number'],
                    total_amount=float(total_amount),
                    currency=primary_transaction.currency,
                    customer_name=invoice_data['customer']['name'],
                    customer_email=invoice_data['customer']['email'],
                    customer_tin=invoice_data['customer']['tin'],
                    invoice_data=response_payload
                )
                logger.info(f"Created SI-APP correlation for consolidated IRN {irn}")
            except Exception as e:
                logger.warning(f"Failed to create SI-APP correlation for consolidated IRN {irn}: {e}")
                # Don't fail the invoice generation if correlation creation fails

        if not is_valid:
            detail = (
                validation_errors[0].get('message')
                if validation_errors and isinstance(validation_errors[0], dict)
                else validation_errors[0]
                if validation_errors
                else "Unknown validation error"
            )
            raise ValueError(f"UBL validation failed: {detail}")

        return response_payload

    async def _generate_irn(
        self,
        transaction: BusinessTransactionData,
        organization_id: UUID,
        is_consolidated: bool = False
    ) -> Optional[str]:
        """Generate FIRS-compliant Invoice Reference Number (IRN)."""

        # Get organization-specific service ID
        from core_platform.data_management.models.organization import Organization
        org_result = await self.db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        organization = org_result.scalar_one_or_none()
        
        if organization:
            service_id = organization.get_firs_service_id()
            logger.debug(f"Using FIRS service ID '{service_id}' for organization {organization_id}")
        else:
            service_id = "94ND90NR"  # Fallback to default
            logger.warning(f"Organization {organization_id} not found, using default service ID")

        if not service_id:
            service_id = "94ND90NR"

        invoice_number = (
            (transaction.raw_data or {}).get("invoice_number")
            or (transaction.raw_data or {}).get("invoiceNumber")
            or transaction.transaction_id
            or "0001"
        )

        if is_consolidated:
            invoice_number = f"CONS-{datetime.utcnow().strftime('%H%M%S')}"

        issued_on = transaction.date if isinstance(transaction.date, datetime) else datetime.utcnow()

        try:
            return generate_canonical_irn(invoice_number, service_id, issued_on)
        except IRNGenerationError:
            fallback_invoice = transaction.transaction_id or "0001"
            return generate_canonical_irn(fallback_invoice, service_id or "94ND90NR", issued_on)

    def _generate_qr_signature_metadata(
        self,
        irn: Optional[str],
        invoice_data: Dict[str, Any],
        verification_code: str = "",
    ) -> Optional[QREncryptionResult]:
        if not irn or not self.qr_signing_service:
            return None
        try:
            return self.qr_signing_service.generate_signed_qr(
                irn=irn,
                verification_code=verification_code,
                invoice_data=invoice_data,
            )
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("QR signing failed for IRN %s: %s", irn, exc)
            return None

    async def get_generation_statistics(self) -> Dict[str, Any]:
        """Get invoice generation statistics."""
        return {
            'transactions_processed': self.stats['transactions_processed'],
            'invoices_generated': self.stats['invoices_generated'],
            'total_amount_processed': float(self.stats['total_amount_processed']),
            'errors_encountered': self.stats['errors_encountered'],
            'success_rate': (
                (self.stats['invoices_generated'] / max(1, self.stats['transactions_processed'])) * 100
            )
        }
