"""Core Platform Incidents Models"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum
import uuid

class IncidentSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class Incident:
    incident_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    description: str = ""
    severity: IncidentSeverity = IncidentSeverity.MEDIUM
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None

@dataclass
class IncidentUpdate:
    update_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    incident_id: str = ""
    message: str = ""
    updated_at: datetime = field(default_factory=datetime.now)

@dataclass
class IncidentResolution:
    resolution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    incident_id: str = ""
    resolution_summary: str = ""
    resolved_at: datetime = field(default_factory=datetime.now)
