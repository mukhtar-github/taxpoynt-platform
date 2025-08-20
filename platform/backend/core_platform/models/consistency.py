"""Core Platform Consistency Models"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid

@dataclass
class ConsistencyRule:
    rule_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    rule_definition: Dict[str, Any] = field(default_factory=dict)
    is_active: bool = True

@dataclass
class ConsistencyViolation:
    violation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = ""
    entity_id: str = ""
    description: str = ""
    detected_at: datetime = field(default_factory=datetime.now)

@dataclass
class ConsistencyCheck:
    check_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str = ""
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    checked_at: datetime = field(default_factory=datetime.now)
