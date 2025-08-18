"""
TaxPoynt Platform - Banking Database Models
==========================================
SQLAlchemy models for banking integration data persistence.
Supports Mono, Stitch, and Unified Banking providers.
"""

from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, Numeric, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from .base import BaseModel
import uuid
from enum import Enum as PyEnum


class BankingProvider(str, PyEnum):
    """Banking service providers"""
    MONO = "mono"
    STITCH = "stitch"
    UNIFIED_BANKING = "unified_banking"


class ConnectionStatus(str, PyEnum):
    """Banking connection status"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    PENDING = "pending"
    ERROR = "error"
    REAUTHORIZATION_REQUIRED = "reauthorization_required"


class TransactionType(str, PyEnum):
    """Banking transaction types"""
    CREDIT = "credit"
    DEBIT = "debit"


class AccountType(str, PyEnum):
    """Bank account types"""
    SAVINGS = "savings"
    CURRENT = "current"
    DOMICILIARY = "domiciliary"
    FIXED_DEPOSIT = "fixed_deposit"


class BankingConnection(BaseModel):
    """
    Banking service connections table.
    Stores connections to Mono, Stitch, and other banking providers.
    """
    __tablename__ = "banking_connections"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    si_id = Column(UUID(as_uuid=True), nullable=False)  # System Integrator ID
    organization_id = Column(UUID(as_uuid=True), nullable=True)  # Organization ID
    
    # Provider information
    provider = Column(Enum(BankingProvider), nullable=False)
    provider_connection_id = Column(String(255), nullable=False)  # Provider's internal ID
    provider_account_id = Column(String(255), nullable=True)  # Provider's account ID
    
    # Connection details
    status = Column(Enum(ConnectionStatus), default=ConnectionStatus.PENDING)
    bank_name = Column(String(255), nullable=True)
    bank_code = Column(String(20), nullable=True)
    account_number = Column(String(50), nullable=True)
    account_name = Column(String(255), nullable=True)
    account_type = Column(Enum(AccountType), nullable=True)
    
    # Authentication and tokens
    access_token = Column(Text, nullable=True)  # Encrypted
    refresh_token = Column(Text, nullable=True)  # Encrypted
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Connection metadata
    connection_metadata = Column(JSONB, default={})
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    sync_frequency_hours = Column(Integer, default=24)
    
    # Relationships
    accounts = relationship("BankAccount", back_populates="connection", cascade="all, delete-orphan")
    transactions = relationship("BankTransaction", back_populates="connection", cascade="all, delete-orphan")


class BankAccount(BaseModel):
    """
    Bank accounts table.
    Stores account information from banking providers.
    """
    __tablename__ = "bank_accounts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("banking_connections.id"), nullable=False)
    
    # Account identification
    provider_account_id = Column(String(255), nullable=False)  # Provider's account ID
    account_number = Column(String(50), nullable=False)
    account_name = Column(String(255), nullable=False)
    account_type = Column(Enum(AccountType), nullable=False)
    
    # Bank information
    bank_name = Column(String(255), nullable=False)
    bank_code = Column(String(20), nullable=False)
    currency = Column(String(3), default="NGN")
    
    # Account status
    is_active = Column(Boolean, default=True)
    balance = Column(Numeric(15, 2), nullable=True)
    available_balance = Column(Numeric(15, 2), nullable=True)
    last_balance_update = Column(DateTime(timezone=True), nullable=True)
    
    # Account metadata
    account_metadata = Column(JSONB, default={})
    
    # Relationships
    connection = relationship("BankingConnection", back_populates="accounts")
    transactions = relationship("BankTransaction", back_populates="account", cascade="all, delete-orphan")


class BankTransaction(BaseModel):
    """
    Bank transactions table.
    Stores transaction data from banking providers.
    """
    __tablename__ = "bank_transactions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("banking_connections.id"), nullable=False)
    account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"), nullable=False)
    
    # Transaction identification
    provider_transaction_id = Column(String(255), nullable=False)  # Provider's transaction ID
    transaction_reference = Column(String(255), nullable=True)
    
    # Transaction details
    transaction_type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Numeric(15, 2), nullable=False)
    currency = Column(String(3), default="NGN")
    description = Column(Text, nullable=True)
    narration = Column(Text, nullable=True)
    
    # Transaction timing
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    value_date = Column(DateTime(timezone=True), nullable=True)
    
    # Balance information
    balance_after = Column(Numeric(15, 2), nullable=True)
    
    # Counterparty information
    counterparty_name = Column(String(255), nullable=True)
    counterparty_account = Column(String(50), nullable=True)
    counterparty_bank = Column(String(255), nullable=True)
    
    # Transaction metadata
    transaction_metadata = Column(JSONB, default={})
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    connection = relationship("BankingConnection", back_populates="transactions")
    account = relationship("BankAccount", back_populates="transactions")


class BankingWebhook(BaseModel):
    """
    Banking webhooks table.
    Stores webhook events from banking providers.
    """
    __tablename__ = "banking_webhooks"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("banking_connections.id"), nullable=True)
    
    # Webhook identification
    provider = Column(Enum(BankingProvider), nullable=False)
    webhook_id = Column(String(255), nullable=True)  # Provider's webhook ID
    event_type = Column(String(100), nullable=False)
    
    # Webhook data
    webhook_data = Column(JSONB, nullable=False)
    raw_payload = Column(Text, nullable=True)
    
    # Processing status
    is_processed = Column(Boolean, default=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)
    processing_error = Column(Text, nullable=True)
    
    # Webhook metadata
    source_ip = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    signature = Column(Text, nullable=True)


class BankingSyncLog(BaseModel):
    """
    Banking sync logs table.
    Tracks synchronization operations with banking providers.
    """
    __tablename__ = "banking_sync_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    connection_id = Column(UUID(as_uuid=True), ForeignKey("banking_connections.id"), nullable=False)
    
    # Sync details
    sync_type = Column(String(50), nullable=False)  # accounts, transactions, balance
    status = Column(String(20), nullable=False)  # success, error, partial
    
    # Sync statistics
    records_processed = Column(Integer, default=0)
    records_created = Column(Integer, default=0)
    records_updated = Column(Integer, default=0)
    records_failed = Column(Integer, default=0)
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration_seconds = Column(Integer, nullable=True)
    
    # Error information
    error_message = Column(Text, nullable=True)
    error_details = Column(JSONB, default={})
    
    # Sync metadata
    sync_metadata = Column(JSONB, default={})


class BankingCredentials(BaseModel):
    """
    Banking credentials table.
    Stores encrypted API credentials for banking providers.
    """
    __tablename__ = "banking_credentials"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    si_id = Column(UUID(as_uuid=True), nullable=False)  # System Integrator ID
    
    # Provider information
    provider = Column(Enum(BankingProvider), nullable=False)
    environment = Column(String(20), default="production")  # sandbox, production
    
    # Credentials (encrypted)
    api_key = Column(Text, nullable=True)
    client_id = Column(Text, nullable=True)
    client_secret = Column(Text, nullable=True)
    webhook_secret = Column(Text, nullable=True)
    
    # Credential status
    is_active = Column(Boolean, default=True)
    last_validated_at = Column(DateTime(timezone=True), nullable=True)
    validation_status = Column(String(20), nullable=True)  # valid, invalid, pending
    
    # Credential metadata
    credentials_metadata = Column(JSONB, default={})