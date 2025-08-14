"""
TaxPoynt Platform - Integration Models
====================================
Models for managing business system integrations and credentials.
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, Boolean, Text, JSON, DateTime, Integer, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel

class IntegrationType(enum.Enum):
    """Types of business system integrations."""
    
    # ERP Systems
    ODOO = "odoo"
    SAP = "sap" 
    QUICKBOOKS = "quickbooks"
    XERO = "xero"
    ORACLE_ERP = "oracle_erp"
    MICROSOFT_DYNAMICS = "microsoft_dynamics"
    
    # CRM Systems
    SALESFORCE = "salesforce"
    HUBSPOT = "hubspot"
    ZOHO_CRM = "zoho_crm"
    MICROSOFT_CRM = "microsoft_crm"
    
    # POS Systems
    SQUARE = "square"
    SHOPIFY = "shopify"
    CLOVER = "clover"
    
    # Nigerian Systems
    MONIEPOINT = "moniepoint"
    PAYSTACK = "paystack"
    FLUTTERWAVE = "flutterwave"
    INTERSWITCH = "interswitch"
    
    # Banking and Financial
    MONO = "mono"
    OKRA = "okra"
    PLAID = "plaid"
    
    # Accounting
    SAGE = "sage"
    WAVE = "wave"
    FRESHBOOKS = "freshbooks"

class IntegrationStatus(enum.Enum):
    """Integration connection status."""
    
    ACTIVE = "active"
    INACTIVE = "inactive" 
    CONNECTING = "connecting"
    FAILED = "failed"
    SUSPENDED = "suspended"
    EXPIRED = "expired"

class AuthMethod(enum.Enum):
    """Authentication methods for integrations."""
    
    OAUTH2 = "oauth2"
    API_KEY = "api_key"
    USERNAME_PASSWORD = "username_password"
    JWT = "jwt"
    WEBHOOK = "webhook"

class Integration(BaseModel):
    """Integration configuration for business systems."""
    
    __tablename__ = "integrations"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Integration details
    integration_type = Column(Enum(IntegrationType), nullable=False)
    name = Column(String(255), nullable=False)  # User-friendly name
    description = Column(Text, nullable=True)
    
    # Connection details
    status = Column(Enum(IntegrationStatus), default=IntegrationStatus.CONNECTING, nullable=False)
    auth_method = Column(Enum(AuthMethod), nullable=False)
    endpoint_url = Column(String(500), nullable=True)
    
    # Configuration
    configuration = Column(JSON, nullable=True)  # Integration-specific config
    sync_settings = Column(JSON, nullable=True)  # Sync preferences
    field_mappings = Column(JSON, nullable=True)  # Field mapping configuration
    
    # Status and health
    is_active = Column(Boolean, default=True, nullable=False)
    last_sync_at = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    error_count = Column(Integer, default=0, nullable=False)
    
    # Performance tracking
    total_records_synced = Column(Integer, default=0, nullable=False)
    sync_frequency = Column(String(50), default="hourly", nullable=False)  # hourly, daily, weekly
    
    # Access control
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="integrations")
    credentials = relationship("IntegrationCredentials", back_populates="integration", cascade="all, delete-orphan")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    
    @property
    def is_healthy(self) -> bool:
        """Check if integration is healthy (active and no recent errors)."""
        return (self.is_active and 
                self.status == IntegrationStatus.ACTIVE and 
                self.error_count < 5)
    
    @property
    def needs_attention(self) -> bool:
        """Check if integration needs attention."""
        return (self.status == IntegrationStatus.FAILED or 
                self.error_count >= 3 or
                (self.last_sync_at and 
                 (datetime.utcnow() - self.last_sync_at).days > 1))
    
    @property
    def display_name(self) -> str:
        """Get display name for integration."""
        return f"{self.name} ({self.integration_type.value.title()})"
    
    def get_credential(self, key: str) -> str:
        """Get specific credential value."""
        for credential in self.credentials:
            if credential.key_name == key and credential.is_active:
                return credential.decrypt_value()
        return None
    
    def update_sync_status(self, success: bool, error_message: str = None):
        """Update sync status and error tracking."""
        self.last_sync_at = datetime.utcnow()
        if success:
            self.status = IntegrationStatus.ACTIVE
            self.error_count = 0
            self.last_error = None
        else:
            self.error_count += 1
            self.last_error = error_message
            if self.error_count >= 5:
                self.status = IntegrationStatus.FAILED

class IntegrationCredentials(BaseModel):
    """Secure storage for integration credentials."""
    
    __tablename__ = "integration_credentials"
    
    # Primary identification  
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    integration_id = Column(UUID(as_uuid=True), ForeignKey("integrations.id"), nullable=False)
    
    # Credential details
    key_name = Column(String(100), nullable=False)  # api_key, client_id, username, etc.
    encrypted_value = Column(Text, nullable=False)  # Encrypted credential value
    
    # Metadata
    is_active = Column(Boolean, default=True, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    
    # Security tracking
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    rotation_required = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    integration = relationship("Integration", back_populates="credentials")
    created_by = relationship("User", foreign_keys=[created_by_user_id])
    
    @property
    def is_expired(self) -> bool:
        """Check if credential has expired."""
        return self.expires_at is not None and self.expires_at < datetime.utcnow()
    
    @property
    def is_valid(self) -> bool:
        """Check if credential is currently valid."""
        return self.is_active and not self.is_expired
    
    def decrypt_value(self) -> str:
        """Decrypt and return credential value."""
        # TODO: Implement proper encryption/decryption
        # For now, return as-is (in production, use proper encryption)
        return self.encrypted_value
    
    def encrypt_value(self, value: str) -> None:
        """Encrypt and store credential value."""
        # TODO: Implement proper encryption
        # For now, store as-is (in production, use proper encryption)
        self.encrypted_value = value
    
    def mark_as_used(self) -> None:
        """Mark credential as recently used."""
        self.last_used_at = datetime.utcnow()