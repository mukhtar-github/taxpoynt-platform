import os
import sys
import asyncio
from pathlib import Path
import uuid as uuidlib

import pytest

# Ensure backend modules are importable
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.mark.asyncio
async def test_sqlalchemy_role_repository_loads_assignments():
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import select

    from core_platform.data_management.models.base import BaseModel
    from core_platform.data_management.models.user import User, UserRole
    from core_platform.data_management.models.organization import Organization, OrganizationUser
    from core_platform.authentication.role_repository_sqlalchemy import SQLAlchemyRoleRepository

    # In-memory async SQLite
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    # Seed one org, one user, one org membership
    async with SessionLocal() as db:
        org = Organization(name="Acme Inc")
        db.add(org)
        await db.flush()

        user = User(email="user@example.com", hashed_password="x", role=UserRole.APP_USER, service_package="app", organization_id=org.id, is_active=True)
        db.add(user)
        await db.flush()

        ou = OrganizationUser(user_id=user.id, organization_id=org.id, role="member", is_primary_contact=False, is_active=True)
        db.add(ou)
        await db.commit()

        # Sanity check
        assert (await db.execute(select(User).where(User.id == user.id))).scalars().first() is not None

    # Repository that uses our sessionmaker
    async def session_factory():
        return SessionLocal()

    repo = SQLAlchemyRoleRepository(session_factory)

    # Load assignments
    assignments = await repo.load_user_assignments(str(user.id))
    # Expect at least primary and org membership
    ids = {a.assignment_id for a in assignments}
    assert any(i.startswith("primary_") for i in ids)
    assert any(i.startswith("org_") for i in ids)
    # Check mapped role IDs include app_admin for APP_USER
    role_ids = {a.role_id for a in assignments}
    assert "app_admin" in role_ids

