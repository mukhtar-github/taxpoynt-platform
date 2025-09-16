"""
TaxPoynt Platform - OWASP Security Headers
==========================================
Production-grade security headers implementation following OWASP guidelines.
Protects against XSS, clickjacking, MIME sniffing, and other web vulnerabilities.
"""

import logging
from typing import Dict, Any, Optional
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import os

logger = logging.getLogger(__name__)


class OWASPSecurityHeaders:
    """
    OWASP-compliant security headers for production financial platform.
    
    Implements security headers to protect against:
    - Cross-Site Scripting (XSS)
    - Clickjacking attacks
    - MIME type sniffing
    - Information leakage
    - Man-in-the-middle attacks
    - Content injection
    """
    
    def __init__(self):
        self.environment = os.getenv("ENVIRONMENT", "production").lower()
        self.domain = os.getenv("DOMAIN", "taxpoynt.com")
        self.frontend_domains = self._get_frontend_domains()
        
        # Security header configuration
        self.security_headers = self._build_security_headers()
        
        logger.info("OWASP Security Headers initialized for production")
    
    def _get_frontend_domains(self) -> list:
        """Get allowed frontend domains"""
        domains = [
            f"https://app.{self.domain}",
            f"https://www.{self.domain}",
            f"https://{self.domain}"
        ]
        
        # Add development domains if needed
        if self.environment == "development":
            domains.extend([
                "http://localhost:3000",
                "http://localhost:3001",
                "https://app-staging.taxpoynt.com"
            ])
        
        return domains
    
    def _build_security_headers(self) -> Dict[str, str]:
        """Build comprehensive OWASP security headers"""
        
        # Build Content Security Policy
        extra_connect = os.getenv("CSP_EXTRA_CONNECT_SRC", "").strip()
        extra_connect_list = [s for s in (x.strip() for x in extra_connect.split(",")) if s]
        csp_directives = [
            "default-src 'self'",
            f"script-src 'self' 'unsafe-inline' 'unsafe-eval' https://*.{self.domain}",
            f"style-src 'self' 'unsafe-inline' https://*.{self.domain} https://fonts.googleapis.com",
            f"img-src 'self' data: https://*.{self.domain} https://mono.co https://stitch.money",
            f"font-src 'self' https://fonts.gstatic.com https://*.{self.domain}",
            f"connect-src 'self' https://*.{self.domain} https://api.firs.gov.ng https://api.mono.co https://api.stitch.money https://*.ondigitalocean.app"
            + (" " + " ".join(extra_connect_list) if extra_connect_list else ""),
            f"frame-src 'self' https://*.{self.domain} https://connect.mono.co https://js.stitch.money",
            "frame-ancestors 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "upgrade-insecure-requests"
        ]
        
        # Add report-uri for CSP violations in production
        if self.environment == "production":
            csp_directives.append(f"report-uri https://api.{self.domain}/security/csp-report")
        
        csp_policy = "; ".join(csp_directives)
        
        return {
            # Content Security Policy - Prevents XSS and injection attacks
            "Content-Security-Policy": csp_policy,
            
            # HTTP Strict Transport Security - Enforces HTTPS
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains; preload",
            
            # X-Frame-Options - Prevents clickjacking
            "X-Frame-Options": "DENY",
            
            # X-Content-Type-Options - Prevents MIME sniffing
            "X-Content-Type-Options": "nosniff",
            
            # X-XSS-Protection - XSS filter (legacy but still useful)
            "X-XSS-Protection": "1; mode=block",
            
            # Referrer Policy - Controls referrer information
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Permissions Policy - Controls browser features
            "Permissions-Policy": (
                "camera=(), "
                "microphone=(), "
                "geolocation=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "accelerometer=(), "
                "gyroscope=()"
            ),
            
            # Cross-Origin Embedder Policy
            "Cross-Origin-Embedder-Policy": "require-corp",
            
            # Cross-Origin Opener Policy  
            "Cross-Origin-Opener-Policy": "same-origin",
            
            # Cross-Origin Resource Policy
            "Cross-Origin-Resource-Policy": "same-site",
            
            # Server identification (hide server info)
            "Server": "TaxPoynt-API",
            
            # Remove X-Powered-By header
            "X-Powered-By": "",
            
            # Cache Control for sensitive endpoints
            "Cache-Control": "no-store, no-cache, must-revalidate, private",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    
    def add_security_headers(self, response: Response, endpoint_path: str = "") -> Response:
        """Add security headers to response"""
        try:
            # Apply all security headers
            for header_name, header_value in self.security_headers.items():
                if header_value:  # Only add non-empty headers
                    response.headers[header_name] = header_value
            
            # Endpoint-specific header adjustments
            if endpoint_path.startswith("/api/v1/auth"):
                # Stricter headers for auth endpoints
                response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, private, max-age=0"
                response.headers["X-Frame-Options"] = "DENY"
            
            elif endpoint_path.startswith("/api/v1/webhooks"):
                # Webhook endpoints - allow external requests but secure
                response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
            
            elif endpoint_path.startswith("/docs") or endpoint_path.startswith("/redoc"):
                # API documentation - only in development
                if self.environment != "development":
                    response.headers["X-Robots-Tag"] = "noindex, nofollow"
            
            # Add security timestamp
            response.headers["X-Security-Timestamp"] = str(int(__import__('time').time()))
            
            return response
            
        except Exception as e:
            logger.error(f"Error adding security headers: {e}")
            return response
    
    def get_csp_report_handler(self):
        """Get CSP violation report handler"""
        async def csp_report_handler(request: Request):
            try:
                report_data = await request.json()
                logger.warning(f"CSP Violation Report: {report_data}")
                
                # In production, you might want to send this to a monitoring service
                # like Sentry, DataDog, or store in database for analysis
                
                return JSONResponse(
                    status_code=204,
                    content={"status": "report_received"}
                )
            except Exception as e:
                logger.error(f"Error processing CSP report: {e}")
                return JSONResponse(
                    status_code=400,
                    content={"error": "Invalid report format"}
                )
        
        return csp_report_handler
    
    def validate_request_headers(self, request: Request) -> Dict[str, Any]:
        """Validate incoming request headers for security"""
        validation_result = {
            "is_valid": True,
            "warnings": [],
            "security_score": 100
        }
        
        try:
            # Check for suspicious headers
            suspicious_patterns = [
                "X-Forwarded-Host",  # Potential host header injection
                "X-Original-URL",    # Potential path traversal
                "X-Rewrite-URL"      # Potential URL manipulation
            ]
            
            for pattern in suspicious_patterns:
                if pattern in request.headers:
                    validation_result["warnings"].append(f"Suspicious header detected: {pattern}")
                    validation_result["security_score"] -= 10
            
            # Check User-Agent (basic bot detection)
            user_agent = request.headers.get("User-Agent", "")
            if not user_agent or len(user_agent) < 10:
                validation_result["warnings"].append("Missing or suspicious User-Agent")
                validation_result["security_score"] -= 5
            
            # Check for security headers in requests (from other services)
            security_headers_present = bool(
                request.headers.get("X-API-Key") or
                request.headers.get("Authorization") or
                request.headers.get("X-Webhook-Signature")
            )
            
            if not security_headers_present and not request.url.path.startswith("/health"):
                validation_result["warnings"].append("No authentication headers present")
                validation_result["security_score"] -= 15
            
            # Determine overall validity
            validation_result["is_valid"] = validation_result["security_score"] >= 70
            
        except Exception as e:
            logger.error(f"Error validating request headers: {e}")
            validation_result["is_valid"] = False
            validation_result["warnings"].append(f"Header validation error: {str(e)}")
        
        return validation_result
    
    def get_security_report(self) -> Dict[str, Any]:
        """Get security configuration report"""
        return {
            "owasp_compliance": {
                "content_security_policy": True,
                "strict_transport_security": True,
                "x_frame_options": True,
                "x_content_type_options": True,
                "x_xss_protection": True,
                "referrer_policy": True,
                "permissions_policy": True
            },
            "headers_configured": len(self.security_headers),
            "environment": self.environment,
            "domain": self.domain,
            "frontend_domains": len(self.frontend_domains),
            "csp_directives": len(self.security_headers.get("Content-Security-Policy", "").split(";")),
            "security_level": "production" if self.environment == "production" else "development"
        }


# Global security headers instance
_security_headers: Optional[OWASPSecurityHeaders] = None


def get_security_headers() -> OWASPSecurityHeaders:
    """Get global security headers instance"""
    global _security_headers
    if _security_headers is None:
        _security_headers = OWASPSecurityHeaders()
    return _security_headers


def initialize_security_headers() -> OWASPSecurityHeaders:
    """Initialize security headers"""
    global _security_headers
    _security_headers = OWASPSecurityHeaders()
    return _security_headers


async def security_headers_middleware(request: Request, call_next):
    """FastAPI middleware to add OWASP security headers"""
    try:
        security_headers = get_security_headers()
        
        # Validate incoming request headers
        header_validation = security_headers.validate_request_headers(request)
        
        # Log security warnings
        if header_validation["warnings"]:
            logger.warning(f"Security warnings for {request.url.path}: {header_validation['warnings']}")
        
        # Process request
        response = await call_next(request)
        
        # Add security headers to response
        response = security_headers.add_security_headers(response, str(request.url.path))
        
        return response
        
    except Exception as e:
        logger.error(f"Security headers middleware error: {e}")
        # Fail safe - continue processing
        return await call_next(request)


# Optional type hint
from typing import Optional
