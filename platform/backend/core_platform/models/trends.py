"""Core Platform Trends Models"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid


class TrendDirection(Enum):
    """Trend direction types"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    VOLATILE = "volatile"


class TrendConfidence(Enum):
    """Trend confidence levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"


@dataclass
class TrendAnalysis:
    """Trend analysis results"""
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metric_name: str = ""
    time_period: str = ""
    direction: TrendDirection = TrendDirection.STABLE
    confidence: TrendConfidence = TrendConfidence.MEDIUM
    slope: float = 0.0
    correlation_coefficient: float = 0.0
    variance: float = 0.0
    data_points: int = 0
    analysis_method: str = "linear_regression"
    metadata: Dict[str, Any] = field(default_factory=dict)
    analyzed_at: datetime = field(default_factory=datetime.now)
    valid_until: Optional[datetime] = None


@dataclass
class TrendPattern:
    """Identified trend pattern"""
    pattern_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    pattern_type: str = ""
    frequency: str = ""
    seasonality: Optional[str] = None
    strength: float = 0.0
    confidence: TrendConfidence = TrendConfidence.MEDIUM
    detection_method: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    first_detected: datetime = field(default_factory=datetime.now)
    last_confirmed: datetime = field(default_factory=datetime.now)
    occurrences: int = 1


@dataclass
class TrendPrediction:
    """Trend prediction results"""
    prediction_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    metric_name: str = ""
    prediction_horizon: str = ""
    predicted_value: float = 0.0
    confidence_interval_lower: float = 0.0
    confidence_interval_upper: float = 0.0
    confidence_level: float = 0.95
    prediction_method: str = ""
    model_accuracy: Optional[float] = None
    input_features: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    predicted_at: datetime = field(default_factory=datetime.now)
    prediction_for: datetime = field(default_factory=datetime.now)


@dataclass
class TrendAlert:
    """Trend-based alert"""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    trend_analysis_id: str = ""
    alert_type: str = ""
    severity: AlertSeverity = AlertSeverity.INFO
    title: str = ""
    message: str = ""
    metric_name: str = ""
    current_value: Optional[float] = None
    threshold_value: Optional[float] = None
    deviation_percentage: Optional[float] = None
    trigger_conditions: Dict[str, Any] = field(default_factory=dict)
    is_resolved: bool = False
    triggered_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    escalated: bool = False


# Backward compatibility
TrendsBase = TrendAnalysis
