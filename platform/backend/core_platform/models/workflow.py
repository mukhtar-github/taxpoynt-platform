"""
Core Platform Workflow Models
==============================
Data models for workflow orchestration system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
from enum import Enum
import uuid


class WorkflowStatus(Enum):
    """Workflow execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepStatus(Enum):
    """Individual step status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class WorkflowPriority(Enum):
    """Workflow execution priority"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class WorkflowStep:
    """Individual workflow step"""
    step_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    step_type: str = ""
    configuration: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass
class WorkflowState:
    """Workflow state information"""
    state_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    current_step: Optional[str] = None
    completed_steps: Set[str] = field(default_factory=set)
    failed_steps: Set[str] = field(default_factory=set)
    variables: Dict[str, Any] = field(default_factory=dict)
    last_updated: datetime = field(default_factory=datetime.now)


@dataclass
class StateTransition:
    """State transition definition"""
    transition_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    from_state: str = ""
    to_state: str = ""
    condition: Optional[str] = None
    action: Optional[str] = None


@dataclass
class StateMachine:
    """State machine definition"""
    machine_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    initial_state: str = ""
    states: List[str] = field(default_factory=list)
    transitions: List[StateTransition] = field(default_factory=list)


@dataclass
class WorkflowExecution:
    """Workflow execution instance"""
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    status: WorkflowStatus = WorkflowStatus.PENDING
    priority: WorkflowPriority = WorkflowPriority.NORMAL
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Optional[Dict[str, Any]] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: str = ""
    error_message: Optional[str] = None


@dataclass
class WorkflowMetrics:
    """Workflow execution metrics"""
    metrics_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str = ""
    total_steps: int = 0
    completed_steps: int = 0
    failed_steps: int = 0
    execution_time_ms: Optional[int] = None
    memory_usage_mb: Optional[float] = None
    collected_at: datetime = field(default_factory=datetime.now)


@dataclass
class WorkflowAlert:
    """Workflow-related alerts"""
    alert_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str = ""
    alert_type: str = ""
    message: str = ""
    severity: str = "medium"
    triggered_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None