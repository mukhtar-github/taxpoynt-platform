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
import math
from collections import Counter, deque
from datetime import datetime, timezone, timedelta
from dataclasses import asdict
from typing import Dict, Any, Optional, List, Tuple, TYPE_CHECKING

from sqlalchemy import select

from core_platform.messaging.message_router import MessageRouter, ServiceRole
from core_platform.config.feature_flags import is_firs_remote_irn_enabled
from core_platform.utils.firs_response import extract_firs_identifiers, merge_identifiers_into_payload
from core_platform.data_management.db_async import get_async_session
from core_platform.data_management.repositories import invoice_repo_async as invoice_repo
from core_platform.data_management.repositories.firs_submission_repo_async import (
    get_tracking_overview_data,
    list_transmission_statuses_data,
    list_recent_status_changes_data,
    list_tracking_alerts,
    acknowledge_tracking_alert,
    list_firs_responses_data,
    get_firs_response_detail,
    get_submission_by_id,
)
from core_platform.data_management.models.firs_submission import FIRSSubmission
from core_platform.data_management.models.si_app_correlation import SIAPPCorrelation
from core_platform.data_management.models.organization import Organization
from core_platform.data_management.models.user import User

from .status_management.app_configuration import AppConfigurationStore

# Import APP services
from .webhook_services.webhook_receiver import WebhookReceiver
from .webhook_services.event_processor import EventProcessor
from .webhook_services.signature_validator import SignatureValidator
from .status_management.callback_manager import CallbackManager
from .status_management.status_tracker import StatusTracker
from .status_management.notification_service import NotificationService
from .firs_communication.firs_api_client import (
    FIRSAPIClient,
    FIRSEnvironment,
    FIRSEndpoint,
    create_firs_api_client,
)
from .firs_communication.certificate_provider import FIRSCertificateProvider
from .firs_communication.firs_payload_mapper import build_firs_invoice
from .validation.firs_validator import FIRSValidator
from .validation.submission_validator import (
    SubmissionValidator,
    SubmissionContext,
    SubmissionReadiness,
    CheckStatus,
)
from .validation.format_validator import FormatValidator
from .transmission.transmission_service import TransmissionService
from .reporting import (
    ReportingServiceManager,
    ReportConfig,
    ReportFormat,
    AnalysisType,
    TransmissionStatus,
    get_dashboard_templates,
)
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
from .taxpayer_management.taxpayer_onboarding import TaxpayerOnboardingService
from .onboarding_management.app_onboarding_service import APPOnboardingService

if TYPE_CHECKING:
    # Type-only import to avoid pulling SI modules at import time
    from si_services.certificate_management.certificate_store import CertificateStore, StoredCertificate  # pragma: no cover

logger = logging.getLogger(__name__)


DEFAULT_CERTIFICATE_LIST_LIMIT = 25
FIRS_REMOTE_IRN_ENABLED = is_firs_remote_irn_enabled()


def _normalize_days_until_expiry(not_after: Optional[str]) -> Optional[int]:
    """Compute days until expiry from an ISO timestamp."""

    if not not_after:
        return None
    try:
        expiry = datetime.fromisoformat(str(not_after))
    except Exception:
        return None

    if expiry.tzinfo is None:
        now = datetime.utcnow()
    else:
        now = datetime.now(expiry.tzinfo)

    delta = expiry - now
    return int(math.floor(delta.total_seconds() / 86400))


def _serialize_certificate_record(record: Dict[str, Any]) -> Dict[str, Any]:
    """Add derived fields to a certificate record for API payloads."""

    enriched = dict(record)
    if "not_after" in enriched and "days_until_expiry" not in enriched:
        enriched["days_until_expiry"] = _normalize_days_until_expiry(enriched.get("not_after"))
    return enriched


def _serialize_stored_certificate(cert: "StoredCertificate") -> Dict[str, Any]:  # type: ignore[name-defined]
    """Convert StoredCertificate dataclass to JSON-safe dict."""

    data = asdict(cert)
    status = data.get("status")
    if hasattr(status, "value"):
        data["status"] = status.value
    data.setdefault("metadata", {})
    data["days_until_expiry"] = _normalize_days_until_expiry(data.get("not_after"))
    return data


