"""
TaxPoynt Platform - Network / Four-Corner Models
================================================
Participant registry for four-corner delivery (buyer/supplier AP discovery).
"""

from sqlalchemy import Column, String, DateTime, Enum as SAEnum, Text, Index
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
from enum import Enum as PyEnum
import uuid

from .base import BaseModel
from .business_systems import get_json_type


class ParticipantRole(str, PyEnum):
    BUYER = "buyer"
    SUPPLIER = "supplier"


class ParticipantStatus(str, PyEnum):
    ACTIVE = "active"
    SUSPENDED = "suspended"


class DeliveryProtocol(str, PyEnum):
    HTTP = "http"
    AS4 = "as4"


class Participant(BaseModel):
    """Network participant (buyer/supplier access point).

    - identifier: external ID (e.g., TIN/GLN) used to resolve routing
    - ap_endpoint_url: delivery endpoint for buyer/supplier AP
    - preferred_protocol: http/as4 (future expansion)
    - public_key / certificate_pem: for message security when applicable
    - last_seen_at: last successful interaction
    - metadata: arbitrary JSON for capabilities, codelists, etc.
    """

    __tablename__ = "participants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    # Optional tenant scoping; when null, participant entry is global
    organization_id = Column(UUID(as_uuid=True), nullable=True)

    identifier = Column(String(128), nullable=False, unique=True)
    role = Column(SAEnum(ParticipantRole), nullable=False)
    status = Column(SAEnum(ParticipantStatus), nullable=False, default=ParticipantStatus.ACTIVE)

    ap_endpoint_url = Column(String(512), nullable=False)
    preferred_protocol = Column(SAEnum(DeliveryProtocol), nullable=False, default=DeliveryProtocol.HTTP)

    public_key = Column(Text, nullable=True)
    certificate_pem = Column(Text, nullable=True)

    last_seen_at = Column(DateTime(timezone=True), nullable=True)

    metadata_json = Column(get_json_type(), default={})

    __table_args__ = (
        Index("ix_participants_identifier", "identifier", unique=True),
        Index("ix_participants_org", "organization_id"),
    )

