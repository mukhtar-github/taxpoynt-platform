"""Core Platform Sync Monitoring Models"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid


class SyncHealthStatus(Enum):
    """Sync health status types"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    CRITICAL = "critical"
    MAINTENANCE = "maintenance"


class SyncAlertSeverity(Enum):
    """Sync alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class SyncDirection(Enum):
    """Data synchronization directions"""
    BIDIRECTIONAL = "bidirectional"
    SOURCE_TO_TARGET = "source_to_target"
    TARGET_TO_SOURCE = "target_to_source"


@dataclass
class SyncHealth:
    """Synchronization health monitoring"""
    health_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    service_name: str = ""
    component_name: str = ""
    status: SyncHealthStatus = SyncHealthStatus.HEALTHY
    
    # Health metrics
    uptime_seconds: int = 0
    last_sync_success: Optional[datetime] = None
    last_sync_failure: Optional[datetime] = None
    consecutive_failures: int = 0
    success_rate_percentage: float = 100.0
    
    # Performance metrics
    average_sync_duration_ms: float = 0.0
    last_sync_duration_ms: Optional[float] = None
    max_sync_duration_ms: float = 0.0
    min_sync_duration_ms: float = 0.0
    
    # Data metrics
    records_synced: int = 0
    records_failed: int = 0
    data_lag_seconds: Optional[int] = None
    queue_size: int = 0
    
    # System resources
    memory_usage_mb: Optional[float] = None
    cpu_usage_percentage: Optional[float] = None
    disk_usage_mb: Optional[float] = None
    network_latency_ms: Optional[float] = None
    
    # Metadata
    health_check_interval_seconds: int = 60
    last_health_check: datetime = field(default_factory=datetime.now)
    health_check_version: str = "1.0.0"
    additional_metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncAlert:
    """Synchronization alert management"""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    service_name: str = ""
    component_name: str = ""
    alert_type: str = ""
    severity: SyncAlertSeverity = SyncAlertSeverity.INFO
    
    # Alert content
    title: str = ""
    message: str = ""
    description: str = ""
    
    # Alert status
    is_active: bool = True
    is_acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    
    # Alert context
    source_health_id: Optional[str] = None
    related_metrics: Dict[str, Any] = field(default_factory=dict)
    affected_services: List[str] = field(default_factory=list)
    
    # Notification settings
    notification_channels: List[str] = field(default_factory=list)
    escalation_level: int = 1
    auto_resolve: bool = False
    resolve_timeout_minutes: Optional[int] = None
    
    # Timing
    first_occurred: datetime = field(default_factory=datetime.now)
    last_occurred: datetime = field(default_factory=datetime.now)
    occurrence_count: int = 1
    
    # Metadata
    alert_version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    additional_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SyncMetrics:
    """Comprehensive synchronization metrics"""
    metrics_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    service_name: str = ""
    component_name: str = ""
    
    # Time window
    period_start: datetime = field(default_factory=datetime.now)
    period_end: datetime = field(default_factory=datetime.now)
    collection_interval_seconds: int = 300  # 5 minutes
    
    # Sync operations
    total_sync_operations: int = 0
    successful_syncs: int = 0
    failed_syncs: int = 0
    retried_syncs: int = 0
    skipped_syncs: int = 0
    
    # Performance metrics
    total_sync_duration_ms: float = 0.0
    average_sync_duration_ms: float = 0.0
    median_sync_duration_ms: float = 0.0
    p95_sync_duration_ms: float = 0.0
    p99_sync_duration_ms: float = 0.0
    
    # Throughput metrics
    records_per_second: float = 0.0
    bytes_per_second: float = 0.0
    operations_per_minute: float = 0.0
    
    # Data volume
    total_records_processed: int = 0
    total_bytes_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    records_deleted: int = 0
    
    # Error tracking
    error_types: Dict[str, int] = field(default_factory=dict)
    most_common_error: Optional[str] = None
    error_rate_percentage: float = 0.0
    
    # Sync direction metrics
    sync_direction: SyncDirection = SyncDirection.BIDIRECTIONAL
    source_to_target_count: int = 0
    target_to_source_count: int = 0
    
    # Resource usage
    peak_memory_usage_mb: float = 0.0
    average_memory_usage_mb: float = 0.0
    peak_cpu_usage_percentage: float = 0.0
    average_cpu_usage_percentage: float = 0.0
    
    # Queue metrics
    max_queue_size: int = 0
    average_queue_size: float = 0.0
    queue_processing_rate: float = 0.0
    
    # Health indicators
    availability_percentage: float = 100.0
    reliability_score: float = 1.0
    data_consistency_score: float = 1.0
    
    # Last update
    last_updated: datetime = field(default_factory=datetime.now)
    metrics_version: str = "1.0.0"


@dataclass
class SyncConfiguration:
    """Sync monitoring configuration"""
    config_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    service_name: str = ""
    
    # Monitoring settings
    health_check_enabled: bool = True
    health_check_interval_seconds: int = 60
    metrics_collection_enabled: bool = True
    metrics_collection_interval_seconds: int = 300
    
    # Alert settings
    alerts_enabled: bool = True
    alert_thresholds: Dict[str, Any] = field(default_factory=dict)
    notification_channels: List[str] = field(default_factory=list)
    
    # Performance thresholds
    max_sync_duration_ms: int = 30000  # 30 seconds
    max_queue_size: int = 10000
    min_success_rate_percentage: float = 95.0
    max_error_rate_percentage: float = 5.0
    
    # Data retention
    metrics_retention_days: int = 30
    alerts_retention_days: int = 90
    health_history_retention_days: int = 7
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


# Backward compatibility
Sync_monitoringBase = SyncHealth
