"""Core Platform Escalation Models"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import uuid


class EscalationTriggerType(Enum):
    """Types of escalation triggers"""
    THRESHOLD_BREACH = "threshold_breach"
    TIME_BASED = "time_based"
    SEVERITY_INCREASE = "severity_increase"
    MANUAL = "manual"
    AUTOMATED_RULE = "automated_rule"
    PATTERN_DETECTED = "pattern_detected"


class EscalationLevelStatus(Enum):
    """Escalation level status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    COMPLETED = "completed"


class EscalationInstanceStatus(Enum):
    """Escalation instance status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class NotificationMethod(Enum):
    """Notification delivery methods"""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    WEBHOOK = "webhook"
    IN_APP = "in_app"
    PUSH_NOTIFICATION = "push_notification"


@dataclass
class EscalationLevel:
    """Escalation level configuration"""
    level_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    policy_id: str = ""
    level_number: int = 1
    level_name: str = ""
    description: str = ""
    
    # Timing configuration
    trigger_delay_minutes: int = 15
    reminder_interval_minutes: Optional[int] = None
    timeout_minutes: Optional[int] = None
    
    # Notification settings
    notification_methods: List[NotificationMethod] = field(default_factory=list)
    recipients: List[str] = field(default_factory=list)  # User IDs or email addresses
    notification_template: Optional[str] = None
    
    # Escalation conditions
    auto_escalate: bool = True
    escalation_conditions: Dict[str, Any] = field(default_factory=dict)
    skip_conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Actions to perform at this level
    actions: List[Dict[str, Any]] = field(default_factory=list)
    required_approvals: int = 0
    
    # Status and metadata
    status: EscalationLevelStatus = EscalationLevelStatus.ACTIVE
    priority: int = 1  # 1 = highest priority
    is_final_level: bool = False
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class EscalationPolicy:
    """Escalation policy definition and management"""
    policy_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    policy_name: str = ""
    description: str = ""
    
    # Policy scope
    service_name: str = ""
    component_names: List[str] = field(default_factory=list)
    error_types: List[str] = field(default_factory=list)
    severity_levels: List[str] = field(default_factory=list)
    
    # Trigger configuration
    trigger_type: EscalationTriggerType = EscalationTriggerType.THRESHOLD_BREACH
    trigger_conditions: Dict[str, Any] = field(default_factory=dict)
    
    # Policy settings
    is_enabled: bool = True
    max_escalation_levels: int = 3
    total_timeout_hours: int = 24
    
    # Business hours and timezone
    business_hours_only: bool = False
    timezone: str = "UTC"
    business_start_hour: int = 9  # 9 AM
    business_end_hour: int = 17   # 5 PM
    business_days: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])  # Mon-Fri
    
    # Escalation levels (ordered by level_number)
    escalation_levels: List[str] = field(default_factory=list)  # List of level IDs
    
    # Policy metadata
    owner: str = ""
    reviewers: List[str] = field(default_factory=list)
    last_reviewed: Optional[datetime] = None
    next_review_due: Optional[datetime] = None
    
    # Statistics and monitoring
    total_escalations: int = 0
    successful_resolutions: int = 0
    timeout_count: int = 0
    average_resolution_time_minutes: float = 0.0
    
    # Audit and compliance
    compliance_required: bool = False
    audit_trail_enabled: bool = True
    retention_days: int = 365
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class EscalationInstance:
    """Active escalation instance tracking"""
    instance_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    policy_id: str = ""
    correlation_id: str = ""  # Links to original issue/error
    
    # Instance details
    trigger_event_id: str = ""
    trigger_type: EscalationTriggerType = EscalationTriggerType.MANUAL
    trigger_reason: str = ""
    triggered_by: str = "system"
    
    # Current status
    status: EscalationInstanceStatus = EscalationInstanceStatus.PENDING
    current_level: int = 1
    current_level_id: Optional[str] = None
    
    # Timing tracking
    escalation_started: datetime = field(default_factory=datetime.now)
    current_level_started: Optional[datetime] = None
    last_activity: datetime = field(default_factory=datetime.now)
    expected_escalation_time: Optional[datetime] = None
    actual_resolution_time: Optional[datetime] = None
    
    # Context and metadata
    issue_context: Dict[str, Any] = field(default_factory=dict)
    business_impact: str = "medium"
    affected_users: int = 0
    affected_services: List[str] = field(default_factory=list)
    
    # Escalation history
    escalation_history: List[Dict[str, Any]] = field(default_factory=list)
    notifications_sent: List[Dict[str, Any]] = field(default_factory=list)
    actions_taken: List[Dict[str, Any]] = field(default_factory=list)
    
    # Resolution tracking
    resolution_notes: str = ""
    resolved_by: Optional[str] = None
    resolution_category: Optional[str] = None
    customer_satisfaction_score: Optional[int] = None
    
    # Follow-up and learning
    post_incident_review_required: bool = False
    lessons_learned: List[str] = field(default_factory=list)
    preventive_actions: List[str] = field(default_factory=list)
    
    # Metrics
    total_escalation_time_minutes: Optional[int] = None
    time_to_first_response_minutes: Optional[int] = None
    sla_met: Optional[bool] = None
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class EscalationConfiguration:
    """Global escalation system configuration"""
    config_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    # Global settings
    escalation_enabled: bool = True
    max_concurrent_escalations: int = 50
    default_timezone: str = "UTC"
    
    # Default timing settings
    default_trigger_delay_minutes: int = 15
    default_level_timeout_minutes: int = 60
    default_total_timeout_hours: int = 24
    
    # Notification settings
    notification_retry_attempts: int = 3
    notification_retry_delay_minutes: int = 5
    enable_notification_batching: bool = True
    
    # Business hours (global defaults)
    global_business_start_hour: int = 9
    global_business_end_hour: int = 17
    global_business_days: List[int] = field(default_factory=lambda: [0, 1, 2, 3, 4])
    
    # Escalation limits and controls
    max_escalation_levels_per_policy: int = 5
    escalation_rate_limit_per_hour: int = 100
    
    # Monitoring and alerting
    enable_escalation_monitoring: bool = True
    alert_on_escalation_failures: bool = True
    metrics_collection_enabled: bool = True
    
    # Audit and compliance
    audit_all_escalations: bool = True
    compliance_mode_enabled: bool = False
    data_retention_days: int = 365
    
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


# Backward compatibility
EscalationBase = EscalationPolicy
