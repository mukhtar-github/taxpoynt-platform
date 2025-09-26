from dataclasses import dataclass
from datetime import datetime, timedelta

from platform.backend.app_services import build_certificate_overview_payload


@dataclass
class DummyStoredCertificate:
    certificate_id: str
    subject_cn: str
    issuer_cn: str
    serial_number: str
    not_before: str
    not_after: str
    fingerprint: str
    status: str
    file_path: str
    organization_id: str
    certificate_type: str
    created_at: str
    updated_at: str
    metadata: dict


def _make_stored_certificate(
    certificate_id: str,
    *,
    status: str,
    not_after: datetime,
    organization_id: str,
) -> DummyStoredCertificate:
    iso_now = datetime.utcnow().isoformat()
    return DummyStoredCertificate(
        certificate_id=certificate_id,
        subject_cn="Test Subject",
        issuer_cn="Test Issuer",
        serial_number="123456",
        not_before=iso_now,
        not_after=not_after.isoformat(),
        fingerprint="abc123",
        status=status,
        file_path=f"/tmp/{certificate_id}.pem",
        organization_id=organization_id,
        certificate_type="signing",
        created_at=iso_now,
        updated_at=iso_now,
        metadata={},
    )


def test_build_certificate_overview_payload_counts_and_enrichment():
    org_id = "org-123"
    now = datetime.utcnow()
    active_expiry = now + timedelta(days=10)
    expired_expiry = now - timedelta(days=5)

    certificates = [
        {
            "certificate_id": "cert-active",
            "status": "active",
            "not_after": active_expiry.isoformat(),
            "organization_id": org_id,
        },
        {
            "certificate_id": "cert-expired",
            "status": "expired",
            "not_after": expired_expiry.isoformat(),
            "organization_id": org_id,
        },
    ]

    expiring = [
        {
            "certificate_id": "cert-active",
            "not_after": active_expiry.isoformat(),
        }
    ]

    lifecycle = {
        "needs_renewal": [
            _make_stored_certificate(
                "cert-active",
                status="active",
                not_after=active_expiry,
                organization_id=org_id,
            )
        ],
        "expired": [
            _make_stored_certificate(
                "cert-expired",
                status="expired",
                not_after=expired_expiry,
                organization_id=org_id,
            )
        ],
    }

    overview = build_certificate_overview_payload(
        certificates,
        expiring,
        lifecycle,
        organization_id=org_id,
        days_ahead=30,
    )

    assert overview["organizationId"] == org_id
    assert overview["summary"]["total"] == 2
    assert overview["summary"]["statusCounts"]["active"] == 1
    assert overview["summary"]["statusCounts"]["expired"] == 1
    assert overview["summary"]["needsRenewal"] == 1
    assert overview["summary"]["expiringSoon"] == 1

    lifecycle_summary = overview["lifecycle"]
    assert lifecycle_summary["needs_renewal"]["count"] == 1
    assert lifecycle_summary["expired"]["count"] == 1

    certificates_section = overview["certificates"]
    assert certificates_section["count"] == 2
    days_values = {item["certificate_id"]: item.get("days_until_expiry") for item in certificates_section["items"]}
    assert days_values["cert-active"] is not None
    assert days_values["cert-expired"] is not None
