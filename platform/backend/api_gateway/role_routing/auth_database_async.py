"""
Async Auth Database Helpers
==========================

Async equivalents for a subset of auth_database helpers using AsyncSession
and SQLAlchemy select() patterns.
"""
from __future__ import annotations

from typing import Optional, Dict, Any
import uuid as _uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from core_platform.data_management.models.user import User
from core_platform.data_management.models.organization import Organization


async def get_user_by_id_async(db: AsyncSession, user_id: str, include_deleted: bool = False) -> Optional[Dict[str, Any]]:
    try:
        _user_id = user_id
        if isinstance(user_id, str):
            try:
                _user_id = _uuid.UUID(user_id)
            except ValueError:
                _user_id = user_id

        stmt = select(User).where(User.id == _user_id)
        if not include_deleted:
            stmt = stmt.where(User.is_deleted == False)  # noqa: E712
        res = await db.execute(stmt)
        user = res.scalars().first()
        if not user:
            return None
        return {
            "id": str(user.id),
            "email": user.email,
            "hashed_password": user.hashed_password,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone": user.phone,
            "role": user.role.value if user.role else None,
            "service_package": user.service_package,
            "is_active": user.is_active,
            "is_email_verified": user.is_email_verified,
            "organization_id": str(user.organization_id) if user.organization_id else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }
    except Exception:
        raise


async def get_organization_by_id_async(db: AsyncSession, org_id: str) -> Optional[Dict[str, Any]]:
    try:
        _org_id = org_id
        if isinstance(org_id, str):
            try:
                _org_id = _uuid.UUID(org_id)
            except ValueError:
                _org_id = org_id

        res = await db.execute(select(Organization).where(Organization.id == _org_id))
        org = res.scalars().first()
        if not org:
            return None
        return {
            "id": str(org.id),
            "name": org.name,
            "business_type": org.business_type.value if org.business_type else None,
            "tin": org.tin,
            "rc_number": org.rc_number,
            "status": org.status.value if org.status else None,
            "service_packages": org.get_service_package_list(),
            "created_at": org.created_at.isoformat() if org.created_at else None,
            "updated_at": org.updated_at.isoformat() if org.updated_at else None,
        }
    except Exception:
        raise

