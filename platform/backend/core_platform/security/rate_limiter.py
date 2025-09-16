"""
TaxPoynt Platform - Production Rate Limiter
===========================================
Comprehensive rate limiting for high-volume financial platform.
Protects against DDoS attacks, API abuse, and ensures fair usage.
"""

import time
import redis
import logging
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import hashlib
import json
import asyncio

logger = logging.getLogger(__name__)


class RateLimitType(str, Enum):
    """Rate limiting strategies"""
    PER_IP = "per_ip"
    PER_USER = "per_user"
    PER_API_KEY = "per_api_key"
    PER_ENDPOINT = "per_endpoint"
    GLOBAL = "global"


class RateLimitWindow(str, Enum):
    """Rate limiting time windows"""
    SECOND = "second"
    MINUTE = "minute"
    HOUR = "hour"
    DAY = "day"


@dataclass
class RateLimitRule:
    """Rate limiting rule configuration"""
    name: str
    limit_type: RateLimitType
    max_requests: int
    window: RateLimitWindow
    window_seconds: int
    endpoint_pattern: str = "*"
    priority: int = 0
    user_roles: list = None
    ip_whitelist: list = None
    burst_allowance: int = 0  # Additional requests allowed in burst
    
    def __post_init__(self):
        if self.user_roles is None:
            self.user_roles = []
        if self.ip_whitelist is None:
            self.ip_whitelist = []


