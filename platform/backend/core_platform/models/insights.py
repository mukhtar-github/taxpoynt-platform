"""Core Platform Insights Models"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid


class InsightType(Enum):
    """Business insight types"""
    PERFORMANCE = "performance"
    ANOMALY = "anomaly"
    TREND = "trend"
    OPTIMIZATION = "optimization"
    RISK = "risk"
    OPPORTUNITY = "opportunity"


class InsightPriority(Enum):
    """Insight priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class InsightStatus(Enum):
    """Insight execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class RuleCondition(Enum):
    """Rule condition operators"""
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EQUALS = "equals"
    BETWEEN = "between"
    CONTAINS = "contains"
    MATCHES_PATTERN = "matches_pattern"


@dataclass
class BusinessInsight:
    """Business insight generated from data analysis"""
    insight_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    insight_type: InsightType = InsightType.PERFORMANCE
    priority: InsightPriority = InsightPriority.MEDIUM
    confidence_score: float = 0.0
    impact_score: float = 0.0
    data_sources: List[str] = field(default_factory=list)
    key_metrics: Dict[str, float] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    generated_by: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None
    is_actionable: bool = True
    action_taken: bool = False


@dataclass
class InsightRule:
    """Rule definition for generating insights"""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    insight_type: InsightType = InsightType.PERFORMANCE
    conditions: List[Dict[str, Any]] = field(default_factory=list)
    threshold_values: Dict[str, float] = field(default_factory=dict)
    data_sources: List[str] = field(default_factory=list)
    evaluation_frequency: str = "hourly"
    is_active: bool = True
    priority: InsightPriority = InsightPriority.MEDIUM
    template: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    last_modified: datetime = field(default_factory=datetime.now)


@dataclass
class InsightExecution:
    """Insight rule execution instance"""
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = ""
    status: InsightStatus = InsightStatus.PENDING
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    results: List[str] = field(default_factory=list)  # List of generated insight IDs
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    data_quality_score: float = 1.0
    insights_generated: int = 0
    evaluation_context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InsightReport:
    """Comprehensive insight report"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    time_period_start: datetime = field(default_factory=datetime.now)
    time_period_end: datetime = field(default_factory=datetime.now)
    insights: List[str] = field(default_factory=list)  # List of insight IDs
    summary: str = ""
    key_findings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    metrics_summary: Dict[str, Any] = field(default_factory=dict)
    charts_data: Dict[str, Any] = field(default_factory=dict)
    generated_by: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
    report_type: str = "standard"
    target_audience: List[str] = field(default_factory=list)
    distribution_list: List[str] = field(default_factory=list)


# Backward compatibility
InsightsBase = BusinessInsight
