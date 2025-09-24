"""Security scanner and vulnerability management for APP services."""

from __future__ import annotations

import asyncio
import uuid
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional

from .threat_detector import (
    ThreatDetector,
    SecurityEvent,
    ThreatDetection,
    ThreatLevel,
    ThreatType,
)
from .audit_logger import AuditLogger, AuditLevel, EventCategory, AuditContext


@dataclass
class ScanRecord:
    scan_id: str
    scan_type: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    scope: Dict[str, Any]
    options: Dict[str, Any]
    detections: List[Dict[str, Any]]
    vulnerabilities: List[Dict[str, Any]]


class SecurityScanner:
    """Security scanner that leverages the ThreatDetector to surface issues."""

    def __init__(self, threat_detector: ThreatDetector, audit_logger: AuditLogger):
        self.threat_detector = threat_detector
        self.audit_logger = audit_logger
        self.scans: Dict[str, ScanRecord] = {}
        self.vulnerabilities: Dict[str, Dict[str, Any]] = {}
        self.recent_activity: deque[Dict[str, Any]] = deque(maxlen=200)
        self.metrics: Dict[str, Any] = {
            "total_scans": 0,
            "successful_scans": 0,
            "failed_scans": 0,
            "open_vulnerabilities": 0,
            "resolved_vulnerabilities": 0,
            "average_scan_duration_ms": 0.0,
            "last_scan_at": None,
        }

    async def run_scan(
        self,
        scope: Optional[Iterable[Dict[str, Any]]] = None,
        *,
        scan_type: str = "ad_hoc",
        options: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Execute a security scan over the supplied scope."""

        scope = list(scope or [])
        options = options or {}
        scan_id = f"scan-{uuid.uuid4().hex[:8]}"
        started_at = datetime.now(timezone.utc)

        record = ScanRecord(
            scan_id=scan_id,
            scan_type=scan_type,
            status="running",
            started_at=started_at,
            completed_at=None,
            scope={"targets": scope},
            options=options,
            detections=[],
            vulnerabilities=[],
        )
        self.scans[scan_id] = record
        self.metrics["total_scans"] += 1

        try:
            if not scope:
                scope = [self._default_event_payload()]

            detections: List[ThreatDetection] = []
            for event_payload in scope:
                event = self._build_security_event(event_payload)
                event_detections = await self.threat_detector.process_event(event)
                detections.extend(event_detections)

            for detection in detections:
                vuln = self._detection_to_vulnerability(scan_id, detection)
                record.vulnerabilities.append(vuln)
                self.vulnerabilities[vuln["vulnerability_id"]] = vuln
                self.recent_activity.appendleft(
                    {
                        "timestamp": vuln["detected_at"],
                        "threat_type": vuln["threat_type"],
                        "severity": vuln["severity"],
                        "summary": vuln["description"],
                        "source_ip": vuln.get("source_ip"),
                    }
                )

            record.detections = [self._serialize_detection(d) for d in detections]
            record.status = "completed"
            record.completed_at = datetime.now(timezone.utc)

            self.metrics["successful_scans"] += 1
            self.metrics["open_vulnerabilities"] = sum(
                1 for vuln in self.vulnerabilities.values() if vuln.get("status") == "open"
            )
            duration_ms = (record.completed_at - record.started_at).total_seconds() * 1000
            self._update_average_duration(duration_ms)
            self.metrics["last_scan_at"] = record.completed_at.isoformat()

            await self.audit_logger.log_event(
                level=AuditLevel.SECURITY,
                category=EventCategory.SECURITY_INCIDENT,
                event_type="security_scan_completed",
                message=f"Security scan {scan_id} completed with {len(record.vulnerabilities)} findings",
                details={
                    "scan_id": scan_id,
                    "scan_type": scan_type,
                    "vulnerabilities": len(record.vulnerabilities),
                },
                context=AuditContext(api_endpoint="/security/scans", http_method="POST"),
                risk_score=50 if record.vulnerabilities else 10,
                severity="high" if record.vulnerabilities else "low",
                source_component="security_scanner",
            )

            return self.get_scan_results(scan_id)
        except Exception as exc:  # pragma: no cover - defensive fallback
            record.status = "failed"
            record.completed_at = datetime.now(timezone.utc)
            self.metrics["failed_scans"] += 1
            await self.audit_logger.log_event(
                level=AuditLevel.ERROR,
                category=EventCategory.SECURITY_INCIDENT,
                event_type="security_scan_failed",
                message=f"Security scan {scan_id} failed: {exc}",
                details={"scan_id": scan_id, "error": str(exc)},
                context=AuditContext(api_endpoint="/security/scans", http_method="POST"),
                severity="critical",
                source_component="security_scanner",
            )
            raise

    def get_scan_status(self, scan_id: str) -> Dict[str, Any]:
        record = self.scans.get(scan_id)
        if not record:
            return {"scan_id": scan_id, "status": "not_found"}
        return {
            "scan_id": scan_id,
            "status": record.status,
            "scan_type": record.scan_type,
            "started_at": record.started_at.isoformat(),
            "completed_at": record.completed_at.isoformat() if record.completed_at else None,
            "vulnerability_count": len(record.vulnerabilities),
        }

    def get_scan_results(self, scan_id: str) -> Dict[str, Any]:
        record = self.scans.get(scan_id)
        if not record:
            return {"scan_id": scan_id, "status": "not_found"}
        return {
            "scan_id": scan_id,
            "status": record.status,
            "scan_type": record.scan_type,
            "started_at": record.started_at.isoformat(),
            "completed_at": record.completed_at.isoformat() if record.completed_at else None,
            "detections": record.detections,
            "vulnerabilities": record.vulnerabilities,
        }

    def list_vulnerabilities(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        vulnerabilities = list(self.vulnerabilities.values())
        if status:
            vulnerabilities = [v for v in vulnerabilities if v.get("status") == status]
        vulnerabilities.sort(key=lambda item: item.get("detected_at", ""), reverse=True)
        return vulnerabilities

    def resolve_vulnerability(self, vulnerability_id: str, resolution: Optional[str] = None) -> Dict[str, Any]:
        vuln = self.vulnerabilities.get(vulnerability_id)
        if not vuln:
            return {"vulnerability_id": vulnerability_id, "status": "not_found"}
        if vuln.get("status") == "resolved":
            return vuln
        vuln["status"] = "resolved"
        vuln["resolved_at"] = datetime.now(timezone.utc).isoformat()
        if resolution:
            vuln.setdefault("resolution_notes", resolution)
        self.metrics["resolved_vulnerabilities"] += 1
        self.metrics["open_vulnerabilities"] = max(0, self.metrics["open_vulnerabilities"] - 1)
        return vuln

    def get_recent_activity(self, limit: int = 20) -> List[Dict[str, Any]]:
        return list(self.recent_activity)[:limit]

    def get_metrics(self) -> Dict[str, Any]:
        return dict(self.metrics)

    def _build_security_event(self, payload: Dict[str, Any]) -> SecurityEvent:
        timestamp = payload.get("timestamp")
        if isinstance(timestamp, str):
            try:
                timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            except ValueError:
                timestamp = datetime.now(timezone.utc)
        elif not isinstance(timestamp, datetime):
            timestamp = datetime.now(timezone.utc)

        return SecurityEvent(
            event_id=payload.get("event_id", f"scan_event_{uuid.uuid4().hex[:8]}"),
            timestamp=timestamp,
            source_ip=payload.get("source_ip", "0.0.0.0"),
            user_id=payload.get("user_id"),
            event_type=payload.get("event_type", "scan_event"),
            resource=payload.get("resource", payload.get("endpoint", "unknown")),
            payload=payload.get("payload", payload),
            user_agent=payload.get("user_agent"),
            session_id=payload.get("session_id"),
            request_id=payload.get("request_id"),
        )

    def _detection_to_vulnerability(self, scan_id: str, detection: ThreatDetection) -> Dict[str, Any]:
        vuln_id = f"vuln-{uuid.uuid4().hex[:8]}"
        vulnerability = {
            "vulnerability_id": vuln_id,
            "scan_id": scan_id,
            "threat_type": detection.threat_type.value,
            "severity": detection.threat_level.value,
            "confidence": detection.confidence,
            "description": detection.description,
            "detected_at": detection.detected_at.isoformat(),
            "source_ip": detection.source_ip,
            "user_id": detection.user_id,
            "evidence": detection.evidence,
            "status": "open",
            "response_actions": [action.value for action in detection.response_actions],
        }
        return vulnerability

    def _serialize_detection(self, detection: ThreatDetection) -> Dict[str, Any]:
        return {
            "detection_id": detection.detection_id,
            "threat_type": detection.threat_type.value,
            "threat_level": detection.threat_level.value,
            "confidence": detection.confidence,
            "description": detection.description,
            "detected_at": detection.detected_at.isoformat(),
            "source_ip": detection.source_ip,
            "user_id": detection.user_id,
            "evidence": detection.evidence,
            "status": detection.status.value,
        }

    def _update_average_duration(self, duration_ms: float) -> None:
        total_scans = self.metrics["total_scans"]
        prev_avg = self.metrics["average_scan_duration_ms"]
        self.metrics["average_scan_duration_ms"] = (
            prev_avg + (duration_ms - prev_avg) / max(total_scans, 1)
        )

    def _default_event_payload(self) -> Dict[str, Any]:
        return {
            "event_type": "system_health_check",
            "source_ip": "127.0.0.1",
            "resource": "internal",
            "payload": {"message": "Synthetic health event"},
        }