class ProductionRateLimiter:
    """
    Production-grade rate limiter with:
    - Multiple limiting strategies (IP, user, API key, endpoint)
    - Redis-backed distributed rate limiting
    - Burst protection
    - Role-based limits
    - IP whitelisting
    - Sliding window algorithm
    - Real-time metrics and monitoring
    """
    
    def __init__(self, redis_client: Optional[redis.Redis] = None):
        self.redis_client = redis_client or self._get_redis_client()
        self.rules: Dict[str, RateLimitRule] = {}
        self.metrics = {
            "total_requests": 0,
            "blocked_requests": 0,
            "rate_limited_ips": set(),
            "rate_limited_users": set()
        }
        
        # Setup default production rules
        self._setup_production_rules()
        
        logger.info("Production Rate Limiter initialized")
    
    def _get_redis_client(self) -> redis.Redis:
        """Get Redis client for distributed rate limiting"""
        import os
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            return redis.from_url(redis_url, decode_responses=True)
        
        return redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "1")),  # Use different DB for rate limiting
            decode_responses=True
        )
    
    def _setup_production_rules(self):
        """Setup production-grade rate limiting rules"""
        
        # Authentication endpoints - strict limits
        self.add_rule(RateLimitRule(
            name="auth_login_per_ip",
            limit_type=RateLimitType.PER_IP,
            max_requests=5,
            window=RateLimitWindow.MINUTE,
            window_seconds=60,
            endpoint_pattern="/api/v1/auth/login",
            priority=100
        ))
        
        self.add_rule(RateLimitRule(
            name="auth_register_per_ip",
            limit_type=RateLimitType.PER_IP,
            max_requests=3,
            window=RateLimitWindow.MINUTE,
            window_seconds=60,
            endpoint_pattern="/api/v1/auth/register",
            priority=100
        ))
        
        # FIRS submission endpoints - business critical
        self.add_rule(RateLimitRule(
            name="firs_submission_per_user",
            limit_type=RateLimitType.PER_USER,
            max_requests=100,
            window=RateLimitWindow.MINUTE,
            window_seconds=60,
            endpoint_pattern="/api/v1/app/firs/submit*",
            priority=90,
            burst_allowance=20
        ))
        
        # Banking integration endpoints
        self.add_rule(RateLimitRule(
            name="banking_per_user",
            limit_type=RateLimitType.PER_USER,
            max_requests=200,
            window=RateLimitWindow.MINUTE,
            window_seconds=60,
            endpoint_pattern="/api/v1/si/banking*",
            priority=80
        ))
        
        # General API endpoints per user
        self.add_rule(RateLimitRule(
            name="api_per_user_general",
            limit_type=RateLimitType.PER_USER,
            max_requests=1000,
            window=RateLimitWindow.MINUTE,
            window_seconds=60,
            endpoint_pattern="/api/v1/*",
            priority=50
        ))
        
        # General API endpoints per IP
        self.add_rule(RateLimitRule(
            name="api_per_ip_general",
            limit_type=RateLimitType.PER_IP,
            max_requests=500,
            window=RateLimitWindow.MINUTE,
            window_seconds=60,
            endpoint_pattern="/api/v1/*",
            priority=40
        ))
        
        # Global rate limit (DDoS protection)
        self.add_rule(RateLimitRule(
            name="global_ddos_protection",
            limit_type=RateLimitType.GLOBAL,
            max_requests=10000,
            window=RateLimitWindow.MINUTE,
            window_seconds=60,
            endpoint_pattern="*",
            priority=10
        ))
        
        # Webhook endpoints - high volume expected
        self.add_rule(RateLimitRule(
            name="webhooks_per_ip",
            limit_type=RateLimitType.PER_IP,
            max_requests=1000,
            window=RateLimitWindow.MINUTE,
            window_seconds=60,
            endpoint_pattern="/api/v1/webhooks/*",
            priority=70
        ))
    
    def add_rule(self, rule: RateLimitRule):
        """Add rate limiting rule"""
        self.rules[rule.name] = rule
        logger.info(f"Added rate limit rule: {rule.name}")
    
    def remove_rule(self, rule_name: str):
        """Remove rate limiting rule"""
        if rule_name in self.rules:
            del self.rules[rule_name]
            logger.info(f"Removed rate limit rule: {rule_name}")
    
    async def check_rate_limit(self, request: Request) -> Tuple[bool, Dict[str, Any]]:
        """
        Check if request should be rate limited
        Returns: (is_allowed, rate_limit_info)
        """
        try:
            self.metrics["total_requests"] += 1
            
            # Extract request information
            client_ip = self._get_client_ip(request)
            user_id = self._get_user_id(request)
            api_key = self._get_api_key(request)
            endpoint = str(request.url.path)
            
            # Check IP whitelist
            if self._is_ip_whitelisted(client_ip):
                return True, {"status": "whitelisted", "ip": client_ip}
            
            # Find applicable rules
            applicable_rules = self._find_applicable_rules(endpoint, user_id)
            
            rate_limit_info = {
                "ip": client_ip,
                "user_id": user_id,
                "endpoint": endpoint,
                "rules_checked": len(applicable_rules),
                "limits": {}
            }
            
            # Check each applicable rule
            for rule in applicable_rules:
                is_allowed, rule_info = await self._check_rule(
                    rule, client_ip, user_id, api_key, endpoint
                )
                
                rate_limit_info["limits"][rule.name] = rule_info
                
                if not is_allowed:
                    self.metrics["blocked_requests"] += 1
                    
                    # Track rate limited entities
                    if rule.limit_type == RateLimitType.PER_IP:
                        self.metrics["rate_limited_ips"].add(client_ip)
                    elif rule.limit_type == RateLimitType.PER_USER and user_id:
                        self.metrics["rate_limited_users"].add(user_id)
                    
                    rate_limit_info["status"] = "rate_limited"
                    rate_limit_info["rule_violated"] = rule.name
                    rate_limit_info["retry_after"] = rule_info.get("retry_after", 60)
                    
                    logger.warning(f"Rate limit exceeded: {rule.name} for {client_ip} ({user_id})")
                    return False, rate_limit_info
            
            rate_limit_info["status"] = "allowed"
            return True, rate_limit_info
            
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            # Fail open - allow request if rate limiting fails
            return True, {"status": "error", "error": str(e)}
    
    async def _check_rule(
        self, 
        rule: RateLimitRule, 
        client_ip: str, 
        user_id: Optional[str], 
        api_key: Optional[str], 
        endpoint: str
    ) -> Tuple[bool, Dict[str, Any]]:
        """Check specific rate limiting rule"""
        try:
            # Generate rate limit key based on rule type
            if rule.limit_type == RateLimitType.PER_IP:
                key_identifier = client_ip
            elif rule.limit_type == RateLimitType.PER_USER:
                key_identifier = user_id or client_ip  # Fallback to IP if no user
            elif rule.limit_type == RateLimitType.PER_API_KEY:
                key_identifier = api_key or client_ip  # Fallback to IP if no API key
            elif rule.limit_type == RateLimitType.PER_ENDPOINT:
                key_identifier = f"{endpoint}:{client_ip}"
            elif rule.limit_type == RateLimitType.GLOBAL:
                key_identifier = "global"
            else:
                key_identifier = client_ip
            
            # Create Redis key
            redis_key = f"taxpoynt:rate_limit:{rule.name}:{key_identifier}"
            
            # Use sliding window algorithm
            current_time = int(time.time())
            window_start = current_time - rule.window_seconds
            
            # Get current request count in window
            pipe = self.redis_client.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(redis_key, 0, window_start)
            
            # Count current requests
            pipe.zcard(redis_key)
            
            # Add current request
            pipe.zadd(redis_key, {str(current_time): current_time})
            
            # Set expiration
            pipe.expire(redis_key, rule.window_seconds + 60)
            
            results = pipe.execute()
            current_count = results[1]  # Count after removing old entries
            
            # Calculate limits
            max_allowed = rule.max_requests + rule.burst_allowance
            remaining = max(0, max_allowed - current_count - 1)  # -1 for current request
            retry_after = rule.window_seconds
            
            rule_info = {
                "rule_name": rule.name,
                "limit": rule.max_requests,
                "burst_allowance": rule.burst_allowance,
                "current_count": current_count + 1,  # +1 for current request
                "remaining": remaining,
                "window_seconds": rule.window_seconds,
                "retry_after": retry_after
            }
            
            # Check if limit exceeded
            if current_count >= max_allowed:
                return False, rule_info
            
            return True, rule_info
            
        except Exception as e:
            logger.error(f"Error checking rule {rule.name}: {e}")
            # Fail open for individual rule errors
            return True, {"error": str(e)}
    
    def _find_applicable_rules(self, endpoint: str, user_id: Optional[str]) -> list:
        """Find rate limiting rules applicable to the request"""
        applicable_rules = []
        
        for rule in self.rules.values():
            # Check endpoint pattern
            if self._pattern_matches(rule.endpoint_pattern, endpoint):
                # Check user role restrictions if any
                if rule.user_roles:
                    # This would require user role lookup - simplified for now
                    # In production, you'd fetch user roles from database
                    pass
                
                applicable_rules.append(rule)
        
        # Sort by priority (highest first)
        applicable_rules.sort(key=lambda r: r.priority, reverse=True)
        return applicable_rules
    
    def _pattern_matches(self, pattern: str, text: str) -> bool:
        """Check if pattern matches text (supports wildcards)"""
        if pattern == "*":
            return True
        if pattern == text:
            return True
        
        # Simple wildcard matching
        if "*" in pattern:
            import fnmatch
            return fnmatch.fnmatch(text, pattern)
        
        return False
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request"""
        # Check for forwarded headers first (load balancer/proxy)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Take the first IP in the chain
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip.strip()
        
        # Fallback to direct connection IP
        return request.client.host if request.client else "unknown"
    
    def _get_user_id(self, request: Request) -> Optional[str]:
        """Extract user ID from request (JWT token, session, etc.)"""
        try:
            # Try to get from JWT token
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                # This would decode JWT and extract user ID
                # Using JWT manager would be ideal here
                from core_platform.security import get_jwt_manager
                jwt_manager = get_jwt_manager()
                payload = jwt_manager.verify_token(token)
                return payload.get("sub")
        except Exception:
            pass
        
        # Try to get from session or other auth mechanisms
        # Implementation depends on your auth system
        return None
    
    def _get_api_key(self, request: Request) -> Optional[str]:
        """Extract API key from request"""
        # Check X-API-Key header
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return api_key
        
        # Check query parameter
        return request.query_params.get("api_key")
    
    def _is_ip_whitelisted(self, ip: str) -> bool:
        """Check if IP is whitelisted"""
        # Internal/admin IPs that should never be rate limited
        whitelist = [
            "127.0.0.1",
            "::1",
            "10.0.0.0/8",    # Private networks
            "172.16.0.0/12",
            "192.168.0.0/16"
        ]
        
        # Add environment-specific whitelists
        import os
        env_whitelist = os.getenv("RATE_LIMIT_IP_WHITELIST", "").split(",")
        whitelist.extend([ip.strip() for ip in env_whitelist if ip.strip()])
        
        # Simple IP matching (would use ipaddress module for CIDR in production)
        return ip in whitelist
    
    async def get_rate_limit_status(self, identifier: str, rule_name: str) -> Dict[str, Any]:
        """Get current rate limit status for identifier"""
        try:
            if rule_name not in self.rules:
                return {"error": "Rule not found"}
            
            rule = self.rules[rule_name]
            redis_key = f"taxpoynt:rate_limit:{rule_name}:{identifier}"
            
            current_time = int(time.time())
            window_start = current_time - rule.window_seconds
            
            # Get current count
            self.redis_client.zremrangebyscore(redis_key, 0, window_start)
            current_count = self.redis_client.zcard(redis_key)
            
            max_allowed = rule.max_requests + rule.burst_allowance
            remaining = max(0, max_allowed - current_count)
            
            return {
                "rule_name": rule_name,
                "identifier": identifier,
                "current_count": current_count,
                "limit": rule.max_requests,
                "burst_allowance": rule.burst_allowance,
                "remaining": remaining,
                "window_seconds": rule.window_seconds,
                "reset_time": current_time + rule.window_seconds
            }
            
        except Exception as e:
            logger.error(f"Error getting rate limit status: {e}")
            return {"error": str(e)}
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get rate limiting metrics"""
        return {
            "total_requests": self.metrics["total_requests"],
            "blocked_requests": self.metrics["blocked_requests"],
            "block_rate": (
                self.metrics["blocked_requests"] / max(1, self.metrics["total_requests"])
            ) * 100,
            "rate_limited_ips": len(self.metrics["rate_limited_ips"]),
            "rate_limited_users": len(self.metrics["rate_limited_users"]),
            "active_rules": len(self.rules),
            "rule_names": list(self.rules.keys())
        }
    
    async def reset_rate_limit(self, identifier: str, rule_name: str) -> bool:
        """Reset rate limit for specific identifier and rule"""
        try:
            redis_key = f"taxpoynt:rate_limit:{rule_name}:{identifier}"
            self.redis_client.delete(redis_key)
            logger.info(f"Reset rate limit for {identifier} on rule {rule_name}")
            return True
        except Exception as e:
            logger.error(f"Error resetting rate limit: {e}")
            return False


