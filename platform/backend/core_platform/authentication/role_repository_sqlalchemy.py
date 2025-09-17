"""
SQLAlchemy Role Repository (Async)
==================================

Loads role assignments from the core data models using an AsyncSession factory.
This is a minimal mapping to support persistence-backed role contexts.
"""
from __future__ import annotations

from typing import Callable, Coroutine, Any, Optional, List, Set
import uuid
from datetime import datetime, timezone
import os

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .role_manager import RoleAssignment, RoleScope, RoleStatus, AssignmentType
from core_platform.data_management.models.user import User, UserRole
from core_platform.data_management.models.organization import OrganizationUser


class SQLAlchemyRoleRepository:
    def __init__(self, session_factory: Callable[[], Coroutine[Any, Any, AsyncSession]]):
        self._session_factory = session_factory
        # Optional enrichment until DB models are introduced
        self._load_permissions = str(os.getenv("ROLE_REPO_LOAD_PERMISSIONS", "false")).lower() in ("1", "true", "yes", "on")

    async def load_user_assignments(
        self,
        user_id: str,
        *,
        include_inactive: bool = False,
        scope: Optional[RoleScope] = None,
    ) -> List[RoleAssignment]:
        assignments: List[RoleAssignment] = []
        async with self._session_factory() as db:
            # Load primary user role
            user = (await db.execute(select(User).where(User.id == uuid.UUID(user_id)))).scalars().first() if _is_uuid(user_id) else None
            if user:
                primary_role_id = _map_user_role_to_role_id(user.role)
                assignments.append(
                    RoleAssignment(
                        assignment_id=f"primary_{user.id}",
                        user_id=str(user.id),
                        role_id=primary_role_id,
                        scope=RoleScope.GLOBAL if user.role == UserRole.PLATFORM_ADMIN else RoleScope.TENANT,
                        status=RoleStatus.ACTIVE if user.is_active else RoleStatus.INACTIVE,
                        assignment_type=AssignmentType.DIRECT,
                        assigned_by="system",
                        assigned_at=datetime.now(timezone.utc),
                        tenant_id=str(user.organization_id) if user.organization_id else None,
                        metadata={"source": "sqlalchemy_repo"},
                    )
                )

            # Load organization-level roles
            if _is_uuid(user_id):
                rows = (
                    await db.execute(
                        select(OrganizationUser).where(OrganizationUser.user_id == uuid.UUID(user_id))
                    )
                ).scalars().all()
                for row in rows:
                    role_id = row.role or "org_member"
                    assignments.append(
                        RoleAssignment(
                            assignment_id=f"org_{row.id}",
                            user_id=str(row.user_id),
                            role_id=role_id,
                            scope=RoleScope.TENANT,
                            status=RoleStatus.ACTIVE if row.is_active else RoleStatus.INACTIVE,
                            assignment_type=AssignmentType.DIRECT,
                            assigned_by="system",
                            assigned_at=datetime.now(timezone.utc),
                            tenant_id=str(row.organization_id),
                            metadata={"source": "sqlalchemy_repo", "org_role": row.role},
                        )
                    )

            # Optional enrichment: attach effective permissions (placeholder or model-backed when available)
            if self._load_permissions:
                for a in assignments:
                    perms = await _try_load_permissions(db, a.role_id)
                    if not perms:
                        perms = _default_permissions_for_role(a.role_id)
                    if perms:
                        a.metadata["effective_permissions"] = sorted(list(perms))

        # Filter by scope and status when requested
        if scope:
            assignments = [a for a in assignments if a.scope == scope]
        if not include_inactive:
            assignments = [a for a in assignments if a.status == RoleStatus.ACTIVE]
        return assignments


def _is_uuid(value: str) -> bool:
    try:
        uuid.UUID(str(value))
        return True
    except Exception:
        return False


