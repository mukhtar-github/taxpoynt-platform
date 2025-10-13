"""
IRN Generator

Provides a legacy-compatible helper for synthesising Invoice Reference Numbers
when running in environments that do not call the live FIRS APIs. The local
fallback now mirrors the FIRS-compliant structure:

    {InvoiceRef}-{ServiceID}-{YYYYMMDD}

The generator now reflects the latest FIRS guidance where System Integrators
produce IRNs locally before submitting invoices for clearance.
"""

import base64
import hashlib
import hmac
import logging
import re
import secrets
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


class IRNGenerator:
    """Generate FIRS-style Invoice Reference Numbers when remote IRNs are disabled."""

    _DEFAULT_SERVICE_ID = "SVC00001"

    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or secrets.token_hex(32)

    def generate_irn(self, invoice_data: Dict[str, Any]) -> Tuple[str, str, str]:
        """Generate a deterministic IRN using the FIRS-compliant structure."""

        invoice_reference = self._resolve_invoice_reference(invoice_data)
        service_id = self._resolve_service_id(invoice_data)
        invoice_date = self._resolve_invoice_date(invoice_data)

        irn_value = f"{invoice_reference}-{service_id}-{invoice_date.strftime('%Y%m%d')}"

        invoice_hash = self._create_invoice_hash(invoice_data)
        verification_code = self._generate_verification_code(irn_value, invoice_hash)
        final_hash = self._create_final_hash(irn_value, verification_code)

        return irn_value, verification_code, final_hash

    def generate_simple_irn(self, invoice_id: str) -> str:
        """Generate simple IRN for basic use cases"""
        invoice_reference = self._sanitize_reference(str(invoice_id) or "INV")
        service_id = self._DEFAULT_SERVICE_ID
        invoice_date = datetime.utcnow()
        return f"{invoice_reference}-{service_id}-{invoice_date.strftime('%Y%m%d')}"

    def _create_invoice_hash(self, invoice_data: Dict[str, Any]) -> str:
        """Create deterministic hash from invoice data"""
        # Extract key fields for hashing
        key_fields = [
            str(invoice_data.get('customer_id', '')),
            str(invoice_data.get('invoice_number', '')),
            str(invoice_data.get('total_amount', '')),
            str(invoice_data.get('invoice_date', ''))
        ]
        
        # Create consistent string
        hash_string = '|'.join(key_fields)
        
        # Generate hash
        return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()

    def _resolve_invoice_reference(self, invoice_data: Dict[str, Any]) -> str:
        candidates = [
            'invoice_reference', 'invoiceReference', 'invoice_ref', 'invoiceRef',
            'invoice_number', 'invoiceNumber', 'document_number', 'documentNumber',
        ]
        for key in candidates:
            value = invoice_data.get(key)
            if value:
                sanitized = self._sanitize_reference(str(value))
                if sanitized:
                    return sanitized
        fallback = f"INV{datetime.utcnow().strftime('%Y%m%d')}{secrets.token_hex(2).upper()}"
        return self._sanitize_reference(fallback)

    def _resolve_service_id(self, invoice_data: Dict[str, Any]) -> str:
        candidates = [
            'service_id', 'serviceId', 'firs_service_id', 'firsServiceId',
            'service_code', 'serviceCode', 'serviceID'
        ]
        for key in candidates:
            value = invoice_data.get(key)
            if value:
                sanitized = self._sanitize_service_id(str(value))
                if sanitized:
                    return sanitized
        return self._DEFAULT_SERVICE_ID

    def _resolve_invoice_date(self, invoice_data: Dict[str, Any]) -> datetime:
        candidates = [
            'invoice_date', 'invoiceDate', 'issue_date', 'issueDate',
            'transaction_date', 'transactionDate', 'date'
        ]
        for key in candidates:
            value = invoice_data.get(key)
            if not value:
                continue
            parsed = self._parse_date(value)
            if parsed:
                return parsed
        return datetime.utcnow()

    def _parse_date(self, value: Any) -> Optional[datetime]:
        if isinstance(value, datetime):
            return value
        text = str(value).strip()
        if not text:
            return None
        for fmt in ('%Y-%m-%d', '%Y/%m/%d', '%d-%m-%Y', '%Y%m%d', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%dT%H:%M:%S.%f'):
            try:
                return datetime.strptime(text, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(text.replace('Z', '+00:00'))
        except ValueError:
            return None

    def _sanitize_reference(self, value: str) -> str:
        cleaned = re.sub(r'[^A-Za-z0-9]', '', value.upper())
        return cleaned[:48] or 'INV'

    def _sanitize_service_id(self, value: str) -> str:
        cleaned = re.sub(r'[^A-Za-z0-9]', '', value.upper())
        if not cleaned:
            return self._DEFAULT_SERVICE_ID
        cleaned = cleaned[:8]
        if len(cleaned) < 8:
            cleaned = cleaned.ljust(8, '0')
        return cleaned

    def _generate_verification_code(self, irn_value: str, invoice_hash: str) -> str:
        """Generate verification code using HMAC"""
        message = f"{irn_value}:{invoice_hash}"
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).digest()
        
        # Return first 8 characters of base64 encoded signature
        return base64.b64encode(signature).decode('utf-8')[:8]
    
    def _create_final_hash(self, irn_value: str, verification_code: str) -> str:
        """Create final hash for data integrity"""
        combined = f"{irn_value}:{verification_code}"
        return hashlib.sha256(combined.encode('utf-8')).hexdigest()
    
    def validate_irn_format(self, irn_value: str) -> bool:
        """Validate IRN format structure"""
        if not irn_value or not isinstance(irn_value, str):
            return False

        pattern = r'^[A-Z0-9]+(?:-[A-Z0-9]+)*-[A-Z0-9]+-\d{8}$'
        return re.match(pattern, irn_value.upper()) is not None

    def extract_timestamp_from_irn(self, irn_value: str) -> Optional[datetime]:
        """Extract timestamp from IRN"""
        if not self.validate_irn_format(irn_value):
            return None
        try:
            date_part = irn_value.split('-')[-1]
            return datetime.strptime(date_part, "%Y%m%d")
        except (ValueError, IndexError):
            return None
