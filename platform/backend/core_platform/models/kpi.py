"""Core Platform KPI Models"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid


class KPIType(Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    RATIO = "ratio"
    PERCENTAGE = "percentage"


class KPIStatus(Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    DRAFT = "draft"
    ARCHIVED = "archived"


class TargetComparison(Enum):
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    EQUAL_TO = "equal_to"
    RANGE = "range"


@dataclass
class KPIDefinition:
    kpi_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    kpi_type: KPIType = KPIType.GAUGE
    status: KPIStatus = KPIStatus.ACTIVE
    calculation_formula: str = ""
    unit: str = ""
    category: str = ""
    owner: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class KPICalculation:
    calculation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    kpi_id: str = ""
    period_start: datetime = field(default_factory=datetime.now)
    period_end: datetime = field(default_factory=datetime.now)
    calculated_value: float = 0.0
    raw_data: Dict[str, Any] = field(default_factory=dict)
    calculation_method: str = ""
    data_sources: List[str] = field(default_factory=list)
    is_provisional: bool = False
    calculated_at: datetime = field(default_factory=datetime.now)


@dataclass
class KPITarget:
    target_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    kpi_id: str = ""
    target_value: float = 0.0
    comparison_operator: TargetComparison = TargetComparison.GREATER_THAN
    target_period: str = ""
    threshold_warning: Optional[float] = None
    threshold_critical: Optional[float] = None
    is_active: bool = True
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    valid_from: datetime = field(default_factory=datetime.now)
    valid_until: Optional[datetime] = None


@dataclass
class KPIHistory:
    history_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    kpi_id: str = ""
    timestamp: datetime = field(default_factory=datetime.now)
    value: float = 0.0
    target_value: Optional[float] = None
    variance: Optional[float] = None
    status: str = "normal"
    notes: str = ""
    recorded_by: str = ""
    data_quality_score: float = 1.0


# Backward compatibility
KpiBase = KPIDefinition
