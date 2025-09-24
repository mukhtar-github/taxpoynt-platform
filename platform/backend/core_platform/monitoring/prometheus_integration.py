"""
TaxPoynt Platform - Prometheus Integration
=========================================
Production Prometheus metrics integration for your existing monitoring system.
Extends the current MetricsAggregator with Prometheus export capabilities.
"""

import asyncio
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum

try:
    from prometheus_client import (
        Counter, Gauge, Histogram, Summary, Info,
        CollectorRegistry, generate_latest, CONTENT_TYPE_LATEST,
        start_http_server, push_to_gateway
    )
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Mock classes for when prometheus_client is not available
    class CollectorRegistry:
        pass
    class Counter:
        pass
    class Gauge:
        pass
    class Histogram:
        pass
    class Summary:
        pass
    class Info:
        pass

from .metrics_aggregator import MetricsAggregator, MetricType, ServiceRole

logger = logging.getLogger(__name__)


class PrometheusMetricsType(str, Enum):
    """Prometheus metric types"""
    COUNTER = "counter"
    GAUGE = "gauge" 
    HISTOGRAM = "histogram"
    SUMMARY = "summary"
    INFO = "info"


@dataclass
class PrometheusMetric:
    """Prometheus metric definition"""
    name: str
    metric_type: PrometheusMetricsType
    description: str
    labels: List[str]
    buckets: Optional[List[float]] = None  # For histograms
    quantiles: Optional[Dict[float, float]] = None  # For summaries


