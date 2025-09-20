"""
TaxPoynt Platform - Organization Models
=====================================
Organization and company models for business entity management.
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, Boolean, Text, JSON, Enum, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel

class BusinessType(enum.Enum):
    """Nigerian business entity types."""
    
    SOLE_PROPRIETORSHIP = "sole_proprietorship"
    PARTNERSHIP = "partnership" 
    LIMITED_COMPANY = "limited_company"
    PUBLIC_COMPANY = "public_company"
    NON_PROFIT = "non_profit"
    COOPERATIVE = "cooperative"

class OrganizationStatus(enum.Enum):
    """Organization status in the platform."""
    
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"

class Organization(BaseModel):
    """Organization model for business entities using TaxPoynt services."""
    
    __tablename__ = "organizations"
    
    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    name = Column(String(255), nullable=False, index=True)
    business_name = Column(String(255), nullable=True)  # Trading name if different
    
    # Business registration details
    business_type = Column(Enum(BusinessType), nullable=True)
    tin = Column(String(50), nullable=True, index=True)  # Tax Identification Number
    rc_number = Column(String(50), nullable=True, index=True)  # Registration Certificate number
    vat_number = Column(String(50), nullable=True)
    
    # Contact information
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    website = Column(String(255), nullable=True)
    
    # Address information
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    state = Column(String(100), nullable=True)
    lga = Column(String(100), nullable=True)  # Local Government Area
    postal_code = Column(String(20), nullable=True)
    country = Column(String(50), default="Nigeria", nullable=False)
    
    # Platform status
    status = Column(Enum(OrganizationStatus), default=OrganizationStatus.ACTIVE, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    verification_documents = Column(JSON, nullable=True)  # Store document references
    
    # FIRS integration
    firs_service_id = Column(String(50), nullable=True, unique=True, index=True)
    firs_app_status = Column(String(50), default="pending", nullable=False)  # pending, active, suspended
    
    # Branding and customization
    logo_url = Column(String(500), nullable=True)
    branding_settings = Column(JSON, nullable=True)  # UI customization settings
    
    # Nigerian compliance fields
    cac_registration_date = Column(String(50), nullable=True)
    business_commencement_date = Column(String(50), nullable=True)
    authorized_share_capital = Column(String(100), nullable=True)
    paid_up_capital = Column(String(100), nullable=True)
    
    # Service configuration
    service_packages = Column(JSON, nullable=True)  # Services subscribed to
    integration_preferences = Column(JSON, nullable=True)  # User preferences
    firs_configuration = Column(JSON, nullable=True)  # FIRS-specific configuration (service_id, environment, etc.)
    
    # Soft delete and data lifecycle management
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime(timezone=True), nullable=True)
    deleted_by = Column(UUID(as_uuid=True), nullable=True)  # User who deleted this org
    deletion_reason = Column(String(255), nullable=True)
    scheduled_hard_delete_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    users = relationship("User", foreign_keys="[User.organization_id]", back_populates="organization")
    organization_users = relationship("OrganizationUser", back_populates="organization", cascade="all, delete-orphan")
    integrations = relationship("Integration", back_populates="organization", cascade="all, delete-orphan")
    firs_submissions = relationship("FIRSSubmission", back_populates="organization", cascade="all, delete-orphan")
    si_app_correlations = relationship("SIAPPCorrelation", back_populates="organization", cascade="all, delete-orphan")
    
    @property
    def display_name(self) -> str:
        """Get organization display name."""
        return self.business_name or self.name
    
    @property
    def primary_contact(self) -> str:
        """Get primary contact information."""
        return self.email or self.phone or "No contact information"
    
    @property
    def is_registered_company(self) -> bool:
        """Check if organization has RC number (registered company)."""
        return bool(self.rc_number)
    
    @property
    def has_tax_registration(self) -> bool:
        """Check if organization has tax registration."""
        return bool(self.tin)
    
    def get_firs_service_id(self) -> str:
        """Get FIRS service ID for this organization."""
        if self.firs_configuration and 'service_id' in self.firs_configuration:
            return self.firs_configuration['service_id']
        # Fallback to default service ID
        return "94ND90NR"  # Default FIRS-assigned Service ID
    
    def set_firs_service_id(self, service_id: str):
        """Set FIRS service ID for this organization."""
        if not self.firs_configuration:
            self.firs_configuration = {}
        self.firs_configuration['service_id'] = service_id
    
    def get_active_integrations(self):
        """Get all active integrations for this organization."""
        return [integration for integration in self.integrations if integration.is_active]
    
    def get_service_package_list(self) -> list[str]:
        """Get list of subscribed service packages."""
        if self.service_packages and isinstance(self.service_packages, list):
            return self.service_packages
        return []
    
    def soft_delete(self, deleted_by_user_id: str = None, reason: str = None) -> None:
        """Soft delete the organization."""
        from datetime import datetime, timezone
        self.is_deleted = True
        self.deleted_at = datetime.now(timezone.utc)
        self.deleted_by = deleted_by_user_id
        self.deletion_reason = reason
        self.status = OrganizationStatus.SUSPENDED
        
    def restore(self) -> None:
        """Restore a soft-deleted organization."""
        self.is_deleted = False
        self.deleted_at = None
        self.deleted_by = None
        self.deletion_reason = None
        self.status = OrganizationStatus.ACTIVE
        
    def schedule_hard_delete(self, days_from_now: int = 2190) -> None:  # 6 years for tax data
        """Schedule organization data for hard deletion (for compliance)."""
        from datetime import datetime, timezone, timedelta
        self.scheduled_hard_delete_at = datetime.now(timezone.utc) + timedelta(days=days_from_now)
        
    @property
    def is_manageable(self) -> bool:
        """Check if organization can be managed (not deleted and active)."""
        return not self.is_deleted and self.status == OrganizationStatus.ACTIVE

class OrganizationUser(BaseModel):
    """Many-to-many relationship between users and organizations."""
    
    __tablename__ = "organization_users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False)
    
    # Role within the organization
    role = Column(String(50), default="member", nullable=False)  # owner, admin, member, viewer
    is_primary_contact = Column(Boolean, default=False, nullable=False)
    
    # Access permissions
    permissions = Column(JSON, nullable=True)  # Specific permissions within organization
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Invitation tracking
    invited_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    invitation_accepted_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="organization_users")
    organization = relationship("Organization", back_populates="organization_users")
    invited_by = relationship("User", foreign_keys=[invited_by_user_id])
    
    @property
    def is_owner(self) -> bool:
        """Check if user is organization owner."""
        return self.role == "owner"
    
    @property
    def is_admin(self) -> bool:
        """Check if user has admin privileges."""
        return self.role in ["owner", "admin"]
    
    @property
    def can_manage_users(self) -> bool:
        """Check if user can manage other users."""
        return self.is_admin and self.is_active
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has specific permission."""
        if not self.is_active:
            return False
        if self.is_owner:
            return True
        if self.permissions and isinstance(self.permissions, list):
            return permission in self.permissions
        return False