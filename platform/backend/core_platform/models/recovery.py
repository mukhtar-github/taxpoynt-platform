"""Core Platform Recovery Models"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import uuid


class RecoverySessionStatus(Enum):
    """Recovery session status types"""
    INITIATED = "initiated"
    IN_PROGRESS = "in_progress"
    SUCCESSFUL = "successful"
    FAILED = "failed"
    PARTIAL = "partial"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class RecoveryActionType(Enum):
    """Recovery action types"""
    RETRY = "retry"
    ROLLBACK = "rollback"
    CIRCUIT_BREAKER = "circuit_breaker"
    FAILOVER = "failover"
    DATA_REPAIR = "data_repair"
    SERVICE_RESTART = "service_restart"
    MANUAL_INTERVENTION = "manual_intervention"
    COMPENSATING_TRANSACTION = "compensating_transaction"


class RecoveryActionStatus(Enum):
    """Recovery action execution status"""
    PENDING = "pending"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"


class RecoveryResultOutcome(Enum):
    """Recovery operation outcome"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL_SUCCESS = "partial_success"
    NO_ACTION_NEEDED = "no_action_needed"
    ESCALATED = "escalated"


@dataclass
class RecoverySession:
    """Recovery session management and tracking"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: str = ""
    service_name: str = ""
    component_name: str = ""
    error_id: Optional[str] = None
    
    # Session status
    status: RecoverySessionStatus = RecoverySessionStatus.INITIATED
    priority: int = 5  # 1 (highest) to 10 (lowest)
    
    # Error context
    original_error_type: str = ""
    original_error_message: str = ""
    error_severity: str = "medium"
    affected_operations: List[str] = field(default_factory=list)
    
    # Recovery strategy
    recovery_strategy: str = ""
    max_retry_attempts: int = 3
    current_attempt: int = 0
    timeout_seconds: int = 300  # 5 minutes
    
    # Recovery actions
    planned_actions: List[str] = field(default_factory=list)  # List of action IDs
    executed_actions: List[str] = field(default_factory=list)
    
    # Timing
    initiated_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    timeout_at: Optional[datetime] = None
    
    # Results
    recovery_successful: bool = False
    partial_recovery: bool = False
    final_outcome: Optional[RecoveryResultOutcome] = None
    recovery_notes: str = ""
    
    # Context and metadata
    business_context: Dict[str, Any] = field(default_factory=dict)
    technical_context: Dict[str, Any] = field(default_factory=dict)
    user_context: Dict[str, str] = field(default_factory=dict)
    
    # Monitoring
    health_checks_passed: int = 0
    health_checks_failed: int = 0
    metrics_collected: Dict[str, Any] = field(default_factory=dict)
    
    # Administrative
    initiated_by: str = "system"
    assigned_to: Optional[str] = None
    escalated_to: Optional[str] = None
    session_version: str = "1.0.0"


@dataclass
class RecoveryAction:
    """Individual recovery action definition and execution"""
    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    action_type: RecoveryActionType = RecoveryActionType.RETRY
    action_name: str = ""
    description: str = ""
    
    # Execution details
    status: RecoveryActionStatus = RecoveryActionStatus.PENDING
    execution_order: int = 1
    is_critical: bool = False
    can_run_parallel: bool = False
    
    # Action configuration
    action_parameters: Dict[str, Any] = field(default_factory=dict)
    target_service: str = ""
    target_operation: str = ""
    
    # Retry and timeout settings
    max_attempts: int = 1
    current_attempt: int = 0
    timeout_seconds: int = 60
    backoff_multiplier: float = 2.0
    
    # Conditions
    prerequisites: List[str] = field(default_factory=list)  # Action IDs that must complete first
    skip_conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Execution tracking
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    
    # Results
    execution_successful: bool = False
    result_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None
    error_details: Dict[str, Any] = field(default_factory=dict)
    
    # Side effects and validation
    expected_side_effects: List[str] = field(default_factory=list)
    validation_checks: List[str] = field(default_factory=list)
    rollback_actions: List[str] = field(default_factory=list)
    
    # Metadata
    created_by: str = "system"
    action_version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class RecoveryResult:
    """Comprehensive recovery operation result"""
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str = ""
    action_id: Optional[str] = None  # If result is for specific action
    
    # Overall outcome
    outcome: RecoveryResultOutcome = RecoveryResultOutcome.SUCCESS
    success: bool = False
    partial_success: bool = False
    
    # Recovery metrics
    total_actions_planned: int = 0
    actions_executed: int = 0
    actions_successful: int = 0
    actions_failed: int = 0
    actions_skipped: int = 0
    
    # Performance metrics
    total_duration_ms: int = 0
    average_action_duration_ms: float = 0.0
    longest_action_duration_ms: int = 0
    recovery_efficiency_score: float = 0.0
    
    # System state
    system_health_before: Dict[str, Any] = field(default_factory=dict)
    system_health_after: Dict[str, Any] = field(default_factory=dict)
    health_improvement_score: float = 0.0
    
    # Business impact
    affected_users: int = 0
    affected_transactions: int = 0
    data_consistency_restored: bool = False
    service_availability_restored: bool = False
    
    # Error analysis
    root_cause_identified: bool = False
    root_cause_description: str = ""
    contributing_factors: List[str] = field(default_factory=list)
    
    # Recovery details
    recovery_strategy_used: str = ""
    fallback_strategies_used: List[str] = field(default_factory=list)
    manual_interventions_required: int = 0
    
    # Recommendations
    prevention_recommendations: List[str] = field(default_factory=list)
    improvement_recommendations: List[str] = field(default_factory=list)
    monitoring_recommendations: List[str] = field(default_factory=list)
    
    # Follow-up actions
    follow_up_actions_needed: List[str] = field(default_factory=list)
    monitoring_duration_hours: int = 24
    escalation_required: bool = False
    
    # Metadata
    result_summary: str = ""
    detailed_report: str = ""
    generated_at: datetime = field(default_factory=datetime.now)
    generated_by: str = "system"
    result_version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)


@dataclass
class RecoveryConfiguration:
    """Recovery system configuration"""
    config_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    service_name: str = ""
    
    # Recovery settings
    auto_recovery_enabled: bool = True
    max_concurrent_sessions: int = 5
    default_timeout_seconds: int = 300
    default_retry_attempts: int = 3
    
    # Action settings
    enable_rollback_actions: bool = True
    enable_failover_actions: bool = True
    enable_circuit_breaker: bool = True
    circuit_breaker_threshold: int = 5
    
    # Escalation settings
    auto_escalation_enabled: bool = True
    escalation_timeout_minutes: int = 30
    escalation_contacts: List[str] = field(default_factory=list)
    
    # Monitoring and alerting
    enable_recovery_monitoring: bool = True
    alert_on_recovery_failure: bool = True
    alert_on_manual_intervention: bool = True
    
    # Reporting
    generate_recovery_reports: bool = True
    report_retention_days: int = 90
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


# Backward compatibility
RecoveryBase = RecoverySession
