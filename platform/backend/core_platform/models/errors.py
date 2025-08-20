"""Core Platform Error Models"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid

class ErrorSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class ErrorContext:
    context_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    service_name: str = ""
    operation: str = ""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    environment: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ErrorRecord:
    error_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    error_type: str = ""
    message: str = ""
    severity: ErrorSeverity = ErrorSeverity.MEDIUM
    context: Optional[ErrorContext] = None
    stack_trace: Optional[str] = None
    occurred_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None

@dataclass
class ErrorPattern:
    pattern_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    pattern_rules: Dict[str, Any] = field(default_factory=dict)
    occurrence_count: int = 0
    first_seen: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)