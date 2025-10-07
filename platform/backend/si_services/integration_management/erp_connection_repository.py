from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


@dataclass
class ERPConnectionRecord:
  """In-memory representation of an ERP connection."""

  connection_id: str
  organization_id: str
  erp_system: str
  connection_name: str
  environment: str
  connection_config: Dict[str, Any]
  metadata: Dict[str, Any] = field(default_factory=dict)
  status: str = "configured"
  created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
  updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ERPConnectionRepository:
  """Simple repository abstraction for ERP connections.

  Currently backed by an in-memory dictionary so that we can hot-swap the
  implementation later (e.g. to a database-backed repository) without touching
  the service registry wiring.
  """

  def __init__(self) -> None:
    self._records: Dict[str, ERPConnectionRecord] = {}

  def create(self, record: ERPConnectionRecord) -> ERPConnectionRecord:
    self._records[record.connection_id] = record
    return record

  def list(self, *, organization_id: Optional[str] = None, erp_system: Optional[str] = None) -> List[ERPConnectionRecord]:
    items = list(self._records.values())
    if organization_id:
      items = [item for item in items if item.organization_id == organization_id]
    if erp_system:
      system = erp_system.lower()
      items = [item for item in items if item.erp_system.lower() == system]
    return items

  def get(self, connection_id: str) -> Optional[ERPConnectionRecord]:
    return self._records.get(connection_id)

  def update(self, connection_id: str, data: Dict[str, Any]) -> Optional[ERPConnectionRecord]:
    record = self._records.get(connection_id)
    if not record:
      return None

    for key, value in data.items():
      if value is None:
        continue
      if key == "connection_config" and isinstance(value, dict):
        record.connection_config.update(value)
      elif hasattr(record, key):
        setattr(record, key, value)

    record.updated_at = datetime.now(timezone.utc)
    self._records[connection_id] = record
    return record

  def delete(self, connection_id: str) -> Optional[ERPConnectionRecord]:
    return self._records.pop(connection_id, None)

