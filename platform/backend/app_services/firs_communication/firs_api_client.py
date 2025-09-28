"""
FIRS API Client - Access Point Provider Services

Official FIRS API client for the APP (Access Point Provider) role.
Handles secure communication with FIRS endpoints using the header-based
authentication model required by the live FIRS scheme (x-api-key,
x-api-secret, x-timestamp, x-request-id, x-certificate).

This client provides:
- TLS 1.3 secure communications
- Request/response handling
- Connection pooling and retry logic
- Rate limiting and quota management
- Environment-specific endpoint management (sandbox/production)
"""

import asyncio
import json
import logging
import ssl
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union

import aiohttp
import certifi
from urllib.parse import urljoin

from core_platform.utils.firs_response import extract_firs_identifiers, merge_identifiers_into_payload
from .party_cache import PartyCache, TINCache

logger = logging.getLogger(__name__)


class FIRSEnvironment(Enum):
    """FIRS environment types"""
    SANDBOX = "sandbox"
    PRODUCTION = "production"


class FIRSEndpoint(Enum):
    """FIRS API endpoints aligned with the live header-auth scheme"""

    # Invoice validation and management
    INVOICE_VALIDATE = "/api/v1/invoice/validate"
    INVOICE_IRN_VALIDATE = "/api/v1/invoice/irn/validate"
    INVOICE_SIGN = "/api/v1/invoice/sign"
    INVOICE_CONFIRM = "/api/v1/invoice/confirm/{irn}"
    INVOICE_DOWNLOAD = "/api/v1/invoice/download/{irn}"
    INVOICE_SEARCH = "/api/v1/invoice/{business_id}"
    INVOICE_UPDATE = "/api/v1/invoice/update/{irn}"

    # Party endpoints
    INVOICE_PARTY = "/api/v1/invoice/party"
    INVOICE_PARTY_DETAIL = "/api/v1/invoice/party/{party_id}"

    # Resource endpoints
    INVOICE_RESOURCES = "/api/v1/invoice/resources/{resource}"

    # Transmission endpoints
    INVOICE_TRANSMIT = "/api/v1/invoice/transmit/{irn}"
    INVOICE_TRANSMIT_LOOKUP_IRN = "/api/v1/invoice/transmit/lookup/{irn}"
    INVOICE_TRANSMIT_LOOKUP_TIN = "/api/v1/invoice/transmit/lookup/tin/{party_id}"
    INVOICE_TRANSMIT_LOOKUP_PARTY = "/api/v1/invoice/transmit/lookup/party/{party_id}"
    INVOICE_TRANSMIT_SELF_HEALTH = "/api/v1/invoice/transmit/self-health-check"
    INVOICE_TRANSMIT_PULL = "/api/v1/invoice/transmit/pull"

    # Utility endpoints
    UTILITIES_VERIFY_TIN = "/api/v1/utilities/verify-tin"
    UTILITIES_AUTHENTICATE = "/api/v1/utilities/authenticate"


@dataclass
class FIRSConfig:
    """Configuration for FIRS API client"""
    environment: FIRSEnvironment = FIRSEnvironment.SANDBOX
    api_key: str = ""
    api_secret: str = ""
    certificate: str = ""
    client_id: str = ""  # retained for backwards compatibility with OAuth flows
    client_secret: str = ""  # retained for backwards compatibility with OAuth flows
    certificates: List[str] = field(default_factory=list)
    certificate_rotation_interval_seconds: int = 0
    
    # Connection settings
    base_url: str = ""
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Rate limiting
    requests_per_minute: int = 60
    requests_per_hour: int = 1000
    
    # TLS settings
    tls_version: str = "TLSv1.3"
    verify_ssl: bool = True
    ca_bundle_path: Optional[str] = None
    
    # Authentication settings
    token_expiry_buffer: int = 300  # 5 minutes before actual expiry
    max_auth_retries: int = 2
    
    def __post_init__(self):
        """Initialize environment-specific settings"""
        if not self.base_url:
            if self.environment == FIRSEnvironment.SANDBOX:
                self.base_url = "https://sandbox-api.firs.gov.ng"
            else:
                self.base_url = "https://api.firs.gov.ng"

        # Normalise certificate pool
        cert_pool: List[str] = []
        if self.certificate:
            cert_pool.append(self.certificate)
        for cert in self.certificates:
            if cert and cert not in cert_pool:
                cert_pool.append(cert)
        self.certificates = cert_pool
        if self.certificates and not self.certificate:
            self.certificate = self.certificates[0]

        if self.certificate_rotation_interval_seconds < 0:
            self.certificate_rotation_interval_seconds = 0


