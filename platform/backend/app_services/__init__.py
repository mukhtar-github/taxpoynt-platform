"""
APP Services Initialization and Registration
============================================

Initializes and registers all Access Point Provider (APP) services with the message router.
APP services handle FIRS communication, compliance, validation, and webhook processing.

Services Registered:
- FIRS Communication Service
- Webhook Processing Service
- Status Management Service
- Validation Service
- Transmission Service
- Compliance Service
- Taxpayer Management Service
"""

import logging
import asyncio
import os
from typing import Dict, Any, Optional

from core_platform.messaging.message_router import MessageRouter, ServiceRole

# Import APP services
from .webhook_services.webhook_receiver import WebhookReceiver
from .webhook_services.event_processor import EventProcessor
from .webhook_services.signature_validator import SignatureValidator
from .status_management.callback_manager import CallbackManager
from .status_management.status_tracker import StatusTracker
from .status_management.notification_service import NotificationService
from .firs_communication.firs_api_client import FIRSAPIClient
from .firs_communication.authentication_handler import FIRSAuthenticationHandler
from .validation.firs_validator import FIRSValidator
from .validation.submission_validator import SubmissionValidator
from .validation.format_validator import FormatValidator
from .transmission.secure_transmitter import SecureTransmitter
from .transmission.batch_transmitter import BatchTransmitter
from .transmission.delivery_tracker import DeliveryTracker
from .security_compliance.encryption_service import EncryptionService
from .security_compliance.audit_logger import AuditLogger
from .authentication_seals.seal_generator import SealGenerator
from .authentication_seals.verification_service import VerificationService
from .reporting.transmission_reports import TransmissionReportGenerator
from .reporting.compliance_metrics import ComplianceMetricsMonitor
from .taxpayer_management.taxpayer_onboarding import TaxpayerOnboardingService
from .onboarding_management.app_onboarding_service import APPOnboardingService

logger = logging.getLogger(__name__)


