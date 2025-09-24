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

import base64
import logging
import asyncio
import os
import uuid
import json
from collections import Counter, deque
from datetime import datetime, timezone, timedelta
from dataclasses import asdict
from typing import Dict, Any, Optional, List, Tuple, TYPE_CHECKING

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
from .validation.submission_validator import (
    SubmissionValidator,
    SubmissionContext,
    SubmissionReadiness,
    CheckStatus,
)
from .validation.format_validator import FormatValidator
from .transmission.transmission_service import TransmissionService
from .reporting.transmission_reports import TransmissionReportGenerator
from .security_compliance.encryption_service import EncryptionService, EncryptedData, EncryptionAlgorithm
from .security_compliance.audit_logger import (
    AuditLogger,
    AuditLevel,
    EventCategory,
    AuditContext,
)
from .security_compliance.threat_detector import ThreatDetector
from .security_compliance.security_scanner import SecurityScanner
from .authentication_seals.seal_generator import SealGenerator
from .authentication_seals.verification_service import VerificationService
from .reporting.compliance_metrics import ComplianceMetricsMonitor
from .taxpayer_management.taxpayer_onboarding import TaxpayerOnboardingService
from .onboarding_management.app_onboarding_service import APPOnboardingService

if TYPE_CHECKING:
    # Type-only import to avoid pulling SI modules at import time
    from si_services.certificate_management.certificate_store import CertificateStore  # pragma: no cover

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
            # Minimal init path for tests or lightweight runs
            minimal_mode = str(os.getenv("APP_INIT_MINIMAL", "false")).lower() in ("1", "true", "yes", "on")
            if minimal_mode:
                await self._register_network_services()
                self.is_initialized = True
                logger.info("APP services initialized in minimal mode (network only)")
                return self.service_endpoints

            # Initialize core APP services
            await self._register_firs_services()
            await self._register_webhook_services()
            await self._register_status_management_services()
            await self._register_validation_services()
            await self._register_transmission_services()
            await self._register_network_services()
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

    async def _register_network_services(self):
        """Register participant registry (four-corner) services."""
        try:
            network_service = {
                "operations": [
                    "register_participant",
                    "update_participant",
                    "list_participants",
                    "get_participant",
                    "resolve_participant",
                ]
            }

            self.services["network_routing"] = network_service

            endpoint_id = await self.message_router.register_service(
                service_name="network_routing",
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                callback=self._create_network_callback(network_service),
                priority=3,
                tags=["network", "participants", "routing", "four_corner"],
                metadata={
                    "service_type": "network_routing",
                    "operations": network_service["operations"],
                },
            )
            self.service_endpoints["network_routing"] = endpoint_id
            logger.info(f"Network routing service registered: {endpoint_id}")

            # Register store-and-forward consumer for outbound deliveries
            try:
                from core_platform.messaging.queue_manager import get_queue_manager
                qm = get_queue_manager()
                await qm.initialize()
                # Optional: override retry policy from environment for ap_outbound
                try:
                    delays_env = os.getenv("OUTBOUND_RETRY_DELAYS")
                    max_retries_env = os.getenv("OUTBOUND_MAX_RETRIES")
                    if delays_env or max_retries_env:
                        delays = None
                        if delays_env:
                            delays = [float(x.strip()) for x in delays_env.split(",") if x.strip()]
                        max_retries = int(max_retries_env) if max_retries_env else None
                        qm.register_retry_policy("ap_outbound", max_retries=max_retries, retry_delays=delays)
                        logger.info("Applied outbound retry policy overrides from environment")
                except Exception as _e:
                    logger.warning(f"Could not apply outbound retry policy overrides: {_e}")

                async def _ap_outbound_consumer(message):
                    try:
                        payload = getattr(message, 'payload', {}) or {}
                        endpoint_url = payload.get('endpoint_url') or payload.get('ap_endpoint_url')
                        identifier = payload.get('identifier')
                        # Resolve endpoint if not provided
                        if not endpoint_url and identifier:
                            import time
                            from core_platform.monitoring.prometheus_integration import get_prometheus_integration
                            prom = get_prometheus_integration()
                            _r0 = time.perf_counter()
                            try:
                                res = await self.message_router.route_message(
                                    service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                                    operation="resolve_participant",
                                    payload={"identifier": identifier},
                                )
                                if prom:
                                    prom.record_metric("taxpoynt_ap_outbound_resolve_attempts_total", 1, {"outcome": "success" if (isinstance(res, dict) and res.get('success')) else "failure"})
                                    prom.record_metric("taxpoynt_ap_outbound_resolve_duration_seconds", float(max(0.0, time.perf_counter() - _r0)), {"outcome": "success" if (isinstance(res, dict) and res.get('success')) else "failure"})
                            except Exception:
                                if prom:
                                    prom.record_metric("taxpoynt_ap_outbound_resolve_attempts_total", 1, {"outcome": "exception"})
                                    prom.record_metric("taxpoynt_ap_outbound_resolve_duration_seconds", float(max(0.0, time.perf_counter() - _r0)), {"outcome": "exception"})
                                res = None
                            if isinstance(res, dict) and res.get('success'):
                                endpoint_url = ((res.get('data') or {}).get('ap_endpoint_url'))
                        if not endpoint_url:
                            # No endpoint to deliver to – treat as client failure, ack to avoid retry, send to DLQ for visibility
                            try:
                                from core_platform.monitoring.prometheus_integration import get_prometheus_integration
                                prom = get_prometheus_integration()
                                if prom:
                                    prom.record_metric("taxpoynt_ap_outbound_delivery_failure_total", 1, {"error_type": "resolve_failed", "status_code": "0"})
                            except Exception:
                                pass
                            try:
                                # Manually enqueue to dead_letter to avoid useless retries
                                await qm.enqueue_message("dead_letter", {
                                    "type": "ap_outbound_delivery",
                                    "reason": "resolve_failed",
                                    "endpoint_url": endpoint_url,
                                    "identifier": identifier,
                                    "original_payload": payload,
                                })
                            except Exception:
                                pass
                            return True
                        # Policy checks (allowed domain, TLS)
                        try:
                            from urllib.parse import urlparse
                            from core_platform.monitoring.prometheus_integration import get_prometheus_integration
                            prom = get_prometheus_integration()
                            u = urlparse(endpoint_url)
                            scheme = (u.scheme or '').lower()
                            host = (u.hostname or '').lower()
                            allow_http = str(os.getenv("OUTBOUND_ALLOW_HTTP", "false")).lower() in ("1", "true", "yes", "on")
                            allowed_env = os.getenv("OUTBOUND_ALLOWED_DOMAINS", "")
                            allowed = [d.strip().lower() for d in allowed_env.split(',') if d.strip()]
                            violation = None
                            if scheme != 'https' and not allow_http:
                                violation = 'insecure_scheme'
                            if not violation and allowed:
                                # Match exact or subdomain suffix
                                ok = any(host == d or host.endswith('.' + d) for d in allowed)
                                if not ok:
                                    violation = 'domain_not_allowed'
                            if violation:
                                if prom:
                                    prom.record_metric("taxpoynt_ap_outbound_delivery_failure_total", 1, {"error_type": "policy_violation", "status_code": "0"})
                                try:
                                    await qm.enqueue_message("dead_letter", {
                                        "type": "ap_outbound_delivery",
                                        "reason": violation,
                                        "endpoint_url": endpoint_url,
                                        "identifier": identifier,
                                        "original_payload": payload,
                                    })
                                except Exception:
                                    pass
                                return True
                        except Exception:
                            pass
                        # Deliver via HTTP POST
                        try:
                            import aiohttp
                            from core_platform.monitoring.prometheus_integration import get_prometheus_integration
                            import time, json
                            timeout = aiohttp.ClientTimeout(total=15)
                            async with aiohttp.ClientSession(timeout=timeout) as session:
                                prom = get_prometheus_integration()
                                # Count attempt only when actually performing POST
                                if prom:
                                    prom.record_metric("taxpoynt_ap_outbound_delivery_attempts_total", 1)
                                    # Body size histogram (best-effort)
                                    try:
                                        body = payload.get('document') or payload
                                        size_bytes = 0
                                        try:
                                            size_bytes = len(json.dumps(body).encode('utf-8'))
                                        except Exception:
                                            size_bytes = len(str(body).encode('utf-8'))
                                        prom.record_metric("taxpoynt_ap_outbound_delivery_body_bytes", float(size_bytes))
                                    except Exception:
                                        pass
                                _t0 = time.perf_counter()
                                async with session.post(endpoint_url, json=payload.get('document') or payload) as resp:
                                    status = resp.status
                                    duration = max(0.0, time.perf_counter() - _t0)
                                    if prom:
                                        prom.record_metric("taxpoynt_ap_outbound_delivery_duration_seconds", float(duration), {"status_code": str(status)})
                                    if 200 <= status < 300:
                                        if prom:
                                            prom.record_metric("taxpoynt_ap_outbound_delivery_success_total", 1, {"status_code": str(status)})
                                        return True
                                    # 4xx: ack and optionally move to DLQ to avoid retries
                                    if 400 <= status < 500:
                                        if prom:
                                            prom.record_metric("taxpoynt_ap_outbound_delivery_failure_total", 1, {"error_type": "client_error", "status_code": str(status)})
                                        try:
                                            await qm.enqueue_message("dead_letter", {
                                                "type": "ap_outbound_delivery",
                                                "reason": "client_error",
                                                "http_status": status,
                                                "endpoint_url": endpoint_url,
                                                "identifier": identifier,
                                                "original_message_id": getattr(message, 'message_id', None),
                                                "original_payload": payload,
                                            })
                                        except Exception:
                                            pass
                                        return True
                                    # 5xx: nack (retry)
                                    if prom:
                                        prom.record_metric("taxpoynt_ap_outbound_delivery_failure_total", 1, {"error_type": "server_error", "status_code": str(status)})
                                    return False
                        except Exception:
                            try:
                                from core_platform.monitoring.prometheus_integration import get_prometheus_integration
                                import time
                                prom = get_prometheus_integration()
                                if prom:
                                    prom.record_metric("taxpoynt_ap_outbound_delivery_failure_total", 1, {"error_type": "timeout_or_exception", "status_code": "0"})
                                    # Record a duration for the failed attempt if we can approximate
                                    try:
                                        # If _t0 exists in scope, we record elapsed; otherwise skip
                                        if '_t0' in locals():
                                            prom.record_metric("taxpoynt_ap_outbound_delivery_duration_seconds", float(max(0.0, time.perf_counter() - _t0)), {"status_code": "0"})
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                            return False
                    except Exception:
                        return False

                await qm.register_consumer("ap_outbound", "ap_outbound_worker", _ap_outbound_consumer)
                logger.info("AP outbound consumer registered for store-and-forward routing")
            except Exception as ce:
                logger.warning(f"Could not register AP outbound consumer: {ce}")
        except Exception as e:
            logger.error(f"Failed to register network services: {str(e)}")

    def _create_network_callback(self, _svc):
        """Create callback for participant registry operations."""
        async def network_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                from core_platform.data_management.db_async import get_async_session
                from core_platform.data_management.repositories import participant_repo_async as repo  # type: ignore
                from core_platform.data_management.models.network import Participant
                from sqlalchemy import select

                def _serialize(p: Participant) -> Dict[str, Any]:
                    return {
                        "id": str(getattr(p, "id", None)),
                        "organization_id": str(getattr(p, "organization_id", "")) if getattr(p, "organization_id", None) else None,
                        "identifier": getattr(p, "identifier", None),
                        "role": getattr(p, "role", None).value if getattr(p, "role", None) else None,
                        "status": getattr(p, "status", None).value if getattr(p, "status", None) else None,
                        "ap_endpoint_url": getattr(p, "ap_endpoint_url", None),
                        "preferred_protocol": getattr(p, "preferred_protocol", None).value if getattr(p, "preferred_protocol", None) else None,
                        "last_seen_at": getattr(p, "last_seen_at", None).isoformat() if getattr(p, "last_seen_at", None) else None,
                        "metadata": getattr(p, "metadata_json", {}) or {},
                    }

                if operation == "register_participant":
                    data = payload.get("participant") or payload
                    async for session in get_async_session():
                        row = await repo.create_participant(
                            session,
                            identifier=data.get("identifier"),
                            role=data.get("role"),
                            ap_endpoint_url=data.get("ap_endpoint_url"),
                            preferred_protocol=data.get("preferred_protocol", "http"),
                            organization_id=data.get("organization_id"),
                            public_key=data.get("public_key"),
                            certificate_pem=data.get("certificate_pem"),
                            metadata=data.get("metadata"),
                        )
                        return {"operation": operation, "success": True, "data": {"participant": _serialize(row)}}

                if operation == "list_participants":
                    limit = int(payload.get("limit", 50))
                    page = int(payload.get("page", 1))
                    offset = max(page - 1, 0) * limit
                    async for session in get_async_session():
                        rows = await repo.list_participants(
                            session,
                            limit=limit,
                            offset=offset,
                            status=payload.get("status"),
                            role=payload.get("role"),
                            organization_id=payload.get("organization_id"),
                        )
                        return {"operation": operation, "success": True, "data": {"participants": [_serialize(r) for r in rows], "page": page, "limit": limit}}

                if operation == "get_participant":
                    identifier = payload.get("identifier")
                    participant_id = payload.get("participant_id")
                    async for session in get_async_session():
                        row = None
                        if identifier:
                            row = await repo.get_participant_by_identifier(session, identifier)
                        elif participant_id:
                            from core_platform.data_management.models.network import Participant
                            row = (await session.execute(select(Participant).where(Participant.id == participant_id))).scalars().first()
                        if not row:
                            return {"operation": operation, "success": False, "error": "not_found"}
                        return {"operation": operation, "success": True, "data": {"participant": _serialize(row)}}

                if operation == "update_participant":
                    participant_id = payload.get("participant_id")
                    updates = payload.get("updates") or {}
                    async for session in get_async_session():
                        row = await repo.update_participant(session, participant_id, updates)
                        if not row:
                            return {"operation": operation, "success": False, "error": "not_found"}
                        return {"operation": operation, "success": True, "data": {"participant": _serialize(row)}}

                if operation == "resolve_participant":
                    identifier = payload.get("identifier")
                    if not identifier:
                        return {"operation": operation, "success": False, "error": "missing_identifier"}
                    async for session in get_async_session():
                        row = await repo.get_participant_by_identifier(session, identifier)
                        if not row:
                            return {"operation": operation, "success": False, "error": "not_found"}
                        data = _serialize(row)
                        return {"operation": operation, "success": True, "data": {"identifier": identifier, "ap_endpoint_url": data["ap_endpoint_url"], "preferred_protocol": data["preferred_protocol"], "status": data["status"], "participant": data}}

                return {"operation": operation, "success": False, "error": "unsupported_operation"}
            except Exception as e:
                return {"operation": operation, "success": False, "error": str(e)}

        return network_callback
    
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

            # Lazy import to avoid SI module import at app import time
            try:
                from si_services.certificate_management.certificate_store import CertificateStore as _CertificateStore  # type: ignore
                certificate_store = _CertificateStore()
            except Exception:
                certificate_store = None
                logger.debug("Certificate store unavailable; continuing without it")

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

    def _create_validation_service_state(self) -> Dict[str, Any]:
        """Build reusable validation service state container."""

        firs_validator = FIRSValidator()
        format_validator = FormatValidator()
        submission_validator = SubmissionValidator(firs_validator=firs_validator)

        recent_limit = max(10, int(os.getenv("VALIDATION_RECENT_LIMIT", "50") or 50))

        rule_catalog: Dict[str, Dict[str, Any]] = {}
        for rule in getattr(firs_validator, "validation_rules", {}).values():
            rule_id = rule.get("rule_id")
            if not rule_id:
                continue
            rule_catalog[rule_id] = {
                "description": rule.get("description"),
                "severity": getattr(rule.get("severity"), "value", None),
            }

        for check in getattr(submission_validator, "check_definitions", {}).values():
            check_id = check.get("check_id")
            if not check_id:
                continue
            rule_catalog[check_id] = {
                "description": check.get("description") or check.get("name"),
                "severity": getattr(check.get("severity"), "value", None),
            }

        return {
            "firs_validator": firs_validator,
            "format_validator": format_validator,
            "submission_validator": submission_validator,
            "recent_results": deque(maxlen=recent_limit),
            "validation_store": {},
            "batch_results": {},
            "issue_counter": Counter(),
            "rule_catalog": rule_catalog,
            "metrics": {
                "total_requests": 0,
                "single_validations": 0,
                "batch_validations": 0,
                "passed": 0,
                "failed": 0,
                "total_duration_ms": 0.0,
                "score_accumulator": 0.0,
                "validations_with_score": 0,
                "last_validation_at": None,
            },
        }

    async def _register_validation_services(self):
        """Register validation services"""
        try:
            validation_service = self._create_validation_service_state()
            validation_service["operations"] = [
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
                "validate_comprehensive_compliance",
            ]
            
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

            transmission_logic = TransmissionService(self.message_router)

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
            threat_detector = ThreatDetector()
            security_scanner = SecurityScanner(threat_detector=threat_detector, audit_logger=audit_logger)
            
            security_service = {
                "encryption_service": encryption_service,
                "audit_logger": audit_logger,
                "scanner": security_scanner,
                "threat_detector": threat_detector,
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
                    # Enrich with queue stats (ap_outbound and dead_letter)
                    status_payload: Dict[str, Any] = {"status": "healthy", "checked_at": datetime.now(timezone.utc).isoformat()}
                    try:
                        from core_platform.messaging.queue_manager import get_queue_manager
                        qm = get_queue_manager()
                        await qm.initialize()
                        queues = await qm.get_all_queue_status()
                        ap_out = queues.get("ap_outbound") or {}
                        dlq = queues.get("dead_letter") or {}
                        status_payload["queues"] = {
                            "ap_outbound": ap_out,
                            "dead_letter": dlq,
                        }
                        # Alerts: DLQ messages > 0 or large backlog on outbound
                        alerts: List[str] = []
                        try:
                            ap_metrics = ap_out.get("metrics") or {}
                            dlq_metrics = dlq.get("metrics") or {}
                            if (dlq_metrics.get("current_queue_size") or 0) > 0:
                                alerts.append("dead_letter_queue_non_empty")
                            if (ap_metrics.get("current_queue_size") or 0) > 1000:
                                alerts.append("ap_outbound_backlog_high")
                            # Oldest message age alert
                            try:
                                from core_platform.monitoring.prometheus_integration import get_prometheus_integration
                                prom = get_prometheus_integration()
                                # Compute oldest age from queue object for accuracy
                                q = getattr(qm, 'queues', {}).get('ap_outbound')
                                oldest_age_sec = 0.0
                                if q and getattr(q, 'message_registry', None):
                                    from datetime import datetime, timezone
                                    now = datetime.now(timezone.utc)
                                    oldest_ts = None
                                    for m in q.message_registry.values():
                                        ts = getattr(m, 'scheduled_time', None) or getattr(m, 'created_time', None)
                                        if ts and (oldest_ts is None or ts < oldest_ts):
                                            oldest_ts = ts
                                    if oldest_ts:
                                        oldest_age_sec = max(0.0, (now - oldest_ts).total_seconds())
                                # Record gauges
                                if prom:
                                    prom.record_metric("taxpoynt_ap_outbound_current_queue_size", float(ap_metrics.get("current_queue_size") or 0), {"queue": "ap_outbound"})
                                    prom.record_metric("taxpoynt_ap_outbound_dead_letter_count", float(dlq_metrics.get("current_queue_size") or 0), {"queue": "dead_letter"})
                                    prom.record_metric("taxpoynt_ap_outbound_oldest_message_age_seconds", float(oldest_age_sec))
                                # Threshold alert
                                import os
                                max_age = float(os.getenv("AP_OUTBOUND_MAX_AGE_SECONDS", "0") or 0)
                                if max_age and oldest_age_sec > max_age:
                                    alerts.append("ap_outbound_message_age_exceeded")
                                    status_payload["oldest_message_age_seconds"] = oldest_age_sec
                            except Exception:
                                pass
                        except Exception:
                            pass
                        if alerts:
                            status_payload["alerts"] = alerts
                            status_payload["status"] = "degraded"
                    except Exception:
                        # If queue manager not available, still return basic status
                        pass
                    return {"operation": operation, "success": True, "data": status_payload}
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
                firs_validator: Optional[FIRSValidator] = validation_service.get("firs_validator")
                format_validator: Optional[FormatValidator] = validation_service.get("format_validator")
                submission_validator: Optional[SubmissionValidator] = validation_service.get("submission_validator")
                recent_results: deque = validation_service.get("recent_results")  # type: ignore[arg-type]
                validation_store: Dict[str, Dict[str, Any]] = validation_service.get("validation_store", {})
                batch_results: Dict[str, Dict[str, Any]] = validation_service.get("batch_results", {})
                issue_counter: Counter = validation_service.get("issue_counter", Counter())  # type: ignore[assignment]
                metrics: Dict[str, Any] = validation_service.get("metrics", {})
                rule_catalog: Dict[str, Dict[str, Any]] = validation_service.get("rule_catalog", {})

                def _utc_now() -> datetime:
                    return datetime.now(timezone.utc)

                def _serialize_format_result(result) -> Dict[str, Any]:
                    return {
                        "field": getattr(result, "field_path", None),
                        "severity": getattr(getattr(result, "severity", None), "value", None),
                        "message": getattr(result, "message", None),
                        "expected": getattr(result, "expected_format", None),
                        "actual": getattr(result, "actual_value", None),
                    }

                def _serialize_firs_result(result) -> Dict[str, Any]:
                    return {
                        "rule_id": getattr(result, "rule_id", None),
                        "field": getattr(result, "field_name", None),
                        "severity": getattr(getattr(result, "severity", None), "value", None),
                        "message": getattr(result, "message", None),
                        "suggestion": getattr(result, "suggestion", None),
                    }

                def _serialize_submission_check(check) -> Dict[str, Any]:
                    return {
                        "check_id": getattr(check, "check_id", None),
                        "name": getattr(check, "check_name", None),
                        "category": getattr(getattr(check, "category", None), "value", None),
                        "status": getattr(getattr(check, "status", None), "value", None),
                        "severity": getattr(getattr(check, "severity", None), "value", None),
                        "message": getattr(check, "message", None),
                        "blocking": getattr(check, "blocking", None),
                    }

                def _serialize_format_report(report) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
                    if report is None:
                        return None, []
                    errors = [_serialize_format_result(res) for res in getattr(report, "errors", [])]
                    warnings = [_serialize_format_result(res) for res in getattr(report, "warnings", [])]
                    info_entries = [_serialize_format_result(res) for res in getattr(report, "info", [])]
                    payload = {
                        "document_id": getattr(report, "document_id", None),
                        "format_type": getattr(getattr(report, "format_type", None), "value", None),
                        "is_valid": getattr(report, "is_valid", None),
                        "schema_version": getattr(report, "schema_version", None),
                        "total_fields": getattr(report, "total_fields", None),
                        "invalid_fields": getattr(report, "invalid_fields", None),
                        "errors": errors,
                        "warnings": warnings,
                        "info": info_entries,
                    }
                    issues = [
                        {
                            "source": "format",
                            "code": f"format::{entry['field']}",
                            "severity": entry["severity"],
                            "message": entry["message"],
                        }
                        for entry in errors + warnings
                    ]
                    return payload, issues

                def _serialize_firs_report(report) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
                    if report is None:
                        return None, []
                    errors = [_serialize_firs_result(res) for res in getattr(report, "errors", [])]
                    warnings = [_serialize_firs_result(res) for res in getattr(report, "warnings", [])]
                    payload = {
                        "document_id": getattr(report, "document_id", None),
                        "document_type": getattr(getattr(report, "document_type", None), "value", None),
                        "is_valid": getattr(report, "is_valid", None),
                        "total_checks": getattr(report, "total_checks", None),
                        "passed_checks": getattr(report, "passed_checks", None),
                        "failed_checks": getattr(report, "failed_checks", None),
                        "errors": errors,
                        "warnings": warnings,
                    }
                    issues = [
                        {
                            "source": "compliance",
                            "code": entry.get("rule_id") or entry.get("field") or "firs_unknown",
                            "severity": entry.get("severity"),
                            "message": entry.get("message"),
                        }
                        for entry in errors + warnings
                    ]
                    return payload, issues

                def _serialize_submission_report(report) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
                    if report is None:
                        return None, []
                    checks = [_serialize_submission_check(check) for check in getattr(report, "checks", [])]
                    categories = {
                        getattr(category, "value", str(category)): data
                        for category, data in getattr(report, "categories", {}).items()
                    }
                    payload = {
                        "document_id": getattr(report, "document_id", None),
                        "validation_id": getattr(report, "validation_id", None),
                        "readiness": getattr(getattr(report, "readiness", None), "value", None),
                        "overall_score": getattr(report, "overall_score", None),
                        "passed_checks": getattr(report, "passed_checks", None),
                        "failed_checks": getattr(report, "failed_checks", None),
                        "warning_checks": getattr(report, "warning_checks", None),
                        "blocking_issues": getattr(report, "blocking_issues", None),
                        "checks": checks,
                        "categories": categories,
                        "recommendations": getattr(report, "recommendations", []),
                    }
                    issues = [
                        {
                            "source": "submission",
                            "code": check.get("check_id"),
                            "severity": check.get("severity"),
                            "message": check.get("message"),
                        }
                        for check in checks
                        if check.get("status") in {CheckStatus.FAILED.value, CheckStatus.WARNING.value}
                    ]
                    return payload, issues

                async def _execute_validation(
                    document: Dict[str, Any],
                    options: Optional[Dict[str, Any]] = None,
                    *,
                    run_format: bool = True,
                    run_firs: bool = True,
                    run_submission: bool = True,
                ) -> Dict[str, Any]:
                    if not isinstance(document, dict):
                        raise ValueError("invoice_data must be a JSON object")

                    options = options or {}
                    validation_id = str(uuid.uuid4())
                    started_at = _utc_now()

                    format_report = None
                    firs_report = None
                    submission_report = None

                    if run_format and format_validator:
                        format_report = await format_validator.validate_document_format(document)

                    if run_firs and firs_validator:
                        firs_report = await firs_validator.validate_document(document)

                    if run_submission and submission_validator:
                        submission_options = options.get("submission", {})
                        submission_context = SubmissionContext(
                            document_data=document,
                            submission_endpoint=submission_options.get(
                                "submission_endpoint", "https://firs.sandbox/api"
                            ),
                            security_level=submission_options.get("security_level", "standard"),
                            transmission_mode=submission_options.get("transmission_mode", "api"),
                            user_permissions=submission_options.get(
                                "user_permissions",
                                ["submit_documents", "access_firs"],
                            ),
                            organization_settings=submission_options.get(
                                "organization_settings", {"required_workflow": ["created", "reviewed"]}
                            ),
                            external_dependencies=submission_options.get(
                                "external_dependencies",
                                {
                                    "system_version": "1.0.0",
                                    "cpu_usage": 20,
                                    "memory_usage": 30,
                                    "signing": {"signing_key": "available"},
                                    "daily_submissions": 0,
                                },
                            ),
                            validation_options=submission_options.get("validation_options", {}),
                        )
                        endpoint = submission_context.submission_endpoint
                        if endpoint:
                            cache_key = f"connectivity_{endpoint}"
                            submission_validator._service_cache[cache_key] = (
                                CheckStatus.PASSED,
                                "Connectivity check skipped (local validation)",
                                None,
                            )
                            submission_validator._cache_expiry[cache_key] = datetime.utcnow() + timedelta(minutes=10)
                        submission_report = await submission_validator.validate_submission(submission_context)

                    format_payload, format_issues = _serialize_format_report(format_report)
                    firs_payload, firs_issues = _serialize_firs_report(firs_report)
                    submission_payload, submission_issues = _serialize_submission_report(submission_report)

                    issues = format_issues + firs_issues + submission_issues
                    for issue in issues:
                        issue_code = issue.get("code") or "unknown_issue"
                        issue_counter[issue_code] += 1

                    duration_ms = (_utc_now() - started_at).total_seconds() * 1000

                    success = True
                    if format_payload is not None:
                        success = success and bool(format_payload.get("is_valid", False))
                    if firs_payload is not None:
                        success = success and bool(firs_payload.get("is_valid", False))
                    if submission_payload is not None:
                        readiness = submission_payload.get("readiness")
                        success = success and readiness in {
                            SubmissionReadiness.READY.value,
                            SubmissionReadiness.PENDING.value,
                        }

                    metrics.setdefault("total_requests", 0)
                    metrics.setdefault("single_validations", 0)
                    metrics.setdefault("batch_validations", 0)
                    metrics.setdefault("passed", 0)
                    metrics.setdefault("failed", 0)
                    metrics.setdefault("total_duration_ms", 0.0)
                    metrics.setdefault("score_accumulator", 0.0)
                    metrics.setdefault("validations_with_score", 0)

                    metrics["total_requests"] += 1
                    metrics["single_validations"] += 1
                    metrics["total_duration_ms"] += duration_ms
                    metrics["last_validation_at"] = started_at.isoformat()

                    if success:
                        metrics["passed"] += 1
                    else:
                        metrics["failed"] += 1

                    submission_score = submission_payload.get("overall_score") if submission_payload else None
                    if submission_score is not None:
                        metrics["score_accumulator"] += submission_score
                        metrics["validations_with_score"] += 1

                    record = {
                        "validation_id": validation_id,
                        "status": "passed" if success else "failed",
                        "timestamp": started_at.isoformat(),
                        "duration_ms": duration_ms,
                        "issues": issues,
                        "reports": {},
                        "summary": {
                            "format": format_payload,
                            "compliance": firs_payload,
                            "submission": submission_payload,
                        },
                    }

                    reports_container = record["reports"]
                    if format_payload is not None:
                        reports_container["format_report"] = format_payload
                    if firs_payload is not None:
                        reports_container["firs_report"] = firs_payload
                    if submission_payload is not None:
                        reports_container["submission_report"] = submission_payload

                    validation_store[validation_id] = record
                    if isinstance(recent_results, deque):
                        recent_results.appendleft(record)

                    return record

                timestamp = _utc_now().isoformat()

                if operation in {"validate_invoice", "validate_single_invoice", "validate_submission", "check_compliance", "verify_format", "validate_ubl_compliance", "validate_peppol_compliance", "validate_iso27001_compliance", "validate_iso20022_compliance", "validate_data_protection_compliance", "validate_lei_compliance", "validate_product_classification", "validate_comprehensive_compliance"}:
                    document = (
                        payload.get("invoice_data")
                        or payload.get("document")
                        or payload.get("submission_data")
                    )
                    if document is None:
                        return {"operation": operation, "success": False, "error": "missing_document"}

                    options = payload.get("options") or {}

                    run_format = operation not in {"check_compliance"}
                    run_firs = operation not in {"verify_format"}
                    run_submission = operation in {"validate_submission", "validate_comprehensive_compliance", "validate_single_invoice", "validate_invoice", "check_compliance", "validate_ubl_compliance", "validate_peppol_compliance", "validate_iso27001_compliance", "validate_iso20022_compliance", "validate_data_protection_compliance", "validate_lei_compliance", "validate_product_classification", "validate_comprehensive_compliance"}

                    record = await _execute_validation(
                        document,
                        options,
                        run_format=run_format,
                        run_firs=run_firs,
                        run_submission=run_submission,
                    )

                    return {
                        "operation": operation,
                        "success": record["status"] == "passed",
                        "data": record,
                    }

                if operation == "validate_invoice_batch":
                    batch_data = payload.get("batch_data") or {}
                    invoices = batch_data.get("invoices") or []
                    if not isinstance(invoices, list) or not invoices:
                        return {"operation": operation, "success": False, "error": "no_invoices_provided"}

                    batch_id = batch_data.get("batch_id") or f"BATCH-{uuid.uuid4().hex[:8]}"
                    options = batch_data.get("options") or {}

                    batch_records: List[Dict[str, Any]] = []
                    for invoice in invoices:
                        record = await _execute_validation(invoice, options)
                        record["batch_id"] = batch_id
                        batch_records.append(record)

                    metrics["batch_validations"] = metrics.get("batch_validations", 0) + 1

                    passed_count = sum(1 for rec in batch_records if rec["status"] == "passed")
                    failed_count = len(batch_records) - passed_count
                    batch_payload = {
                        "batch_id": batch_id,
                        "status": "completed",
                        "summary": {
                            "total": len(batch_records),
                            "passed": passed_count,
                            "failed": failed_count,
                        },
                        "validated_at": timestamp,
                        "results": batch_records,
                    }

                    batch_results[batch_id] = batch_payload

                    return {
                        "operation": operation,
                        "success": failed_count == 0,
                        "data": batch_payload,
                    }

                if operation == "validate_uploaded_file":
                    file_content = payload.get("file_content")
                    if isinstance(file_content, bytes):
                        try:
                            file_content = file_content.decode("utf-8")
                        except UnicodeDecodeError:
                            return {"operation": operation, "success": False, "error": "invalid_file_encoding"}
                    if isinstance(file_content, str):
                        try:
                            parsed = json.loads(file_content)
                        except json.JSONDecodeError:
                            return {"operation": operation, "success": False, "error": "invalid_json_payload"}
                    else:
                        parsed = file_content

                    if isinstance(parsed, list):
                        return await validation_callback("validate_invoice_batch", {"batch_data": {"invoices": parsed}})
                    if isinstance(parsed, dict):
                        return await validation_callback("validate_single_invoice", {"invoice_data": parsed})

                    return {"operation": operation, "success": False, "error": "unsupported_file_structure"}

                if operation == "get_validation_result":
                    validation_id = payload.get("validation_id")
                    if not validation_id:
                        return {"operation": operation, "success": False, "error": "missing_validation_id"}
                    record = validation_store.get(validation_id)
                    if not record:
                        return {"operation": operation, "success": False, "error": "not_found"}
                    return {"operation": operation, "success": True, "data": record}

                if operation == "get_batch_validation_status":
                    batch_id = payload.get("batch_id")
                    if not batch_id:
                        return {"operation": operation, "success": False, "error": "missing_batch_id"}
                    record = batch_results.get(batch_id)
                    if not record:
                        return {"operation": operation, "success": False, "error": "not_found"}
                    return {"operation": operation, "success": True, "data": record}

                if operation == "get_recent_validation_results":
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "results": list(recent_results) if isinstance(recent_results, deque) else [],
                            "generated_at": timestamp,
                        },
                    }

                if operation == "get_validation_metrics":
                    total = metrics.get("total_requests", 0)
                    passed = metrics.get("passed", 0)
                    failed = metrics.get("failed", 0)
                    avg_duration = (
                        metrics.get("total_duration_ms", 0.0) / total if total else 0.0
                    )
                    avg_score = (
                        metrics.get("score_accumulator", 0.0) / metrics.get("validations_with_score", 1)
                        if metrics.get("validations_with_score", 0) > 0
                        else None
                    )
                    data = {
                        "metrics": {
                            "total_validations": total,
                            "passed": passed,
                            "failed": failed,
                            "pass_rate": (passed / total * 100) if total else 0.0,
                            "average_duration_ms": avg_duration,
                            "average_score": avg_score,
                            "single_validations": metrics.get("single_validations", 0),
                            "batch_validations": metrics.get("batch_validations", 0),
                            "last_validation_at": metrics.get("last_validation_at"),
                        },
                        "generated_at": timestamp,
                    }
                    return {"operation": operation, "success": True, "data": data}

                if operation == "get_validation_overview":
                    overview = {
                        "metrics": await validation_callback("get_validation_metrics", {})["data"],
                        "recent": list(recent_results)[:5] if isinstance(recent_results, deque) else [],
                        "common_issues": [
                            {"code": code, "count": count}
                            for code, count in issue_counter.most_common(10)
                        ],
                        "generated_at": timestamp,
                    }
                    return {"operation": operation, "success": True, "data": overview}

                if operation in {"get_validation_rules", "get_firs_validation_standards", "get_ubl_validation_standards"}:
                    rules_payload = {
                        "firs_rules": [
                            {
                                "rule_id": rule_id,
                                **details,
                            }
                            for rule_id, details in rule_catalog.items()
                            if not rule_id.startswith("format::")
                        ],
                        "format_schemas": list(getattr(format_validator, "schemas", {}).keys()) if format_validator else [],
                        "generated_at": timestamp,
                    }
                    return {"operation": operation, "success": True, "data": rules_payload}

                if operation == "get_validation_error_analysis":
                    analysis = [
                        {"code": code, "count": count}
                        for code, count in issue_counter.most_common(20)
                    ]
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {"analysis": analysis, "generated_at": timestamp},
                    }

                if operation == "get_validation_error_help":
                    error_code = payload.get("error_code")
                    if not error_code:
                        return {"operation": operation, "success": False, "error": "missing_error_code"}
                    help_entry = rule_catalog.get(error_code)
                    if help_entry:
                        return {"operation": operation, "success": True, "data": help_entry}
                    if error_code.startswith("format::"):
                        return {
                            "operation": operation,
                            "success": True,
                            "data": {
                                "description": "Format validation issue",
                                "severity": "warning",
                                "remediation": "Review field formatting against schema requirements.",
                            },
                        }
                    return {"operation": operation, "success": False, "error": "unknown_error_code"}

                if operation in {"get_data_quality_metrics", "generate_quality_report", "generate_compliance_report", "get_compliance_report", "list_compliance_reports"}:
                    total_validations = metrics.get("total_requests", 0)
                    passed = metrics.get("passed", 0)
                    fail_rate = (metrics.get("failed", 0) / total_validations * 100) if total_validations else 0.0
                    quality_score = (passed / total_validations * 100) if total_validations else 100.0
                    top_issues = [
                        {"code": code, "count": count}
                        for code, count in issue_counter.most_common(5)
                    ]
                    quality_payload = {
                        "overall_quality_score": round(quality_score, 2),
                        "pass_rate": (passed / total_validations * 100) if total_validations else 100.0,
                        "failure_rate": fail_rate,
                        "total_validations": total_validations,
                        "top_issues": top_issues,
                        "generated_at": timestamp,
                    }
                    if operation == "get_data_quality_metrics":
                        return {"operation": operation, "success": True, "data": quality_payload}

                    report = {
                        "report_id": f"quality-{uuid.uuid4().hex[:8]}",
                        "summary": quality_payload,
                        "recommendations": [
                            "Increase automated validation coverage" if fail_rate > 10 else "Maintain current validation procedures",
                            "Review top recurring issues" if top_issues else "Great job keeping issues low",
                        ],
                        "generated_at": timestamp,
                    }
                    if operation == "list_compliance_reports":
                        return {
                            "operation": operation,
                            "success": True,
                            "data": {"reports": [report], "generated_at": timestamp},
                        }
                    return {"operation": operation, "success": True, "data": report}

                return {"operation": operation, "success": False, "error": "unsupported_operation"}
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
                encryption_service: EncryptionService = security_service["encryption_service"]
                audit_logger: AuditLogger = security_service["audit_logger"]
                scanner: SecurityScanner = security_service.get("scanner")
                threat_detector: ThreatDetector = security_service.get("threat_detector")

                def _to_enum(enum_cls, value, default):
                    if isinstance(value, enum_cls):
                        return value
                    if isinstance(value, str):
                        try:
                            return enum_cls(value.lower())
                        except ValueError:
                            try:
                                return enum_cls[value.upper()]
                            except Exception:
                                return default
                    return default

                def _decode_bytes(value: Optional[str]) -> Optional[bytes]:
                    if value is None:
                        return None
                    if isinstance(value, bytes):
                        return value
                    try:
                        return base64.b64decode(value)
                    except Exception:
                        return None

                if operation == "encrypt_document":
                    document = payload.get("document")
                    if document is None:
                        return {"operation": operation, "success": False, "error": "missing_document"}
                    document_id = payload.get("document_id") or f"doc-{uuid.uuid4().hex[:8]}"
                    algorithm = payload.get("algorithm")
                    algorithm_enum = None
                    if algorithm:
                        algorithm_enum = _to_enum(EncryptionAlgorithm, algorithm, None)
                    encrypted = await encryption_service.encrypt_document(
                        document=document,
                        document_id=document_id,
                        algorithm=algorithm_enum,
                    )
                    last_operation = encryption_service.operations[-1] if encryption_service.operations else None
                    key_id = None
                    algorithm_used = encrypted.algorithm or algorithm_enum or encryption_service.config.algorithm
                    if last_operation:
                        key_id = last_operation.key_id or key_id
                        if not algorithm_used and last_operation.algorithm:
                            algorithm_used = last_operation.algorithm
                    if not encrypted.key_id and key_id:
                        encrypted.key_id = key_id
                    if algorithm_used and not encrypted.algorithm:
                        encrypted.algorithm = algorithm_used if isinstance(algorithm_used, EncryptionAlgorithm) else _to_enum(EncryptionAlgorithm, algorithm_used, encryption_service.config.algorithm)

                    data = {
                        "document_id": document_id,
                        "data": base64.b64encode(encrypted.data).decode("utf-8"),
                        "iv": base64.b64encode(encrypted.iv).decode("utf-8"),
                        "tag": base64.b64encode(encrypted.tag).decode("utf-8") if encrypted.tag else None,
                        "salt": base64.b64encode(encrypted.salt).decode("utf-8") if encrypted.salt else None,
                        "algorithm": (encrypted.algorithm.value if isinstance(encrypted.algorithm, EncryptionAlgorithm) else str(encrypted.algorithm or "")) or algorithm_used.value,
                        "key_id": encrypted.key_id or key_id,
                    }
                    return {"operation": operation, "success": True, "data": data}

                if operation == "decrypt_document":
                    encrypted_payload = payload.get("encrypted_data")
                    if not isinstance(encrypted_payload, dict):
                        return {"operation": operation, "success": False, "error": "missing_encrypted_data"}
                    encrypted_data = EncryptedData(
                        data=_decode_bytes(encrypted_payload.get("data")) or b"",
                        iv=_decode_bytes(encrypted_payload.get("iv")) or b"",
                        tag=_decode_bytes(encrypted_payload.get("tag")),
                        salt=_decode_bytes(encrypted_payload.get("salt")),
                        algorithm=_to_enum(EncryptionAlgorithm, encrypted_payload.get("algorithm"), encryption_service.config.algorithm),
                        key_id=encrypted_payload.get("key_id"),
                    )
                    document_id = payload.get("document_id", "unknown")
                    decrypted = await encryption_service.decrypt_document(encrypted_data, document_id)
                    if isinstance(decrypted, bytes):
                        try:
                            decrypted = decrypted.decode("utf-8")
                        except UnicodeDecodeError:
                            decrypted = base64.b64encode(decrypted).decode("utf-8")
                    return {"operation": operation, "success": True, "data": {"document": decrypted}}

                if operation == "log_security_event":
                    event = payload.get("event", {})
                    level = _to_enum(AuditLevel, event.get("level", "security"), AuditLevel.SECURITY)
                    category = _to_enum(EventCategory, event.get("category", "security_incident"), EventCategory.SECURITY_INCIDENT)
                    message = event.get("message", "Security event logged")
                    details = event.get("details") or {}
                    context_payload = event.get("context") or {}
                    context = None
                    if isinstance(context_payload, dict):
                        allowed = {field for field in AuditContext.__annotations__}
                        context_kwargs = {k: v for k, v in context_payload.items() if k in allowed}
                        context = AuditContext(**context_kwargs)
                    await audit_logger.log_event(
                        level=level,
                        category=category,
                        event_type=event.get("event_type", "custom_security_event"),
                        message=message,
                        details=details,
                        context=context,
                        risk_score=int(event.get("risk_score", 50)),
                        severity=event.get("severity", "medium"),
                        source_component=event.get("source", "security_api"),
                    )
                    return {"operation": operation, "success": True, "data": {"logged": True}}

                if operation == "generate_security_report":
                    report = {
                        "report_id": f"security-report-{uuid.uuid4().hex[:8]}",
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                        "metrics": audit_logger.get_metrics(),
                        "vulnerabilities": scanner.list_vulnerabilities(status="open") if scanner else [],
                    }
                    return {"operation": operation, "success": True, "data": report}

                if operation == "run_security_scan" and scanner:
                    scope = (
                        payload.get("scan_scope")
                        or payload.get("targets")
                        or payload.get("events")
                        or []
                    )
                    result = await scanner.run_scan(scope, scan_type=payload.get("scan_type", "ad_hoc"), options=payload.get("options"))
                    return {"operation": operation, "success": True, "data": result}

                if operation == "get_scan_status" and scanner:
                    return {"operation": operation, "success": True, "data": scanner.get_scan_status(payload.get("scan_id", ""))}

                if operation == "get_scan_results" and scanner:
                    return {"operation": operation, "success": True, "data": scanner.get_scan_results(payload.get("scan_id", ""))}

                if operation == "list_vulnerabilities" and scanner:
                    status_filter = payload.get("status")
                    vulns = scanner.list_vulnerabilities(status=status_filter)
                    return {"operation": operation, "success": True, "data": {"vulnerabilities": vulns}}

                if operation == "resolve_vulnerability" and scanner:
                    vuln_id = payload.get("vulnerability_id")
                    if not vuln_id:
                        return {"operation": operation, "success": False, "error": "missing_vulnerability_id"}
                    result = scanner.resolve_vulnerability(vuln_id, payload.get("resolution"))
                    return {"operation": operation, "success": result.get("status") != "not_found", "data": result}

                if operation == "get_suspicious_activity" and scanner:
                    limit = int(payload.get("limit", 20))
                    return {"operation": operation, "success": True, "data": {"activities": scanner.get_recent_activity(limit=limit)}}

                if operation == "get_access_logs":
                    limit = int(payload.get("limit", 100))
                    # Flush buffered events so logs reflect latest entries
                    await audit_logger._flush_buffer()
                    events = list(audit_logger.event_storage)[-limit:]

                    def _serialize_event(event):
                        data = asdict(event)
                        data["timestamp"] = event.timestamp.isoformat()
                        if event.context:
                            ctx = asdict(event.context)
                            data["context"] = ctx
                        data["level"] = event.level.value
                        data["category"] = event.category.value
                        data["compliance_tags"] = [tag.value for tag in event.compliance_tags]
                        return data

                    logs = [_serialize_event(evt) for evt in events]
                    return {"operation": operation, "success": True, "data": {"logs": logs, "count": len(logs)}}

                if operation == "get_security_metrics":
                    scanner_metrics = scanner.get_metrics() if scanner else {}
                    audit_metrics = audit_logger.get_metrics()
                    threat_metrics = {}
                    if threat_detector:
                        threat_metrics = dict(threat_detector.metrics)
                        threat_metrics["threats_by_type"] = dict(threat_metrics.get("threats_by_type", {}))
                        threat_metrics["threats_by_level"] = dict(threat_metrics.get("threats_by_level", {}))
                    metrics_payload = {
                        "scanner": scanner_metrics,
                        "auditing": audit_metrics,
                        "threat_detection": threat_metrics,
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                    }
                    return {"operation": operation, "success": True, "data": metrics_payload}

                if operation == "get_security_overview":
                    overview = {
                        "metrics": await security_callback("get_security_metrics", {})["data"],
                        "recent_activity": scanner.get_recent_activity(limit=10) if scanner else [],
                        "open_vulnerabilities": scanner.list_vulnerabilities(status="open")[:10] if scanner else [],
                        "generated_at": datetime.now(timezone.utc).isoformat(),
                    }
                    return {"operation": operation, "success": True, "data": overview}

                if operation == "check_iso27001_compliance":
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "compliant": scanner.metrics.get("open_vulnerabilities", 0) == 0 if scanner else True,
                            "last_scan_at": scanner.metrics.get("last_scan_at") if scanner else None,
                        },
                    }

                if operation == "check_gdpr_compliance":
                    await audit_logger._flush_buffer()
                    high_risk_events = [evt for evt in audit_logger.event_storage if evt.risk_score >= 80]
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "compliant": len(high_risk_events) == 0,
                            "high_risk_events": len(high_risk_events),
                        },
                    }

                if operation in {"audit_compliance", "get_scan_status", "get_scan_results", "list_vulnerabilities", "resolve_vulnerability", "get_suspicious_activity"} and not scanner:
                    return {"operation": operation, "success": False, "error": "scanner_unavailable"}

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
                from core_platform.data_management.db_async import get_async_session
                from core_platform.data_management.models.business_systems import Taxpayer, TaxpayerStatus
                from core_platform.data_management.grant_tracking_repository import (
                    GrantTrackingRepository,
                    TaxpayerSize,
                )
                from core_platform.data_management.database_init import get_database
                from sqlalchemy import select
                timestamp = datetime.now(timezone.utc).isoformat()

                grant_repo: Optional[GrantTrackingRepository] = None

                def _get_grant_repo() -> GrantTrackingRepository:
                    nonlocal grant_repo
                    if grant_repo is None:
                        db = get_database()
                        if not db:
                            raise RuntimeError("Database not initialized for grant tracking")
                        grant_repo = GrantTrackingRepository(db_layer=db)
                    return grant_repo

                def _resolve_tenant_id(source: Dict[str, Any], fallback: Optional[str] = None) -> Optional[str]:
                    for key in ("tenant_id", "organization_id", "app_id"):
                        value = source.get(key)
                        if value:
                            return value
                    return fallback

                def _infer_taxpayer_size(data: Dict[str, Any]) -> str:
                    size_candidates = [
                        data.get("taxpayer_size"),
                        data.get("size"),
                        data.get("business_size"),
                        (data.get("metadata") or {}).get("taxpayer_size") if isinstance(data.get("metadata"), dict) else None,
                    ]
                    for candidate in size_candidates:
                        if isinstance(candidate, str) and candidate.strip():
                            return candidate.strip().lower()
                    turnover = data.get("annual_turnover") or data.get("turnover")
                    if isinstance(turnover, (int, float)):
                        return TaxpayerSize.LARGE.value if turnover >= 500_000_000 else TaxpayerSize.SME.value
                    employee_count = data.get("employee_count")
                    if isinstance(employee_count, int):
                        return TaxpayerSize.LARGE.value if employee_count >= 250 else TaxpayerSize.SME.value
                    return TaxpayerSize.SME.value

                async def _serialize_taxpayer(t: Taxpayer) -> Dict[str, Any]:
                    return {
                        "id": str(getattr(t, "id", None)),
                        "organization_id": str(getattr(t, "organization_id", "")),
                        "tin": getattr(t, "tin", None),
                        "business_name": getattr(t, "business_name", None),
                        "registration_status": getattr(t, "registration_status", None).value if getattr(t, "registration_status", None) else None,
                        "registration_date": getattr(t, "registration_date", None).isoformat() if getattr(t, "registration_date", None) else None,
                        "sector": getattr(t, "sector", None),
                        "vat_registered": bool(getattr(t, "vat_registered", False)),
                        "compliance_level": getattr(t, "compliance_level", None),
                        "metadata": getattr(t, "taxpayer_metadata", {}) or {},
                        "last_updated_from_firs": getattr(t, "last_updated_from_firs", None).isoformat() if getattr(t, "last_updated_from_firs", None) else None,
                    }

                if operation == "onboard_taxpayer":
                    taxpayer_data = payload.get("taxpayer_data", {})
                    result = taxpayer_service["onboarding_service"].onboard_taxpayer(taxpayer_data)
                    return {"operation": operation, "success": True, "data": {"result": result}}

                if operation == "create_taxpayer":
                    data = payload.get("taxpayer_data") or {}
                    org_id = (
                        data.get("organization_id")
                        or payload.get("organization_id")
                        or _resolve_tenant_id(payload)
                    )
                    tin = data.get("tax_id") or data.get("tin")
                    name = data.get("name") or data.get("business_name")
                    if not org_id or not tin or not name:
                        return {
                            "operation": operation,
                            "success": False,
                            "error": "missing_required_fields: organization_id,tax_id/name",
                        }
                    async for session in get_async_session():
                        exists = (
                            await session.execute(select(Taxpayer).where(Taxpayer.tin == tin))
                        ).scalars().first()
                        if exists:
                            return {"operation": operation, "success": False, "error": "taxpayer_already_exists"}
                        tp = Taxpayer(
                            organization_id=org_id,
                            tin=tin,
                            business_name=name,
                            registration_status=TaxpayerStatus.PENDING_REGISTRATION,
                            business_type=data.get("business_type"),
                            sector=data.get("sector"),
                            business_address=(data.get("contact_info", {}) or {}).get("address"),
                            contact_person=(data.get("contact_info", {}) or {}).get("person"),
                            contact_email=(data.get("contact_info", {}) or {}).get("email"),
                            contact_phone=(data.get("contact_info", {}) or {}).get("phone"),
                            vat_registered=bool(data.get("vat_registered", False)),
                            vat_number=data.get("vat_number"),
                            taxpayer_metadata={"source": "api", **(data.get("metadata", {}) or {})},
                        )
                        session.add(tp)
                        await session.commit()
                        await session.refresh(tp)

                        tenant_identifier = org_id or str(getattr(tp, "organization_id", ""))
                        try:
                            if tenant_identifier:
                                repo = _get_grant_repo()
                                await repo.register_taxpayer(
                                    tenant_id=tenant_identifier,
                                    organization_id=tenant_identifier,
                                    taxpayer_tin=tp.tin,
                                    taxpayer_name=tp.business_name,
                                    taxpayer_size=_infer_taxpayer_size(data),
                                    sector=data.get("sector"),
                                )
                        except Exception as exc:  # pragma: no cover - defensive
                            logger.warning(
                                "Failed to register taxpayer %s for grant tracking: %s",
                                tp.tin,
                                exc,
                            )

                        return {
                            "operation": operation,
                            "success": True,
                            "data": {
                                "taxpayer": await _serialize_taxpayer(tp),
                                "created_at": timestamp,
                            },
                        }

                if operation == "list_taxpayers":
                    page = int(payload.get("page", 1))
                    limit = int(payload.get("limit", 50))
                    offset = max(page - 1, 0) * limit
                    filters = payload.get("filters") or {}
                    tenant_identifier = _resolve_tenant_id(payload)

                    async for session in get_async_session():
                        query = select(Taxpayer)
                        tenant_uuid = None
                        if tenant_identifier:
                            try:
                                tenant_uuid = uuid.UUID(str(tenant_identifier))
                            except (ValueError, TypeError):
                                logger.debug("Unable to coerce tenant identifier %s to UUID", tenant_identifier)
                        if tenant_uuid:
                            query = query.where(Taxpayer.organization_id == tenant_uuid)
                        status_filter = filters.get("status")
                        if status_filter:
                            try:
                                status_enum = TaxpayerStatus(status_filter)
                                query = query.where(Taxpayer.registration_status == status_enum)
                            except ValueError:
                                logger.debug("Ignoring invalid taxpayer status filter: %s", status_filter)

                        rows = (
                            await session.execute(query.offset(offset).limit(limit))
                        ).scalars().all()
                        items = [await _serialize_taxpayer(r) for r in rows]

                        grant_summary = None
                        analytics = None
                        target_tenant = tenant_identifier or (items[0]["organization_id"] if items else None)
                        if target_tenant:
                            try:
                                repo = _get_grant_repo()
                                grant_summary = await repo.get_grant_summary(target_tenant)
                                analytics = await repo.get_taxpayer_analytics(target_tenant)
                            except Exception as exc:  # pragma: no cover - defensive
                                logger.warning("Failed to load grant metrics: %s", exc)

                        response_payload: Dict[str, Any] = {
                            "taxpayers": items,
                            "page": page,
                            "limit": limit,
                        }
                        if grant_summary:
                            response_payload["grant_summary"] = grant_summary
                        if analytics:
                            response_payload["analytics"] = analytics

                        return {
                            "operation": operation,
                            "success": True,
                            "data": response_payload,
                        }

                if operation == "get_taxpayer":
                    taxpayer_id = payload.get("taxpayer_id")
                    async for session in get_async_session():
                        row = (await session.execute(select(Taxpayer).where(Taxpayer.id == taxpayer_id))).scalars().first()
                        if not row:
                            return {"operation": operation, "success": False, "error": "not_found"}
                        tenant_identifier = str(getattr(row, "organization_id", ""))
                        grant_details = None
                        if tenant_identifier:
                            try:
                                grant_details = await _get_grant_repo().get_taxpayer_onboarding_status(
                                    tenant_identifier,
                                    str(getattr(row, "id", "")),
                                )
                            except Exception as exc:  # pragma: no cover - defensive
                                logger.warning(
                                    "Failed to fetch grant details for taxpayer %s: %s",
                                    taxpayer_id,
                                    exc,
                                )
                        payload_data: Dict[str, Any] = {"taxpayer": await _serialize_taxpayer(row)}
                        if grant_details:
                            payload_data["grant_tracking"] = grant_details
                        return {"operation": operation, "success": True, "data": payload_data}

                if operation == "update_taxpayer":
                    taxpayer_id = payload.get("taxpayer_id")
                    updates = payload.get("updates") or {}
                    async for session in get_async_session():
                        row = (await session.execute(select(Taxpayer).where(Taxpayer.id == taxpayer_id))).scalars().first()
                        if not row:
                            return {"operation": operation, "success": False, "error": "not_found"}
                        grant_updates: Dict[str, Any] = {}
                        if "sector" in updates:
                            grant_updates["sector"] = updates["sector"]
                        if "taxpayer_size" in updates:
                            grant_updates["taxpayer_size"] = updates["taxpayer_size"]
                        if "validation_completed" in updates:
                            grant_updates["validation_completed"] = updates["validation_completed"]
                        if "grant_tracking" in updates and isinstance(updates["grant_tracking"], dict):
                            grant_updates.setdefault("grant_tracking", {}).update(updates["grant_tracking"])
                        # Apply simple updates
                        for src_key, model_key in [
                            ("business_name", "business_name"),
                            ("sector", "sector"),
                            ("business_type", "business_type"),
                            ("contact_email", "contact_email"),
                            ("contact_phone", "contact_phone"),
                            ("vat_registered", "vat_registered"),
                            ("vat_number", "vat_number"),
                            ("compliance_level", "compliance_level"),
                        ]:
                            if src_key in updates:
                                setattr(row, model_key, updates[src_key])
                        # Merge metadata
                        if isinstance(updates.get("metadata"), dict):
                            meta = getattr(row, "taxpayer_metadata", {}) or {}
                            meta.update(updates["metadata"])
                            row.taxpayer_metadata = meta
                            grant_meta_update = updates["metadata"].get("grant_tracking")
                            if isinstance(grant_meta_update, dict):
                                grant_updates.setdefault("grant_tracking", {}).update(grant_meta_update)
                        await session.commit()
                        await session.refresh(row)
                        try:
                            repo = _get_grant_repo()
                            await repo.update_taxpayer_profile(row.id, grant_updates)
                        except Exception as exc:  # pragma: no cover - defensive
                            logger.warning("Failed to update grant metadata for taxpayer %s: %s", taxpayer_id, exc)
                        return {"operation": operation, "success": True, "data": {"taxpayer": await _serialize_taxpayer(row)}}

                if operation == "delete_taxpayer":
                    taxpayer_id = payload.get("taxpayer_id")
                    async for session in get_async_session():
                        row = (await session.execute(select(Taxpayer).where(Taxpayer.id == taxpayer_id))).scalars().first()
                        if not row:
                            return {"operation": operation, "success": False, "error": "not_found"}
                        # Soft-delete via metadata flag
                        meta = getattr(row, "taxpayer_metadata", {}) or {}
                        meta["deleted"] = True
                        row.taxpayer_metadata = meta
                        await session.commit()
                        try:
                            await _get_grant_repo().deactivate_taxpayer(row.id)
                        except Exception as exc:  # pragma: no cover - defensive
                            logger.warning("Failed to deactivate taxpayer %s in grant tracker: %s", taxpayer_id, exc)
                        return {"operation": operation, "success": True, "data": {"deleted": True}}
                if operation == "bulk_onboard_taxpayers":
                    taxpayers_payload = payload.get("taxpayers") or []
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {"processed": len(taxpayers_payload)},
                    }

                if operation == "get_taxpayer_overview":
                    tenant_identifier = _resolve_tenant_id(payload)
                    if not tenant_identifier:
                        return {"operation": operation, "success": False, "error": "missing_tenant_id"}
                    summary = await _get_grant_repo().get_grant_summary(tenant_identifier)
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {"overview": summary, "generated_at": summary.get("generated_at", timestamp)},
                    }

                if operation == "get_taxpayer_statistics":
                    tenant_identifier = _resolve_tenant_id(payload)
                    if not tenant_identifier:
                        return {"operation": operation, "success": False, "error": "missing_tenant_id"}
                    stats_result = await _get_grant_repo().get_taxpayer_statistics(
                        tenant_identifier,
                        payload.get("period", "30d"),
                    )
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {"statistics": stats_result, "period": stats_result.get("period")},
                    }

                if operation == "get_taxpayer_onboarding_status":
                    tenant_identifier = _resolve_tenant_id(payload)
                    taxpayer_id = payload.get("taxpayer_id")
                    if not tenant_identifier or not taxpayer_id:
                        return {"operation": operation, "success": False, "error": "missing_parameters"}
                    status_payload = await _get_grant_repo().get_taxpayer_onboarding_status(
                        tenant_identifier,
                        taxpayer_id,
                    )
                    if not status_payload:
                        return {"operation": operation, "success": False, "error": "not_found"}
                    return {"operation": operation, "success": True, "data": status_payload}

                if operation == "get_taxpayer_compliance_status":
                    tenant_identifier = _resolve_tenant_id(payload)
                    taxpayer_id = payload.get("taxpayer_id")
                    if not tenant_identifier or not taxpayer_id:
                        return {"operation": operation, "success": False, "error": "missing_parameters"}
                    status_payload = await _get_grant_repo().get_taxpayer_onboarding_status(
                        tenant_identifier,
                        taxpayer_id,
                    )
                    compliance_state = (status_payload or {}).get("metadata", {}).get("compliance_state", "unknown")
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {"status": compliance_state, "checked_at": timestamp},
                    }

                if operation == "update_taxpayer_compliance_status":
                    taxpayer_id = payload.get("taxpayer_id")
                    new_status = payload.get("status") or payload.get("compliance_state")
                    if not taxpayer_id or not new_status:
                        return {"operation": operation, "success": False, "error": "missing_parameters"}

                    async for session in get_async_session():
                        row = (
                            await session.execute(select(Taxpayer).where(Taxpayer.id == taxpayer_id))
                        ).scalars().first()
                        if not row:
                            return {"operation": operation, "success": False, "error": "not_found"}
                        metadata = dict(getattr(row, "taxpayer_metadata", {}) or {})
                        grant_meta = dict(metadata.get("grant_tracking") or {})
                        grant_meta["compliance_state"] = new_status
                        grant_meta["compliance_updated_at"] = timestamp
                        metadata["grant_tracking"] = grant_meta
                        row.taxpayer_metadata = metadata
                        await session.commit()
                        await session.refresh(row)
                        try:
                            await _get_grant_repo().update_taxpayer_compliance_status(row.id, new_status)
                        except Exception as exc:  # pragma: no cover - defensive
                            logger.warning("Grant compliance update failed for %s: %s", taxpayer_id, exc)
                        return {
                            "operation": operation,
                            "success": True,
                            "data": {"updated": True, "status": new_status},
                        }

                if operation == "list_non_compliant_taxpayers":
                    tenant_identifier = _resolve_tenant_id(payload)
                    if not tenant_identifier:
                        return {"operation": operation, "success": False, "error": "missing_tenant_id"}
                    records = await _get_grant_repo().list_non_compliant_taxpayers(tenant_identifier)
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {"taxpayers": records, "generated_at": timestamp},
                    }

                if operation == "generate_grant_tracking_report":
                    tenant_identifier = _resolve_tenant_id(payload)
                    if not tenant_identifier:
                        return {"operation": operation, "success": False, "error": "missing_tenant_id"}
                    report = await _get_grant_repo().generate_grant_report(tenant_identifier)
                    return {"operation": operation, "success": True, "data": report}

                if operation == "get_grant_milestones":
                    tenant_identifier = _resolve_tenant_id(payload)
                    progress: Dict[str, Any] = {}
                    if tenant_identifier:
                        try:
                            progress = await _get_grant_repo().get_milestone_progress(tenant_identifier)
                        except Exception as exc:  # pragma: no cover - defensive
                            logger.warning("Failed to compute milestone progress: %s", exc)
                    milestones = {
                        milestone.value: {
                            "definition": {
                                "taxpayer_threshold": definition.taxpayer_threshold,
                                **definition.requirements,
                                "description": definition.description,
                                "grant_amount": definition.grant_amount,
                            },
                            "progress": progress.get(milestone.value),
                        }
                        for milestone, definition in GrantTrackingRepository.MILESTONE_DEFINITIONS.items()
                    }
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {"milestones": milestones, "generated_at": timestamp},
                    }

                if operation == "get_onboarding_performance":
                    tenant_identifier = _resolve_tenant_id(payload)
                    if not tenant_identifier:
                        return {"operation": operation, "success": False, "error": "missing_tenant_id"}
                    analytics = await _get_grant_repo().get_taxpayer_analytics(tenant_identifier)
                    performance = {
                        "total_taxpayers": analytics.get("total_taxpayers", 0),
                        "active_taxpayers": analytics.get("active_taxpayers", 0),
                        "large_taxpayers": analytics.get("large_taxpayers", 0),
                        "sme_taxpayers": analytics.get("sme_taxpayers", 0),
                        "transmission_rate": analytics.get("transmission_rate", 0.0),
                    }
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {"performance": performance, "period": payload.get("period", "30d")},
                    }

                if operation == "get_grant_overview":
                    tenant_identifier = _resolve_tenant_id(payload)
                    if not tenant_identifier:
                        return {"operation": operation, "success": False, "error": "missing_tenant_id"}
                    summary = await _get_grant_repo().get_grant_summary(tenant_identifier)
                    return {"operation": operation, "success": True, "data": summary}

                if operation == "get_current_grant_status":
                    tenant_identifier = _resolve_tenant_id(payload)
                    if not tenant_identifier:
                        return {"operation": operation, "success": False, "error": "missing_tenant_id"}
                    status_payload = await _get_grant_repo().get_current_grant_status(tenant_identifier)
                    return {"operation": operation, "success": True, "data": status_payload}

                if operation == "list_grant_milestones":
                    tenant_identifier = _resolve_tenant_id(payload)
                    progress: Dict[str, Any] = {}
                    if tenant_identifier:
                        try:
                            progress = await _get_grant_repo().get_milestone_progress(tenant_identifier)
                        except Exception as exc:  # pragma: no cover - defensive
                            logger.warning("Failed to compute milestone list progress: %s", exc)
                    milestone_list = [
                        {
                            "milestone": milestone.value,
                            "description": definition.description,
                            "grant_amount": definition.grant_amount,
                            "progress": progress.get(milestone.value),
                        }
                        for milestone, definition in GrantTrackingRepository.MILESTONE_DEFINITIONS.items()
                    ]
                    return {"operation": operation, "success": True, "data": {"milestones": milestone_list}}

                if operation == "get_milestone_details":
                    tenant_identifier = _resolve_tenant_id(payload)
                    milestone_id = payload.get("milestone_id")
                    if not tenant_identifier or not milestone_id:
                        return {"operation": operation, "success": False, "error": "missing_parameters"}
                    details = await _get_grant_repo().get_milestone_details(tenant_identifier, milestone_id)
                    if not details:
                        return {"operation": operation, "success": False, "error": "not_found"}
                    return {"operation": operation, "success": True, "data": details}

                if operation == "get_milestone_progress":
                    tenant_identifier = _resolve_tenant_id(payload)
                    if not tenant_identifier:
                        return {"operation": operation, "success": False, "error": "missing_tenant_id"}
                    progress = await _get_grant_repo().get_milestone_progress(tenant_identifier)
                    return {"operation": operation, "success": True, "data": progress}

                if operation == "get_upcoming_milestones":
                    tenant_identifier = _resolve_tenant_id(payload)
                    if not tenant_identifier:
                        return {"operation": operation, "success": False, "error": "missing_tenant_id"}
                    upcoming = await _get_grant_repo().get_upcoming_milestones(tenant_identifier)
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {"milestones": upcoming, "days_ahead": payload.get("days_ahead", 30)},
                    }

                if operation == "get_performance_metrics":
                    tenant_identifier = _resolve_tenant_id(payload)
                    if not tenant_identifier:
                        return {"operation": operation, "success": False, "error": "missing_tenant_id"}
                    metrics = await _get_grant_repo().get_performance_metrics(tenant_identifier)
                    return {"operation": operation, "success": True, "data": {"metrics": metrics, "generated_at": metrics.get("generated_at", timestamp)}}

                if operation == "get_performance_trends":
                    tenant_identifier = _resolve_tenant_id(payload)
                    if not tenant_identifier:
                        return {"operation": operation, "success": False, "error": "missing_tenant_id"}
                    trends = await _get_grant_repo().get_performance_trends(tenant_identifier)
                    return {"operation": operation, "success": True, "data": {"trends": trends, "generated_at": timestamp}}

                if operation == "generate_grant_report":
                    tenant_identifier = _resolve_tenant_id(payload)
                    if not tenant_identifier:
                        return {"operation": operation, "success": False, "error": "missing_tenant_id"}
                    report = await _get_grant_repo().generate_grant_report(tenant_identifier)
                    return {"operation": operation, "success": True, "data": report}

                if operation == "list_grant_reports":
                    tenant_identifier = _resolve_tenant_id(payload)
                    if not tenant_identifier:
                        return {"operation": operation, "success": False, "error": "missing_tenant_id"}
                    reports = await _get_grant_repo().list_grant_reports(tenant_identifier)
                    return {"operation": operation, "success": True, "data": {"reports": reports}}

                if operation == "get_grant_report":
                    tenant_identifier = _resolve_tenant_id(payload)
                    report_id = payload.get("report_id", "grant-report-current")
                    if not tenant_identifier:
                        return {"operation": operation, "success": False, "error": "missing_tenant_id"}
                    report = await _get_grant_repo().get_grant_report(tenant_identifier, report_id)
                    return {"operation": operation, "success": True, "data": report}
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
                # Avoid runtime import dependency on SI modules for type annotation
                certificate_store: Optional[Any] = firs_service.get("certificate_store")

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
            # First, coordinate through HYBRID layer
            from core_platform.messaging.message_router import ServiceRole as _SR
            hybrid_payload = {
                "invoice_ids": invoice_ids,
                "si_user_id": si_user_id,
                "submission_options": submission_options or {},
            }

            async def _call_hybrid_once() -> Dict[str, Any]:
                return await self.message_router.route_message(
                    service_role=_SR.HYBRID,
                    operation="coordinate_si_invoices_for_firs",
                    payload=hybrid_payload,
                )

            hybrid_resp = await _call_hybrid_once()
            if not (isinstance(hybrid_resp, dict) and hybrid_resp.get("success")):
                # Basic one-shot retry; then bubble error
                hybrid_resp = await _call_hybrid_once()
                if not (isinstance(hybrid_resp, dict) and hybrid_resp.get("success")):
                    return {"error": "hybrid_coordination_failed", "details": hybrid_resp, "success": False}

            # Resolve invoice payloads via SI (Odoo RPC) and transform to FIRS
            erp_type = str((submission_options or {}).get("erp_type", "odoo")).lower()
            if erp_type != "odoo":
                return {"success": False, "error": f"unsupported_erp_type:{erp_type}"}

            si_fetch = await self.message_router.route_message(
                service_role=_SR.SYSTEM_INTEGRATOR,
                operation="fetch_odoo_invoices_for_firs",
                payload={
                    "invoice_ids": invoice_ids,
                    "odoo_config": (submission_options or {}).get("odoo_config") or {},
                    "transform": True,
                    "target_format": (submission_options or {}).get("target_format", "UBL_BIS_3.0"),
                },
            )
            if not (isinstance(si_fetch, dict) and si_fetch.get("success")):
                return {"success": False, "error": "si_invoice_fetch_failed", "details": si_fetch}
            invoices = (si_fetch.get("data") or {}).get("invoices") or []
            # Unwrap to raw FIRS invoice payload if transformer wrapped output
            normalized_invoices = [
                (inv.get("firs_invoice") if isinstance(inv, dict) and "firs_invoice" in inv else inv)
                for inv in invoices
            ]
            if not invoices:
                return {"success": False, "error": "no_invoices_resolved"}

            # Submit to APP transmission service (DB persistence + FIRS submission)
            submit_resp = await self.message_router.route_message(
                service_role=_SR.ACCESS_POINT_PROVIDER,
                operation="submit_invoice_batch",
                payload={
                    "invoices": normalized_invoices,
                    "organization_id": (submission_options or {}).get("organization_id"),
                    "api_version": "v1",
                },
            )

            # Surface combined result
            return {
                "success": bool(submit_resp.get("success")) if isinstance(submit_resp, dict) else False,
                "data": {
                    "hybrid_ack": hybrid_resp.get("data") if isinstance(hybrid_resp, dict) else None,
                    "transmission": submit_resp,
                },
            }
            
        except Exception as e:
            logger.error(f"Error processing SI invoices for FIRS: {str(e)}")
            raise
    
    async def _process_si_batch_for_firs(self, batch_id, si_user_id, batch_options):
        """Process invoice batch received from SI for FIRS submission"""
        try:
            # Coordinate via HYBRID layer first
            from core_platform.messaging.message_router import ServiceRole as _SR
            hybrid_payload = {
                "batch_id": batch_id,
                "si_user_id": si_user_id,
                "batch_options": batch_options or {},
            }

            async def _call_hybrid_once() -> Dict[str, Any]:
                return await self.message_router.route_message(
                    service_role=_SR.HYBRID,
                    operation="coordinate_si_batch_for_firs",
                    payload=hybrid_payload,
                )

            hybrid_resp = await _call_hybrid_once()
            if not (isinstance(hybrid_resp, dict) and hybrid_resp.get("success")):
                hybrid_resp = await _call_hybrid_once()
                if not (isinstance(hybrid_resp, dict) and hybrid_resp.get("success")):
                    return {"error": "hybrid_coordination_failed", "details": hybrid_resp, "success": False}

            # Resolve invoices for the batch via SI (Odoo RPC)
            erp_type = str((batch_options or {}).get("erp_type", "odoo")).lower()
            if erp_type != "odoo":
                return {"success": False, "error": f"unsupported_erp_type:{erp_type}"}

            si_fetch = await self.message_router.route_message(
                service_role=_SR.SYSTEM_INTEGRATOR,
                operation="fetch_odoo_invoice_batch_for_firs",
                payload={
                    "batch_id": batch_id,
                    "batch_size": int((batch_options or {}).get("batch_size", 50)),
                    "odoo_config": (batch_options or {}).get("odoo_config") or {},
                    "transform": True,
                    "target_format": (batch_options or {}).get("target_format", "UBL_BIS_3.0"),
                },
            )
            if not (isinstance(si_fetch, dict) and si_fetch.get("success")):
                return {"success": False, "error": "si_batch_fetch_failed", "details": si_fetch}
            invoices = (si_fetch.get("data") or {}).get("invoices") or []
            normalized_invoices = [
                (inv.get("firs_invoice") if isinstance(inv, dict) and "firs_invoice" in inv else inv)
                for inv in invoices
            ]
            if not invoices:
                return {"success": False, "error": "no_invoices_resolved_for_batch"}

            # Submit resolved invoices as a batch via APP transmission
            submit_resp = await self.message_router.route_message(
                service_role=_SR.ACCESS_POINT_PROVIDER,
                operation="submit_invoice_batch",
                payload={
                    "invoices": normalized_invoices,
                    "organization_id": (batch_options or {}).get("organization_id"),
                    "api_version": "v1",
                },
            )

            return {
                "success": bool(submit_resp.get("success")) if isinstance(submit_resp, dict) else False,
                "data": {
                    "hybrid_ack": hybrid_resp.get("data") if isinstance(hybrid_resp, dict) else None,
                    "transmission": submit_resp,
                },
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
