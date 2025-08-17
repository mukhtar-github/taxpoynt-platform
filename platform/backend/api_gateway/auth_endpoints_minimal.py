"""
Minimal Authentication Endpoints for Production
==============================================
Simple, production-ready authentication endpoints that don't rely on complex imports.
"""
import os
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
from jose import JWTError, jwt
import sqlite3
from pathlib import Path

logger = logging.getLogger(__name__)

# Database setup
DB_PATH = Path(__file__).parent.parent / "taxpoynt_auth.db"
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
def init_database():
    """Initialize SQLite database with basic tables"""
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    hashed_password TEXT NOT NULL,
                    first_name TEXT NOT NULL,
                    last_name TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT 1
                )
            """)
            conn.commit()
            logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

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
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            return dict(row) if row else None
    except Exception as e:
        logger.error(f"Error getting user by email: {e}")
        return None

def create_user(user_data: Dict[str, Any]) -> Dict[str, Any]:
    try:
        user_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()
        
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                INSERT INTO users (id, email, hashed_password, first_name, last_name, role, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user_id,
                user_data["email"],
                user_data["hashed_password"],
                user_data["first_name"],
                user_data["last_name"],
                user_data["role"],
                created_at
            ))
            conn.commit()
        
        return {
            "id": user_id,
            "email": user_data["email"],
            "first_name": user_data["first_name"],
            "last_name": user_data["last_name"],
            "role": user_data["role"],
            "created_at": created_at,
            "is_active": True
        }
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise

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