"""
FIRS HTTP Client (Header-based)
===============================
Lightweight client for the current FIRS API flows observed in the repository
and Postman collection (header auth with x-api-key/x-api-secret/x-timestamp/
x-request-id/x-certificate).

Scope:
- Validate invoice: POST /api/v1/invoice/validate
- Validate IRN: POST /api/v1/invoice/irn/validate
- Create/Search party: POST /api/v1/invoice/party, GET /api/v1/invoice/party/{id}
- Resources: GET /api/v1/invoice/resources/{currencies|invoice-types|services-codes|vat-exemptions}
- Verify TIN: POST /api/v1/utilities/verify-tin

Notes:
- Network host, creds and certificate are read from env.
- Errors are returned as dicts with {success, status_code, data|error}.
"""
import os
import time
import uuid
import logging
from typing import Any, Dict, Optional

import aiohttp

from core_platform.utils.firs_response import extract_firs_identifiers
from .certificate_provider import FIRSCertificateProvider

logger = logging.getLogger(__name__)


class FIRSHttpClient:
    """Thin async HTTP client for FIRS APIs (header-based auth)."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        *,
        certificate_provider: Optional[FIRSCertificateProvider] = None,
    ):
        self.base_url = (base_url or os.getenv("FIRS_API_URL") or "").rstrip("/")
        self.api_key = os.getenv("FIRS_API_KEY", "")
        self.api_secret = os.getenv("FIRS_API_SECRET", "")
        self._certificate_provider = certificate_provider or FIRSCertificateProvider()
        self._session: Optional[aiohttp.ClientSession] = None

    async def start(self):
        if not self._session:
            timeout = aiohttp.ClientTimeout(total=30)
            self._session = aiohttp.ClientSession(timeout=timeout)

    async def stop(self):
        if self._session:
            await self._session.close()
            self._session = None

    def _headers(self) -> Dict[str, str]:
        headers = {
            "accept": "application/json",
            "x-api-key": self.api_key,
            "x-api-secret": self.api_secret,
            "x-timestamp": str(int(time.time())),
            "x-request-id": str(uuid.uuid4()),
            "Content-Type": "application/json"
        }

        certificate = self._certificate_provider.get_active_certificate()
        if certificate:
            headers["x-certificate"] = certificate

        return headers

    async def _post(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            await self.start()
            async with self._session.post(url, json=payload, headers=self._headers()) as resp:
                data = await _safe_json(resp)
                return {"success": resp.status == 200, "status_code": resp.status, "data": data}
        except Exception as e:
            logger.error(f"FIRS POST {path} failed: {e}")
            return {"success": False, "status_code": 0, "error": str(e)}

    async def _get(self, path: str) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            await self.start()
            async with self._session.get(url, headers=self._headers()) as resp:
                data = await _safe_json(resp)
                return {"success": resp.status == 200, "status_code": resp.status, "data": data}
        except Exception as e:
            logger.error(f"FIRS GET {path} failed: {e}")
            return {"success": False, "status_code": 0, "error": str(e)}

    # Public API
    async def validate_invoice(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._post("/api/v1/invoice/validate", payload)

    async def validate_irn(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._post("/api/v1/invoice/irn/validate", payload)

    async def create_party(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._post("/api/v1/invoice/party", payload)

    async def get_party(self, party_id: str) -> Dict[str, Any]:
        return await self._get(f"/api/v1/invoice/party/{party_id}")

    async def get_resource(self, resource: str) -> Dict[str, Any]:
        # resource: currencies | invoice-types | services-codes | vat-exemptions
        return await self._get(f"/api/v1/invoice/resources/{resource}")

    async def verify_tin(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._post("/api/v1/utilities/verify-tin/", payload)

    async def authenticate_taxpayer(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._post("/api/v1/utilities/authenticate", payload)

    # Manage E-Invoice
    async def sign_invoice(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        response = await self._post("/api/v1/invoice/sign", payload)
        identifiers = extract_firs_identifiers(response.get("data"))
        if identifiers:
            response.setdefault("identifiers", identifiers)
        return response

    async def confirm_invoice(self, irn: str) -> Dict[str, Any]:
        return await self._get(f"/api/v1/invoice/confirm/{irn}")

    async def _patch(self, path: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        try:
            await self.start()
            async with self._session.patch(url, json=payload, headers=self._headers()) as resp:
                data = await _safe_json(resp)
                return {"success": resp.status in (200, 204), "status_code": resp.status, "data": data}
        except Exception as e:
            logger.error(f"FIRS PATCH {path} failed: {e}")
            return {"success": False, "status_code": 0, "error": str(e)}

    async def download_invoice(self, irn: str) -> Dict[str, Any]:
        return await self._get(f"/api/v1/invoice/download/{irn}")

    async def search_invoice(self, business_id: str) -> Dict[str, Any]:
        return await self._get(f"/api/v1/invoice/{business_id}")

    async def update_invoice(self, irn: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self._patch(f"/api/v1/invoice/update/{irn}", payload)

    # Exchange E-Invoice (transmission)
    async def transmit(self, irn: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        response = await self._post(f"/api/v1/invoice/transmit/{irn}", payload or {})
        identifiers = extract_firs_identifiers(response.get("data"))
        if identifiers:
            response.setdefault("identifiers", identifiers)
        return response

    async def confirm_receipt(self, irn: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return await self._patch(f"/api/v1/invoice/transmit/{irn}", payload or {})

    async def lookup_transmit_by_irn(self, irn: str) -> Dict[str, Any]:
        return await self._get(f"/api/v1/invoice/transmit/lookup/{irn}")

    async def lookup_transmit_by_tin(self, party_id: str) -> Dict[str, Any]:
        return await self._get(f"/api/v1/invoice/transmit/lookup/tin/{party_id}")

    async def lookup_transmit_by_party(self, party_id: str) -> Dict[str, Any]:
        return await self._get(f"/api/v1/invoice/transmit/lookup/party/{party_id}")

    async def transmit_self_health(self) -> Dict[str, Any]:
        return await self._get("/api/v1/invoice/transmit/self-health-check")

    async def transmit_pull(self) -> Dict[str, Any]:
        return await self._get("/api/v1/invoice/transmit/pull")


async def _safe_json(resp: aiohttp.ClientResponse) -> Any:
    try:
        return await resp.json()
    except Exception:
        try:
            text = await resp.text()
            return {"raw": text}
        except Exception:
            return None
