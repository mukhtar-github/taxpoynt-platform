"""
Authentication Router - Shared Across All Service Types
======================================================
Provides authentication endpoints accessible to SI, APP, and Hybrid users.
Integrates with role-based routing system and supports user onboarding flow.
"""
import logging
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt
import os

# Fix import paths
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from core_platform.authentication.role_manager import PlatformRole
    from core_platform.messaging.message_router import MessageRouter, ServiceRole
except ImportError:
    # Use fallback classes from __init__.py
    from . import PlatformRole, MessageRouter, ServiceRole
from .models import HTTPRoutingContext
from .role_detector import HTTPRoleDetector
from .permission_guard import APIPermissionGuard

logger = logging.getLogger(__name__)

# Authentication configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "taxpoynt-platform-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))  # 24 hours

# Pydantic models for requests/responses
class UserRegisterRequest(BaseModel):
    """User registration request model"""
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    service_package: str = "si"  # si, app, hybrid
    business_name: str
    business_type: Optional[str] = None  # Now optional, collected during onboarding
    tin: Optional[str] = None
    rc_number: Optional[str] = None
    address: Optional[str] = None
    state: Optional[str] = None
    lga: Optional[str] = None
    terms_accepted: bool = False
    privacy_accepted: bool = False
    marketing_consent: bool = False
    consents: Optional[Dict[str, Any]] = None

class UserLoginRequest(BaseModel):
    """User login request model"""
    email: EmailStr
    password: str
    remember_me: Optional[bool] = False

class OrganizationResponse(BaseModel):
    """Organization response model"""
    id: str
    name: str
    business_type: str
    tin: Optional[str] = None
    rc_number: Optional[str] = None
    status: str
    service_packages: list[str]

class UserResponse(BaseModel):
    """User response model"""
    id: str
    email: str
    first_name: str
    last_name: str
    phone: Optional[str] = None
    role: str
    service_package: str
    is_email_verified: bool
    organization: Optional[OrganizationResponse] = None
    permissions: Optional[list[str]] = None