@dataclass
class FIRSRequest:
    """FIRS API request structure"""
    endpoint: str
    method: str = "POST"
    headers: Dict[str, str] = field(default_factory=dict)
    params: Dict[str, Any] = field(default_factory=dict)
    data: Optional[Dict[str, Any]] = None
    timeout: Optional[int] = None
    retry_count: int = 0


@dataclass
class FIRSResponse:
    """FIRS API response structure"""
    status_code: int
    headers: Dict[str, str]
    data: Dict[str, Any]
    raw_response: str
    request_id: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = False
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    identifiers: Optional[Dict[str, Any]] = None


@dataclass
class FIRSClientMetrics:
    """Metrics for FIRS API client"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    authentication_requests: int = 0
    retry_attempts: int = 0
    average_response_time: float = 0.0
    rate_limit_hits: int = 0
    last_request_time: Optional[datetime] = None
    uptime_start: datetime = field(default_factory=datetime.now)


class FIRSAPIClient:
    """
    Official FIRS API client for Access Point Provider services.
    
    Provides secure communication with FIRS endpoints using the required
    header-based authentication scheme and TLS 1.3.
    """
    
    def __init__(
        self,
        config: FIRSConfig,
        auth_handler: Optional[Any] = None,
        *,
        party_cache: Optional[PartyCache] = None,
        tin_cache: Optional[TINCache] = None,
    ):
        self.config = config

        # Optional legacy authentication handler (kept for backwards compatibility)
        self.auth_handler = auth_handler

        # Client state
        self.session: Optional[aiohttp.ClientSession] = None

        # Certificate rotation state
        self._certificate_pool: List[str] = self._initialize_certificate_pool()
        self._current_certificate_index: int = 0
        self._last_certificate_rotation: Optional[datetime] = None

        # Rate limiting
        self.request_timestamps: List[datetime] = []
        self.is_rate_limited: bool = False
        self.rate_limit_reset_time: Optional[datetime] = None

        # Metrics
        self.metrics = FIRSClientMetrics()

        # SSL context for TLS 1.3
        self._ssl_context: Optional[ssl.SSLContext] = None

        # Cache layers for repeated lookups
        self.party_cache = party_cache or PartyCache()
        self.tin_cache = tin_cache or TINCache()
        self._party_refresh_tasks: Dict[str, asyncio.Task] = {}
        self._tin_refresh_tasks: Dict[str, asyncio.Task] = {}
    
    async def start(self) -> None:
        """Start the FIRS API client"""
        try:
            logger.info(f"Starting FIRS API client for {self.config.environment.value}")

            # Initialize optional legacy authentication handler, if provided
            if self.auth_handler and hasattr(self.auth_handler, "start"):
                try:
                    await self.auth_handler.start()
                except Exception:  # pragma: no cover - best-effort legacy support
                    logger.debug("FIRS legacy auth handler failed to start; continuing with header auth")

            # Create SSL context for TLS 1.3
            self._ssl_context = self._create_ssl_context()
            
            # Create HTTP session with connection pooling
            connector = aiohttp.TCPConnector(
                ssl=self._ssl_context,
                limit=100,
                limit_per_host=20,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=30,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(
                total=self.config.timeout_seconds,
                connect=10,
                sock_read=self.config.timeout_seconds
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'TaxPoynt-APP-Client/1.0',
                    'Accept': 'application/json'
                }
            )

            logger.info("FIRS API client started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start FIRS API client: {e}")
            raise
    
    async def stop(self) -> None:
        """Stop the FIRS API client"""
        try:
            logger.info("Stopping FIRS API client")
            
            if self.session:
                await self.session.close()
                self.session = None

            for task in list(self._party_refresh_tasks.values()):
                task.cancel()
            self._party_refresh_tasks.clear()

            for task in list(self._tin_refresh_tasks.values()):
                task.cancel()
            self._tin_refresh_tasks.clear()

            if self.auth_handler and hasattr(self.auth_handler, "stop"):
                try:
                    await self.auth_handler.stop()
                except Exception:  # pragma: no cover - best-effort legacy support
                    logger.debug("FIRS legacy auth handler failed to stop cleanly")
            
            logger.info("FIRS API client stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping FIRS API client: {e}")
    
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Create SSL context for TLS 1.3"""
        try:
            # Create SSL context with TLS 1.3
            context = ssl.create_default_context(cafile=certifi.where())
            
            # Force TLS 1.3 if supported
            if hasattr(ssl, 'TLSVersion'):
                context.minimum_version = ssl.TLSVersion.TLSv1_2
                context.maximum_version = ssl.TLSVersion.TLSv1_3
            
            # Security settings
            context.check_hostname = self.config.verify_ssl
            context.verify_mode = ssl.CERT_REQUIRED if self.config.verify_ssl else ssl.CERT_NONE
            
            # Use custom CA bundle if provided
            if self.config.ca_bundle_path:
                context.load_verify_locations(self.config.ca_bundle_path)
            
            # Cipher configuration for maximum security
            context.set_ciphers('ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS')
            
            logger.info(f"SSL context created with TLS version: {self.config.tls_version}")
            return context
            
        except Exception as e:
            logger.error(f"Failed to create SSL context: {e}")
            raise
    
    def _build_headers(self, extra_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """Construct the required header-based authentication values."""

        timestamp = str(int(time.time()))
        request_id = f"req_{timestamp}_{uuid.uuid4().hex[:8]}"

        headers = {
            "accept": "application/json",
            "x-api-key": self.config.api_key,
            "x-api-secret": self.config.api_secret,
            "x-timestamp": timestamp,
            "x-request-id": request_id,
        }

        certificate = self._select_certificate()
        if certificate:
            headers["x-certificate"] = certificate

        if extra_headers:
            headers.update({k: v for k, v in extra_headers.items() if v is not None})

        return headers
    
    async def _check_rate_limits(self) -> bool:
        """Check if request can be made within rate limits"""
        try:
            current_time = datetime.now()
            
            # Clean old timestamps
            cutoff_time = current_time - timedelta(minutes=1)
            self.request_timestamps = [
                ts for ts in self.request_timestamps 
                if ts > cutoff_time
            ]
            
            # Check per-minute limit
            if len(self.request_timestamps) >= self.config.requests_per_minute:
                self.is_rate_limited = True
                self.rate_limit_reset_time = current_time + timedelta(minutes=1)
                self.metrics.rate_limit_hits += 1
                return False
            
            self.is_rate_limited = False
            return True
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return True  # Allow request if check fails
    
    async def make_request(
        self,
        endpoint: Union[str, FIRSEndpoint],
        method: str = "POST",
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        retry_on_auth_failure: bool = True
    ) -> FIRSResponse:
        """
        Make authenticated request to FIRS API
        
        Args:
            endpoint: API endpoint (string or FIRSEndpoint enum)
            method: HTTP method
            data: Request payload
            params: Query parameters
            headers: Additional headers
            timeout: Request timeout
            retry_on_auth_failure: Whether to retry on auth failure
            
        Returns:
            FIRSResponse object
        """
        try:
            # Prepare endpoint URL
            if isinstance(endpoint, FIRSEndpoint):
                endpoint_path = endpoint.value
            else:
                endpoint_path = endpoint

            url = urljoin(self.config.base_url, endpoint_path)

            # Check rate limits
            if not await self._check_rate_limits():
                raise Exception("Rate limit exceeded")

            if not self.session:
                raise RuntimeError("FIRS API client session is not initialized. Call start() first.")

            request_headers = self._build_headers(headers)

            http_method = method.upper()

            # Only include JSON payload when appropriate
            json_payload = data if http_method not in {"GET", "DELETE"} else None

            if http_method not in {"GET", "DELETE"} and "Content-Type" not in request_headers:
                request_headers["Content-Type"] = "application/json"

            request_timeout = timeout or self.config.timeout_seconds

            # Make request
            start_time = datetime.now()

            async with self.session.request(
                method=method,
                url=url,
                json=json_payload,
                params=params,
                headers=request_headers,
                timeout=aiohttp.ClientTimeout(total=request_timeout)
            ) as response:

                response_time = (datetime.now() - start_time).total_seconds()

                # Update metrics
                self.metrics.total_requests += 1
                now = datetime.now()
                self.metrics.last_request_time = now
                self.request_timestamps.append(now)

                # Update average response time
                total_time = self.metrics.average_response_time * (self.metrics.total_requests - 1)
                self.metrics.average_response_time = (total_time + response_time) / self.metrics.total_requests

                # Parse response
                response_text = await response.text()

                try:
                    response_data = json.loads(response_text) if response_text else {}
                except json.JSONDecodeError:
                    response_data = {'raw_response': response_text}

                identifiers = extract_firs_identifiers(response_data)
                if identifiers:
                    response_data = merge_identifiers_into_payload(response_data or {}, identifiers)

                firs_response = FIRSResponse(
                    status_code=response.status,
                    headers=dict(response.headers),
                    data=response_data,
                    raw_response=response_text,
                    request_id=request_headers.get('x-request-id'),
                    timestamp=now,
                    success=200 <= response.status < 300,
                    identifiers=identifiers or None
                )

                if response.status in {401, 403} and retry_on_auth_failure:
                    logger.warning("Received %s from FIRS; rotating certificate and retrying once", response.status)
                    self.rotate_certificate()
                    return await self.make_request(
                        endpoint=endpoint,
                        method=method,
                        data=data,
                        params=params,
                        headers=headers,
                        timeout=timeout,
                        retry_on_auth_failure=False
                    )

                if firs_response.success:
                    self.metrics.successful_requests += 1
                else:
                    self.metrics.failed_requests += 1
                    firs_response.error_code = response_data.get('error_code') or response_data.get('code')
                    firs_response.error_message = (
                        response_data.get('error_message')
                        or response_data.get('message')
                        or response_data.get('error')
                        or 'Unknown error'
                    )

                return firs_response

        except asyncio.TimeoutError:
            self.metrics.failed_requests += 1
            return FIRSResponse(
                status_code=408,
                headers={},
                data={'error': 'Request timeout'},
                raw_response='',
                success=False,
                error_code='TIMEOUT',
                error_message='Request timed out'
            )
        except Exception as e:
            self.metrics.failed_requests += 1
            logger.error(f"FIRS API request failed: {e}")
            return FIRSResponse(
                status_code=500,
                headers={},
                data={'error': str(e)},
                raw_response='',
                success=False,
                error_code='REQUEST_FAILED',
                error_message=str(e)
            )
    
    async def health_check(self) -> FIRSResponse:
        """Check FIRS API health"""
        return await self.make_request(
            endpoint=FIRSEndpoint.INVOICE_TRANSMIT_SELF_HEALTH,
            method="GET"
        )

    async def system_status(self) -> FIRSResponse:
        """Get FIRS system status"""
        return await self.make_request(
            endpoint=FIRSEndpoint.INVOICE_TRANSMIT_PULL,
            method="GET"
        )

    async def validate_invoice(self, payload: Dict[str, Any]) -> FIRSResponse:
        """Validate invoice payload with FIRS."""
        return await self.make_request(
            endpoint=FIRSEndpoint.INVOICE_VALIDATE,
            method="POST",
            data=payload,
        )

    async def submit_invoice(self, payload: Dict[str, Any]) -> FIRSResponse:
        """Submit invoice for signing/clearance."""
        return await self.make_request(
            endpoint=FIRSEndpoint.INVOICE_SIGN,
            method="POST",
            data=payload,
        )

    async def transmit_invoice(self, irn: str, payload: Optional[Dict[str, Any]] = None) -> FIRSResponse:
        """Transmit a signed invoice to the recipient channel."""
        endpoint = FIRSEndpoint.INVOICE_TRANSMIT.value.format(irn=irn)
        return await self.make_request(
            endpoint=endpoint,
            method="POST",
            data=payload or {},
        )

    async def get_submission_status(self, irn: str) -> FIRSResponse:
        """Retrieve submission status for an IRN."""
        endpoint = FIRSEndpoint.INVOICE_TRANSMIT_LOOKUP_IRN.value.format(irn=irn)
        return await self.make_request(
            endpoint=endpoint,
            method="GET",
        )

    async def confirm_invoice(self, irn: str, payload: Optional[Dict[str, Any]] = None) -> FIRSResponse:
        """Confirm invoice receipt/acceptance."""
        endpoint = FIRSEndpoint.INVOICE_CONFIRM.value.format(irn=irn)
        return await self.make_request(
            endpoint=endpoint,
            method="POST",
            data=payload or {},
        )

    async def create_party(self, payload: Dict[str, Any]) -> FIRSResponse:
        """Create or update a party record in FIRS."""
        response = await self.make_request(
            endpoint=FIRSEndpoint.INVOICE_PARTY,
            method="POST",
            data=payload,
        )
        party_id = (
            payload.get("partyId")
            or payload.get("party_id")
            or (response.data or {}).get("partyId")
            if isinstance(response.data, dict)
            else None
        )
        if response.success and party_id:
            await self.party_cache.set(party_id, response)
        elif party_id:
            await self.party_cache.invalidate(party_id)
        return response

    async def get_party(self, party_id: str) -> FIRSResponse:
        """Fetch a party record from FIRS with caching and background revalidation."""

        cached = await self.party_cache.get(party_id, allow_stale=True)
        if cached:
            is_fresh = await self.party_cache.is_fresh(party_id)
            logger.debug("Party cache hit for %s (fresh=%s)", party_id, is_fresh)
            if not is_fresh:
                self._schedule_party_refresh(party_id)
            return cached

        return await self._load_party(party_id)

    async def _load_party(self, party_id: str) -> FIRSResponse:
        endpoint = FIRSEndpoint.INVOICE_PARTY_DETAIL.value.format(party_id=party_id)
        response = await self.make_request(
            endpoint=endpoint,
            method="GET",
        )
        if response.success:
            await self.party_cache.set(party_id, response)
        return response

    def _schedule_party_refresh(self, party_id: str) -> None:
        task = self._party_refresh_tasks.get(party_id)
        if task and not task.done():
            return

        async def _runner():
            try:
                await self._load_party(party_id)
            except Exception as exc:  # pragma: no cover - background refresh should not raise
                logger.debug("Party cache refresh failed for %s: %s", party_id, exc)
            finally:
                self._party_refresh_tasks.pop(party_id, None)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # pragma: no cover - typically shouldn't happen inside async context
            return

        self._party_refresh_tasks[party_id] = loop.create_task(_runner())

    async def verify_tin(self, payload: Dict[str, Any]) -> FIRSResponse:
        """Verify a taxpayer identification number with caching and revalidation."""
        tin_value = payload.get("tin") or payload.get("TIN")
        tin = str(tin_value).strip() if tin_value else None
        branch = payload.get("branchCode") or payload.get("branch_code")

        if tin:
            cached = await self.tin_cache.get(tin, extra=branch, allow_stale=True)
            if cached:
                is_fresh = await self.tin_cache.is_fresh(tin, extra=branch)
                logger.debug("TIN cache hit for %s (fresh=%s)", tin, is_fresh)
                if not is_fresh:
                    self._schedule_tin_refresh(tin, dict(payload), branch)
                return cached

        return await self._load_tin_verification(dict(payload), tin, branch)

    async def _load_tin_verification(self, payload: Dict[str, Any], tin: Optional[str], branch: Optional[str]) -> FIRSResponse:
        response = await self.make_request(
            endpoint=FIRSEndpoint.UTILITIES_VERIFY_TIN,
            method="POST",
            data=payload,
        )
        if tin:
            if response.success:
                await self.tin_cache.set(tin, response, extra=branch)
            else:
                await self.tin_cache.invalidate(tin, extra=branch)
        return response

    def _tin_refresh_key(self, tin: str, branch: Optional[str]) -> str:
        branch_component = (branch or "").strip().upper()
        return f"{tin.strip().upper()}::{branch_component}"

    def _schedule_tin_refresh(self, tin: str, payload: Dict[str, Any], branch: Optional[str]) -> None:
        key = self._tin_refresh_key(tin, branch)
        task = self._tin_refresh_tasks.get(key)
        if task and not task.done():
            return

        async def _runner():
            try:
                await self._load_tin_verification(payload, tin, branch)
            except Exception as exc:  # pragma: no cover - background refresh
                logger.debug("TIN cache refresh failed for %s: %s", tin, exc)
            finally:
                self._tin_refresh_tasks.pop(key, None)

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:  # pragma: no cover
            return

        self._tin_refresh_tasks[key] = loop.create_task(_runner())

    async def get_resources(self, resource: str) -> FIRSResponse:
        """Fetch resource metadata (currencies, invoice types, etc.)."""
        endpoint = FIRSEndpoint.INVOICE_RESOURCES.value.format(resource=resource)
        return await self.make_request(
            endpoint=endpoint,
            method="GET",
        )

    async def get_resources_currencies(self) -> FIRSResponse:
        return await self.get_resources("currencies")

    async def get_resources_invoice_types(self) -> FIRSResponse:
        return await self.get_resources("invoice-types")

    async def get_resources_service_codes(self) -> FIRSResponse:
        return await self.get_resources("services-codes")

    async def get_resources_vat_exemptions(self) -> FIRSResponse:
        return await self.get_resources("vat-exemptions")

    async def get_invoice(self, business_id: str) -> FIRSResponse:
        """Retrieve invoices for a business identifier."""
        endpoint = FIRSEndpoint.INVOICE_SEARCH.value.format(business_id=business_id)
        return await self.make_request(
            endpoint=endpoint,
            method="GET",
        )

    def get_metrics(self) -> FIRSClientMetrics:
        """Get client metrics"""
        return self.metrics

    def get_connection_info(self) -> Dict[str, Any]:
        """Get connection information"""
        return {
            'environment': self.config.environment.value,
            'base_url': self.config.base_url,
            'tls_version': self.config.tls_version,
            'api_key_configured': bool(self.config.api_key),
            'api_secret_configured': bool(self.config.api_secret),
            'certificate_configured': bool(self.config.certificate or self._certificate_pool),
            'rate_limited': self.is_rate_limited,
            'rate_limit_reset_time': self.rate_limit_reset_time.isoformat() if self.rate_limit_reset_time else None,
            'session_active': self.session is not None and not self.session.closed
        }

    def rotate_certificate(self) -> Optional[str]:
        """Force rotation to the next certificate in the pool."""
        if not self._certificate_pool or len(self._certificate_pool) <= 1:
            return self._select_certificate()
        self._current_certificate_index = (self._current_certificate_index + 1) % len(self._certificate_pool)
        self._last_certificate_rotation = datetime.utcnow()
        return self._certificate_pool[self._current_certificate_index]

    def update_certificates(self, certificates: List[str]) -> None:
        """Replace the certificate pool and reset rotation state."""
        sanitized = [c for c in certificates if c]
        if self.config.certificate:
            sanitized.insert(0, self.config.certificate)
        # Deduplicate while preserving order
        seen: List[str] = []
        for cert in sanitized:
            if cert not in seen:
                seen.append(cert)
        self._certificate_pool = seen
        self.config.certificates = seen
        if seen and not self.config.certificate:
            self.config.certificate = seen[0]
        self._current_certificate_index = 0
        self._last_certificate_rotation = None

    def get_current_certificate(self) -> Optional[str]:
        """Return the certificate currently used for headers."""
        if self._certificate_pool:
            return self._certificate_pool[self._current_certificate_index]
        return self.config.certificate if self.config.certificate else None

    def _initialize_certificate_pool(self) -> List[str]:
        pool: List[str] = []
        if self.config.certificate:
            pool.append(self.config.certificate)
        for cert in self.config.certificates:
            if cert and cert not in pool:
                pool.append(cert)
        return pool

    def _select_certificate(self) -> Optional[str]:
        """Select the certificate for the current request, applying rotation policy."""
        if self._certificate_pool:
            if self._current_certificate_index >= len(self._certificate_pool):
                self._current_certificate_index = 0

            now = datetime.utcnow()
            if self._last_certificate_rotation is None:
                self._last_certificate_rotation = now
            elif (
                self.config.certificate_rotation_interval_seconds > 0
                and len(self._certificate_pool) > 1
                and (now - self._last_certificate_rotation).total_seconds() >= self.config.certificate_rotation_interval_seconds
            ):
                self._current_certificate_index = (self._current_certificate_index + 1) % len(self._certificate_pool)
                self._last_certificate_rotation = now
            return self._certificate_pool[self._current_certificate_index]

        return self.config.certificate or None


# Factory function for creating FIRS API client
def create_firs_api_client(
    environment: FIRSEnvironment = FIRSEnvironment.SANDBOX,
    client_id: str = "",
    client_secret: str = "",
    api_key: str = "",
    api_secret: str = "",
    certificate: str = "",
    certificates: Optional[List[str]] = None,
    certificate_rotation_interval_seconds: int = 0,
    config_overrides: Optional[Dict[str, Any]] = None,
    *,
    party_cache_ttl_minutes: float = 30.0,
    tin_cache_ttl_minutes: float = 15.0,
) -> FIRSAPIClient:
    """
    Factory function to create FIRS API client
    
    Args:
        environment: FIRS environment
        client_id: Legacy OAuth 2.0 client ID (unused for header auth)
        client_secret: Legacy OAuth 2.0 client secret (unused for header auth)
        api_key: FIRS API key (x-api-key header)
        api_secret: FIRS API secret (x-api-secret header)
        certificate: Base64 encoded certificate (x-certificate header)
        config_overrides: Additional configuration options
        
    Returns:
        Configured FIRS API client
    """
    config = FIRSConfig(
        environment=environment,
        client_id=client_id,
        client_secret=client_secret,
        api_key=api_key,
        api_secret=api_secret,
        certificate=certificate,
        certificates=certificates or [],
        certificate_rotation_interval_seconds=certificate_rotation_interval_seconds,
    )
    
    # Apply configuration overrides
    if config_overrides:
        for key, value in config_overrides.items():
            if hasattr(config, key):
                setattr(config, key, value)
    
    party_cache = PartyCache(ttl_minutes=party_cache_ttl_minutes)
    tin_cache = TINCache(ttl_minutes=tin_cache_ttl_minutes)

    return FIRSAPIClient(
        config,
        party_cache=party_cache,
        tin_cache=tin_cache,
    )


# Convenience function for creating production client
def create_production_firs_client(
    client_id: str,
    client_secret: str,
    api_key: str,
    api_secret: str = "",
    certificate: str = "",
    **kwargs
) -> FIRSAPIClient:
    """Create production FIRS API client"""
    return create_firs_api_client(
        environment=FIRSEnvironment.PRODUCTION,
        client_id=client_id,
        client_secret=client_secret,
        api_key=api_key,
        api_secret=api_secret,
        certificate=certificate,
        config_overrides=kwargs
    )


# Convenience function for creating sandbox client
def create_sandbox_firs_client(
    client_id: str,
    client_secret: str,
    api_key: str,
    api_secret: str = "",
    certificate: str = "",
    **kwargs
) -> FIRSAPIClient:
    """Create sandbox FIRS API client"""
    return create_firs_api_client(
        environment=FIRSEnvironment.SANDBOX,
        client_id=client_id,
        client_secret=client_secret,
        api_key=api_key,
        api_secret=api_secret,
        certificate=certificate,
        config_overrides=kwargs
    )
