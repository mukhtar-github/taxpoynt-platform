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

import logging
import asyncio
from typing import Dict, Any, Optional

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

logger = logging.getLogger(__name__)


class SIServiceRegistry:
    """
    Registry for all SI services that handles initialization and message router registration.
    """
    
    def __init__(self, message_router: MessageRouter):
        """
        Initialize SI service registry.
        
        Args:
            message_router: Core platform message router
        """
        self.message_router = message_router
        self.services: Dict[str, Any] = {}
        self.service_endpoints: Dict[str, str] = {}
        self.is_initialized = False
        
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
            from .erp_integration.erp_integration_service import test_odoo_connection
            from .erp_integration.erp_data_processor import ERPDataProcessor
            from .erp_integration.data_sync_coordinator import DataSyncCoordinator
            
            # Create ERP service wrapper
            erp_service = {
                "connection_tester": test_odoo_connection,
                "data_processor": ERPDataProcessor() if hasattr(ERPDataProcessor, '__init__') else None,
                "sync_coordinator": DataSyncCoordinator() if hasattr(DataSyncCoordinator, '__init__') else None
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
                        "process_erp_invoices",
                        "validate_erp_mapping"
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
                        "get_certificate_status"
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
                    "supported_formats": ["ubl", "json", "xml", "pdf"]
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
            
            # Create IRN service wrapper
            irn_service = {
                "generation_service": IRNGenerationService(),
                "irn_generator": IRNGenerator() if hasattr(IRNGenerator, '__init__') else None,
                "qr_generator": QRCodeGenerator() if hasattr(QRCodeGenerator, '__init__') else None
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
                        "generate_irn",
                        "generate_qr_code",
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
    
    async def _register_data_extraction_services(self):
        """Register data extraction services"""
        try:
            from .data_extraction.erp_data_extractor import ERPDataExtractor
            from .data_extraction.batch_processor import BatchProcessor
            from .data_extraction.extraction_scheduler import ExtractionScheduler
            from .data_extraction.data_reconciler import DataReconciler
            from .data_extraction.incremental_sync import IncrementalSync
            
            # Create data extraction service wrapper
            extraction_service = {
                "erp_extractor": ERPDataExtractor() if hasattr(ERPDataExtractor, '__init__') else None,
                "batch_processor": BatchProcessor() if hasattr(BatchProcessor, '__init__') else None,
                "scheduler": ExtractionScheduler() if hasattr(ExtractionScheduler, '__init__') else None,
                "reconciler": DataReconciler() if hasattr(DataReconciler, '__init__') else None,
                "incremental_sync": IncrementalSync() if hasattr(IncrementalSync, '__init__') else None
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
            from .integration_management.connection_manager import ConnectionManager
            from .integration_management.integration_health_monitor import IntegrationHealthMonitor
            from .integration_management.metrics_collector import MetricsCollector
            from .integration_management.sync_orchestrator import SyncOrchestrator
            
            # Create integration management service wrapper
            integration_service = {
                "connection_manager": ConnectionManager() if hasattr(ConnectionManager, '__init__') else None,
                "health_monitor": IntegrationHealthMonitor() if hasattr(IntegrationHealthMonitor, '__init__') else None,
                "metrics_collector": MetricsCollector() if hasattr(MetricsCollector, '__init__') else None,
                "sync_orchestrator": SyncOrchestrator() if hasattr(SyncOrchestrator, '__init__') else None
            }
            
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
            from .authentication.token_manager import TokenManager
            
            # Create authentication service wrapper
            auth_service = {
                "auth_manager": AuthManager() if hasattr(AuthManager, '__init__') else None,
                "firs_auth": FIRSAuthService() if hasattr(FIRSAuthService, '__init__') else None,
                "cert_auth": CertificateAuth() if hasattr(CertificateAuth, '__init__') else None,
                "token_manager": TokenManager() if hasattr(TokenManager, '__init__') else None
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
                else:
                    return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return erp_callback
    
    def _create_certificate_callback(self, cert_service):
        """Create callback for certificate operations with AsyncSession DI"""
        from core_platform.data_management.db_async import get_async_session
        from si_services.certificate_management.certificate_service import CertificateService

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
        async def irn_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return irn_callback
    
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
                return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return integration_callback
    
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


async def initialize_si_services(message_router: MessageRouter) -> SIServiceRegistry:
    """
    Initialize SI services with message router.
    
    Args:
        message_router: Core platform message router
        
    Returns:
        Initialized service registry
    """
    global _service_registry
    
    if _service_registry is None:
        _service_registry = SIServiceRegistry(message_router)
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
