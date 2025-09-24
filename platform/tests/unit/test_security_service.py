import asyncio
import base64
import shutil

import pytest

from core_platform.messaging.message_router import MessageRouter
from app_services import APPServiceRegistry
from app_services.security_compliance.encryption_service import EncryptionService
from app_services.security_compliance.audit_logger import AuditLogger
from app_services.security_compliance.threat_detector import ThreatDetector
from app_services.security_compliance.security_scanner import SecurityScanner


@pytest.fixture
def security_environment(tmp_path):
    registry = APPServiceRegistry(MessageRouter())

    audit_dir = tmp_path / "audit_logs"
    audit_logger = AuditLogger(log_directory=str(audit_dir))
    encryption_service = EncryptionService()
    threat_detector = ThreatDetector()
    security_scanner = SecurityScanner(threat_detector=threat_detector, audit_logger=audit_logger)

    security_service = {
        "encryption_service": encryption_service,
        "audit_logger": audit_logger,
        "scanner": security_scanner,
        "threat_detector": threat_detector,
    }

    callback = registry._create_security_callback(security_service)

    yield security_service, callback

    shutil.rmtree(audit_dir, ignore_errors=True)


@pytest.mark.asyncio
async def test_run_security_scan(security_environment):
    service_state, callback = security_environment

    scan_response = await callback(
        "run_security_scan",
        {
            "scan_scope": [
                {
                    "event_type": "login_failure",
                    "source_ip": "192.168.1.10",
                    "payload": {"username": "admin", "attempts": 12},
                }
            ]
        },
    )

    assert scan_response["success"] is True
    scan_data = scan_response["data"]
    assert scan_data["scan_id"].startswith("scan-")

    status_response = await callback("get_scan_status", {"scan_id": scan_data["scan_id"]})
    assert status_response["data"]["scan_id"] == scan_data["scan_id"]

    vulns_response = await callback("list_vulnerabilities", {})
    assert vulns_response["success"] is True
    assert isinstance(vulns_response["data"]["vulnerabilities"], list)


@pytest.mark.asyncio
async def test_access_logs_and_metrics(security_environment):
    service_state, callback = security_environment

    await callback(
        "log_security_event",
        {
            "event": {
                "event_type": "user_access",
                "level": "security",
                "category": "security_incident",
                "message": "Test access event",
                "details": {"user_id": "tester"},
            }
        },
    )

    logs_response = await callback("get_access_logs", {"limit": 5})
    assert logs_response["success"] is True
    assert logs_response["data"]["count"] >= 1

    metrics_response = await callback("get_security_metrics", {})
    assert metrics_response["success"] is True
    assert "scanner" in metrics_response["data"]
    assert "auditing" in metrics_response["data"]


@pytest.mark.asyncio
async def test_encryption_roundtrip(security_environment):
    service_state, callback = security_environment
    document = {"message": "hello"}

    encrypt_response = await callback("encrypt_document", {"document": document})
    assert encrypt_response["success"] is True
    encrypted = encrypt_response["data"]
    assert base64.b64decode(encrypted["data"])  # ensure valid base64 payload

    decrypt_response = await callback(
        "decrypt_document",
        {"encrypted_data": encrypted, "document_id": encrypted["document_id"]},
    )
    assert decrypt_response["success"] is True
    assert decrypt_response["data"]["document"] == document
