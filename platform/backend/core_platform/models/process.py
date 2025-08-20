"""
Core Platform Process Models
=============================
Data models for process coordination system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid


class ProcessStatus(Enum):
    """Process execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProcessType(Enum):
    """Types of processes"""
    SYNCHRONOUS = "synchronous"
    ASYNCHRONOUS = "asynchronous"
    BACKGROUND = "background"
    SCHEDULED = "scheduled"


@dataclass
class ProcessStep:
    """Individual process step"""
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    handler: str = ""
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    timeout_seconds: Optional[int] = None
    retry_policy: Dict[str, Any] = field(default_factory=dict)
    order: int = 0


@dataclass
class ProcessExecution:
    """Process execution instance"""
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    process_id: str = ""
    status: ProcessStatus = ProcessStatus.PENDING
    process_type: ProcessType = ProcessType.SYNCHRONOUS
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    context: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    executed_by: str = ""


@dataclass
class ProcessCoordination:
    """Process coordination and orchestration"""
    coordination_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    processes: List[str] = field(default_factory=list)
    coordination_rules: Dict[str, Any] = field(default_factory=dict)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    is_active: bool = True