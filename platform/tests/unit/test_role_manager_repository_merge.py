import os
import sys
from pathlib import Path
import asyncio
from datetime import datetime, timezone

# Ensure backend modules are importable
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


def test_role_manager_merges_repository_assignments(monkeypatch):
    from core_platform.authentication.role_manager import (
        RoleManager,
        RoleAssignment,
        RoleScope,
        RoleStatus,
        AssignmentType,
    )

    class FakeRepo:
        async def load_user_assignments(self, user_id: str, *, include_inactive=False, scope=None):
            # Return one ACTIVE and one INACTIVE assignment to test filtering
            return [
                RoleAssignment(
                    assignment_id="repo_active",
                    user_id=user_id,
                    role_id="app_admin",
                    scope=RoleScope.GLOBAL,
                    status=RoleStatus.ACTIVE,
                    assignment_type=AssignmentType.DIRECT,
                    assigned_by="repo",
                    assigned_at=datetime.now(timezone.utc),
                ),
                RoleAssignment(
                    assignment_id="repo_inactive",
                    user_id=user_id,
                    role_id="si_admin",
                    scope=RoleScope.GLOBAL,
                    status=RoleStatus.INACTIVE,
                    assignment_type=AssignmentType.DIRECT,
                    assigned_by="repo",
                    assigned_at=datetime.now(timezone.utc),
                ),
            ]

    rm = RoleManager({}, repository=FakeRepo())

    # Seed an in-memory assignment
    user_id = "user-123"
    mem_assignment = RoleAssignment(
        assignment_id="mem_1",
        user_id=user_id,
        role_id="user",
        scope=RoleScope.TENANT,
        status=RoleStatus.ACTIVE,
        assignment_type=AssignmentType.DIRECT,
        assigned_by="system",
        assigned_at=datetime.now(timezone.utc),
    )
    rm.assignments[mem_assignment.assignment_id] = mem_assignment
    rm.user_assignments[user_id] = [mem_assignment.assignment_id]

    roles = asyncio.run(rm.get_user_roles(user_id))
    # Should include the in-memory + repo ACTIVE (but not repo INACTIVE)
    ids = {a.assignment_id for a in roles}
    assert "mem_1" in ids
    assert "repo_active" in ids
    assert "repo_inactive" not in ids

