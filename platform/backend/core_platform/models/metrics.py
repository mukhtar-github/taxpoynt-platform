"""
Core Platform Metrics Models
============================
Data models for metrics collection and aggregation.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Union
from enum import Enum
import uuid


class MetricType(Enum):
    """Types of metrics"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"


class MetricStatus(Enum):
    """Status of metric collection"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    ERROR = "error"


@dataclass
class MetricRecord:
    """Individual metric record"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    value: Union[int, float] = 0
    metric_type: MetricType = MetricType.GAUGE
    timestamp: datetime = field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'value': self.value,
            'metric_type': self.metric_type.value,
            'timestamp': self.timestamp.isoformat(),
            'labels': self.labels,
            'metadata': self.metadata
        }


@dataclass
class MetricAggregation:
    """Aggregated metric data"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metric_name: str = ""
    count: int = 0
    sum: Union[int, float] = 0
    min_value: Union[int, float] = 0
    max_value: Union[int, float] = 0
    avg_value: Union[int, float] = 0
    start_time: datetime = field(default_factory=datetime.utcnow)
    end_time: datetime = field(default_factory=datetime.utcnow)
    labels: Dict[str, str] = field(default_factory=dict)
    
    @property
    def duration_seconds(self) -> float:
        """Duration of aggregation period in seconds"""
        return (self.end_time - self.start_time).total_seconds()
    
    def add_record(self, record: MetricRecord):
        """Add a metric record to this aggregation"""
        if self.count == 0:
            self.min_value = record.value
            self.max_value = record.value
            self.sum = record.value
        else:
            self.min_value = min(self.min_value, record.value)
            self.max_value = max(self.max_value, record.value)
            self.sum += record.value
        
        self.count += 1
        self.avg_value = self.sum / self.count
        self.end_time = max(self.end_time, record.timestamp)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'metric_name': self.metric_name,
            'count': self.count,
            'sum': self.sum,
            'min_value': self.min_value,
            'max_value': self.max_value,
            'avg_value': self.avg_value,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_seconds': self.duration_seconds,
            'labels': self.labels
        }


@dataclass
class MetricSnapshot:
    """Point-in-time snapshot of metrics"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metrics: List[MetricRecord] = field(default_factory=list)
    aggregations: List[MetricAggregation] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_metric(self, metric: MetricRecord):
        """Add a metric to this snapshot"""
        self.metrics.append(metric)
    
    def add_aggregation(self, aggregation: MetricAggregation):
        """Add an aggregation to this snapshot"""
        self.aggregations.append(aggregation)
    
    @property
    def metric_count(self) -> int:
        """Total number of metrics in snapshot"""
        return len(self.metrics)
    
    @property
    def aggregation_count(self) -> int:
        """Total number of aggregations in snapshot"""
        return len(self.aggregations)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat(),
            'metric_count': self.metric_count,
            'aggregation_count': self.aggregation_count,
            'metrics': [metric.to_dict() for metric in self.metrics],
            'aggregations': [agg.to_dict() for agg in self.aggregations],
            'metadata': self.metadata
        }


# Convenience functions
def create_metric_record(name: str, value: Union[int, float], 
                        metric_type: MetricType = MetricType.GAUGE,
                        labels: Optional[Dict[str, str]] = None) -> MetricRecord:
    """Create a new metric record"""
    return MetricRecord(
        name=name,
        value=value,
        metric_type=metric_type,
        labels=labels or {}
    )


def create_metric_aggregation(metric_name: str, records: List[MetricRecord]) -> MetricAggregation:
    """Create aggregation from a list of metric records"""
    agg = MetricAggregation(metric_name=metric_name)
    for record in records:
        agg.add_record(record)
    return agg