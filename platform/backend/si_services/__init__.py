"""
SI Services Initialization and Registration
==========================================

Initializes and registers all System Integrator services with the message router.
This ensures that SI services are properly connected to the platform messaging system.

Services Registered:
- Banking Integration Service
- Mono Integration Service
- ERP Integration Service
- Certificate Management Service
- Document Processing Service
- IRN/QR Generation Service
- Data Extraction Service
- Integration Management Service
- Authentication Service
- Subscription Management Service
"""

import base64
import logging
import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, Optional, List
from uuid import uuid4
from datetime import datetime, timezone
from urllib.parse import urlparse
from dataclasses import asdict
from enum import Enum

from pydantic import ValidationError

from core_platform.messaging.message_router import MessageRouter, ServiceRole

# Import SI services
from .banking_integration.banking_service import SIBankingService
from .banking_integration.mono_integration_service import MonoIntegrationService
from .onboarding_management.onboarding_service import SIOnboardingService
from .organization_management.organization_service import SIOrganizationService
from .payment_integration.payment_service import SIPaymentService
from .reconciliation_management.reconciliation_service import SIReconciliationService
from .validation_services.validation_service import SIValidationService
from .reporting_services.reporting_service import SIReportingService
from .integration_management.connection_manager import ConnectionConfig, SystemType, connection_manager
from .integration_management.connection_tester import connection_tester
from .integration_management import (
    SyncConfiguration,
    SyncDirection,
    register_sync_configuration,
    sync_orchestrator,
)
from .integration_management.erp_connection_repository import ERPConnectionRepository, ERPConnectionRecord
from .invoice_validation import InvoiceValidationService

logger = logging.getLogger(__name__)

# Ensure legacy app package is importable for shims still referencing it
_archive_backend = Path(__file__).resolve().parents[2] / "archive" / "legacy" / "backend"
if _archive_backend.exists():
    archive_path_str = str(_archive_backend)
    if archive_path_str not in sys.path:
        sys.path.append(archive_path_str)


