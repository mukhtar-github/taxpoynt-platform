"""
Hybrid Transmission Coordination
Bridges SI → APP invoice submissions by performing cross-role coordination
before APP TransmissionService persists and submits to FIRS.

Responsibilities (minimal v1):
- Accept SI invoice IDs or batch IDs with SI metadata.
- Record a coordination acknowledgement and optional correlation stub.
- Degrade gracefully if optional infra (queues/analytics) is unavailable.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class TransmissionCoordinationService:
    """Lightweight coordination for SI → APP invoice forwarding."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)

    async def coordinate_invoices(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate a set of SI invoices forwarded to APP for FIRS.

        Expected payload keys:
        - invoice_ids: List[str]
        - si_user_id: str
        - options/submission_options: Dict[str, Any] (optional)
        """
        try:
            invoice_ids = payload.get("invoice_ids") or []
            si_user_id = payload.get("si_user_id")
            options = (
                payload.get("options")
                or payload.get("submission_options")
                or {}
            )

            if not isinstance(invoice_ids, list):
                invoice_ids = [invoice_ids] if invoice_ids else []

            self.logger.info(
                "Hybrid coordination: %d SI invoices from user %s",
                len(invoice_ids),
                si_user_id,
            )

            # Minimal acknowledgement object; real correlation/queueing can extend this.
            ack = {
                "ack_type": "si_invoices",
                "received_count": len(invoice_ids),
                "si_user_id": si_user_id,
                "options": options,
            }

            # Best-effort: create a single batch correlation stub if correlation service available
            try:
                from hybrid_services import get_hybrid_service_registry  # circular-safe import
                from core_platform.messaging.message_router import ServiceRole
                registry = get_hybrid_service_registry()
                if registry and registry.message_router:
                    corr_resp = await registry.message_router.route_message(
                        service_role=ServiceRole.HYBRID,
                        operation="create_correlation",
                        payload={
                            "si_reference_id": options.get("batch_ref") or ",".join(invoice_ids[:5])[:64],
                            "app_reference_id": options.get("app_ref"),
                            "organization_id": options.get("organization_id") or options.get("tenant_id"),
                            "status": "APP_RECEIVED",
                            "metadata": {
                                "source": "si_forward",
                                "invoice_ids": invoice_ids[:50],
                                "count": len(invoice_ids),
                            },
                        },
                    )
                    if isinstance(corr_resp, dict) and corr_resp.get("success"):
                        ack["correlation"] = corr_resp.get("data")
            except Exception as ce:
                self.logger.debug("Correlation creation skipped: %s", ce)

            # Best-effort: kick off lightweight analytics event (no critical path)
            try:
                if registry and registry.message_router:
                    await registry.message_router.route_message(
                        service_role=ServiceRole.HYBRID,
                        operation="process_analytics",
                        payload={
                            "data": {
                                "event": "si_forward_received",
                                "received_count": len(invoice_ids),
                                "organization_id": options.get("organization_id") or options.get("tenant_id"),
                                "source": "si_forward",
                            }
                        },
                    )
            except Exception as ae:
                self.logger.debug("Analytics kick-off skipped: %s", ae)

            return {"success": True, "data": ack}
        except Exception as e:
            self.logger.error("Hybrid coordination failed (invoices): %s", e)
            return {"success": False, "error": str(e)}

    async def coordinate_batch(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate an SI batch forwarded to APP for FIRS.

        Expected payload keys:
        - batch_id: str
        - si_user_id: str
        - options/batch_options: Dict[str, Any] (optional)
        """
        try:
            batch_id = payload.get("batch_id")
            si_user_id = payload.get("si_user_id")
            options = payload.get("options") or payload.get("batch_options") or {}

            self.logger.info(
                "Hybrid coordination: SI batch %s from user %s",
                batch_id,
                si_user_id,
            )

            ack = {
                "ack_type": "si_batch",
                "batch_id": batch_id,
                "si_user_id": si_user_id,
                "options": options,
            }

            # Best-effort correlation record
            try:
                from hybrid_services import get_hybrid_service_registry
                from core_platform.messaging.message_router import ServiceRole
                registry = get_hybrid_service_registry()
                if registry and registry.message_router:
                    corr_resp = await registry.message_router.route_message(
                        service_role=ServiceRole.HYBRID,
                        operation="create_correlation",
                        payload={
                            "si_reference_id": batch_id,
                            "app_reference_id": options.get("app_ref"),
                            "organization_id": options.get("organization_id") or options.get("tenant_id"),
                            "status": "APP_RECEIVED",
                            "metadata": {"source": "si_forward_batch"},
                        },
                    )
                    if isinstance(corr_resp, dict) and corr_resp.get("success"):
                        ack["correlation"] = corr_resp.get("data")
            except Exception as ce:
                self.logger.debug("Correlation creation skipped: %s", ce)

            # Best-effort: analytics event for batch receipt
            try:
                if registry and registry.message_router:
                    await registry.message_router.route_message(
                        service_role=ServiceRole.HYBRID,
                        operation="process_analytics",
                        payload={
                            "data": {
                                "event": "si_batch_forward_received",
                                "batch_id": batch_id,
                                "organization_id": options.get("organization_id") or options.get("tenant_id"),
                                "source": "si_forward_batch",
                            }
                        },
                    )
            except Exception as ae:
                self.logger.debug("Analytics kick-off skipped: %s", ae)

            return {"success": True, "data": ack}
        except Exception as e:
            self.logger.error("Hybrid coordination failed (batch): %s", e)
            return {"success": False, "error": str(e)}