class PrometheusIntegration:
    """
    Prometheus integration for TaxPoynt Platform
    
    Features:
    - Integrates with existing MetricsAggregator
    - Business-specific metrics for e-invoicing
    - Platform performance metrics
    - Role-based service metrics
    - Custom metric registration
    - HTTP metrics endpoint
    - Push gateway support
    """
    
    def __init__(self, metrics_aggregator: Optional[MetricsAggregator] = None,
                 registry: Optional[CollectorRegistry] = None):
        """Initialize Prometheus integration"""
        if not PROMETHEUS_AVAILABLE:
            raise ImportError("prometheus_client package is required for Prometheus integration")
        
        self.metrics_aggregator = metrics_aggregator
        self.registry = registry or CollectorRegistry()
        
        # Prometheus metrics storage
        self.prometheus_metrics: Dict[str, Any] = {}
        self.metric_definitions: Dict[str, PrometheusMetric] = {}
        
        # Configuration
        self.metrics_port = 9090
        self.metrics_path = "/metrics"
        self.push_gateway_url = None
        self.push_job_name = "taxpoynt_platform"
        
        # Background tasks
        self._metrics_sync_task = None
        self._http_server_task = None
        self._running = False
        
        # Initialize core business metrics
        self._initialize_business_metrics()
        self._initialize_platform_metrics()
        
        logger.info("Prometheus integration initialized")
    
    def _initialize_business_metrics(self):
        """Initialize business-specific metrics for e-invoicing"""
        
        # E-Invoice Processing Metrics
        self.register_metric(PrometheusMetric(
            name="taxpoynt_invoices_total",
            metric_type=PrometheusMetricsType.COUNTER,
            description="Total number of e-invoices processed",
            labels=["service_role", "service_name", "status", "invoice_type"]
        ))
        
        self.register_metric(PrometheusMetric(
            name="taxpoynt_invoice_processing_duration_seconds",
            metric_type=PrometheusMetricsType.HISTOGRAM,
            description="Time spent processing e-invoices",
            labels=["service_role", "service_name", "invoice_type"],
            buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0]
        ))
        
        # FIRS Integration Metrics
        self.register_metric(PrometheusMetric(
            name="taxpoynt_firs_requests_total",
            metric_type=PrometheusMetricsType.COUNTER,
            description="Total FIRS API requests",
            labels=["service_name", "endpoint", "status_code", "operation"]
        ))
        
        self.register_metric(PrometheusMetric(
            name="taxpoynt_firs_request_duration_seconds",
            metric_type=PrometheusMetricsType.HISTOGRAM,
            description="FIRS API request duration",
            labels=["endpoint", "operation"],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        ))
        
        # Business System Integration Metrics
        self.register_metric(PrometheusMetric(
            name="taxpoynt_business_integrations_total",
            metric_type=PrometheusMetricsType.COUNTER,
            description="Total business system integration calls",
            labels=["integration_type", "service_name", "status", "operation"]
        ))
        
        # Banking Integration Metrics
        self.register_metric(PrometheusMetric(
            name="taxpoynt_banking_transactions_total",
            metric_type=PrometheusMetricsType.COUNTER,
            description="Total banking transactions processed",
            labels=["provider", "account_type", "status", "transaction_type"]
        ))
        
        # Revenue and Billing Metrics
        self.register_metric(PrometheusMetric(
            name="taxpoynt_revenue_total",
            metric_type=PrometheusMetricsType.COUNTER,
            description="Total platform revenue in kobo",
            labels=["service_tier", "billing_type", "customer_type"]
        ))
        
        # Compliance Metrics
        self.register_metric(PrometheusMetric(
            name="taxpoynt_compliance_checks_total",
            metric_type=PrometheusMetricsType.COUNTER,
            description="Total compliance checks performed",
            labels=["check_type", "status", "regulation"]
        ))
    
    def _initialize_platform_metrics(self):
        """Initialize platform performance metrics"""
        
        # HTTP Request Metrics
        self.register_metric(PrometheusMetric(
            name="taxpoynt_http_requests_total",
            metric_type=PrometheusMetricsType.COUNTER,
            description="Total HTTP requests",
            labels=["method", "endpoint", "status_code", "service_role"]
        ))
        
        self.register_metric(PrometheusMetric(
            name="taxpoynt_http_request_duration_seconds",
            metric_type=PrometheusMetricsType.HISTOGRAM,
            description="HTTP request duration",
            labels=["method", "endpoint", "service_role"],
            buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
        ))
        
        # Database Metrics
        self.register_metric(PrometheusMetric(
            name="taxpoynt_database_connections_active",
            metric_type=PrometheusMetricsType.GAUGE,
            description="Active database connections",
            labels=["pool_name", "database"]
        ))
        # Additional DB pool stats
        self.register_metric(PrometheusMetric(
            name="taxpoynt_database_pool_stats",
            metric_type=PrometheusMetricsType.GAUGE,
            description="DB pool stats by metric",
            labels=["metric"]
        ))
        self.register_metric(PrometheusMetric(
            name="taxpoynt_database_query_stats",
            metric_type=PrometheusMetricsType.GAUGE,
            description="DB query statistics (counts and averages)",
            labels=["metric"]
        ))
        
        self.register_metric(PrometheusMetric(
            name="taxpoynt_database_queries_total",
            metric_type=PrometheusMetricsType.COUNTER,
            description="Total database queries",
            labels=["operation", "table", "status"]
        ))
        
        # Redis Metrics  
        self.register_metric(PrometheusMetric(
            name="taxpoynt_redis_operations_total",
            metric_type=PrometheusMetricsType.COUNTER,
            description="Total Redis operations",
            labels=["operation", "key_pattern", "status"]
        ))
        
        # Message Router Metrics (Phase 3)
        self.register_metric(PrometheusMetric(
            name="taxpoynt_messages_routed_total",
            metric_type=PrometheusMetricsType.COUNTER,
            description="Total messages routed",
            labels=["source_role", "target_role", "message_type", "status"]
        ))
        
        # Circuit Breaker Metrics (Phase 3)
        self.register_metric(PrometheusMetric(
            name="taxpoynt_circuit_breaker_state",
            metric_type=PrometheusMetricsType.GAUGE,
            description="Circuit breaker state (0=closed, 1=open, 2=half-open)",
            labels=["service_name", "circuit_name"]
        ))
        
        # Health Check Metrics (Phase 3)
        health_labels = ["service_role", "service_name", "check_id", "check_type", "priority"]
        self.register_metric(PrometheusMetric(
            name="taxpoynt_health_check_status",
            metric_type=PrometheusMetricsType.GAUGE,
            description="Health check status (1=healthy, 0=unhealthy)",
            labels=health_labels
        ))
        metric_labels = ["service_role", "service_name", "check_id"]
        for metric_name, description in [
            ("taxpoynt_health_check_duration_ms", "Health check duration in milliseconds"),
            ("taxpoynt_health_check_response_time_ms", "Health check response time in milliseconds"),
            ("taxpoynt_health_check_connection_time_ms", "Health check connection time in milliseconds"),
            ("taxpoynt_health_check_active_connections", "Active connections reported by the health check"),
            ("taxpoynt_health_check_memory_usage_percent", "Memory usage percentage reported by the health check"),
        ]:
            self.register_metric(PrometheusMetric(
                name=metric_name,
                metric_type=PrometheusMetricsType.GAUGE,
                description=description,
                labels=metric_labels
            ))
        
        # Scaling Metrics (Phase 3)
        self.register_metric(PrometheusMetric(
            name="taxpoynt_active_instances",
            metric_type=PrometheusMetricsType.GAUGE,
            description="Number of active service instances",
            labels=["service_type", "coordinator_id"]
        ))
        # Repository query KPIs
        self.register_metric(PrometheusMetric(
            name="taxpoynt_repository_queries_total",
            metric_type=PrometheusMetricsType.COUNTER,
            description="Total repository queries by method/table/outcome",
            labels=["repository", "method", "table", "outcome"]
        ))
        self.register_metric(PrometheusMetric(
            name="taxpoynt_repository_query_duration_seconds",
            metric_type=PrometheusMetricsType.HISTOGRAM,
            description="Repository query duration",
            labels=["repository", "method", "table"],
            buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
        ))
        # Tenant cache metrics
        self.register_metric(PrometheusMetric(
            name="taxpoynt_tenant_cache_stats",
            metric_type=PrometheusMetricsType.GAUGE,
            description="Tenant cache hit/miss stats",
            labels=["metric"]
        ))
        # Outbound AP delivery/queue metrics
        self.register_metric(PrometheusMetric(
            name="taxpoynt_ap_outbound_current_queue_size",
            metric_type=PrometheusMetricsType.GAUGE,
            description="Current size of ap_outbound queue",
            labels=["queue"]
        ))
        self.register_metric(PrometheusMetric(
            name="taxpoynt_ap_outbound_dead_letter_count",
            metric_type=PrometheusMetricsType.GAUGE,
            description="Current size of dead_letter queue (AP outbound)",
            labels=["queue"]
        ))
        self.register_metric(PrometheusMetric(
            name="taxpoynt_ap_outbound_delivery_success_total",
            metric_type=PrometheusMetricsType.COUNTER,
            description="Total successful outbound AP deliveries",
            labels=["status_code"]
        ))
        self.register_metric(PrometheusMetric(
            name="taxpoynt_ap_outbound_delivery_failure_total",
            metric_type=PrometheusMetricsType.COUNTER,
            description="Total failed outbound AP deliveries",
            labels=["error_type", "status_code"]
        ))
        self.register_metric(PrometheusMetric(
            name="taxpoynt_ap_outbound_oldest_message_age_seconds",
            metric_type=PrometheusMetricsType.GAUGE,
            description="Age in seconds of the oldest queued/scheduled outbound message",
            labels=[]
        ))
        # Outbound POST attempts and latency
        self.register_metric(PrometheusMetric(
            name="taxpoynt_ap_outbound_delivery_attempts_total",
            metric_type=PrometheusMetricsType.COUNTER,
            description="Total outbound POST attempts to AP endpoints",
            labels=[]
        ))
        self.register_metric(PrometheusMetric(
            name="taxpoynt_ap_outbound_delivery_duration_seconds",
            metric_type=PrometheusMetricsType.HISTOGRAM,
            description="Duration of outbound POST requests",
            labels=["status_code"],
            buckets=[0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0]
        ))
        # Resolve attempts and duration
        self.register_metric(PrometheusMetric(
            name="taxpoynt_ap_outbound_resolve_attempts_total",
            metric_type=PrometheusMetricsType.COUNTER,
            description="Total attempts to resolve AP participant identifiers",
            labels=["outcome"]
        ))
        self.register_metric(PrometheusMetric(
            name="taxpoynt_ap_outbound_resolve_duration_seconds",
            metric_type=PrometheusMetricsType.HISTOGRAM,
            description="Duration of resolve calls for AP participants",
            labels=["outcome"],
            buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0]
        ))
        # Delivery body size distribution
        self.register_metric(PrometheusMetric(
            name="taxpoynt_ap_outbound_delivery_body_bytes",
            metric_type=PrometheusMetricsType.HISTOGRAM,
            description="Size of outbound delivery bodies (bytes)",
            labels=[],
            buckets=[512, 1024, 2048, 4096, 8192, 16384, 65536, 262144, 1048576]
        ))
    
    def register_metric(self, metric_definition: PrometheusMetric):
        """Register a new Prometheus metric"""
        try:
            metric_name = metric_definition.name
            
            if metric_definition.metric_type == PrometheusMetricsType.COUNTER:
                prometheus_metric = Counter(
                    metric_name,
                    metric_definition.description,
                    metric_definition.labels,
                    registry=self.registry
                )
            elif metric_definition.metric_type == PrometheusMetricsType.GAUGE:
                prometheus_metric = Gauge(
                    metric_name,
                    metric_definition.description,
                    metric_definition.labels,
                    registry=self.registry
                )
            elif metric_definition.metric_type == PrometheusMetricsType.HISTOGRAM:
                prometheus_metric = Histogram(
                    metric_name,
                    metric_definition.description,
                    metric_definition.labels,
                    buckets=metric_definition.buckets or [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, float("inf")],
                    registry=self.registry
                )
            elif metric_definition.metric_type == PrometheusMetricsType.SUMMARY:
                prometheus_metric = Summary(
                    metric_name,
                    metric_definition.description,
                    metric_definition.labels,
                    quantiles=metric_definition.quantiles or {0.5: 0.05, 0.9: 0.01, 0.99: 0.001},
                    registry=self.registry
                )
            elif metric_definition.metric_type == PrometheusMetricsType.INFO:
                prometheus_metric = Info(
                    metric_name,
                    metric_definition.description,
                    registry=self.registry
                )
            else:
                raise ValueError(f"Unsupported metric type: {metric_definition.metric_type}")
            
            self.prometheus_metrics[metric_name] = prometheus_metric
            self.metric_definitions[metric_name] = metric_definition
            
            logger.info(f"Registered Prometheus metric: {metric_name}")
            
        except Exception as e:
            logger.error(f"Failed to register Prometheus metric {metric_definition.name}: {e}")
    
    def record_metric(self, metric_name: str, value: float, labels: Optional[Dict[str, str]] = None):
        """Record a metric value"""
        try:
            if metric_name not in self.prometheus_metrics:
                logger.warning(f"Metric {metric_name} not registered")
                return
            
            prometheus_metric = self.prometheus_metrics[metric_name]
            labels = labels or {}
            
            if isinstance(prometheus_metric, Counter):
                if labels:
                    prometheus_metric.labels(**labels).inc(value)
                else:
                    prometheus_metric.inc(value)
                    
            elif isinstance(prometheus_metric, Gauge):
                if labels:
                    prometheus_metric.labels(**labels).set(value)
                else:
                    prometheus_metric.set(value)
                    
            elif isinstance(prometheus_metric, (Histogram, Summary)):
                if labels:
                    prometheus_metric.labels(**labels).observe(value)
                else:
                    prometheus_metric.observe(value)
            
        except Exception as e:
            logger.error(f"Failed to record metric {metric_name}: {e}")
    
    async def start_metrics_server(self, port: Optional[int] = None):
        """Start HTTP metrics server"""
        port = port or self.metrics_port
        
        try:
            # Start Prometheus HTTP server
            start_http_server(port, registry=self.registry)
            logger.info(f"Prometheus metrics server started on port {port}")
            
            # Start background sync with existing metrics aggregator
            if self.metrics_aggregator:
                await self._start_metrics_sync()
                
            self._running = True
            
        except Exception as e:
            logger.error(f"Failed to start Prometheus metrics server: {e}")
            raise
    
    async def _start_metrics_sync(self):
        """Start background sync with existing metrics aggregator"""
        if self._metrics_sync_task:
            return
        
        self._metrics_sync_task = asyncio.create_task(self._metrics_sync_loop())
        logger.info("Started metrics sync with existing aggregator")
    
    async def _metrics_sync_loop(self):
        """Background loop to sync with existing metrics aggregator"""
        while self._running:
            try:
                await self._sync_aggregator_metrics()
                await self._sync_platform_runtime_metrics()
                await asyncio.sleep(10)  # Sync every 10 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in metrics sync loop: {e}")
                await asyncio.sleep(10)

    async def _sync_platform_runtime_metrics(self):
        """Collect DB pool and tenant cache metrics into Prometheus gauges."""
        try:
            # DB pool metrics
            try:
                from core_platform.data_management.connection_pool import get_database_metrics
                dbm = get_database_metrics()
                pool_stats = dbm.get("pool_statistics", {})
                perf = dbm.get("performance_metrics", {})
                # Pool stats
                for key in ("pool_size", "checked_in", "checked_out", "overflow", "invalid"):
                    val = float(pool_stats.get(key, 0) or 0)
                    self.record_metric("taxpoynt_database_pool_stats", val, {"metric": key})
                # Performance metrics (counts/averages)
                for mkey in ("query_count", "read_queries", "write_queries", "slow_queries", "average_query_time"):
                    val = float(perf.get(mkey, 0) or 0)
                    self.record_metric("taxpoynt_database_query_stats", val, {"metric": mkey})
            except Exception as e:
                logger.debug(f"DB metrics unavailable: {e}")

            # Tenant cache metrics (best-effort)
            try:
                from core_platform.data_management.multi_tenant_manager import get_tenant_manager
                mgr = get_tenant_manager()
                if mgr is not None:
                    # Simulate cache stats via query stats keys
                    stats = getattr(mgr, "_query_stats", {})
                    for k in ("cache_hits", "cache_misses", "tenant_filtered_queries", "total_queries"):
                        val = float(stats.get(k, 0) or 0)
                        self.record_metric("taxpoynt_tenant_cache_stats", val, {"metric": k})
            except Exception as e:
                logger.debug(f"Tenant manager metrics unavailable: {e}")
        except Exception as e:
            logger.error(f"Error syncing platform runtime metrics: {e}")
    
    async def _sync_aggregator_metrics(self):
        """Sync metrics from existing aggregator to Prometheus"""
        if not self.metrics_aggregator:
            return
        
        try:
            # Get current metrics from aggregator
            current_metrics = await self.metrics_aggregator.get_current_metrics()
            
            for metric_data in current_metrics:
                await self._convert_aggregator_metric(metric_data)
                
        except Exception as e:
            logger.error(f"Failed to sync aggregator metrics: {e}")
    
    async def _convert_aggregator_metric(self, metric_data: Dict[str, Any]):
        """Convert aggregator metric to Prometheus format"""
        try:
            metric_name = metric_data.get("name", "")
            value = metric_data.get("value", 0)
            tags = metric_data.get("tags", {})
            metric_type = metric_data.get("type", "")
            service_role = metric_data.get("service_role", "")
            service_name = metric_data.get("service_name", "")
            
            # Add standard labels
            labels = {
                "service_role": str(getattr(service_role, "value", service_role)),
                "service_name": str(service_name),
                **{k: str(v) for k, v in (tags or {}).items() if v is not None}
            }

            # Map to appropriate Prometheus metric
            prometheus_name = f"taxpoynt_{metric_name}"

            # Record the metric
            if prometheus_name not in self.prometheus_metrics:
                label_names = sorted(labels.keys())
                self.register_metric(PrometheusMetric(
                    name=prometheus_name,
                    metric_type=PrometheusMetricsType.GAUGE,
                    description=f"Auto-registered metric for {metric_name}",
                    labels=label_names
                ))

            self.record_metric(prometheus_name, value, labels)
            
        except Exception as e:
            logger.error(f"Failed to convert aggregator metric: {e}")
    
    def get_metrics_output(self) -> str:
        """Get Prometheus metrics output"""
        try:
            return generate_latest(self.registry).decode('utf-8')
        except Exception as e:
            logger.error(f"Failed to generate metrics output: {e}")
            return ""
    
    async def push_to_gateway(self, gateway_url: str, job_name: Optional[str] = None):
        """Push metrics to Prometheus push gateway"""
        if not gateway_url:
            return
        
        job_name = job_name or self.push_job_name
        
        try:
            push_to_gateway(gateway_url, job=job_name, registry=self.registry)
            logger.info(f"Pushed metrics to gateway: {gateway_url}")
        except Exception as e:
            logger.error(f"Failed to push metrics to gateway: {e}")
    
    async def get_prometheus_stats(self) -> Dict[str, Any]:
        """Get Prometheus integration statistics"""
        return {
            "running": self._running,
            "metrics_registered": len(self.prometheus_metrics),
            "metrics_port": self.metrics_port,
            "push_gateway_url": self.push_gateway_url,
            "registry_samples": len(list(self.registry.collect())),
            "sync_with_aggregator": self.metrics_aggregator is not None,
            "registered_metrics": list(self.prometheus_metrics.keys())
        }
    
    async def stop(self):
        """Stop Prometheus integration"""
        self._running = False
        
        if self._metrics_sync_task:
            self._metrics_sync_task.cancel()
            try:
                await self._metrics_sync_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Prometheus integration stopped")


