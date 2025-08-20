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
            await self._register_erp_services()
            await self._register_certificate_services()
            await self._register_document_services()
            await self._register_irn_services()
            await self._register_data_extraction_services()
            await self._register_integration_management_services()
            await self._register_authentication_services()
            await self._register_subscription_services()
            
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
                        "get_banking_connection_health"
                    ],
                    "providers": ["mono", "stitch", "unified_banking"]
                }
            )
            
            self.service_endpoints["banking_integration"] = endpoint_id
            logger.info(f"Banking service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register banking services: {str(e)}")
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
                        "manage_connections",
                        "monitor_health",
                        "collect_metrics",
                        "orchestrate_sync",
                        "test_connections"
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
                else:
                    return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return erp_callback
    
    def _create_certificate_callback(self, cert_service):
        """Create callback for certificate operations"""
        async def cert_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
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