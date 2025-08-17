"""
Production Authentication Endpoints with PostgreSQL
==================================================
Production-ready authentication endpoints using Railway PostgreSQL database.
"""
import os
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt
from sqlalchemy.orm import Session

# Import existing database infrastructure
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from core_platform.data_management.database_abstraction import DatabaseAbstractionLayer
    from core_platform.data_management.models.user import User, UserRole
    from core_platform.data_management.models.organization import Organization
    from core_platform.data_management.models.base import BaseModel
except ImportError as e:
    logging.warning(f"Could not import database models: {e}")
    # Fallback to basic implementation
    DatabaseAbstractionLayer = None

logger = logging.getLogger(__name__)

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL") or os.getenv("PGDATABASE") 
if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Initialize database
db_layer = None
if DatabaseAbstractionLayer and DATABASE_URL:
    try:
        db_layer = DatabaseAbstractionLayer(DATABASE_URL)
        logger.info("PostgreSQL database connection established")
    except Exception as e:
        logger.error(f"Failed to connect to PostgreSQL: {e}")
        db_layer = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "taxpoynt-platform-secret-key")
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Pydantic models
class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    role: str = "system_integrator"

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: Dict[str, Any]

# Database functions
def get_db_session() -> Optional[Session]:
    """Get database session"""
    if not db_layer:
        return None
    try:
        return db_layer.get_session()
    except Exception as e:
        logger.error(f"Failed to get database session: {e}")
        return None

def get_database():
    """Database dependency for FastAPI"""
    if not db_layer:
        return None
    try:
        session = db_layer.get_session()
        try:
            yield session
        finally:
            session.close()
    except Exception as e:
        logger.error(f"Database dependency error: {e}")
        yield None

def init_database():
    """Initialize PostgreSQL database with existing models"""
    try:
        if db_layer and BaseModel:
            # Create tables using existing SQLAlchemy models
            BaseModel.metadata.create_all(bind=db_layer.engine)
            logger.info("PostgreSQL database tables initialized successfully")
        else:
            logger.warning("Database layer not available - using fallback mode")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        # Don't raise - allow fallback mode
        pass

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=JWT_EXPIRATION_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Get user by email from PostgreSQL"""
    if not db_layer or not User:
        return None
        
    try:
        with db_layer.get_session() as session:
            user = session.query(User).filter(User.email == email).first()
            if user:
                return {
                    "id": str(user.id),
                    "email": user.email,
                    "hashed_password": user.password_hash,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "role": user.role.value if hasattr(user.role, 'value') else str(user.role),
                    "created_at": user.created_at.isoformat() if user.created_at else None,
                    "is_active": user.is_active
                }
            return None
    except Exception as e:
        logger.error(f"Error getting user by email: {e}")
        return None

def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    """Create user in PostgreSQL"""
    if not db_layer or not User:
        # Fallback to mock user for development
        user_id = str(uuid.uuid4())
        return {
            "id": user_id,
            "email": user_data["email"],
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
            "role": user_data["role"],
            "created_at": datetime.utcnow().isoformat(),
            "is_active": True
        }
        
    try:
        # Map role string to enum
        role_enum = UserRole.SI_USER  # Default
        if user_data["role"] == "system_integrator":
            role_enum = UserRole.SI_USER
        elif user_data["role"] == "access_point_provider":
            role_enum = UserRole.APP_USER
        elif user_data["role"] == "hybrid_user":
            role_enum = UserRole.HYBRID_USER
        
        with db_layer.get_session() as session:
            # Create new user
            new_user = User(
                id=uuid.uuid4(),
                email=user_data["email"],
                password_hash=user_data["hashed_password"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                role=role_enum,
                is_active=True
            )
            
            session.add(new_user)
            session.commit()
            session.refresh(new_user)
            
            return {
                "id": str(new_user.id),
                "email": new_user.email,
                "first_name": new_user.first_name,
                "last_name": new_user.last_name,
                "role": new_user.role.value if hasattr(new_user.role, 'value') else str(new_user.role),
                "created_at": new_user.created_at.isoformat() if new_user.created_at else None,
                "is_active": new_user.is_active
            }
            
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )

# Initialize database on module load
init_database()

# Create router
router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
async def register_user(user_data: UserRegisterRequest):
    """Register a new user"""
    try:
        # Check if user already exists
        if get_user_by_email(user_data.email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email address is already registered"
            )
        
        # Hash password
        hashed_password = hash_password(user_data.password)
        
        # Create user
        user = create_user({
            "email": user_data.email,
            "hashed_password": hashed_password,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "role": user_data.role
        })
        
        # Create access token
        token_data = {
            "sub": user["email"],
            "user_id": user["id"],
            "role": user["role"]
        }
        access_token = create_access_token(data=token_data)
        
        logger.info(f"User registered successfully: {user['email']}")
        
        return TokenResponse(
            access_token=access_token,
            user={
                "id": user["id"],
                "email": user["email"],
                "first_name": user["first_name"],
                "last_name": user["last_name"],
                "role": user["role"]
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed due to server error"
        )

@router.get("/health")
async def auth_health():
    """Authentication health check"""
    return JSONResponse(content={
        "status": "healthy",
        "service": "authentication",
        "timestamp": datetime.utcnow().isoformat()
    })