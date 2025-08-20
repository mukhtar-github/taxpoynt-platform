"""Core Platform Validation Models"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid


class ValidationStatus(Enum):
    """Validation status types"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


class ValidationSeverity(Enum):
    """Validation severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class RuleType(Enum):
    """Validation rule types"""
    BUSINESS_RULE = "business_rule"
    DATA_QUALITY = "data_quality"
    COMPLIANCE = "compliance"
    SECURITY = "security"
    TECHNICAL = "technical"


@dataclass
class ValidationResult:
    """Result of a validation operation"""
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    validation_id: str = ""
    rule_id: str = ""
    status: ValidationStatus = ValidationStatus.PENDING
    severity: ValidationSeverity = ValidationSeverity.INFO
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    data_path: str = ""
    expected_value: Optional[Any] = None
    actual_value: Optional[Any] = None
    error_code: Optional[str] = None
    suggestions: List[str] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.now)
    execution_time_ms: Optional[int] = None


@dataclass
class CrossRoleValidation:
    """Cross-role validation definition"""
    validation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    source_role: str = ""
    target_role: str = ""
    validation_rules: List[str] = field(default_factory=list)
    data_mapping: Dict[str, str] = field(default_factory=dict)
    is_bidirectional: bool = False
    frequency: str = "on_demand"
    timeout_seconds: int = 30
    retry_count: int = 3
    is_active: bool = True
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    last_executed: Optional[datetime] = None


@dataclass
class ValidationRule:
    """Validation rule definition"""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    rule_type: RuleType = RuleType.BUSINESS_RULE
    expression: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    severity: ValidationSeverity = ValidationSeverity.ERROR
    is_blocking: bool = True
    is_active: bool = True
    scope: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    error_message_template: str = ""
    success_message_template: str = ""
    tags: List[str] = field(default_factory=list)
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    version: int = 1


@dataclass
class ValidationExecution:
    """Validation execution instance"""
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    validation_id: str = ""
    triggered_by: str = ""
    trigger_source: str = ""
    input_data: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    results: List[ValidationResult] = field(default_factory=list)
    overall_status: ValidationStatus = ValidationStatus.PENDING
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_rules: int = 0
    passed_rules: int = 0
    failed_rules: int = 0
    warning_rules: int = 0
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None


@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    scope: str = ""
    period_start: datetime = field(default_factory=datetime.now)
    period_end: datetime = field(default_factory=datetime.now)
    executions: List[str] = field(default_factory=list)  # List of execution IDs
    summary: Dict[str, Any] = field(default_factory=dict)
    compliance_score: float = 0.0
    trend_analysis: Dict[str, Any] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)
    generated_by: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
    report_format: str = "json"
    export_path: Optional[str] = None


# Backward compatibility
ValidationBase = ValidationResult
