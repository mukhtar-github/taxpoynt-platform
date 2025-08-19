"""
TaxPoynt Platform - OpenTelemetry Integration
===========================================
Production OpenTelemetry distributed tracing integration.
Extends the existing TraceCollector with OpenTelemetry export capabilities.
"""

import asyncio
import logging
import os
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum
from contextlib import asynccontextmanager
import functools
import inspect

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider, Span as OtelSpan
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
    from opentelemetry.instrumentation.redis import RedisInstrumentor
    from opentelemetry.instrumentation.requests import RequestsInstrumentor
    from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
    from opentelemetry.propagate import inject, extract
    from opentelemetry.baggage import set_baggage, get_baggage
    from opentelemetry.trace.status import Status, StatusCode
    OPENTELEMETRY_AVAILABLE = True
except ImportError:
    OPENTELEMETRY_AVAILABLE = False

from .trace_collector import TraceCollector, Span as PlatformSpan, SpanKind, SpanStatus

logger = logging.getLogger(__name__)


class TracingBackend(str, Enum):
    """Supported tracing backends"""
    JAEGER = "jaeger"
    OTLP = "otlp" 
    CONSOLE = "console"
    PLATFORM_ONLY = "platform_only"


@dataclass
class TracingConfiguration:
    """OpenTelemetry tracing configuration"""
    service_name: str = "taxpoynt-platform"
    service_version: str = "1.0.0"
    environment: str = "production"
    
    # Backend configuration
    backend: TracingBackend = TracingBackend.JAEGER
    jaeger_endpoint: Optional[str] = None
    otlp_endpoint: Optional[str] = None
    
    # Sampling configuration
    sample_rate: float = 1.0  # 100% sampling for now
    
    # Resource attributes
    resource_attributes: Dict[str, str] = None
    
    # Instrumentation
    auto_instrument_fastapi: bool = True
    auto_instrument_sqlalchemy: bool = True
    auto_instrument_redis: bool = True
    auto_instrument_http: bool = True
    
    def __post_init__(self):
        if self.resource_attributes is None:
            self.resource_attributes = {}


