"""Core Platform Cache Models"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid


class CacheStatus(Enum):
    """Cache entry status types"""
    ACTIVE = "active"
    EXPIRED = "expired"
    INVALIDATED = "invalidated"
    PENDING = "pending"


class CachePolicy(Enum):
    """Cache policy types"""
    LRU = "lru"  # Least Recently Used
    LFU = "lfu"  # Least Frequently Used
    FIFO = "fifo"  # First In First Out
    TTL = "ttl"  # Time To Live
    WRITE_THROUGH = "write_through"
    WRITE_BACK = "write_back"


@dataclass
class CacheEntry:
    """Cache entry with metadata and expiration"""
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    key: str = ""
    value: Any = None
    namespace: str = "default"
    status: CacheStatus = CacheStatus.ACTIVE
    
    # Timing and expiration
    created_at: datetime = field(default_factory=datetime.now)
    accessed_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    ttl_seconds: Optional[int] = None
    
    # Usage statistics
    access_count: int = 0
    hit_count: int = 0
    miss_count: int = 0
    
    # Metadata
    size_bytes: Optional[int] = None
    content_type: str = "application/json"
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Source tracking
    source_system: str = ""
    source_version: str = "1.0.0"
    cache_version: int = 1


@dataclass
class CacheStatistics:
    """Cache performance statistics"""
    stats_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    namespace: str = "default"
    
    # Hit/miss statistics
    total_requests: int = 0
    cache_hits: int = 0
    cache_misses: int = 0
    hit_ratio: float = 0.0
    
    # Performance metrics
    average_response_time_ms: float = 0.0
    total_response_time_ms: float = 0.0
    max_response_time_ms: float = 0.0
    min_response_time_ms: float = 0.0
    
    # Storage metrics
    total_entries: int = 0
    total_size_bytes: int = 0
    average_entry_size_bytes: float = 0.0
    max_entry_size_bytes: int = 0
    
    # Expiration metrics
    expired_entries: int = 0
    invalidated_entries: int = 0
    evicted_entries: int = 0
    
    # Time window
    period_start: datetime = field(default_factory=datetime.now)
    period_end: datetime = field(default_factory=datetime.now)
    
    # Last update
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class CacheConfiguration:
    """Cache configuration settings"""
    config_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    namespace: str = "default"
    
    # Policy settings
    policy: CachePolicy = CachePolicy.LRU
    max_size: int = 1000
    max_size_bytes: int = 100 * 1024 * 1024  # 100MB
    default_ttl_seconds: int = 3600  # 1 hour
    
    # Performance settings
    enable_compression: bool = True
    enable_encryption: bool = False
    enable_statistics: bool = True
    statistics_interval_seconds: int = 60
    
    # Cleanup settings
    cleanup_interval_seconds: int = 300  # 5 minutes
    expired_cleanup_batch_size: int = 100
    
    # Redis/external cache settings
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    connection_pool_size: int = 10
    
    # Advanced settings
    enable_write_behind: bool = False
    write_behind_delay_ms: int = 1000
    enable_read_through: bool = True
    
    # Monitoring
    enable_metrics: bool = True
    alert_on_high_miss_ratio: bool = True
    miss_ratio_threshold: float = 0.8
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


# Backward compatibility
CacheBase = CacheEntry