class SIServiceRegistry:
    """
    Registry for all SI services that handles initialization and message router registration.
    """
    
    def __init__(
        self,
        message_router: MessageRouter,
        *,
        background_runner: Optional[Any] = None,
    ):
        """
        Initialize SI service registry.
        
        Args:
            message_router: Core platform message router
        """
        self.message_router = message_router
        self.services: Dict[str, Any] = {}
        self.service_endpoints: Dict[str, str] = {}
        self.is_initialized = False
        self.erp_connection_repository = ERPConnectionRepository()
        self.integration_health_monitor = None
        self.background_runner = background_runner

    def configure_background_runner(self, runner: Any) -> None:
        """Inject or update the background task runner."""
        self.background_runner = runner

    async def initialize_services(self) -> Dict[str, str]:
        """
        Initialize and register all SI services.
        
        Returns:
            Dict mapping service names to endpoint IDs
        """
        try:
            logger.info("Initializing SI services...")
            
            # Initialize all SI services
            await self._register_banking_services()
            await self._register_onboarding_services()
            await self._register_organization_services()
            await self._register_payment_services()
            await self._register_reconciliation_services()
            await self._register_validation_services()
            await self._register_erp_services()
            await self._register_odoo_business_services()
            await self._register_certificate_services()
            await self._register_document_services()
            await self._register_irn_services()
            await self._register_invoice_validation_services()
            await self._register_data_extraction_services()
            await self._register_integration_management_services()
            await self._register_authentication_services()
            await self._register_subscription_services()
            await self._register_reporting_services()
            
            self.is_initialized = True
            logger.info(f"SI services initialized successfully. Registered {len(self.service_endpoints)} services.")
            
            return self.service_endpoints
            
        except Exception as e:
            logger.error(f"Failed to initialize SI services: {str(e)}", exc_info=True)
            raise RuntimeError(f"SI service initialization failed: {str(e)}")
    
    async def _register_banking_services(self):
        """Register banking integration services"""
        try:
            # Initialize banking service
            banking_service = SIBankingService()
            self.services["banking"] = banking_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="banking_integration",
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                callback=self._create_banking_callback(banking_service),
                priority=5,
                tags=["banking", "mono", "open_banking", "financial"],
                metadata={
                    "service_type": "banking_integration",
                    "operations": [
                        "create_mono_widget_link",
                        "process_mono_callback",
                        "process_banking_callback",
                        "list_open_banking_connections",
                        "create_open_banking_connection",
                        "get_open_banking_connection",
                        "update_open_banking_connection",
                        "delete_open_banking_connection",
                        "get_banking_transactions",
                        "sync_banking_transactions",
                        "get_banking_accounts",
                        "get_account_balance",
                        "test_banking_connection",
                        "get_banking_connection_health",
                        "get_banking_statistics"
                    ],
                    "providers": ["mono", "stitch", "unified_banking"]
                }
            )
            
            self.service_endpoints["banking_integration"] = endpoint_id
            logger.info(f"Banking service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register banking services: {str(e)}")
            raise

    async def _register_organization_services(self):
        """Register organization management service (scaffold)"""
        try:
            org_service = SIOrganizationService()
            endpoint_id = await self.message_router.register_service(
                service_name="organization_management",
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                callback=self._create_org_callback(org_service),
                priority=4,
                tags=["organization", "compliance"],
                metadata={
                    "service_type": "organization_management",
                    "operations": [
                        "create_organization",
                        "get_organization",
                        "update_organization",
                        "delete_organization",
                        "get_organization_compliance",
                        "validate_organization_compliance",
                        "initiate_organization_onboarding",
                        "get_organization_onboarding_status",
                    ],
                },
            )
            self.service_endpoints["organization_management"] = endpoint_id
        except Exception as e:
            logger.error(f"Failed to register organization services: {str(e)}")

    def _create_org_callback(self, org_service: SIOrganizationService):
        from core_platform.data_management.db_async import get_async_session
        async def cb(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            async for db in get_async_session():
                return await org_service.handle_operation(operation, payload, db)
        return cb

    async def _register_payment_services(self):
        """Register payment processor integration service (scaffold)"""
        try:
            pay_service = SIPaymentService()
            endpoint_id = await self.message_router.register_service(
                service_name="payment_integration",
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                callback=self._create_payment_callback(pay_service),
                priority=4,
                tags=["payments", "processors"],
                metadata={
                    "service_type": "payment_integration",
                    "operations": [
                        "register_payment_webhooks",
                        "list_payment_webhooks",
                        "process_payment_transactions",
                        "bulk_import_payment_transactions",
                        "get_unified_payment_transactions",
                        "get_unified_payment_summary",
                        "get_payment_connections_summary",
                        "list_all_payment_connections",
                        "test_payment_connection",
                        "get_payment_connection_health",
                        "receive_payment_webhook",
                    ],
                },
            )
            self.service_endpoints["payment_integration"] = endpoint_id
        except Exception as e:
            logger.error(f"Failed to register payment services: {str(e)}")

    def _create_payment_callback(self, pay_service: SIPaymentService):
        from core_platform.data_management.db_async import get_async_session
        async def cb(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            async for db in get_async_session():
                return await pay_service.handle_operation(operation, payload, db)
        return cb

    async def _register_reconciliation_services(self):
        """Register reconciliation configuration service (scaffold)"""
        try:
            rec_service = SIReconciliationService()
            endpoint_id = await self.message_router.register_service(
                service_name="reconciliation_management",
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                callback=self._create_reconciliation_callback(rec_service),
                priority=4,
                tags=["reconciliation", "rules"],
                metadata={
                    "service_type": "reconciliation_management",
                    "operations": [
                        "save_reconciliation_configuration",
                        "get_reconciliation_configuration",
                        "update_reconciliation_configuration",
                        "list_transaction_categories",
                        "create_transaction_category",
                        "update_transaction_category",
                        "delete_transaction_category",
                        "test_pattern_matching",
                        "get_pattern_statistics",
                        "sync_with_transaction_processor",
                        "get_processor_integration_status",
                        "update_universal_processor_patterns",
                    ],
                },
            )
            self.service_endpoints["reconciliation_management"] = endpoint_id
        except Exception as e:
            logger.error(f"Failed to register reconciliation services: {str(e)}")

    def _create_reconciliation_callback(self, rec_service: SIReconciliationService):
        from core_platform.data_management.db_async import get_async_session
        async def cb(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            async for db in get_async_session():
                return await rec_service.handle_operation(operation, payload, db)
        return cb

    async def _register_validation_services(self):
        """Register validation services (scaffold)"""
        try:
            val_service = SIValidationService()
            endpoint_id = await self.message_router.register_service(
                service_name="validation_services",
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                callback=self._create_validation_callback(val_service),
                priority=4,
                tags=["validation", "bvn", "kyc", "identity"],
                metadata={
                    "service_type": "validation_services",
                    "operations": [
                        "validate_bvn",
                        "lookup_bvn",
                        "bulk_validate_bvn",
                        "bulk_lookup_bvn",
                        "get_bvn_validation_history",
                        "get_bvn_validation_status",
                        "process_kyc",
                        "process_bulk_kyc",
                        "verify_kyc_document",
                        "get_kyc_status",
                        "get_kyc_details",
                        "list_kyc_processes",
                        "check_kyc_compliance",
                        "verify_identity",
                        "verify_bulk_identity",
                        "validate_identity_document",
                        "verify_biometric",
                        "get_identity_verification_status",
                        "get_identity_verification_history",
                        "test_validation_service",
                        "get_validation_service_health",
                    ],
                },
            )
            self.service_endpoints["validation_services"] = endpoint_id
        except Exception as e:
            logger.error(f"Failed to register validation services: {str(e)}")

    def _create_validation_callback(self, val_service: SIValidationService):
        from core_platform.data_management.db_async import get_async_session
        async def cb(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            async for db in get_async_session():
                return await val_service.handle_operation(operation, payload, db)  # type: ignore[arg-type]
        return cb

    async def _register_reporting_services(self):
        """Register reporting services (scaffold)"""
        try:
            rep_service = SIReportingService()
            endpoint_id = await self.message_router.register_service(
                service_name="reporting_services",
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                callback=self._create_reporting_callback(rep_service),
                priority=3,
                tags=["reporting", "compliance", "onboarding"],
                metadata={
                    "service_type": "reporting_services",
                    "operations": [
                        "generate_onboarding_report",
                        "generate_transaction_compliance_report",
                        # Bridge ops used by SI endpoints that forward to APP
                        "receive_invoices_from_si",
                        "receive_invoice_batch_from_si",
                        # Read-only summaries used by POS endpoints
                        "get_transactions",
                        "get_sales_summary",
                    ],
                },
            )
            self.service_endpoints["reporting_services"] = endpoint_id
        except Exception as e:
            logger.error(f"Failed to register reporting services: {str(e)}")

    def _create_reporting_callback(self, rep_service: SIReportingService):
        from core_platform.data_management.db_async import get_async_session
        async def cb(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            async for db in get_async_session():
                return await rep_service.handle_operation(operation, payload, db)
        return cb
    
    async def _register_onboarding_services(self):
        """Register onboarding management services"""
        try:
            # Initialize onboarding service
            onboarding_service = SIOnboardingService()
            self.services["onboarding"] = onboarding_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="onboarding_management",
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                callback=self._create_onboarding_callback(onboarding_service),
                priority=4,
                tags=["onboarding", "state_management", "progress_tracking"],
                metadata={
                    "service_type": "onboarding_management",
                    "operations": [
                        "get_onboarding_state",
                        "update_onboarding_state",
                        "complete_onboarding_step",
                        "complete_onboarding",
                        "reset_onboarding_state",
                        "get_onboarding_analytics"
                    ],
                    "supported_roles": ["system_integrator", "access_point_provider", "hybrid_user"]
                }
            )
            
            self.service_endpoints["onboarding_management"] = endpoint_id
            logger.info(f"Onboarding service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register onboarding services: {str(e)}")
            raise
    
    def _create_banking_callback(self, banking_service: SIBankingService):
        """Create callback function for banking service operations"""
        async def banking_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            """Handle banking service operations"""
            try:
                logger.info(f"Processing banking operation: {operation}")
                result = await banking_service.handle_operation(operation, payload)
                
                logger.info(f"Banking operation completed: {operation}")
                return result
                
            except Exception as e:
                logger.error(f"Banking operation failed {operation}: {str(e)}", exc_info=True)
                return {
                    "operation": operation,
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
        
        return banking_callback
    
    def _create_onboarding_callback(self, onboarding_service: SIOnboardingService):
        """Create callback function for onboarding service operations"""
        async def onboarding_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            """Handle onboarding service operations"""
            try:
                logger.info(f"Processing onboarding operation: {operation}")
                result = await onboarding_service.handle_operation(operation, payload)
                return result
                
            except Exception as e:
                logger.error(f"Onboarding operation failed {operation}: {str(e)}", exc_info=True)
                return {
                    "operation": operation,
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
        
        return onboarding_callback
    
    async def _register_erp_services(self):
        """Register ERP integration services"""
        try:
            # Import ERP services
            try:
                from .erp_integration.erp_integration_service import test_odoo_connection  # type: ignore
                _test_connection_fn = test_odoo_connection
            except Exception as import_err:
                logger.warning(
                    "Falling back to stub Odoo connection tester due to import error: %s",
                    import_err,
                )

                class _StubIntegrationResult:
                    def __init__(self, success: bool, message: str, details: Optional[Dict[str, Any]] = None):
                        self.success = success
                        self.message = message
                        self.details = details or {}

                    def dict(self) -> Dict[str, Any]:
                        return {
                            "success": self.success,
                            "message": self.message,
                            "details": self.details,
                        }

                def _test_connection_fn(*args: Any, **kwargs: Any) -> _StubIntegrationResult:
                    return _StubIntegrationResult(
                        success=False,
                        message="odoo_connection_test_unavailable",
                        details={"error": str(import_err)},
                    )

            from .erp_integration.erp_data_processor import ERPDataProcessor, ProcessingConfig
            from .erp_integration.data_sync_coordinator import DataSyncCoordinator, CoordinatorConfig
            
            # Create ERP service wrapper
            try:
                data_processor = ERPDataProcessor(ProcessingConfig())
            except Exception as proc_err:
                logger.warning(f"ERP data processor unavailable, continuing without processor: {proc_err}")
                data_processor = None

            try:
                sync_coordinator = DataSyncCoordinator(CoordinatorConfig())
            except Exception as sync_err:
                logger.warning(f"ERP sync coordinator unavailable, continuing without coordinator: {sync_err}")
                sync_coordinator = None

            erp_service = {
                "connection_tester": _test_connection_fn,
                "data_processor": data_processor,
                "sync_coordinator": sync_coordinator
            }
            
            self.services["erp_integration"] = erp_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="erp_integration",
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                callback=self._create_erp_callback(erp_service),
                priority=5,
                tags=["erp", "odoo", "sap", "business_systems"],
                metadata={
                    "service_type": "erp_integration",
                    "operations": [
                        "test_erp_connection",
                        "extract_erp_data",
                        "sync_erp_data",
                        "get_erp_sync_status",
                        "process_erp_invoices",
                        "validate_erp_mapping",
                        # Bridge operations used by APP to fetch/transform invoices
                        "fetch_odoo_invoices_for_firs",
                        "fetch_odoo_invoice_batch_for_firs",
                    ],
                    "supported_erp": ["odoo", "sap", "oracle", "dynamics"]
                }
            )
            
            self.service_endpoints["erp_integration"] = endpoint_id
            logger.info(f"ERP integration service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register ERP services: {str(e)}")
            # Don't raise - continue with other services

    async def _register_odoo_business_services(self):
        """Register minimal Odoo CRM/POS/E‑commerce services (env-scoped)."""
        try:
            try:
                from external_integrations.business_systems.odoo.unified_connector import OdooUnifiedConnector
            except Exception:
                OdooUnifiedConnector = None  # type: ignore

            async def odoo_business_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
                try:
                    # Prefer direct Odoo services for CRM/POS
                    from .erp_integration.odoo_crm_pos_services import OdooCRMService, OdooPOSService
                    if operation == "get_crm_opportunities":
                        limit = int(payload.get("limit", 50))
                        offset = int(payload.get("offset", 0))
                        recs = await OdooCRMService.list_opportunities(limit=limit, offset=offset)
                        return {"operation": operation, "success": True, "data": recs}
                    if operation == "get_crm_opportunity":
                        oid = int(payload.get("opportunity_id"))
                        rec = await OdooCRMService.get_opportunity(oid)
                        return {"operation": operation, "success": rec is not None, "data": rec or {"error": "not_found"}}
                    if operation == "create_crm_opportunity":
                        data = payload.get("data", {})
                        created = await OdooCRMService.create_opportunity(data)
                        # Audit
                        try:
                            from si_services.utils.audit import record_audit_event
                            from core_platform.data_management.db_async import get_async_session
                            from core_platform.data_management.models import AuditEventType
                            async for db in get_async_session():
                                await record_audit_event(
                                    db,
                                    event_type=AuditEventType.INTEGRATION_CHANGE,
                                    description="crm_opportunity_created",
                                    target_type="crm.opportunity",
                                    target_id=str(created.get('id')),
                                    new_values=created,
                                    correlation_id=payload.get("correlation_id"),
                                )
                        except Exception:
                            pass
                        return {"operation": operation, "success": True, "data": created}
                    if operation == "update_crm_opportunity":
                        oid = int(payload.get("opportunity_id"))
                        updates = payload.get("updates", {})
                        updated = await OdooCRMService.update_opportunity(oid, updates)
                        try:
                            from si_services.utils.audit import record_audit_event
                            from core_platform.data_management.db_async import get_async_session
                            from core_platform.data_management.models import AuditEventType
                            async for db in get_async_session():
                                await record_audit_event(
                                    db,
                                    event_type=AuditEventType.INTEGRATION_CHANGE,
                                    description="crm_opportunity_updated",
                                    target_type="crm.opportunity",
                                    target_id=str(oid),
                                    new_values=updates,
                                    correlation_id=payload.get("correlation_id"),
                                )
                        except Exception:
                            pass
                        return {"operation": operation, "success": updated is not None, "data": updated or {"error": "not_found"}}
                    if operation == "get_pos_orders":
                        limit = int(payload.get("limit", 50))
                        offset = int(payload.get("offset", 0))
                        recs = await OdooPOSService.list_orders(limit=limit, offset=offset)
                        return {"operation": operation, "success": True, "data": recs}
                    if operation == "get_pos_order":
                        oid = int(payload.get("order_id"))
                        rec = await OdooPOSService.get_order(oid)
                        return {"operation": operation, "success": rec is not None, "data": rec or {"error": "not_found"}}
                    # Fallback unified connector for online orders if available
                    if operation == "get_online_orders" and OdooUnifiedConnector:
                        conn = OdooUnifiedConnector.from_env()
                        if conn and conn.available():
                            from datetime import datetime, timedelta
                            end = datetime.utcnow()
                            start = end - timedelta(days=int(payload.get("days", 30)))
                            recs = await conn.get_online_orders_by_date_range(start, end)
                            return {"operation": operation, "success": True, "data": recs}
                        return {"operation": operation, "success": False, "error": "odoo_connector_not_configured"}
                    return {"operation": operation, "success": False, "error": "unsupported_operation"}
                except Exception as e:
                    return {"operation": operation, "success": False, "error": str(e)}

            endpoint_id = await self.message_router.register_service(
                service_name="odoo_business",
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                callback=odoo_business_callback,
                priority=4,
                tags=["odoo", "crm", "pos", "ecommerce"],
                metadata={
                    "service_type": "odoo_business",
                    "operations": [
                        "get_crm_opportunities",
                        "get_crm_opportunity",
                        "create_crm_opportunity",
                        "update_crm_opportunity",
                        "get_pos_orders",
                        "get_pos_order",
                        "get_online_orders"
                    ]
                }
            )
            self.service_endpoints["odoo_business"] = endpoint_id
        except Exception as e:
            logger.error(f"Failed to register Odoo business services: {str(e)}")
    
    async def _register_certificate_services(self):
        """Register certificate management services"""
        try:
            from .certificate_management.certificate_service import CertificateService
            from .certificate_management.certificate_generator import CertificateGenerator
            from .certificate_management.key_manager import KeyManager
            
            # Create certificate service wrapper
            cert_service = {
                "certificate_service": "CertificateService",  # Requires DB session
                "generator": CertificateGenerator() if hasattr(CertificateGenerator, '__init__') else None,
                "key_manager": KeyManager() if hasattr(KeyManager, '__init__') else None
            }
            
            self.services["certificate_management"] = cert_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="certificate_management",
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                callback=self._create_certificate_callback(cert_service),
                priority=4,
                tags=["certificate", "pki", "security", "firs"],
                metadata={
                    "service_type": "certificate_management",
                    "operations": [
                        "generate_certificate",
                        "validate_certificate",
                        "revoke_certificate",
                        "renew_certificate",
                        "get_certificate_status",
                        "verify_signature",
                    ]
                }
            )

            self.service_endpoints["certificate_management"] = endpoint_id
            logger.info(f"Certificate management service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register certificate services: {str(e)}")
    
    async def _register_document_services(self):
        """Register document processing services"""
        try:
            from .document_processing.invoice_generator import InvoiceGenerator
            from .document_processing.pdf_generator import PDFGenerator
            from .document_processing.template_engine import TemplateEngine
            
            # Create document service wrapper
            doc_service = {
                "invoice_generator": InvoiceGenerator(),
                "pdf_generator": PDFGenerator() if hasattr(PDFGenerator, '__init__') else None,
                "template_engine": TemplateEngine() if hasattr(TemplateEngine, '__init__') else None
            }
            
            self.services["document_processing"] = doc_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="document_processing",
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                callback=self._create_document_callback(doc_service),
                priority=3,
                tags=["document", "invoice", "pdf", "template"],
                metadata={
                    "service_type": "document_processing",
                    "operations": [
                        "generate_invoice",
                        "generate_pdf",
                        "process_template",
                        "validate_document",
                        "convert_format"
                    ],
                    "supported_formats": ["ubl", "json", "xml", "pdf"],
                    "response_fields": {
                        "generate_invoice": {
                            "irn_signature": "Encrypted IRN payload packaged with metadata and optional qr_png_base64 when requested"
                        }
                    }
                }
            )
            
            self.service_endpoints["document_processing"] = endpoint_id
            logger.info(f"Document processing service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register document services: {str(e)}")
    
    async def _register_irn_services(self):
        """Register IRN/QR generation services"""
        try:
            from .irn_qr_generation.irn_generation_service import IRNGenerationService
            from .irn_qr_generation.irn_generator import IRNGenerator
            from .irn_qr_generation.qr_code_generator import QRCodeGenerator
            from .irn_qr_generation.qr_signing_service import QRSigningService
            
            # Create IRN service wrapper
            key_path_env = os.getenv("FIRS_CRYPTO_KEYS_PATH")
            inline_key_env = os.getenv("FIRS_CRYPTO_KEYS_B64")
            inline_public_key = None
            if inline_key_env:
                try:
                    inline_public_key = base64.b64decode(inline_key_env).decode("utf-8")
                except Exception as decode_err:
                    logger.warning(f"Failed to decode FIRS_CRYPTO_KEYS_B64: {decode_err}")

            irn_service = {
                "generation_service": IRNGenerationService(),
                "irn_generator": IRNGenerator() if hasattr(IRNGenerator, '__init__') else None,
                "qr_generator": QRCodeGenerator() if hasattr(QRCodeGenerator, '__init__') else None,
                "qr_signing_service": QRSigningService(
                    key_path=Path(key_path_env).expanduser() if key_path_env else None,
                    public_key_pem=inline_public_key,
                ),
            }
            
            self.services["irn_generation"] = irn_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="irn_generation",
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                callback=self._create_irn_callback(irn_service),
                priority=5,
                tags=["irn", "qr", "firs", "compliance"],
                metadata={
                    "service_type": "irn_generation",
                    "operations": [
                        "request_irn_from_firs",
                        "submit_irn_to_firs",
                        "generate_irn",
                    "generate_qr_code",
                    "sign_qr_payload",
                        "validate_irn",
                        "bulk_generate_irn",
                        "get_irn_status"
                    ]
                }
            )
            
            self.service_endpoints["irn_generation"] = endpoint_id
            logger.info(f"IRN generation service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register IRN services: {str(e)}")

    async def _register_invoice_validation_services(self):
        """Register invoice validation services"""
        try:
            validation_service = InvoiceValidationService()
            self.services["invoice_validation"] = validation_service

            endpoint_id = await self.message_router.register_service(
                service_name="invoice_validation",
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                callback=self._create_invoice_validation_callback(validation_service),
                priority=4,
                tags=["validation", "firs", "invoice", "qr"],
                metadata={
                    "service_type": "invoice_validation",
                    "operations": [
                        "validate_invoice_proxy",
                    ],
                },
            )

            self.service_endpoints["invoice_validation"] = endpoint_id
            logger.info(f"Invoice validation service registered: {endpoint_id}")

        except Exception as e:
            logger.error(f"Failed to register invoice validation services: {str(e)}")
    
    async def _register_data_extraction_services(self):
        """Register data extraction services"""
        try:
            from .data_extraction.erp_data_extractor import ERPDataExtractor
            from .data_extraction.batch_processor import BatchProcessor, BatchConfig
            from .data_extraction.data_reconciler import DataReconciler, ReconciliationConfig
            try:
                from .data_extraction.extraction_scheduler import ExtractionScheduler, SchedulerConfig
            except Exception as scheduler_import_err:
                logger.warning(f"Extraction scheduler unavailable, continuing without scheduler: {scheduler_import_err}")
                ExtractionScheduler = None  # type: ignore
                SchedulerConfig = None  # type: ignore
            try:
                from .data_extraction.incremental_sync import IncrementalSyncService, SyncConfig
            except Exception as sync_import_err:
                logger.warning(f"Incremental sync service unavailable, continuing without incremental sync: {sync_import_err}")
                IncrementalSyncService = None  # type: ignore
                SyncConfig = None  # type: ignore

            extractor = None
            try:
                extractor = ERPDataExtractor()
            except Exception as extractor_err:
                logger.warning(f"ERP data extractor unavailable: {extractor_err}")

            batch_processor = None
            if extractor:
                try:
                    batch_processor = BatchProcessor(BatchConfig(), extractor)
                except Exception as batch_err:
                    logger.warning(f"Batch processor unavailable, continuing without batch support: {batch_err}")

            reconciler = None
            if extractor:
                try:
                    reconciler = DataReconciler(ReconciliationConfig(), extractor)
                except Exception as reconcile_err:
                    logger.warning(f"Data reconciler unavailable, continuing without reconciliation: {reconcile_err}")

            incremental_sync = None
            if extractor and IncrementalSyncService and SyncConfig:
                try:
                    incremental_sync = IncrementalSyncService(SyncConfig(), extractor)
                except Exception as inc_err:
                    logger.warning(f"Incremental sync unavailable, continuing without incremental sync: {inc_err}")

            scheduler = None
            if extractor and ExtractionScheduler and SchedulerConfig:
                try:
                    scheduler = ExtractionScheduler(
                        SchedulerConfig(),
                        extractor,
                        batch_processor=batch_processor,
                        sync_service=incremental_sync
                    )
                except Exception as sched_err:
                    logger.warning(f"Extraction scheduler initialization failed, continuing without scheduler: {sched_err}")

            # Create data extraction service wrapper
            extraction_service = {
                "erp_extractor": extractor,
                "batch_processor": batch_processor,
                "scheduler": scheduler,
                "reconciler": reconciler,
                "incremental_sync": incremental_sync
            }
            
            self.services["data_extraction"] = extraction_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="data_extraction",
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                callback=self._create_extraction_callback(extraction_service),
                priority=4,
                tags=["extraction", "etl", "batch", "sync"],
                metadata={
                    "service_type": "data_extraction",
                    "operations": [
                        "extract_erp_data",
                        "get_transactions",
                        "get_sales_summary",
                        "process_batch",
                        "schedule_extraction",
                        "reconcile_data",
                        "incremental_sync"
                    ]
                }
            )
            
            self.service_endpoints["data_extraction"] = endpoint_id
            logger.info(f"Data extraction service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register data extraction services: {str(e)}")
    
    async def _register_integration_management_services(self):
        """Register integration management services"""
        try:
            from .integration_management.connection_manager import connection_manager
            from .integration_management.integration_health_monitor import integration_health_monitor
            from .integration_management.metrics_collector import metrics_collector
            from .integration_management.sync_orchestrator import sync_orchestrator
            from .integration_management.dependency_injector import configure_integration_dependencies
            
            # Create integration management service wrapper
            integration_service = {
                "connection_manager": connection_manager,
                "health_monitor": integration_health_monitor,
                "metrics_collector": metrics_collector,
                "sync_orchestrator": sync_orchestrator,
                "connection_tester": connection_tester,
            }

            try:
                configure_integration_dependencies()
            except Exception as dep_err:
                logger.warning(f"Failed to configure integration dependencies: {dep_err}")

            orchestrator = integration_service.get("sync_orchestrator")
            if orchestrator and self.background_runner:
                try:
                    orchestrator.configure_task_runner(self.background_runner)
                except Exception as runner_err:
                    logger.warning(f"Failed to configure background runner for orchestrator: {runner_err}")

            self.integration_health_monitor = integration_service.get("health_monitor")
            if self.integration_health_monitor and integration_service["connection_manager"]:
                try:
                    await self.integration_health_monitor.attach_connection_manager(integration_service["connection_manager"])
                except Exception as attach_err:
                    logger.warning(f"Integration health monitor attach failed: {attach_err}")
            
            self.services["integration_management"] = integration_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="integration_management",
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                callback=self._create_integration_callback(integration_service),
                priority=3,
                tags=["integration", "management", "monitoring", "orchestration"],
                metadata={
                    "service_type": "integration_management",
                    "operations": [
                        "health_check",
                        "manage_connections",
                        "monitor_health",
                        "collect_metrics",
                        "orchestrate_sync",
                        "test_connections",
                        # ERP connection management operations used by SI routes
                        "list_erp_connections",
                        "create_erp_connection",
                        "get_erp_connection",
                        "update_erp_connection",
                        "delete_erp_connection",
                        "test_erp_connection",
                        "test_erp_connection_credentials",
                        "get_erp_connection_health",
                        "bulk_test_erp_connections",
                        "bulk_sync_erp_data",
                    ]
                }
            )
            
            self.service_endpoints["integration_management"] = endpoint_id
            logger.info(f"Integration management service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register integration management services: {str(e)}")
    
    async def _register_authentication_services(self):
        """Register authentication services"""
        try:
            from .authentication.auth_manager import AuthManager
            from .authentication.firs_auth_service import FIRSAuthService
            from .authentication.certificate_auth import CertificateAuth
            from .authentication.token_manager import TokenManager, TokenConfig
            
            # Create authentication service wrapper
            auth_manager = None
            try:
                auth_manager = AuthManager()
            except Exception as auth_mgr_err:
                logger.warning(f"Auth manager unavailable, continuing without manager: {auth_mgr_err}")

            firs_auth = None
            try:
                firs_auth = FIRSAuthService()
            except Exception as firs_err:
                logger.warning(f"FIRS auth service unavailable, continuing without FIRS auth: {firs_err}")

            cert_auth = None
            try:
                cert_auth = CertificateAuth()
            except Exception as cert_err:
                logger.warning(f"Certificate auth unavailable, continuing without certificate auth: {cert_err}")

            token_manager = None
            try:
                token_manager = TokenManager(TokenConfig())
            except Exception as token_err:
                logger.warning(f"Token manager unavailable, continuing without token manager: {token_err}")

            auth_service = {
                "auth_manager": auth_manager,
                "firs_auth": firs_auth,
                "cert_auth": cert_auth,
                "token_manager": token_manager
            }
            
            self.services["authentication"] = auth_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="authentication",
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                callback=self._create_auth_callback(auth_service),
                priority=5,
                tags=["auth", "security", "firs", "certificate"],
                metadata={
                    "service_type": "authentication",
                    "operations": [
                        "authenticate_user",
                        "validate_certificate",
                        "manage_tokens",
                        "firs_auth",
                        "refresh_credentials"
                    ]
                }
            )
            
            self.service_endpoints["authentication"] = endpoint_id
            logger.info(f"Authentication service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register authentication services: {str(e)}")
    
    async def _register_subscription_services(self):
        """Register subscription management services"""
        try:
            from .subscription_management.si_tier_manager import SITierManager
            from .subscription_management.si_tier_validator import SITierValidator
            from .subscription_management.si_usage_tracker import SIUsageTracker
            from .subscription_management.si_subscription_guard import SISubscriptionGuard
            
            # Create subscription service wrapper
            subscription_service = {
                "tier_manager": SITierManager(),
                "tier_validator": SITierValidator(),
                "usage_tracker": SIUsageTracker(),
                "subscription_guard": SISubscriptionGuard(),
                "operations": [
                    "manage_subscription_tier",
                    "validate_tier_access",
                    "track_usage",
                    "enforce_subscription_limits",
                    "check_feature_access"
                ]
            }
            
            self.services["subscription_management"] = subscription_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="subscription_management",
                service_role=ServiceRole.SYSTEM_INTEGRATOR,
                callback=self._create_subscription_callback(subscription_service),
                priority=4,
                tags=["subscription", "billing", "tier_management", "usage_tracking"],
                metadata={
                    "service_type": "subscription_management",
                    "operations": [
                        "manage_subscription_tier",
                        "validate_tier_access", 
                        "track_usage",
                        "enforce_subscription_limits",
                        "check_feature_access"
                    ]
                }
            )
            
            self.service_endpoints["subscription_management"] = endpoint_id
            logger.info(f"Subscription management service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register subscription services: {str(e)}")
    
    # Service callback creators
    def _create_erp_callback(self, erp_service):
        """Create callback for ERP operations"""
        async def erp_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                # New: Fetch Odoo invoices and transform to FIRS format for APP submissions
                if operation == "fetch_odoo_invoices_for_firs":
                    try:
                        from external_integrations.business_systems.erp.odoo.connector import OdooConnector
                    except Exception as _imp_err:
                        return {"operation": operation, "success": False, "error": f"odoo_connector_unavailable: {_imp_err}"}

                    odoo_cfg = payload.get("odoo_config") or {}
                    invoice_ids = payload.get("invoice_ids") or []
                    target_format = payload.get("target_format", "UBL_BIS_3.0")
                    transform = bool(payload.get("transform", True))
                    if not isinstance(invoice_ids, list):
                        invoice_ids = [invoice_ids]

                    try:
                        connector = OdooConnector(odoo_cfg)
                    except Exception as ce:
                        return {"operation": operation, "success": False, "error": f"connector_init_failed: {ce}"}

                    invoices = []
                    errors = []
                    for inv_id in invoice_ids:
                        try:
                            raw = connector.get_invoice_by_id(int(inv_id) if str(inv_id).isdigit() else inv_id)
                            if transform:
                                transformed = await connector.transform_to_firs_format(raw, target_format=target_format)
                                # Shape shim: return just the payload expected by APP signing
                                out = transformed.get("firs_invoice") if isinstance(transformed, dict) else transformed
                                invoices.append(out)
                            else:
                                invoices.append(raw)
                        except Exception as e:
                            errors.append({"invoice_id": inv_id, "error": str(e)})
                    return {
                        "operation": operation,
                        "success": len(invoices) > 0,
                        "data": {"invoices": invoices, "errors": errors}
                    }

                if operation == "fetch_odoo_invoice_batch_for_firs":
                    try:
                        from external_integrations.business_systems.erp.odoo.connector import OdooConnector
                    except Exception as _imp_err:
                        return {"operation": operation, "success": False, "error": f"odoo_connector_unavailable: {_imp_err}"}

                    odoo_cfg = payload.get("odoo_config") or {}
                    batch_size = int(payload.get("batch_size", 50))
                    include_attachments = bool(payload.get("include_attachments", False))
                    transform = bool(payload.get("transform", True))
                    target_format = payload.get("target_format", "UBL_BIS_3.0")
                    try:
                        connector = OdooConnector(odoo_cfg)
                    except Exception as ce:
                        return {"operation": operation, "success": False, "error": f"connector_init_failed: {ce}"}

                    try:
                        raw_list = connector.get_invoices(limit=batch_size, include_attachments=include_attachments)
                        invoices = []
                        for raw in raw_list or []:
                            if transform:
                                transformed = await connector.transform_to_firs_format(raw, target_format=target_format)
                                out = transformed.get("firs_invoice") if isinstance(transformed, dict) else transformed
                                invoices.append(out)
                            else:
                                invoices.append(raw)
                        return {
                            "operation": operation,
                            "success": len(invoices) > 0,
                            "data": {"invoices": invoices, "errors": []},
                        }
                    except Exception as e:
                        return {"operation": operation, "success": False, "error": str(e)}

                if operation == "test_erp_connection":
                    # Use the test_odoo_connection function
                    result = erp_service["connection_tester"](payload.get("connection_params"))
                    return {"operation": operation, "success": True, "data": result}
                elif operation == "extract_erp_data":
                    # Minimal non-placeholder implementation using ERPDataProcessor
                    from .erp_integration.erp_data_processor import ERPDataProcessor, ProcessingConfig, ERPRecord
                    config = ProcessingConfig()
                    processor = ERPDataProcessor(config)
                    records = payload.get("records", []) or []
                    # Convert dict records to ERPRecord if needed
                    erp_records = []
                    for idx, r in enumerate(records):
                        if isinstance(r, ERPRecord):
                            erp_records.append(r)
                        else:
                            erp_records.append(
                                ERPRecord(
                                    record_id=r.get("record_id", f"rec-{idx}"),
                                    record_type=r.get("record_type", "invoice"),
                                    source_system=r.get("source_system", "erp"),
                                    raw_data=r,
                                )
                            )
                    result = await processor.process_erp_data(erp_records, processing_options=payload.get("processing_options", {}))
                    data = {
                        "result_id": result.result_id,
                        "status": result.status.value,
                        "total_records": result.total_records,
                        "processed_records": result.processed_records,
                        "failed_records": result.failed_records,
                        "issues_detected": [i.__dict__ for i in result.issues_detected],
                        "processing_duration": result.processing_duration,
                    }
                    return {"operation": operation, "success": True, "data": data}
                elif operation == "sync_erp_data":
                    return await self._handle_sync_erp_data(payload)
                elif operation == "get_erp_sync_status":
                    return await self._handle_get_erp_sync_status(payload)
                else:
                    return None
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return erp_callback
    
    def _create_certificate_callback(self, cert_service):
        """Create callback for certificate operations with AsyncSession DI"""
        from core_platform.data_management.db_async import get_async_session
        from si_services.certificate_management.certificate_service import CertificateService
        from si_services.certificate_management.digital_certificate_service import DigitalCertificateService

        async def cert_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                # Acquire a short-lived async session for operations that need DB
                async for db in get_async_session():
                    service = CertificateService(db=db)

                    if operation == "generate_certificate":
                        subject_info = payload.get("subject_info", {})
                        organization_id = payload.get("organization_id")
                        validity_days = int(payload.get("validity_days", 365))
                        certificate_type = payload.get("certificate_type", "signing")
                        cert_id, cert_pem = await service.generate_certificate(
                            subject_info=subject_info,
                            organization_id=organization_id,
                            validity_days=validity_days,
                            certificate_type=certificate_type,
                        )
                        return {"operation": operation, "success": True, "data": {"certificate_id": cert_id, "certificate_pem": cert_pem}}

                    if operation == "revoke_certificate":
                        certificate_id = payload.get("certificate_id")
                        reason = payload.get("reason", "unspecified")
                        success = await service.revoke_certificate(certificate_id, reason)
                        return {"operation": operation, "success": success, "data": {"certificate_id": certificate_id}}

                    if operation == "renew_certificate":
                        certificate_id = payload.get("certificate_id")
                        validity_days = int(payload.get("validity_days", 365))
                        new_id, success = service.renew_certificate(certificate_id, validity_days)
                        return {"operation": operation, "success": success, "data": {"new_certificate_id": new_id}}

                    if operation == "validate_certificate":
                        certificate_data = payload.get("certificate_data")
                        result = service.validate_certificate(certificate_data)
                        return {"operation": operation, "success": result.get("is_valid", False), "data": result}

                    if operation == "verify_signature":
                        certificate_id = payload.get("certificate_id")
                        data_payload = payload.get("data")
                        signature_info = payload.get("signature_info", {})
                        if isinstance(data_payload, dict):
                            data_payload = json.dumps(data_payload, sort_keys=True, separators=(",", ":"))

                        verifier = DigitalCertificateService()
                        verification_result = verifier.verify_signature(
                            data=data_payload or "",
                            signature_info=signature_info,
                            certificate_id=certificate_id,
                        )
                        return {
                            "operation": operation,
                            "success": verification_result.get("is_valid", False),
                            "data": verification_result,
                        }

                    if operation == "get_certificate_status":
                        certificate_id = payload.get("certificate_id")
                        status = service.get_certificate_status(certificate_id)
                        return {"operation": operation, "success": True, "data": status}

                    # Default placeholder
                    return {"operation": operation, "success": True, "data": {"status": "unsupported_operation"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return cert_callback
    
    def _create_document_callback(self, doc_service):
        """Create callback for document operations"""
        async def doc_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                if operation == "generate_invoice" and doc_service["invoice_generator"]:
                    result = await doc_service["invoice_generator"].generate_from_erp_data(
                        payload.get("erp_data", {}),
                        payload.get("format_type", "ubl")
                    )
                    return {"operation": operation, "success": True, "data": result}
                else:
                    return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return doc_callback
    
    def _create_irn_callback(self, irn_service):
        """Create callback for IRN operations"""

        generation_service = irn_service.get("generation_service")
        irn_generator = irn_service.get("irn_generator")
        qr_generator = irn_service.get("qr_generator")
        qr_signer = irn_service.get("qr_signing_service")

        async def irn_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                if operation in {"request_irn_from_firs", "submit_irn_to_firs"}:
                    if not generation_service:
                        return {"operation": operation, "success": False, "error": "irn_service_unavailable"}

                    invoice_data = payload.get("invoice_data") or {}
                    irn_value = payload.get("irn")
                    organization_id = payload.get("organization_id") or payload.get("tenant_id") or payload.get("tenantId")
                    environment = payload.get("environment", "sandbox")

                    result = await generation_service.request_irn_from_firs(
                        irn_value=irn_value,
                        invoice_data=invoice_data,
                        environment=environment,
                        organization_id=organization_id,
                    )
                    return {
                        "operation": operation,
                        "success": result.get("success", False),
                        "data": result,
                    }

                if operation == "generate_irn":
                    if not irn_generator:
                        return {"operation": operation, "success": False, "error": "irn_generator_unavailable"}

                    invoice_data = payload.get("invoice_data") or {}
                    irn_value, verification_code, hash_value = irn_generator.generate_irn(invoice_data)
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "irn": irn_value,
                            "verification_code": verification_code,
                            "hash": hash_value,
                        },
                    }

                if operation == "generate_qr_code":
                    if not qr_generator:
                        return {"operation": operation, "success": False, "error": "qr_generator_unavailable"}

                    irn_value = payload.get("irn") or payload.get("IRN")
                    if not irn_value:
                        return {"operation": operation, "success": False, "error": "missing_irn"}

                    verification_code = (
                        payload.get("verification_code")
                        or payload.get("verificationCode")
                        or ""
                    )
                    invoice_data = payload.get("invoice_data") or {}
                    format_type = payload.get("format_type", "json")

                    qr_payload = qr_generator.generate_qr_code(
                        irn_value=irn_value,
                        verification_code=verification_code,
                        invoice_data=invoice_data,
                        format_type=format_type,
                    )

                    return {
                        "operation": operation,
                        "success": True,
                        "data": qr_payload,
                    }

                if operation == "sign_qr_payload":
                    if not qr_signer:
                        return {"operation": operation, "success": False, "error": "qr_signing_unavailable"}

                    irn_value = payload.get("irn")
                    verification_code = payload.get("verification_code") or payload.get("verificationCode") or ""
                    invoice_data = payload.get("invoice_data") or {}
                    format_type = payload.get("format_type", "json")

                    if not irn_value:
                        return {"operation": operation, "success": False, "error": "missing_irn"}

                    signed = qr_signer.generate_signed_qr(
                        irn=irn_value,
                        verification_code=verification_code,
                        invoice_data=invoice_data,
                        qr_format=format_type,
                    )

                    if signed is None:
                        return {"operation": operation, "success": False, "error": "public_key_unavailable"}

                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "qr_data": signed.qr_data,
                            "qr_string": signed.qr_string,
                            "encrypted_payload": signed.encrypted_payload,
                            "encryption_metadata": signed.encryption_metadata,
                        },
                    }

                if operation == "validate_irn":
                    if not generation_service:
                        return {"operation": operation, "success": False, "error": "irn_service_unavailable"}

                    irn_value = payload.get("irn")
                    if not irn_value:
                        return {"operation": operation, "success": False, "error": "missing_irn"}

                    verification_code = payload.get("verification_code") or payload.get("verificationCode")
                    validation_level_value = payload.get("validation_level") or payload.get("validationLevel")

                    if validation_level_value:
                        from si_services.irn_qr_generation.irn_validator import ValidationLevel as _ValidationLevel

                        try:
                            validation_level = (
                                validation_level_value
                                if isinstance(validation_level_value, _ValidationLevel)
                                else _ValidationLevel[str(validation_level_value).upper()]
                            )
                        except Exception:
                            validation_level = _ValidationLevel.STANDARD
                    else:
                        from si_services.irn_qr_generation.irn_validator import ValidationLevel as _ValidationLevel

                        validation_level = _ValidationLevel.STANDARD

                    validation = generation_service.validate_irn(
                        irn_value=str(irn_value),
                        verification_code=verification_code,
                        validation_level=validation_level,
                    )

                    return {
                        "operation": operation,
                        "success": validation.get("is_valid", False),
                        "data": validation,
                    }

                if operation == "bulk_generate_irn":
                    return {
                        "operation": operation,
                        "success": False,
                        "error": "bulk_irn_generation_deprecated",
                    }

                if operation == "get_irn_status":
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "remote_irn_enabled": False,
                        },
                    }

                return {"operation": operation, "success": False, "error": "unsupported_operation"}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}

        return irn_callback

    def _create_invoice_validation_callback(self, validation_service: InvoiceValidationService):
        async def callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                if operation == "validate_invoice_proxy":
                    try:
                        result = await validation_service.validate_invoice(payload)
                        return {
                            "operation": operation,
                            "success": True,
                            "data": result,
                        }
                    except ValidationError as exc:
                        return {
                            "operation": operation,
                            "success": False,
                            "error": "validation_failed",
                            "details": exc.errors(),
                        }
                return {"operation": operation, "success": False, "error": "unsupported_operation"}
            except Exception as exc:
                return {"operation": operation, "success": False, "error": str(exc)}

        return callback
    
    def _create_extraction_callback(self, extraction_service):
        """Create callback for data extraction operations"""
        async def extraction_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                from core_platform.data_management.db_async import get_async_session
                from external_integrations.financial_systems.banking.open_banking.invoice_automation.firs_formatter import FIRSFormatter
                from si_services.firs_integration.comprehensive_invoice_generator import ComprehensiveFIRSInvoiceGenerator
                
                if operation == "get_transactions":
                    # Aggregate business transactions using the generator
                    organization_id = payload.get("organization_id")
                    source_types = payload.get("source_types")  # optional list
                    date_from = payload.get("date_from")
                    date_to = payload.get("date_to")
                    
                    async for db in get_async_session():
                        formatter = FIRSFormatter(
                            supplier_info={"name": "TaxPoynt", "address": "", "tin": "", "phone": "", "email": ""}
                        )
                        generator = ComprehensiveFIRSInvoiceGenerator(db, formatter)
                        date_range = None
                        if date_from and date_to:
                            from datetime import datetime
                            try:
                                date_range = (
                                    datetime.fromisoformat(date_from),
                                    datetime.fromisoformat(date_to),
                                )
                            except Exception:
                                date_range = None
                        txns = await generator.aggregate_business_data(organization_id=organization_id, date_range=date_range)
                        # Optional filtering by source types
                        if source_types:
                            stypes = set(source_types)
                            txns = [t for t in txns if t.source_type.value in stypes]
                        items = [
                            {
                                "id": t.id,
                                "source_type": t.source_type.value,
                                "source_id": t.source_id,
                                "transaction_id": t.transaction_id,
                                "date": t.date.isoformat(),
                                "customer_name": t.customer_name,
                                "customer_email": t.customer_email,
                                "amount": float(t.amount),
                                "currency": t.currency,
                                "description": t.description,
                                "tax_amount": float(t.tax_amount),
                                "payment_status": t.payment_status,
                                "payment_method": t.payment_method,
                                "confidence": t.confidence,
                            }
                            for t in txns
                        ]
                        return {"operation": operation, "success": True, "data": {"transactions": items, "total_count": len(items)}}

                if operation == "get_sales_summary":
                    # Build a basic sales summary from aggregated transactions
                    organization_id = payload.get("organization_id")
                    source_types = payload.get("source_types")
                    async for db in get_async_session():
                        formatter = FIRSFormatter(
                            supplier_info={"name": "TaxPoynt", "address": "", "tin": "", "phone": "", "email": ""}
                        )
                        generator = ComprehensiveFIRSInvoiceGenerator(db, formatter)
                        txns = await generator.aggregate_business_data(organization_id=organization_id)
                        if source_types:
                            stypes = set(source_types)
                            txns = [t for t in txns if t.source_type.value in stypes]
                        total = sum(float(t.amount) for t in txns)
                        by_source = {}
                        for t in txns:
                            key = t.source_type.value
                            by_source.setdefault(key, {"count": 0, "amount": 0.0})
                            by_source[key]["count"] += 1
                            by_source[key]["amount"] += float(t.amount)
                        return {"operation": operation, "success": True, "data": {"total_amount": total, "by_source": by_source, "count": len(txns)}}

                if operation == "extract_erp_data":
                    # Use ERP extractor if available
                    extractor = extraction_service.get("erp_extractor")
                    if not extractor:
                        return {"operation": operation, "success": False, "error": "ERP extractor not available"}
                    filters = payload.get("filters", {})
                    # Minimal invocation path for demo/mock
                    from si_services.data_extraction.erp_data_extractor import ExtractionFilter
                    ef = ExtractionFilter()
                    invoices = await extractor.extract_invoices(ef)
                    items = [
                        {
                            "invoice_number": inv.invoice_number,
                            "total_amount": inv.total_amount,
                            "tax_amount": inv.tax_amount,
                            "currency": inv.currency,
                            "customer_name": inv.customer_name,
                            "invoice_date": inv.invoice_date.isoformat(),
                        }
                        for inv in invoices
                    ]
                    return {"operation": operation, "success": True, "data": {"invoices": items, "total_count": len(items)}}

                if operation == "reconcile_data":
                    # Start reconciliation over a window
                    try:
                        from si_services.data_extraction.data_reconciler import DataReconciler, ReconciliationConfig
                        from si_services.data_extraction.erp_data_extractor import ERPDataExtractor, ERPType
                        cfg = ReconciliationConfig()
                        extractor = ERPDataExtractor()
                        reconciler = DataReconciler(cfg, extractor)
                        erp_type = ERPType[payload.get("erp_type", "ODOO").upper()]
                        recon_id = await reconciler.start_reconciliation(erp_type)
                        return {"operation": operation, "success": True, "data": {"reconciliation_id": recon_id}}
                    except Exception as e:
                        return {"operation": operation, "success": False, "error": str(e)}

                if operation == "schedule_extraction":
                    # Schedule a one-time incremental sync job and start scheduler
                    try:
                        from si_services.data_extraction.extraction_scheduler import (
                            ExtractionScheduler, SchedulerConfig, ScheduledJob, ScheduleConfig, ScheduleType, JobType
                        )
                        from si_services.data_extraction.erp_data_extractor import ERPDataExtractor, ERPType
                        from si_services.data_extraction.incremental_sync import IncrementalSyncService, SyncConfig
                        from datetime import datetime, timedelta
                        erp_type = ERPType[payload.get("erp_type", "ODOO").upper()]
                        sched_cfg = SchedulerConfig(enable_job_persistence=False)
                        extractor = ERPDataExtractor()
                        sync_svc = IncrementalSyncService(SyncConfig(), extractor)
                        scheduler = ExtractionScheduler(sched_cfg, extractor, batch_processor=None, sync_service=sync_svc)
                        await scheduler.start_scheduler()
                        job_id = f"job_{erp_type.value}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
                        schedule = ScheduleConfig(
                            schedule_type=ScheduleType.ONE_TIME,
                            start_time=datetime.utcnow() + timedelta(seconds=5)
                        )
                        job = ScheduledJob(
                            job_id=job_id,
                            job_name=f"One-time incremental sync ({erp_type.value})",
                            job_type=JobType.INCREMENTAL_SYNC,
                            erp_type=erp_type,
                            schedule_config=schedule
                        )
                        jid = await scheduler.schedule_job(job)
                        return {"operation": operation, "success": True, "data": {"job_id": jid, "status": "scheduled"}}
                    except Exception as e:
                        return {"operation": operation, "success": False, "error": str(e)}

                if operation == "incremental_sync":
                    # Start an incremental ERP sync (default Odoo)
                    try:
                        from si_services.data_extraction.incremental_sync import IncrementalSyncService, SyncConfig
                        from si_services.data_extraction.erp_data_extractor import ERPDataExtractor, ERPType
                        cfg = SyncConfig()
                        erp_type = ERPType[payload.get("erp_type", "ODOO").upper()]
                        extractor = ERPDataExtractor()
                        svc = IncrementalSyncService(cfg, extractor)
                        sync_id = await svc.start_incremental_sync(erp_type, force_full_sync=bool(payload.get("force_full_sync", False)))
                        return {"operation": operation, "success": True, "data": {"sync_id": sync_id}}
                    except Exception as e:
                        return {"operation": operation, "success": False, "error": str(e)}

                # Default placeholder for other operations
                return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return extraction_callback
    
    def _create_integration_callback(self, integration_service):
        """Create callback for integration management operations"""
        async def integration_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                health_monitor = integration_service.get("health_monitor")
                connection_tester = integration_service.get("connection_tester")
                if operation == "create_erp_connection":
                    return await self._handle_create_erp_connection(payload)
                if operation == "list_erp_connections":
                    return await self._handle_list_erp_connections(payload)
                if operation == "get_erp_connection":
                    return await self._handle_get_erp_connection(payload)
                if operation == "update_erp_connection":
                    return await self._handle_update_erp_connection(payload)
                if operation == "delete_erp_connection":
                    return await self._handle_delete_erp_connection(payload)
                if operation == "test_erp_connection":
                    return await self._handle_test_erp_connection(payload)
                if operation == "test_erp_connection_credentials":
                    return await self._handle_test_erp_connection_credentials(payload, connection_tester)
                if operation == "get_erp_connection_health":
                    return await self._handle_get_erp_connection_health(payload, health_monitor)
                if operation == "bulk_test_erp_connections":
                    return await self._handle_bulk_test_erp_connections(payload, integration_service)
                if operation == "bulk_sync_erp_data":
                    return await self._handle_bulk_sync_erp_data(payload, integration_service)

                return None
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return integration_callback

    async def _handle_create_erp_connection(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        print("_handle_create_erp_connection start")
        connection_data = payload.get("connection_data") or {}
        required_fields = ["erp_system", "organization_id", "connection_config"]
        missing = [field for field in required_fields if field not in connection_data]
        if missing:
            return {
                "operation": "create_erp_connection",
                "success": False,
                "error": f"Missing required fields: {', '.join(missing)}",
            }

        connection_id = str(uuid4())
        record = ERPConnectionRecord(
            connection_id=connection_id,
            organization_id=connection_data.get("organization_id"),
            erp_system=connection_data.get("erp_system"),
            connection_name=connection_data.get("connection_name")
            or connection_data.get("name")
            or "ERP Connection",
            environment=connection_data.get("environment", "sandbox"),
            connection_config=dict(connection_data.get("connection_config") or {}),
            metadata=connection_data.get("metadata") or {},
        )

        record = await self.erp_connection_repository.create(record)
        record = await self._configure_sync_for_connection(record)

        config = self._build_connection_config(record)
        registered = await connection_manager.register_system(config)
        if not registered:
            await self._teardown_sync_for_connection(record)
            self.erp_connection_repository.delete(connection_id)
            return {
                "operation": "create_erp_connection",
                "success": False,
                "error": "Unable to register connection with connection manager",
            }

        if self.integration_health_monitor:
            try:
                await self.integration_health_monitor.track_connection(
                    connection_id,
                    {
                        "erp_system": record.erp_system,
                        "connection_config": dict(record.connection_config or {}),
                        "environment": record.environment,
                    },
                )
            except Exception as monitor_err:
                logger.warning(f"Failed to start health monitoring for {connection_id}: {monitor_err}")

        result = {
            "operation": "create_erp_connection",
            "success": True,
            "data": {
                "connection_id": connection_id,
                "connection": self._record_to_dict(record),
            },
        }
        print("_handle_create_erp_connection end")
        return result

    async def _handle_get_erp_connection_health(self, payload: Dict[str, Any], health_monitor) -> Dict[str, Any]:
        connection_id = payload.get("connection_id")
        if not connection_id:
            return {
                "operation": "get_erp_connection_health",
                "success": False,
                "error": "connection_id is required",
            }

        snapshot = None
        if health_monitor:
            try:
                snapshot = health_monitor.get_health_snapshot(connection_id, include_history=True, history_limit=5)
            except Exception as hm_err:
                logger.warning(f"Health monitor snapshot error for {connection_id}: {hm_err}")

        status_obj = await connection_manager.get_system_status(connection_id)
        status_dict = self._connection_status_to_dict(status_obj)

        data = {
            "connection_id": connection_id,
            "status": (snapshot or {}).get("status") or (status_dict.get("state") if status_dict else "unknown"),
            "last_checked": (snapshot or {}).get("last_checked"),
            "message": (snapshot or {}).get("message"),
            "details": (snapshot or {}).get("details", {}) if snapshot else {},
            "health_score": status_dict.get("health_score") if status_dict else None,
            "state": status_dict.get("state") if status_dict else None,
            "connection_status": status_dict,
            "recent_history": (snapshot or {}).get("recent_history", []) if snapshot else [],
        }

        if not data.get("message"):
            data["message"] = "Health data not available yet"

        return {
            "operation": "get_erp_connection_health",
            "success": True,
            "data": data,
        }

    async def _handle_list_erp_connections(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        filters = payload.get("filters") or {}
        organization_filter = filters.get("organization_id")
        erp_filter = filters.get("erp_system")

        try:
            records = await self.erp_connection_repository.list(
                organization_id=organization_filter,
                erp_system=erp_filter,
            )
        except Exception as exc:
            logger.warning("Failed to list ERP connections: %s", exc)
            return {
                "operation": "list_erp_connections",
                "success": False,
                "error": "unavailable",
                "details": str(exc),
            }
        items = [self._record_to_dict(record) for record in records]

        return {
            "operation": "list_erp_connections",
            "success": True,
            "data": {
                "connections": items,
                "total_count": len(items),
            },
        }

    async def _handle_get_erp_connection(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        connection_id = payload.get("connection_id")
        if not connection_id:
            return {
                "operation": "get_erp_connection",
                "success": False,
                "error": "connection_id is required",
            }

        record = await self.erp_connection_repository.get(connection_id)
        if not record:
            return {
                "operation": "get_erp_connection",
                "success": False,
                "error": "Connection not found",
            }

        return {
            "operation": "get_erp_connection",
            "success": True,
            "data": self._record_to_dict(record),
        }

    async def _handle_update_erp_connection(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        connection_id = payload.get("connection_id")
        update_data = payload.get("connection_data") or {}
        if not connection_id:
            return {
                "operation": "update_erp_connection",
                "success": False,
                "error": "connection_id is required",
            }

        existing = await self.erp_connection_repository.get(connection_id)
        if not existing:
            return {
                "operation": "update_erp_connection",
                "success": False,
                "error": "Connection not found",
            }

        updated_record = await self.erp_connection_repository.update(connection_id, update_data)
        if not updated_record:
            return {
                "operation": "update_erp_connection",
                "success": False,
                "error": "Unable to update connection",
            }

        updated_record = await self._configure_sync_for_connection(updated_record)

        await connection_manager.unregister_system(connection_id)
        config = self._build_connection_config(updated_record)
        registered = await connection_manager.register_system(config)
        if not registered:
            await self._teardown_sync_for_connection(updated_record)
            return {
                "operation": "update_erp_connection",
                "success": False,
                "error": "Unable to register updated connection",
            }

        if self.integration_health_monitor:
            try:
                await self.integration_health_monitor.track_connection(
                    connection_id,
                    {
                        "erp_system": updated_record.erp_system,
                        "connection_config": dict(updated_record.connection_config or {}),
                        "environment": updated_record.environment,
                    },
                )
            except Exception as monitor_err:
                logger.warning(f"Failed to update health monitoring for {connection_id}: {monitor_err}")

        return {
            "operation": "update_erp_connection",
            "success": True,
            "data": self._record_to_dict(updated_record),
        }

    async def _handle_delete_erp_connection(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        connection_id = payload.get("connection_id")
        if not connection_id:
            return {
                "operation": "delete_erp_connection",
                "success": False,
                "error": "connection_id is required",
            }

        record = await self.erp_connection_repository.delete(connection_id)
        if not record:
            return {
                "operation": "delete_erp_connection",
                "success": False,
                "error": "Connection not found",
            }

        await connection_manager.unregister_system(connection_id)

        if self.integration_health_monitor:
            try:
                await self.integration_health_monitor.untrack_connection(connection_id)
            except Exception as monitor_err:
                logger.warning(f"Failed to stop health monitoring for {connection_id}: {monitor_err}")

        return {
            "operation": "delete_erp_connection",
            "success": True,
            "data": {"connection_id": connection_id},
        }

    async def _handle_bulk_test_erp_connections(
        self,
        payload: Dict[str, Any],
        integration_service: Dict[str, Any],
    ) -> Dict[str, Any]:
        connection_ids = payload.get("connection_ids") or []
        options = payload.get("options") or {}
        metrics_collector = (integration_service or {}).get("metrics_collector")

        if not connection_ids:
            records = await self.erp_connection_repository.list()
            connection_ids = [record.connection_id for record in records]

        test_id = f"bulk_test_{uuid4().hex[:8]}"
        results: List[Dict[str, Any]] = []
        success_count = 0
        failure_count = 0

        for connection_id in connection_ids:
            record = await self.erp_connection_repository.get(connection_id)
            if not record:
                outcome = {
                    "connection_id": connection_id,
                    "success": False,
                    "status": "not_found",
                }
                failure_count += 1
                if metrics_collector:
                    metrics_collector.record_test_result(
                        connection_id,
                        False,
                        {"reason": "not_found"},
                    )
                results.append(outcome)
                continue

            details = {
                "message": "Connection test queued",
                "options": options,
            }
            outcome = {
                "connection_id": connection_id,
                "success": True,
                "status": "queued",
                "details": details,
            }
            success_count += 1
            if metrics_collector:
                metrics_collector.record_test_result(connection_id, True, details)
            results.append(outcome)

        summary = {
            "total": len(connection_ids),
            "successful": success_count,
            "failed": failure_count,
        }

        response_data: Dict[str, Any] = {
            "test_id": test_id,
            "results": results,
            "summary": summary,
        }

        if metrics_collector:
            metrics_collector.record_bulk_test_run(test_id, summary, results)
            response_data["connection_activity"] = {
                cid: metrics_collector.get_connection_activity(cid)
                for cid in connection_ids
            }

        return {
            "operation": "bulk_test_erp_connections",
            "success": True,
            "data": response_data,
        }

    async def _handle_bulk_sync_erp_data(
        self,
        payload: Dict[str, Any],
        integration_service: Dict[str, Any],
    ) -> Dict[str, Any]:
        connection_ids = payload.get("connection_ids") or []
        data_type = payload.get("data_type", "invoices")
        options = payload.get("options") or {}
        initiated_by = payload.get("si_id")
        metrics_collector = (integration_service or {}).get("metrics_collector")
        orchestrator = (integration_service or {}).get("sync_orchestrator")

        if not orchestrator:
            return {
                "operation": "bulk_sync_erp_data",
                "success": False,
                "error": "sync_orchestrator_unavailable",
            }

        if not connection_ids:
            records = await self.erp_connection_repository.list()
            connection_ids = [record.connection_id for record in records]

        batch_id = f"sync_batch_{uuid4().hex[:8]}"
        jobs: List[Dict[str, Any]] = []
        success_count = 0
        failure_count = 0

        for connection_id in connection_ids:
            record = await self.erp_connection_repository.get(connection_id)
            if not record:
                job = {
                    "job_id": f"syncjob_{uuid4().hex[:8]}",
                    "connection_id": connection_id,
                    "data_type": data_type,
                    "status": "not_found",
                }
                failure_count += 1
                if metrics_collector:
                    metrics_collector.record_sync_execution(
                        connection_id,
                        False,
                        0,
                        {"reason": "not_found"},
                    )
                jobs.append(job)
                continue

            job = await orchestrator.queue_ad_hoc_sync(
                connection_id=connection_id,
                data_type=data_type,
                initiated_by=initiated_by,
                options=options,
            )
            success_count += 1
            if metrics_collector:
                metrics_collector.record_sync_execution(
                    connection_id,
                    True,
                    job.get("records_synced", 0),
                    {"job_id": job.get("job_id"), "data_type": data_type},
                )
            jobs.append(job)

        summary = {
            "total": len(connection_ids),
            "queued": success_count,
            "failed": failure_count,
        }

        response_data: Dict[str, Any] = {
            "sync_batch_id": batch_id,
            "jobs": jobs,
            "summary": summary,
        }

        if metrics_collector:
            response_data["connection_activity"] = {
                cid: metrics_collector.get_connection_activity(cid)
                for cid in connection_ids
            }

        return {
            "operation": "bulk_sync_erp_data",
            "success": True,
            "data": response_data,
        }

    async def _handle_sync_erp_data(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        connection_id = payload.get("connection_id")
        if not connection_id:
            return {
                "operation": "sync_erp_data",
                "success": False,
                "error": "connection_id is required",
            }

        record = await self.erp_connection_repository.get(connection_id)
        if not record:
            return {
                "operation": "sync_erp_data",
                "success": False,
                "error": "connection_not_found",
            }

        # Ensure configuration is up to date (sanitizes interval + registers sync)
        record = await self._configure_sync_for_connection(record)
        metadata = dict(record.metadata or {})
        sync_id = metadata.get("sync_id")
        if not sync_id:
            return {
                "operation": "sync_erp_data",
                "success": False,
                "error": "sync_configuration_unavailable",
            }

        force = bool(payload.get("force", False))

        try:
            execution_id = await sync_orchestrator.execute_sync(sync_id, force=force)
        except Exception as exc:
            return {
                "operation": "sync_erp_data",
                "success": False,
                "error": str(exc),
            }

        status = await sync_orchestrator.get_sync_status(sync_id)

        response_data: Dict[str, Any] = {
            "connection_id": connection_id,
            "sync_id": sync_id,
            "execution_id": execution_id,
            "auto_sync": metadata.get("auto_sync", False),
            "polling_interval_minutes": metadata.get("polling_interval_minutes"),
            "status": status,
        }

        await self.erp_connection_repository.update(
            connection_id,
            {"metadata": {"last_manual_sync_at": datetime.utcnow().isoformat()}},
        )

        return {
            "operation": "sync_erp_data",
            "success": True,
            "data": response_data,
        }

    async def _handle_get_erp_sync_status(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        connection_id = payload.get("connection_id")
        if not connection_id:
            return {
                "operation": "get_erp_sync_status",
                "success": False,
                "error": "connection_id is required",
            }

        record = await self.erp_connection_repository.get(connection_id)
        if not record:
            return {
                "operation": "get_erp_sync_status",
                "success": False,
                "error": "connection_not_found",
            }

        metadata = dict(record.metadata or {})
        sync_id = metadata.get("sync_id")
        if not sync_id:
            return {
                "operation": "get_erp_sync_status",
                "success": True,
                "data": {
                    "connection_id": connection_id,
                    "sync_available": False,
                    "auto_sync": metadata.get("auto_sync", False),
                },
            }

        status = await sync_orchestrator.get_sync_status(sync_id)

        return {
            "operation": "get_erp_sync_status",
            "success": True,
            "data": {
                "connection_id": connection_id,
                "sync_available": True,
                "sync_id": sync_id,
                "auto_sync": metadata.get("auto_sync", False),
                "polling_interval_minutes": metadata.get("polling_interval_minutes"),
                "status": status,
            },
        }

    async def _handle_test_erp_connection(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        from archive.legacy.backend.app.schemas.integration import (
            OdooConnectionTestRequest,
            OdooAuthMethod,
            FIRSEnvironment,
        )
        from .integration_management.integration_service_legacy import test_odoo_connection

        connection_id = payload.get("connection_id")
        if not connection_id:
            return {
                "operation": "test_erp_connection",
                "success": False,
                "error": "connection_id is required",
            }

        record = await self.erp_connection_repository.get(connection_id)
        if not record:
            return {
                "operation": "test_erp_connection",
                "success": False,
                "error": "Connection not found",
            }

        if record.erp_system.lower() != 'odoo':
            return {
                "operation": "test_erp_connection",
                "success": False,
                "error": "Only Odoo connections are supported for testing",
            }

        config = dict(record.connection_config or {})

        try:
            request = OdooConnectionTestRequest(
                url=config.get("url"),
                database=config.get("database"),
                username=config.get("username"),
                auth_method=OdooAuthMethod(config.get("auth_method", "api_key")),
                password=config.get("password"),
                api_key=config.get("api_key"),
                firs_environment=FIRSEnvironment(config.get("environment", "sandbox")),
            )
        except Exception as exc:
            return {
                "operation": "test_erp_connection",
                "success": False,
                "error": f"Invalid Odoo configuration: {exc}",
            }

        result = test_odoo_connection(request)
        return {
            "operation": "test_erp_connection",
            "success": result.success,
            "data": result.dict(),
        }

    async def _handle_test_erp_connection_credentials(
        self,
        payload: Dict[str, Any],
        connection_tester_instance: Optional[Any] = None,
    ) -> Dict[str, Any]:
        erp_system = (payload.get("erp_system") or "").lower()
        credentials = payload.get("credentials") or {}

        if not erp_system:
            return {
                "operation": "test_erp_connection_credentials",
                "success": False,
                "error": "erp_system is required",
            }

        if not isinstance(credentials, dict) or not credentials:
            return {
                "operation": "test_erp_connection_credentials",
                "success": False,
                "error": "credentials payload is required",
            }

        if erp_system != "odoo":
            return {
                "operation": "test_erp_connection_credentials",
                "success": False,
                "error": f"Credential testing not supported for ERP system '{erp_system}'",
            }

        tester = connection_tester_instance or connection_tester
        test_fn = getattr(tester, "test_odoo_connection_params", None)
        if not callable(test_fn):
            return {
                "operation": "test_erp_connection_credentials",
                "success": False,
                "error": "Odoo connection tester is unavailable",
            }

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        try:
            if loop and loop.is_running():
                result = await loop.run_in_executor(None, test_fn, credentials)
            else:
                result = test_fn(credentials)
        except Exception as exc:
            return {
                "operation": "test_erp_connection_credentials",
                "success": False,
                "error": f"Odoo credential test failed: {exc}",
            }

        success = bool(result.get("success", True)) if isinstance(result, dict) else True
        return {
            "operation": "test_erp_connection_credentials",
            "success": success,
            "data": result,
        }

    def _record_to_dict(self, record: ERPConnectionRecord) -> Dict[str, Any]:
        return {
            "connection_id": record.connection_id,
            "organization_id": record.organization_id,
            "erp_system": record.erp_system,
            "connection_name": record.connection_name,
            "environment": record.environment,
            "connection_config": record.connection_config,
            "metadata": record.metadata,
            "status": record.status,
            "status_reason": record.status_reason,
            "owner_user_id": record.owner_user_id,
            "is_active": record.is_active,
            "last_status_at": record.last_status_at.isoformat() if record.last_status_at else None,
            "created_at": record.created_at.isoformat() if record.created_at else None,
            "updated_at": record.updated_at.isoformat() if record.updated_at else None,
        }

    @staticmethod
    def _normalize_polling_interval(connection_config: Dict[str, Any], metadata: Dict[str, Any]) -> int:
        raw_value = (
            connection_config.get("polling_interval")
            or metadata.get("polling_interval_minutes")
            or 15
        )
        try:
            minutes = int(raw_value)
        except (TypeError, ValueError):
            minutes = 15
        return max(5, minutes)

    async def _configure_sync_for_connection(self, record: ERPConnectionRecord) -> ERPConnectionRecord:
        connection_config = dict(record.connection_config or {})
        metadata = dict(record.metadata or {})

        interval_minutes = self._normalize_polling_interval(connection_config, metadata)
        auto_sync_enabled = bool(connection_config.get("auto_sync", metadata.get("auto_sync", False)))
        sync_id = metadata.get("sync_id") or f"erp-sync-{record.connection_id}"
        schedule_type = "interval" if auto_sync_enabled else "manual"
        schedule_interval = interval_minutes * 60 if auto_sync_enabled else None

        try:
            existing = sync_orchestrator.configurations.get(sync_id)
            if existing:
                await sync_orchestrator.pause_sync(sync_id)
                sync_orchestrator.configurations.pop(sync_id, None)
        except Exception as exc:
            logger.warning("Failed to pause existing sync %s: %s", sync_id, exc)

        try:
            sync_config = SyncConfiguration(
                sync_id=sync_id,
                name=f"{record.connection_name or record.erp_system} Invoice Sync",
                source_system=record.connection_id,
                target_system="taxpoynt_core",
                direction=SyncDirection.PULL,
                data_type="invoices",
                schedule_type=schedule_type,
                schedule_interval=schedule_interval,
                enabled=True,
            )
            await register_sync_configuration(sync_config)
        except Exception as exc:
            logger.warning("Unable to register sync configuration for %s: %s", record.connection_id, exc)

        metadata_updates = {
            "sync_id": sync_id,
            "auto_sync": auto_sync_enabled,
            "polling_interval_minutes": interval_minutes,
            "schedule_type": schedule_type,
        }
        config_updates = {
            "auto_sync": auto_sync_enabled,
            "polling_interval": interval_minutes,
        }

        updated = await self.erp_connection_repository.update(
            record.connection_id,
            {
                "metadata": metadata_updates,
                "connection_config": config_updates,
            },
        )
        return updated or record

    async def _teardown_sync_for_connection(self, record: ERPConnectionRecord) -> None:
        metadata = dict(record.metadata or {})
        sync_id = metadata.get("sync_id")
        if not sync_id:
            return
        try:
            if sync_id in getattr(sync_orchestrator, "configurations", {}):
                await sync_orchestrator.pause_sync(sync_id)
                sync_orchestrator.configurations.pop(sync_id, None)
            scheduled_tasks = getattr(sync_orchestrator, "scheduled_tasks", {})
            task = scheduled_tasks.pop(sync_id, None)
            if task:
                task.cancel()
        except Exception as exc:
            logger.warning("Failed to tear down sync %s for connection %s: %s", sync_id, record.connection_id, exc)

    def _build_connection_config(self, record: ERPConnectionRecord) -> ConnectionConfig:
        config = record.connection_config or {}
        metadata = record.metadata or {}
        base_url = config.get("url") or config.get("base_url")
        parsed = urlparse(base_url) if base_url else None
        host = parsed.hostname if parsed and parsed.hostname else base_url or "localhost"
        port = parsed.port if parsed and parsed.port else (443 if parsed and parsed.scheme == 'https' else 80)
        interval_minutes = self._normalize_polling_interval(config, metadata)
        interval_seconds = max(300, interval_minutes * 60)

        return ConnectionConfig(
            system_id=record.connection_id,
            system_type=SystemType.ODOO,
            host=host,
            port=port,
            database=config.get("database"),
            username=config.get("username"),
            password=config.get("password"),
            api_key=config.get("api_key"),
            ssl_enabled=bool(parsed and parsed.scheme == 'https'),
            timeout=config.get("timeout", 30),
            health_check_interval=max(60, interval_seconds // 3),
            auto_sync_enabled=bool(config.get("auto_sync")),
            polling_interval_seconds=interval_seconds,
            metadata={
                "base_url": base_url,
                "environment": record.environment,
                "auth_method": config.get("auth_method"),
                "auto_sync": bool(config.get("auto_sync")),
                "polling_interval_minutes": interval_minutes,
            },
        )

    def _connection_status_to_dict(self, status) -> Optional[Dict[str, Any]]:
        if not status:
            return None

        data = asdict(status)
        state = data.get("state")
        if isinstance(state, Enum):
            data["state"] = state.value

        for key in ("connected_at", "last_activity", "last_status_at"):
            if data.get(key) and isinstance(data[key], datetime):
                data[key] = data[key].isoformat()

        return data
    
    def _create_auth_callback(self, auth_service):
        """Create callback for authentication operations"""
        async def auth_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return auth_callback
    
    def _create_subscription_callback(self, subscription_service):
        """Create callback for subscription management operations"""
        async def subscription_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                if operation == "manage_subscription_tier":
                    tier_data = payload.get("tier_data", {})
                    result = subscription_service["tier_manager"].manage_tier(tier_data)
                    return {"operation": operation, "success": True, "data": result}
                elif operation == "validate_tier_access":
                    access_data = payload.get("access_data", {})
                    result = subscription_service["tier_validator"].validate_access(access_data)
                    return {"operation": operation, "success": True, "data": result}
                elif operation == "track_usage":
                    usage_data = payload.get("usage_data", {})
                    result = subscription_service["usage_tracker"].track_usage(usage_data)
                    return {"operation": operation, "success": True, "data": result}
                elif operation == "enforce_subscription_limits":
                    limit_data = payload.get("limit_data", {})
                    result = subscription_service["subscription_guard"].enforce_limits(limit_data)
                    return {"operation": operation, "success": True, "data": result}
                else:
                    return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return subscription_callback
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get health status of all registered services"""
        health_status = {
            "registry_status": "healthy" if self.is_initialized else "uninitialized",
            "total_services": len(self.services),
            "registered_endpoints": len(self.service_endpoints),
            "services": {}
        }
        
        # Check banking service health
        if "banking" in self.services:
            try:
                banking_health = await self.services["banking"].health_check()
                health_status["services"]["banking"] = banking_health
            except Exception as e:
                health_status["services"]["banking"] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return health_status
    
    async def cleanup_services(self):
        """Cleanup all services and unregister from message router"""
        try:
            logger.info("Cleaning up SI services...")
            
            # Unregister from message router
            for service_name, endpoint_id in self.service_endpoints.items():
                try:
                    await self.message_router.unregister_service(endpoint_id)
                    logger.info(f"Unregistered service: {service_name}")
                except Exception as e:
                    logger.error(f"Failed to unregister {service_name}: {str(e)}")
            
            # Cleanup service instances
            for service_name, service in self.services.items():
                try:
                    if hasattr(service, 'cleanup'):
                        await service.cleanup()
                except Exception as e:
                    logger.error(f"Failed to cleanup {service_name}: {str(e)}")
            
            self.services.clear()
            self.service_endpoints.clear()
            self.is_initialized = False
            
            logger.info("SI services cleanup completed")
            
        except Exception as e:
            logger.error(f"SI services cleanup failed: {str(e)}")


# Global service registry instance
_service_registry: Optional[SIServiceRegistry] = None


async def initialize_si_services(
    message_router: MessageRouter,
    *,
    background_runner: Optional[Any] = None,
) -> SIServiceRegistry:
    """
    Initialize SI services with message router.
    
    Args:
        message_router: Core platform message router
        
    Returns:
        Initialized service registry
    """
    global _service_registry
    
    if _service_registry is not None and _service_registry.message_router is not message_router:
        try:
            await _service_registry.cleanup_services()
        except Exception as cleanup_err:
            logger.warning(f"Previous SI registry cleanup failed during router swap: {cleanup_err}")
        logger.info("Reinitializing SI service registry with new message router instance")
        _service_registry = None

    if _service_registry is None:
        _service_registry = SIServiceRegistry(
            message_router,
            background_runner=background_runner,
        )

    if background_runner is not None:
        _service_registry.configure_background_runner(background_runner)

    if not _service_registry.is_initialized:
        await _service_registry.initialize_services()
    
    return _service_registry


def get_si_service_registry() -> Optional[SIServiceRegistry]:
    """Get the global SI service registry instance"""
    return _service_registry


async def cleanup_si_services():
    """Cleanup SI services"""
    global _service_registry
    
    if _service_registry:
        await _service_registry.cleanup_services()
        _service_registry = None
