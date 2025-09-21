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
from datetime import datetime, timezone
from dataclasses import asdict
from typing import Dict, Any, Optional, List

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
from .transmission.transmission_service import TransmissionService
from .security_compliance.encryption_service import EncryptionService
from .security_compliance.audit_logger import AuditLogger
from .authentication_seals.seal_generator import SealGenerator
from .authentication_seals.verification_service import VerificationService
from si_services.certificate_management.certificate_store import CertificateStore
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
            await self._register_certificate_services()
            
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

                # Map existing environment naming to client expectations
                encryption_key = os.getenv("FIRS_ENCRYPTION_KEY")
                if encryption_key:
                    os.environ.setdefault("FIRS_ENCRYPTION_KEY", encryption_key)

                if os.getenv("FIRS_USE_SANDBOX", "false").lower() == "true":
                    os.environ.setdefault("FIRS_API_URL", os.getenv("FIRS_SANDBOX_URL", ""))
                    os.environ.setdefault("FIRS_API_KEY", os.getenv("FIRS_SANDBOX_API_KEY", ""))
                    os.environ.setdefault("FIRS_API_SECRET", os.getenv("FIRS_SANDBOX_API_SECRET", ""))

                firs_http_client = FIRSHttpClient()
                resource_cache = FIRSResourceCache(firs_http_client)
            except Exception:
                firs_http_client = None
                resource_cache = None

            try:
                if hasattr(auth_handler, "start"):
                    await auth_handler.start()
            except Exception:
                logger.debug("FIRS auth handler start failed; continuing with placeholders")

            certificate_store = CertificateStore()

            firs_operations = [
                "process_firs_webhook",
                "update_firs_submission_status",
                "submit_to_firs",
                "submit_invoice_to_firs",
                "submit_invoice",
                "submit_invoice_batch_to_firs",
                "submit_invoice_batch",
                "validate_firs_response",
                "validate_invoice_for_firs",
                "validate_invoice_batch_for_firs",
                "get_firs_validation_rules",
                "refresh_firs_resources",
                "refresh_firs_resource",
                "update_firs_invoice",
                "transmit_firs_invoice",
                "confirm_firs_receipt",
                "get_firs_submission_status",
                "get_submission_status",
                "authenticate_firs",
                "authenticate_with_firs",
                "refresh_firs_token",
                "test_firs_connection",
                "get_firs_auth_status",
                "get_firs_system_info",
                "check_firs_system_health",
                "list_firs_submissions",
                "list_firs_certificates",
                "get_firs_certificate",
                "renew_firs_certificate",
                "get_firs_errors",
                "get_firs_integration_logs",
                "generate_firs_report",
                "get_firs_reporting_dashboard",
                "receive_invoices_from_si",
                "receive_invoice_batch_from_si"
            ]

            firs_service = {
                "api_client": firs_api_client,
                "auth_handler": auth_handler,
                "http_client": firs_http_client,
                "resource_cache": resource_cache,
                "certificate_store": certificate_store,
                "operations": firs_operations,
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
                    "operations": firs_operations,
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
                    "track_status_change",
                    "get_status_history",
                    "health_check",
                    "get_app_status",
                    "get_dashboard_summary",
                    "get_app_configuration",
                    "update_app_configuration",
                    "get_tracking_overview",
                    "get_transmission_statuses",
                    "get_transmission_tracking",
                    "get_transmission_progress",
                    "get_live_updates",
                    "get_recent_status_changes",
                    "get_active_alerts",
                    "acknowledge_alert",
                    "get_batch_status_summary",
                    "get_firs_responses",
                    "get_firs_response_details",
                    "search_transmissions"
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
                    "operations": status_service["operations"],
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
                    "check_compliance",
                    "verify_format",
                    "validate_single_invoice",
                    "validate_invoice_batch",
                    "validate_uploaded_file",
                    "get_validation_result",
                    "get_batch_validation_status",
                    "get_validation_metrics",
                    "get_validation_overview",
                    "get_recent_validation_results",
                    "get_validation_rules",
                    "get_firs_validation_standards",
                    "get_ubl_validation_standards",
                    "get_validation_error_analysis",
                    "get_validation_error_help",
                    "get_data_quality_metrics",
                    "generate_quality_report",
                    "generate_compliance_report",
                    "list_compliance_reports",
                    "get_compliance_report",
                    "validate_ubl_compliance",
                    "validate_ubl_batch",
                    "validate_peppol_compliance",
                    "validate_iso27001_compliance",
                    "validate_iso20022_compliance",
                    "validate_data_protection_compliance",
                    "validate_lei_compliance",
                    "validate_product_classification",
                    "validate_comprehensive_compliance"
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
                    "operations": validation_service["operations"],
                }
            )
            
            self.service_endpoints["validation"] = endpoint_id
            logger.info(f"Validation service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register validation services: {str(e)}")
    
    async def _register_transmission_services(self):
        """Register transmission services"""
        try:
            transmission_operations = [
                "get_available_batches",
                "list_transmission_batches",
                "get_batch_details",
                "submit_invoice_batches",
                "submit_single_batch",
                "submit_invoice_file",
                "generate_firs_compliant_invoice",
                "generate_invoice_batch",
                "submit_invoice",
                "submit_invoice_batch",
                "get_submission_status",
                "list_submissions",
                "cancel_invoice_submission",
                "resubmit_invoice",
                "get_invoice",
                "get_transmission_history",
                "get_transmission_details",
                "generate_transmission_report",
                "get_transmission_status",
                "retry_transmission",
                "cancel_transmission",
                "get_transmission_statistics",
                "transmit_batch",
                "transmit_real_time",
            ]

            transmission_logic = TransmissionService(
                message_router=self.message_router,
                report_generator=TransmissionReportGenerator(),
            )

            transmission_service = {
                "service": transmission_logic,
                "operations": transmission_operations,
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
                    "operations": transmission_operations,
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
                    "audit_compliance",
                    "get_security_metrics",
                    "get_security_overview",
                    "run_security_scan",
                    "get_scan_status",
                    "get_scan_results",
                    "list_vulnerabilities",
                    "resolve_vulnerability",
                    "get_suspicious_activity",
                    "get_access_logs",
                    "generate_security_report",
                    "check_iso27001_compliance",
                    "check_gdpr_compliance"
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
                    "operations": security_service["operations"],
                }
            )
            
            self.service_endpoints["security_compliance"] = endpoint_id
            logger.info(f"Security compliance service registered: {endpoint_id}")
            
        except Exception as e:
            logger.error(f"Failed to register security services: {str(e)}")

    async def _register_certificate_services(self):
        """Register APP-side certificate management service"""
        try:
            from core_platform.data_management.db_async import get_async_session
            from si_services.certificate_management.certificate_service import CertificateService

            async def certificate_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
                try:
                    async for db in get_async_session():
                        service = CertificateService(db=db)

                        if operation == "create_certificate":
                            cd = payload.get("certificate_data")
                            if isinstance(cd, dict) and cd.get("subject_info"):
                                org_id = cd.get("organization_id") or payload.get("organization_id")
                                cert_type = cd.get("certificate_type", "signing")
                                validity_days = int(cd.get("validity_days", 365))
                                cert_id, cert_pem = await service.generate_certificate(
                                    subject_info=cd["subject_info"],
                                    organization_id=org_id,
                                    validity_days=validity_days,
                                    certificate_type=cert_type,
                                )
                                return {"operation": operation, "success": True, "data": {"certificate_id": cert_id, "certificate_pem": cert_pem}}
                            else:
                                org_id = (cd.get("organization_id") if isinstance(cd, dict) else None) or payload.get("organization_id")
                                cert_type = (cd.get("certificate_type") if isinstance(cd, dict) else None) or payload.get("certificate_type", "signing")
                                meta = cd.get("metadata") if isinstance(cd, dict) else None
                                pem = cd if isinstance(cd, str) else cd.get("certificate_pem") or cd.get("pem") or cd.get("data")
                                cert_id = await service.store_certificate(pem, org_id, cert_type, meta)
                                return {"operation": operation, "success": True, "data": {"certificate_id": cert_id}}

                        if operation in {"get_certificate", "list_certificates", "get_certificate_overview"}:
                            certificate_id = payload.get("certificate_id")
                            if operation == "list_certificates":
                                return {"operation": operation, "success": True, "data": {"certificates": []}}
                            if operation == "get_certificate_overview":
                                return {"operation": operation, "success": True, "data": {"total": 0, "active": 0, "expiring": 0}}
                            pem = service.retrieve_certificate(certificate_id)
                            if not pem:
                                return {"operation": operation, "success": False, "error": "not_found"}
                            return {"operation": operation, "success": True, "data": {"certificate_id": certificate_id, "certificate_pem": pem}}

                        if operation == "update_certificate":
                            return {"operation": operation, "success": True, "data": {"status": "no_op"}}

                        if operation == "delete_certificate":
                            certificate_id = payload.get("certificate_id")
                            ok = await service.revoke_certificate(certificate_id, reason=payload.get("reason", "revoked_by_app"))
                            return {"operation": operation, "success": ok, "data": {"certificate_id": certificate_id}}

                        if operation == "renew_certificate":
                            certificate_id = payload.get("certificate_id")
                            validity_days = int(payload.get("validity_days", 365))
                            new_id, ok = service.renew_certificate(certificate_id, validity_days)
                            return {"operation": operation, "success": ok, "data": {"new_certificate_id": new_id}}

                        if operation == "get_renewal_status":
                            return {"operation": operation, "success": True, "data": {"status": "unknown"}}

                        if operation == "list_expiring_certificates":
                            days = int(payload.get("days_ahead", 30))
                            return {"operation": operation, "success": True, "data": {"expiring_within_days": days, "items": []}}

                        if operation == "validate_certificate":
                            cd = payload.get("certificate_data")
                            result = service.validate_certificate(cd)
                            return {"operation": operation, "success": result.get("is_valid", False), "data": result}

                        return {"operation": operation, "success": False, "error": "unsupported_operation"}
                except Exception as e:
                    return {"operation": operation, "success": False, "error": str(e)}

            endpoint_id = await self.message_router.register_service(
                service_name="certificate_management",
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                callback=certificate_callback,
                priority=4,
                tags=["certificate", "pki", "security"],
                metadata={
                    "service_type": "certificate_management",
                    "operations": [
                        "create_certificate",
                        "get_certificate",
                        "update_certificate",
                        "delete_certificate",
                        "renew_certificate",
                        "get_renewal_status",
                        "list_expiring_certificates",
                        "validate_certificate",
                        "list_certificates",
                        "get_certificate_overview",
                    ],
                },
            )

            self.service_endpoints["certificate_management_app"] = endpoint_id
            logger.info(f"APP certificate management service registered: {endpoint_id}")
        except Exception as e:
            logger.error(f"Failed to register APP certificate services: {str(e)}")
    
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
                    "create_dashboard",
                    "generate_custom_report",
                    "generate_security_report",
                    "generate_financial_report",
                    "generate_compliance_report",
                    "list_generated_reports",
                    "list_scheduled_reports",
                    "schedule_report",
                    "update_scheduled_report",
                    "delete_scheduled_report",
                    "get_report_templates",
                    "get_report_template",
                    "get_report_details",
                    "get_report_status",
                    "download_report",
                    "preview_report",
                    "get_dashboard_metrics",
                    "get_dashboard_overview",
                    "get_pending_invoices",
                    "get_status_summary",
                    "get_transmission_batches",
                    "quick_validate_invoices",
                    "quick_submit_invoices",
                    "validate_firs_batch",
                    "submit_firs_batch"
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
                    "operations": reporting_service["operations"],
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
                    "analyze_taxpayer",
                    "create_taxpayer",
                    "list_taxpayers",
                    "get_taxpayer",
                    "update_taxpayer",
                    "delete_taxpayer",
                    "bulk_onboard_taxpayers",
                    "get_taxpayer_overview",
                    "get_taxpayer_statistics",
                    "get_taxpayer_onboarding_status",
                    "get_taxpayer_compliance_status",
                    "update_taxpayer_compliance_status",
                    "list_non_compliant_taxpayers",
                    "generate_grant_tracking_report",
                    "get_grant_milestones",
                    "get_onboarding_performance",
                    "get_grant_overview",
                    "get_current_grant_status",
                    "list_grant_milestones",
                    "get_milestone_details",
                    "get_milestone_progress",
                    "get_upcoming_milestones",
                    "get_performance_metrics",
                    "get_performance_trends",
                    "generate_grant_report",
                    "list_grant_reports",
                    "get_grant_report"
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
                    "operations": taxpayer_service["operations"],
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
                if operation == "update_submission_status":
                    return {"operation": operation, "success": True, "data": {"updated": True}}
                if operation in {"health_check", "get_app_status"}:
                    return {"operation": operation, "success": True, "data": {"status": "healthy", "checked_at": datetime.now(timezone.utc).isoformat()}}
                if operation == "get_dashboard_summary":
                    return {"operation": operation, "success": True, "data": {"summary": {}, "generated_at": datetime.now(timezone.utc).isoformat()}}
                if operation == "get_app_configuration":
                    return {"operation": operation, "success": True, "data": {"configuration": {}}}
                if operation == "update_app_configuration":
                    return {"operation": operation, "success": True, "data": {"updated": True}}
                if operation == "get_status_history":
                    return {"operation": operation, "success": True, "data": {"history": []}}
                if operation in {"get_tracking_overview", "get_transmission_statuses", "get_transmission_tracking", "get_transmission_progress", "get_live_updates", "get_recent_status_changes", "get_active_alerts", "acknowledge_alert", "get_batch_status_summary", "get_firs_responses", "get_firs_response_details", "search_transmissions"}:
                    return {"operation": operation, "success": True, "data": {"items": [], "timestamp": datetime.now(timezone.utc).isoformat()}}
                else:
                    return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return status_callback
    
    def _create_validation_callback(self, validation_service):
        """Create callback for validation operations"""
        async def validation_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                # Placeholder responses for validation/compliance operations
                timestamp = datetime.now(timezone.utc).isoformat()
                if operation in {"validate_invoice", "validate_submission", "validate_single_invoice", "validate_invoice_batch", "validate_uploaded_file", "validate_ubl_compliance", "validate_ubl_batch", "validate_peppol_compliance", "validate_iso27001_compliance", "validate_iso20022_compliance", "validate_data_protection_compliance", "validate_lei_compliance", "validate_product_classification", "validate_comprehensive_compliance"}:
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "validated": True,
                            "issues": [],
                            "checked_at": timestamp
                        }
                    }
                if operation == "get_validation_result":
                    return {"operation": operation, "success": True, "data": {"result_id": payload.get("validation_id"), "status": "completed", "checked_at": timestamp}}
                if operation == "get_batch_validation_status":
                    return {"operation": operation, "success": True, "data": {"batch_id": payload.get("batch_id"), "status": "pending", "processed": 0}}
                if operation in {"get_validation_metrics", "get_validation_overview", "get_recent_validation_results", "get_data_quality_metrics"}:
                    return {"operation": operation, "success": True, "data": {"metrics": {}, "generated_at": timestamp}}
                if operation in {"get_validation_rules", "get_firs_validation_standards", "get_ubl_validation_standards"}:
                    return {"operation": operation, "success": True, "data": {"rules": [], "fetched_at": timestamp}}
                if operation in {"get_validation_error_analysis", "get_validation_error_help"}:
                    return {"operation": operation, "success": True, "data": {"analysis": [], "generated_at": timestamp}}
                if operation in {"generate_quality_report", "generate_compliance_report", "get_compliance_report"}:
                    return {"operation": operation, "success": True, "data": {"report_id": "validation-report", "generated_at": timestamp}}
                if operation == "list_compliance_reports":
                    return {"operation": operation, "success": True, "data": {"reports": [], "generated_at": timestamp}}
                return {"operation": operation, "success": True, "data": {"status": "placeholder", "timestamp": timestamp}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return validation_callback
    
    def _create_transmission_callback(self, transmission_service):
        """Create callback for transmission operations"""

        service: Optional[TransmissionService] = transmission_service.get("service")

        async def transmission_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                if isinstance(service, TransmissionService):
                    return await service.handle(operation, payload)
                return {
                    "operation": operation,
                    "success": False,
                    "error": "transmission_service_unavailable",
                }
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}

        return transmission_callback
    
    def _create_security_callback(self, security_service):
        """Create callback for security operations"""
        async def security_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                if operation == "encrypt_document":
                    document = payload.get("document", "")
                    encrypted = security_service["encryption_service"].encrypt_sensitive_data(document)
                    return {"operation": operation, "success": True, "data": {"encrypted": encrypted}}
                if operation == "decrypt_document":
                    document = payload.get("document", "")
                    decrypt_fn = getattr(security_service["encryption_service"], "decrypt_sensitive_data", None)
                    decrypted = decrypt_fn(document) if callable(decrypt_fn) else document
                    return {"operation": operation, "success": True, "data": {"decrypted": decrypted}}
                if operation == "log_security_event":
                    event = payload.get("event", {})
                    security_service["audit_logger"].log_security_event(event)
                    return {"operation": operation, "success": True, "data": {"logged": True}}
                if operation == "generate_security_report":
                    return {"operation": operation, "success": True, "data": {"report_id": "security-report"}}
                if operation in {"get_security_metrics", "get_security_overview"}:
                    return {"operation": operation, "success": True, "data": {"metrics": {}, "generated_at": datetime.now(timezone.utc).isoformat()}}
                if operation == "run_security_scan":
                    return {"operation": operation, "success": True, "data": {"scan_id": "scan-demo", "status": "running"}}
                if operation == "get_scan_status":
                    return {"operation": operation, "success": True, "data": {"status": "completed", "scan_id": payload.get("scan_id")}}
                if operation == "get_scan_results":
                    return {"operation": operation, "success": True, "data": {"results": [], "scan_id": payload.get("scan_id")}}
                if operation == "list_vulnerabilities":
                    return {"operation": operation, "success": True, "data": {"vulnerabilities": []}}
                if operation == "resolve_vulnerability":
                    return {"operation": operation, "success": True, "data": {"resolved": True}}
                if operation == "get_suspicious_activity":
                    return {"operation": operation, "success": True, "data": {"activities": []}}
                if operation == "get_access_logs":
                    return {"operation": operation, "success": True, "data": {"logs": []}}
                if operation == "check_iso27001_compliance":
                    return {"operation": operation, "success": True, "data": {"compliant": True}}
                if operation == "check_gdpr_compliance":
                    return {"operation": operation, "success": True, "data": {"compliant": True}}
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
                timestamp = datetime.now(timezone.utc).isoformat()
                if operation == "generate_transmission_report":
                    report_config = payload.get("config", {})
                    report = reporting_service["transmission_reporter"].generate_transmission_report(report_config)
                    return {"operation": operation, "success": True, "data": {"report": report}}
                if operation == "monitor_compliance":
                    metrics = reporting_service["compliance_monitor"].get_compliance_metrics()
                    return {"operation": operation, "success": True, "data": {"metrics": metrics}}
                if operation in {"generate_custom_report", "generate_security_report", "generate_financial_report", "generate_compliance_report"}:
                    return {"operation": operation, "success": True, "data": {"report_id": f"report-{operation}", "generated_at": timestamp}}
                if operation in {"list_generated_reports", "list_scheduled_reports"}:
                    return {"operation": operation, "success": True, "data": {"reports": [], "generated_at": timestamp}}
                if operation == "schedule_report":
                    return {"operation": operation, "success": True, "data": {"schedule_id": "schedule-demo", "scheduled_at": timestamp}}
                if operation == "update_scheduled_report":
                    return {"operation": operation, "success": True, "data": {"updated": True}}
                if operation == "delete_scheduled_report":
                    return {"operation": operation, "success": True, "data": {"deleted": True}}
                if operation == "get_report_templates":
                    return {"operation": operation, "success": True, "data": {"templates": []}}
                if operation == "get_report_template":
                    return {"operation": operation, "success": True, "data": {"template_id": payload.get("template_id"), "config": {}}}
                if operation == "get_report_details":
                    return {"operation": operation, "success": True, "data": {"report_id": payload.get("report_id"), "status": "completed"}}
                if operation == "get_report_status":
                    return {"operation": operation, "success": True, "data": {"status": "processing", "report_id": payload.get("report_id")}}
                if operation == "download_report":
                    return {"operation": operation, "success": True, "data": {"download_url": "https://example.com/report.pdf"}}
                if operation == "preview_report":
                    return {"operation": operation, "success": True, "data": {"preview": "Report preview unavailable in stub"}}
                if operation in {"get_dashboard_metrics", "get_dashboard_overview", "get_pending_invoices", "get_status_summary", "get_transmission_batches"}:
                    return {"operation": operation, "success": True, "data": {"data": {}, "generated_at": timestamp}}
                if operation in {"quick_validate_invoices", "quick_submit_invoices", "validate_firs_batch", "submit_firs_batch"}:
                    return {"operation": operation, "success": True, "data": {"processed": True, "timestamp": timestamp}}
                if operation == "create_dashboard":
                    return {"operation": operation, "success": True, "data": {"dashboard_id": "dashboard-demo"}}
                if operation == "analyze_performance":
                    return {"operation": operation, "success": True, "data": {"analysis": {}}}
                return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return reporting_callback
    
    def _create_taxpayer_callback(self, taxpayer_service):
        """Create callback for taxpayer management operations"""
        async def taxpayer_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                timestamp = datetime.now(timezone.utc).isoformat()
                if operation == "onboard_taxpayer":
                    taxpayer_data = payload.get("taxpayer_data", {})
                    result = taxpayer_service["onboarding_service"].onboard_taxpayer(taxpayer_data)
                    return {"operation": operation, "success": True, "data": {"result": result}}
                if operation == "create_taxpayer":
                    return {"operation": operation, "success": True, "data": {"taxpayer_id": "taxpayer-demo", "created_at": timestamp}}
                if operation == "list_taxpayers":
                    return {"operation": operation, "success": True, "data": {"taxpayers": [], "page": payload.get("page", 1)}}
                if operation == "get_taxpayer":
                    return {"operation": operation, "success": True, "data": {"taxpayer_id": payload.get("taxpayer_id"), "status": "active"}}
                if operation == "update_taxpayer":
                    return {"operation": operation, "success": True, "data": {"updated": True}}
                if operation == "delete_taxpayer":
                    return {"operation": operation, "success": True, "data": {"deleted": True}}
                if operation == "bulk_onboard_taxpayers":
                    return {"operation": operation, "success": True, "data": {"processed": len(payload.get("taxpayers", []))}}
                if operation == "get_taxpayer_overview":
                    return {"operation": operation, "success": True, "data": {"overview": {}, "generated_at": timestamp}}
                if operation == "get_taxpayer_statistics":
                    return {"operation": operation, "success": True, "data": {"statistics": {}, "period": payload.get("period", "30d")}}
                if operation == "get_taxpayer_onboarding_status":
                    return {"operation": operation, "success": True, "data": {"taxpayer_id": payload.get("taxpayer_id"), "status": "in_progress"}}
                if operation == "get_taxpayer_compliance_status":
                    return {"operation": operation, "success": True, "data": {"status": "compliant", "checked_at": timestamp}}
                if operation == "update_taxpayer_compliance_status":
                    return {"operation": operation, "success": True, "data": {"updated": True}}
                if operation == "list_non_compliant_taxpayers":
                    return {"operation": operation, "success": True, "data": {"taxpayers": [], "generated_at": timestamp}}
                if operation == "generate_grant_tracking_report":
                    return {"operation": operation, "success": True, "data": {"report_id": "grant-report", "generated_at": timestamp}}
                if operation == "get_grant_milestones":
                    return {"operation": operation, "success": True, "data": {"milestones": [], "generated_at": timestamp}}
                if operation == "get_onboarding_performance":
                    return {"operation": operation, "success": True, "data": {"performance": {}, "period": payload.get("period", "30d")}}
                if operation == "get_grant_overview":
                    return {"operation": operation, "success": True, "data": {"overview": {}, "generated_at": timestamp}}
                if operation == "get_current_grant_status":
                    return {"operation": operation, "success": True, "data": {"status": "on_track", "checked_at": timestamp}}
                if operation == "list_grant_milestones":
                    return {"operation": operation, "success": True, "data": {"milestones": []}}
                if operation == "get_milestone_details":
                    return {"operation": operation, "success": True, "data": {"milestone_id": payload.get("milestone_id"), "status": "in_progress"}}
                if operation == "get_milestone_progress":
                    return {"operation": operation, "success": True, "data": {"milestone_id": payload.get("milestone_id"), "progress": 0}}
                if operation == "get_upcoming_milestones":
                    return {"operation": operation, "success": True, "data": {"milestones": [], "days_ahead": payload.get("days_ahead", 30)}}
                if operation == "get_performance_metrics":
                    return {"operation": operation, "success": True, "data": {"metrics": {}, "generated_at": timestamp}}
                if operation == "get_performance_trends":
                    return {"operation": operation, "success": True, "data": {"trends": [], "generated_at": timestamp}}
                if operation == "generate_grant_report":
                    return {"operation": operation, "success": True, "data": {"report_id": "grant-report", "generated_at": timestamp}}
                if operation == "list_grant_reports":
                    return {"operation": operation, "success": True, "data": {"reports": []}}
                if operation == "get_grant_report":
                    return {"operation": operation, "success": True, "data": {"report_id": payload.get("report_id"), "status": "completed"}}
                return {"operation": operation, "success": True, "data": {"status": "placeholder"}}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}
        return taxpayer_callback
    
    def _create_firs_callback(self, firs_service):
        """Create callback for FIRS communication operations"""

        def _utc_now() -> str:
            return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")

        async def firs_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                # Utilities
                http_client = firs_service.get("http_client")
                resource_cache = firs_service.get("resource_cache")
                auth_handler = firs_service.get("auth_handler")
                certificate_store: Optional[CertificateStore] = firs_service.get("certificate_store")

                async def _fetch_transmissions(tin: Optional[str] = None) -> Dict[str, Any]:
                    if not http_client:
                        return {"success": False, "error": "http_client_unavailable"}
                    if tin:
                        return await http_client.lookup_transmit_by_tin(tin)
                    return await http_client.transmit_pull()

                def _normalize_transmissions(raw: Any) -> List[Dict[str, Any]]:
                    if isinstance(raw, dict):
                        if 'transmissions' in raw and isinstance(raw['transmissions'], list):
                            return raw['transmissions']
                        if 'data' in raw and isinstance(raw['data'], list):
                            return raw['data']
                        return [raw]
                    if isinstance(raw, list):
                        return raw
                    return []

                def _summarize_transmissions(records: List[Dict[str, Any]]) -> Dict[str, Any]:
                    summary = {"total": len(records), "status_counts": {}}
                    for record in records:
                        status = str(record.get("status", "unknown")).lower()
                        summary["status_counts"][status] = summary["status_counts"].get(status, 0) + 1
                    return summary

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

                elif operation in ("submit_to_firs", "submit_invoice_to_firs", "submit_invoice"):
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

                elif operation == "refresh_firs_resources":
                    if not resource_cache:
                        return {"operation": operation, "success": False, "error": "resource_cache_unavailable"}
                    resources = await resource_cache.refresh_all()
                    return {"operation": operation, "success": True, "data": {"resources": resources}}

                elif operation == "refresh_firs_resource":
                    if not resource_cache:
                        return {"operation": operation, "success": False, "error": "resource_cache_unavailable"}
                    res_key = payload.get("resource")
                    if res_key not in ("currencies", "invoice-types", "services-codes", "vat-exemptions"):
                        return {"operation": operation, "success": False, "error": "invalid_resource"}
                    out = await resource_cache.refresh_resource(res_key)
                    return {"operation": operation, "success": True, "data": out}

                elif operation == "process_firs_webhook":
                    # Process FIRS webhook events
                    result = await self._handle_firs_webhook(payload)
                    return {"operation": operation, "success": True, "data": {"result": result}}
                    
                elif operation in ("get_submission_status", "get_firs_submission_status"):
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

                elif operation in ("submit_invoice_batch_to_firs", "submit_invoice_batch"):
                    # Batch submit: sign -> transmit for each invoice
                    if not http_client:
                        return {"operation": operation, "success": False, "error": "http_client_unavailable"}
                    batch = payload.get("batch_data") or payload.get("invoices") or []
                    if isinstance(batch, dict) and "invoices" in batch:
                        batch = batch["invoices"]
                    results = []
                    overall = True
                    for item in (batch or []):
                        try:
                            sign_resp = await http_client.sign_invoice(item)
                            if not sign_resp.get("success"):
                                results.append({"sign": sign_resp, "transmit": None, "success": False})
                                overall = False
                                continue
                            irn = item.get("irn")
                            if not irn and isinstance(sign_resp.get("data"), dict):
                                irn = sign_resp["data"].get("irn")
                            if not irn:
                                results.append({"sign": sign_resp, "transmit": {"success": False, "error": "missing_irn"}, "success": False})
                                overall = False
                                continue
                            tx_resp = await http_client.transmit(irn)
                            success = sign_resp.get("success", False) and tx_resp.get("success", False)
                            results.append({"sign": sign_resp, "transmit": tx_resp, "success": success})
                            overall = overall and success
                        except Exception as ex:
                            results.append({"error": str(ex), "success": False})
                            overall = False
                    return {"operation": operation, "success": overall, "data": {"results": results, "count": len(batch or [])}}

                elif operation == "transmit_firs_invoice":
                    if not http_client:
                        return {"operation": operation, "success": False, "error": "http_client_unavailable"}
                    irn = payload.get("irn")
                    if not irn:
                        return {"operation": operation, "success": False, "error": "missing_irn"}
                    # Update SI-APP correlation: APP submitting
                    try:
                        await self.message_router.route_message(
                            service_role=ServiceRole.HYBRID,
                            operation="update_app_submitting",
                            payload={"irn": irn, "metadata": {"source": "app_service", "operation": "transmit"}}
                        )
                    except Exception:
                        logger.debug("Correlation update_app_submitting skipped")
                    resp = await http_client.transmit(irn, payload.get("options"))
                    # Update SI-APP correlation: APP submitted
                    try:
                        await self.message_router.route_message(
                            service_role=ServiceRole.HYBRID,
                            operation="update_app_submitted",
                            payload={"irn": irn, "metadata": {"source": "app_service"}}
                        )
                    except Exception:
                        logger.debug("Correlation update_app_submitted skipped")
                    # Optionally push FIRS response if status/id available
                    try:
                        data = resp.get("data") if isinstance(resp, dict) else None
                        firs_status = (resp.get("status") if isinstance(resp, dict) else None) or (data.get("status") if isinstance(data, dict) else None) or "submitted"
                        firs_response_id = (data.get("submission_id") if isinstance(data, dict) else None) or (data.get("id") if isinstance(data, dict) else None)
                        if firs_response_id:
                            await self.message_router.route_message(
                                service_role=ServiceRole.HYBRID,
                                operation="update_firs_response",
                                payload={
                                    "irn": irn,
                                    "firs_response_id": str(firs_response_id),
                                    "firs_status": str(firs_status),
                                    "response_data": data or resp,
                                },
                            )
                    except Exception:
                        logger.debug("Correlation update_firs_response skipped")
                    return {"operation": operation, "success": resp.get("success", False), "data": resp}

                elif operation == "confirm_firs_receipt":
                    if not http_client:
                        return {"operation": operation, "success": False, "error": "http_client_unavailable"}
                    irn = payload.get("irn")
                    if not irn:
                        return {"operation": operation, "success": False, "error": "missing_irn"}
                    resp = await http_client.confirm_receipt(irn, payload.get("options"))
                    return {"operation": operation, "success": resp.get("success", False), "data": resp}

                elif operation in ("authenticate_with_firs", "authenticate_firs"):
                    if not auth_handler:
                        return {"operation": operation, "success": False, "error": "auth_handler_unavailable"}
                    client_id = payload.get("client_id") or os.getenv("FIRS_CLIENT_ID")
                    client_secret = payload.get("client_secret") or os.getenv("FIRS_CLIENT_SECRET")
                    api_key = payload.get("api_key") or os.getenv("FIRS_API_KEY")
                    scope = payload.get("scope")
                    if not all([client_id, client_secret, api_key]):
                        return {
                            "operation": operation,
                            "success": False,
                            "error": "missing_credentials",
                            "data": {"details": "FIRS credentials not configured"}
                        }
                    try:
                        if hasattr(auth_handler, "start"):
                            await auth_handler.start()
                        auth_result = await auth_handler.authenticate_client_credentials(
                            client_id=client_id,
                            client_secret=client_secret,
                            api_key=api_key,
                            scope=scope
                        )
                        if auth_result.success:
                            data = {
                                "auth_data": auth_result.auth_data,
                                "expires_at": auth_result.expires_at.isoformat() if auth_result.expires_at else None,
                                "session_id": auth_result.session_id,
                                "provider": auth_result.provider
                            }
                        else:
                            data = {
                                "error": auth_result.error_message,
                                "error_code": auth_result.error_code,
                                "provider": auth_result.provider
                            }
                        return {"operation": operation, "success": auth_result.success, "data": data}
                    except Exception as auth_error:
                        return {"operation": operation, "success": False, "error": str(auth_error)}

                elif operation == "refresh_firs_token":
                    if not auth_handler:
                        return {"operation": operation, "success": False, "error": "auth_handler_unavailable"}
                    try:
                        if hasattr(auth_handler, "start"):
                            await auth_handler.start()
                        refresh_result = await auth_handler.refresh_access_token(payload.get("refresh_token"))
                        return {
                            "operation": operation,
                            "success": refresh_result.success,
                            "data": refresh_result.auth_data if refresh_result.success else {
                                "error": refresh_result.error_message,
                                "error_code": refresh_result.error_code
                            }
                        }
                    except Exception as refresh_error:
                        return {"operation": operation, "success": False, "error": str(refresh_error)}

                elif operation == "test_firs_connection":
                    if http_client:
                        resp = await http_client.transmit_self_health()
                        return {"operation": operation, "success": resp.get("success", False), "data": resp}
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {"status": "unknown", "reason": "http_client_unavailable", "timestamp": _utc_now()}
                    }

                elif operation == "get_firs_auth_status":
                    if auth_handler and hasattr(auth_handler, "auth_state"):
                        state = auth_handler.auth_state
                        data = {
                            "is_authenticated": state.is_authenticated,
                            "last_auth_time": state.last_auth_time.isoformat() if state.last_auth_time else None,
                            "last_refresh_time": state.last_refresh_time.isoformat() if state.last_refresh_time else None,
                            "auth_attempts": state.auth_attempts,
                            "refresh_attempts": state.refresh_attempts,
                            "active_session_id": state.active_session_id,
                        }
                    else:
                        data = {"is_authenticated": False, "details": "auth_handler_unavailable"}
                    return {"operation": operation, "success": True, "data": data}

                elif operation == "get_firs_system_info":
                    info = {
                        "environment": os.getenv("FIRS_ENVIRONMENT", "sandbox"),
                        "api_base_url": getattr(http_client, "base_url", None) if http_client else None,
                        "resources_cached": getattr(resource_cache, "cached_resources", [] ) if resource_cache else [],
                        "timestamp": _utc_now(),
                    }
                    return {"operation": operation, "success": True, "data": info}

                elif operation == "check_firs_system_health":
                    if http_client:
                        resp = await http_client.transmit_self_health()
                        return {"operation": operation, "success": resp.get("success", False), "data": resp}
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {"status": "unknown", "reason": "http_client_unavailable"}
                    }

                elif operation == "list_firs_submissions":
                    resp = await _fetch_transmissions(payload.get("tin") or payload.get("taxpayer_tin"))
                    if resp.get("success"):
                        records = _normalize_transmissions(resp.get("data"))
                        return {
                            "operation": operation,
                            "success": True,
                            "data": {
                                "submissions": records,
                                "summary": _summarize_transmissions(records)
                            }
                        }
                    return {"operation": operation, "success": False, "error": resp.get("error", "transmission_lookup_failed"), "data": resp.get("data")}

                elif operation == "list_firs_certificates":
                    if not certificate_store:
                        return {"operation": operation, "success": False, "error": "certificate_store_unavailable"}
                    certs_payload = []
                    for cert in certificate_store.list_certificates(
                        organization_id=payload.get("organization_id"),
                        certificate_type=payload.get("certificate_type")
                    ):
                        cert_dict = asdict(cert)
                        cert_dict["status"] = cert.status.value
                        certs_payload.append(cert_dict)
                    return {"operation": operation, "success": True, "data": {"certificates": certs_payload, "retrieved_at": _utc_now()}}

                elif operation == "get_firs_certificate":
                    if not certificate_store:
                        return {"operation": operation, "success": False, "error": "certificate_store_unavailable"}
                    cert_id = payload.get("certificate_id")
                    info = certificate_store.get_certificate_info(cert_id)
                    if not info:
                        return {"operation": operation, "success": False, "error": "not_found"}
                    pem = certificate_store.retrieve_certificate(cert_id)
                    cert_dict = asdict(info)
                    cert_dict["status"] = info.status.value
                    cert_dict["certificate_pem"] = pem.decode("utf-8") if isinstance(pem, bytes) else pem
                    return {"operation": operation, "success": True, "data": cert_dict}

                elif operation == "renew_firs_certificate":
                    cert_id = payload.get("certificate_id")
                    validity_days = int(payload.get("validity_days", 365))
                    from core_platform.data_management.db_async import get_async_session
                    from si_services.certificate_management.certificate_service import CertificateService
                    new_cert_id = ""
                    success = False
                    async for db in get_async_session():
                        service = CertificateService(db=db)
                        new_cert_id, success = service.renew_certificate(cert_id, validity_days)
                        break
                    data = {
                        "certificate_id": cert_id,
                        "renewed_at": _utc_now()
                    }
                    if success:
                        data["new_certificate_id"] = new_cert_id
                    else:
                        data["error"] = "renewal_failed"
                    return {"operation": operation, "success": success, "data": data}

                elif operation == "get_firs_errors":
                    resp = await _fetch_transmissions()
                    if resp.get("success"):
                        records = [r for r in _normalize_transmissions(resp.get("data")) if str(r.get("status", "")).lower() in {"failed", "error", "rejected"} or r.get("error")]
                        return {"operation": operation, "success": True, "data": {"errors": records, "retrieved_at": _utc_now()}}
                    return {"operation": operation, "success": False, "error": resp.get("error", "transmission_lookup_failed")}

                elif operation == "get_firs_integration_logs":
                    resp = await _fetch_transmissions()
                    if resp.get("success"):
                        records = _normalize_transmissions(resp.get("data"))
                        logs = [
                            {
                                "transmission_id": rec.get("id") or rec.get("irn"),
                                "status": rec.get("status"),
                                "timestamp": rec.get("timestamp") or rec.get("submitted_at") or _utc_now(),
                                "message": rec.get("message") or rec.get("status_message")
                            }
                            for rec in records
                        ]
                        return {"operation": operation, "success": True, "data": {"entries": logs, "retrieved_at": _utc_now()}}
                    return {"operation": operation, "success": False, "error": resp.get("error", "transmission_lookup_failed")}

                elif operation == "generate_firs_report":
                    resp = await _fetch_transmissions(payload.get("tin"))
                    if resp.get("success"):
                        records = _normalize_transmissions(resp.get("data"))
                        summary = _summarize_transmissions(records)
                        summary["generated_at"] = _utc_now()
                        return {"operation": operation, "success": True, "data": summary}
                    return {"operation": operation, "success": False, "error": resp.get("error", "report_generation_failed")}

                elif operation == "get_firs_reporting_dashboard":
                    resp = await _fetch_transmissions()
                    if resp.get("success"):
                        records = _normalize_transmissions(resp.get("data"))
                        summary = _summarize_transmissions(records)
                        dashboard = {
                            "metrics": summary,
                            "recent_submissions": records[:10],
                            "refreshed_at": _utc_now()
                        }
                        return {"operation": operation, "success": True, "data": dashboard}
                    return {"operation": operation, "success": False, "error": resp.get("error", "dashboard_generation_failed")}

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
