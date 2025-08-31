"""
Admin Router - Platform Administration Endpoints
===============================================
Provides administrative endpoints for platform management.
Only accessible to platform administrators.
"""

import logging
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, status, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel

# Import auth utilities
from .auth_router import verify_access_token, get_user_by_id
from .auth_database import get_auth_database

logger = logging.getLogger(__name__)
security = HTTPBearer()

class UserManagementRequest(BaseModel):
    """Request model for user management operations."""
    reason: str
    
class AdminStatsResponse(BaseModel):
    """Response model for admin statistics."""
    total_users: int
    active_users: int
    deleted_users: int
    total_organizations: int
    active_organizations: int
    platform_health: str

def verify_admin_access(credentials: HTTPAuthorizationCredentials) -> dict:
    """Verify that the current user has admin access."""
    payload = verify_access_token(credentials.credentials)
    user_id = payload.get("user_id")
    
    current_user = get_user_by_id(user_id)
    if not current_user or current_user.get("role") not in ["platform_admin", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Platform administrator access required"
        )
    
    return current_user

def create_admin_router() -> APIRouter:
    """Factory function to create admin router."""
    
    router = APIRouter(prefix="/admin", tags=["Platform Administration"])
    
    @router.get("/dashboard/stats")
    async def get_admin_statistics(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Get platform statistics for admin dashboard."""
        try:
            # Verify admin access
            admin_user = verify_admin_access(credentials)
            
            # Get database stats
            db = get_auth_database()
            
            # Get user statistics
            all_users = db.get_all_users(include_deleted=True, limit=10000)  # Get all for stats
            active_users = [u for u in all_users if not u.get("is_deleted", False)]
            deleted_users = [u for u in all_users if u.get("is_deleted", False)]
            
            # Get organization statistics (mock for now since we don't have org methods yet)
            total_orgs = len(set(u.get("organization_id") for u in all_users if u.get("organization_id")))
            
            return AdminStatsResponse(
                total_users=len(all_users),
                active_users=len(active_users),
                deleted_users=len(deleted_users),
                total_organizations=total_orgs,
                active_organizations=total_orgs,  # Assume all orgs are active for now
                platform_health="healthy"
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get admin stats failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get admin statistics"
            )

    @router.get("/users")
    async def get_all_users(
        include_deleted: bool = Query(False, description="Include soft-deleted users"),
        limit: int = Query(100, le=1000, description="Number of users to return"),
        offset: int = Query(0, ge=0, description="Number of users to skip"),
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Get all users with pagination (admin only)."""
        try:
            # Verify admin access
            admin_user = verify_admin_access(credentials)
            
            # Get users from database
            db = get_auth_database()
            users = db.get_all_users(include_deleted=include_deleted, limit=limit, offset=offset)
            
            return JSONResponse(content={
                "users": users,
                "total": len(users),
                "include_deleted": include_deleted,
                "pagination": {
                    "limit": limit,
                    "offset": offset
                },
                "admin_user": admin_user.get("email"),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get all users failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get users"
            )

    @router.delete("/users/{user_id}")
    async def soft_delete_user(
        user_id: str,
        request: UserManagementRequest,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Soft delete a user (admin only)."""
        try:
            # Verify admin access
            admin_user = verify_admin_access(credentials)
            admin_user_id = admin_user.get("id")
            
            # Prevent self-deletion
            if admin_user_id == user_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Cannot delete your own account"
                )
            
            # Soft delete the user
            db = get_auth_database()
            success = db.soft_delete_user(user_id, admin_user_id, request.reason)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            logger.info(f"Admin {admin_user.get('email')} soft deleted user {user_id}")
            
            return JSONResponse(content={
                "message": f"User soft deleted successfully",
                "user_id": user_id,
                "deleted_by": admin_user.get("email"),
                "reason": request.reason,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Soft delete user failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to delete user"
            )

    @router.post("/users/{user_id}/restore")
    async def restore_user(
        user_id: str,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Restore a soft-deleted user (admin only)."""
        try:
            # Verify admin access
            admin_user = verify_admin_access(credentials)
            
            # Restore the user
            db = get_auth_database()
            success = db.restore_user(user_id)
            
            if not success:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found or not deleted"
                )
            
            logger.info(f"Admin {admin_user.get('email')} restored user {user_id}")
            
            return JSONResponse(content={
                "message": f"User restored successfully",
                "user_id": user_id,
                "restored_by": admin_user.get("email"),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Restore user failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to restore user"
            )

    @router.get("/users/{user_id}/audit")
    async def get_user_audit_log(
        user_id: str,
        credentials: HTTPAuthorizationCredentials = Depends(security)
    ):
        """Get audit log for a specific user (admin only)."""
        try:
            # Verify admin access
            admin_user = verify_admin_access(credentials)
            
            # Get user details including soft delete info
            db = get_auth_database()
            user = db.get_user_by_id(user_id, include_deleted=True)
            
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            # Build audit information
            audit_info = {
                "user_id": user_id,
                "email": user.get("email"),
                "current_status": {
                    "is_active": user.get("is_active"),
                    "is_deleted": user.get("is_deleted"),
                    "role": user.get("role")
                },
                "lifecycle_events": {
                    "created_at": user.get("created_at"),
                    "last_login": user.get("last_login"),
                    "deletion_info": {
                        "deleted_at": user.get("deleted_at"),
                        "deleted_by": user.get("deleted_by"),
                        "deletion_reason": user.get("deletion_reason")
                    } if user.get("is_deleted") else None
                },
                "organization_id": user.get("organization_id"),
                "service_package": user.get("service_package"),
                "retrieved_by": admin_user.get("email"),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            return JSONResponse(content=audit_info)
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get user audit failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user audit log"
            )
    
    return router