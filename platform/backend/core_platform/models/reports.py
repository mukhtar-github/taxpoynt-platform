"""
Core Platform Reports Models
============================
Data models for reporting system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid


class ReportType(Enum):
    """Types of reports"""
    ANALYTICS = "analytics"
    COMPLIANCE = "compliance"
    OPERATIONAL = "operational"
    FINANCIAL = "financial"
    SECURITY = "security"


class ReportStatus(Enum):
    """Report execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportFormat(Enum):
    """Report output formats"""
    PDF = "pdf"
    CSV = "csv"
    JSON = "json"
    EXCEL = "excel"


@dataclass
class ReportDefinition:
    """Report definition and configuration"""
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    report_type: ReportType = ReportType.ANALYTICS
    query_template: str = ""
    parameters: Dict[str, Any] = field(default_factory=dict)
    schedule: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    created_by: str = ""
    is_active: bool = True


@dataclass
class ReportExecution:
    """Report execution instance"""
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    report_id: str = ""
    status: ReportStatus = ReportStatus.PENDING
    parameters: Dict[str, Any] = field(default_factory=dict)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[int] = None
    row_count: Optional[int] = None


@dataclass
class ReportOutput:
    """Report output data"""
    output_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str = ""
    format: ReportFormat = ReportFormat.JSON
    file_path: Optional[str] = None
    data: Optional[Dict[str, Any]] = None
    size_bytes: Optional[int] = None
    generated_at: datetime = field(default_factory=datetime.now)
    expires_at: Optional[datetime] = None