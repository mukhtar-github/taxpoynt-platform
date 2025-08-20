"""Core Platform Synchronization Models"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum
import uuid

# Basic model structure for synchronization
@dataclass
class SynchronizationBase:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

# Add specific classes based on the import patterns

@dataclass
class SyncState:
    state_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_type: str = ""
    entity_id: str = ""
    sync_status: str = "pending"
    last_synced: datetime = field(default_factory=datetime.now)

@dataclass  
class SyncEvent:
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: str = ""
    entity_id: str = ""
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class SyncConflict:
    conflict_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    entity_id: str = ""
    conflict_type: str = ""
    description: str = ""
    detected_at: datetime = field(default_factory=datetime.now)
