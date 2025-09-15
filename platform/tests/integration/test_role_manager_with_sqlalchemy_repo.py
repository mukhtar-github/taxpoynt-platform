import os
import sys
import asyncio
from pathlib import Path
from datetime import datetime, timezone

import pytest

# Ensure backend modules are importable
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.mark.asyncio
async def test_role_manager_with_sqlalchemy_repo_merges_assignments():
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import select

    from core_platform.data_management.models.base import BaseModel
    from core_platform.data_management.models.user import User, UserRole
    from core_platform.data_management.models.organization import Organization, OrganizationUser
    from core_platform.authentication.role_repository_sqlalchemy import SQLAlchemyRoleRepository
    from core_platform.authentication.role_manager import (
        RoleManager,
        RoleAssignment,
        RoleScope,
        RoleStatus,
        AssignmentType,
    )

    # In-memory async SQLite
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    # Seed org + user + org membership
    async with SessionLocal() as db:
        org = Organization(name="Acme Org")
        db.add(org)
        await db.flush()

        user = User(email="merge@example.com", hashed_password="x", role=UserRole.SI_USER, service_package="si", organization_id=org.id, is_active=True)
        db.add(user)
        await db.flush()

        ou = OrganizationUser(user_id=user.id, organization_id=org.id, role="member", is_primary_contact=False, is_active=True)
        db.add(ou)
        await db.commit()

    async def session_factory():
        return SessionLocal()

    repo = SQLAlchemyRoleRepository(session_factory)

    # RoleManager with repository + one in-memory assignment
    rm = RoleManager({}, repository=repo)
    mem_assignment = RoleAssignment(
        assignment_id="mem_1",
        user_id=str(user.id),
        role_id="user",
        scope=RoleScope.TENANT,
        status=RoleStatus.ACTIVE,
        assignment_type=AssignmentType.DIRECT,
        assigned_by="system",
        assigned_at=datetime.now(timezone.utc),
    )
    rm.assignments[mem_assignment.assignment_id] = mem_assignment
    rm.user_assignments[str(user.id)] = [mem_assignment.assignment_id]

    roles = await rm.get_user_roles(str(user.id))
    ids = {a.assignment_id for a in roles}
    # Expect in-memory + at least primary/org assignments from repo
    assert "mem_1" in ids
    assert any(i.startswith("primary_") for i in ids)
    assert any(i.startswith("org_") for i in ids)

