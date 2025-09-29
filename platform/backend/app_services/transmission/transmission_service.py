"""Transmission orchestration for APP message router callbacks.

This module provides a service layer that backs the App Gateway transmission
endpoints using the platform's async repositories and FIRS client helpers.
It replaces the earlier mock replies with database-backed results while
preserving the route-facing contract.
"""

from __future__ import annotations

import logging
import os
import uuid
from contextlib import asynccontextmanager, nullcontext
from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select

from core_platform.authentication.tenant_context import tenant_context
from core_platform.data_management.db_async import get_async_session
from core_platform.data_management.models.firs_submission import (
    FIRSSubmission,
    InvoiceType,
    SubmissionStatus,
)
from core_platform.data_management.models.organization import Organization
from core_platform.data_management.repositories import (
    firs_submission_repo_async as firs_repo,
    invoice_repo_async as invoice_repo,
    participant_repo_async as participant_repo,
)
from core_platform.data_management.models.network import ParticipantStatus
from core_platform.messaging.message_router import MessageRouter, ServiceRole
from core_platform.messaging.queue_manager import get_queue_manager
from core_platform.messaging.queue_manager import (
    QueueConfiguration,
    QueueType,
    QueueStrategy,
    QueuedMessage,
)
from core_platform.utils.firs_response import (
    extract_firs_identifiers,
    merge_identifiers_into_payload,
)

from app_services.firs_communication.firs_payload_mapper import build_firs_invoice
from app_services.transmission.retry_handler import RetryHandler, RetryPolicy, RetryStrategy
from app_services.transmission.secure_transmitter import (
    TransmissionRequest,
    TransmissionResult,
    TransmissionStatus,
    SecurityLevel,
)

from si_services.schema_compliance import (
    compliance_checker,
    ComplianceLevel,
    ComplianceStatus,
)
from si_services.certificate_management.digital_certificate_service import DigitalCertificateService


InvoiceRecord = invoice_repo.InvoiceRecord