class TokenResponse(BaseModel):
    """Authentication token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse

# Database integration (production-ready)
from .auth_database import get_auth_database

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_access_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT access token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except JWTError as e:
        logger.warning(f"Token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Get user by ID from database"""
    db = get_auth_database()
    return db.get_user_by_id(user_id)

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email from database"""
    db = get_auth_database()
    return db.get_user_by_email(email)

def determine_user_role(service_package: str) -> str:
    """Determine user role based on service package selection"""
    role_mapping = {
        "si": "system_integrator",
        "app": "access_point_provider",
        "hybrid": "hybrid_user"
    }
    return role_mapping.get(service_package, "system_integrator")

def create_auth_router(
    role_detector: HTTPRoleDetector,
    permission_guard: APIPermissionGuard,
    message_router: MessageRouter
) -> APIRouter:
    """Factory function to create authentication router"""
    
    router = APIRouter(prefix="/auth", tags=["Authentication"])
    
    @router.post("/register", response_model=TokenResponse)
    async def register_user(user_data: UserRegisterRequest):
        """Register a new user with organization"""
        try:
            # Validate required agreements
            if not user_data.terms_accepted:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Terms and conditions must be accepted"
                )
            
            if not user_data.privacy_accepted:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Privacy policy must be accepted"
                )
            
            # Check if user already exists
            if get_user_by_email(user_data.email):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email address is already registered"
                )
            
            # Validate service package
            valid_packages = ["si", "app", "hybrid"]
            if user_data.service_package not in valid_packages:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid service package. Must be one of: {', '.join(valid_packages)}"
                )
            
            # Hash password
            hashed_password = hash_password(user_data.password)
            
            # Determine user role
            user_role = determine_user_role(user_data.service_package)
            
            # Get database manager
            db = get_auth_database()
            
            # Create organization record in database
            organization_data = {
                "name": user_data.business_name,
                "business_type": user_data.business_type or "To be determined",  # Default if not provided
                "tin": user_data.tin,
                "rc_number": user_data.rc_number,
                "address": user_data.address,
                "state": user_data.state,
                "lga": user_data.lga,
                "owner_id": None,  # Will be set after user creation
                "service_packages": [user_data.service_package]
            }
            
            organization = db.create_organization(organization_data)
            organization_id = organization["id"]
            
            # Create user record in database
            user_data_dict = {
                "email": user_data.email,
                "hashed_password": hashed_password,
                "first_name": user_data.first_name,
                "last_name": user_data.last_name,
                "phone": user_data.phone,
                "service_package": user_data.service_package,
                "organization_id": organization_id,
                "terms_accepted_at": datetime.utcnow() if user_data.terms_accepted else None,
                "privacy_accepted_at": datetime.utcnow() if user_data.privacy_accepted else None
            }
            
            user = db.create_user(user_data_dict)
            user_id = user["id"]
            
            # Update organization with owner_id
            db.update_organization_owner(organization_id, user_id)
            
            # Create access token
            token_data = {
                "sub": user["email"],
                "user_id": user_id,
                "role": user_role,
                "organization_id": organization_id,
                "service_package": user_data.service_package
            }
            
            # Set token expiration based on remember_me (default to 24 hours)
            expires_delta = timedelta(minutes=JWT_EXPIRATION_MINUTES)
            access_token = create_access_token(data=token_data, expires_delta=expires_delta)
            
            # Prepare response
            organization_response = OrganizationResponse(
                id=organization_id,
                name=organization["name"],
                business_type=organization["business_type"],
                tin=organization["tin"],
                rc_number=organization["rc_number"],
                status=organization["status"],
                service_packages=organization["service_packages"]
            )
            
            user_response = UserResponse(
                id=user_id,
                email=user["email"],
                first_name=user["first_name"],
                last_name=user["last_name"],
                phone=user["phone"],
                role=user_role,
                service_package=user["service_package"],
                is_email_verified=user["is_email_verified"],
                organization=organization_response
            )
            
            logger.info(f"User registered successfully: {user['email']} ({user_role})")
            
            return TokenResponse(
                access_token=access_token,
                expires_in=JWT_EXPIRATION_MINUTES * 60,
                user=user_response
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed due to server error"
            )
    
    @router.post("/login", response_model=TokenResponse)
    async def login_user(credentials: UserLoginRequest):
        """Authenticate user and return access token"""
        try:
            # Find user by email
            user = get_user_by_email(credentials.email)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Verify password
            if not verify_password(credentials.password, user["hashed_password"]):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid email or password"
                )
            
            # Check if user account is active
            if not user.get("is_active", False):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account has been deactivated. Please contact support."
                )
            
            # Get organization from database
            db = get_auth_database()
            organization = db.get_organization_by_id(user.get("organization_id"))
            if not organization:
                logger.error(f"Organization not found for user {user['id']}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="User organization data not found"
                )
            
            # Create access token
            token_data = {
                "sub": user["email"],
                "user_id": user["id"],
                "role": user["role"],
                "organization_id": user["organization_id"],
                "service_package": user["service_package"]
            }
            
            # Set token expiration based on remember_me
            if credentials.remember_me:
                expires_delta = timedelta(days=30)  # 30 days for remember me
            else:
                expires_delta = timedelta(minutes=JWT_EXPIRATION_MINUTES)  # 24 hours default
            
            access_token = create_access_token(data=token_data, expires_delta=expires_delta)
            
            # Update last login info
            user["last_login"] = datetime.utcnow().isoformat()
            user["login_count"] = user.get("login_count", 0) + 1
            
            # Prepare response
            organization_response = OrganizationResponse(
                id=organization["id"],
                name=organization["name"],
                business_type=organization["business_type"],
                tin=organization["tin"],
                rc_number=organization["rc_number"],
                status=organization["status"],
                service_packages=organization["service_packages"]
            )
            
            user_response = UserResponse(
                id=user["id"],
                email=user["email"],
                first_name=user["first_name"],
                last_name=user["last_name"],
                phone=user["phone"],
                role=user["role"],
                service_package=user["service_package"],
                is_email_verified=user["is_email_verified"],
                organization=organization_response
            )
            
            logger.info(f"User login successful: {user['email']}")
            
            return TokenResponse(
                access_token=access_token,
                expires_in=int(expires_delta.total_seconds()),
                user=user_response
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication failed due to server error"
            )
    
    @router.get("/me", response_model=UserResponse)
    async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Get current authenticated user information"""
        try:
            # Verify token
            payload = verify_access_token(credentials.credentials)
            user_id = payload.get("user_id")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: user ID not found"
                )
            
            # Get user from database
            user = get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            # Check if user is still active
            if not user.get("is_active", False):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account has been deactivated"
                )
            
            # Get organization from database
            db = get_auth_database()
            organization = None
            organization_response = None
            
            if user.get("organization_id"):
                organization = db.get_organization_by_id(user["organization_id"])
                if organization:
                    organization_response = OrganizationResponse(
                        id=organization["id"],
                        name=organization["name"],
                        business_type=organization["business_type"],
                        tin=organization["tin"],
                        rc_number=organization["rc_number"],
                        status=organization["status"],
                        service_packages=organization["service_packages"]
                    )
            
            return UserResponse(
                id=user["id"],
                email=user["email"],
                first_name=user["first_name"],
                last_name=user["last_name"],
                phone=user["phone"],
                role=user["role"],
                service_package=user["service_package"],
                is_email_verified=user["is_email_verified"],
                organization=organization_response
            )
            
        except HTTPException:
            raise
        except JWTError as e:
            logger.warning(f"JWT token validation failed: {e}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        except Exception as e:
            logger.error(f"Get current user failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user information"
            )
    
    @router.get("/user-roles")
    async def get_user_roles(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Get current authenticated user's roles and permissions"""
        try:
            # Verify token
            payload = verify_access_token(credentials.credentials)
            user_id = payload.get("user_id")
            
            if not user_id:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token: user ID not found"
                )
            
            # Get user from database
            user = get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="User not found"
                )
            
            # Check if user is still active
            if not user.get("is_active", False):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Account has been deactivated"
                )
            
            # Build role detection result based on user's service package and role
            user_role = user.get("role", determine_user_role(user.get("service_package", "si")))
            
            # Map service package to permissions
            service_permissions = {
                "si": [
                    "business_systems.read",
                    "business_systems.write", 
                    "integration.manage",
                    "organization.manage",
                    "webhook.manage"
                ],
                "app": [
                    "firs.read",
                    "firs.write",
                    "taxpayer.manage",
                    "compliance.read",
                    "einvoice.issue",
                    "einvoice.validate"
                ],
                "hybrid": [
                    "business_systems.read",
                    "business_systems.write",
                    "integration.manage", 
                    "organization.manage",
                    "webhook.manage",
                    "firs.read",
                    "firs.write",
                    "taxpayer.manage",
                    "compliance.read",
                    "einvoice.issue",
                    "einvoice.validate"
                ]
            }
            
            permissions = service_permissions.get(user.get("service_package", "si"), [])
            
            # Create role assignment
            role_assignment = {
                "assignment_id": f"default_{user_id}",
                "user_id": user_id,
                "platform_role": user_role,
                "scope": "tenant",
                "status": "active",
                "permissions": permissions,
                "tenant_id": None,
                "organization_id": user.get("organization_id"),
                "expires_at": None,
                "assigned_at": user.get("created_at", datetime.utcnow().isoformat()),
                "metadata": {
                    "service_package": user.get("service_package", "si"),
                    "primary_role": True
                }
            }
            
            # Determine available roles based on service package
            available_roles = []
            if user.get("service_package") == "hybrid":
                available_roles = ["system_integrator", "access_point_provider", "hybrid"]
            elif user.get("service_package") == "si":
                available_roles = ["system_integrator"]
            elif user.get("service_package") == "app":
                available_roles = ["access_point_provider"]
            else:
                available_roles = [user_role]
            
            # Build role detection result
            role_detection_result = {
                "primary_role": user_role,
                "all_roles": [role_assignment],
                "active_permissions": permissions,
                "can_switch_roles": len(available_roles) > 1,
                "available_roles": available_roles,
                "is_hybrid_user": user.get("service_package") == "hybrid",
                "current_scope": "tenant",
                "organization_id": user.get("organization_id"),
                "tenant_id": None
            }
            
            return JSONResponse(content={
                "role_detection_result": role_detection_result,
                "user_info": {
                    "id": user_id,
                    "email": user.get("email"),
                    "first_name": user.get("first_name"),
                    "last_name": user.get("last_name"),
                    "service_package": user.get("service_package"),
                    "organization_id": user.get("organization_id")
                },
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Get user roles failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user roles"
            )

    @router.post("/logout")
    async def logout_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Logout user and revoke token"""
        try:
            # Import JWT manager for token revocation
            from core_platform.security import get_jwt_manager
            jwt_manager = get_jwt_manager()
            
            # Extract token from authorization header
            token = credentials.credentials
            
            # Revoke the token
            revoked = jwt_manager.revoke_token(token)
            
            if revoked:
                logger.info("User token revoked successfully on logout")
                return JSONResponse(content={
                    "message": "Logged out successfully - token revoked",
                    "timestamp": datetime.utcnow().isoformat()
                })
            else:
                logger.warning("Token revocation failed during logout")
                return JSONResponse(content={
                    "message": "Logged out (token may still be valid)",
                    "timestamp": datetime.utcnow().isoformat()
                })
                
        except Exception as e:
            logger.error(f"Logout error: {e}")
            # Even if revocation fails, we should allow logout
            return JSONResponse(content={
                "message": "Logged out (revocation unavailable)",
                "timestamp": datetime.utcnow().isoformat()
            })
    
    @router.post("/admin/revoke-user-tokens")
    async def revoke_user_tokens(user_id: str, credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Admin endpoint to revoke all tokens for a user (security incident response)"""
        try:
            # Import JWT manager and verify admin permissions
            from core_platform.security import get_jwt_manager
            jwt_manager = get_jwt_manager()
            
            # Verify current user is admin (basic check)
            current_token = credentials.credentials
            payload = jwt_manager.verify_token(current_token)
            current_role = payload.get("role", "")
            
            if current_role not in ["admin", "platform_admin"]:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Admin access required"
                )
            
            # Revoke all tokens for the specified user
            revoked_count = jwt_manager.revoke_user_tokens(user_id)
            
            logger.info(f"Admin revoked {revoked_count} tokens for user {user_id}")
            
            return JSONResponse(content={
                "message": f"Revoked {revoked_count} tokens for user {user_id}",
                "user_id": user_id,
                "tokens_revoked": revoked_count,
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Token revocation error: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke user tokens"
            )

    @router.get("/health")
    async def auth_health_check():
        """Authentication service health check"""
        try:
            # Test database connection
            db = get_auth_database()
            db_status = "connected"
            
            return JSONResponse(content={
                "status": "healthy",
                "service": "authentication",
                "timestamp": datetime.utcnow().isoformat(),
                "database_status": db_status,
                "database_url_type": "PostgreSQL" if "postgresql://" in db.database_url else "SQLite"
            })
        except Exception as e:
            logger.error(f"Auth health check failed: {e}")
            return JSONResponse(
                content={
                    "status": "unhealthy",
                    "service": "authentication", 
                    "error": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                },
                status_code=503
            )
    
    return router