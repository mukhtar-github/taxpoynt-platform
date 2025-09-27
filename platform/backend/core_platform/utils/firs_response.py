"""Helpers for normalizing FIRS API responses."""

from __future__ import annotations

import json
from typing import Any, Dict, Iterable, Optional


def _iter_nodes(payload: Any) -> Iterable[Any]:
    """Yield every dictionary or list node within the payload."""

    stack = [payload]
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            yield node
            stack.extend(node.values())
        elif isinstance(node, list):
            stack.extend(node)


_IRN_KEYS = {"irn", "invoice_reference", "invoice_reference_number", "invoiceReference", "invoiceReferenceNumber"}
_CSID_KEYS = {"csid", "cryptographic_stamp", "cryptographicStamp"}
_CSID_HASH_KEYS = {"csidhash", "cryptographic_hash", "cryptographicHash"}
_QR_KEYS = {"qr", "qr_code", "qrCode", "qrPayload"}
_STAMP_METADATA_KEYS = {"stampmetadata", "cryptographic_stamp_metadata", "stampMetadata"}
_STATUS_KEYS = {"status", "status_text", "statusText", "firs_status", "firsStatus", "state"}
_STATUS_CODE_KEYS = {"statuscode", "status_code", "statusCode"}
_RESPONSE_ID_KEYS = {"submission_id", "submissionId", "response_id", "responseId"}


def extract_firs_identifiers(payload: Any) -> Dict[str, Any]:
    """Extract IRN/CSID/QR identifiers from a FIRS response payload."""

    if payload is None:
        return {}

    identifiers: Dict[str, Any] = {}

    def _maybe_json(value: Any) -> Any:
        if isinstance(value, str):
            text = value.strip()
            if text.startswith("{") or text.startswith("["):
                try:
                    return json.loads(text)
                except json.JSONDecodeError:
                    return value
        return value

    for node in _iter_nodes(payload):
        if not isinstance(node, dict):
            continue

        normalized_keys = {key.lower().replace("-", "").replace("_", ""): key for key in node.keys()}

        for alias in _IRN_KEYS:
            key = normalized_keys.get(alias.lower().replace("-", "").replace("_", ""))
            if key and node.get(key):
                identifiers.setdefault("irn", node[key])

        for alias in _CSID_KEYS:
            key = normalized_keys.get(alias.lower().replace("-", "").replace("_", ""))
            if key and node.get(key):
                identifiers.setdefault("csid", node[key])

        for alias in _CSID_HASH_KEYS:
            key = normalized_keys.get(alias.lower().replace("-", "").replace("_", ""))
            if key and node.get(key):
                identifiers.setdefault("csid_hash", node[key])

        for alias in _QR_KEYS:
            key = normalized_keys.get(alias.lower().replace("-", "").replace("_", ""))
            if key and node.get(key):
                identifiers.setdefault("qr_payload", _maybe_json(node[key]))

        for alias in _STAMP_METADATA_KEYS:
            key = normalized_keys.get(alias.lower().replace("-", "").replace("_", ""))
            if key and node.get(key):
                identifiers.setdefault("firs_stamp_metadata", _maybe_json(node[key]))

        for alias in _STATUS_KEYS:
            key = normalized_keys.get(alias.lower().replace("-", "").replace("_", ""))
            if key and node.get(key):
                identifiers.setdefault("status", node[key])

        for alias in _STATUS_CODE_KEYS:
            key = normalized_keys.get(alias.lower().replace("-", "").replace("_", ""))
            if key and node.get(key):
                identifiers.setdefault("status_code", node[key])

        for alias in _RESPONSE_ID_KEYS:
            key = normalized_keys.get(alias.lower().replace("-", "").replace("_", ""))
            if key and node.get(key):
                identifiers.setdefault("response_id", node[key])

    return identifiers


def merge_identifiers_into_payload(payload: Dict[str, Any], identifiers: Dict[str, Any]) -> Dict[str, Any]:
    """Merge normalized identifiers into the payload using canonical FIRS keys."""

    if not identifiers:
        return payload

    payload = payload.copy()
    payload.setdefault("identifiers", identifiers)

    irn = identifiers.get("irn")
    if irn and "irn" not in payload:
        payload["irn"] = irn

    csid = identifiers.get("csid")
    if csid:
        payload.setdefault("csid", csid)

    csid_hash = identifiers.get("csid_hash")
    if csid_hash:
        payload.setdefault("csidHash", csid_hash)

    qr_payload = identifiers.get("qr_payload")
    if qr_payload is not None:
        payload.setdefault("qr", qr_payload)

    stamp_metadata = identifiers.get("firs_stamp_metadata")
    if stamp_metadata is not None:
        payload.setdefault("stampMetadata", stamp_metadata)

    response_id = identifiers.get("response_id")
    if response_id and "submissionId" not in payload:
        payload["submissionId"] = response_id

    status_code = identifiers.get("status_code")
    if status_code and "statusCode" not in payload:
        payload["statusCode"] = status_code

    status_text = identifiers.get("status")
    if status_text and "status" not in payload:
        payload["status"] = status_text

    return payload


def map_firs_status_to_submission(status_text: Optional[str]) -> str:
    """Return a normalized status label."""

    if not status_text:
        return "submitted"
    normalized = str(status_text).strip().lower()
    if any(keyword in normalized for keyword in ("accept", "success", "approved")):
        return "accepted"
    if any(keyword in normalized for keyword in ("reject", "fail", "error")):
        return "rejected"
    if any(keyword in normalized for keyword in ("processing", "pending", "queue")):
        return "processing"
    return normalized or "submitted"
