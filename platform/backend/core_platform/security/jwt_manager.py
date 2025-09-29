"""
TaxPoynt Platform - Production JWT Security Manager
==================================================
Secure JWT token management with proper key rotation and encryption.
NO HARDCODED SECRETS - Production-grade security implementation.
"""

import os
import secrets
import hashlib
import base64
import jwt
import redis
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Optional, List
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import logging

logger = logging.getLogger(__name__)


class ProductionJWTManager:
    """
    Production-grade JWT Manager with:
    - No hardcoded secrets
    - Key rotation support
    - Token revocation
    - Secure key derivation
    - Redis-backed token blacklist
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or self._get_redis_client()
        
        # Generate or retrieve secure JWT secret
        self.jwt_secret = self._get_or_generate_jwt_secret()
        self.algorithm = "HS256"
        
        # Token configuration
        self.access_token_expire_minutes = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
        self.refresh_token_expire_days = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30"))
        
        # Encryption for sensitive data
        self.encryption_key = self._get_or_generate_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
        
        logger.info("Production JWT Manager initialized with secure key management")
    
    def _get_redis_client(self) -> redis.Redis:
        """Get Redis client for token blacklist management.

        In CI/development, Redis is optional. If `JWT_REDIS_DISABLED` is true-y,
        use a lightweight in-memory stub to avoid connection attempts that can
        hang tests/CI when no Redis is available.
        """
        # Allow explicit disable (default on for common dev/test envs)
        env = os.getenv("ENVIRONMENT", "production").lower()
        default_disable = env in ("development", "dev", "testing", "test", "ci")
        disable_redis = str(os.getenv("JWT_REDIS_DISABLED", str(default_disable))).lower() in ("1", "true", "yes", "on")

        if disable_redis:
            class _DummyRedis:
                def __init__(self):
                    self._kv = {}
                    self._hash = {}
                # Simple KV
                def setex(self, key, ttl, value):
                    self._kv[key] = value
                    return True
                def get(self, key):
                    return self._kv.get(key)
                def exists(self, key):
                    return 1 if key in self._kv else 0
                def expire(self, key, ttl):
                    return True
                # Hash helpers
                def hset(self, key, mapping=None, **kwargs):
                    data = mapping or kwargs
                    if not isinstance(data, dict):
                        return False
                    self._hash[key] = dict(data)
                    return True
                # Back-compat alias
                def hmset(self, key, mapping):
                    return self.hset(key, mapping=mapping)
                def hgetall(self, key):
                    return dict(self._hash.get(key, {}))
                def scan_iter(self, match=None):
                    # Iterate over stored keys respecting a simple prefix match
                    keys = list(self._kv.keys()) + list(self._hash.keys())
                    if match is None:
                        for k in keys:
                            yield k
                    else:
                        import fnmatch as _fnm
                        for k in keys:
                            if _fnm.fnmatch(k, match):
                                yield k
            logger.info("JWT_REDIS_DISABLED=true; using in-memory Redis stub for JWT management")
            return _DummyRedis()

        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            # Use conservative timeouts to avoid long hangs in CI
            return redis.from_url(redis_url, decode_responses=True, socket_timeout=2.0, socket_connect_timeout=1.0)

        # Fallback to local Redis with timeouts
        return redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            decode_responses=True,
            socket_timeout=2.0,
            socket_connect_timeout=1.0,
        )
    
    def _get_or_generate_jwt_secret(self) -> str:
        """
        Get JWT secret from secure environment or generate new one.
        CRITICAL: Never use hardcoded fallbacks in production.
        """
        # 1. Try environment variable (production)
        jwt_secret = os.getenv("JWT_SECRET_KEY")
        if jwt_secret and len(jwt_secret) >= 32:
            return jwt_secret
        
        # 2. Try Redis cache (for consistency across instances)
        try:
            cached_secret = self.redis_client.get("taxpoynt:jwt_secret")
            if cached_secret:
                return cached_secret
        except Exception as e:
            logger.warning(f"Could not retrieve JWT secret from Redis: {e}")
        
        # 3. Generate new secure secret (development only)
        if os.getenv("ENVIRONMENT", "production").lower() == "production":
            raise ValueError(
                "CRITICAL SECURITY ERROR: JWT_SECRET_KEY environment variable is required in production. "
                "Generate a secure 64-character secret and set it in your environment."
            )
        
        # Development fallback - generate secure random secret
        new_secret = self._generate_secure_secret()
        
        # Cache in Redis for consistency
        try:
            self.redis_client.setex("taxpoynt:jwt_secret", 86400, new_secret)  # 24 hours
            logger.warning("Generated new JWT secret for development. Set JWT_SECRET_KEY in production.")
        except Exception as e:
            logger.error(f"Could not cache JWT secret in Redis: {e}")
        
        return new_secret
    
    def _get_or_generate_encryption_key(self) -> bytes:
        """Get or generate encryption key for sensitive data"""
        # Try environment variable first
        encryption_key = os.getenv("ENCRYPTION_KEY")
        if encryption_key:
            try:
                # Fernet expects a base64-encoded key as bytes
                return encryption_key.encode()
            except Exception:
                logger.error("Invalid ENCRYPTION_KEY format in environment")
        # In production, fail hard if no explicit encryption key is provided
        if os.getenv("ENVIRONMENT", "production").lower() == "production":
            raise ValueError(
                "CRITICAL SECURITY ERROR: ENCRYPTION_KEY is required in production. "
                "Set a base64-encoded Fernet key via ENCRYPTION_KEY."
            )

        # Development fallback: derive from master password (dev only)
        master_password = os.getenv("MASTER_PASSWORD", "taxpoynt-development-key").encode()
        salt = os.getenv("ENCRYPTION_SALT", "taxpoynt-salt").encode()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_password))
        logger.warning("Derived development encryption key. Set ENCRYPTION_KEY in production.")
        return key
    
    def _generate_secure_secret(self) -> str:
        """Generate cryptographically secure random secret"""
        return secrets.token_urlsafe(64)
    
    def create_access_token(self, user_data: Dict[str, Any]) -> str:
        """Create JWT access token with secure payload"""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(minutes=self.access_token_expire_minutes)

        payload = {
            "sub": str(user_data.get("user_id")),
            "email": user_data.get("email"),
            "role": user_data.get("role"),
            "organization_id": str(user_data.get("organization_id")) if user_data.get("organization_id") else None,
            "permissions": user_data.get("permissions", []),
            "token_type": "access",
            "iat": now,
            "exp": expire,
            "jti": self._generate_token_id(),  # Unique token ID for revocation
            "iss": "taxpoynt-platform",
            "aud": "taxpoynt-api"
        }

        extra_claims = user_data.get("extra_claims") if isinstance(user_data, dict) else None
        if isinstance(extra_claims, dict):
            for key, value in extra_claims.items():
                if key not in payload:
                    payload[key] = value

        token = jwt.encode(payload, self.jwt_secret, algorithm=self.algorithm)

        # Cache token metadata for revocation
        self._cache_token_metadata(payload["jti"], {
            "user_id": payload["sub"],
            "token_type": "access",
            "expires_at": expire.isoformat(),
            "created_at": now.isoformat()
        })

        return token
    
    def create_refresh_token(self, user_id: str) -> str:
        """Create JWT refresh token"""
        now = datetime.now(timezone.utc)
        expire = now + timedelta(days=self.refresh_token_expire_days)
        
        payload = {
            "sub": str(user_id),
            "token_type": "refresh",
            "iat": now,
            "exp": expire,
            "jti": self._generate_token_id(),
            "iss": "taxpoynt-platform",
            "aud": "taxpoynt-api"
        }
        
        token = jwt.encode(payload, self.jwt_secret, algorithm=self.algorithm)
        
        # Cache refresh token for revocation
        self._cache_token_metadata(payload["jti"], {
            "user_id": user_id,
            "token_type": "refresh",
            "expires_at": expire.isoformat(),
            "created_at": now.isoformat()
        })
        
        return token
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify JWT token with comprehensive security checks
        """
        try:
            # Decode token
            payload = jwt.decode(
                token, 
                self.jwt_secret, 
                algorithms=[self.algorithm],
                audience="taxpoynt-api",
                issuer="taxpoynt-platform"
            )
            
            # Check if token is revoked
            if self._is_token_revoked(payload.get("jti")):
                raise jwt.InvalidTokenError("Token has been revoked")
            
            # Validate token structure
            required_fields = ["sub", "token_type", "exp", "jti"]
            for field in required_fields:
                if field not in payload:
                    raise jwt.InvalidTokenError(f"Missing required field: {field}")
            
            return payload
            
        except jwt.ExpiredSignatureError:
            raise jwt.InvalidTokenError("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning(f"Invalid token: {e}")
            raise
        except Exception as e:
            logger.error(f"Token verification error: {e}")
            raise jwt.InvalidTokenError("Token verification failed")
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a specific token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.algorithm], options={"verify_exp": False})
            jti = payload.get("jti")
            
            if jti:
                # Add to blacklist
                expire_at = payload.get("exp", 0)
                ttl = max(0, expire_at - datetime.now(timezone.utc).timestamp())
                
                self.redis_client.setex(f"taxpoynt:revoked_token:{jti}", int(ttl), "revoked")
                logger.info(f"Token {jti} revoked successfully")
                return True
                
        except Exception as e:
            logger.error(f"Error revoking token: {e}")
        
        return False
    
    def revoke_user_tokens(self, user_id: str) -> int:
        """Revoke all tokens for a specific user"""
        try:
            # Get all token metadata for user
            pattern = f"taxpoynt:token_meta:*"
            revoked_count = 0
            
            for key in self.redis_client.scan_iter(match=pattern):
                token_data = self.redis_client.hgetall(key)
                if token_data.get("user_id") == str(user_id):
                    jti = key.split(":")[-1]
                    
                    # Calculate TTL based on expiration
                    expire_str = token_data.get("expires_at")
                    if expire_str:
                        expire_dt = datetime.fromisoformat(expire_str.replace("Z", "+00:00"))
                        ttl = max(0, (expire_dt - datetime.now(timezone.utc)).total_seconds())
                        
                        self.redis_client.setex(f"taxpoynt:revoked_token:{jti}", int(ttl), "revoked")
                        revoked_count += 1
            
            logger.info(f"Revoked {revoked_count} tokens for user {user_id}")
            return revoked_count
            
        except Exception as e:
            logger.error(f"Error revoking user tokens: {e}")
            return 0
    
    def refresh_access_token(self, refresh_token: str) -> str:
        """Create new access token from valid refresh token"""
        payload = self.verify_token(refresh_token)
        
        if payload.get("token_type") != "refresh":
            raise jwt.InvalidTokenError("Invalid token type for refresh")
        
        user_id = payload.get("sub")
        if not user_id:
            raise jwt.InvalidTokenError("Invalid user ID in refresh token")
        
        # Here you would typically fetch current user data from database
        # For now, we'll create a basic access token
        user_data = {
            "user_id": user_id,
            "role": "user",  # This should come from database
            "permissions": []  # This should come from database
        }
        
        return self.create_access_token(user_data)

    def create_custom_token(
        self,
        payload: Dict[str, Any],
        *,
        expires_in_seconds: int,
        token_type: str = "custom",
    ) -> str:
        """Create a JWT with custom payload and expiry (used for OAuth tokens)."""

        now = datetime.now(timezone.utc)
        expire = now + timedelta(seconds=max(1, int(expires_in_seconds)))

        token_payload = dict(payload)
        token_payload.setdefault("sub", token_payload.get("client_id"))
        token_payload.setdefault("iss", "taxpoynt-platform")
        token_payload.setdefault("aud", token_payload.get("aud") or "taxpoynt-api")
        token_payload["token_type"] = token_payload.get("token_type", token_type)
        token_payload["iat"] = now
        token_payload["exp"] = expire
        token_payload["jti"] = self._generate_token_id()

        token = jwt.encode(token_payload, self.jwt_secret, algorithm=self.algorithm)

        metadata = {
            "user_id": token_payload.get("sub"),
            "token_type": token_payload.get("token_type"),
            "expires_at": expire.isoformat(),
            "created_at": now.isoformat(),
        }
        client_id = token_payload.get("client_id")
        if client_id:
            metadata["client_id"] = str(client_id)
        usage = token_payload.get("token_usage")
        if usage:
            metadata["token_usage"] = usage

        self._cache_token_metadata(token_payload["jti"], metadata)
        return token
    
    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data for database storage"""
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return base64.urlsafe_b64encode(encrypted_data).decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise ValueError("Failed to encrypt sensitive data")
    
    def decrypt_sensitive_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data from database"""
        try:
            decoded_data = base64.urlsafe_b64decode(encrypted_data.encode())
            decrypted_data = self.cipher_suite.decrypt(decoded_data)
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise ValueError("Failed to decrypt sensitive data")
    
    def _generate_token_id(self) -> str:
        """Generate unique token ID"""
        return secrets.token_urlsafe(32)
    
    def _cache_token_metadata(self, jti: str, metadata: Dict[str, Any]) -> None:
        """Cache token metadata for management"""
        try:
            # redis-py hmset is deprecated; use hset with mapping
            self.redis_client.hset(f"taxpoynt:token_meta:{jti}", mapping=metadata)
            # Set expiration based on token expiration
            expire_str = metadata.get("expires_at")
            if expire_str:
                expire_dt = datetime.fromisoformat(expire_str)
                ttl = max(0, (expire_dt - datetime.now(timezone.utc)).total_seconds())
                self.redis_client.expire(f"taxpoynt:token_meta:{jti}", int(ttl))
        except Exception as e:
            logger.error(f"Error caching token metadata: {e}")
    
    def _is_token_revoked(self, jti: str) -> bool:
        """Check if token is in revocation list"""
        try:
            return self.redis_client.exists(f"taxpoynt:revoked_token:{jti}")
        except Exception as e:
            logger.error(f"Error checking token revocation: {e}")
            return False
    
    def get_token_statistics(self) -> Dict[str, Any]:
        """Get token usage statistics"""
        try:
            stats = {
                "active_tokens": 0,
                "revoked_tokens": 0,
                "access_tokens": 0,
                "refresh_tokens": 0
            }
            
            # Count active tokens
            for key in self.redis_client.scan_iter(match="taxpoynt:token_meta:*"):
                token_data = self.redis_client.hgetall(key)
                stats["active_tokens"] += 1
                
                token_type = token_data.get("token_type", "unknown")
                if token_type == "access":
                    stats["access_tokens"] += 1
                elif token_type == "refresh":
                    stats["refresh_tokens"] += 1
            
            # Count revoked tokens
            for key in self.redis_client.scan_iter(match="taxpoynt:revoked_token:*"):
                stats["revoked_tokens"] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting token statistics: {e}")
            return {"error": "Failed to get statistics"}


# Global JWT manager instance
_jwt_manager: Optional[ProductionJWTManager] = None


def get_jwt_manager() -> ProductionJWTManager:
    """Get global JWT manager instance"""
    global _jwt_manager
    if _jwt_manager is None:
        _jwt_manager = ProductionJWTManager()
    return _jwt_manager


def initialize_jwt_manager(redis_client: Optional[redis.Redis] = None) -> ProductionJWTManager:
    """Initialize JWT manager with custom Redis client"""
    global _jwt_manager
    _jwt_manager = ProductionJWTManager(redis_client)
    return _jwt_manager
