import os
import sys
import hmac
import hashlib
import json
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

# Ensure backend modules are importable
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


class StubMessageRouter:
    """Stub async MessageRouter that records last call."""

    def __init__(self):
        self.calls = []

    async def route_message(self, *, service_role, operation, payload):
        self.calls.append({
            "service_role": service_role,
            "operation": operation,
            "payload": payload,
        })
        # Return a simple echo result to verify plumbing
        return {"operation": operation, "received": True}


def _hmac_sha256(secret: str, signed_payload: str) -> str:
    return hmac.new(secret.encode("utf-8"), signed_payload.encode("utf-8"), hashlib.sha256).hexdigest()


def _hmac_sha512(secret: str, payload: str) -> str:
    return hmac.new(secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha512).hexdigest()


def test_firs_webhook_valid_signature_routes(monkeypatch):
    # Ensure secret is set for FIRS webhook router
    monkeypatch.setenv("FIRS_WEBHOOK_SECRET", "test_firs_secret")

    from api_gateway.api_versions.v1.webhook_endpoints.firs_webhook import create_firs_webhook_router
    
    app = FastAPI()
    stub_router = StubMessageRouter()
    app.include_router(create_firs_webhook_router(stub_router))
    client = TestClient(app)

    # Build payload and signature
    payload = {
        "event_type": "invoice.accepted",
        "submission_id": "sub-123",
        "irn": "IRN-ABC",
        "status": {"code": "ACCEPTED"},
    }
    body = json.dumps(payload)
    ts = str(int(datetime.utcnow().timestamp()))
    sig = _hmac_sha256("test_firs_secret", f"{ts}.{body}")

    r = client.post(
        "/webhooks/firs/callback",
        data=body,
        headers={
            "x-firs-signature": sig,
            "x-firs-timestamp": ts,
            "x-firs-event": "invoice.accepted",
            "content-type": "application/json",
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["success"] is True
    # Verify message router call includes the processing op (order may vary)
    assert stub_router.calls, "route_message was not called"
    ops = [c["operation"] for c in stub_router.calls]
    assert "process_firs_webhook" in ops
    # Find the specific call to process_firs_webhook and validate payload
    webhook_calls = [c for c in stub_router.calls if c["operation"] == "process_firs_webhook"]
    assert webhook_calls, "process_firs_webhook call not recorded"
    assert webhook_calls[-1]["payload"]["event_type"] == "invoice.accepted"


def test_firs_webhook_bad_signature_unauthorized(monkeypatch):
    monkeypatch.setenv("FIRS_WEBHOOK_SECRET", "test_firs_secret")
    from api_gateway.api_versions.v1.webhook_endpoints.firs_webhook import create_firs_webhook_router

    app = FastAPI()
    app.include_router(create_firs_webhook_router(StubMessageRouter()))
    client = TestClient(app)

    body = json.dumps({"event_type": "invoice.rejected", "submission_id": "sub-999"})
    ts = str(int(datetime.utcnow().timestamp()))
    bad_sig = "deadbeef"
    r = client.post(
        "/webhooks/firs/callback",
        data=body,
        headers={
            "x-firs-signature": bad_sig,
            "x-firs-timestamp": ts,
            "content-type": "application/json",
        },
    )
    assert r.status_code == 401


def test_firs_webhook_invalid_json_returns_400(monkeypatch):
    monkeypatch.setenv("FIRS_WEBHOOK_SECRET", "test_firs_secret")
    from api_gateway.api_versions.v1.webhook_endpoints.firs_webhook import create_firs_webhook_router

    app = FastAPI()
    app.include_router(create_firs_webhook_router(StubMessageRouter()))
    client = TestClient(app)

    # Invalid JSON body but correct signature over the raw body string
    body = "{ invalid json"
    ts = str(int(datetime.utcnow().timestamp()))
    sig = _hmac_sha256("test_firs_secret", f"{ts}.{body}")

    r = client.post(
        "/webhooks/firs/callback",
        data=body,
        headers={
            "x-firs-signature": sig,
            "x-firs-timestamp": ts,
            "content-type": "application/json",
        },
    )
    assert r.status_code == 400


def test_mono_webhook_valid_signature_routes():
    from api_gateway.api_versions.v1.webhook_endpoints.mono_webhook import create_mono_webhook_router

    # Mono router hardcodes secret to this value in code
    mono_secret = "sec_O62WW0RY6TP8ZGOPNILU"

    app = FastAPI()
    stub_router = StubMessageRouter()
    app.include_router(create_mono_webhook_router(stub_router))
    client = TestClient(app)

    payload = {
        "event": "account.linked",
        "account_id": "acct_123",
        "data": {"bank": "TestBank"},
    }
    body = json.dumps(payload)
    ts = str(int(datetime.utcnow().timestamp()))
    sig = _hmac_sha256(mono_secret, f"{ts}.{body}")

    r = client.post(
        "/integrations/mono/webhook",
        data=body,
        headers={
            "x-mono-signature": sig,
            "x-mono-timestamp": ts,
            "content-type": "application/json",
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()
    assert data["success"] is True
    # Verify it routed
    assert stub_router.calls, "route_message was not called"
    call = stub_router.calls[-1]
    assert call["operation"] == "process_account_linked"


def test_mono_webhook_bad_signature_unauthorized():
    from api_gateway.api_versions.v1.webhook_endpoints.mono_webhook import create_mono_webhook_router

    app = FastAPI()
    app.include_router(create_mono_webhook_router(StubMessageRouter()))
    client = TestClient(app)

    body = json.dumps({"event": "transaction.created", "account_id": "acct_999", "data": {"id": "tx1", "amount": 1000}})
    ts = str(int(datetime.utcnow().timestamp()))
    r = client.post(
        "/integrations/mono/webhook",
        data=body,
        headers={
            "x-mono-signature": "bad",
            "x-mono-timestamp": ts,
            "content-type": "application/json",
        },
    )
    assert r.status_code == 401


def test_mono_webhook_invalid_json_returns_400():
    from api_gateway.api_versions.v1.webhook_endpoints.mono_webhook import create_mono_webhook_router

    app = FastAPI()
    app.include_router(create_mono_webhook_router(StubMessageRouter()))
    client = TestClient(app)

    body = "{ invalid json"
    ts = str(int(datetime.utcnow().timestamp()))
    # Signature computed over raw body
    sig = _hmac_sha256("sec_O62WW0RY6TP8ZGOPNILU", f"{ts}.{body}")

    r = client.post(
        "/integrations/mono/webhook",
        data=body,
        headers={
            "x-mono-signature": sig,
            "x-mono-timestamp": ts,
            "content-type": "application/json",
        },
    )
    assert r.status_code == 400


def test_payment_webhook_valid_signature_routes(monkeypatch):
    # Use default test secret in router
    from api_gateway.api_versions.v1.webhook_endpoints.payment_webhook import create_payment_webhook_router

    app = FastAPI()
    stub_router = StubMessageRouter()
    app.include_router(create_payment_webhook_router(stub_router))
    client = TestClient(app)

    payload = {"event": "charge.success", "data": {"id": "pay_123", "amount": 5000}}
    body = json.dumps(payload)
    sig = _hmac_sha512("test_paystack_secret", body)

    r = client.post(
        "/payments/callback",
        data=body,
        headers={"x-paystack-signature": sig, "content-type": "application/json"},
    )
    assert r.status_code == 200
    assert stub_router.calls and stub_router.calls[-1]["operation"] == "process_payment_webhook"


def test_payment_webhook_bad_signature_unauthorized():
    from api_gateway.api_versions.v1.webhook_endpoints.payment_webhook import create_payment_webhook_router

    app = FastAPI()
    app.include_router(create_payment_webhook_router(StubMessageRouter()))
    client = TestClient(app)

    body = json.dumps({"event": "charge.failed", "data": {"id": "pay_999"}})
    r = client.post(
        "/payments/callback",
        data=body,
        headers={"x-paystack-signature": "bad", "content-type": "application/json"},
    )
    assert r.status_code == 401