# Global instance
_prometheus_integration: Optional[PrometheusIntegration] = None


def get_prometheus_integration() -> Optional[PrometheusIntegration]:
    """Get global Prometheus integration instance"""
    return _prometheus_integration


async def initialize_prometheus_integration(
    metrics_aggregator: Optional[MetricsAggregator] = None,
    metrics_port: int = 9090,
    auto_start_server: bool = True
) -> PrometheusIntegration:
    """Initialize Prometheus integration"""
    global _prometheus_integration
    
    if not PROMETHEUS_AVAILABLE:
        logger.error("prometheus_client package not available - install with: pip install prometheus-client")
        raise ImportError("prometheus_client package required")
    
    _prometheus_integration = PrometheusIntegration(metrics_aggregator)
    _prometheus_integration.metrics_port = metrics_port
    
    if auto_start_server:
        await _prometheus_integration.start_metrics_server(metrics_port)
    
    logger.info(f"Prometheus integration initialized on port {metrics_port}")
    return _prometheus_integration


async def shutdown_prometheus_integration():
    """Shutdown Prometheus integration"""
    global _prometheus_integration
    
    if _prometheus_integration:
        await _prometheus_integration.stop()
        _prometheus_integration = None
        logger.info("Prometheus integration shutdown complete")


# Convenience functions for recording business metrics
async def record_invoice_processed(service_role: str, service_name: str, 
                                 invoice_type: str, status: str, 
                                 processing_time: Optional[float] = None):
    """Record e-invoice processing metrics"""
    if _prometheus_integration:
        labels = {
            "service_role": service_role,
            "service_name": service_name,
            "status": status,
            "invoice_type": invoice_type
        }
        _prometheus_integration.record_metric("taxpoynt_invoices_total", 1, labels)
        
        if processing_time is not None:
            time_labels = {k: v for k, v in labels.items() if k != "status"}
            _prometheus_integration.record_metric(
                "taxpoynt_invoice_processing_duration_seconds", 
                processing_time, 
                time_labels
            )


