"""Core Platform Conflicts Models"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional
from enum import Enum
import uuid

class ConflictType(Enum):
    DATA = "data"
    RESOURCE = "resource"
    PERMISSION = "permission"

@dataclass
class Conflict:
    conflict_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conflict_type: ConflictType = ConflictType.DATA
    entity_id: str = ""
    description: str = ""
    detected_at: datetime = field(default_factory=datetime.now)

@dataclass
class ConflictResolution:
    resolution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conflict_id: str = ""
    resolution_strategy: str = ""
    resolved_at: datetime = field(default_factory=datetime.now)

@dataclass
class ConflictHistory:
    history_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    conflict_id: str = ""
    actions: list = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
