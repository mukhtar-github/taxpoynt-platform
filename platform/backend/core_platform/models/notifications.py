"""Core Platform Notifications Models"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid

# Basic model structure for notifications
@dataclass
class NotificationsBase:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

# Notification Rule Types and Priorities
class NotificationType(Enum):
    """Types of notifications"""
    EMAIL = "email"
    SMS = "sms"
    SLACK = "slack"
    WEBHOOK = "webhook"
    IN_APP = "in_app"
    PUSH = "push"
    TEAMS = "teams"
    DISCORD = "discord"

class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"
    CRITICAL = "critical"

class NotificationStatus(Enum):
    """Notification delivery status"""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"

class RuleCondition(Enum):
    """Rule triggering conditions"""
    ERROR_THRESHOLD = "error_threshold"
    SUCCESS_RATE = "success_rate"
    RESPONSE_TIME = "response_time"
    QUEUE_LENGTH = "queue_length"
    SYSTEM_LOAD = "system_load"
    BUSINESS_EVENT = "business_event"

# Enterprise Notification Models
@dataclass
class NotificationRule(NotificationsBase):
    """Enterprise notification rule configuration"""
    name: str = ""
    description: str = ""
    service_name: str = ""
    condition_type: RuleCondition = RuleCondition.ERROR_THRESHOLD
    condition_value: float = 0.0
    condition_operator: str = ">"  # >, <, >=, <=, ==, !=
    evaluation_window_minutes: int = 5
    cooldown_minutes: int = 15
    is_active: bool = True
    priority: NotificationPriority = NotificationPriority.NORMAL
    message_template: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # Business Hours and Scheduling
    business_hours_only: bool = False
    timezone: str = "Africa/Lagos"
    allowed_days: List[str] = field(default_factory=lambda: ["monday", "tuesday", "wednesday", "thursday", "friday"])
    allowed_hours_start: int = 9  # 9 AM
    allowed_hours_end: int = 17   # 5 PM
    
    # Advanced Configuration
    max_notifications_per_hour: int = 10
    escalation_delay_minutes: int = 30
    auto_resolve_minutes: int = 60
    require_acknowledgment: bool = False

@dataclass
class NotificationTarget(NotificationsBase):
    """Enterprise notification target (recipient)"""
    rule_id: str = ""
    target_type: NotificationType = NotificationType.EMAIL
    target_address: str = ""  # email, phone number, webhook URL, etc.
    display_name: str = ""
    is_active: bool = True
    priority_override: Optional[NotificationPriority] = None
    
    # Target-specific Configuration
    configuration: Dict[str, Any] = field(default_factory=dict)  # API keys, credentials, etc.
    retry_attempts: int = 3
    retry_delay_minutes: int = 2
    timeout_seconds: int = 30
    
    # Nigerian Business Context
    language_preference: str = "en"  # en, yo, ig, ha for Nigerian languages
    business_role: str = ""  # admin, manager, developer, business_owner
    department: str = ""
    cost_center: str = ""
    escalation_level: int = 1

@dataclass
class NotificationDelivery(NotificationsBase):
    """Enterprise notification delivery tracking"""
    rule_id: str = ""
    target_id: str = ""
    message_content: str = ""
    status: NotificationStatus = NotificationStatus.PENDING
    priority: NotificationPriority = NotificationPriority.NORMAL
    
    # Delivery Tracking
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    acknowledged_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    
    # Error Information
    error_message: str = ""
    error_code: str = ""
    error_details: Dict[str, Any] = field(default_factory=dict)
    
    # Business Context
    triggered_by_service: str = ""
    triggered_by_event: str = ""
    business_impact: str = ""
    cost_estimate: float = 0.0  # SMS cost, API call cost, etc.
    
    # Nigerian Compliance
    data_residency: str = "nigeria"  # Data must stay in Nigeria
    retention_days: int = 365
    audit_trail: List[Dict[str, Any]] = field(default_factory=list)

# Additional Supporting Models
@dataclass
class NotificationTemplate(NotificationsBase):
    """Reusable notification templates"""
    name: str = ""
    template_type: NotificationType = NotificationType.EMAIL
    subject_template: str = ""
    body_template: str = ""
    variables: List[str] = field(default_factory=list)
    is_active: bool = True
    created_by: str = ""
    organization_id: str = ""
    
    # Nigerian Language Support
    translations: Dict[str, Dict[str, str]] = field(default_factory=dict)
    default_language: str = "en"

@dataclass
class NotificationSchedule(NotificationsBase):
    """Scheduled notification management"""
    rule_id: str = ""
    schedule_type: str = "cron"  # cron, interval, once
    schedule_expression: str = ""  # cron expression or interval
    next_execution: Optional[datetime] = None
    is_active: bool = True
    execution_count: int = 0
    max_executions: Optional[int] = None
    timezone: str = "Africa/Lagos"