# Global rate limiter instance
_rate_limiter: Optional[ProductionRateLimiter] = None


def get_rate_limiter() -> ProductionRateLimiter:
    """Get global rate limiter instance"""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = ProductionRateLimiter()
    return _rate_limiter


def initialize_rate_limiter(redis_client: Optional[redis.Redis] = None) -> ProductionRateLimiter:
    """Initialize rate limiter with custom Redis client"""
    global _rate_limiter
    _rate_limiter = ProductionRateLimiter(redis_client)
    return _rate_limiter


async def rate_limit_middleware(request: Request, call_next):
    """FastAPI middleware for rate limiting"""
    rate_limiter = get_rate_limiter()
    # Align dynamic limits with APIVersionCoordinator per-role config when available
    try:
        app = request.app
        gateway = getattr(app.state, 'gateway_controller', None)
        if gateway and hasattr(gateway, 'version_coordinator'):
            vc = gateway.version_coordinator
            # Detect API version from request path/headers
            version = vc.detect_version_from_request(request)
            routing = vc.get_routing_config(version)
            # Derive role from routing_context if available
            role_key = None
            ctx = getattr(request.state, 'routing_context', None)
            if ctx and getattr(ctx, 'primary_role', None):
                role_val = str(getattr(ctx, 'primary_role')).lower()
                if 'system_integrator' in role_val or 'si' in role_val:
                    role_key = 'system_integrator'
                elif 'access_point_provider' in role_val or 'app' in role_val:
                    role_key = 'access_point_provider'
                elif 'admin' in role_val:
                    role_key = 'administrator'
            # Fallback: infer from path prefix
            if role_key is None:
                path = str(request.url.path)
                if '/si/' in path:
                    role_key = 'system_integrator'
                elif '/app/' in path:
                    role_key = 'access_point_provider'
            # Apply dynamic rule if mapping present
            if role_key and role_key in routing.rate_limits:
                per_hour = routing.rate_limits[role_key]
                per_minute = max(1, int(per_hour / 60))
                rule_name = f"dynamic_{version}_{role_key}_per_user"
                # Create/update a high-priority rule for this version+role scope
                rate_limiter.add_rule(RateLimitRule(
                    name=rule_name,
                    limit_type=RateLimitType.PER_USER,
                    max_requests=per_minute,
                    window=RateLimitWindow.MINUTE,
                    window_seconds=60,
                    endpoint_pattern=f"/api/{version}/*",
                    priority=120,  # higher than defaults
                ))
    except Exception as _e:
        # Fail open on adapter issues
        pass

    try:
        # Check rate limit
        is_allowed, rate_info = await rate_limiter.check_rate_limit(request)
        
        if not is_allowed:
            # Return rate limit exceeded response
            retry_after = rate_info.get("retry_after", 60)
            
            response_data = {
                "error": "Rate limit exceeded",
                "message": f"Too many requests. Try again in {retry_after} seconds.",
                "rate_limit": {
                    "limit": rate_info.get("limits", {}).get(rate_info.get("rule_violated", {}), {}).get("limit"),
                    "remaining": 0,
                    "retry_after": retry_after,
                    "rule": rate_info.get("rule_violated")
                }
            }
            
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=response_data,
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(rate_info.get("limits", {}).get(rate_info.get("rule_violated", {}), {}).get("limit", "unknown")),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time()) + retry_after)
                }
            )
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to successful responses
        if rate_info.get("limits"):
            # Get the most restrictive limit for headers
            most_restrictive = min(
                rate_info["limits"].values(),
                key=lambda x: x.get("remaining", float('inf'))
            )
            
            response.headers["X-RateLimit-Limit"] = str(most_restrictive.get("limit", "unknown"))
            response.headers["X-RateLimit-Remaining"] = str(most_restrictive.get("remaining", "unknown"))
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + most_restrictive.get("window_seconds", 60))
        
        return response
        
    except Exception as e:
        logger.error(f"Rate limiting middleware error: {e}")
        # Fail open - continue processing request
        return await call_next(request)