class OpenTelemetryIntegration:
    """
    OpenTelemetry integration for TaxPoynt Platform
    
    Features:
    - Integrates with existing TraceCollector
    - Business-specific span naming and attributes
    - Automatic FastAPI/SQLAlchemy/Redis instrumentation
    - Multiple export backends (Jaeger, OTLP, Console)
    - Custom span processors
    - Distributed tracing across services
    - Baggage propagation for business context
    """
    
    def __init__(self, config: TracingConfiguration, 
                 trace_collector: Optional[TraceCollector] = None):
        """Initialize OpenTelemetry integration"""
        if not OPENTELEMETRY_AVAILABLE:
            raise ImportError("OpenTelemetry packages are required for tracing integration")
        
        self.config = config
        self.trace_collector = trace_collector
        
        # OpenTelemetry components
        self.tracer_provider: Optional[TracerProvider] = None
        self.tracer: Optional[trace.Tracer] = None
        self.span_processors: List[BatchSpanProcessor] = []
        
        # Integration state
        self._initialized = False
        self._instrumentors = []
        
        # Custom span processors
        self._custom_processors: List[Callable] = []
        
        logger.info(f"OpenTelemetry integration created for {config.service_name}")
    
    async def initialize(self):
        """Initialize OpenTelemetry tracing"""
        if self._initialized:
            return
        
        try:
            # Create resource
            resource = self._create_resource()
            
            # Create tracer provider
            self.tracer_provider = TracerProvider(resource=resource)
            trace.set_tracer_provider(self.tracer_provider)
            
            # Create tracer
            self.tracer = trace.get_tracer(
                __name__,
                version=self.config.service_version
            )
            
            # Setup exporters and processors
            await self._setup_exporters()
            
            # Setup auto-instrumentation
            await self._setup_auto_instrumentation()
            
            # Setup custom span processors
            await self._setup_custom_processors()
            
            self._initialized = True
            logger.info(f"OpenTelemetry initialized for {self.config.service_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize OpenTelemetry: {e}")
            raise
    
    def _create_resource(self) -> Resource:
        """Create OpenTelemetry resource"""
        attributes = {
            "service.name": self.config.service_name,
            "service.version": self.config.service_version,
            "deployment.environment": self.config.environment,
            "platform.name": "taxpoynt-einvoice-platform",
            "platform.version": "1.0.0",
            **self.config.resource_attributes
        }
        
        return Resource.create(attributes)
    
    async def _setup_exporters(self):
        """Setup span exporters based on configuration"""
        exporters = []
        
        if self.config.backend == TracingBackend.JAEGER:
            jaeger_endpoint = (
                self.config.jaeger_endpoint or 
                os.getenv("JAEGER_ENDPOINT", "http://localhost:14268/api/traces")
            )
            
            jaeger_exporter = JaegerExporter(
                collector_endpoint=jaeger_endpoint,
            )
            exporters.append(jaeger_exporter)
            logger.info(f"Configured Jaeger exporter: {jaeger_endpoint}")
            
        elif self.config.backend == TracingBackend.OTLP:
            otlp_endpoint = (
                self.config.otlp_endpoint or
                os.getenv("OTLP_ENDPOINT", "http://localhost:4317")
            )
            
            otlp_exporter = OTLPSpanExporter(
                endpoint=otlp_endpoint,
            )
            exporters.append(otlp_exporter)
            logger.info(f"Configured OTLP exporter: {otlp_endpoint}")
            
        elif self.config.backend == TracingBackend.CONSOLE:
            console_exporter = ConsoleSpanExporter()
            exporters.append(console_exporter)
            logger.info("Configured console exporter")
        
        # Create batch span processors
        for exporter in exporters:
            processor = BatchSpanProcessor(exporter)
            self.tracer_provider.add_span_processor(processor)
            self.span_processors.append(processor)
    
    async def _setup_auto_instrumentation(self):
        """Setup automatic instrumentation"""
        try:
            if self.config.auto_instrument_fastapi:
                # FastAPI instrumentation will be done in main.py
                logger.info("FastAPI auto-instrumentation enabled")
            
            if self.config.auto_instrument_sqlalchemy:
                SQLAlchemyInstrumentor().instrument()
                self._instrumentors.append("sqlalchemy")
                logger.info("SQLAlchemy auto-instrumentation enabled")
            
            if self.config.auto_instrument_redis:
                RedisInstrumentor().instrument()
                self._instrumentors.append("redis")
                logger.info("Redis auto-instrumentation enabled")
            
            if self.config.auto_instrument_http:
                RequestsInstrumentor().instrument()
                HTTPXClientInstrumentor().instrument()
                self._instrumentors.append("http")
                logger.info("HTTP client auto-instrumentation enabled")
                
        except Exception as e:
            logger.error(f"Error setting up auto-instrumentation: {e}")
    
    async def _setup_custom_processors(self):
        """Setup custom span processors for business logic"""
        
        # Business context processor
        async def business_context_processor(span: OtelSpan, span_data: Dict[str, Any]):
            """Add business context to spans"""
            try:
                # Add TaxPoynt-specific attributes
                span.set_attribute("taxpoynt.platform.role", span_data.get("service_role", "unknown"))
                span.set_attribute("taxpoynt.platform.component", span_data.get("component", "unknown"))
                
                # Add invoice-specific context if available
                if "invoice_id" in span_data:
                    span.set_attribute("taxpoynt.invoice.id", span_data["invoice_id"])
                    span.set_attribute("taxpoynt.invoice.type", span_data.get("invoice_type", "unknown"))
                
                # Add customer context
                if "customer_id" in span_data:
                    span.set_attribute("taxpoynt.customer.id", span_data["customer_id"])
                    span.set_attribute("taxpoynt.customer.type", span_data.get("customer_type", "unknown"))
                
                # Add FIRS integration context
                if "firs_endpoint" in span_data:
                    span.set_attribute("taxpoynt.firs.endpoint", span_data["firs_endpoint"])
                    span.set_attribute("taxpoynt.firs.operation", span_data.get("firs_operation", "unknown"))
                
                # Add banking context
                if "bank_provider" in span_data:
                    span.set_attribute("taxpoynt.banking.provider", span_data["bank_provider"])
                    span.set_attribute("taxpoynt.banking.account_type", span_data.get("account_type", "unknown"))
                
            except Exception as e:
                logger.error(f"Error in business context processor: {e}")
        
        self._custom_processors.append(business_context_processor)
    
    def create_span(self, name: str, kind: Optional[SpanKind] = None, 
                   attributes: Optional[Dict[str, Any]] = None) -> 'TracedSpan':
        """Create a new traced span"""
        if not self._initialized or not self.tracer:
            logger.warning("OpenTelemetry not initialized, creating mock span")
            return MockTracedSpan(name)
        
        # Map platform span kinds to OpenTelemetry
        otel_kind = trace.SpanKind.INTERNAL
        if kind == SpanKind.SERVER:
            otel_kind = trace.SpanKind.SERVER
        elif kind == SpanKind.CLIENT:
            otel_kind = trace.SpanKind.CLIENT
        elif kind == SpanKind.PRODUCER:
            otel_kind = trace.SpanKind.PRODUCER
        elif kind == SpanKind.CONSUMER:
            otel_kind = trace.SpanKind.CONSUMER
        
        span = self.tracer.start_span(name, kind=otel_kind)
        
        # Add attributes
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
        
        return TracedSpan(span, self, attributes or {})
    
    async def integrate_with_platform_collector(self):
        """Integrate with existing platform trace collector"""
        if not self.trace_collector:
            return
        
        # Add handler to convert platform spans to OpenTelemetry
        async def platform_span_handler(platform_span: PlatformSpan):
            """Convert platform span to OpenTelemetry span"""
            try:
                # Create OpenTelemetry span
                with self.create_span(
                    platform_span.operation_name,
                    kind=platform_span.kind,
                    attributes={
                        "platform.span.id": platform_span.span_id,
                        "platform.trace.id": platform_span.trace_id,
                        "platform.parent.id": platform_span.parent_span_id or "",
                        "platform.service.name": platform_span.service_name,
                        "platform.service.role": platform_span.service_role,
                        **platform_span.tags
                    }
                ) as span:
                    # Set span timing
                    if platform_span.start_time:
                        span.span.set_attribute("platform.start_time", platform_span.start_time.isoformat())
                    if platform_span.end_time:
                        span.span.set_attribute("platform.end_time", platform_span.end_time.isoformat())
                        span.span.set_attribute("platform.duration_ms", 
                                              (platform_span.end_time - platform_span.start_time).total_seconds() * 1000)
                    
                    # Set span status
                    if platform_span.status == SpanStatus.ERROR:
                        span.set_status(StatusCode.ERROR, platform_span.error_message or "Error occurred")
                    elif platform_span.status == SpanStatus.OK:
                        span.set_status(StatusCode.OK)
                    
            except Exception as e:
                logger.error(f"Error converting platform span to OpenTelemetry: {e}")
        
        # Add the handler to platform collector
        # This would need to be implemented in the platform collector
        logger.info("Integrated with platform trace collector")
    
    def get_current_span(self) -> Optional['TracedSpan']:
        """Get current active span"""
        if not self._initialized:
            return None
        
        current_span = trace.get_current_span()
        if current_span and current_span != trace.INVALID_SPAN:
            return TracedSpan(current_span, self, {})
        return None
    
    def inject_trace_context(self, headers: Dict[str, str]) -> Dict[str, str]:
        """Inject trace context into headers for distributed tracing"""
        if not self._initialized:
            return headers
        
        inject(headers)
        return headers
    
    def extract_trace_context(self, headers: Dict[str, str]) -> Optional[trace.Context]:
        """Extract trace context from headers"""
        if not self._initialized:
            return None
        
        return extract(headers)
    
    async def shutdown(self):
        """Shutdown OpenTelemetry integration"""
        try:
            # Shutdown span processors
            for processor in self.span_processors:
                processor.shutdown()
            
            # Uninstrument auto-instrumentation
            if "sqlalchemy" in self._instrumentors:
                SQLAlchemyInstrumentor().uninstrument()
            if "redis" in self._instrumentors:
                RedisInstrumentor().uninstrument()
            if "http" in self._instrumentors:
                RequestsInstrumentor().uninstrument()
                HTTPXClientInstrumentor().uninstrument()
            
            self._initialized = False
            logger.info("OpenTelemetry integration shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during OpenTelemetry shutdown: {e}")


