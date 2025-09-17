"""
Payment Integration Models
==========================

SQLAlchemy models to persist payment processor connections and webhooks.
"""
from __future__ import annotations

import uuid
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Enum, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .base import BaseModel
from .banking import get_json_type


class PaymentProvider(str, PyEnum):
    PAYSTACK = "paystack"
    MONIEPOINT = "moniepoint"
    OPAY = "opay"
    PALMPAY = "palmpay"
    INTERSWITCH = "interswitch"
    FLUTTERWAVE = "flutterwave"
    STRIPE = "stripe"


class PaymentConnectionStatus(str, PyEnum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PENDING = "pending"
    ERROR = "error"


class PaymentConnection(BaseModel):
    __tablename__ = "payment_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    si_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True)

    provider = Column(Enum(PaymentProvider), nullable=False)
    provider_connection_id = Column(String(255), nullable=True)
    status = Column(Enum(PaymentConnectionStatus), default=PaymentConnectionStatus.PENDING, nullable=False)
    account_reference = Column(String(255), nullable=True)

    connection_metadata = Column(get_json_type(), default={})

    webhooks = relationship("PaymentWebhook", back_populates="connection", cascade="all, delete-orphan")


class PaymentWebhook(BaseModel):
    __tablename__ = "payment_webhooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("payment_connections.id"), nullable=True, index=True)
    si_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    provider = Column(Enum(PaymentProvider), nullable=False)
    endpoint_url = Column(String(500), nullable=False)
    secret = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    webhook_metadata = Column(get_json_type(), default={})

    connection = relationship("PaymentConnection", back_populates="webhooks")


class PaymentStatus(str, PyEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PaymentTransaction(BaseModel):
    __tablename__ = "payment_transactions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("payment_connections.id", ondelete="CASCADE"), nullable=False, index=True)
    provider = Column(Enum(PaymentProvider), nullable=False)
    provider_transaction_id = Column(String(255), nullable=False, index=True)
    amount = Column(String(50), nullable=False)
    currency = Column(String(3), default="NGN")
    status = Column(Enum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    occurred_at = Column(DateTime(timezone=True), nullable=True)
    transaction_metadata = Column(get_json_type(), default={})