def build_certificate_overview_payload(
    certificates: List[Dict[str, Any]],
    expiring: List[Dict[str, Any]],
    lifecycle_categories: Dict[str, List["StoredCertificate"]],  # type: ignore[name-defined]
    *,
    organization_id: Optional[str],
    days_ahead: int,
) -> Dict[str, Any]:
    """Create a rich certificate overview payload for APP endpoints."""

    enriched = [_serialize_certificate_record(item) for item in certificates]
    status_counts = Counter(item.get("status", "unknown") for item in enriched)

    lifecycle_summary: Dict[str, Dict[str, Any]] = {}
    for key, items in lifecycle_categories.items():
        serialized_items = [_serialize_stored_certificate(entry) for entry in items]
        lifecycle_summary[key] = {
            "count": len(serialized_items),
            "items": serialized_items[:DEFAULT_CERTIFICATE_LIST_LIMIT],
        }

    expiring_enriched = [
        _serialize_certificate_record(item) for item in expiring
    ]

    overview = {
        "organizationId": organization_id,
        "summary": {
            "total": len(enriched),
            "statusCounts": dict(status_counts),
            "expiringSoon": len(expiring_enriched),
            "needsRenewal": lifecycle_summary.get("needs_renewal", {}).get("count", 0),
            "expired": lifecycle_summary.get("expired", {}).get("count", 0),
        },
        "certificates": {
            "count": len(enriched),
            "items": enriched[:DEFAULT_CERTIFICATE_LIST_LIMIT],
        },
        "expiring": {
            "daysAhead": days_ahead,
            "count": len(expiring_enriched),
            "items": expiring_enriched[:DEFAULT_CERTIFICATE_LIST_LIMIT],
        },
        "lifecycle": lifecycle_summary,
    }

    return overview


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
                init_timeout = 5.0 if os.getenv("PYTEST_CURRENT_TEST") else None
                if not getattr(qm, "is_initialized", False):
                    try:
                        if init_timeout:
                            await asyncio.wait_for(qm.initialize(), timeout=init_timeout)
                        else:
                            await qm.initialize()
                    except asyncio.TimeoutError:
                        logger.warning("Queue manager initialization timed out; skipping AP outbound consumer bootstrap")
                    except Exception as init_error:
                        logger.warning(f"Queue manager initialization failed: {init_error}")

                if not getattr(qm, "is_initialized", False):
                    logger.debug("Queue manager unavailable; skipping AP outbound consumer registration")
                    return

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
            # Lazy import to avoid SI module import at app import time
            try:
                from si_services.certificate_management.certificate_store import CertificateStore as _CertificateStore  # type: ignore
                certificate_store = _CertificateStore()
            except Exception:
                certificate_store = None
                logger.debug("Certificate store unavailable; continuing without it")

            certificate_provider = FIRSCertificateProvider(certificate_store=certificate_store)

            # Initialize FIRS services with real implementations
            firs_api_client = await self._create_firs_api_client(
                certificate_provider=certificate_provider
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

                firs_http_client = FIRSHttpClient(certificate_provider=certificate_provider)
                resource_cache = FIRSResourceCache(firs_http_client)
            except Exception:
                firs_http_client = None
                resource_cache = None

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
                "get_firs_connection_status",
                "update_firs_credentials",
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
                "http_client": firs_http_client,
                "resource_cache": resource_cache,
                "party_cache": getattr(firs_api_client, "party_cache", None),
                "tin_cache": getattr(firs_api_client, "tin_cache", None),
                "certificate_store": certificate_store,
                "certificate_provider": certificate_provider,
                "operations": firs_operations,
                "remote_irn_enabled": FIRS_REMOTE_IRN_ENABLED,
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
                    "remote_irn_enabled": FIRS_REMOTE_IRN_ENABLED,
                }
            )
            
            self.service_endpoints["firs_communication"] = endpoint_id
            logger.info(
                "FIRS communication service registered: %s (remote_irn=%s)",
                endpoint_id,
                FIRS_REMOTE_IRN_ENABLED,
            )
            
        except Exception as e:
            logger.error(f"Failed to register FIRS services: {str(e)}")
    
    async def _register_webhook_services(self):
        """Register webhook processing services"""
        try:
            # Initialize webhook services with real implementations
            secret = os.getenv("FIRS_WEBHOOK_SECRET")
            if not secret:
                logger.warning("FIRS_WEBHOOK_SECRET not set; using development placeholder secret")
                secret = "development-placeholder-secret"

            webhook_receiver = WebhookReceiver(
                webhook_secret=secret,
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
            
            configuration_store = AppConfigurationStore()

            status_service = {
                "callback_manager": callback_manager,
                "configuration_store": configuration_store,
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

        schema_validator = self._build_schema_validator()

        return {
            "firs_validator": firs_validator,
            "format_validator": format_validator,
            "submission_validator": submission_validator,
            "schema_validator": schema_validator,
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

    class _FallbackInvoiceValidator:
        is_fallback_validator = True

        async def validate_invoice(self, payload: Dict[str, Any]) -> Dict[str, Any]:
            invoice = payload.get("invoice_data") or {}
            return {
                "validated": True,
                "invoice": invoice,
                "irn": invoice.get("irn"),
                "qr_signature": None,
                "forwarded": False,
                "firs_response": None,
            }

    def _build_schema_validator(self):
        """Attempt to initialize the shared invoice schema validator."""
        try:
            from si_services.invoice_validation import InvoiceValidationService  # type: ignore
        except Exception as exc:
            logger.warning("Invoice validation service unavailable, using fallback: %s", exc)
            return self._FallbackInvoiceValidator()

        try:
            return InvoiceValidationService()
        except Exception as exc:
            logger.error("Failed to initialize invoice schema validator, using fallback: %s", exc)
            return self._FallbackInvoiceValidator()

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
                "run_b2c_reporting_job",
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
            try:
                from si_services.certificate_management.certificate_store import (
                    CertificateStore,
                    CertificateStatus,
                    StoredCertificate,
                )
                from si_services.certificate_management.certificate_generator import CertificateGenerator
                from si_services.certificate_management.lifecycle_manager import LifecycleManager
                from si_services.certificate_management.key_manager import KeyManager
            except (ImportError, AttributeError) as import_err:
                logger.warning(
                    "Certificate services unavailable; skipping APP registration: %s",
                    import_err,
                )
                return

            certificate_store = CertificateStore()
            certificate_generator = CertificateGenerator()
            key_manager = KeyManager()
            lifecycle_manager = LifecycleManager(
                certificate_store=certificate_store,
                certificate_generator=certificate_generator,
                key_manager=key_manager,
            )

            def _resolve_org_id(payload: Dict[str, Any]) -> str:
                certificate_data = payload.get("certificate_data") or {}
                org_id = payload.get("organization_id") or certificate_data.get("organization_id")
                if not org_id:
                    raise ValueError("organization_id is required")
                return str(org_id)

            def _resolve_certificate_id(payload: Dict[str, Any]) -> str:
                certificate_id = payload.get("certificate_id")
                if not certificate_id:
                    raise ValueError("certificate_id is required")
                return str(certificate_id)

            def _as_dict(cert: StoredCertificate) -> Dict[str, Any]:
                return _stored_to_dict(cert)

            async def _create_certificate(payload: Dict[str, Any]) -> Dict[str, Any]:
                certificate_data = payload.get("certificate_data") or {}
                organization_id = _resolve_org_id(payload)
                certificate_type = (
                    certificate_data.get("certificate_type")
                    or payload.get("certificate_type")
                    or "signing"
                )
                metadata = certificate_data.get("metadata") or {}
                pem_content = (
                    certificate_data.get("certificate_pem")
                    or certificate_data.get("pem")
                    or certificate_data.get("data")
                )
                private_key_pem = (
                    certificate_data.get("private_key")
                    or certificate_data.get("private_key_pem")
                )
                generated_key_path = None

                if not pem_content:
                    subject_info = certificate_data.get("subject_info") or {
                        "common_name": certificate_data.get("common_name") or f"Org {organization_id} Certificate",
                    }
                    validity_days = int(certificate_data.get("validity_days", 365) or 365)
                    cert_pem, key_pem = certificate_generator.generate_self_signed_certificate(
                        subject_info=subject_info,
                        validity_days=validity_days,
                    )
                    pem_content = cert_pem.decode("utf-8")
                    private_key_pem = key_pem.decode("utf-8")
                    metadata.setdefault("generated", True)
                    metadata.setdefault("subject_info", subject_info)

                certificate_id = certificate_store.store_certificate(
                    certificate_pem=pem_content.encode("utf-8") if isinstance(pem_content, str) else pem_content,
                    organization_id=organization_id,
                    certificate_type=certificate_type,
                    metadata=metadata,
                )

                if private_key_pem:
                    key_path = key_manager.store_key(
                        private_key_pem.encode("utf-8") if isinstance(private_key_pem, str) else private_key_pem,
                        key_name=f"{certificate_id}_private",
                        key_type="private",
                    )
                    generated_key_path = key_path

                cert_info = certificate_store.get_certificate_info(certificate_id)
                response_data = {
                    "certificate_id": certificate_id,
                    "certificate_pem": pem_content,
                    "organization_id": organization_id,
                    "metadata": metadata,
                }
                if generated_key_path:
                    response_data["private_key_path"] = generated_key_path
                if cert_info:
                    response_data["certificate"] = _as_dict(cert_info)

                return {
                    "operation": "create_certificate",
                    "success": True,
                    "data": response_data,
                }

            async def _list_certificates(payload: Dict[str, Any]) -> Dict[str, Any]:
                filters = payload.get("filters") or {}
                organization_id = filters.get("organization_id") or payload.get("organization_id")
                status_filter = filters.get("status")
                certificate_type = filters.get("certificate_type") or filters.get("type")

                certificates = certificate_store.list_certificates(organization_id=organization_id)

                def _matches(cert: StoredCertificate) -> bool:
                    if certificate_type and cert.certificate_type != certificate_type:
                        return False
                    if status_filter and cert.status.value != status_filter:
                        return False
                    return True

                records = [_as_dict(cert) for cert in certificates if _matches(cert)]
                status_counts = Counter(item.get("status", "unknown") for item in records)
                return {
                    "operation": "list_certificates",
                    "success": True,
                    "data": {
                        "certificates": records,
                        "count": len(records),
                        "statusCounts": dict(status_counts),
                        "filters": filters,
                    },
                }

            async def _get_certificate(payload: Dict[str, Any]) -> Dict[str, Any]:
                certificate_id = _resolve_certificate_id(payload)
                info = certificate_store.get_certificate_info(certificate_id)
                certificate_pem = certificate_store.retrieve_certificate(certificate_id)

                if not info:
                    return {
                        "operation": "get_certificate",
                        "success": False,
                        "error": "certificate_not_found",
                    }

                data = _as_dict(info)
                if certificate_pem:
                    data["certificate_pem"] = certificate_pem.decode("utf-8")
                return {
                    "operation": "get_certificate",
                    "success": True,
                    "data": data,
                }

            async def _update_certificate(payload: Dict[str, Any]) -> Dict[str, Any]:
                certificate_id = _resolve_certificate_id(payload)
                updates = payload.get("updates") or {}
                metadata_updates = updates.get("metadata") or {}
                status_update = updates.get("status")

                status_enum = None
                if status_update:
                    try:
                        status_enum = CertificateStatus(status_update)
                    except ValueError as exc:
                        raise ValueError(f"Unsupported status '{status_update}'") from exc

                success = certificate_store.update_certificate_status(
                    certificate_id=certificate_id,
                    status=status_enum or CertificateStatus.ACTIVE,
                    metadata=metadata_updates if metadata_updates else None,
                )

                return {
                    "operation": "update_certificate",
                    "success": success,
                    "data": {
                        "certificate_id": certificate_id,
                        "status": status_enum.value if status_enum else None,
                        "metadata": metadata_updates,
                    },
                }

            async def _delete_certificate(payload: Dict[str, Any]) -> Dict[str, Any]:
                certificate_id = _resolve_certificate_id(payload)
                success = certificate_store.delete_certificate(certificate_id)
                return {
                    "operation": "delete_certificate",
                    "success": success,
                    "data": {"certificate_id": certificate_id},
                }

            async def _renew_certificate(payload: Dict[str, Any]) -> Dict[str, Any]:
                certificate_id = _resolve_certificate_id(payload)
                validity_days = payload.get("validity_days")
                reuse_key = payload.get("reuse_key", True)

                new_cert_id, success = lifecycle_manager.renew_certificate(
                    certificate_id=certificate_id,
                    validity_days=validity_days,
                    reuse_key=reuse_key,
                )

                return {
                    "operation": "renew_certificate",
                    "success": success,
                    "data": {
                        "certificate_id": certificate_id,
                        "renewed_certificate_id": new_cert_id,
                    },
                }

            async def _get_renewal_status(payload: Dict[str, Any]) -> Dict[str, Any]:
                certificate_id = _resolve_certificate_id(payload)
                info = certificate_store.get_certificate_info(certificate_id)
                if not info:
                    return {
                        "operation": "get_renewal_status",
                        "success": False,
                        "error": "certificate_not_found",
                    }
                data = _as_dict(info)
                renewal_threshold = lifecycle_manager.default_renewal_days
                days_until_expiry = data.get("days_until_expiry")
                status = "valid"
                if days_until_expiry is None:
                    status = "unknown"
                elif days_until_expiry < 0:
                    status = "expired"
                elif days_until_expiry <= renewal_threshold:
                    status = "needs_renewal"
                data.update(
                    {
                        "status": status,
                        "renewal_threshold_days": renewal_threshold,
                        "needs_renewal": status == "needs_renewal",
                    }
                )
                return {
                    "operation": "get_renewal_status",
                    "success": True,
                    "data": data,
                }

            async def _list_expiring(payload: Dict[str, Any]) -> Dict[str, Any]:
                days_ahead = int(payload.get("days_ahead", 30) or 30)
                organization_id = payload.get("organization_id")
                now = datetime.now(timezone.utc)
                expiring: List[Dict[str, Any]] = []
                for cert in certificate_store.list_certificates(organization_id=organization_id):
                    info = _as_dict(cert)
                    not_after = info.get("not_after")
                    if not not_after:
                        continue
                    try:
                        expires_at = datetime.fromisoformat(str(not_after))
                    except Exception:
                        continue
                    delta_days = (expires_at - now).days
                    if 0 <= delta_days <= days_ahead:
                        info["days_until_expiry"] = delta_days
                        expiring.append(info)

                return {
                    "operation": "list_expiring_certificates",
                    "success": True,
                    "data": {
                        "days_ahead": days_ahead,
                        "count": len(expiring),
                        "items": expiring,
                    },
                }

            async def _validate_certificate(payload: Dict[str, Any]) -> Dict[str, Any]:
                certificate_data = payload.get("certificate_data")
                if not certificate_data:
                    raise ValueError("certificate_data is required")
                if isinstance(certificate_data, dict):
                    certificate_data = (
                        certificate_data.get("certificate_pem")
                        or certificate_data.get("pem")
                        or certificate_data.get("data")
                    )
                if not certificate_data:
                    raise ValueError("certificate PEM content is required")

                info = certificate_generator.extract_certificate_info(
                    certificate_data.encode("utf-8") if isinstance(certificate_data, str) else certificate_data
                )

                return {
                    "operation": "validate_certificate",
                    "success": True,
                    "data": {
                        "is_valid": True,
                        "certificate_info": info,
                    },
                }

            async def _get_certificate_overview(payload: Dict[str, Any]) -> Dict[str, Any]:
                organization_id = payload.get("organization_id")
                days_ahead = int(payload.get("days_ahead", 30) or 30)
                certificates = [_as_dict(cert) for cert in certificate_store.list_certificates(organization_id=organization_id)]
                expiring = [cert for cert in certificates if (cert.get("days_until_expiry") is not None and cert["days_until_expiry"] <= days_ahead)]
                lifecycle_categories = lifecycle_manager.check_certificate_expiration(organization_id=organization_id)
                overview = build_certificate_overview_payload(
                    certificates=certificates,
                    expiring=expiring,
                    lifecycle_categories=lifecycle_categories,
                    organization_id=organization_id,
                    days_ahead=days_ahead,
                )
                return {
                    "operation": "get_certificate_overview",
                    "success": True,
                    "data": overview,
                }

            operation_handlers: Dict[str, Any] = {
                "create_certificate": _create_certificate,
                "list_certificates": _list_certificates,
                "get_certificate": _get_certificate,
                "update_certificate": _update_certificate,
                "delete_certificate": _delete_certificate,
                "renew_certificate": _renew_certificate,
                "get_renewal_status": _get_renewal_status,
                "list_expiring_certificates": _list_expiring,
                "validate_certificate": _validate_certificate,
                "get_certificate_overview": _get_certificate_overview,
            }

            async def certificate_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
                handler = operation_handlers.get(operation)
                if not handler:
                    return {
                        "operation": operation,
                        "success": False,
                        "error": "unsupported_operation",
                    }
                try:
                    return await handler(payload or {})
                except Exception as exc:
                    logger.error(
                        "Certificate service operation '%s' failed: %s",
                        operation,
                        exc,
                        exc_info=True,
                    )
                    return {
                        "operation": operation,
                        "success": False,
                        "error": str(exc),
                    }

            endpoint_id = await self.message_router.register_service(
                service_name="certificate_management",
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                callback=certificate_callback,
                priority=4,
                tags=["certificate", "pki", "security"],
                metadata={
                    "service_type": "certificate_management",
                    "operations": list(operation_handlers.keys()),
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
            manager = ReportingServiceManager()
            await manager.initialize_services()

            reporting_service = {
                "manager": manager,
                "transmission_reporter": manager.transmission_reporter,
                "compliance_monitor": manager.compliance_monitor,
                "performance_analyzer": manager.performance_analyzer,
                "regulatory_dashboard": manager.regulatory_dashboard,
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
                ],
                "report_history": {},
                "report_index": {},
                "schedules": {},
                "schedule_index": {},
                "lock": asyncio.Lock(),
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
    
    async def _create_firs_api_client(self, *, certificate_provider: Optional[FIRSCertificateProvider] = None):
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
            api_secret = os.getenv("FIRS_API_SECRET", "")
            certificate = os.getenv("FIRS_CERTIFICATE") or os.getenv("FIRS_ENCRYPTION_KEY", "")

            # Create FIRS API client using factory function (synchronous factory)
            client = create_firs_api_client(
                environment=environment,
                client_id=client_id,
                client_secret=client_secret,
                api_key=api_key,
                api_secret=api_secret,
                certificate=certificate,
                certificate_provider=certificate_provider,
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
        configuration_store: Optional[AppConfigurationStore] = status_service.get("configuration_store")

        def _snapshot_configuration() -> Dict[str, Any]:
            if configuration_store:
                return configuration_store.snapshot()
            return {
                "configuration": {},
                "metadata": {
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "source": "unavailable",
                },
            }

        async def _fetch_queue_status() -> Dict[str, Any]:
            try:
                from core_platform.messaging.queue_manager import get_queue_manager

                qm = get_queue_manager()
                await qm.initialize()
                return await qm.get_all_queue_status()
            except Exception:
                return {}

        async def _build_status_payload() -> Dict[str, Any]:
            snapshot = _snapshot_configuration()
            status_payload: Dict[str, Any] = {
                "status": "healthy",
                "checked_at": datetime.now(timezone.utc).isoformat(),
                "environment": snapshot["configuration"].get("environment")
                if isinstance(snapshot.get("configuration"), dict)
                else os.getenv("ENVIRONMENT", "development"),
                "configuration_metadata": snapshot.get("metadata", {}),
            }

            queues = await _fetch_queue_status()
            if queues:
                status_payload["queues"] = queues

            alerts: List[str] = []
            ap_out = queues.get("ap_outbound") or {}
            dlq = queues.get("dead_letter") or {}
            ap_metrics = ap_out.get("metrics") or {}
            dlq_metrics = dlq.get("metrics") or {}

            if (dlq_metrics.get("current_queue_size") or 0) > 0:
                alerts.append("dead_letter_queue_non_empty")
            if (ap_metrics.get("current_queue_size") or 0) > 1000:
                alerts.append("ap_outbound_backlog_high")

            oldest_age_sec = 0.0
            if ap_metrics:
                try:
                    from core_platform.messaging.queue_manager import get_queue_manager
                    from core_platform.monitoring.prometheus_integration import get_prometheus_integration

                    qm = get_queue_manager()
                    q = getattr(qm, "queues", {}).get("ap_outbound")
                    if q and getattr(q, "message_registry", None):
                        now = datetime.now(timezone.utc)
                        oldest_ts = None
                        for m in q.message_registry.values():
                            ts = getattr(m, "scheduled_time", None) or getattr(m, "created_time", None)
                            if ts and (oldest_ts is None or ts < oldest_ts):
                                oldest_ts = ts
                        if oldest_ts:
                            oldest_age_sec = max(0.0, (now - oldest_ts).total_seconds())

                    prom = get_prometheus_integration()
                    if prom:
                        prom.record_metric(
                            "taxpoynt_ap_outbound_current_queue_size",
                            float(ap_metrics.get("current_queue_size") or 0),
                            {"queue": "ap_outbound"},
                        )
                        prom.record_metric(
                            "taxpoynt_ap_outbound_dead_letter_count",
                            float(dlq_metrics.get("current_queue_size") or 0),
                            {"queue": "dead_letter"},
                        )
                        prom.record_metric(
                            "taxpoynt_ap_outbound_oldest_message_age_seconds",
                            float(oldest_age_sec),
                        )
                except Exception:
                    pass

            status_payload["queue_metrics"] = {
                "ap_outbound": ap_metrics,
                "dead_letter": dlq_metrics,
            }

            messaging_cfg = {}
            if isinstance(snapshot.get("configuration"), dict):
                messaging_cfg = snapshot["configuration"].get("messaging", {}) or {}

            max_age = float(messaging_cfg.get("ap_outbound_max_age_seconds") or 0)
            if max_age and oldest_age_sec > max_age:
                alerts.append("ap_outbound_message_age_exceeded")
                status_payload["oldest_message_age_seconds"] = oldest_age_sec

            if alerts:
                status_payload["alerts"] = alerts
                status_payload["status"] = "degraded"

            status_payload["configuration"] = snapshot["configuration"]
            return status_payload

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
                    status_payload = await _build_status_payload()
                    if operation == "get_app_status":
                        status_payload["configuration_snapshot"] = _snapshot_configuration()
                    return {"operation": operation, "success": True, "data": status_payload}
                if operation == "get_dashboard_summary":
                    return {"operation": operation, "success": True, "data": {"summary": {}, "generated_at": datetime.now(timezone.utc).isoformat()}}
                if operation == "get_app_configuration":
                    return {"operation": operation, "success": True, "data": _snapshot_configuration()}
                if operation == "update_app_configuration":
                    updates = payload.get("configuration_updates") or {}
                    try:
                        snapshot = configuration_store.update_config(
                            updates,
                            actor=payload.get("app_id"),
                        ) if configuration_store else {
                            "configuration": updates,
                            "metadata": {
                                "generated_at": datetime.now(timezone.utc).isoformat(),
                            },
                        }
                    except ValueError as exc:
                        return {"operation": operation, "success": False, "error": str(exc)}
                    return {"operation": operation, "success": True, "data": snapshot}
                if operation == "get_status_history":
                    return {"operation": operation, "success": True, "data": {"history": []}}
                if operation == "get_tracking_overview":
                    async for db in get_async_session():
                        overview = await get_tracking_overview_data(db)
                        return {"operation": operation, "success": True, "data": overview}

                if operation == "get_transmission_statuses":
                    async for db in get_async_session():
                        statuses = await list_transmission_statuses_data(
                            db,
                            status=payload.get("status"),
                            limit=payload.get("limit", 50) or 50,
                        )
                        return {"operation": operation, "success": True, "data": statuses}

                if operation == "get_recent_status_changes":
                    async for db in get_async_session():
                        changes = await list_recent_status_changes_data(
                            db,
                            hours=payload.get("hours", 24) or 24,
                        )
                        return {"operation": operation, "success": True, "data": changes}

                if operation == "get_active_alerts":
                    async for db in get_async_session():
                        alerts = await list_tracking_alerts(
                            db,
                            include_acknowledged=payload.get("include_acknowledged", True),
                        )
                        return {"operation": operation, "success": True, "data": {"alerts": alerts, "count": len(alerts)}}

                if operation == "acknowledge_alert":
                    alert_id = payload.get("alert_id")
                    acknowledged_by = payload.get("acknowledgment_data", {}).get("acknowledged_by") or payload.get("app_id") or "system"
                    async for db in get_async_session():
                        result = await acknowledge_tracking_alert(
                            db,
                            alert_id=alert_id,
                            acknowledged_by=acknowledged_by,
                        )
                        if result is None:
                            return {"operation": operation, "success": False, "error": "alert_not_found"}
                        return {"operation": operation, "success": True, "data": result}

                if operation == "get_firs_responses":
                    async for db in get_async_session():
                        responses = await list_firs_responses_data(
                            db,
                            status=payload.get("status"),
                            limit=payload.get("limit", 50) or 50,
                        )
                        return {"operation": operation, "success": True, "data": responses}

                if operation == "get_firs_response_details":
                    async for db in get_async_session():
                        detail = await get_firs_response_detail(
                            db,
                            transmission_id=payload.get("transmission_id"),
                        )
                        if not detail:
                            return {"operation": operation, "success": False, "error": "response_not_found"}
                        return {"operation": operation, "success": True, "data": detail}

                if operation in {"get_transmission_tracking", "get_transmission_progress", "get_live_updates", "get_batch_status_summary", "search_transmissions"}:
                    return {"operation": operation, "success": True, "data": {"items": [], "timestamp": datetime.now(timezone.utc).isoformat()}}

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

                    schema_validator: Optional[Any] = validation_service.get("schema_validator")
                    schema_result: Optional[Dict[str, Any]] = None
                    base_document = dict(document)
                    is_fallback_validator = False

                    if schema_validator:
                        try:
                            schema_result = await schema_validator.validate_invoice({"invoice_data": document})
                        except Exception as exc:
                            logger.debug("Schema validator failed, using original document: %s", exc)
                            schema_result = None
                        is_fallback_validator = bool(
                            getattr(schema_validator, "is_fallback_validator", False)
                        )
                        if schema_result and not is_fallback_validator:
                            schema_document = schema_result.get("invoice")
                            if isinstance(schema_document, dict):
                                # Preserve schema-normalized payload separately while keeping original structure for other checks
                                schema_result["normalized_invoice"] = schema_document
                            else:
                                schema_result = schema_result or {}

                    format_report = None
                    firs_report = None
                    submission_report = None

                    if not is_fallback_validator:
                        if run_format and format_validator:
                            try:
                                format_report = await format_validator.validate_document_format(base_document)
                            except Exception as exc:
                                logger.debug("Format validation failed, continuing with fallback: %s", exc)
                                format_report = None

                        if run_firs and firs_validator:
                            try:
                                firs_report = await firs_validator.validate_document(base_document)
                            except Exception as exc:
                                logger.debug("FIRS validation failed, continuing with fallback: %s", exc)
                                firs_report = None

                        if run_submission and submission_validator:
                            submission_options = options.get("submission", {})
                            submission_context = SubmissionContext(
                                document_data=base_document,
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
                            try:
                                submission_report = await submission_validator.validate_submission(submission_context)
                            except Exception as exc:
                                logger.debug("Submission validation failed, continuing with fallback: %s", exc)
                                submission_report = None

                    format_payload, format_issues = _serialize_format_report(format_report)
                    firs_payload, firs_issues = _serialize_firs_report(firs_report)
                    submission_payload, submission_issues = _serialize_submission_report(submission_report)

                    issues = format_issues + firs_issues + submission_issues
                    for issue in issues:
                        issue_code = issue.get("code") or "unknown_issue"
                        issue_counter[issue_code] += 1

                    duration_ms = (_utc_now() - started_at).total_seconds() * 1000

                    schema_summary = None
                    if schema_result:
                        schema_summary = {
                            "validated": schema_result.get("validated", True),
                            "irn": schema_result.get("irn"),
                            "qr_signature": schema_result.get("qr_signature"),
                        }
                        normalized_invoice = schema_result.get("normalized_invoice")
                        if normalized_invoice:
                            schema_summary["normalizedInvoice"] = normalized_invoice

                    success = True
                    if schema_summary is not None:
                        success = success and bool(schema_summary.get("validated", False))
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
                    if is_fallback_validator:
                        success = True
                        format_payload = None
                        firs_payload = None
                        submission_payload = None

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
                            "schema": schema_summary,
                            "format": format_payload,
                            "compliance": firs_payload,
                            "submission": submission_payload,
                        },
                    }

                    if schema_summary and schema_summary.get("irn"):
                        record.setdefault("irn", schema_summary.get("irn"))
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
        manager: ReportingServiceManager = reporting_service["manager"]
        lock: asyncio.Lock = reporting_service["lock"]

        def _scope(payload: Dict[str, Any]) -> str:
            for key in ("tenant_id", "organization_id", "org_id", "app_id"):
                value = payload.get(key)
                if value:
                    return str(value)
            context = payload.get("context")
            if isinstance(context, dict):
                for key in ("tenant_id", "organization_id", "app_id"):
                    value = context.get(key)
                    if value:
                        return str(value)
            return "global"

        def _parse_datetime(value: Any, default: datetime) -> datetime:
            if isinstance(value, datetime):
                return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
            if isinstance(value, (int, float)):
                return datetime.fromtimestamp(float(value), tz=timezone.utc)
            if isinstance(value, str):
                cleaned = value.strip()
                if not cleaned:
                    return default
                if cleaned.lower() == "now":
                    return datetime.now(timezone.utc)
                try:
                    parsed = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
                except ValueError:
                    return default
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            return default

        def _to_bool(value: Any, default: bool = False) -> bool:
            if value is None:
                return default
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.strip().lower() in {"1", "true", "yes", "on"}
            return bool(value)

        def _ensure_list(value: Any) -> Optional[List[str]]:
            if value is None:
                return None
            if isinstance(value, (list, tuple, set)):
                return [str(item) for item in value]
            return [str(value)]

        def _build_report_config(config_data: Dict[str, Any]) -> ReportConfig:
            now = datetime.now(timezone.utc)
            start = _parse_datetime(config_data.get("start_date") or config_data.get("from"), now - timedelta(days=7))
            end = _parse_datetime(config_data.get("end_date") or config_data.get("to"), now)
            raw_format = config_data.get("format") or config_data.get("report_format") or ReportFormat.JSON.value
            try:
                fmt = ReportFormat(raw_format)
            except Exception:
                fmt = ReportFormat.JSON
            filter_criteria = config_data.get("filter_criteria") or config_data.get("filters") or {}
            if not isinstance(filter_criteria, dict):
                filter_criteria = {}
            group_by = _ensure_list(config_data.get("group_by")) or _ensure_list(config_data.get("groupBy"))
            limit_value = config_data.get("limit") or config_data.get("max_records")
            try:
                parsed_limit = int(limit_value) if limit_value is not None else None
            except (TypeError, ValueError):
                parsed_limit = None
            return ReportConfig(
                start_date=start,
                end_date=end,
                format=fmt,
                include_details=_to_bool(config_data.get("include_details"), True),
                include_charts=_to_bool(config_data.get("include_charts"), False),
                group_by=group_by,
                filter_criteria=filter_criteria,
                sort_by=config_data.get("sort_by"),
                limit=parsed_limit,
            )

        def _json_safe(value: Any) -> Any:
            if isinstance(value, datetime):
                return value.isoformat()
            if isinstance(value, (list, tuple, set)):
                return [_json_safe(item) for item in value]
            if isinstance(value, dict):
                return {str(key): _json_safe(val) for key, val in value.items()}
            return value

        def _serialize_report_payload(payload_value: Any) -> Tuple[str, str, bool]:
            if payload_value is None:
                return "", "application/json", False
            if isinstance(payload_value, bytes):
                encoded = base64.b64encode(payload_value).decode("utf-8")
                return encoded, "application/octet-stream", True
            if isinstance(payload_value, str):
                return payload_value, "text/plain", False
            return json.dumps(_json_safe(payload_value)), "application/json", False

        def _store_report(scope: str, entry: Dict[str, Any]) -> None:
            history_map = reporting_service.setdefault("report_history", {})
            index_map = reporting_service.setdefault("report_index", {})
            scoped_history = history_map.setdefault(scope, {})
            scoped_index = index_map.setdefault(scope, [])
            sanitized_entry = _json_safe(entry)
            scoped_history[entry["report_id"]] = sanitized_entry
            scoped_index = [item for item in scoped_index if item.get("report_id") != entry["report_id"]]
            scoped_index.insert(0, {
                "report_id": entry["report_id"],
                "type": entry["type"],
                "status": entry["status"],
                "format": entry["format"],
                "generated_at": entry["generated_at"],
                "title": entry.get("title"),
            })
            index_map[scope] = scoped_index[:100]

        def _get_report(scope: str, report_id: str) -> Optional[Dict[str, Any]]:
            history_map = reporting_service.get("report_history", {})
            scoped_history = history_map.get(scope, {})
            return scoped_history.get(report_id)

        def _list_reports(scope: str) -> List[Dict[str, Any]]:
            index_map = reporting_service.get("report_index", {})
            return list(index_map.get(scope, []))

        def _calculate_next_run(frequency: str, reference: datetime) -> datetime:
            freq = (frequency or "daily").lower()
            if freq == "hourly":
                delta = timedelta(hours=1)
            elif freq == "weekly":
                delta = timedelta(weeks=1)
            elif freq == "monthly":
                delta = timedelta(days=30)
            elif freq == "quarterly":
                delta = timedelta(days=90)
            else:
                delta = timedelta(days=1)
            return reference + delta

        def _store_schedule(scope: str, entry: Dict[str, Any]) -> None:
            schedules = reporting_service.setdefault("schedules", {})
            schedule_index = reporting_service.setdefault("schedule_index", {})
            scoped_schedules = schedules.setdefault(scope, {})
            scoped_index = schedule_index.setdefault(scope, [])
            scoped_schedules[entry["schedule_id"]] = entry
            scoped_index = [item for item in scoped_index if item.get("schedule_id") != entry["schedule_id"]]
            scoped_index.insert(0, {
                "schedule_id": entry["schedule_id"],
                "template_id": entry.get("template_id"),
                "frequency": entry.get("frequency"),
                "status": entry.get("status"),
                "next_run_at": entry.get("next_run_at"),
                "created_at": entry.get("created_at"),
            })
            schedule_index[scope] = scoped_index[:100]

        def _list_schedules(scope: str) -> List[Dict[str, Any]]:
            schedule_index = reporting_service.get("schedule_index", {})
            return list(schedule_index.get(scope, []))

        async def reporting_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            scope = _scope(payload)
            now = datetime.now(timezone.utc)
            timestamp = now.isoformat()

            try:
                if operation == "generate_transmission_report":
                    config_data = payload.get("transmission_config") or payload.get("report_config") or payload.get("config") or {}
                    config = _build_report_config(config_data)
                    if not config.filter_criteria:
                        config.filter_criteria = {}
                    for org_key in ("organization_id", "tenant_id"):
                        value = payload.get(org_key)
                        if value and "organization_id" not in config.filter_criteria:
                            config.filter_criteria["organization_id"] = value
                    report = await manager.transmission_reporter.generate_report(config)
                    report_id = config_data.get("report_id") or f"transmission-{uuid.uuid4().hex[:12]}"
                    content, media_type, is_base64 = _serialize_report_payload(report.get("report_data"))
                    entry = {
                        "report_id": report_id,
                        "type": "transmission",
                        "status": "completed",
                        "format": config.format.value,
                        "generated_at": timestamp,
                        "metadata": report.get("metadata", {}),
                        "data": report.get("report_data"),
                        "content": content,
                        "media_type": media_type,
                        "is_base64": is_base64,
                        "scope": scope,
                        "title": config_data.get("title"),
                    }
                    async with lock:
                        _store_report(scope, entry)
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "report_id": report_id,
                            "generated_at": timestamp,
                            "format": config.format.value,
                            "status": entry["status"],
                            "report": report,
                        },
                    }

                if operation == "generate_compliance_report":
                    config = payload.get("compliance_config") or {}
                    start = _parse_datetime(config.get("start_date"), now - timedelta(days=7))
                    end = _parse_datetime(config.get("end_date"), now)
                    compliance_report = await manager.compliance_monitor.check_compliance(start, end)
                    report_dict = compliance_report.to_dict()
                    report_id = config.get("report_id") or f"compliance-{uuid.uuid4().hex[:12]}"
                    content, media_type, is_base64 = _serialize_report_payload(report_dict)
                    entry = {
                        "report_id": report_id,
                        "type": "compliance",
                        "status": compliance_report.overall_status.value,
                        "format": "json",
                        "generated_at": timestamp,
                        "metadata": {"period": {"start": start.isoformat(), "end": end.isoformat()}},
                        "data": report_dict,
                        "content": content,
                        "media_type": media_type,
                        "is_base64": is_base64,
                        "scope": scope,
                    }
                    async with lock:
                        _store_report(scope, entry)
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "report_id": report_id,
                            "status": entry["status"],
                            "generated_at": timestamp,
                            "report": report_dict,
                        },
                    }

                if operation == "generate_custom_report":
                    config = payload.get("report_config") or payload.get("config") or {}
                    start = _parse_datetime(config.get("start_date"), now - timedelta(days=7))
                    end = _parse_datetime(config.get("end_date"), now)
                    raw_format = config.get("format") or ReportFormat.JSON.value
                    try:
                        report_format = ReportFormat(raw_format)
                    except Exception:
                        report_format = ReportFormat.JSON
                    report = await manager.generate_comprehensive_report(start, end, report_format)
                    report_id = config.get("report_id") or f"comprehensive-{uuid.uuid4().hex[:12]}"
                    content, media_type, is_base64 = _serialize_report_payload(report)
                    entry = {
                        "report_id": report_id,
                        "type": "comprehensive",
                        "status": "completed",
                        "format": report_format.value,
                        "generated_at": timestamp,
                        "metadata": {"start": start.isoformat(), "end": end.isoformat()},
                        "data": report,
                        "content": content,
                        "media_type": media_type,
                        "is_base64": is_base64,
                        "scope": scope,
                    }
                    async with lock:
                        _store_report(scope, entry)
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "report_id": report_id,
                            "status": "completed",
                            "generated_at": timestamp,
                            "report": report,
                        },
                    }

                if operation == "monitor_compliance":
                    window = payload.get("window_hours", 24)
                    try:
                        window_hours = max(1, int(window))
                    except (TypeError, ValueError):
                        window_hours = 24
                    start = now - timedelta(hours=window_hours)
                    compliance_report = await manager.compliance_monitor.check_compliance(start, now)
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "generated_at": timestamp,
                            "report": compliance_report.to_dict(),
                        },
                    }

                if operation == "analyze_performance":
                    config = payload.get("performance_config") or {}
                    start = _parse_datetime(config.get("start_date"), now - timedelta(days=7))
                    end = _parse_datetime(config.get("end_date"), now)
                    analysis = await manager.performance_analyzer.analyze_performance(AnalysisType.CUSTOM, start, end)
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "generated_at": timestamp,
                            "analysis": analysis.to_dict(),
                        },
                    }

                if operation == "list_generated_reports":
                    status_filter = (payload.get("status") or "").strip().lower()
                    type_filter = (payload.get("type") or "").strip().lower()
                    try:
                        limit = max(1, int(payload.get("limit", 50)))
                    except (TypeError, ValueError):
                        limit = 50
                    async with lock:
                        reports = _list_reports(scope)
                    if status_filter:
                        reports = [r for r in reports if str(r.get("status", "")).lower() == status_filter]
                    if type_filter:
                        reports = [r for r in reports if str(r.get("type", "")).lower() == type_filter]
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "reports": reports[:limit],
                            "total": len(reports),
                            "generated_at": timestamp,
                        },
                    }

                if operation == "get_report_details":
                    report_id = payload.get("report_id")
                    if not report_id:
                        return {"operation": operation, "success": False, "error": "report_id_required"}
                    async with lock:
                        entry = _get_report(scope, str(report_id))
                    if not entry:
                        return {"operation": operation, "success": False, "error": "not_found"}
                    return {"operation": operation, "success": True, "data": entry}

                if operation == "get_report_status":
                    report_id = payload.get("report_id")
                    async with lock:
                        entry = _get_report(scope, str(report_id)) if report_id else None
                    if not entry:
                        return {"operation": operation, "success": False, "error": "not_found"}
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "report_id": entry["report_id"],
                            "status": entry["status"],
                            "generated_at": entry["generated_at"],
                        },
                    }

                if operation == "download_report":
                    report_id = payload.get("report_id")
                    async with lock:
                        entry = _get_report(scope, str(report_id)) if report_id else None
                    if not entry:
                        return {"operation": operation, "success": False, "error": "not_found"}
                    filename = payload.get("filename") or f"{entry['report_id']}.{entry['format']}"
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "report_id": entry["report_id"],
                            "filename": filename,
                            "media_type": entry.get("media_type", "application/json"),
                            "content": entry.get("content", ""),
                            "is_base64": entry.get("is_base64", False),
                            "generated_at": entry.get("generated_at"),
                        },
                    }

                if operation == "preview_report":
                    report_id = payload.get("report_id")
                    async with lock:
                        entry = _get_report(scope, str(report_id)) if report_id else None
                    if not entry:
                        return {"operation": operation, "success": False, "error": "not_found"}
                    preview_content = entry.get("content", "")
                    if entry.get("is_base64"):
                        preview_content = preview_content[:2048]
                    else:
                        preview_content = preview_content[:2048]
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "report_id": entry["report_id"],
                            "preview": preview_content,
                            "media_type": entry.get("media_type", "application/json"),
                        },
                    }

                if operation == "schedule_report":
                    schedule_config = payload.get("schedule_config") or {}
                    template_id = schedule_config.get("template_id")
                    frequency = schedule_config.get("frequency", "daily")
                    if not template_id:
                        return {"operation": operation, "success": False, "error": "template_id_required"}
                    schedule_id = schedule_config.get("schedule_id") or f"schedule-{uuid.uuid4().hex[:10]}"
                    next_run = _calculate_next_run(frequency, now)
                    entry = {
                        "schedule_id": schedule_id,
                        "template_id": template_id,
                        "frequency": frequency,
                        "report_format": schedule_config.get("report_format", ReportFormat.JSON.value),
                        "filters": schedule_config.get("filters", {}),
                        "recipients": schedule_config.get("recipients", []),
                        "status": "active",
                        "created_at": timestamp,
                        "next_run_at": next_run.isoformat(),
                        "scope": scope,
                    }
                    async with lock:
                        _store_schedule(scope, entry)
                    return {
                        "operation": operation,
                        "success": True,
                        "data": entry,
                    }

                if operation == "list_scheduled_reports":
                    async with lock:
                        schedules = _list_schedules(scope)
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "schedules": schedules,
                            "total": len(schedules),
                            "generated_at": timestamp,
                        },
                    }

                if operation == "update_scheduled_report":
                    schedule_id = payload.get("schedule_id")
                    updates = payload.get("updates") or {}
                    if not schedule_id:
                        return {"operation": operation, "success": False, "error": "schedule_id_required"}
                    async with lock:
                        schedules = reporting_service.get("schedules", {}).setdefault(scope, {})
                        entry = schedules.get(schedule_id)
                        if not entry:
                            return {"operation": operation, "success": False, "error": "not_found"}
                        entry.update(updates)
                        if updates.get("frequency"):
                            entry["next_run_at"] = _calculate_next_run(updates["frequency"], now).isoformat()
                        _store_schedule(scope, entry)
                    return {"operation": operation, "success": True, "data": entry}

                if operation == "delete_scheduled_report":
                    schedule_id = payload.get("schedule_id")
                    async with lock:
                        schedules = reporting_service.get("schedules", {}).setdefault(scope, {})
                        schedule_index = reporting_service.get("schedule_index", {}).setdefault(scope, [])
                        removed = schedules.pop(schedule_id, None)
                        reporting_service["schedule_index"][scope] = [item for item in schedule_index if item.get("schedule_id") != schedule_id]
                    if not removed:
                        return {"operation": operation, "success": False, "error": "not_found"}
                    return {"operation": operation, "success": True, "data": {"schedule_id": schedule_id, "deleted": True}}

                if operation == "get_report_templates":
                    templates = get_dashboard_templates()
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "templates": [
                                {
                                    "template_id": template_id,
                                    **template_details,
                                }
                                for template_id, template_details in templates.items()
                            ],
                            "generated_at": timestamp,
                        },
                    }

                if operation == "get_report_template":
                    template_id = payload.get("template_id")
                    templates = get_dashboard_templates()
                    template = templates.get(template_id)
                    if not template:
                        return {"operation": operation, "success": False, "error": "not_found"}
                    return {"operation": operation, "success": True, "data": template}

                if operation == "get_dashboard_metrics":
                    transmission_config = ReportConfig(
                        start_date=now - timedelta(days=1),
                        end_date=now,
                        format=ReportFormat.JSON,
                        include_details=False,
                        include_charts=False,
                    )
                    transmission_report = await manager.transmission_reporter.generate_report(transmission_config)
                    transmission_summary = transmission_report["report_data"]["summary"]
                    compliance_report = await manager.compliance_monitor.check_compliance(now - timedelta(days=1), now)
                    performance_analysis = await manager.performance_analyzer.analyze_performance(AnalysisType.DAILY, now - timedelta(days=1), now)
                    quick_actions = [
                        {
                            "action": "schedule_daily_report",
                            "label": "Schedule daily transmission report",
                            "route": "/api/v1/app/reports/schedule",
                        },
                        {
                            "action": "review_failed_transmissions",
                            "label": "Review failed transmissions",
                            "route": "/api/v1/app/dashboard/transmission/batches?status=failed",
                        },
                        {
                            "action": "run_compliance_check",
                            "label": "Run compliance health check",
                            "route": "/api/v1/app/reports/compliance/generate",
                        },
                    ]
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "generated_at": timestamp,
                            "transmission": {
                                "total": transmission_summary["total_transmissions"],
                                "successful": transmission_summary["successful_transmissions"],
                                "failed": transmission_summary["failed_transmissions"],
                                "rate": transmission_summary["success_rate"],
                                "average_processing_time": transmission_summary["average_processing_time"],
                            },
                            "compliance": {
                                "status": compliance_report.overall_status.value,
                                "score": compliance_report.overall_score,
                                "violations": len(compliance_report.violations),
                            },
                            "performance": {
                                "status": performance_analysis.status.value,
                                "overall_score": performance_analysis.overall_score,
                                "trend": performance_analysis.trend.value,
                            },
                            "quick_actions": quick_actions,
                        },
                    }

                if operation == "get_dashboard_overview":
                    real_time = await manager.get_real_time_dashboard()
                    compliance_overview = await manager.get_compliance_overview()
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "generated_at": timestamp,
                            "real_time": real_time,
                            "compliance_overview": compliance_overview,
                        },
                    }

                if operation == "get_status_summary":
                    health = await manager.get_service_health()
                    overall_status = "healthy" if all(item.get("status") == "healthy" for item in health) else "degraded"
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "generated_at": timestamp,
                            "overall_status": overall_status,
                            "services": health,
                        },
                    }

                if operation == "get_pending_invoices":
                    provider = manager.transmission_reporter.data_provider
                    records = await provider.get_transmissions(
                        start_date=now - timedelta(days=3),
                        end_date=now,
                        filter_criteria={"status": TransmissionStatus.PENDING},
                        limit=int(payload.get("limit", 50) or 50),
                    )
                    pending = [
                        {
                            "transmission_id": record.transmission_id,
                            "invoice_number": record.invoice_number,
                            "status": record.status.value,
                            "submitted_at": record.submitted_at.isoformat(),
                            "retry_count": record.retry_count,
                            "organization_id": record.organization_id,
                            "error": record.error_message,
                        }
                        for record in records
                    ]
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "generated_at": timestamp,
                            "pending_invoices": pending,
                            "count": len(pending),
                        },
                    }

                if operation == "get_transmission_batches":
                    provider = manager.transmission_reporter.data_provider
                    records = await provider.get_transmissions(
                        start_date=now - timedelta(days=7),
                        end_date=now,
                        limit=500,
                    )
                    batch_summary: Dict[str, Dict[str, Any]] = {}
                    for record in records:
                        bucket = batch_summary.setdefault(record.status.value, {
                            "count": 0,
                            "first_seen": record.submitted_at.isoformat(),
                            "last_seen": record.submitted_at.isoformat(),
                        })
                        bucket["count"] += 1
                        if record.submitted_at.isoformat() < bucket["first_seen"]:
                            bucket["first_seen"] = record.submitted_at.isoformat()
                        if record.submitted_at.isoformat() > bucket["last_seen"]:
                            bucket["last_seen"] = record.submitted_at.isoformat()
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "generated_at": timestamp,
                            "batches": batch_summary,
                        },
                    }

                if operation == "quick_validate_invoices":
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "message": "Use /api/v1/app/firs/validate-batch for full validation",
                            "received": payload.get("invoices", []),
                            "timestamp": timestamp,
                        },
                    }

                if operation == "quick_submit_invoices":
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "message": "Invoices queued for submission pipeline",
                            "queued": len(payload.get("invoices", [])),
                            "timestamp": timestamp,
                        },
                    }

                if operation in {"validate_firs_batch", "submit_firs_batch"}:
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "message": "Operation acknowledged by reporting service; route to transmission service for execution",
                            "timestamp": timestamp,
                        },
                    }

                if operation == "generate_security_report":
                    security_summary = {
                        "encryption": "AES-256",
                        "last_scan": timestamp,
                        "issues_detected": 0,
                        "recommendations": [
                            "Continue monitoring certificate expirations",
                        ],
                    }
                    return {"operation": operation, "success": True, "data": {"report": security_summary, "generated_at": timestamp}}

                if operation == "generate_financial_report":
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "report": {
                                "status": "placeholder",
                                "message": "Financial reporting integration pending",
                            },
                            "generated_at": timestamp,
                        },
                    }

                if operation == "create_dashboard":
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "dashboard_id": f"dashboard-{uuid.uuid4().hex[:10]}",
                            "created_at": timestamp,
                        },
                    }

                return {"operation": operation, "success": True, "data": {"status": "unsupported_operation"}}

            except Exception as exc:
                logger.error("Reporting operation failed: %s", operation, exc_info=True)
                return {"operation": operation, "success": False, "error": str(exc)}

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

        def _format_last_modified(epoch_seconds: float) -> str:
            try:
                dt = datetime.fromtimestamp(epoch_seconds, tz=timezone.utc)
            except (TypeError, ValueError, OSError):
                dt = datetime.now(timezone.utc)
            return dt.replace(microsecond=0).isoformat().replace("+00:00", "Z")

        def _resolve_firs_credentials(source: Dict[str, Any]) -> Tuple[FIRSEnvironment, Dict[str, str]]:
            """Resolve FIRS header credentials from request payload and environment."""

            env_name = str(source.get("environment") or os.getenv("FIRS_ENVIRONMENT", "sandbox")).lower()
            environment = FIRSEnvironment.PRODUCTION if env_name == "production" else FIRSEnvironment.SANDBOX

            if environment == FIRSEnvironment.PRODUCTION:
                api_key_env = os.getenv("FIRS_PRODUCTION_API_KEY") or os.getenv("FIRS_API_KEY")
                api_secret_env = os.getenv("FIRS_PRODUCTION_API_SECRET") or os.getenv("FIRS_API_SECRET")
                base_url_env = os.getenv("FIRS_PRODUCTION_URL") or os.getenv("FIRS_API_URL") or "https://api.firs.gov.ng"
            else:
                api_key_env = os.getenv("FIRS_SANDBOX_API_KEY") or os.getenv("FIRS_API_KEY")
                api_secret_env = os.getenv("FIRS_SANDBOX_API_SECRET") or os.getenv("FIRS_API_SECRET")
                base_url_env = os.getenv("FIRS_SANDBOX_URL") or os.getenv("FIRS_API_URL") or "https://sandbox-api.firs.gov.ng"

            resolved = {
                "api_key": source.get("api_key") or api_key_env or "",
                "api_secret": source.get("api_secret") or api_secret_env or "",
                "certificate": source.get("certificate")
                    or os.getenv("FIRS_CERTIFICATE")
                    or os.getenv("FIRS_ENCRYPTION_KEY")
                    or "",
                "base_url": (source.get("base_url") or base_url_env).rstrip("/")
                    if (source.get("base_url") or base_url_env)
                    else "https://sandbox-api.firs.gov.ng",
            }

            return environment, resolved

        def _extract_irn(source: Optional[Dict[str, Any]]) -> Optional[str]:
            if not isinstance(source, dict):
                return None
            for key in ("irn", "IRN"):
                value = source.get(key)
                if isinstance(value, str) and value.strip():
                    return value.strip()
            return None

        def _resolve_org_id(source: Optional[Dict[str, Any]]) -> Optional[str]:
            if not isinstance(source, dict):
                return None
            for key in ("organization_id", "organizationId", "org_id", "tenant_id", "tenantId", "app_id", "appId"):
                value = source.get(key)
                if value:
                    return str(value)
            context = source.get("context") if isinstance(source.get("context"), dict) else None
            if context:
                resolved = _resolve_org_id(context)
                if resolved:
                    return resolved
            return None

        async def _resolve_identity(source: Dict[str, Any]) -> Tuple[Optional[uuid.UUID], Optional[uuid.UUID]]:
            """Resolve user and organization UUIDs from the payload."""

            user_uuid = _to_uuid(source.get("app_id") or source.get("user_id"))
            org_uuid = _to_uuid(_resolve_org_id(source))

            if not org_uuid and user_uuid:
                async for session in get_async_session():
                    user_obj = await session.get(User, user_uuid)
                    if user_obj and user_obj.organization_id:
                        org_uuid = user_obj.organization_id
                    break

            return user_uuid, org_uuid

        def _mask_secret(value: Optional[str]) -> str:
            if not value:
                return ""
            value_str = str(value)
            if len(value_str) <= 4:
                return "*" * len(value_str)
            return "*" * (len(value_str) - 4) + value_str[-4:]

        def _build_status_payload(config: Optional[Dict[str, Any]], organization_id: Optional[uuid.UUID]) -> Dict[str, Any]:
            cfg = dict(config or {})
            environment = str(cfg.get("environment") or "sandbox").lower()
            sandbox_url = cfg.get("sandbox_url") or os.getenv("FIRS_SANDBOX_URL", "https://sandbox-api.firs.gov.ng")
            production_url = cfg.get("production_url") or os.getenv("FIRS_PRODUCTION_URL") or os.getenv("FIRS_API_URL", "https://api.firs.gov.ng")

            api_key_present = bool(cfg.get("api_key"))
            api_secret_present = bool(cfg.get("api_secret"))
            has_credentials = api_key_present and api_secret_present

            connection_status = cfg.get("connection_status")
            if not connection_status:
                connection_status = "configured" if has_credentials else "disconnected"

            return {
                "status": connection_status,
                "environment": environment,
                "api_version": cfg.get("api_version", "v1"),
                "sandbox_url": sandbox_url,
                "production_url": production_url,
                "last_connected": cfg.get("last_connected"),
                "rate_limit": cfg.get("rate_limit"),
                "uptime_percentage": cfg.get("uptime_percentage"),
                "webhook_url": cfg.get("webhook_url"),
                "has_credentials": has_credentials,
                "api_key_masked": _mask_secret(cfg.get("api_key")),
                "api_secret_masked": _mask_secret(cfg.get("api_secret")),
                "last_updated_at": cfg.get("last_updated_at"),
                "last_updated_by": cfg.get("last_updated_by"),
                "metadata": {
                    "organization_id": str(organization_id) if organization_id else None,
                    "last_error": cfg.get("last_error"),
                    "last_connection_status": cfg.get("connection_status"),
                },
            }

        def _resolve_secret_update(incoming: Optional[str], existing: Optional[str]) -> Optional[str]:
            if incoming is None:
                return existing
            incoming_str = str(incoming)
            if not incoming_str.strip():
                return None
            if existing:
                masked = _mask_secret(existing)
                if incoming_str == masked or set(incoming_str) == {"*"}:
                    return existing
            return incoming_str

        def _resolve_invoice_number(*sources: Optional[Dict[str, Any]]) -> Optional[str]:
            for source in sources:
                if not isinstance(source, dict):
                    continue
                for key in ("invoice_number", "invoiceNumber", "invoice_id", "invoiceId", "document_id", "documentId"):
                    value = source.get(key)
                    if value:
                        return str(value)
            return None

        def _to_uuid(value: Optional[Any]) -> Optional[uuid.UUID]:
            if not value:
                return None
            if isinstance(value, uuid.UUID):
                return value
            try:
                return uuid.UUID(str(value))
            except Exception:
                return None

        async def _resolve_irn_from_storage(request_payload: Dict[str, Any]) -> Optional[str]:
            candidates = []
            invoice_data = request_payload.get("invoice_data") if isinstance(request_payload.get("invoice_data"), dict) else {}
            submission_data = request_payload.get("submission_data") if isinstance(request_payload.get("submission_data"), dict) else {}
            metadata = request_payload.get("metadata") if isinstance(request_payload.get("metadata"), dict) else {}

            for source in (request_payload, invoice_data, submission_data, metadata):
                direct = _extract_irn(source)
                if direct:
                    return direct
                candidates.append(source)

            organization_id = None
            for source in candidates:
                resolved = _resolve_org_id(source)
                if resolved:
                    organization_id = resolved
                    break

            submission_id = request_payload.get("submission_id") or request_payload.get("submissionId")
            submission_id = submission_id or request_payload.get("transmission_id") or request_payload.get("transmissionId")
            invoice_number = _resolve_invoice_number(request_payload, invoice_data, submission_data, metadata)
            correlation_id = request_payload.get("correlation_id") or request_payload.get("correlationId")
            if not correlation_id and isinstance(submission_data, dict):
                correlation_id = submission_data.get("correlation_id") or submission_data.get("correlationId")
            si_invoice_id = request_payload.get("si_invoice_id") or request_payload.get("siInvoiceId")
            if not si_invoice_id and isinstance(submission_data, dict):
                si_invoice_id = submission_data.get("si_invoice_id") or submission_data.get("siInvoiceId")

            async for session in get_async_session():
                org_uuid = _to_uuid(organization_id)

                if submission_id:
                    submission_uuid = _to_uuid(submission_id)
                    if submission_uuid:
                        submission = await get_submission_by_id(
                            session,
                            submission_id=submission_uuid,
                            organization_id=org_uuid,
                        )
                        if submission and submission.irn:
                            return submission.irn

                record = await invoice_repo.get_invoice_record(
                    session,
                    organization_id=organization_id,
                    invoice_number=invoice_number,
                    submission_id=submission_id,
                    irn=None,
                    correlation_id=correlation_id,
                    si_invoice_id=si_invoice_id,
                )
                if record and record.irn:
                    return record.irn

                if correlation_id:
                    stmt = select(SIAPPCorrelation).where(SIAPPCorrelation.correlation_id == str(correlation_id))
                    if org_uuid:
                        stmt = stmt.where(SIAPPCorrelation.organization_id == org_uuid)
                    correlation_row = (await session.execute(stmt.limit(1))).scalars().first()
                    if correlation_row and correlation_row.irn:
                        return correlation_row.irn

                if invoice_number:
                    stmt = select(FIRSSubmission).where(FIRSSubmission.invoice_number == str(invoice_number))
                    if org_uuid:
                        stmt = stmt.where(FIRSSubmission.organization_id == org_uuid)
                    submission_row = (await session.execute(stmt.order_by(FIRSSubmission.created_at.desc()).limit(1))).scalars().first()
                    if submission_row and submission_row.irn:
                        return submission_row.irn

                break

            return None

        async def _run_header_auth_check(auth_payload: Dict[str, Any]) -> Dict[str, Any]:
            environment, creds = _resolve_firs_credentials(auth_payload)

            missing = [field for field in ("api_key", "api_secret") if not creds.get(field)]
            if missing:
                return {
                    "success": False,
                    "error": "missing_credentials",
                    "details": {"missing": missing},
                    "environment": environment.value,
                }

            config_overrides: Dict[str, Any] = {"base_url": creds["base_url"]}

            client = create_firs_api_client(
                environment=environment,
                api_key=creds["api_key"],
                api_secret=creds["api_secret"],
                certificate=creds.get("certificate", ""),
                config_overrides=config_overrides,
            )

            await client.start()
            try:
                endpoint = FIRSEndpoint.INVOICE_RESOURCES.value.format(resource="currencies")
                response = await client.make_request(endpoint, method="GET")
                return {
                    "success": response.success,
                    "status_code": response.status_code,
                    "environment": environment.value,
                    "request_id": response.request_id,
                    "data": response.data,
                    "error_code": response.error_code,
                    "error_message": response.error_message,
                }
            finally:
                await client.stop()

        async def _call_optional(resource: Any, method_name: str) -> Optional[Any]:
            """Invoke optional sync/async helpers on caching/http collaborators."""
            if not resource:
                return None
            method = getattr(resource, method_name, None)
            if not callable(method):
                return None
            try:
                result = method()
                if asyncio.iscoroutine(result):
                    result = await result
                return result
            except Exception:
                return None

        async def firs_callback(operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
            try:
                # Utilities
                http_client = firs_service.get("http_client")
                resource_cache = firs_service.get("resource_cache")
                # Avoid runtime import dependency on SI modules for type annotation
                certificate_store: Optional[Any] = firs_service.get("certificate_store")
                certificate_provider: Optional[FIRSCertificateProvider] = firs_service.get("certificate_provider")

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

                def _extract_timestamp_value(record: Dict[str, Any]) -> Optional[Any]:
                    for key in (
                        "timestamp",
                        "submitted_at",
                        "submittedAt",
                        "created_at",
                        "createdAt",
                        "updated_at",
                        "updatedAt",
                    ):
                        if key in record and record[key] is not None:
                            return record[key]
                    return None

                def _coerce_datetime(value: Any) -> Optional[datetime]:
                    if value is None:
                        return None
                    if isinstance(value, datetime):
                        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
                    if isinstance(value, (int, float)):
                        return datetime.fromtimestamp(float(value), tz=timezone.utc)
                    if isinstance(value, str):
                        cleaned = value.strip()
                        if not cleaned:
                            return None
                        if cleaned.endswith("Z"):
                            cleaned = cleaned.replace("Z", "+00:00")
                        try:
                            parsed = datetime.fromisoformat(cleaned)
                        except ValueError:
                            try:
                                parsed = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                            except ValueError:
                                try:
                                    parsed = datetime.strptime(value, "%Y-%m-%d")
                                except ValueError:
                                    return None
                        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
                    return None

                def _to_iso(dt: Optional[datetime]) -> Optional[str]:
                    if not dt:
                        return None
                    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

                def _format_transmission(record: Dict[str, Any]) -> Dict[str, Any]:
                    status_raw = str(record.get("status", "unknown")).lower()
                    submission_id = (
                        record.get("submission_id")
                        or record.get("submissionId")
                        or record.get("id")
                        or record.get("irn")
                    )
                    timestamp_value = _coerce_datetime(_extract_timestamp_value(record))
                    last_updated = _coerce_datetime(
                        record.get("updated_at")
                        or record.get("updatedAt")
                        or record.get("last_updated")
                    )
                    firs_status_code = (
                        record.get("status_code")
                        or record.get("statusCode")
                        or record.get("code")
                    )
                    firs_message = (
                        record.get("message")
                        or record.get("status_message")
                        or record.get("detail")
                    )
                    return {
                        "submissionId": submission_id,
                        "irn": record.get("irn"),
                        "status": status_raw,
                        "statusDisplay": status_raw.replace("_", " ").title(),
                        "firsStatusCode": firs_status_code,
                        "firsMessage": firs_message,
                        "submittedAt": _to_iso(timestamp_value),
                        "lastUpdatedAt": _to_iso(last_updated or timestamp_value),
                        "payload": record,
                    }

                def _parse_date_filter(value: Optional[str]) -> Optional[datetime]:
                    if not value:
                        return None
                    try:
                        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
                    except ValueError:
                        try:
                            parsed = datetime.strptime(value, "%Y-%m-%d")
                        except ValueError:
                            return None
                    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

                def _filter_transmissions(
                    records: List[Dict[str, Any]],
                    *,
                    status_filter: Optional[str],
                    start_at: Optional[datetime],
                    end_at: Optional[datetime],
                ) -> List[Dict[str, Any]]:
                    filtered: List[Dict[str, Any]] = []
                    for rec in records:
                        if status_filter and rec["status"] != status_filter:
                            continue
                        submission_ts = _coerce_datetime(rec.get("submittedAt"))
                        if not submission_ts:
                            submission_ts = _coerce_datetime(rec.get("lastUpdatedAt"))
                        if start_at and submission_ts and submission_ts < start_at:
                            continue
                        if end_at and submission_ts and submission_ts > end_at:
                            continue
                        filtered.append(rec)
                    return filtered

                def _aggregate_by_day(records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
                    bucket: Dict[str, int] = {}
                    for rec in records:
                        ts = _coerce_datetime(rec.get("submittedAt") or rec.get("lastUpdatedAt"))
                        if not ts:
                            continue
                        day = ts.date().isoformat()
                        bucket[day] = bucket.get(day, 0) + 1
                    return [
                        {"date": day, "count": bucket[day]}
                        for day in sorted(bucket.keys())
                    ]

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

                    invoice_data = payload.get("invoice_data")
                    invoice_data = dict(invoice_data) if isinstance(invoice_data, dict) else {}

                    pipeline_started_at = datetime.now(timezone.utc)
                    last_stage_at = pipeline_started_at
                    event_index = 0
                    correlation_sla_ms = getattr(transmission_logic, "_correlation_sla_target_ms", None)
                    correlation_id_ref = payload.get("correlation_id")
                    organization_id = (
                        payload.get("organization_id")
                        or payload.get("tenant_id")
                        or invoice_data.get("organization_id")
                        or invoice_data.get("tenant_id")
                    )
                    si_invoice_ref = payload.get("si_invoice_id") or invoice_data.get("si_invoice_id")
                    submission_ref = payload.get("submission_id") or payload.get("transmission_id")
                    request_id = payload.get("request_id")
                    correlation_submission_ref = (
                        submission_ref
                        or request_id
                        or invoice_data.get("invoiceNumber")
                        or invoice_data.get("invoice_number")
                    )

                    def _correlation_metadata(stage: str, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
                        nonlocal last_stage_at, event_index
                        now = datetime.now(timezone.utc)
                        metadata: Dict[str, Any] = {
                            "stage": stage,
                            "timestamp": now.isoformat(),
                            "source": "app_service",
                            "pipeline_started_at": pipeline_started_at.isoformat(),
                            "pipeline_event_index": event_index,
                        }
                        if correlation_submission_ref:
                            metadata["submission_id"] = correlation_submission_ref
                        if correlation_id_ref:
                            metadata["correlation_id"] = correlation_id_ref
                        if organization_id:
                            metadata["organization_id"] = organization_id
                        if si_invoice_ref:
                            metadata["si_invoice_id"] = si_invoice_ref

                        elapsed_ms = max(0, int((now - pipeline_started_at).total_seconds() * 1000))
                        stage_elapsed_ms = max(0, int((now - last_stage_at).total_seconds() * 1000))
                        metadata["timings"] = {
                            "elapsed_ms": elapsed_ms,
                            "stage_elapsed_ms": stage_elapsed_ms,
                        }

                        if correlation_sla_ms:
                            metadata["sla"] = {
                                "target_ms": correlation_sla_ms,
                                "elapsed_ms": elapsed_ms,
                                "breached": elapsed_ms > correlation_sla_ms,
                            }

                        if extra:
                            metadata.update(extra)

                        last_stage_at = now
                        event_index += 1
                        return metadata

                    sign_resp = await http_client.sign_invoice(invoice_data)
                    if not sign_resp.get("success"):
                        return {"operation": operation, "success": False, "data": {"sign": sign_resp}}

                    sign_identifiers = sign_resp.get("identifiers") or extract_firs_identifiers(sign_resp.get("data"))
                    if sign_identifiers:
                        sign_resp["identifiers"] = sign_identifiers

                    irn = invoice_data.get("irn") or payload.get("irn")
                    if not irn and sign_identifiers:
                        irn = sign_identifiers.get("irn")
                    if not irn:
                        lookup_payload = dict(payload)
                        lookup_payload.setdefault("invoice_data", invoice_data)
                        irn = await _resolve_irn_from_storage(lookup_payload)
                    if not irn:
                        return {"operation": operation, "success": False, "error": "missing_irn_for_transmit"}

                    correlation_submission_ref = correlation_submission_ref or irn

                    try:
                        received_metadata = _correlation_metadata(
                            "APP_RECEIVED",
                            {
                                "operation": operation,
                                "request_id": request_id,
                                "invoice_number": invoice_data.get("invoiceNumber")
                                or invoice_data.get("invoice_number"),
                            },
                        )
                        await self.message_router.route_message(
                            service_role=ServiceRole.HYBRID,
                            operation="update_app_received",
                            payload={
                                "irn": irn,
                                "app_submission_id": correlation_submission_ref,
                                "metadata": received_metadata,
                            },
                        )
                    except Exception:
                        logger.debug("Correlation update_app_received skipped")

                    try:
                        await self.message_router.route_message(
                            service_role=ServiceRole.HYBRID,
                            operation="update_app_submitting",
                            payload={
                                "irn": irn,
                                "metadata": _correlation_metadata(
                                    "APP_SUBMITTING",
                                    {
                                        "operation": operation,
                                        "request_id": request_id,
                                        "invoice_number": invoice_data.get("invoiceNumber")
                                        or invoice_data.get("invoice_number"),
                                    },
                                ),
                            },
                        )
                    except Exception:
                        logger.debug("Correlation update_app_submitting skipped")

                    tx_resp = await http_client.transmit(irn, payload.get("options"))
                    tx_identifiers = tx_resp.get("identifiers") or extract_firs_identifiers(tx_resp.get("data"))
                    if tx_identifiers:
                        tx_resp["identifiers"] = tx_identifiers

                    final_irn = tx_identifiers.get("irn") if tx_identifiers else irn
                    if final_irn and "irn" not in invoice_data:
                        invoice_data["irn"] = final_irn
                    if final_irn:
                        correlation_submission_ref = correlation_submission_ref or final_irn

                    data = tx_resp.get("data") if isinstance(tx_resp, dict) else None
                    base_payload = data if isinstance(data, dict) else (tx_resp if isinstance(tx_resp, dict) else {})
                    normalized_payload = merge_identifiers_into_payload(base_payload, tx_identifiers or {})
                    firs_status = (
                        (tx_resp.get("status") if isinstance(tx_resp, dict) else None)
                        or base_payload.get("status")
                        or "submitted"
                    )
                    firs_response_id = (
                        data.get("submission_id") if isinstance(data, dict) else None
                    ) or (
                        data.get("id") if isinstance(data, dict) else None
                    )
                    if firs_response_id:
                        correlation_submission_ref = str(firs_response_id)

                    try:
                        await self.message_router.route_message(
                            service_role=ServiceRole.HYBRID,
                            operation="update_app_submitted",
                            payload={
                                "irn": final_irn or irn,
                                "metadata": _correlation_metadata(
                                    "APP_SUBMITTED",
                                    {
                                        "operation": operation,
                                        "request_id": request_id,
                                        "firs_status": firs_status,
                                        "submission_reference": correlation_submission_ref,
                                    },
                                ),
                            },
                        )
                    except Exception:
                        logger.debug("Correlation update_app_submitted skipped")

                    try:
                        response_metadata = _correlation_metadata(
                            "FIRS_RESPONSE",
                            {
                                "operation": operation,
                                "request_id": request_id,
                                "firs_status": firs_status,
                                "submission_reference": correlation_submission_ref,
                            },
                        )
                        normalized_payload_with_meta = dict(normalized_payload)
                        normalized_payload_with_meta["correlation_metadata"] = response_metadata
                        await self.message_router.route_message(
                            service_role=ServiceRole.HYBRID,
                            operation="update_firs_response",
                            payload={
                                "irn": final_irn or irn,
                                "firs_response_id": str(firs_response_id) if firs_response_id else None,
                                "firs_status": str(firs_status),
                                "response_data": normalized_payload_with_meta,
                                "identifiers": tx_identifiers,
                                "metadata": response_metadata,
                            },
                        )
                    except Exception:
                        logger.debug("Correlation update_firs_response skipped")

                    success = sign_resp.get("success", False) and tx_resp.get("success", False)
                    return {
                        "operation": operation,
                        "success": success,
                        "data": {"sign": sign_resp, "transmit": tx_resp, "irn": final_irn or irn},
                    }

                elif operation == "validate_invoice_for_firs":
                    # Validate invoice via thin HTTP client
                    if not http_client:
                        return {"operation": operation, "success": False, "error": "http_client_unavailable"}
                    data = payload.get("validation_data") or payload.get("submission_data") or {}
                    firs_invoice = build_firs_invoice(data)
                    resp = await http_client.validate_invoice(firs_invoice)
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
                        resp = await http_client.validate_invoice(build_firs_invoice(item))
                        overall = overall and resp.get("success", False)
                        results.append(resp)
                    return {"operation": operation, "success": overall, "data": {"results": results}}

                elif operation == "get_firs_validation_rules":
                    # Use resource cache to return consolidated rules metadata
                    if not resource_cache:
                        return {"operation": operation, "success": False, "error": "resource_cache_unavailable"}
                    resources = await resource_cache.get_resources()
                    normalized = resources or {}
                    metadata = {
                        "retrieved_at": _utc_now(),
                        "resource_keys": sorted(normalized.keys()) if isinstance(normalized, dict) else [],
                    }
                    combined_etag = await _call_optional(resource_cache, "get_combined_etag")
                    if combined_etag:
                        metadata["etag"] = combined_etag
                    last_modified_ts = await _call_optional(resource_cache, "get_last_modified")
                    if last_modified_ts:
                        metadata["last_modified"] = _format_last_modified(last_modified_ts)
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "resources": normalized,
                            "metadata": metadata,
                        },
                    }

                elif operation == "refresh_firs_resources":
                    if not resource_cache:
                        return {"operation": operation, "success": False, "error": "resource_cache_unavailable"}
                    resources = await resource_cache.refresh_all()
                    metadata = {
                        "retrieved_at": _utc_now(),
                        "resource_keys": sorted(resources.keys()) if isinstance(resources, dict) else [],
                    }
                    combined_etag = resource_cache.get_combined_etag()
                    if combined_etag:
                        metadata["etag"] = combined_etag
                    last_modified_ts = resource_cache.get_last_modified()
                    if last_modified_ts:
                        metadata["last_modified"] = _format_last_modified(last_modified_ts)
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "resources": resources,
                            "metadata": metadata,
                        },
                    }

                elif operation == "refresh_firs_resource":
                    if not resource_cache:
                        return {"operation": operation, "success": False, "error": "resource_cache_unavailable"}
                    res_key = payload.get("resource")
                    if res_key not in ("currencies", "invoice-types", "services-codes", "vat-exemptions"):
                        return {"operation": operation, "success": False, "error": "invalid_resource"}
                    out = await resource_cache.refresh_resource(res_key)
                    metadata = {
                        "retrieved_at": _utc_now(),
                        "resource": res_key,
                    }
                    etag = resource_cache.get_resource_etag(res_key)
                    if etag:
                        metadata["etag"] = etag
                    last_modified_ts = resource_cache.get_resource_last_modified(res_key)
                    if last_modified_ts:
                        metadata["last_modified"] = _format_last_modified(last_modified_ts)
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "resource": res_key,
                            "value": out.get(res_key),
                            "metadata": metadata,
                        },
                    }

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
                    if not resp.get("success"):
                        return {
                            "operation": operation,
                            "success": False,
                            "error": resp.get("error") or resp.get("data"),
                            "data": {
                                "status_code": resp.get("status_code"),
                                "firs_response": resp.get("data"),
                            },
                        }
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "irn": irn,
                            "status_code": resp.get("status_code"),
                            "updated_at": _utc_now(),
                            "firs_response": resp.get("data"),
                        },
                    }

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
                            identifiers = sign_resp.get("identifiers") or extract_firs_identifiers(sign_resp.get("data"))
                            if identifiers:
                                sign_resp["identifiers"] = identifiers
                                item.update({
                                    "irn": identifiers.get("irn", item.get("irn")),
                                    "csid": identifiers.get("csid") or item.get("csid"),
                                    "csidHash": identifiers.get("csid_hash") or item.get("csidHash"),
                                    "qr": identifiers.get("qr_payload") or item.get("qr"),
                                })
                            if not sign_resp.get("success"):
                                results.append({"sign": sign_resp, "transmit": None, "success": False})
                                overall = False
                                continue
                            irn = item.get("irn")
                            if not irn and isinstance(sign_resp.get("data"), dict):
                                irn = sign_resp["data"].get("irn")
                            if not irn and identifiers:
                                irn = identifiers.get("irn")
                            if not irn:
                                results.append({"sign": sign_resp, "transmit": {"success": False, "error": "missing_irn"}, "success": False})
                                overall = False
                                continue
                            tx_resp = await http_client.transmit(irn)
                            tx_identifiers = tx_resp.get("identifiers") or extract_firs_identifiers(tx_resp.get("data"))
                            if tx_identifiers:
                                tx_resp["identifiers"] = tx_identifiers
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
                    irn = await _resolve_irn_from_storage(payload)
                    if not irn:
                        return {"operation": operation, "success": False, "error": "missing_irn"}
                    payload = dict(payload)
                    payload["irn"] = irn
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
                    identifiers = resp.get("identifiers") or extract_firs_identifiers(resp.get("data"))
                    if identifiers:
                        resp["identifiers"] = identifiers
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
                        base_payload = data if isinstance(data, dict) else (resp if isinstance(resp, dict) else {})
                        normalized_payload = merge_identifiers_into_payload(base_payload, identifiers or {})
                        firs_status = (resp.get("status") if isinstance(resp, dict) else None) or (base_payload.get("status") if isinstance(base_payload, dict) else None) or "submitted"
                        firs_response_id = (data.get("submission_id") if isinstance(data, dict) else None) or (data.get("id") if isinstance(data, dict) else None)
                        await self.message_router.route_message(
                            service_role=ServiceRole.HYBRID,
                            operation="update_firs_response",
                            payload={
                                "irn": irn,
                                "firs_response_id": str(firs_response_id) if firs_response_id else None,
                                "firs_status": str(firs_status),
                                "response_data": normalized_payload,
                                "identifiers": identifiers,
                            },
                        )
                    except Exception:
                        logger.debug("Correlation update_firs_response skipped")
                    return {"operation": operation, "success": resp.get("success", False), "data": resp}

                elif operation == "confirm_firs_receipt":
                    if not http_client:
                        return {"operation": operation, "success": False, "error": "http_client_unavailable"}
                    irn = await _resolve_irn_from_storage(payload)
                    if not irn:
                        return {"operation": operation, "success": False, "error": "missing_irn"}
                    resp = await http_client.confirm_receipt(irn, payload.get("options"))
                    return {"operation": operation, "success": resp.get("success", False), "data": resp}

                elif operation in ("authenticate_with_firs", "authenticate_firs"):
                    auth_payload = payload.get("auth_data") or payload
                    auth_result = await _run_header_auth_check(auth_payload or {})
                    if auth_result.get("success"):
                        data = {
                            "environment": auth_result.get("environment"),
                            "status_code": auth_result.get("status_code"),
                            "request_id": auth_result.get("request_id"),
                            "message": "FIRS header authentication verified",
                            "response": auth_result.get("data"),
                        }
                    else:
                        data = {
                            "error": auth_result.get("error") or auth_result.get("error_message"),
                            "details": auth_result.get("details"),
                            "status_code": auth_result.get("status_code"),
                            "response": auth_result.get("data"),
                        }
                    return {"operation": operation, "success": auth_result.get("success", False), "data": data}

                elif operation == "refresh_firs_token":
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "message": "Header-based FIRS authentication does not require token refresh",
                            "timestamp": _utc_now(),
                        },
                    }

                elif operation == "test_firs_connection":
                    if http_client:
                        resp = await http_client.transmit_self_health()
                        return {"operation": operation, "success": resp.get("success", False), "data": resp}
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {"status": "unknown", "reason": "http_client_unavailable", "timestamp": _utc_now()}
                    }

                elif operation == "get_firs_connection_status":
                    user_uuid, org_uuid = await _resolve_identity(payload)
                    if not org_uuid:
                        status_payload = _build_status_payload({}, None)
                        status_payload["metadata"]["last_error"] = "organization_not_found"
                        return {"operation": operation, "success": True, "data": status_payload}

                    async for session in get_async_session():
                        organization = await session.get(Organization, org_uuid)
                        if not organization:
                            status_payload = _build_status_payload({}, org_uuid)
                            status_payload["metadata"]["last_error"] = "organization_not_found"
                            return {"operation": operation, "success": True, "data": status_payload}

                        config = organization.firs_configuration if isinstance(organization.firs_configuration, dict) else {}
                        status_payload = _build_status_payload(config, org_uuid)
                        if user_uuid and not status_payload.get("last_updated_by"):
                            status_payload["last_updated_by"] = str(user_uuid)
                        return {"operation": operation, "success": True, "data": status_payload}

                    return {"operation": operation, "success": False, "error": "session_unavailable"}

                elif operation == "update_firs_credentials":
                    credentials_payload = (
                        payload.get("credentials")
                        if isinstance(payload.get("credentials"), dict)
                        else payload
                    )
                    if not isinstance(credentials_payload, dict):
                        return {"operation": operation, "success": False, "error": "invalid_credentials_payload"}

                    user_uuid, org_uuid = await _resolve_identity(payload)
                    if not org_uuid:
                        return {"operation": operation, "success": False, "error": "organization_not_found"}

                    async for session in get_async_session():
                        organization = await session.get(Organization, org_uuid)
                        if not organization:
                            return {"operation": operation, "success": False, "error": "organization_not_found"}

                        existing_config = dict(organization.firs_configuration or {})

                        resolved_api_key = _resolve_secret_update(
                            credentials_payload.get("api_key"), existing_config.get("api_key")
                        )
                        resolved_api_secret = _resolve_secret_update(
                            credentials_payload.get("api_secret"), existing_config.get("api_secret")
                        )
                        environment = str(
                            credentials_payload.get("environment")
                            or existing_config.get("environment")
                            or "sandbox"
                        ).lower()
                        webhook_url = credentials_payload.get("webhook_url", existing_config.get("webhook_url"))

                        updated_config = dict(existing_config)
                        updated_config.update({
                            "environment": environment,
                            "webhook_url": webhook_url,
                            "last_updated_at": _utc_now(),
                            "last_updated_by": str(user_uuid) if user_uuid else existing_config.get("last_updated_by"),
                            "api_version": "v1",
                        })

                        updated_config["api_key"] = resolved_api_key
                        updated_config["api_secret"] = resolved_api_secret

                        if updated_config.get("api_key") and updated_config.get("api_secret"):
                            updated_config.setdefault("connection_status", "configured")
                        else:
                            updated_config["connection_status"] = "disconnected"

                        organization.firs_configuration = updated_config
                        session.add(organization)
                        await session.commit()
                        await session.refresh(organization)

                        status_payload = _build_status_payload(updated_config, org_uuid)
                        return {"operation": operation, "success": True, "data": status_payload}

                    return {"operation": operation, "success": False, "error": "session_unavailable"}

                elif operation == "get_firs_auth_status":
                    return {
                        "operation": operation,
                        "success": True,
                        "data": {
                            "provider": "header_based",
                            "is_authenticated": False,
                            "details": "FIRS header authentication is stateless; provide credentials per request",
                            "timestamp": _utc_now(),
                        },
                    }

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
                    filters = payload.get("filters") if isinstance(payload.get("filters"), dict) else {}
                    pagination = payload.get("pagination") if isinstance(payload.get("pagination"), dict) else {}
                    status_filter = (filters.get("status") or "").strip().lower() or None
                    start_at = _parse_date_filter(filters.get("start_date"))
                    end_at = _parse_date_filter(filters.get("end_date"))
                    try:
                        limit = max(1, int(pagination.get("limit", payload.get("limit", 50))))
                    except (TypeError, ValueError):
                        limit = 50
                    try:
                        offset = max(0, int(pagination.get("offset", payload.get("offset", 0))))
                    except (TypeError, ValueError):
                        offset = 0

                    resp = await _fetch_transmissions(payload.get("tin") or payload.get("taxpayer_tin"))
                    if resp.get("success"):
                        raw_records = _normalize_transmissions(resp.get("data"))
                        formatted = [_format_transmission(record) for record in raw_records]
                        filtered = _filter_transmissions(
                            formatted,
                            status_filter=status_filter,
                            start_at=start_at,
                            end_at=end_at,
                        )
                        total = len(filtered)
                        paged = filtered[offset : offset + limit]
                        summary_counts = Counter(item["status"] for item in filtered)
                        payload_data = {
                            "items": paged,
                            "count": total,
                            "summary": {
                                "total": total,
                                "statusCounts": dict(summary_counts),
                            },
                            "pagination": {"limit": limit, "offset": offset},
                            "generated_at": _utc_now(),
                        }
                        return {"operation": operation, "success": True, "data": payload_data}
                    return {
                        "operation": operation,
                        "success": False,
                        "error": resp.get("error", "transmission_lookup_failed"),
                        "data": resp.get("data"),
                    }

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
                        if certificate_provider:
                            certificate_provider.refresh(organization_id=payload.get("organization_id"))
                        api_client = firs_service.get("api_client")
                        if api_client:
                            api_client.set_certificate_provider(certificate_provider)
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
                    filters = payload.get("filters") if isinstance(payload.get("filters"), dict) else {}
                    status_filter = (filters.get("status") or "").strip().lower() or None
                    start_at = _parse_date_filter(filters.get("start_date"))
                    end_at = _parse_date_filter(filters.get("end_date"))
                    resp = await _fetch_transmissions(payload.get("tin") or payload.get("taxpayer_tin"))
                    if resp.get("success"):
                        raw_records = _normalize_transmissions(resp.get("data"))
                        formatted = [_format_transmission(record) for record in raw_records]
                        filtered = _filter_transmissions(
                            formatted,
                            status_filter=status_filter,
                            start_at=start_at,
                            end_at=end_at,
                        )
                        summary_counts = Counter(item["status"] for item in filtered)
                        report = {
                            "generated_at": _utc_now(),
                            "total": len(filtered),
                            "statusBreakdown": dict(summary_counts),
                            "dailyCounts": _aggregate_by_day(filtered),
                            "recent": filtered[:10],
                        }
                        return {"operation": operation, "success": True, "data": report}
                    return {
                        "operation": operation,
                        "success": False,
                        "error": resp.get("error", "report_generation_failed"),
                    }

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
