"""
Core Platform Compliance Models
================================
Data models for compliance management system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid


class ComplianceStatus(Enum):
    """Compliance status"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    PENDING = "pending"
    UNKNOWN = "unknown"


@dataclass
class Regulation:
    """Regulatory requirement"""
    regulation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    authority: str = ""
    version: str = "1.0"
    effective_date: Optional[datetime] = None
    
    
@dataclass
class RegulationRule:
    """Individual regulation rule"""
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    regulation_id: str = ""
    rule_code: str = ""
    description: str = ""
    requirements: List[str] = field(default_factory=list)


@dataclass
class ComplianceViolation:
    """Compliance violation record"""
    violation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = ""
    entity_id: str = ""
    description: str = ""
    severity: str = "medium"
    detected_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None


@dataclass
class ComplianceExecution:
    """Compliance check execution"""
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = ""
    status: ComplianceStatus = ComplianceStatus.PENDING
    result: Optional[Dict[str, Any]] = None
    executed_at: datetime = field(default_factory=datetime.now)


@dataclass
class ComplianceWorkflow:
    """Compliance workflow definition"""
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    regulations: List[str] = field(default_factory=list)
    schedule: Optional[str] = None


@dataclass
class ComplianceResult:
    """Compliance assessment result"""
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    overall_status: ComplianceStatus = ComplianceStatus.UNKNOWN
    violations: List[ComplianceViolation] = field(default_factory=list)
    assessed_at: datetime = field(default_factory=datetime.now)