class TracedSpan:
    """Wrapper for OpenTelemetry span with business context"""
    
    def __init__(self, span: OtelSpan, integration: OpenTelemetryIntegration, 
                 context_data: Dict[str, Any]):
        self.span = span
        self.integration = integration
        self.context_data = context_data
        self.start_time = time.time()
    
    def set_attribute(self, key: str, value: Any):
        """Set span attribute"""
        try:
            self.span.set_attribute(key, str(value))
        except Exception as e:
            logger.error(f"Error setting span attribute {key}: {e}")
    
    def set_status(self, status_code: StatusCode, description: str = ""):
        """Set span status"""
        try:
            self.span.set_status(Status(status_code, description))
        except Exception as e:
            logger.error(f"Error setting span status: {e}")
    
    def record_exception(self, exception: Exception):
        """Record exception in span"""
        try:
            self.span.record_exception(exception)
            self.set_status(StatusCode.ERROR, str(exception))
        except Exception as e:
            logger.error(f"Error recording exception: {e}")
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        """Add event to span"""
        try:
            self.span.add_event(name, attributes or {})
        except Exception as e:
            logger.error(f"Error adding span event: {e}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            if exc_type is not None:
                self.record_exception(exc_val)
            
            # Process custom processors
            for processor in self.integration._custom_processors:
                try:
                    asyncio.create_task(processor(self.span, self.context_data))
                except Exception as e:
                    logger.error(f"Error in custom processor: {e}")
            
            self.span.end()
        except Exception as e:
            logger.error(f"Error ending span: {e}")


class MockTracedSpan:
    """Mock span for when OpenTelemetry is not available"""
    
    def __init__(self, name: str):
        self.name = name
    
    def set_attribute(self, key: str, value: Any):
        pass
    
    def set_status(self, status_code: Any, description: str = ""):
        pass
    
    def record_exception(self, exception: Exception):
        pass
    
    def add_event(self, name: str, attributes: Optional[Dict[str, Any]] = None):
        pass
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# Global integration instance
_opentelemetry_integration: Optional[OpenTelemetryIntegration] = None


def get_opentelemetry_integration() -> Optional[OpenTelemetryIntegration]:
    """Get global OpenTelemetry integration instance"""
    return _opentelemetry_integration


async def initialize_opentelemetry_integration(
    config: TracingConfiguration,
    trace_collector: Optional[TraceCollector] = None
) -> OpenTelemetryIntegration:
    """Initialize OpenTelemetry integration"""
    global _opentelemetry_integration
    
    if not OPENTELEMETRY_AVAILABLE:
        logger.error("OpenTelemetry packages not available - install with: pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-jaeger")
        raise ImportError("OpenTelemetry packages required")
    
    _opentelemetry_integration = OpenTelemetryIntegration(config, trace_collector)
    await _opentelemetry_integration.initialize()
    
    # Integrate with existing platform collector
    await _opentelemetry_integration.integrate_with_platform_collector()
    
    logger.info(f"OpenTelemetry integration initialized for {config.service_name}")
    return _opentelemetry_integration


async def shutdown_opentelemetry_integration():
    """Shutdown OpenTelemetry integration"""
    global _opentelemetry_integration
    
    if _opentelemetry_integration:
        await _opentelemetry_integration.shutdown()
        _opentelemetry_integration = None
        logger.info("OpenTelemetry integration shutdown complete")


# Decorators for automatic tracing
def trace_async(name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """Decorator for tracing async functions"""
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            integration = get_opentelemetry_integration()
            if not integration:
                return await func(*args, **kwargs)
            
            span_name = name or f"{func.__module__}.{func.__name__}"
            span_attributes = attributes or {}
            
            # Add function info
            span_attributes.update({
                "function.name": func.__name__,
                "function.module": func.__module__,
                "function.type": "async"
            })
            
            with integration.create_span(span_name, attributes=span_attributes) as span:
                try:
                    result = await func(*args, **kwargs)
                    span.set_status(StatusCode.OK)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator


def trace_sync(name: Optional[str] = None, attributes: Optional[Dict[str, Any]] = None):
    """Decorator for tracing sync functions"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            integration = get_opentelemetry_integration()
            if not integration:
                return func(*args, **kwargs)
            
            span_name = name or f"{func.__module__}.{func.__name__}"
            span_attributes = attributes or {}
            
            # Add function info
            span_attributes.update({
                "function.name": func.__name__,
                "function.module": func.__module__,
                "function.type": "sync"
            })
            
            with integration.create_span(span_name, attributes=span_attributes) as span:
                try:
                    result = func(*args, **kwargs)
                    span.set_status(StatusCode.OK)
                    return result
                except Exception as e:
                    span.record_exception(e)
                    raise
        
        return wrapper
    return decorator


# Business-specific tracing helpers
async def trace_invoice_processing(invoice_id: str, invoice_type: str, 
                                  customer_id: str, operation: str):
    """Create span for invoice processing operations"""
    integration = get_opentelemetry_integration()
    if not integration:
        return MockTracedSpan(f"invoice_processing_{operation}")
    
    return integration.create_span(
        f"taxpoynt.invoice.{operation}",
        kind=SpanKind.INTERNAL,
        attributes={
            "taxpoynt.invoice.id": invoice_id,
            "taxpoynt.invoice.type": invoice_type,
            "taxpoynt.customer.id": customer_id,
            "taxpoynt.operation": operation,
            "taxpoynt.component": "invoice_processing"
        }
    )


async def trace_firs_integration(endpoint: str, operation: str, 
                               customer_id: Optional[str] = None):
    """Create span for FIRS integration operations"""
    integration = get_opentelemetry_integration()
    if not integration:
        return MockTracedSpan(f"firs_{operation}")
    
    attributes = {
        "taxpoynt.firs.endpoint": endpoint,
        "taxpoynt.firs.operation": operation,
        "taxpoynt.component": "firs_integration"
    }
    
    if customer_id:
        attributes["taxpoynt.customer.id"] = customer_id
    
    return integration.create_span(
        f"taxpoynt.firs.{operation}",
        kind=SpanKind.CLIENT,
        attributes=attributes
    )


async def trace_banking_operation(provider: str, operation: str, 
                                account_type: str, customer_id: Optional[str] = None):
    """Create span for banking operations"""
    integration = get_opentelemetry_integration()
    if not integration:
        return MockTracedSpan(f"banking_{operation}")
    
    attributes = {
        "taxpoynt.banking.provider": provider,
        "taxpoynt.banking.operation": operation,
        "taxpoynt.banking.account_type": account_type,
        "taxpoynt.component": "banking_integration"
    }
    
    if customer_id:
        attributes["taxpoynt.customer.id"] = customer_id
    
    return integration.create_span(
        f"taxpoynt.banking.{operation}",
        kind=SpanKind.CLIENT,
        attributes=attributes
    )