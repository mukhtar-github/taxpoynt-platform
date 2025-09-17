"""
RBAC Models
===========

Lightweight role-based access control models to support repository-backed
permission enrichment. Designed to work with SQLAlchemy AsyncSession.
"""
from __future__ import annotations

import uuid
from sqlalchemy import Column, String, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from .base import BaseModel


class Role(BaseModel):
    __tablename__ = "rbac_roles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    # Stable identifier used by app code, e.g., "app_admin", "si_admin"
    role_id = Column(String(100), unique=True, nullable=False, index=True)
    name = Column(String(150), nullable=True)
    description = Column(String(500), nullable=True)

    permissions = relationship("RolePermission", back_populates="role", cascade="all, delete-orphan")


class Permission(BaseModel):
    __tablename__ = "rbac_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    # Canonical permission name, e.g., "invoices.read"
    name = Column(String(150), unique=True, nullable=False, index=True)
    description = Column(String(500), nullable=True)

    role_links = relationship("RolePermission", back_populates="permission", cascade="all, delete-orphan")
    parent_links = relationship("PermissionHierarchy", foreign_keys="[PermissionHierarchy.parent_permission_id]", back_populates="parent", cascade="all, delete-orphan")
    child_links = relationship("PermissionHierarchy", foreign_keys="[PermissionHierarchy.child_permission_id]", back_populates="child", cascade="all, delete-orphan")


class RolePermission(BaseModel):
    __tablename__ = "rbac_role_permissions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    role_id = Column(UUID(as_uuid=True), ForeignKey("rbac_roles.id", ondelete="CASCADE"), nullable=False, index=True)
    permission_id = Column(UUID(as_uuid=True), ForeignKey("rbac_permissions.id", ondelete="CASCADE"), nullable=False, index=True)

    role = relationship("Role", back_populates="permissions")
    permission = relationship("Permission", back_populates="role_links")

    __table_args__ = (
        UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )


class PermissionHierarchy(BaseModel):
    """Defines an implication relationship: child implies parent.

    Example: child = "integrations.write" implies parent = "integrations.read".
    """
    __tablename__ = "rbac_permission_hierarchy"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    parent_permission_id = Column(UUID(as_uuid=True), ForeignKey("rbac_permissions.id", ondelete="CASCADE"), nullable=False, index=True)
    child_permission_id = Column(UUID(as_uuid=True), ForeignKey("rbac_permissions.id", ondelete="CASCADE"), nullable=False, index=True)

    parent = relationship("Permission", foreign_keys=[parent_permission_id], back_populates="parent_links")
    child = relationship("Permission", foreign_keys=[child_permission_id], back_populates="child_links")

    __table_args__ = (
        UniqueConstraint("parent_permission_id", "child_permission_id", name="uq_permission_hierarchy"),
    )

__all__ = [
    "Role",
    "Permission",
    "RolePermission",
    "PermissionHierarchy",
]


class RoleInheritance(BaseModel):
    """Defines role composition: child role inherits from parent role.

    Example: child = "app_admin" inherits parent = "base_reader".
    """
    __tablename__ = "rbac_role_inheritance"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    parent_role_id = Column(UUID(as_uuid=True), ForeignKey("rbac_roles.id", ondelete="CASCADE"), nullable=False, index=True)
    child_role_id = Column(UUID(as_uuid=True), ForeignKey("rbac_roles.id", ondelete="CASCADE"), nullable=False, index=True)

    parent = relationship("Role", foreign_keys=[parent_role_id])
    child = relationship("Role", foreign_keys=[child_role_id])

    __table_args__ = (
        UniqueConstraint("parent_role_id", "child_role_id", name="uq_role_inheritance"),
    )

__all__ += [
    "RoleInheritance",
]