def _map_user_role_to_role_id(user_role: Optional[UserRole]) -> str:
    if not user_role:
        return "user"
    # Map platform enum to RoleManager role IDs
    if user_role == UserRole.PLATFORM_ADMIN:
        return "platform_admin"
    if user_role == UserRole.SI_USER:
        return "si_admin"
    if user_role == UserRole.APP_USER:
        return "app_admin"
    if user_role == UserRole.HYBRID_USER:
        return "hybrid_admin"
    # Business roles collapse to basic user
    return "user"


async def _try_load_permissions(db: AsyncSession, role_id: str) -> Set[str]:
    """Load effective permissions for a role_id using RBAC tables, including inheritance.

    - Direct permissions via rbac_role_permissions
    - Inherited permissions by traversing rbac_permission_hierarchy upward
    """
    try:
        from core_platform.data_management.models.rbac import (
            Role as DBRole,
            Permission as DBPerm,
            RolePermission as DBRolePerm,
            PermissionHierarchy as DBPermHier,
        )

        role = (await db.execute(select(DBRole).where(DBRole.role_id == role_id))).scalars().first()
        if not role:
            return set()

        # Collect role inheritance closure (child -> parents)
        from core_platform.data_management.models.rbac import RoleInheritance as DBRoleInh
        edges = (
            await db.execute(
                select(DBRoleInh.parent_role_id, DBRoleInh.child_role_id)
            )
        ).all()
        parents_by_child = {}
        for parent_id, child_id in edges:
            parents_by_child.setdefault(child_id, set()).add(parent_id)

        collected_roles = {role.id}
        frontier = [role.id]
        while frontier:
            current = frontier.pop()
            new_parents = parents_by_child.get(current, set()) - collected_roles
            if new_parents:
                collected_roles.update(new_parents)
                frontier.extend(new_parents)

        # Direct permissions for role set
        direct_perm_rows = (
            await db.execute(
                select(DBPerm.id, DBPerm.name)
                .join(DBRolePerm, DBRolePerm.permission_id == DBPerm.id)
                .where(DBRolePerm.role_id.in_(list(collected_roles)))
            )
        ).all()
        if not direct_perm_rows:
            return set()

        id_to_name = {pid: name for (pid, name) in direct_perm_rows}
        collected_ids: Set[str] = set(id_to_name.keys())

        # Load hierarchy edges and walk ancestors (child -> parent)
        edges = (
            await db.execute(
                select(DBPermHier.parent_permission_id, DBPermHier.child_permission_id)
            )
        ).all()
        parent_by_child = {}
        for parent_id, child_id in edges:
            parent_by_child.setdefault(child_id, set()).add(parent_id)

        # Also map names for any parents we may discover
        async def ensure_name_map(perm_ids: Set[str]):
            missing = [pid for pid in perm_ids if pid not in id_to_name]
            if not missing:
                return
            rows = (
                await db.execute(select(DBPerm.id, DBPerm.name).where(DBPerm.id.in_(missing)))
            ).all()
            for pid, name in rows:
                id_to_name[pid] = name

        # BFS up the hierarchy to include implied parent permissions
        frontier = list(collected_ids)
        while frontier:
            current = frontier.pop()
            parents = parent_by_child.get(current, set())
            new_parents = parents - collected_ids
            if new_parents:
                collected_ids.update(new_parents)
                await ensure_name_map(new_parents)
                frontier.extend(new_parents)

        return {id_to_name[pid] for pid in collected_ids if pid in id_to_name}
    except Exception:
        return set()


def _default_permissions_for_role(role_id: str) -> Set[str]:
    """Fallback permission mapping until RBAC models are ready."""
    mapping = {
        "platform_admin": {"*"},
        "si_admin": {"integrations.read", "integrations.write", "invoices.read", "invoices.write", "certificates.manage"},
        "app_admin": {"invoices.read", "invoices.write", "compliance.read", "taxpayers.manage"},
        "hybrid_admin": {"integrations.read", "invoices.read", "invoices.write", "compliance.read", "taxpayers.manage"},
        "user": {"invoices.read"},
    }
    return mapping.get(role_id, set())