async def record_firs_request(service_name: str, endpoint: str, 
                            operation: str, status_code: int, 
                            duration: Optional[float] = None):
    """Record FIRS API request metrics"""
    if _prometheus_integration:
        labels = {
            "service_name": service_name,
            "endpoint": endpoint,
            "status_code": str(status_code),
            "operation": operation
        }
        _prometheus_integration.record_metric("taxpoynt_firs_requests_total", 1, labels)
        
        if duration is not None:
            time_labels = {k: v for k, v in labels.items() if k != "status_code"}
            _prometheus_integration.record_metric(
                "taxpoynt_firs_request_duration_seconds", 
                duration, 
                time_labels
            )


async def record_banking_transaction(provider: str, account_type: str,
                                   transaction_type: str, status: str):
    """Record banking transaction metrics"""
    if _prometheus_integration:
        labels = {
            "provider": provider,
            "account_type": account_type,
            "status": status,
            "transaction_type": transaction_type
        }
        _prometheus_integration.record_metric("taxpoynt_banking_transactions_total", 1, labels)


async def record_revenue(amount_kobo: int, service_tier: str, 
                       billing_type: str, customer_type: str):
    """Record revenue metrics"""
    if _prometheus_integration:
        labels = {
            "service_tier": service_tier,
            "billing_type": billing_type,
            "customer_type": customer_type
        }
        _prometheus_integration.record_metric("taxpoynt_revenue_total", amount_kobo, labels)
