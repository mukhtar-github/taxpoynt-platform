"""Core Platform Regulatory Models"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid

class RegulatoryStatus(Enum):
    """Regulatory change status types"""
    PROPOSED = "proposed"
    PENDING = "pending"
    ACTIVE = "active"
    SUPERSEDED = "superseded"
    CANCELLED = "cancelled"


class RegulatoryType(Enum):
    """Types of regulatory changes"""
    TAX_RATE = "tax_rate"
    COMPLIANCE_RULE = "compliance_rule"
    REPORTING_REQUIREMENT = "reporting_requirement"
    DOCUMENTATION = "documentation"
    PROCEDURE = "procedure"
    PENALTY = "penalty"


class NotificationPriority(Enum):
    """Notification priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class RegulatoryChange:
    """Regulatory change tracking"""
    change_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    regulatory_type: RegulatoryType = RegulatoryType.COMPLIANCE_RULE
    status: RegulatoryStatus = RegulatoryStatus.PROPOSED
    authority: str = ""
    reference_number: str = ""
    effective_date: Optional[datetime] = None
    announcement_date: Optional[datetime] = None
    impact_areas: List[str] = field(default_factory=list)
    affected_entities: List[str] = field(default_factory=list)
    compliance_deadline: Optional[datetime] = None
    implementation_guidance: str = ""
    related_changes: List[str] = field(default_factory=list)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class RegulatorySubscription:
    """Regulatory change subscription settings"""
    subscription_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    entity_id: str = ""
    subscription_name: str = ""
    regulatory_types: List[RegulatoryType] = field(default_factory=list)
    authorities: List[str] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)
    impact_areas: List[str] = field(default_factory=list)
    notification_frequency: str = "immediate"
    notification_channels: List[str] = field(default_factory=list)
    is_active: bool = True
    auto_apply_filters: bool = False
    custom_filters: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class RegulatoryNotification:
    """Regulatory change notification"""
    notification_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    change_id: str = ""
    subscription_id: str = ""
    recipient_id: str = ""
    title: str = ""
    message: str = ""
    priority: NotificationPriority = NotificationPriority.MEDIUM
    notification_type: str = "regulatory_change"
    channel: str = "email"
    is_read: bool = False
    is_archived: bool = False
    action_required: bool = False
    action_deadline: Optional[datetime] = None
    related_entities: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    sent_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)


# Backward compatibility
RegulatoryBase = RegulatoryChange
