"""
Idempotency Store (Async)
=========================
Helper for DB-backed idempotency using the IdempotencyKey model.
Falls back to in-memory cache if DB operations fail (best-effort).
"""
from __future__ import annotations

import asyncio
import json
import hashlib
from typing import Any, Dict, Optional, Tuple
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError

from core_platform.data_management.models import IdempotencyKey, IdempotencyStatus


_MEM_CACHE: Dict[str, Dict[str, Any]] = {}
_MEM_LOCK = asyncio.Lock()


def _canonical_json_hash(data: Any) -> str:
    try:
        normalized = json.dumps(data, sort_keys=True, separators=(",", ":"))
    except Exception:
        normalized = json.dumps(str(data))
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


class IdempotencyStore:
    @staticmethod
    def compute_request_hash(body: Any) -> str:
        return _canonical_json_hash(body)

    @staticmethod
    async def try_begin(
        db: AsyncSession,
        *,
        requester_id: Optional[str],
        key: str,
        method: str,
        endpoint: str,
        request_hash: str,
    ) -> Tuple[bool, Optional[Dict[str, Any]], Optional[int], bool]:
        """
        Attempt to create an idempotency record.
        Returns (existing, response_data, status_code) if a completed record exists.
        If not existing, creates an IN_PROGRESS record and returns (False, None, None).
        """
        try:
            # Check existing
            stmt = select(IdempotencyKey).where(
                IdempotencyKey.requester_id == requester_id,
                IdempotencyKey.key == key,
            )
            res = await db.execute(stmt)
            row: Optional[IdempotencyKey] = res.scalars().first()
            if row:
                # Body mismatch => conflict
                if row.request_hash and row.request_hash != request_hash:
                    return True, None, None, True
                if row.status == IdempotencyStatus.SUCCEEDED and row.response_data is not None:
                    return True, row.response_data, row.status_code or 200, False
                # In-progress or failed: treat as existing but not ready
                return True, None, None, False

            # Insert IN_PROGRESS
            idem = IdempotencyKey(
                requester_id=requester_id,
                key=key,
                method=method.upper(),
                endpoint=endpoint,
                request_hash=request_hash,
                status=IdempotencyStatus.IN_PROGRESS,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
            db.add(idem)
            await db.commit()
            return False, None, None, False
        except IntegrityError:
            await db.rollback()
            # Someone else inserted concurrently; re-check
            stmt = select(IdempotencyKey).where(
                IdempotencyKey.requester_id == requester_id,
                IdempotencyKey.key == key,
            )
            res = await db.execute(stmt)
            row = res.scalars().first()
            if row:
                if row.request_hash and row.request_hash != request_hash:
                    return True, None, None, True
                if row.status == IdempotencyStatus.SUCCEEDED and row.response_data is not None:
                    return True, row.response_data, row.status_code or 200, False
            return True, None, None, False
        except Exception:
            # Fallback to per-process memory cache
            async with _MEM_LOCK:
                scope = f"{requester_id}:{key}"
                if scope in _MEM_CACHE:
                    entry = _MEM_CACHE[scope]
                    if entry.get("hash") and entry.get("hash") != request_hash:
                        return True, None, None, True
                    if entry.get("status") == "succeeded":
                        return True, entry.get("response"), entry.get("status_code") or 200, False
                    return True, None, None, False
                _MEM_CACHE[scope] = {"status": "in_progress", "endpoint": endpoint, "method": method, "hash": request_hash}
            return False, None, None, False

    @staticmethod
    async def cleanup(db: AsyncSession, *, older_than_days: int = 7) -> int:
        """Delete idempotency rows older than TTL. Returns rows deleted."""
        from sqlalchemy import delete, func
        try:
            cutoff = func.now() - func.make_interval(0,0,0, older_than_days)
            # Use plain SQL to be dialect-friendly if needed
            stmt = delete(IdempotencyKey).where(IdempotencyKey.created_at < cutoff)
            res = await db.execute(stmt)
            await db.commit()
            return res.rowcount or 0
        except Exception:
            return 0

    @staticmethod
    async def finalize_success(
        db: AsyncSession,
        *,
        requester_id: Optional[str],
        key: str,
        response: Dict[str, Any],
        status_code: int,
    ) -> None:
        try:
            stmt = (
                update(IdempotencyKey)
                .where(IdempotencyKey.requester_id == requester_id, IdempotencyKey.key == key)
                .values(
                    status=IdempotencyStatus.SUCCEEDED,
                    response_data=response,
                    status_code=status_code,
                    updated_at=datetime.utcnow(),
                )
            )
            await db.execute(stmt)
            await db.commit()
        except Exception:
            # Best-effort memory cache update
            async with _MEM_LOCK:
                scope = f"{requester_id}:{key}"
                if scope in _MEM_CACHE:
                    _MEM_CACHE[scope].update({
                        "status": "succeeded",
                        "response": response,
                        "status_code": status_code,
                    })
