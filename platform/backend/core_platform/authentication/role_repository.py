"""
Role Repository (Stub)
======================

Provides an optional persistence interface for RoleManager to load role
assignments from a backing store. This stub returns empty results and serves
as a contract for future DB-backed implementations.
"""
from __future__ import annotations

from typing import List, Optional

from .role_manager import RoleAssignment, RoleScope


class RoleRepository:
    async def load_user_assignments(
        self,
        user_id: str,
        *,
        include_inactive: bool = False,
        scope: Optional[RoleScope] = None,
    ) -> List[RoleAssignment]:
        raise NotImplementedError


class StubRoleRepository(RoleRepository):
    async def load_user_assignments(
        self,
        user_id: str,
        *,
        include_inactive: bool = False,
        scope: Optional[RoleScope] = None,
    ) -> List[RoleAssignment]:
        # Placeholder stub; real implementation should query persistence
        return []

