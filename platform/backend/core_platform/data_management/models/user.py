"""
TaxPoynt Platform - User Models
==============================
User authentication and role management models for the platform.
"""

import uuid
import enum
from datetime import datetime
from sqlalchemy import Boolean, Column, String, Enum, DateTime, func, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
from .base import BaseModel

class UserRole(enum.Enum):
    """User role enumeration for service access control."""
    
    # Service-based roles
    SI_USER = "si_user"                    # Systems Integration user
    APP_USER = "app_user"                  # Access Point Provider user  
    HYBRID_USER = "hybrid_user"            # Hybrid service user (SI + APP)
    
    # Business roles
    BUSINESS_OWNER = "business_owner"      # Business owner/primary contact
    BUSINESS_ADMIN = "business_admin"      # Business administrator
    BUSINESS_USER = "business_user"        # Regular business user
    
    # Platform roles
    PLATFORM_ADMIN = "platform_admin"     # TaxPoynt platform administrator
    SUPPORT_USER = "support_user"          # Customer support user

class ServiceType(enum.Enum):
    """Service types available in the platform."""
    
    SI_SERVICE = "si_service"              # Systems Integration
    APP_SERVICE = "app_service"            # Access Point Provider
    HYBRID_SERVICE = "hybrid_service"      # Combined SI + APP
    PLATFORM_ADMIN = "platform_admin"     # Platform administration

class AccessLevel(enum.Enum):
    """Access levels for service permissions."""
    
    READ = "read"                          # Read-only access
    WRITE = "write"                        # Read and write access
    ADMIN = "admin"                        # Full administrative access

class User(BaseModel):
    """User model for authentication and authorization."""
    
    __tablename__ = "users"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    
    # Personal information
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    
    # Primary role and service package
    role = Column(Enum(UserRole), default=UserRole.SI_USER, nullable=False)
    service_package = Column(String(20), default="si", nullable=False)  # si, app, hybrid
    
    # Email verification
    email_verification_token = Column(String(255), nullable=True)
    email_verification_sent_at = Column(DateTime(timezone=True), nullable=True)
    
    # Password reset
    password_reset_token = Column(String(255), nullable=True)
    password_reset_at = Column(DateTime(timezone=True), nullable=True)
    password_reset_expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Login tracking
    last_login = Column(DateTime(timezone=True), nullable=True)
    login_count = Column(Integer, default=0, nullable=False)
    
    # Consent and agreements
    terms_accepted_at = Column(DateTime(timezone=True), nullable=True)
    privacy_accepted_at = Column(DateTime(timezone=True), nullable=True)
    data_usage_consents = Column(String, nullable=True)  # JSON string of consents
    
    # Organization relationship (primary organization for user)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True)
    
    # Relationships  
    organization = relationship("Organization", foreign_keys="[User.organization_id]", back_populates="users")
    organization_users = relationship("OrganizationUser", foreign_keys="[OrganizationUser.user_id]", back_populates="user", cascade="all, delete-orphan")
    service_access = relationship("UserServiceAccess", foreign_keys="[UserServiceAccess.user_id]", back_populates="user", cascade="all, delete-orphan")
    
    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.email.split("@")[0]
    
    @property
    def is_business_user(self) -> bool:
        """Check if user has business-level access."""
        business_roles = [UserRole.BUSINESS_OWNER, UserRole.BUSINESS_ADMIN, UserRole.BUSINESS_USER]
        return self.role in business_roles
    
    @property
    def is_platform_admin(self) -> bool:
        """Check if user is a platform administrator."""
        return self.role == UserRole.PLATFORM_ADMIN
    
    def has_service_access(self, service_type: ServiceType, access_level: AccessLevel = AccessLevel.READ) -> bool:
        """Check if user has access to a specific service with required level."""
        for access in self.service_access:
            if (access.service_type == service_type and 
                self._has_sufficient_access_level(access.access_level, access_level)):
                return True
        return False
    
    def _has_sufficient_access_level(self, user_level: AccessLevel, required_level: AccessLevel) -> bool:
        """Check if user's access level is sufficient for required level."""
        level_hierarchy = {
            AccessLevel.READ: 1,
            AccessLevel.WRITE: 2,
            AccessLevel.ADMIN: 3
        }
        return level_hierarchy[user_level] >= level_hierarchy[required_level]

class UserServiceAccess(BaseModel):
    """User access control for specific services."""
    
    __tablename__ = "user_service_access"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    service_type = Column(Enum(ServiceType), nullable=False)
    access_level = Column(Enum(AccessLevel), default=AccessLevel.READ, nullable=False)
    
    # Subscription and billing
    is_active = Column(Boolean, default=True, nullable=False)
    subscription_status = Column(String(50), default="active", nullable=False)  # active, suspended, expired
    subscription_tier = Column(String(50), nullable=True)  # basic, premium, enterprise
    
    # Access tracking
    granted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    granted_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    last_accessed = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="service_access")
    granted_by = relationship("User", foreign_keys=[granted_by_user_id])
    
    @property
    def is_expired(self) -> bool:
        """Check if access has expired."""
        return self.expires_at is not None and self.expires_at < datetime.utcnow()
    
    @property
    def is_valid(self) -> bool:
        """Check if access is currently valid."""
        return (self.is_active and 
                self.subscription_status == "active" and 
                not self.is_expired)