class TransmissionService:
    """Handle APP transmission operations routed through the MessageRouter."""

    _BATCH_STATUSES = {
        SubmissionStatus.PENDING,
        SubmissionStatus.PROCESSING,
    }

    _STATUS_MAP = {
        "submitted": SubmissionStatus.SUBMITTED,
        "submitting": SubmissionStatus.SUBMITTED,
        "accepted": SubmissionStatus.ACCEPTED,
        "acknowledged": SubmissionStatus.ACCEPTED,
        "completed": SubmissionStatus.ACCEPTED,
        "processing": SubmissionStatus.PROCESSING,
        "pending": SubmissionStatus.PENDING,
        "failed": SubmissionStatus.FAILED,
        "rejected": SubmissionStatus.REJECTED,
        "cancelled": SubmissionStatus.CANCELLED,
    }

    class _RouterTransmissionAdapter:
        """Bridge TransmissionRequest execution through the message router."""

        def __init__(self, service: "TransmissionService") -> None:
            self._service = service
            self._logger = logging.getLogger(f"{__name__}.RouterTransmitter")

        async def transmit_document(self, request: TransmissionRequest) -> TransmissionResult:
            metadata = request.metadata or {}
            operation = metadata.get("operation") or "submit_invoice_to_firs"

            payload = dict(metadata.get("payload") or {})
            organization_id = metadata.get("organization_id")
            invoice_number = metadata.get("invoice_number") or request.document_id

            if "organization_id" not in payload and organization_id:
                payload["organization_id"] = organization_id
            if "invoice_number" not in payload and invoice_number:
                payload["invoice_number"] = invoice_number
            if "invoice_data" not in payload:
                payload["invoice_data"] = request.document_data

            response = await self._service._call_firs(operation, payload)

            success = bool(response.get("success")) if isinstance(response, dict) else False
            data = response.get("data") if isinstance(response, dict) else None
            error = response.get("error") if isinstance(response, dict) else None

            result = TransmissionResult(
                request_id=str(uuid.uuid4()),
                document_id=request.document_id,
                status=TransmissionStatus.DELIVERED if success else TransmissionStatus.FAILED,
                transmission_id=(data or {}).get("submission_id") or (data or {}).get("id"),
                response_data=data if isinstance(data, dict) else None,
                error_message=None if success else (error or "transmission_failed"),
                metadata={**metadata, "operation": operation},
            )

            if result.status == TransmissionStatus.DELIVERED:
                result.transmitted_at = datetime.now(timezone.utc)
            else:
                self._logger.debug(
                    "Router transmission failed for %s: %s",
                    request.document_id,
                    result.error_message,
                )

            return result

    def __init__(self, message_router: MessageRouter) -> None:
        self.message_router = message_router
        self.logger = logging.getLogger(__name__)
        self._queue_manager = None
        self._queue_consumers_registered = False
        self._status_poll_consumer_registered = False
        self._retry_handler: Optional[RetryHandler] = None
        self._router_transmitter = self._RouterTransmissionAdapter(self)
        self._default_retry_policy = RetryPolicy(
            max_attempts=5,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            base_delay=5.0,
            max_delay=600.0,
            backoff_multiplier=2.0,
            jitter_factor=0.2,
            timeout=1800.0,
        )
        self._digital_certificate_service = DigitalCertificateService()
        self._signing_certificate_cache: Dict[str, Optional[str]] = {}
        self._correlation_sla_target_ms = self._resolve_correlation_sla_target_ms()

    async def handle(self, operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        handlers = {
            "get_available_batches": self._handle_get_available_batches,
            "list_transmission_batches": self._handle_list_transmission_batches,
            "get_batch_details": self._handle_get_batch_details,
            "submit_invoice_batches": self._handle_submit_invoice_batches,
            "submit_invoice_file": self._handle_submit_invoice_file,
            "submit_single_batch": self._handle_submit_single_batch,
            "generate_firs_compliant_invoice": self._handle_generate_invoice,
            "generate_invoice_batch": self._handle_generate_invoice_batch,
            "submit_invoice": self._handle_submit_invoice,
            "submit_invoice_batch": self._handle_submit_invoice_batches,
            "get_submission_status": self._handle_get_submission_status,
            "list_submissions": self._handle_list_submissions,
            "cancel_invoice_submission": self._handle_cancel_submission,
            "cancel_transmission": self._handle_cancel_submission,
            "resubmit_invoice": self._handle_resubmit_invoice,
            "retry_transmission": self._handle_retry_transmission,
            "get_invoice": self._handle_get_invoice,
            "get_transmission_history": self._handle_get_transmission_history,
            "get_transmission_details": self._handle_get_transmission_details,
            "generate_transmission_report": self._handle_generate_transmission_report,
            "get_transmission_status": self._handle_get_submission_status,
            "get_transmission_statistics": self._handle_get_transmission_statistics,
            "transmit_batch": self._handle_queue_transmission,
            "transmit_real_time": self._handle_queue_transmission,
            "run_b2c_reporting_job": self._handle_run_b2c_reporting_job,
        }

        handler = handlers.get(operation)
        if not handler:
            return self._unsupported(operation)

        try:
            data = await handler(payload)
            return self._success(operation, data)
        except Exception as exc:  # pragma: no cover - defensive catch for router path
            self.logger.exception("Transmission operation failed: %s", operation)
            return self._failure(operation, str(exc))

    # ------------------------------------------------------------------
    # Query helpers
    # ------------------------------------------------------------------

    @asynccontextmanager
    async def _session_scope(self):
        async for session in get_async_session():
            yield session
            break

    def _resolve_org_id(self, payload: Dict[str, Any]) -> Optional[str]:
        """Best-effort extraction of organization/tenant identifier from payload."""

        def _extract(source: Dict[str, Any]) -> Optional[str]:
            for key in ("organization_id", "organizationId", "org_id", "tenant_id", "tenantId"):
                value = source.get(key)
                if value:
                    return str(value)
            return None

        if not isinstance(payload, dict):
            return None

        direct = _extract(payload)
        if direct:
            return direct

        nested_candidates = (
            payload.get("context"),
            payload.get("metadata"),
            payload.get("invoice_data"),
            payload.get("submission_data"),
            payload.get("batch_submission_data"),
            payload.get("generation_data"),
            payload.get("filters"),
        )
        for candidate in nested_candidates:
            if isinstance(candidate, dict):
                value = _extract(candidate)
                if value:
                    return value

        return None

    def _resolve_invoice_number(self, payload: Any, fallback: Optional[str] = None) -> Optional[str]:
        """Extract invoice identifier from assorted payload shapes."""

        if isinstance(payload, dict):
            for key in ("invoice_id", "invoiceId", "invoice_number", "invoiceNumber", "irn"):
                value = payload.get(key)
                if value:
                    return str(value)

            metadata = payload.get("metadata")
            if isinstance(metadata, dict):
                for key in ("invoice_id", "invoiceNumber", "invoice_number"):
                    value = metadata.get(key)
                    if value:
                        return str(value)

        return fallback

    def _ensure_uuid(self, value: Any) -> Optional[UUID]:
        if not value:
            return None
        try:
            return UUID(str(value))
        except Exception:
            return None

    def _resolve_signature_preferences(
        self,
        options: Optional[Dict[str, Any]],
    ) -> Tuple[bool, bool]:
        """Return tuple of (sign_enabled, require_signature)."""

        env_sign = str(os.getenv("APP_TRANSMISSION_AUTO_SIGN", "true")).lower() in (
            "1",
            "true",
            "yes",
            "on",
        )
        env_required = str(os.getenv("APP_TRANSMISSION_REQUIRE_SIGNATURE", "false")).lower() in (
            "1",
            "true",
            "yes",
            "on",
        )

        sign_enabled = env_sign
        require_signature = env_required

        if isinstance(options, dict):
            if "sign_before_transmit" in options:
                sign_enabled = bool(options["sign_before_transmit"])
            if "require_signature" in options:
                require_signature = bool(options["require_signature"])

        return sign_enabled, require_signature

    def _extract_validation_warnings(self, report: Dict[str, Any]) -> List[str]:
        warnings: List[str] = []
        results = report.get("validation_results")
        if not isinstance(results, dict):
            return warnings
        for stage, outcome in results.items():
            if not isinstance(outcome, dict):
                continue
            for error_entry in outcome.get("errors", []):
                if isinstance(error_entry, dict) and error_entry.get("severity") in {"warning", "info"}:
                    message = error_entry.get("message") or stage
                    warnings.append(f"{stage}:{message}")
        return warnings

    def _extract_validation_error(self, report: Dict[str, Any]) -> Optional[str]:
        results = report.get("validation_results")
        if not isinstance(results, dict):
            return None
        for stage, outcome in results.items():
            if not isinstance(outcome, dict):
                continue
            for error_entry in outcome.get("errors", []):
                if isinstance(error_entry, dict) and error_entry.get("severity") == "error":
                    message = error_entry.get("message") or stage
                    return f"{stage}:{message}"
        return None

    async def _validate_invoice(
        self,
        invoice_payload: Dict[str, Any],
        *,
        organization_id: Optional[str],
        invoice_number: Optional[str],
    ) -> Dict[str, Any]:
        context = {
            "organization_id": organization_id,
            "invoice_number": invoice_number,
            "source": "app_transmission",
        }
        report = compliance_checker.check_full_compliance(
            invoice_payload,
            compliance_level=ComplianceLevel.STRICT,
            transform_if_needed=True,
            context=context,
        )

        overall = report.get("overall_status")
        total_errors = report.get("summary", {}).get("total_errors", 0)
        if (
            overall in {ComplianceStatus.ERROR.value, ComplianceStatus.NON_COMPLIANT.value}
            or (isinstance(total_errors, int) and total_errors > 0)
        ):
            first_error = self._extract_validation_error(report) or "validation_failed"
            raise ValueError(f"invoice_validation_failed:{first_error}")

        return report

    async def _get_signing_certificate_id(self, organization_id: Optional[str]) -> Optional[str]:
        cache_key = str(organization_id) if organization_id else "default"
        if cache_key in self._signing_certificate_cache:
            return self._signing_certificate_cache[cache_key]

        certificate_id = os.getenv("APP_SIGNING_CERTIFICATE_ID")

        if organization_id and not certificate_id:
            async with self._session_scope() as session:
                org_uuid = self._ensure_uuid(organization_id)
                organization = None
                if org_uuid:
                    organization = await session.get(Organization, org_uuid)
                else:
                    stmt = select(Organization).where(Organization.firs_service_id == str(organization_id)).limit(1)
                    organization = (await session.execute(stmt)).scalars().first()
                if organization and organization.firs_configuration:
                    certificate_id = (
                        organization.firs_configuration.get("signing_certificate_id")
                        or organization.firs_configuration.get("certificate_id")
                    )

        self._signing_certificate_cache[cache_key] = certificate_id
        return certificate_id

    async def _maybe_sign_invoice(
        self,
        invoice_payload: Dict[str, Any],
        *,
        organization_id: Optional[str],
        options: Optional[Dict[str, Any]],
        validation_warnings: Optional[List[str]] = None,
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]], List[str]]:
        warnings = list(validation_warnings or [])
        sign_enabled, require_signature = self._resolve_signature_preferences(options)
        if not sign_enabled:
            return invoice_payload, None, warnings

        certificate_id = await self._get_signing_certificate_id(organization_id)
        if not certificate_id:
            message = "signing_certificate_unavailable"
            if require_signature:
                raise ValueError(message)
            warnings.append(message)
            return invoice_payload, None, warnings

        try:
            signature_info = self._digital_certificate_service.sign_invoice_document(
                document=invoice_payload,
                certificate_id=certificate_id,
            )
        except Exception as exc:
            message = f"signature_failed:{exc}"
            if require_signature:
                raise ValueError(message)
            warnings.append(message)
            return invoice_payload, None, warnings

        signed_payload = dict(invoice_payload)
        signed_payload["signature"] = signature_info
        return signed_payload, signature_info, warnings

    async def _prepare_invoice_for_submission(
        self,
        invoice: Dict[str, Any],
        *,
        organization_id: Optional[str],
        invoice_number: Optional[str],
        options: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], Dict[str, Any], List[str]]:
        firs_invoice = build_firs_invoice(invoice)
        validation_report = await self._validate_invoice(
            firs_invoice,
            organization_id=organization_id,
            invoice_number=invoice_number,
        )
        validation_warnings = self._extract_validation_warnings(validation_report)
        signed_invoice, signature_info, signing_warnings = await self._maybe_sign_invoice(
            firs_invoice,
            organization_id=organization_id,
            options=options,
            validation_warnings=validation_warnings,
        )
        pipeline_metadata = {
            "validation_report": validation_report,
            "signature": signature_info,
        }
        combined_warnings = validation_warnings + [w for w in signing_warnings if w not in validation_warnings]
        return signed_invoice, pipeline_metadata, combined_warnings

    def _is_b2c_invoice(self, invoice: Dict[str, Any]) -> bool:
        if not isinstance(invoice, dict):
            return False
        metadata = invoice.get("documentMetadata")
        if isinstance(metadata, dict):
            customer_type = metadata.get("customerType") or metadata.get("customer_type")
            if isinstance(customer_type, str) and customer_type.upper() == "B2C":
                return True
        customer = invoice.get("customer") or invoice.get("buyer") or invoice.get("accountingCustomerParty")
        if isinstance(customer, dict):
            tax_id = (
                customer.get("tin")
                or customer.get("tax_id")
                or customer.get("taxId")
                or customer.get("vat")
            )
            if tax_id and str(tax_id).strip():
                return False
        # Default heuristic: if customer TIN stored elsewhere on submission it'll be set; absence implies B2C
        return True

    def _now_iso(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _resolve_correlation_sla_target_ms(self) -> Optional[int]:
        for raw_value, multiplier in (
            (os.getenv("APP_CORRELATION_SLA_MS"), 1.0),
            (os.getenv("APP_CORRELATION_SLA_MINUTES"), 60_000.0),
        ):
            if raw_value is None:
                continue
            try:
                candidate = float(raw_value) * multiplier
            except (TypeError, ValueError):
                continue
            if candidate <= 0:
                return None
            return int(candidate)

        default_raw = os.getenv("APP_CORRELATION_SLA_DEFAULT_MS")
        if default_raw is not None:
            try:
                default_value = float(default_raw)
            except (TypeError, ValueError):
                return None
            if default_value <= 0:
                return None
            return int(default_value)

        return 900_000

    def _build_correlation_metadata(
        self,
        *,
        stage: str,
        pipeline_started_at: datetime,
        previous_stage_at: datetime,
        submission_id: Optional[str],
        correlation_id: Optional[str],
        organization_id: Optional[str],
        si_invoice_id: Optional[str],
        extra: Optional[Dict[str, Any]] = None,
    ) -> Tuple[Dict[str, Any], datetime]:
        now = datetime.now(timezone.utc)
        metadata: Dict[str, Any] = {
            "stage": stage,
            "timestamp": now.isoformat(),
            "source": "app_transmission",
            "pipeline_started_at": pipeline_started_at.isoformat(),
        }
        if submission_id:
            metadata["submission_id"] = submission_id
        if correlation_id:
            metadata["correlation_id"] = correlation_id
        if organization_id:
            metadata["organization_id"] = organization_id
        if si_invoice_id:
            metadata["si_invoice_id"] = si_invoice_id

        elapsed_ms = max(0, int((now - pipeline_started_at).total_seconds() * 1000))
        stage_elapsed_ms = max(0, int((now - previous_stage_at).total_seconds() * 1000))
        metadata["timings"] = {
            "elapsed_ms": elapsed_ms,
            "stage_elapsed_ms": stage_elapsed_ms,
        }

        sla_target_ms = self._correlation_sla_target_ms
        if sla_target_ms is not None:
            metadata["sla"] = {
                "target_ms": sla_target_ms,
                "elapsed_ms": elapsed_ms,
                "breached": elapsed_ms > sla_target_ms,
            }

        if extra:
            metadata.update(extra)

        return metadata, now

    async def _emit_correlation_event(
        self,
        operation: str,
        *,
        irn: Optional[str],
        app_submission_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        firs_response_id: Optional[str] = None,
        firs_status: Optional[str] = None,
        response_data: Optional[Dict[str, Any]] = None,
        identifiers: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not irn or not self.message_router:
            return

        payload: Dict[str, Any] = {"irn": irn}
        if app_submission_id:
            payload["app_submission_id"] = app_submission_id
        if metadata is not None:
            payload["metadata"] = metadata
        if firs_response_id:
            payload["firs_response_id"] = firs_response_id
        if firs_status:
            payload["firs_status"] = firs_status
        if response_data is not None:
            payload["response_data"] = response_data
        if identifiers:
            payload["identifiers"] = identifiers

        try:
            await self.message_router.route_message(
                service_role=ServiceRole.HYBRID,
                operation=operation,
                payload=payload,
            )
        except Exception as exc:  # pragma: no cover - correlation telemetry is best-effort
            self.logger.debug(
                "Correlation event %s skipped for IRN %s: %s",
                operation,
                irn,
                exc,
            )

    def _record_transmission_metric(self, queue_name: str, outcome: str) -> None:
        try:
            from core_platform.monitoring.prometheus_integration import get_prometheus_integration

            prom = get_prometheus_integration()
            if prom:
                prom.record_metric(
                    "taxpoynt_firs_transmission_result_total",
                    1,
                    {"queue": queue_name, "outcome": outcome},
                )
        except Exception:
            pass

    async def _record_sla_telemetry(self, metadata: Dict[str, Any], stage: str) -> None:
        if not isinstance(metadata, dict):
            return

        sla_blob = metadata.get("sla") if isinstance(metadata, dict) else None
        if not isinstance(sla_blob, dict):
            return

        elapsed_ms = sla_blob.get("elapsed_ms")
        target_ms = sla_blob.get("target_ms")
        breached = bool(sla_blob.get("breached"))

        try:
            from core_platform.monitoring.prometheus_integration import get_prometheus_integration

            prom = get_prometheus_integration()
            if prom and elapsed_ms is not None:
                prom.record_metric(
                    "taxpoynt_sla_elapsed_seconds",
                    float(elapsed_ms) / 1000.0,
                    {"service": "app_transmission", "stage": stage},
                )
                if breached:
                    breach_type = "hard" if target_ms is not None and elapsed_ms > target_ms else "soft"
                    prom.record_metric(
                        "taxpoynt_sla_breach_total",
                        1,
                        {"service": "app_transmission", "stage": stage, "breach_type": breach_type},
                    )
        except Exception:
            pass

        try:
            from core_platform.monitoring.opentelemetry_integration import record_sla_event

            await record_sla_event(
                service="app_transmission",
                stage=stage,
                elapsed_ms=float(elapsed_ms) if elapsed_ms is not None else None,
                target_ms=float(target_ms) if target_ms is not None else None,
                breached=breached,
            )
        except Exception:
            pass

    async def _dispatch_dead_letter(
        self,
        message: QueuedMessage,
        request: TransmissionRequest,
        result: TransmissionResult,
        error: Optional[str] = None,
    ) -> None:
        try:
            from core_platform.messaging.dead_letter_handler import (
                get_dead_letter_handler,
                FailureReason,
            )

            handler = get_dead_letter_handler()
            if not handler:
                return

            metadata = {
                "document_id": request.document_id,
                "organization_id": request.metadata.get("organization_id"),
                "operation": request.metadata.get("operation"),
                "queue": message.queue_name,
                "transmission_status": getattr(result.status, "value", str(result.status)),
                "transmission_id": result.transmission_id,
            }

            await handler.handle_failed_message(
                message,
                failure_reason=FailureReason.RETRY_EXHAUSTED,
                error_message=error or result.error_message or "transmission_failed",
                source_queue=message.queue_name,
                source_service="app_transmission",
                metadata=metadata,
            )
        except Exception as exc:
            self.logger.debug("Dead-letter dispatch skipped: %s", exc)

    def _iso(self, dt: Optional[datetime]) -> Optional[str]:
        if not dt:
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()

    def _parse_decimal(self, raw: Any) -> Optional[Decimal]:
        if raw is None:
            return None
        try:
            return Decimal(str(raw))
        except (InvalidOperation, ValueError, TypeError):
            return None

    def _default_destination_endpoint(self) -> str:
        return os.getenv("FIRS_API_URL", "https://sandbox-api.firs.gov.ng")

    def _clone_retry_policy(self) -> RetryPolicy:
        return RetryPolicy(
            max_attempts=self._default_retry_policy.max_attempts,
            strategy=self._default_retry_policy.strategy,
            base_delay=self._default_retry_policy.base_delay,
            max_delay=self._default_retry_policy.max_delay,
            backoff_multiplier=self._default_retry_policy.backoff_multiplier,
            jitter_factor=self._default_retry_policy.jitter_factor,
            timeout=self._default_retry_policy.timeout,
            retry_on_status=list(self._default_retry_policy.retry_on_status),
            retry_on_reasons=list(self._default_retry_policy.retry_on_reasons),
            circuit_breaker_enabled=self._default_retry_policy.circuit_breaker_enabled,
            circuit_breaker_threshold=self._default_retry_policy.circuit_breaker_threshold,
            circuit_breaker_timeout=self._default_retry_policy.circuit_breaker_timeout,
        )

    def _build_retry_policy(self, raw_policy: Optional[Dict[str, Any]]) -> RetryPolicy:
        if not isinstance(raw_policy, dict):
            return self._clone_retry_policy()

        policy = self._clone_retry_policy()

        if "max_attempts" in raw_policy:
            try:
                policy.max_attempts = max(1, int(raw_policy["max_attempts"]))
            except (TypeError, ValueError):
                pass

        if "base_delay" in raw_policy:
            try:
                policy.base_delay = float(raw_policy["base_delay"])
            except (TypeError, ValueError):
                pass

        if "max_delay" in raw_policy:
            try:
                policy.max_delay = float(raw_policy["max_delay"])
            except (TypeError, ValueError):
                pass

        if "backoff_multiplier" in raw_policy:
            try:
                policy.backoff_multiplier = max(1.0, float(raw_policy["backoff_multiplier"]))
            except (TypeError, ValueError):
                pass

        if "jitter_factor" in raw_policy:
            try:
                jitter_value = float(raw_policy["jitter_factor"])
                policy.jitter_factor = max(0.0, min(jitter_value, 1.0))
            except (TypeError, ValueError):
                pass

        if "timeout" in raw_policy:
            try:
                policy.timeout = max(0.0, float(raw_policy["timeout"]))
            except (TypeError, ValueError):
                pass

        if "strategy" in raw_policy and isinstance(raw_policy["strategy"], str):
            strategy_value = raw_policy["strategy"].strip().lower()
            for candidate in RetryStrategy:
                if candidate.value == strategy_value or candidate.name.lower() == strategy_value:
                    policy.strategy = candidate
                    break

        return policy

    def _create_transmission_request(
        self,
        *,
        document_id: str,
        document_data: Dict[str, Any],
        organization_id: Optional[str],
        operation: str,
        priority: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> TransmissionRequest:
        enriched_metadata = {
            "operation": operation,
            "organization_id": organization_id,
            "invoice_number": document_id,
        }
        if metadata:
            enriched_metadata.update(metadata)

        document_type = str(document_data.get("invoiceType") or document_data.get("invoice_type") or "firs_invoice")

        return TransmissionRequest(
            document_id=str(document_id),
            document_type=document_type,
            document_data=document_data,
            destination_endpoint=self._default_destination_endpoint(),
            security_level=SecurityLevel.STANDARD,
            priority=priority,
            metadata=enriched_metadata,
        )

    def _serialize_transmission_request(self, request: TransmissionRequest) -> Dict[str, Any]:
        return {
            "document_id": request.document_id,
            "document_type": request.document_type,
            "document_data": request.document_data,
            "destination_endpoint": request.destination_endpoint,
            "security_level": request.security_level.value if isinstance(request.security_level, SecurityLevel) else request.security_level,
            "priority": request.priority,
            "metadata": request.metadata,
        }

    def _deserialize_transmission_request(self, data: Dict[str, Any]) -> TransmissionRequest:
        level_value = data.get("security_level") or SecurityLevel.STANDARD.value
        try:
            security_level = SecurityLevel(level_value)
        except Exception:
            security_level = SecurityLevel.STANDARD

        return TransmissionRequest(
            document_id=str(data.get("document_id")),
            document_type=str(data.get("document_type") or "firs_invoice"),
            document_data=data.get("document_data") or {},
            destination_endpoint=data.get("destination_endpoint") or self._default_destination_endpoint(),
            security_level=security_level,
            priority=int(data.get("priority", 1)),
            metadata=data.get("metadata") or {},
        )

    def _map_status(self, status_value: Any, success_hint: Optional[bool] = None) -> SubmissionStatus:
        if isinstance(status_value, SubmissionStatus):
            return status_value
        if isinstance(status_value, str):
            status_key = status_value.lower()
        elif isinstance(status_value, dict):
            status_key = str(status_value.get("status", "")).lower()
        else:
            status_key = ""
        mapped = self._STATUS_MAP.get(status_key)
        if mapped:
            return mapped
        if success_hint is False:
            return SubmissionStatus.FAILED
        if success_hint is True:
            return SubmissionStatus.SUBMITTED
        return SubmissionStatus.PROCESSING

    def _normalize_invoice_payload(self, data: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not isinstance(data, dict):
            return None
        if "invoice_data" in data and isinstance(data["invoice_data"], dict):
            return self._normalize_invoice_payload(data["invoice_data"])
        if "firs_invoice" in data and isinstance(data["firs_invoice"], dict):
            return self._normalize_invoice_payload(data["firs_invoice"])
        if "documentMetadata" in data and isinstance(data["documentMetadata"], dict):
            normalized = dict(data)
            metadata = normalized["documentMetadata"]
            invoice_number = metadata.get("invoiceNumber") or metadata.get("invoice_number")
            if invoice_number:
                normalized.setdefault("invoiceNumber", invoice_number)
                normalized.setdefault("invoice_number", invoice_number)
            if metadata.get("invoiceDate"):
                normalized.setdefault("invoice_date", metadata.get("invoiceDate"))
            return normalized
        return data

    def _looks_like_invoice_payload(self, data: Any) -> bool:
        normalized = self._normalize_invoice_payload(data)
        if not isinstance(normalized, dict):
            return False
        indicators = {
            "items",
            "lineItems",
            "totalAmount",
            "total_amount",
            "subtotal",
            "customer",
            "customer_info",
        }
        return any(key in normalized for key in indicators)

    def _combine_invoice_payload(
        self,
        existing: Optional[Dict[str, Any]],
        record: Optional[InvoiceRecord],
    ) -> Optional[Dict[str, Any]]:
        merged: Dict[str, Any] = {}
        if record and isinstance(record.invoice_data, dict):
            merged.update(record.invoice_data)
        if isinstance(existing, dict):
            merged.update(existing)
        return merged or None

    async def _fetch_invoice_record(
        self,
        *,
        organization_id: Optional[str],
        invoice_number: Optional[str],
        submission_id: Optional[str],
        irn: Optional[str],
        correlation_id: Optional[str],
        si_invoice_id: Optional[str],
    ) -> Optional[InvoiceRecord]:
        async with self._session_scope() as session:
            return await invoice_repo.get_invoice_record(
                session,
                organization_id=organization_id,
                invoice_number=invoice_number,
                submission_id=submission_id,
                irn=irn,
                correlation_id=correlation_id,
                si_invoice_id=si_invoice_id,
            )

    def _select_invoice_number(
        self,
        primary: Optional[str],
        fallback: Optional[str],
        record: Optional[InvoiceRecord],
        invoice_payload: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        if primary:
            return primary
        if fallback:
            return fallback
        if record and record.invoice_number:
            return record.invoice_number
        normalized = self._normalize_invoice_payload(invoice_payload or {})
        if isinstance(normalized, dict):
            for key in ("invoiceNumber", "invoice_number", "id", "invoiceId"):
                value = normalized.get(key)
                if value:
                    return str(value)
        return None

    def _select_irn(
        self,
        irn: Optional[str],
        record: Optional[InvoiceRecord],
        invoice_payload: Optional[Dict[str, Any]] = None,
        firs_response: Optional[Dict[str, Any]] = None,
    ) -> Optional[str]:
        if irn:
            return irn
        if record and record.irn:
            return record.irn
        for source in (invoice_payload, firs_response):
            if isinstance(source, dict):
                candidate = source.get("irn") or source.get("IRN")
                if isinstance(candidate, str) and candidate.strip():
                    return candidate.strip()
        return None

    def _serialize_submission(self, submission: FIRSSubmission) -> Dict[str, Any]:
        return {
            "id": str(submission.id),
            "invoiceNumber": submission.invoice_number,
            "invoiceType": submission.invoice_type.value if submission.invoice_type else None,
            "status": submission.status.value,
            "statusDisplay": submission.status.value.replace("_", " ").title(),
            "irn": submission.irn,
            "firsSubmissionId": submission.firs_submission_id,
            "firsStatusCode": submission.firs_status_code,
            "firsMessage": submission.firs_message,
            "totalAmount": float(submission.total_amount) if submission.total_amount is not None else None,
            "currency": submission.currency,
            "retryCount": submission.retry_count,
            "submittedAt": self._iso(submission.submitted_at),
            "acceptedAt": self._iso(submission.accepted_at),
            "rejectedAt": self._iso(submission.rejected_at),
            "createdAt": self._iso(getattr(submission, "created_at", None)),
            "updatedAt": self._iso(getattr(submission, "updated_at", None)),
            "metadata": submission.invoice_data or {},
        }

    def _serialize_batch(self, submission: FIRSSubmission) -> Dict[str, Any]:
        data = self._serialize_submission(submission)
        return {
            "batch_id": data["id"],
            "invoiceNumber": data["invoiceNumber"],
            "status": data["status"],
            "invoiceCount": len(data["metadata"].get("invoices", [])) if isinstance(data["metadata"], dict) else 1,
            "submittedAt": data["submittedAt"],
            "createdAt": data["createdAt"],
        }

    def _build_summary(self, submissions: Iterable[FIRSSubmission]) -> Dict[str, Any]:
        submissions = list(submissions)
        total = len(submissions)
        compliant_set = {SubmissionStatus.ACCEPTED, SubmissionStatus.SUBMITTED}
        non_compliant_set = {SubmissionStatus.REJECTED, SubmissionStatus.FAILED}
        compliant = sum(1 for s in submissions if s.status in compliant_set)
        non_compliant = sum(1 for s in submissions if s.status in non_compliant_set)
        pending = total - compliant - non_compliant
        return {
            "total": total,
            "compliant": compliant,
            "non_compliant": non_compliant,
            "pending": pending,
        }

    def _build_metrics(self, submissions: Iterable[FIRSSubmission]) -> Dict[str, Dict[str, int]]:
        submissions = list(submissions)
        daily: Dict[str, int] = {}
        status_hist: Dict[str, int] = {}
        invoice_hist: Dict[str, int] = {}
        currency_hist: Dict[str, int] = {}
        for sub in submissions:
            created = getattr(sub, "created_at", None)
            if created:
                day = created.date().isoformat()
                daily[day] = daily.get(day, 0) + 1
            status_hist[sub.status.value] = status_hist.get(sub.status.value, 0) + 1
            inv_type = sub.invoice_type.value if sub.invoice_type else "unknown"
            invoice_hist[inv_type] = invoice_hist.get(inv_type, 0) + 1
            currency = (sub.currency or "unknown").upper()
            currency_hist[currency] = currency_hist.get(currency, 0) + 1
        return {
            "daily_counts": daily,
            "status_histogram": status_hist,
            "invoice_type_histogram": invoice_hist,
            "currency_histogram": currency_hist,
        }

    def _extract_retry_config(self, payload: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not isinstance(payload, dict):
            return None
        candidate = (
            payload.get("retry_config")
            or payload.get("retryConfig")
            or payload.get("retryPolicy")
            or payload.get("retry_options")
        )
        return candidate if isinstance(candidate, dict) else None

    async def _ensure_queue_manager(self):
        if self._queue_manager:
            return self._queue_manager

        qm = get_queue_manager()
        try:
            await qm.initialize()
        except Exception as exc:
            self.logger.error("Failed to initialize queue manager: %s", exc)
            raise

        if not self._queue_consumers_registered:
            try:
                await qm.register_consumer(
                    "firs_submissions_high",
                    "app_transmission_worker",
                    self._consume_transmission_message,
                )
                await qm.register_consumer(
                    "firs_submissions_retry",
                    "app_transmission_retry_worker",
                    self._consume_transmission_message,
                )
                self._queue_consumers_registered = True
            except Exception as exc:
                self.logger.error("Failed to register transmission consumers: %s", exc)
                raise

        if not self._status_poll_consumer_registered:
            try:
                await qm.register_consumer(
                    "delayed_tasks",
                    "app_firs_status_poll_worker",
                    self._consume_status_poll,
                )
                self._status_poll_consumer_registered = True
            except Exception as exc:
                self.logger.debug("Status poll consumer registration skipped: %s", exc)

        self._queue_manager = qm
        return qm

    async def _ensure_retry_handler(self) -> RetryHandler:
        if self._retry_handler:
            return self._retry_handler

        handler = RetryHandler(
            secure_transmitter=self._router_transmitter,
            default_retry_policy=self._clone_retry_policy(),
        )
        await handler.start()
        self._retry_handler = handler
        return handler

    async def _queue_transmission_job(
        self,
        *,
        queue_name: str,
        submission_id: Optional[str],
        organization_id: Optional[str],
        request: TransmissionRequest,
        retry_config: Optional[Dict[str, Any]] = None,
        batch_id: Optional[str] = None,
    ) -> Optional[str]:
        try:
            qm = await self._ensure_queue_manager()
        except Exception:
            return None

        payload: Dict[str, Any] = {
            "transmission_request": self._serialize_transmission_request(request),
            "submission_id": submission_id,
            "organization_id": organization_id,
        }
        if batch_id:
            payload["batch_id"] = batch_id
        if retry_config:
            payload["retry_policy"] = retry_config

        try:
            return await qm.enqueue_message(
                queue_name,
                payload,
                metadata={
                    "source_service": "app_transmission",
                    "operation": request.metadata.get("operation"),
                },
            )
        except Exception as exc:
            self.logger.error("Failed to enqueue transmission job: %s", exc)
            return None

    async def _schedule_status_poll(
        self,
        submission: FIRSSubmission,
        organization_id: Optional[str],
        *,
        attempt: int = 1,
        max_attempts: Optional[int] = None,
    ) -> Optional[str]:
        try:
            qm = await self._ensure_queue_manager()
        except Exception:
            return None

        interval_minutes = float(os.getenv("APP_STATUS_POLL_INTERVAL_MINUTES", "15"))
        delay_seconds = max(60, int(interval_minutes * 60))
        max_attempts = max_attempts or int(os.getenv("APP_STATUS_POLL_MAX_ATTEMPTS", "16"))

        scheduled_time = datetime.now(timezone.utc) + timedelta(seconds=delay_seconds)
        payload: Dict[str, Any] = {
            "kind": "firs_status_poll",
            "submission_id": str(submission.id),
            "attempt": attempt,
            "max_attempts": max_attempts,
            "irn": submission.irn,
            "last_status": submission.status.value,
        }
        org_field = organization_id or (str(submission.organization_id) if submission.organization_id else None)
        if org_field:
            payload["organization_id"] = str(org_field)

        return await qm.enqueue_message(
            "delayed_tasks",
            payload,
            scheduled_time=scheduled_time,
        )

    async def _schedule_retry(
        self,
        request: TransmissionRequest,
        result: TransmissionResult,
        retry_config: Optional[Dict[str, Any]],
    ) -> Optional[str]:
        handler = await self._ensure_retry_handler()
        policy = self._build_retry_policy(retry_config or request.metadata.get("retry_config"))
        retry_id = await handler.handle_failed_transmission(
            transmission_request=request,
            transmission_result=result,
            retry_policy=policy,
        )
        return retry_id or None

    async def _persist_transmission_outcome(
        self,
        *,
        request: TransmissionRequest,
        result: TransmissionResult,
        submission_id: Optional[str],
        organization_id: Optional[str],
    ) -> Optional[FIRSSubmission]:
        firs_response: Dict[str, Any] = {
            "success": result.status == TransmissionStatus.DELIVERED,
            "data": result.response_data or {},
        }
        if result.error_message:
            firs_response["error"] = result.error_message

        status_hint = "accepted" if firs_response["success"] else "failed"

        persisted: Optional[FIRSSubmission] = None
        async with self._session_scope() as session:
            tenant_id = None
            org_uuid = self._ensure_uuid(organization_id)
            if org_uuid is not None:
                tenant_id = str(org_uuid)
            elif isinstance(organization_id, str):
                tenant_id = organization_id

            with tenant_context(tenant_id) if tenant_id else nullcontext():
                persisted = await self._persist_submission(
                    session,
                    organization_id,
                    request.document_data,
                    firs_response,
                    status_hint=status_hint,
                    request_id=request.metadata.get("request_id"),
                )

        if submission_id and organization_id:
            try:
                await self._update_submission_status(
                    submission_id,
                    organization_id,
                    SubmissionStatus.ACCEPTED if firs_response["success"] else SubmissionStatus.FAILED,
                    message=result.error_message,
                    invoice_number=request.metadata.get("invoice_number"),
                )
            except Exception as exc:
                self.logger.debug("Unable to update submission status for %s: %s", submission_id, exc)

        if persisted and persisted.status in self._BATCH_STATUSES:
            try:
                org_identifier = organization_id or (
                    str(persisted.organization_id) if persisted.organization_id else None
                )
                await self._schedule_status_poll(
                    persisted,
                    organization_id=org_identifier,
                )
            except Exception as exc:
                self.logger.debug("Status poll scheduling skipped for %s: %s", persisted.id, exc)

        return persisted

    async def _persist_submission(
        self,
        session,
        organization_id: Optional[str],
        invoice_data: Optional[Dict[str, Any]],
        firs_response: Dict[str, Any],
        status_hint: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> Optional[FIRSSubmission]:
        org_uuid = self._ensure_uuid(organization_id)
        if org_uuid is None:
            return None

        invoice_data = invoice_data or {}
        if not isinstance(invoice_data, dict):
            invoice_data = {}
        invoice_number = (
            invoice_data.get("invoiceNumber")
            or invoice_data.get("invoice_number")
            or self._make_identifier("INV")
        )
        total_amount = self._parse_decimal(
            invoice_data.get("totalAmount") or invoice_data.get("total_amount")
        )
        currency = (
            invoice_data.get("currency")
            or invoice_data.get("currency_code")
            or invoice_data.get("documentMetadata", {}).get("currencyCode")
            or "NGN"
        ).upper()
        invoice_type_value = invoice_data.get("invoiceType") or invoice_data.get("invoice_type")
        invoice_type_enum = None
        if invoice_type_value:
            try:
                invoice_type_enum = InvoiceType(invoice_type_value)
            except Exception:
                invoice_type_enum = None

        response_data = firs_response.get("data") if isinstance(firs_response, dict) else {}
        normalized_response = dict(response_data) if isinstance(response_data, dict) else {}
        identifiers = normalized_response.get("identifiers")
        if isinstance(identifiers, dict):
            for key, target_key in (
                ("irn", "irn"),
                ("csid", "csid"),
                ("csid_hash", "csidHash"),
                ("csidHash", "csidHash"),
                ("qr", "qr"),
                ("qr_code", "qr"),
                ("qrCode", "qr"),
                ("stampMetadata", "stampMetadata"),
                ("cryptographic_stamp", "stampMetadata"),
            ):
                if key in identifiers and target_key not in normalized_response:
                    normalized_response[target_key] = identifiers[key]

        response_status = normalized_response.get("status") if isinstance(normalized_response, dict) else None
        status_enum = self._map_status(status_hint or response_status, firs_response.get("success"))

        async with session.begin():
            existing_stmt = select(FIRSSubmission).where(
                FIRSSubmission.organization_id == org_uuid,
                FIRSSubmission.invoice_number == invoice_number,
            ).limit(1)
            existing = (await session.execute(existing_stmt)).scalars().first()
            if existing:
                target = existing
            else:
                target = FIRSSubmission(
                    organization_id=org_uuid,
                    invoice_number=invoice_number,
                    invoice_type=invoice_type_enum or InvoiceType.STANDARD_INVOICE,
                )
                session.add(target)

            target.status = status_enum
            target.invoice_type = invoice_type_enum or target.invoice_type
            target.invoice_data = invoice_data
            target.total_amount = total_amount
            target.currency = currency
            target.firs_response = normalized_response  # type: ignore[assignment]
            target.firs_submission_id = (
                normalized_response.get("submission_id")
                or normalized_response.get("submissionId")
                or target.firs_submission_id
            )
            target.firs_status_code = normalized_response.get("statusCode") or normalized_response.get("status_code")
            target.firs_message = normalized_response.get("message") or firs_response.get("error")
            irn_value = self._select_irn(
                target.irn,
                None,
                invoice_payload=invoice_data,
                firs_response=normalized_response,
            )
            if irn_value:
                target.irn = irn_value
            csid_value = normalized_response.get("csid") or normalized_response.get("csid_code")
            if csid_value:
                target.csid = csid_value
            csid_hash_value = normalized_response.get("csidHash") or normalized_response.get("csid_hash")
            if csid_hash_value:
                target.csid_hash = csid_hash_value
            qr_value = (
                normalized_response.get("qr")
                or normalized_response.get("qr_code")
                or normalized_response.get("qrCode")
                or normalized_response.get("qr_payload")
            )
            if qr_value:
                target.qr_payload = qr_value
            stamp_metadata = normalized_response.get("stampMetadata") or normalized_response.get("cryptographic_stamp")
            if stamp_metadata:
                target.firs_stamp_metadata = stamp_metadata
            now = datetime.now(timezone.utc)
            target.submitted_at = target.submitted_at or now
            if status_enum == SubmissionStatus.ACCEPTED:
                target.accepted_at = now
            if status_enum in {SubmissionStatus.REJECTED, SubmissionStatus.FAILED, SubmissionStatus.CANCELLED}:
                target.rejected_at = now
            if request_id:
                target.request_id = request_id

        await session.refresh(target)
        return target

    async def _update_submission_status(
        self,
        submission_id: Optional[str],
        organization_id: Optional[str],
        new_status: SubmissionStatus,
        message: Optional[str] = None,
        *,
        invoice_number: Optional[str] = None,
    ) -> Optional[FIRSSubmission]:
        async with self._session_scope() as session:
            org_uuid = self._ensure_uuid(organization_id)
            tenant_id = str(org_uuid) if org_uuid else (
                organization_id if isinstance(organization_id, str) else None
            )

            with tenant_context(tenant_id) if tenant_id else nullcontext():
                submission: Optional[FIRSSubmission] = None

                sub_uuid = self._ensure_uuid(submission_id)
                if sub_uuid is not None:
                    submission = await firs_repo.get_submission_by_id(
                        session,
                        submission_id=sub_uuid,
                        organization_id=org_uuid,
                    )

                if submission is None and invoice_number:
                    submission = await self._get_submission_by_invoice(
                        session,
                        invoice_number=invoice_number,
                        organization_id=org_uuid,
                    )

                if submission is None:
                    return None

                async with session.begin():
                    submission.status = new_status
                    if new_status == SubmissionStatus.CANCELLED:
                        submission.rejected_at = datetime.now(timezone.utc)
                    if message:
                        submission.firs_message = message

                await session.refresh(submission)
                return submission

    async def _get_submission_by_invoice(
        self,
        session,
        *,
        invoice_number: str,
        organization_id: Optional[UUID],
    ) -> Optional[FIRSSubmission]:
        if not invoice_number:
            return None

        stmt = select(FIRSSubmission).where(
            FIRSSubmission.invoice_number == str(invoice_number)
        ).limit(1)

        if organization_id is not None:
            stmt = stmt.where(FIRSSubmission.organization_id == organization_id)

        result = await session.execute(stmt)
        return result.scalars().first()

    async def _list_submissions(
        self,
        payload: Dict[str, Any],
        *,
        status: Optional[str] = None,
        limit: int = 50,
        page: int = 1,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> List[FIRSSubmission]:
        organization_id = self._resolve_org_id(payload)

        filters = payload.get("filters") if isinstance(payload.get("filters"), dict) else {}

        status_value = status or filters.get("status") or filters.get("submissionStatus")
        status_filter = status_value.upper() if isinstance(status_value, str) else status_value

        start_date = (
            start_date
            or filters.get("start_date")
            or filters.get("startDate")
            or filters.get("from")
        )
        end_date = (
            end_date
            or filters.get("end_date")
            or filters.get("endDate")
            or filters.get("to")
        )

        async with self._session_scope() as session:
            with tenant_context(organization_id) if organization_id else nullcontext():
                rows = await firs_repo.list_submissions_filtered(
                    session,
                    organization_id=organization_id,
                    status=status_filter,
                    start_date=start_date,
                    end_date=end_date,
                    limit=limit * max(page, 1),
                )
        offset = max(page - 1, 0) * limit
        return rows[offset : offset + limit]

    # ------------------------------------------------------------------
    # Operation handlers
    # ------------------------------------------------------------------

    async def _handle_get_available_batches(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        limit = int(payload.get("limit", 20))
        submissions = await self._list_submissions(payload, limit=limit)
        batches = [s for s in submissions if s.status in self._BATCH_STATUSES]
        return {
            "batches": [self._serialize_batch(s) for s in batches],
            "total": len(batches),
            "generated_at": self._now_iso(),
        }

    async def _handle_list_transmission_batches(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        limit = int(payload.get("limit", 50))
        filters = payload.get("filters") if isinstance(payload.get("filters"), dict) else {}
        status = payload.get("status") or filters.get("status")
        submissions = await self._list_submissions(payload, status=status, limit=limit)
        return {
            "batches": [self._serialize_batch(s) for s in submissions],
            "meta": {
                "limit": limit,
                "count": len(submissions),
                "generated_at": self._now_iso(),
            },
        }

    async def _handle_get_batch_details(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        batch_id = payload.get("batch_id") or payload.get("transmission_id")
        organization_id = self._resolve_org_id(payload)
        async with self._session_scope() as session:
            with tenant_context(organization_id) if organization_id else nullcontext():
                submission = await firs_repo.get_submission_by_id(
                    session, submission_id=batch_id, organization_id=organization_id
                )
        if not submission:
            return {"batch_id": batch_id, "found": False, "checked_at": self._now_iso()}
        return {
            "batch_id": batch_id,
            "details": self._serialize_submission(submission),
            "checked_at": self._now_iso(),
        }

    async def _handle_submit_invoice_batches(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        batch_submission = payload.get("batch_submission_data")
        invoices = payload.get("invoices") or payload.get("batch_data") or []

        if isinstance(batch_submission, dict):
            invoices = batch_submission.get("invoices") or batch_submission.get("items") or invoices

        if isinstance(invoices, dict) and "invoices" in invoices:
            invoices = invoices["invoices"]

        if not isinstance(invoices, list):
            invoices = [invoices] if invoices else []

        organization_id = self._resolve_org_id(payload) or self._resolve_org_id(batch_submission or {})

        resolved_invoices: List[Dict[str, Any]] = []
        references: List[Dict[str, Any]] = []

        for entry in invoices:
            if self._looks_like_invoice_payload(entry):
                normalized = self._normalize_invoice_payload(entry) or {}
                resolved_invoices.append(dict(normalized))
            else:
                ref_dict: Dict[str, Any]
                if isinstance(entry, dict):
                    ref_dict = dict(entry)
                elif isinstance(entry, str):
                    ref_dict = {"invoice_number": entry}
                else:
                    ref_dict = {}
                references.append(ref_dict)

        if references:
            async with self._session_scope() as session:
                for ref in references:
                    invoice_number = self._select_invoice_number(
                        ref.get("invoice_number")
                        or ref.get("invoiceNumber")
                        or ref.get("invoice_id")
                        or ref.get("invoiceId"),
                        None,
                        None,
                        ref,
                    )
                    record = await invoice_repo.get_invoice_record(
                        session,
                        organization_id=organization_id,
                        invoice_number=invoice_number,
                        submission_id=ref.get("submission_id") or ref.get("transmission_id"),
                        irn=ref.get("irn"),
                        correlation_id=ref.get("correlation_id"),
                        si_invoice_id=ref.get("si_invoice_id"),
                    )
                    if not record or not record.invoice_data:
                        identifier = invoice_number or ref.get("submission_id") or ref.get("irn") or "invoice_reference_missing"
                        raise ValueError(f"invoice_payload_unavailable:{identifier}")
                    invoice_payload = dict(record.invoice_data)
                    if record.irn and "irn" not in invoice_payload:
                        invoice_payload.setdefault("irn", record.irn)
                    resolved_invoices.append(invoice_payload)

        if not resolved_invoices:
            raise ValueError("invoice_payload_unavailable")

        request_id = payload.get("request_id")
        batch_options = None
        if isinstance(payload.get("options"), dict):
            batch_options = dict(payload["options"])
        elif isinstance(batch_submission, dict) and isinstance(batch_submission.get("options"), dict):
            batch_options = dict(batch_submission["options"])

        prepared_invoices: List[Dict[str, Any]] = []
        pipeline_reports: List[Dict[str, Any]] = []
        pipeline_warnings: List[str] = []

        for invoice_entry in resolved_invoices:
            invoice_number_hint = self._select_invoice_number(None, None, None, invoice_entry)
            prepared_invoice, meta, warnings = await self._prepare_invoice_for_submission(
                invoice_entry,
                organization_id=organization_id,
                invoice_number=invoice_number_hint,
                options=batch_options,
            )
            prepared_invoices.append(prepared_invoice)
            pipeline_reports.append(meta)
            pipeline_warnings.extend(warnings)

        resolved_invoices = prepared_invoices

        firs_payload: Dict[str, Any] = {
            "invoices": resolved_invoices,
            "organization_id": organization_id,
        }
        if isinstance(batch_submission, dict):
            firs_payload["metadata"] = batch_submission

        firs_response = await self._call_firs("submit_invoice_batch_to_firs", firs_payload)

        persisted_ids: List[str] = []
        persisted_submissions: List[FIRSSubmission] = []
        async with self._session_scope() as session:
            with tenant_context(organization_id) if organization_id else nullcontext():
                for invoice in resolved_invoices:
                    submission = await self._persist_submission(
                        session,
                        organization_id,
                        invoice,
                        firs_response,
                        status_hint="submitted",
                        request_id=request_id,
                    )
                    if submission:
                        persisted_ids.append(str(submission.id))
                        persisted_submissions.append(submission)

        try:
            delivery = payload.get("delivery") or {}
            await self._enqueue_outbound_delivery(organization_id, resolved_invoices, delivery)
        except Exception:
            self.logger.debug("Outbound delivery enqueue skipped")

        submission_batch_id = (
            payload.get("batch_id")
            or payload.get("batchId")
            or (batch_submission or {}).get("batch_id")
            or (batch_submission or {}).get("batchId")
        )

        if not firs_response.get("success"):
            retry_config = self._extract_retry_config(payload) or self._extract_retry_config(batch_submission)
            for index, invoice in enumerate(resolved_invoices):
                submission_ref = persisted_ids[index] if index < len(persisted_ids) else None
                document_id = (
                    invoice.get("invoiceNumber")
                    or invoice.get("invoice_number")
                    or submission_ref
                    or self._make_identifier("INV")
                )
                request = self._create_transmission_request(
                    document_id=document_id,
                    document_data=invoice,
                    organization_id=organization_id,
                    operation="submit_invoice_to_firs",
                    metadata={
                        "submission_id": submission_ref,
                        "batch_id": submission_batch_id,
                        "request_id": request_id,
                        "retry_config": retry_config,
                    },
                )
                await self._queue_transmission_job(
                    queue_name="firs_submissions_high",
                    submission_id=submission_ref,
                    organization_id=organization_id,
                    request=request,
                    retry_config=retry_config,
                    batch_id=submission_batch_id,
                )

        response_payload = {
            "submitted_at": self._now_iso(),
            "firs_response": firs_response,
            "persisted_submissions": persisted_ids,
        }
        if pipeline_reports:
            response_payload["pipeline_reports"] = pipeline_reports
        if pipeline_warnings:
            response_payload["pipeline_warnings"] = pipeline_warnings

        for submission in persisted_submissions:
            if submission.status in self._BATCH_STATUSES:
                try:
                    org_identifier = organization_id or (
                        str(submission.organization_id) if submission.organization_id else None
                    )
                    await self._schedule_status_poll(
                        submission,
                        organization_id=org_identifier,
                    )
                except Exception:
                    self.logger.debug("Status poll scheduling skipped for %s", submission.id)

        return response_payload

    async def _handle_submit_invoice_file(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "status": "processing",
            "transmission_id": self._make_identifier("TX"),
            "file_name": payload.get("file_name"),
            "received_at": self._now_iso(),
        }

    async def _handle_submit_single_batch(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        normalized_payload = dict(payload)
        submission_config = normalized_payload.get("submission_config") or {}
        if "batch_submission_data" not in normalized_payload:
            normalized_payload["batch_submission_data"] = submission_config
        if "invoices" not in normalized_payload and isinstance(submission_config, dict):
            normalized_payload["invoices"] = submission_config.get("invoices") or submission_config.get("items")
        return await self._handle_submit_invoice_batches(normalized_payload)

    async def _handle_generate_invoice(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        generation_data = payload.get("generation_data", {})
        invoice_data = generation_data.get("invoice_data", {})
        invoice_id = invoice_data.get("invoiceNumber") or self._make_identifier("INV")
        return {
            "invoice_id": invoice_id,
            "validated": True,
            "generated_at": self._now_iso(),
            "source": generation_data.get("source", "app"),
        }

    async def _handle_generate_invoice_batch(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        batch_data = payload.get("batch_generation_data", {})
        invoices = batch_data.get("invoices", [])
        return {
            "batch_id": self._make_identifier("BATCH"),
            "invoice_count": len(invoices),
            "created_at": self._now_iso(),
            "metadata": {
                "priority": batch_data.get("priority", "normal"),
                "auto_validate": batch_data.get("auto_validate", True),
            },
        }

    async def _handle_submit_invoice(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raw_submission = payload.get("submission_data")
        submission_data = raw_submission if isinstance(raw_submission, dict) else {}

        pipeline_started_at = datetime.now(timezone.utc)
        last_stage_at = pipeline_started_at
        event_index = 0

        correlation_id_ref = payload.get("correlation_id") or submission_data.get("correlation_id")
        si_invoice_ref = payload.get("si_invoice_id") or submission_data.get("si_invoice_id")

        invoice_payload = self._normalize_invoice_payload(payload.get("invoice_data"))
        organization_id = self._resolve_org_id(payload) or self._resolve_org_id(submission_data)
        invoice_number_primary = self._resolve_invoice_number(payload)
        invoice_number_fallback = self._resolve_invoice_number(submission_data)
        submission_identifier = (
            payload.get("submission_id")
            or payload.get("transmission_id")
            or submission_data.get("submission_id")
            or submission_data.get("transmission_id")
        )
        irn_candidate = payload.get("irn") or submission_data.get("irn")

        request_id = payload.get("request_id") or submission_data.get("request_id")

        record = None
        if not self._looks_like_invoice_payload(invoice_payload):
            record = await self._fetch_invoice_record(
                organization_id=organization_id,
                invoice_number=invoice_number_primary or invoice_number_fallback,
                submission_id=submission_identifier,
                irn=irn_candidate,
                correlation_id=payload.get("correlation_id") or submission_data.get("correlation_id"),
                si_invoice_id=payload.get("si_invoice_id") or submission_data.get("si_invoice_id"),
            )
            invoice_payload = self._combine_invoice_payload(invoice_payload, record)

        if not invoice_payload:
            raise ValueError("invoice_payload_unavailable")

        invoice_number = self._select_invoice_number(
            invoice_number_primary,
            invoice_number_fallback,
            record,
            invoice_payload,
        )
        irn_value = self._select_irn(irn_candidate, record, invoice_payload=invoice_payload)
        if irn_value and "irn" not in invoice_payload:
            invoice_payload = dict(invoice_payload)
            invoice_payload.setdefault("irn", irn_value)

        correlation_submission_ref = (
            submission_identifier
            or request_id
            or invoice_number
            or invoice_number_primary
            or invoice_number_fallback
            or irn_value
        )

        if irn_value:
            received_metadata_extra = {
                "invoice_number": invoice_number,
                "pipeline_event_index": event_index,
                "request_id": request_id,
            }
            received_metadata, last_stage_at = self._build_correlation_metadata(
                stage="APP_RECEIVED",
                pipeline_started_at=pipeline_started_at,
                previous_stage_at=last_stage_at,
                submission_id=correlation_submission_ref,
                correlation_id=correlation_id_ref,
                organization_id=organization_id,
                si_invoice_id=si_invoice_ref,
                extra=received_metadata_extra,
            )
            await self._emit_correlation_event(
                "update_app_received",
                irn=irn_value,
                app_submission_id=correlation_submission_ref,
                metadata=received_metadata,
            )
            event_index += 1
            await self._record_sla_telemetry(received_metadata, "APP_RECEIVED")

        options = None
        if isinstance(payload.get("options"), dict):
            options = dict(payload["options"])
        elif isinstance(submission_data.get("options"), dict):
            options = dict(submission_data["options"])

        prepared_invoice, pipeline_metadata, pipeline_warnings = await self._prepare_invoice_for_submission(
            invoice_payload or {},
            organization_id=organization_id,
            invoice_number=invoice_number,
            options=options,
        )
        invoice_payload = prepared_invoice

        firs_payload = {
            "invoice_data": invoice_payload,
            "invoice_number": invoice_number,
            "organization_id": organization_id,
        }
        if irn_value:
            firs_payload["irn"] = irn_value

        if irn_value:
            submitting_extra = {
                "invoice_number": invoice_number,
                "pipeline_event_index": event_index,
                "request_id": request_id,
                "options_applied": bool(options),
            }
            submitting_metadata, last_stage_at = self._build_correlation_metadata(
                stage="APP_SUBMITTING",
                pipeline_started_at=pipeline_started_at,
                previous_stage_at=last_stage_at,
                submission_id=correlation_submission_ref,
                correlation_id=correlation_id_ref,
                organization_id=organization_id,
                si_invoice_id=si_invoice_ref,
                extra=submitting_extra,
            )
            await self._emit_correlation_event(
                "update_app_submitting",
                irn=irn_value,
                metadata=submitting_metadata,
            )
            event_index += 1
            await self._record_sla_telemetry(submitting_metadata, "APP_SUBMITTING")

        firs_response = await self._call_firs("submit_invoice_to_firs", firs_payload)
        firs_response_data = (
            firs_response.get("data") if isinstance(firs_response, dict) else {}
        )
        firs_response_payload = (
            dict(firs_response_data) if isinstance(firs_response_data, dict) else {}
        )
        firs_status = (
            (firs_response.get("status") if isinstance(firs_response, dict) else None)
            or firs_response_payload.get("status")
            or firs_response_payload.get("documentStatus")
            or firs_response_payload.get("document_status")
            or "submitted"
        )
        firs_response_id = (
            firs_response_payload.get("submission_id")
            or firs_response_payload.get("submissionId")
            or firs_response_payload.get("id")
        )
        firs_identifiers = (
            firs_response.get("identifiers") if isinstance(firs_response, dict) else None
        )
        if not firs_identifiers and isinstance(firs_response_payload, dict):
            firs_identifiers = extract_firs_identifiers(firs_response_payload) or None
        if firs_identifiers:
            firs_response_payload = merge_identifiers_into_payload(
                dict(firs_response_payload),
                firs_identifiers,
            )
            if isinstance(firs_response, dict):
                firs_response = dict(firs_response)
                firs_response["identifiers"] = firs_identifiers

        submission = None
        async with self._session_scope() as session:
            with tenant_context(organization_id) if organization_id else nullcontext():
                submission = await self._persist_submission(
                    session,
                    organization_id,
                    invoice_payload,
                    firs_response,
                    status_hint="submitted",
                    request_id=request_id,
                )

        submission_ref = (
            str(submission.id)
            if submission and getattr(submission, "id", None) is not None
            else correlation_submission_ref
        )
        correlation_submission_ref = submission_ref or correlation_submission_ref

        if irn_value:
            submission_state = getattr(submission, "status", None)
            if submission_state and hasattr(submission_state, "value"):
                submission_state_value = str(submission_state.value)
            elif submission_state is not None:
                submission_state_value = str(submission_state)
            else:
                submission_state_value = None

            submitted_extra = {
                "invoice_number": invoice_number,
                "pipeline_event_index": event_index,
                "request_id": request_id,
                "submission_status": submission_state_value,
                "firs_status": firs_status,
                "submission_id": submission_ref,
            }
            submitted_metadata, last_stage_at = self._build_correlation_metadata(
                stage="APP_SUBMITTED",
                pipeline_started_at=pipeline_started_at,
                previous_stage_at=last_stage_at,
                submission_id=submission_ref,
                correlation_id=correlation_id_ref,
                organization_id=organization_id,
                si_invoice_id=si_invoice_ref,
                extra=submitted_extra,
            )
            await self._emit_correlation_event(
                "update_app_submitted",
                irn=irn_value,
                metadata=submitted_metadata,
            )
            event_index += 1
            await self._record_sla_telemetry(submitted_metadata, "APP_SUBMITTED")

        if irn_value:
            response_extra = {
                "invoice_number": invoice_number,
                "pipeline_event_index": event_index,
                "request_id": request_id,
                "firs_status": firs_status,
                "firs_success": bool(firs_response.get("success"))
                if isinstance(firs_response, dict)
                else None,
                "submission_id": submission_ref,
            }
            response_metadata, last_stage_at = self._build_correlation_metadata(
                stage="FIRS_RESPONSE",
                pipeline_started_at=pipeline_started_at,
                previous_stage_at=last_stage_at,
                submission_id=submission_ref,
                correlation_id=correlation_id_ref,
                organization_id=organization_id,
                si_invoice_id=si_invoice_ref,
                extra=response_extra,
            )
            correlation_response_payload = dict(firs_response_payload)
            correlation_response_payload["correlation_metadata"] = response_metadata
            await self._emit_correlation_event(
                "update_firs_response",
                irn=irn_value,
                metadata=response_metadata,
                firs_response_id=str(firs_response_id) if firs_response_id else None,
                firs_status=str(firs_status) if firs_status else None,
                response_data=correlation_response_payload,
                identifiers=firs_identifiers,
            )
            event_index += 1
            await self._record_sla_telemetry(response_metadata, "FIRS_RESPONSE")

        try:
            delivery = payload.get("delivery") or submission_data.get("delivery") or {}
            await self._enqueue_outbound_delivery(organization_id, [invoice_payload], delivery)
        except Exception:
            self.logger.debug("Outbound delivery enqueue skipped")

        if not firs_response.get("success"):
            retry_config = self._extract_retry_config(payload) or self._extract_retry_config(submission_data)
            submission_ref_retry = submission_ref
            document_id = (
                invoice_number
                or invoice_number_primary
                or invoice_number_fallback
                or submission_ref_retry
                or self._make_identifier("INV")
            )
            request = self._create_transmission_request(
                document_id=document_id,
                document_data=invoice_payload,
                organization_id=organization_id,
                operation="submit_invoice_to_firs",
                metadata={
                    "submission_id": submission_ref_retry,
                    "request_id": request_id,
                    "retry_config": retry_config,
                    "payload": {
                        "irn": irn_value,
                        "invoice_number": invoice_number,
                        "organization_id": organization_id,
                    },
                },
            )
            await self._queue_transmission_job(
                queue_name="firs_submissions_high",
                submission_id=submission_ref,
                organization_id=organization_id,
                request=request,
                retry_config=retry_config,
            )

        response_payload = {
            "submission_id": str(submission.id) if submission else self._make_identifier("SUB"),
            "submitted_at": self._now_iso(),
            "firs_response": firs_response,
            "submission": self._serialize_submission(submission) if submission else None,
        }
        if pipeline_metadata.get("validation_report"):
            response_payload["validation_report"] = pipeline_metadata["validation_report"]
        if pipeline_metadata.get("signature"):
            response_payload["signature"] = pipeline_metadata["signature"]
        if pipeline_warnings:
            response_payload["pipeline_warnings"] = pipeline_warnings

        if submission and submission.status in self._BATCH_STATUSES:
            try:
                org_identifier = organization_id or (
                    str(submission.organization_id) if submission.organization_id else None
                )
                await self._schedule_status_poll(
                    submission,
                    organization_id=org_identifier,
                )
            except Exception:
                self.logger.debug("Status poll scheduling skipped for %s", submission.id)

        return response_payload

    async def _enqueue_outbound_delivery(
        self,
        organization_id: Optional[str],
        invoices: List[Dict[str, Any]],
        delivery: Dict[str, Any],
    ) -> None:
        """Enqueue outbound delivery messages when buyer AP delivery is requested.

        Expects optional delivery config with keys like:
          - participant_identifier (buyer)
          - endpoint_url (direct override)
          - headers/meta (optional)
        """
        if not isinstance(delivery, dict) or not invoices:
            return

        # Allow disabling auto delivery via env or flag
        import os
        auto_enabled = str(os.getenv("OUTBOUND_AUTO_DELIVER", "true")).lower() in ("1", "true", "yes", "on")

        participant_identifier = delivery.get("participant_identifier") or delivery.get("identifier")
        endpoint_url = delivery.get("endpoint_url") or delivery.get("ap_endpoint_url")
        if not participant_identifier and not endpoint_url and not auto_enabled:
            return

        qm = get_queue_manager()
        await qm.initialize()

        participant_cache: Dict[str, Optional[str]] = {}

        async def resolve_endpoint(identifier_value: str) -> Optional[str]:
            if identifier_value in participant_cache:
                return participant_cache[identifier_value]
            async with self._session_scope() as session:
                participant = await participant_repo.get_participant_by_identifier(session, identifier_value)
                if participant and participant.status == ParticipantStatus.ACTIVE:
                    endpoint = participant.ap_endpoint_url
                else:
                    endpoint = None
            participant_cache[identifier_value] = endpoint
            return endpoint

        # Prepare one message per invoice to keep retries independent
        for inv in invoices:
            identifier = participant_identifier or (self._extract_buyer_identifier(inv) if auto_enabled else None)
            resolved_endpoint = endpoint_url
            if not resolved_endpoint and identifier:
                resolved_endpoint = await resolve_endpoint(identifier)
            if not resolved_endpoint and not identifier:
                continue

            payload = {
                "organization_id": organization_id,
                "identifier": identifier,
                "endpoint_url": resolved_endpoint,
                "document": inv,
                "metadata": delivery.get("metadata") or {},
            }
            await qm.enqueue_message(
                "ap_outbound",
                payload,
                metadata={"source_service": "store_and_forward", "participant_identifier": identifier or ""},
            )

    def _extract_buyer_identifier(self, invoice: Dict[str, Any]) -> Optional[str]:
        """Best-effort extraction of buyer participant identifier (e.g., TIN) from invoice payload.

        Tries common keys in both our normalized and UBL-like structures.
        """
        if not isinstance(invoice, dict):
            return None
        # Common shapes
        for path in (
            ("customer", "tax_id"),
            ("customer", "tin"),
            ("buyer", "tax_id"),
            ("buyer", "tin"),
            ("buyer", "party_tax_id"),
        ):
            cur = invoice
            for key in path:
                if not isinstance(cur, dict) or key not in cur:
                    cur = None
                    break
                cur = cur.get(key)
            if isinstance(cur, str) and cur.strip():
                return cur.strip()
        # UBL-like: accounting_customer_party.party.party_tax_scheme.company_id
        try:
            acp = invoice.get("accounting_customer_party") or {}
            party = acp.get("party") or {}
            tax_scheme = party.get("party_tax_scheme") or {}
            cid = tax_scheme.get("company_id")
            if isinstance(cid, str) and cid.strip():
                return cid.strip()
        except Exception:
            pass
        # Other camelCase variants
        for key in ("customerTaxId", "customerTIN", "buyerTaxId", "buyerTIN"):
            val = invoice.get(key)
            if isinstance(val, str) and val.strip():
                return val.strip()
        return None

    async def _handle_get_submission_status(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        submission_id = payload.get("submission_id") or payload.get("transmission_id")
        invoice_identifier = (
            payload.get("invoice_id")
            or payload.get("invoiceNumber")
            or payload.get("irn")
        )
        organization_id = self._resolve_org_id(payload)
        db_submission = None
        async with self._session_scope() as session:
            org_uuid = self._ensure_uuid(organization_id)
            tenant_id = str(org_uuid) if org_uuid else (
                organization_id if isinstance(organization_id, str) else None
            )
            with tenant_context(tenant_id) if tenant_id else nullcontext():
                sub_uuid = self._ensure_uuid(submission_id)
                if sub_uuid is not None:
                    db_submission = await firs_repo.get_submission_by_id(
                        session,
                        submission_id=sub_uuid,
                        organization_id=org_uuid,
                    )
                if db_submission is None and invoice_identifier:
                    db_submission = await self._get_submission_by_invoice(
                        session,
                        invoice_number=invoice_identifier,
                        organization_id=org_uuid,
                    )
                if db_submission is None and payload.get("irn"):
                    stmt = select(FIRSSubmission).where(
                        FIRSSubmission.irn == payload["irn"]
                    ).limit(1)
                    db_submission = (await session.execute(stmt)).scalars().first()
        if db_submission:
            return {
                "submission_id": str(db_submission.id),
                "status": db_submission.status.value,
                "details": self._serialize_submission(db_submission),
                "checked_at": self._now_iso(),
            }
        firs_response = await self._call_firs(
            "get_firs_submission_status",
            {"submission_id": submission_id, "irn": payload.get("irn")},
        )
        return {
            "submission_id": submission_id,
            "status_checked_at": self._now_iso(),
            "firs_response": firs_response,
        }

    async def _handle_list_submissions(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        pagination = payload.get("pagination") if isinstance(payload.get("pagination"), dict) else {}

        raw_limit = payload.get("limit") or pagination.get("limit")
        limit = int(raw_limit or 50)

        raw_page = payload.get("page") or pagination.get("page")
        if raw_page is None and payload.get("offset") is not None:
            try:
                offset_val = int(payload.get("offset", 0))
            except (TypeError, ValueError):
                offset_val = 0
            page = (max(offset_val, 0) // max(limit, 1)) + 1
        else:
            page = int(raw_page or 1)

        submissions = await self._list_submissions(payload, limit=limit, page=page)
        return {
            "items": [self._serialize_submission(s) for s in submissions],
            "count": len(submissions),
            "page": page,
            "limit": limit,
            "generated_at": self._now_iso(),
        }

    async def _handle_cancel_submission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        submission_id = (
            payload.get("submission_id")
            or payload.get("transmission_id")
            or payload.get("invoice_id")
        )
        organization_id = self._resolve_org_id(payload)
        invoice_number = self._resolve_invoice_number(payload, fallback=submission_id)
        reason = payload.get("reason") or payload.get("cancellation_reason")

        firs_response = None
        if submission_id or invoice_number:
            firs_response = await self._call_firs(
                "update_firs_submission_status",
                {
                    "submission_id": submission_id,
                    "invoice_number": invoice_number,
                    "status": "cancelled",
                    "reason": reason,
                },
            )

        updated = await self._update_submission_status(
            submission_id,
            organization_id,
            SubmissionStatus.CANCELLED,
            reason,
            invoice_number=invoice_number,
        )
        return {
            "submission_id": submission_id,
            "cancelled_at": self._now_iso(),
            "submission": self._serialize_submission(updated) if updated else None,
            "firs_response": firs_response,
        }

    async def _handle_resubmit_invoice(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raw_resubmission = payload.get("resubmission_data")
        resubmission_data = raw_resubmission if isinstance(raw_resubmission, dict) else {}

        submission_id = (
            payload.get("submission_id")
            or payload.get("transmission_id")
            or payload.get("invoice_id")
            or resubmission_data.get("submission_id")
        )
        invoice_number = self._resolve_invoice_number(resubmission_data, fallback=self._resolve_invoice_number(payload))
        organization_id = self._resolve_org_id(payload) or self._resolve_org_id(resubmission_data)

        invoice_payload = self._normalize_invoice_payload(resubmission_data.get("invoice_data"))
        irn_value = payload.get("irn") or resubmission_data.get("irn")

        record = None
        if not self._looks_like_invoice_payload(invoice_payload) or not irn_value:
            record = await self._fetch_invoice_record(
                organization_id=organization_id,
                invoice_number=invoice_number,
                submission_id=submission_id,
                irn=irn_value,
                correlation_id=payload.get("correlation_id") or resubmission_data.get("correlation_id"),
                si_invoice_id=payload.get("si_invoice_id") or resubmission_data.get("si_invoice_id"),
            )
            invoice_payload = self._combine_invoice_payload(invoice_payload, record)
            irn_value = self._select_irn(irn_value, record, invoice_payload=invoice_payload)

        if not irn_value:
            raise ValueError("irn_required_for_resubmission")

        invoice_payload = dict(invoice_payload) if isinstance(invoice_payload, dict) else {}

        firs_payload = {
            "irn": irn_value,
            "invoice_data": invoice_payload,
            "organization_id": organization_id,
            "options": resubmission_data.get("options") if isinstance(resubmission_data, dict) else None,
        }

        firs_response = await self._call_firs("transmit_firs_invoice", firs_payload)

        updated = await self._update_submission_status(
            submission_id,
            organization_id,
            SubmissionStatus.PROCESSING,
            firs_response.get("error"),
            invoice_number=invoice_number or submission_id,
        )
        return {
            "submission_id": submission_id,
            "resubmitted_at": self._now_iso(),
            "firs_response": firs_response,
            "submission": self._serialize_submission(updated) if updated else None,
        }

    async def _handle_retry_transmission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        submission_id = (
            payload.get("submission_id")
            or payload.get("transmission_id")
            or payload.get("invoice_id")
        )
        invoice_number = self._resolve_invoice_number(payload, fallback=submission_id)
        organization_id = self._resolve_org_id(payload)
        retry_config = self._extract_retry_config(payload)

        submission_record: Optional[FIRSSubmission] = None
        invoice_payload: Optional[Dict[str, Any]] = None

        async with self._session_scope() as session:
            org_uuid = self._ensure_uuid(organization_id)
            tenant_id = str(org_uuid) if org_uuid else (
                organization_id if isinstance(organization_id, str) else None
            )
            with tenant_context(tenant_id) if tenant_id else nullcontext():
                sub_uuid = self._ensure_uuid(submission_id)
                if sub_uuid is not None:
                    submission_record = await firs_repo.get_submission_by_id(
                        session,
                        submission_id=sub_uuid,
                        organization_id=org_uuid,
                    )
                if submission_record is None and invoice_number:
                    submission_record = await self._get_submission_by_invoice(
                        session,
                        invoice_number=invoice_number,
                        organization_id=org_uuid,
                    )

        if submission_record and isinstance(submission_record.invoice_data, dict):
            invoice_payload = dict(submission_record.invoice_data)

        if invoice_payload is None:
            record = await self._fetch_invoice_record(
                organization_id=organization_id,
                invoice_number=invoice_number,
                submission_id=submission_id,
                irn=getattr(submission_record, "irn", None),
                correlation_id=payload.get("correlation_id"),
                si_invoice_id=payload.get("si_invoice_id"),
            )
            if record and isinstance(record.invoice_data, dict):
                invoice_payload = dict(record.invoice_data)

        if invoice_payload is None:
            raise ValueError("invoice_payload_unavailable_for_retry")

        prepared_invoice = build_firs_invoice(dict(invoice_payload))
        irn_value = payload.get("irn") or (submission_record.irn if submission_record else None)
        submission_ref = str(submission_record.id) if submission_record else (submission_id if submission_id else None)
        operation = "transmit_firs_invoice" if irn_value else "submit_invoice_to_firs"

        metadata_payload: Dict[str, Any] = {
            k: v for k, v in {
                "irn": irn_value,
                "invoice_number": invoice_number,
                "organization_id": organization_id,
            }.items() if v
        }

        request = self._create_transmission_request(
            document_id=invoice_number or submission_ref or self._make_identifier("INV"),
            document_data=prepared_invoice,
            organization_id=organization_id,
            operation=operation,
            metadata={
                "submission_id": submission_ref,
                "request_id": payload.get("request_id"),
                "retry_config": retry_config,
                "payload": metadata_payload if metadata_payload else None,
            },
        )

        job_id = await self._queue_transmission_job(
            queue_name="firs_submissions_retry",
            submission_id=submission_ref,
            organization_id=organization_id,
            request=request,
            retry_config=retry_config,
        )

        failure_result = TransmissionResult(
            request_id=str(uuid.uuid4()),
            document_id=request.document_id,
            status=TransmissionStatus.FAILED,
            transmission_id=submission_ref,
            response_data=submission_record.firs_response if submission_record and isinstance(submission_record.firs_response, dict) else None,
            error_message=submission_record.firs_message if submission_record and submission_record.firs_message else None,
        )

        retry_id = await self._schedule_retry(request, failure_result, retry_config)

        firs_response = None
        if submission_ref or invoice_number:
            try:
                firs_response = await self._call_firs(
                    "update_firs_submission_status",
                    {
                        "submission_id": submission_ref,
                        "invoice_number": invoice_number,
                        "status": "processing",
                    },
                )
            except Exception as exc:
                self.logger.debug("FIRS status sync failed for %s: %s", submission_ref or invoice_number, exc)

        updated = await self._update_submission_status(
            submission_ref,
            organization_id,
            SubmissionStatus.PROCESSING,
            invoice_number=invoice_number,
        )

        return {
            "submission_id": submission_ref,
            "retry": True,
            "queue_message_id": job_id,
            "retry_id": retry_id,
            "submission": self._serialize_submission(updated) if updated else None,
            "firs_response": firs_response,
        }

    async def _handle_run_b2c_reporting_job(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        organization_id = self._resolve_org_id(payload)
        lookback_hours = float(payload.get("lookback_hours") or os.getenv("B2C_REPORTING_LOOKBACK_HOURS", "24"))
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=max(1.0, lookback_hours))
        max_batch = int(payload.get("max_invoices") or os.getenv("B2C_REPORTING_MAX_BATCH", "200"))
        max_batch = max(1, max_batch)

        status_filter = [
            SubmissionStatus.PENDING,
            SubmissionStatus.PROCESSING,
            SubmissionStatus.SUBMITTED,
        ]

        submissions: List[FIRSSubmission] = []
        async with self._session_scope() as session:
            stmt = select(FIRSSubmission).where(FIRSSubmission.status.in_(status_filter))
            org_uuid = None
            if organization_id:
                org_uuid = self._ensure_uuid(organization_id)
                if org_uuid:
                    stmt = stmt.where(FIRSSubmission.organization_id == org_uuid)
            rows = (await session.execute(stmt)).scalars().all()
            submissions = rows

        queued: List[str] = []
        skipped: List[str] = []

        for submission in submissions:
            if len(queued) >= max_batch:
                break

            created_ts = getattr(submission, "created_at", None) or submission.submitted_at or submission.updated_at
            if created_ts and created_ts > cutoff_time:
                skipped.append(str(submission.id))
                continue

            invoice_payload = submission.invoice_data if isinstance(submission.invoice_data, dict) else {}
            if not invoice_payload or not self._is_b2c_invoice(invoice_payload):
                skipped.append(str(submission.id))
                continue

            org_identifier = organization_id or (
                str(submission.organization_id) if submission.organization_id else None
            )

            try:
                prepared_invoice, _, _ = await self._prepare_invoice_for_submission(
                    dict(invoice_payload),
                    organization_id=org_identifier,
                    invoice_number=submission.invoice_number,
                    options=None,
                )
            except Exception as exc:
                self.logger.debug("Skipping B2C invoice %s due to validation failure: %s", submission.invoice_number, exc)
                skipped.append(str(submission.id))
                continue

            try:
                async with self._session_scope() as session:
                    tenant_id = str(submission.organization_id) if submission.organization_id else org_identifier
                    with tenant_context(tenant_id) if tenant_id else nullcontext():
                        existing = await session.get(FIRSSubmission, submission.id)
                        if existing:
                            async with session.begin():
                                existing.invoice_data = prepared_invoice
            except Exception as exc:
                self.logger.debug("Unable to refresh invoice payload for %s: %s", submission.id, exc)

            request = self._create_transmission_request(
                document_id=submission.invoice_number or str(submission.id),
                document_data=prepared_invoice,
                organization_id=org_identifier,
                operation="submit_invoice_to_firs",
                metadata={
                    "submission_id": str(submission.id),
                    "request_id": payload.get("request_id") or self._make_identifier("B2CJOB"),
                    "pipeline": "b2c_reporting",
                },
            )

            await self._queue_transmission_job(
                queue_name="firs_submissions_high",
                submission_id=str(submission.id),
                organization_id=org_identifier,
                request=request,
                retry_config=None,
            )

            try:
                await self._update_submission_status(
                    str(submission.id),
                    org_identifier,
                    SubmissionStatus.PROCESSING,
                    invoice_number=submission.invoice_number,
                )
            except Exception:
                self.logger.debug("Status update skipped for B2C submission %s", submission.id)

            queued.append(str(submission.id))

        return {
            "queued": queued,
            "skipped": skipped,
            "generated_at": self._now_iso(),
            "lookback_hours": lookback_hours,
        }

    async def _handle_get_invoice(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        submission_id = payload.get("submission_id")
        invoice_identifier = (
            payload.get("invoice_id")
            or payload.get("invoiceNumber")
            or payload.get("irn")
        )
        organization_id = self._resolve_org_id(payload)
        async with self._session_scope() as session:
            org_uuid = self._ensure_uuid(organization_id)
            tenant_id = str(org_uuid) if org_uuid else (
                organization_id if isinstance(organization_id, str) else None
            )
            with tenant_context(tenant_id) if tenant_id else nullcontext():
                submission = None
                sub_uuid = self._ensure_uuid(submission_id)
                if sub_uuid is not None:
                    submission = await firs_repo.get_submission_by_id(
                        session,
                        submission_id=sub_uuid,
                        organization_id=org_uuid,
                    )
                if submission is None and invoice_identifier:
                    submission = await self._get_submission_by_invoice(
                        session,
                        invoice_number=invoice_identifier,
                        organization_id=org_uuid,
                    )
        return {
            "invoice_id": invoice_identifier or submission_id,
            "submission": self._serialize_submission(submission) if submission else None,
        }

    async def _handle_get_transmission_history(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        limit = int(payload.get("limit", 25))
        page = int(payload.get("page", 1))
        date_range = payload.get("date_range") if isinstance(payload.get("date_range"), dict) else {}
        submissions = await self._list_submissions(
            payload,
            limit=limit,
            page=page,
            status=payload.get("status"),
            start_date=date_range.get("start"),
            end_date=date_range.get("end"),
        )
        summary = self._build_summary(submissions)
        return {
            "items": [self._serialize_submission(s) for s in submissions],
            "page": page,
            "limit": limit,
            "total": summary["total"],
            "generated_at": self._now_iso(),
        }

    async def _handle_get_transmission_details(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        transmission_id = payload.get("transmission_id") or payload.get("submission_id")
        invoice_identifier = (
            payload.get("invoice_id")
            or payload.get("invoiceNumber")
            or payload.get("irn")
        )
        organization_id = self._resolve_org_id(payload)
        async with self._session_scope() as session:
            org_uuid = self._ensure_uuid(organization_id)
            tenant_id = str(org_uuid) if org_uuid else (
                organization_id if isinstance(organization_id, str) else None
            )
            with tenant_context(tenant_id) if tenant_id else nullcontext():
                submission = None
                sub_uuid = self._ensure_uuid(transmission_id)
                if sub_uuid is not None:
                    submission = await firs_repo.get_submission_by_id(
                        session,
                        submission_id=sub_uuid,
                        organization_id=org_uuid,
                    )
                if submission is None and invoice_identifier:
                    submission = await self._get_submission_by_invoice(
                        session,
                        invoice_number=invoice_identifier,
                        organization_id=org_uuid,
                    )
        resolved_identifier = transmission_id or invoice_identifier
        if not submission:
            return {"transmission_id": resolved_identifier, "found": False}
        return {
            "transmission_id": resolved_identifier,
            "details": self._serialize_submission(submission),
        }

    async def _handle_generate_transmission_report(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        limit = int(payload.get("limit", 100))
        submissions = await self._list_submissions(
            payload,
            limit=limit,
            status=payload.get("status"),
            start_date=payload.get("start_date"),
            end_date=payload.get("end_date"),
        )
        summary = self._build_summary(submissions)
        metrics = self._build_metrics(submissions)
        return {
            "generated_at": self._now_iso(),
            "summary": summary,
            "metrics": metrics,
            "records": [self._serialize_submission(s) for s in submissions],
        }

    async def _handle_get_transmission_statistics(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        organization_id = self._resolve_org_id(payload)
        async with self._session_scope() as session:
            with tenant_context(organization_id) if organization_id else nullcontext():
                metrics = await firs_repo.get_submission_metrics(
                    session, organization_id=organization_id
                )
        return {"statistics": metrics, "generated_at": self._now_iso()}

    async def _handle_queue_transmission(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        operation_name = payload.get("operation") or payload.get("action") or "transmit_batch"
        organization_id = self._resolve_org_id(payload)
        retry_config = self._extract_retry_config(payload)
        batch_id = payload.get("batch_id") or payload.get("batchId")

        source_invoices: List[Any] = []
        candidate_lists = [
            payload.get("invoices"),
            payload.get("documents"),
            payload.get("items"),
            payload.get("invoice_batch"),
        ]
        for candidate in candidate_lists:
            if candidate:
                source_invoices = candidate
                break

        if not source_invoices:
            single_invoice = (
                payload.get("invoice_data")
                or payload.get("document")
                or payload.get("invoice")
            )
            if single_invoice:
                source_invoices = [single_invoice]

        if isinstance(source_invoices, dict):
            source_invoices = (
                source_invoices.get("items")
                or source_invoices.get("invoices")
                or source_invoices.get("documents")
                or []
            )

        normalized_invoices: List[Dict[str, Any]] = []
        for raw in source_invoices or []:
            normalized = self._normalize_invoice_payload(raw)
            if normalized:
                normalized_invoices.append(dict(normalized))

        if not normalized_invoices:
            raise ValueError("invoice_payload_unavailable_for_queueing")

        job_results: List[Dict[str, Any]] = []
        for entry in normalized_invoices:
            prepared_invoice = build_firs_invoice(dict(entry))
            document_id = (
                self._resolve_invoice_number(entry)
                or entry.get("invoiceNumber")
                or entry.get("invoice_number")
                or self._make_identifier("INV")
            )
            request = self._create_transmission_request(
                document_id=document_id,
                document_data=prepared_invoice,
                organization_id=organization_id,
                operation="submit_invoice_to_firs",
                metadata={
                    "batch_id": batch_id,
                    "retry_config": retry_config,
                    "payload": {
                        "batch_id": batch_id,
                        "organization_id": organization_id,
                    },
                },
            )
            job_id = await self._queue_transmission_job(
                queue_name="firs_submissions_high",
                submission_id=None,
                organization_id=organization_id,
                request=request,
                retry_config=retry_config,
                batch_id=batch_id,
            )
            job_results.append(
                {
                    "document_id": document_id,
                    "queue_message_id": job_id,
                }
            )

        return {
            "queued_operation": operation_name,
            "queued_at": self._now_iso(),
            "status": "queued",
            "jobs": job_results,
            "batch_id": batch_id,
            "count": len(job_results),
        }

    # ------------------------------------------------------------------
    # Messaging helpers
    # ------------------------------------------------------------------

    async def _consume_transmission_message(self, message) -> Any:
        payload = getattr(message, "payload", {}) or {}
        request_data = payload.get("transmission_request")
        if not isinstance(request_data, dict):
            self.logger.debug("Transmission message missing request payload")
            return False

        request = self._deserialize_transmission_request(request_data)
        submission_id = payload.get("submission_id") or request.metadata.get("submission_id")
        organization_id = payload.get("organization_id") or request.metadata.get("organization_id")
        retry_config = payload.get("retry_policy")

        if submission_id and "submission_id" not in request.metadata:
            request.metadata["submission_id"] = submission_id
        if organization_id and "organization_id" not in request.metadata:
            request.metadata["organization_id"] = organization_id

        batch_id = payload.get("batch_id")
        if batch_id:
            request.metadata.setdefault("batch_id", batch_id)

        result = await self._router_transmitter.transmit_document(request)

        await self._persist_transmission_outcome(
            request=request,
            result=result,
            submission_id=submission_id,
            organization_id=organization_id,
        )

        if result.status == TransmissionStatus.DELIVERED:
            self._record_transmission_metric(message.queue_name, "delivered")
            return {
                "status": "delivered",
                "document_id": request.document_id,
                "queue": message.queue_name,
            }

        retry_id = await self._schedule_retry(request, result, retry_config)
        if retry_id:
            self._record_transmission_metric(message.queue_name, "retry_scheduled")
            return {
                "status": "scheduled_retry",
                "retry_id": retry_id,
                "document_id": request.document_id,
                "queue": message.queue_name,
            }

        await self._dispatch_dead_letter(message, request, result, result.error_message)
        self._record_transmission_metric(message.queue_name, "dead_letter")
        return False

    async def _consume_status_poll(self, message: QueuedMessage) -> bool:
        payload = getattr(message, "payload", {}) or {}
        if payload.get("kind") != "firs_status_poll":
            return True

        submission_id = payload.get("submission_id")
        if not submission_id:
            return True

        attempt = int(payload.get("attempt", 1) or 1)
        max_attempts = int(payload.get("max_attempts", 1) or 1)
        organization_id = payload.get("organization_id")
        irn_hint = payload.get("irn")

        submission: Optional[FIRSSubmission] = None
        org_uuid = self._ensure_uuid(organization_id)
        tenant_id = str(org_uuid) if org_uuid else (organization_id if isinstance(organization_id, str) else None)

        async with self._session_scope() as session:
            with tenant_context(tenant_id) if tenant_id else nullcontext():
                sub_uuid = self._ensure_uuid(submission_id)
                if sub_uuid:
                    submission = await firs_repo.get_submission_by_id(
                        session,
                        submission_id=sub_uuid,
                        organization_id=org_uuid,
                    )

        if not submission:
            return True

        if submission.status not in self._BATCH_STATUSES:
            return True

        firs_payload: Dict[str, Any] = {
            "submission_id": submission_id,
        }
        if organization_id:
            firs_payload["organization_id"] = organization_id
        irn_value = irn_hint or submission.irn
        if irn_value:
            firs_payload["irn"] = irn_value

        try:
            firs_response = await self._call_firs("get_submission_status", firs_payload)
        except Exception as exc:
            self.logger.debug("Status poll call failed for %s: %s", submission_id, exc)
            firs_response = {"success": False, "error": str(exc)}

        updated_submission = submission
        if firs_response.get("success"):
            response_data = firs_response.get("data") if isinstance(firs_response.get("data"), dict) else {}
            status_hint = None
            if isinstance(response_data, dict):
                status_hint = response_data.get("status") or response_data.get("documentStatus")
            invoice_snapshot = submission.invoice_data if isinstance(submission.invoice_data, dict) else {}

            async with self._session_scope() as session:
                tenant_ctx_id = str(submission.organization_id) if submission.organization_id else tenant_id
                with tenant_context(tenant_ctx_id) if tenant_ctx_id else nullcontext():
                    updated_submission = await self._persist_submission(
                        session,
                        organization_id or (str(submission.organization_id) if submission.organization_id else None),
                        dict(invoice_snapshot),
                        firs_response,
                        status_hint=status_hint,
                        request_id=submission.request_id,
                    )
        else:
            self.logger.debug(
                "Status poll unsuccessful for %s: %s",
                submission_id,
                firs_response.get("error"),
            )

        final_submission = updated_submission or submission
        if (
            final_submission
            and final_submission.status in self._BATCH_STATUSES
            and attempt < max_attempts
        ):
            try:
                await self._schedule_status_poll(
                    final_submission,
                    organization_id or (str(final_submission.organization_id) if final_submission.organization_id else None),
                    attempt=attempt + 1,
                    max_attempts=max_attempts,
                )
            except Exception as exc:
                self.logger.debug("Unable to reschedule status poll for %s: %s", submission_id, exc)

        return True

    async def _call_firs(self, operation: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            return await self.message_router.route_message(
                service_role=ServiceRole.ACCESS_POINT_PROVIDER,
                operation=operation,
                payload=payload or {},
                source_service="transmission_service",
            )
        except Exception as exc:  # pragma: no cover - defensive fallback
            self.logger.warning("FIRS call failed: %s", exc)
            return {"operation": operation, "success": False, "error": str(exc)}

    # ------------------------------------------------------------------
    # Common response helpers
    # ------------------------------------------------------------------

    def _success(self, operation: str, data: Dict[str, Any]) -> Dict[str, Any]:
        return {"operation": operation, "success": True, "data": data}

    def _failure(self, operation: str, error: str) -> Dict[str, Any]:
        return {"operation": operation, "success": False, "error": error}

    def _unsupported(self, operation: str) -> Dict[str, Any]:
        return {"operation": operation, "success": False, "error": "unsupported_operation"}

    def _make_identifier(self, prefix: str) -> str:
        return f"{prefix}-{uuid.uuid4().hex[:12]}"


__all__ = ["TransmissionService"]
