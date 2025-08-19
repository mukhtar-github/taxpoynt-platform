"""
TaxPoynt Platform - FastAPI Observability Middleware
==================================================
Automatic metrics collection and distributed tracing for FastAPI requests.
Integrates with Phase 4 Prometheus and OpenTelemetry implementations.
"""

import time
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Callable
from urllib.parse import urlparse

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from .prometheus_integration import get_prometheus_integration, record_firs_request
from .opentelemetry_integration import get_opentelemetry_integration, trace_firs_integration, trace_invoice_processing

logger = logging.getLogger(__name__)


class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for automatic observability
    
    Features:
    - Automatic HTTP request metrics (Prometheus)
    - Distributed tracing for all requests (OpenTelemetry)
    - Business-specific metrics and traces
    - Error tracking and monitoring
    - Performance monitoring
    """
    
    def __init__(self, app: ASGIApp, 
                 collect_metrics: bool = True,
                 collect_traces: bool = True,
                 track_business_operations: bool = True):
        super().__init__(app)
        
        self.collect_metrics = collect_metrics
        self.collect_traces = collect_traces
        self.track_business_operations = track_business_operations
        
        # Business operation patterns
        self.business_patterns = {
            "invoice": ["/api/v1/invoices", "/api/v1/einvoice"],
            "firs": ["/api/v1/firs", "/api/firs"],
            "banking": ["/api/v1/banking", "/api/v1/banks"],
            "auth": ["/api/v1/auth"],
            "webhook": ["/api/v1/webhooks"],
            "business_systems": ["/api/v1/erp", "/api/v1/crm", "/api/v1/pos"],
            "health": ["/health", "/api/health"],
            "metrics": ["/metrics"]
        }
        
        logger.info("ObservabilityMiddleware initialized")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with observability collection"""
        start_time = time.time()
        
        # Extract request information
        method = request.method
        url_path = request.url.path
        headers = dict(request.headers)
        
        # Determine service role and business operation
        service_role = self._determine_service_role(url_path)
        business_operation = self._determine_business_operation(url_path)
        
        # Create tracing context
        trace_context = None
        if self.collect_traces:
            trace_context = await self._create_trace_context(
                method, url_path, service_role, business_operation, headers
            )
        
        try:
            # Process the request
            if trace_context:
                with trace_context as span:
                    response = await self._process_request_with_tracing(
                        request, call_next, span, start_time
                    )
            else:
                response = await call_next(request)
            
            # Calculate request duration
            duration = time.time() - start_time
            
            # Collect metrics
            if self.collect_metrics:
                await self._collect_request_metrics(
                    method, url_path, response.status_code, 
                    duration, service_role, business_operation
                )
            
            # Add observability headers
            self._add_observability_headers(response, trace_context)
            
            return response
            
        except Exception as e:
            # Calculate duration for failed requests
            duration = time.time() - start_time
            
            # Record error metrics
            if self.collect_metrics:
                await self._collect_error_metrics(
                    method, url_path, 500, duration, service_role, str(e)
                )
            
            # Record error in trace
            if trace_context and hasattr(trace_context, 'record_exception'):
                trace_context.record_exception(e)
            
            logger.error(f"Request error: {method} {url_path} - {e}")
            raise
    
    def _determine_service_role(self, url_path: str) -> str:
        """Determine service role based on URL path"""
        if url_path.startswith('/api/v1/si/') or 'erp' in url_path or 'crm' in url_path:
            return "si_services"
        elif url_path.startswith('/api/v1/app/') or 'firs' in url_path or 'einvoice' in url_path:
            return "app_services"
        elif url_path.startswith('/api/v1/hybrid/') or 'analytics' in url_path or 'billing' in url_path:
            return "hybrid_services"
        elif url_path.startswith('/api/v1/auth/') or url_path.startswith('/health'):
            return "core_platform"
        else:
            return "unknown"
    
    def _determine_business_operation(self, url_path: str) -> str:
        """Determine business operation type"""
        for operation, patterns in self.business_patterns.items():
            for pattern in patterns:
                if pattern in url_path:
                    return operation
        return "other"
    
    async def _create_trace_context(self, method: str, url_path: str, 
                                  service_role: str, business_operation: str,
                                  headers: Dict[str, str]):
        """Create appropriate tracing context"""
        otel_integration = get_opentelemetry_integration()
        if not otel_integration:
            return None
        
        # Extract trace context from headers
        otel_integration.extract_trace_context(headers)
        
        # Create business-specific spans
        if business_operation == "invoice" and "einvoice" in url_path:
            # Extract invoice context if available
            invoice_id = headers.get("x-invoice-id", "unknown")
            invoice_type = headers.get("x-invoice-type", "standard")
            customer_id = headers.get("x-customer-id", "unknown")
            
            return await trace_invoice_processing(
                invoice_id, invoice_type, customer_id, 
                f"{method.lower()}_request"
            )
            
        elif business_operation == "firs":
            # Extract FIRS context
            endpoint = url_path
            operation = f"{method.lower()}_firs_api"
            customer_id = headers.get("x-customer-id")
            
            return await trace_firs_integration(endpoint, operation, customer_id)
        
        else:
            # Generic HTTP request span
            return otel_integration.create_span(
                f"HTTP {method} {url_path}",
                attributes={
                    "http.method": method,
                    "http.url": url_path,
                    "http.scheme": "https",
                    "taxpoynt.service_role": service_role,
                    "taxpoynt.business_operation": business_operation,
                    "http.user_agent": headers.get("user-agent", "unknown")
                }
            )
    
    async def _process_request_with_tracing(self, request: Request, call_next: Callable,
                                          span, start_time: float) -> Response:
        """Process request with active tracing span"""
        try:
            # Add request attributes to span
            span.set_attribute("http.request.size", len(await request.body()) if hasattr(request, 'body') else 0)
            
            # Process the request
            response = await call_next(request)
            
            # Add response attributes
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("http.response.size", len(getattr(response, 'body', b'')))
            
            # Set span status based on HTTP status
            from opentelemetry.trace.status import StatusCode
            if response.status_code >= 400:
                span.set_status(StatusCode.ERROR, f"HTTP {response.status_code}")
            else:
                span.set_status(StatusCode.OK)
            
            return response
            
        except Exception as e:
            span.record_exception(e)
            raise
    
    async def _collect_request_metrics(self, method: str, url_path: str, 
                                     status_code: int, duration: float,
                                     service_role: str, business_operation: str):
        """Collect Prometheus metrics for the request"""
        prometheus_integration = get_prometheus_integration()
        if not prometheus_integration:
            return
        
        try:
            # Standard HTTP request metrics
            prometheus_integration.record_metric(
                "taxpoynt_http_requests_total",
                1,
                {
                    "method": method,
                    "endpoint": self._normalize_endpoint(url_path),
                    "status_code": str(status_code),
                    "service_role": service_role
                }
            )
            
            prometheus_integration.record_metric(
                "taxpoynt_http_request_duration_seconds",
                duration,
                {
                    "method": method,
                    "endpoint": self._normalize_endpoint(url_path),
                    "service_role": service_role
                }
            )
            
            # Business-specific metrics
            if business_operation == "firs" and self.track_business_operations:
                await record_firs_request(
                    service_name="taxpoynt_platform",
                    endpoint=url_path,
                    operation=f"{method.lower()}_request",
                    status_code=status_code,
                    duration=duration
                )
            
        except Exception as e:
            logger.error(f"Error collecting request metrics: {e}")
    
    async def _collect_error_metrics(self, method: str, url_path: str,
                                   status_code: int, duration: float,
                                   service_role: str, error_message: str):
        """Collect error-specific metrics"""
        prometheus_integration = get_prometheus_integration()
        if not prometheus_integration:
            return
        
        try:
            # Error request metrics
            prometheus_integration.record_metric(
                "taxpoynt_http_requests_total",
                1,
                {
                    "method": method,
                    "endpoint": self._normalize_endpoint(url_path),
                    "status_code": str(status_code),
                    "service_role": service_role
                }
            )
            
            # Error-specific counter
            prometheus_integration.record_metric(
                "taxpoynt_http_errors_total",
                1,
                {
                    "method": method,
                    "endpoint": self._normalize_endpoint(url_path),
                    "service_role": service_role,
                    "error_type": "exception"
                }
            )
            
        except Exception as e:
            logger.error(f"Error collecting error metrics: {e}")
    
    def _normalize_endpoint(self, url_path: str) -> str:
        """Normalize endpoint path for metrics (remove IDs)"""
        import re
        
        # Replace UUIDs and numeric IDs with placeholders
        normalized = re.sub(r'/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '/{uuid}', url_path)
        normalized = re.sub(r'/\d+', '/{id}', normalized)
        
        # Limit to known patterns to avoid cardinality explosion
        if len(normalized) > 100:
            normalized = normalized[:100] + "..."
        
        return normalized
    
    def _add_observability_headers(self, response: Response, trace_context):
        """Add observability headers to response"""
        try:
            # Add trace ID if available
            if trace_context and hasattr(trace_context, 'span') and trace_context.span:
                trace_id = format(trace_context.span.get_span_context().trace_id, '032x')
                response.headers["X-Trace-ID"] = trace_id
            
            # Add platform identifier
            response.headers["X-TaxPoynt-Platform"] = "v1.0.0"
            response.headers["X-Observability"] = "prometheus,opentelemetry"
            
        except Exception as e:
            logger.error(f"Error adding observability headers: {e}")


def create_observability_middleware(
    collect_metrics: bool = True,
    collect_traces: bool = True,
    track_business_operations: bool = True
) -> ObservabilityMiddleware:
    """Factory function to create observability middleware"""
    return lambda app: ObservabilityMiddleware(
        app,
        collect_metrics=collect_metrics,
        collect_traces=collect_traces,
        track_business_operations=track_business_operations
    )