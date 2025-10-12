from __future__ import annotations

import base64
import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic import ValidationError

from core_platform.utils.irn_helper import generate_canonical_irn
from core_platform.validation.firs_invoice_schema import FIRSInvoiceModel
from si_services.irn_qr_generation.qr_signing_service import QRSigningService

logger = logging.getLogger(__name__)


class InvoiceValidationService:
    """Validate invoice payloads, enrich with IRN/QR data, and proxy to FIRS."""

    def __init__(self, qr_signing_service: Optional[QRSigningService] = None):
        self.qr_signing_service = qr_signing_service or self._build_default_signer()

    async def validate_invoice(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        invoice_payload = payload.get("invoice_data") or payload

        try:
            invoice = FIRSInvoiceModel.parse_obj(invoice_payload)
        except ValidationError as exc:
            logger.debug("Invoice validation failed: %s", exc)
            raise

        invoice_dict = invoice.dict(by_alias=True)
        irn = (
            invoice_dict.get("irn")
            or generate_canonical_irn(
                invoice.invoice_number,
                invoice.supplier.service_id,
                invoice.issue_date,
            )
        )
        invoice_dict["irn"] = irn

        qr_signature = self._generate_qr_signature(
            irn=irn,
            invoice=invoice_dict,
        )

        if qr_signature:
            verification_code = qr_signature["qr_data"].get("verification_code")
            if verification_code:
                invoice_dict["verificationCode"] = verification_code

        result = {
            "validated": True,
            "invoice": invoice_dict,
            "irn": irn,
            "qr_signature": qr_signature,
            "forwarded": False,
            "firs_response": None,
        }

        return result

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _generate_qr_signature(
        self,
        *,
        irn: str,
        invoice: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        if not self.qr_signing_service:
            return None

        invoice_data = {
            "invoice_number": invoice.get("invoiceNumber"),
            "invoice_date": invoice.get("issueDate"),
            "total_amount": invoice.get("totals", {}).get("total"),
            "currency": invoice.get("totals", {}).get("currency", "NGN"),
            "customer_name": invoice.get("customer", {}).get("name", ""),
            "customer_tax_id": invoice.get("customer", {}).get("tin", ""),
        }

        signature = self.qr_signing_service.generate_signed_qr(
            irn=irn,
            verification_code=invoice.get("verificationCode", ""),
            invoice_data=invoice_data,
        )

        if not signature:
            return None

        return {
            "qr_data": signature.qr_data,
            "qr_string": signature.qr_string,
            "encrypted_payload": signature.encrypted_payload,
            "encryption_metadata": signature.encryption_metadata,
        }

    def _build_default_signer(self) -> Optional[QRSigningService]:
        key_path_env = os.getenv("FIRS_CRYPTO_KEYS_PATH")
        inline_key_env = os.getenv("FIRS_CRYPTO_KEYS_B64")
        inline_public_key = None

        if inline_key_env:
            try:
                inline_public_key = base64.b64decode(inline_key_env).decode("utf-8")
            except Exception as exc:
                logger.warning("Failed to decode FIRS_CRYPTO_KEYS_B64: %s", exc)

        if not key_path_env and not inline_public_key:
            logger.info("QR signing disabled: no crypto key configuration found")
            return None

        try:
            return QRSigningService(
                key_path=Path(key_path_env).expanduser() if key_path_env else None,
                public_key_pem=inline_public_key,
            )
        except Exception as exc:
            logger.warning("Unable to initialize QRSigningService: %s", exc)
            return None
