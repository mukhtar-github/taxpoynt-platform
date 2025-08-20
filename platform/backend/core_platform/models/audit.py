"""
Core Platform Audit Models
===========================
Data models for audit trail system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid


class AuditLevel(Enum):
    """Audit event levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AuditCategory(Enum):
    """Audit event categories"""
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    DATA_ACCESS = "data_access"
    CONFIGURATION = "configuration"
    SYSTEM = "system"


@dataclass
class AuditEvent:
    """Individual audit event"""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    category: AuditCategory = AuditCategory.SYSTEM
    level: AuditLevel = AuditLevel.INFO
    message: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class AuditTrail:
    """Audit trail collection"""
    trail_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: str = ""
    entity_id: str = ""
    events: List[AuditEvent] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class AuditSession:
    """Audit session tracking"""
    session_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    started_at: datetime = field(default_factory=datetime.now)
    ended_at: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    events_count: int = 0
    is_active: bool = True


@dataclass
class AuditReport:
    """Audit report generation"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    date_range_start: datetime = field(default_factory=datetime.now)
    date_range_end: datetime = field(default_factory=datetime.now)
    filters: Dict[str, Any] = field(default_factory=dict)
    events_included: int = 0
    generated_at: datetime = field(default_factory=datetime.now)
    generated_by: str = ""