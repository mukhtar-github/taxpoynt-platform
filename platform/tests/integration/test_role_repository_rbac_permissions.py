import os
import sys
import asyncio
from pathlib import Path

import pytest

# Ensure backend modules are importable
BACKEND_DIR = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


@pytest.mark.asyncio
async def test_role_repository_permission_enrichment_with_rbac():
    # Enable permission enrichment
    os.environ["ROLE_REPO_LOAD_PERMISSIONS"] = "true"

    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
    from sqlalchemy import select

    from core_platform.data_management.models.base import BaseModel
    from core_platform.data_management.models.user import User, UserRole
    from core_platform.data_management.models.organization import Organization
    from core_platform.data_management.models.rbac import Role, Permission, RolePermission, PermissionHierarchy, RoleInheritance
    from core_platform.authentication.role_repository_sqlalchemy import SQLAlchemyRoleRepository

    # In-memory async SQLite
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    SessionLocal = async_sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)

    async with engine.begin() as conn:
        await conn.run_sync(BaseModel.metadata.create_all)

    # Seed org, user and RBAC data
    async with SessionLocal() as db:
        org = Organization(name="RBAC Co")
        db.add(org)
        await db.flush()

        user = User(email="rbac@example.com", hashed_password="x", role=UserRole.APP_USER, service_package="app", organization_id=org.id, is_active=True)
        db.add(user)
        await db.flush()

        # RBAC: app_admin role and permissions
        role = Role(role_id="app_admin", name="APP Admin")
        base_reader = Role(role_id="base_reader", name="Base Reader")
        p_read = Permission(name="invoices.read")
        p_write = Permission(name="invoices.write")
        p_integrations_read = Permission(name="integrations.read")
        db.add_all([role, base_reader, p_read, p_write, p_integrations_read])
        await db.flush()

        # app_admin -> invoices.write (and write implies read)
        rp = RolePermission(role_id=role.id, permission_id=p_write.id)
        edge = PermissionHierarchy(parent_permission_id=p_read.id, child_permission_id=p_write.id)
        # base_reader -> integrations.read, and app_admin inherits base_reader
        rp2 = RolePermission(role_id=base_reader.id, permission_id=p_integrations_read.id)
        inh = RoleInheritance(parent_role_id=base_reader.id, child_role_id=role.id)
        db.add_all([rp, edge, rp2, inh])
        await db.commit()

    async def session_factory():
        return SessionLocal()

    repo = SQLAlchemyRoleRepository(session_factory)
    assignments = await repo.load_user_assignments(str(user.id))

    # Find the primary app_admin assignment
    primary = [a for a in assignments if a.role_id == "app_admin"]
    assert primary, "expected primary app_admin assignment"
    enriched = primary[0].metadata.get("effective_permissions", [])
    # Expect both write and implied read present
    assert "invoices.write" in enriched
    assert "invoices.read" in enriched
    # Expect role inheritance to bring integrations.read
    assert "integrations.read" in enriched