class APPServiceRegistry:
    """
    Registry for all APP services that handles initialization and message router registration.
    """
    
    def __init__(self, message_router: MessageRouter):
        """
        Initialize APP service registry.
        
        Args:
            message_router: Core platform message router
        """
        self.message_router = message_router
        self.services: Dict[str, Any] = {}
        self.service_endpoints: Dict[str, str] = {}
        self.is_initialized = False
        
    async def initialize_services(self) -> Dict[str, str]:
        """
        Initialize and register all APP services.
        
        Returns:
            Dict mapping service names to endpoint IDs
        """
        try:
            logger.info("Initializing APP services...")
            
            # Initialize core APP services
            await self._register_firs_services()
            await self._register_webhook_services()
            await self._register_status_management_services()
            await self._register_validation_services()
            await self._register_transmission_services()
            await self._register_security_services()
            await self._register_authentication_services()
            await self._register_reporting_services()
            await self._register_taxpayer_services()
            await self._register_onboarding_services()
            
            self.is_initialized = True
            logger.info(f"APP services initialized successfully. Registered {len(self.service_endpoints)} services.")
            
            return self.service_endpoints
            
        except Exception as e:
            logger.error(f"Failed to initialize APP services: {str(e)}", exc_info=True)
            raise RuntimeError(f"APP service initialization failed: {str(e)}")
    
    async def _register_firs_services(self):
        """Register FIRS communication services"""
        try:
            # Initialize FIRS services with real implementations
            firs_api_client = await self._create_firs_api_client()
            auth_handler = FIRSAuthenticationHandler(
                environment=os.getenv("FIRS_ENVIRONMENT", "sandbox")
            )
            # Thin HTTP client + resource cache for current FIRS header-based flows
            try:
                from .firs_communication.firs_http_client import FIRSHttpClient
                from .firs_communication.resource_cache import FIRSResourceCache
                firs_http_client = FIRSHttpClient()
                resource_cache = FIRSResourceCache(firs_http_client)
            except Exception:
                firs_http_client = None
                resource_cache = None

            firs_service = {
                "api_client": firs_api_client,
                "auth_handler": auth_handler,
                "http_client": firs_http_client,
                "resource_cache": resource_cache,
                "operations": [
                    "process_firs_webhook",
                    "update_firs_submission_status",
                    "submit_to_firs",
                    "validate_firs_response",
                    "validate_invoice_for_firs",
                    "validate_invoice_batch_for_firs",
                    "get_firs_validation_rules",
                    "update_firs_invoice",
                        "transmit_firs_invoice",
                        "confirm_firs_receipt",
                        "authenticate_firs",
                        "get_submission_status",
                        "receive_invoices_from_si",
                        "receive_invoice_batch_from_si"
                    ]
            }
            
            self.services["firs_communication"] = firs_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="firs_communication",
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                callback=self._create_firs_callback(firs_service),
                priority=5,
                tags=["firs", "api", "communication", "compliance"],
                metadata={
                    "service_type": "firs_communication",
                    "operations": [
                        "process_firs_webhook",
                        "update_firs_submission_status",
                        "submit_to_firs",
                        "validate_firs_response",
                        "validate_invoice_for_firs",
                        "validate_invoice_batch_for_firs",
                        "get_firs_validation_rules",
                        "get_submission_status",
                        "update_firs_invoice",
                        "transmit_firs_invoice",
                        "receive_invoices_from_si",
                        "receive_invoice_batch_from_si"
                    ]
                }
            )
            
            self.service_endpoints["firs_communication"] = endpoint_id
            logger.info(f"FIRS communication service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register FIRS services: {str(e)}")
    
    async def _register_webhook_services(self):
        """Register webhook processing services"""
        try:
            # Initialize webhook services with real implementations
            webhook_receiver = WebhookReceiver(
                webhook_secret=os.getenv("FIRS_WEBHOOK_SECRET", "yRLXTUtWIU2OlMyKOBAWEVmjIop1xJe5ULPJLYoJpyA"),
                max_payload_size=1024 * 1024  # 1MB
            )
            event_processor = EventProcessor()
            signature_validator = SignatureValidator()
            
            webhook_service = {
                "webhook_receiver": webhook_receiver,
                "event_processor": event_processor,
                "signature_validator": signature_validator,
                "operations": [
                    "process_webhook_event",
                    "verify_webhook_signature",
                    "handle_webhook_retry",
                    "process_event",
                    "validate_signature"
                ]
            }
            
            self.services["webhook_processing"] = webhook_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="webhook_processing",
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                callback=self._create_webhook_callback(webhook_service),
                priority=4,
                tags=["webhook", "event", "processing"],
                metadata={
                    "service_type": "webhook_processing",
                    "operations": [
                        "process_webhook_event",
                        "verify_webhook_signature",
                        "handle_webhook_retry",
                        "log_webhook_event"
                    ]
                }
            )
            
            self.service_endpoints["webhook_processing"] = endpoint_id
            logger.info(f"Webhook processing service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register webhook services: {str(e)}")
    
    async def _register_status_management_services(self):
        """Register status management services"""
        try:
            # Initialize status management services
            callback_manager = CallbackManager()
            
            status_service = {
                "callback_manager": callback_manager,
                "operations": [
                    "update_submission_status",
                    "send_status_notification",
                    "track_status_change"
                ]
            }
            
            self.services["status_management"] = status_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="status_management",
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                callback=self._create_status_callback(status_service),
                priority=4,
                tags=["status", "tracking", "notification"],
                metadata={
                    "service_type": "status_management",
                    "operations": [
                        "update_submission_status",
                        "send_status_notification",
                        "track_status_change",
                        "get_status_history"
                    ]
                }
            )
            
            self.service_endpoints["status_management"] = endpoint_id
            logger.info(f"Status management service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register status management services: {str(e)}")
    
    async def _register_validation_services(self):
        """Register validation services"""
        try:
            # Initialize validation services
            firs_validator = FIRSValidator() if hasattr(FIRSValidator, '__init__') else None
            
            validation_service = {
                "firs_validator": firs_validator,
                "operations": [
                    "validate_invoice",
                    "validate_submission",
                    "check_compliance"
                ]
            }
            
            self.services["validation"] = validation_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="validation",
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                callback=self._create_validation_callback(validation_service),
                priority=5,
                tags=["validation", "compliance", "firs"],
                metadata={
                    "service_type": "validation",
                    "operations": [
                        "validate_invoice",
                        "validate_submission",
                        "check_compliance",
                        "verify_format"
                    ]
                }
            )
            
            self.service_endpoints["validation"] = endpoint_id
            logger.info(f"Validation service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register validation services: {str(e)}")
    
    async def _register_transmission_services(self):
        """Register transmission services"""
        try:
            # Initialize transmission services - using placeholders for now
            transmission_service = {
                "batch_transmitter": None,  # Would initialize actual service
                "real_time_transmitter": None,
                "operations": [
                    "transmit_batch",
                    "transmit_real_time",
                    "retry_transmission"
                ]
            }
            
            self.services["transmission"] = transmission_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="transmission",
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                callback=self._create_transmission_callback(transmission_service),
                priority=4,
                tags=["transmission", "delivery", "firs"],
                metadata={
                    "service_type": "transmission",
                    "operations": [
                        "transmit_batch",
                        "transmit_real_time",
                        "retry_transmission",
                        "track_delivery"
                    ]
                }
            )
            
            self.service_endpoints["transmission"] = endpoint_id
            logger.info(f"Transmission service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register transmission services: {str(e)}")
    
    async def _register_security_services(self):
        """Register security and compliance services"""
        try:
            # Initialize security services
            encryption_service = EncryptionService()
            audit_logger = AuditLogger(log_directory="audit_logs")
            
            security_service = {
                "encryption_service": encryption_service,
                "audit_logger": audit_logger,
                "operations": [
                    "encrypt_document",
                    "decrypt_document",
                    "log_security_event",
                    "audit_compliance"
                ]
            }
            
            self.services["security_compliance"] = security_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="security_compliance",
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                callback=self._create_security_callback(security_service),
                priority=5,
                tags=["security", "encryption", "audit", "compliance"],
                metadata={
                    "service_type": "security_compliance",
                    "operations": [
                        "encrypt_document",
                        "decrypt_document", 
                        "log_security_event",
                        "audit_compliance"
                    ]
                }
            )
            
            self.service_endpoints["security_compliance"] = endpoint_id
            logger.info(f"Security compliance service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register security services: {str(e)}")
    
    async def _register_authentication_services(self):
        """Register authentication and seals services"""
        try:
            # Initialize authentication services
            seal_generator = SealGenerator()
            verification_service = VerificationService()
            
            auth_service = {
                "seal_generator": seal_generator,
                "verification_service": verification_service,
                "operations": [
                    "generate_digital_seal",
                    "verify_document",
                    "create_stamp",
                    "validate_signature"
                ]
            }
            
            self.services["authentication_seals"] = auth_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="authentication_seals",
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                callback=self._create_auth_seals_callback(auth_service),
                priority=5,
                tags=["authentication", "seals", "digital_signature", "verification"],
                metadata={
                    "service_type": "authentication_seals",
                    "operations": [
                        "generate_digital_seal",
                        "verify_document",
                        "create_stamp",
                        "validate_signature"
                    ]
                }
            )
            
            self.service_endpoints["authentication_seals"] = endpoint_id
            logger.info(f"Authentication seals service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register authentication services: {str(e)}")
    
    async def _register_reporting_services(self):
        """Register reporting and analytics services"""
        try:
            # Initialize reporting services
            transmission_reporter = TransmissionReportGenerator()
            compliance_monitor = ComplianceMetricsMonitor()
            
            reporting_service = {
                "transmission_reporter": transmission_reporter,
                "compliance_monitor": compliance_monitor,
                "operations": [
                    "generate_transmission_report",
                    "monitor_compliance",
                    "analyze_performance",
                    "create_dashboard"
                ]
            }
            
            self.services["reporting"] = reporting_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="reporting",
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                callback=self._create_reporting_callback(reporting_service),
                priority=3,
                tags=["reporting", "analytics", "compliance", "dashboard"],
                metadata={
                    "service_type": "reporting",
                    "operations": [
                        "generate_transmission_report",
                        "monitor_compliance",
                        "analyze_performance",
                        "create_dashboard"
                    ]
                }
            )
            
            self.service_endpoints["reporting"] = endpoint_id
            logger.info(f"Reporting service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register reporting services: {str(e)}")
    
    async def _register_taxpayer_services(self):
        """Register taxpayer management services"""
        try:
            # Initialize taxpayer services
            onboarding_service = TaxpayerOnboardingService()
            
            taxpayer_service = {
                "onboarding_service": onboarding_service,
                "operations": [
                    "onboard_taxpayer",
                    "track_registration",
                    "monitor_compliance",
                    "analyze_taxpayer"
                ]
            }
            
            self.services["taxpayer_management"] = taxpayer_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="taxpayer_management",
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                callback=self._create_taxpayer_callback(taxpayer_service),
                priority=3,
                tags=["taxpayer", "onboarding", "compliance", "registration"],
                metadata={
                    "service_type": "taxpayer_management",
                    "operations": [
                        "onboard_taxpayer",
                        "track_registration",
                        "monitor_compliance",
                        "analyze_taxpayer"
                    ]
                }
            )
            
            self.service_endpoints["taxpayer_management"] = endpoint_id
            logger.info(f"Taxpayer management service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register taxpayer services: {str(e)}")
    
    async def _register_onboarding_services(self):
        """Register APP onboarding management services"""
        try:
            # Initialize APP onboarding service
            app_onboarding_service = APPOnboardingService()
            
            onboarding_service = {
                "onboarding_service": app_onboarding_service,
                "operations": [
                    "get_onboarding_state",
                    "update_onboarding_state",
                    "complete_onboarding_step",
                    "complete_onboarding",
                    "reset_onboarding_state",
                    "get_onboarding_analytics",
                    "get_business_verification_status",
                    "get_firs_integration_status"
                ]
            }
            
            self.services["app_onboarding_management"] = onboarding_service
            
            # Register with message router
            endpoint_id = await self.message_router.register_service(
                service_name="app_onboarding_management",
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                callback=self._create_app_onboarding_callback(onboarding_service),
                priority=4,
                tags=["onboarding", "state_management", "app", "progress_tracking"],
                metadata={
                    "service_type": "app_onboarding_management",
                    "operations": [
                        "get_onboarding_state",
                        "update_onboarding_state",
                        "complete_onboarding_step",
                        "complete_onboarding",
                        "reset_onboarding_state",
                        "get_onboarding_analytics",
                        "get_business_verification_status",
                        "get_firs_integration_status"
                    ],
                    "supported_roles": ["access_point_provider"]
                }
            )
            
            self.service_endpoints["app_onboarding_management"] = endpoint_id
            logger.info(f"APP onboarding management service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register APP onboarding services: {str(e)}")
    
    def _create_app_onboarding_callback(self, onboarding_service: Dict[str, Any]):
        """Create callback function for APP onboarding service operations"""
        async def app_onboarding_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            """Handle APP onboarding service operations"""
            try:
                logger.info(f"Processing APP onboarding operation: {operation}")
                result = await onboarding_service["onboarding_service"].handle_operation(operation, payload)
                return result
                
            except Exception as e:
                logger.error(f"APP onboarding operation failed {operation}: {str(e)}", exc_info=True)
                return {
                    "operation": operation,
                    "success": False,
                    "error": str(e),
                    "error_type": type(e).__name__
                }
        
        return app_onboarding_callback
    
    async def _create_firs_api_client(self):
        """Create FIRS API client with proper configuration"""
        try:
            from .firs_communication.firs_api_client import (
                create_firs_api_client,
                FIRSEnvironment,
            )

            # Resolve environment and credentials from env (fallbacks for dev)
            env_str = os.getenv("FIRS_ENVIRONMENT", "sandbox").lower()
            environment = FIRSEnvironment.SANDBOX if env_str != "production" else FIRSEnvironment.PRODUCTION

            client_id = os.getenv("FIRS_CLIENT_ID", "your_firs_client_id")
            client_secret = os.getenv("FIRS_CLIENT_SECRET", "your_firs_client_secret")
            api_key = os.getenv("FIRS_API_KEY", "test_api_key")

            # Create FIRS API client using factory function (synchronous factory)
            client = create_firs_api_client(
                environment=environment,
                client_id=client_id,
                client_secret=client_secret,
                api_key=api_key,
            )
            
            return client
            
        except Exception as e:
            logger.error(f"Failed to create FIRS API client: {str(e)}")
            return None
    
    # Service callback creators
    def _create_firs_callback(self, firs_service):
        """Create callback for FIRS operations"""
        async def firs_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                if operation == "process_firs_webhook":
                    return await self._handle_firs_webhook(payload)
                elif operation == "update_firs_submission_status":
                    return await self._handle_status_update(payload)
                else:
                    return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return firs_callback
    
    def _create_webhook_callback(self, webhook_service):
        """Create callback for webhook operations"""
        async def webhook_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                if operation == "process_webhook_event":
                    # Use existing webhook receiver
                    result = await webhook_service["webhook_receiver"].process_webhook(
                        payload.get("event_type"),
                        payload.get("webhook_data", {}),
                        payload.get("source", "unknown")
                    )
                    return {"operation": operation, "success": True, "data": result}
                else:
                    return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return webhook_callback
    
    def _create_status_callback(self, status_service):
        """Create callback for status management operations"""
        async def status_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                if operation == "send_status_notification":
                    # Use existing callback manager
                    await status_service["callback_manager"].send_callback(
                        callback_type=payload.get("callback_type", "status_change"),
                        data=payload.get("data", {})
                    )
                    return {"operation": operation, "success": True, "data": {"sent": True}}
                else:
                    return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return status_callback
    
    def _create_validation_callback(self, validation_service):
        """Create callback for validation operations"""
        async def validation_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return validation_callback
    
    def _create_transmission_callback(self, transmission_service):
        """Create callback for transmission operations"""
        async def transmission_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return transmission_callback
    
    def _create_security_callback(self, security_service):
        """Create callback for security operations"""
        async def security_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                if operation == "encrypt_document":
                    # Use encryption service
                    document = payload.get("document", "")
                    encrypted = security_service["encryption_service"].encrypt_sensitive_data(document)
                    return {"operation": operation, "success": True, "data": {"encrypted": encrypted}}
                elif operation == "log_security_event":
                    # Use audit logger
                    event = payload.get("event", {})
                    security_service["audit_logger"].log_security_event(event)
                    return {"operation": operation, "success": True, "data": {"logged": True}}
                else:
                    return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return security_callback
    
    def _create_auth_seals_callback(self, auth_service):
        """Create callback for authentication seals operations"""
        async def auth_seals_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                if operation == "generate_digital_seal":
                    # Use seal generator
                    document = payload.get("document", "")
                    seal = auth_service["seal_generator"].generate_digital_seal(document)
                    return {"operation": operation, "success": True, "data": {"seal": seal}}
                elif operation == "verify_document":
                    # Use verification service
                    document = payload.get("document", "")
                    signature = payload.get("signature", "")
                    verified = auth_service["verification_service"].verify_document_authenticity(document, signature)
                    return {"operation": operation, "success": True, "data": {"verified": verified}}
                else:
                    return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return auth_seals_callback
    
    def _create_reporting_callback(self, reporting_service):
        """Create callback for reporting operations"""
        async def reporting_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                if operation == "generate_transmission_report":
                    # Use transmission reporter
                    report_config = payload.get("config", {})
                    report = reporting_service["transmission_reporter"].generate_transmission_report(report_config)
                    return {"operation": operation, "success": True, "data": {"report": report}}
                elif operation == "monitor_compliance":
                    # Use compliance monitor
                    metrics = reporting_service["compliance_monitor"].get_compliance_metrics()
                    return {"operation": operation, "success": True, "data": {"metrics": metrics}}
                else:
                    return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return reporting_callback
    
    def _create_taxpayer_callback(self, taxpayer_service):
        """Create callback for taxpayer management operations"""
        async def taxpayer_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                if operation == "onboard_taxpayer":
                    # Use onboarding service
                    taxpayer_data = payload.get("taxpayer_data", {})
                    result = taxpayer_service["onboarding_service"].onboard_taxpayer(taxpayer_data)
                    return {"operation": operation, "success": True, "data": {"result": result}}
                else:
                    return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return taxpayer_callback
    
    def _create_firs_callback(self, firs_service):
        """Create callback for FIRS communication operations"""
        async def firs_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                # Utilities
                http_client = firs_service.get("http_client")
                resource_cache = firs_service.get("resource_cache")

                if operation == "receive_invoices_from_si":
                    # Handle receiving invoices from SI for FIRS submission
                    invoice_ids = payload.get("invoice_ids", [])
                    si_user_id = payload.get("si_user_id")
                    submission_options = payload.get("submission_options", {})
                    
                    logger.info(f"Received {len(invoice_ids)} invoices from SI user {si_user_id}")
                    
                    # Process invoices for FIRS submission
                    submission_result = await self._process_si_invoices_for_firs(
                        invoice_ids, si_user_id, submission_options
                    )
                    
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "submission_id": submission_result.get("submission_id"),
                            "processed_count": len(invoice_ids),
                            "status": "submitted_to_firs"
                        }
                    }
                    
                elif operation == "receive_invoice_batch_from_si":
                    # Handle receiving invoice batch from SI
                    batch_id = payload.get("batch_id")
                    si_user_id = payload.get("si_user_id")
                    batch_options = payload.get("batch_options", {})
                    
                    logger.info(f"Received invoice batch {batch_id} from SI user {si_user_id}")
                    
                    # Process batch for FIRS submission
                    batch_result = await self._process_si_batch_for_firs(
                        batch_id, si_user_id, batch_options
                    )
                    
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "batch_submission_id": batch_result.get("batch_submission_id"),
                            "batch_status": "submitted_to_firs"
                        }
                    }

                elif operation == "submit_to_firs":
                    # Submit flow using header-based endpoints: sign -> transmit
                    if not http_client:
                        return {"operation": operation, "success": False, "error": "http_client_unavailable"}
                    invoice_data = payload.get("invoice_data", {})
                    irn = invoice_data.get("irn") or payload.get("irn")
                    sign_resp = await http_client.sign_invoice(invoice_data)
                    if not sign_resp.get("success"):
                        return {"operation": operation, "success": False, "data": {"sign": sign_resp}}
                    if not irn and isinstance(sign_resp.get("data"), dict):
                        irn = sign_resp["data"].get("irn") or irn
                    if not irn:
                        return {"operation": operation, "success": False, "error": "missing_irn_for_transmit"}
                    tx_resp = await http_client.transmit(irn)
                    success = sign_resp.get("success", False) and tx_resp.get("success", False)
                    return {"operation": operation, "success": success, "data": {"sign": sign_resp, "transmit": tx_resp}}

                elif operation == "validate_invoice_for_firs":
                    # Validate invoice via thin HTTP client
                    if not http_client:
                        return {"operation": operation, "success": False, "error": "http_client_unavailable"}
                    data = payload.get("validation_data") or payload.get("submission_data") or {}
                    resp = await http_client.validate_invoice(data)
                    return {"operation": operation, "success": resp.get("success", False), "data": resp}

                elif operation == "validate_invoice_batch_for_firs":
                    # Validate invoices in a batch (map each item)
                    if not http_client:
                        return {"operation": operation, "success": False, "error": "http_client_unavailable"}
                    batch = payload.get("validation_data") or payload.get("batch_data") or []
                    results = []
                    overall = True
                    if isinstance(batch, dict) and "invoices" in batch:
                        batch = batch["invoices"]
                    for item in (batch or []):
                        resp = await http_client.validate_invoice(item)
                        overall = overall and resp.get("success", False)
                        results.append(resp)
                    return {"operation": operation, "success": overall, "data": {"results": results}}

                elif operation == "get_firs_validation_rules":
                    # Use resource cache to return consolidated rules metadata
                    if not resource_cache:
                        return {"operation": operation, "success": False, "error": "resource_cache_unavailable"}
                    resources = await resource_cache.get_resources()
                    return {"operation": operation, "success": True, "data": {"resources": resources}}

                elif operation == "process_firs_webhook":
                    # Process FIRS webhook events
                    result = await self._handle_firs_webhook(payload)
                    return {"operation": operation, "success": True, "data": {"result": result}}
                    
                elif operation == "get_submission_status":
                    # Interpret submission_id as IRN and lookup transmit status
                    if not http_client:
                        return {"operation": operation, "success": False, "error": "http_client_unavailable"}
                    irn = payload.get("submission_id") or payload.get("irn")
                    if not irn:
                        return {"operation": operation, "success": False, "error": "missing_irn"}
                    resp = await http_client.lookup_transmit_by_irn(irn)
                    return {"operation": operation, "success": resp.get("success", False), "data": resp}

                elif operation == "update_firs_invoice":
                    if not http_client:
                        return {"operation": operation, "success": False, "error": "http_client_unavailable"}
                    upd = payload.get("invoice_update", {})
                    irn = upd.get("invoice_id") or upd.get("irn")
                    update_data = upd.get("update_data", {})
                    if not irn:
                        return {"operation": operation, "success": False, "error": "missing_irn"}
                    resp = await http_client.update_invoice(irn, update_data)
                    return {"operation": operation, "success": resp.get("success", False), "data": resp}

                elif operation == "transmit_firs_invoice":
                    if not http_client:
                        return {"operation": operation, "success": False, "error": "http_client_unavailable"}
                    irn = payload.get("irn")
                    if not irn:
                        return {"operation": operation, "success": False, "error": "missing_irn"}
                    resp = await http_client.transmit(irn, payload.get("options"))
                    return {"operation": operation, "success": resp.get("success", False), "data": resp}

                elif operation == "confirm_firs_receipt":
                    if not http_client:
                        return {"operation": operation, "success": False, "error": "http_client_unavailable"}
                    irn = payload.get("irn")
                    if not irn:
                        return {"operation": operation, "success": False, "error": "missing_irn"}
                    resp = await http_client.confirm_receipt(irn, payload.get("options"))
                    return {"operation": operation, "success": resp.get("success", False), "data": resp}
                    
                else:
                    return {"operation": operation, "success": True, "data": {"status": "placeholder"}}

            except Exception as e:
                logger.error(f"Error in FIRS operation {operation}: {str(e)}")
                return {"operation": operation, "success": False, "error": str(e)}

        return firs_callback
    
    async def _process_si_invoices_for_firs(self, invoice_ids, si_user_id, submission_options):
        """Process invoices received from SI for FIRS submission"""
        try:
            # This would fetch invoice data from SI and submit to FIRS
            logger.info(f"Processing {len(invoice_ids)} invoices for FIRS submission")
            
            # Generate submission ID
            from datetime import datetime
            submission_id = f"FIRS-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}-{len(invoice_ids)}"
            
            # Mock processing - in real implementation:
            # 1. Fetch invoice data from SI database
            # 2. Validate FIRS compliance
            # 3. Submit to FIRS API
            # 4. Track submission status
            
            return {
                "submission_id": submission_id,
                "status": "submitted",
                "submitted_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing SI invoices for FIRS: {str(e)}")
            raise
    
    async def _process_si_batch_for_firs(self, batch_id, si_user_id, batch_options):
        """Process invoice batch received from SI for FIRS submission"""
        try:
            logger.info(f"Processing batch {batch_id} for FIRS submission")
            
            # Generate batch submission ID
            from datetime import datetime
            batch_submission_id = f"FIRS-BATCH-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}"
            
            # Mock batch processing - in real implementation:
            # 1. Fetch batch data from SI
            # 2. Validate batch compliance
            # 3. Submit batch to FIRS
            # 4. Track batch status
            
            return {
                "batch_submission_id": batch_submission_id,
                "status": "submitted",
                "submitted_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing SI batch for FIRS: {str(e)}")
            raise
    
    async def _handle_firs_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle FIRS webhook processing"""
        try:
            event_type = payload.get("event_type")
            submission_id = payload.get("submission_id")
            
            logger.info(f"Processing FIRS webhook: {event_type} for submission: {submission_id}")
            
            # Process the webhook event
            result = {
                "event_type": event_type,
                "submission_id": submission_id,
                "processed_at": payload.get("timestamp"),
                "status": "processed"
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling FIRS webhook: {str(e)}")
            raise
    
    async def _handle_status_update(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle FIRS submission status update"""
        try:
            submission_id = payload.get("submission_id")
            new_status = payload.get("new_status")
            
            logger.info(f"Updating submission {submission_id} status to {new_status}")
            
            # Update status in database (placeholder - would use actual database service)
            result = {
                "submission_id": submission_id,
                "old_status": "PROCESSING",
                "new_status": new_status,
                "updated_at": payload.get("updated_at"),
                "success": True
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error updating submission status: {str(e)}")
            raise
    
    async def get_service_health(self) -> Dict[str, Any]:
        """Get health status of all registered APP services"""
        health_status = {
            "registry_status": "healthy" if self.is_initialized else "uninitialized",
            "total_services": len(self.services),
            "registered_endpoints": len(self.service_endpoints),
            "services": {}
        }
        
        # Check service health
        for service_name in self.services:
            try:
                health_status["services"][service_name] = {
                    "status": "healthy",
                    "endpoint": self.service_endpoints.get(service_name, "not_registered")
                }
            except Exception as e:
                health_status["services"][service_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return health_status
    
    async def cleanup_services(self):
        """Cleanup all services and unregister from message router"""
        try:
            logger.info("Cleaning up APP services...")
            
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
            
            logger.info("APP services cleanup completed")
            
        except Exception as e:
            logger.error(f"APP services cleanup failed: {str(e)}")


# Global service registry instance
_app_service_registry: Optional[APPServiceRegistry] = None


async def initialize_app_services(message_router: MessageRouter) -> APPServiceRegistry:
    """
    Initialize APP services with message router.
    
    Args:
        message_router: Core platform message router
        
    Returns:
        Initialized service registry
    """
    global _app_service_registry
    
    if _app_service_registry is None:
        _app_service_registry = APPServiceRegistry(message_router)
        await _app_service_registry.initialize_services()
    
    return _app_service_registry


def get_app_service_registry() -> Optional[APPServiceRegistry]:
    """Get the global APP service registry instance"""
    return _app_service_registry


async def cleanup_app_services():
    """Cleanup APP services"""
    global _app_service_registry
    
    if _app_service_registry:
        await _app_service_registry.cleanup_services()
        _app_service_registry = None
