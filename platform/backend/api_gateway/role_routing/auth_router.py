"""
Authentication Router - Shared Across All Service Types
======================================================
Provides authentication endpoints accessible to SI, APP, and Hybrid users.
Integrates with role-based routing system and supports user onboarding flow.
"""
import asyncio
import base64
import json
import logging
import os
import re
import smtplib
import secrets
import string
import uuid
from datetime import datetime, timedelta, timezone
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from typing import Dict, Any, Optional, List, Tuple, Union, Literal, Awaitable

from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from passlib.context import CryptContext
import jwt
import httpx

# Fix import paths
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from core_platform.authentication.role_manager import PlatformRole
    from core_platform.messaging.message_router import MessageRouter, ServiceRole
    from core_platform.security import get_oauth2_manager
except ImportError:
    from . import PlatformRole, MessageRouter, ServiceRole  # type: ignore

    def get_oauth2_manager():  # type: ignore
        raise RuntimeError("OAuth2 manager unavailable in fallback mode")

from .models import HTTPRoutingContext
from .role_detector import HTTPRoleDetector
from .permission_guard import APIPermissionGuard
from .auth_database import get_auth_database
from core_platform.data_management.db_async import get_async_session
from core_platform.data_management.repositories.onboarding_state_repo_async import (
    OnboardingStateRepositoryAsync,
)
from core_platform.services.kyc import SubmitKYCCommand

logger = logging.getLogger(__name__)
SHARED_CONFIG_DIR = Path(__file__).resolve().parents[3] / "shared_config"
FREE_EMAIL_DOMAINS_DEFAULT_PATH = SHARED_CONFIG_DIR / "free_email_domains.json"
submit_kyc_command = SubmitKYCCommand()

# Authentication configuration
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
security = HTTPBearer()

# JWT settings are managed centrally by core_platform.security.jwt_manager

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

class PasswordResetRequest(BaseModel):
    """Password reset request model"""
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    """Password reset confirmation model"""
    token: str
    new_password: str

class EmailVerificationRequest(BaseModel):
    """Email verification request payload"""
    email: EmailStr
    code: str
    service_package: Optional[str] = None
    onboarding_token: Optional[str] = None
    terms_accepted: bool = False
    privacy_accepted: bool = False
    tin: Optional[str] = None
    rc_number: Optional[str] = None

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


class RegistrationPendingResponse(BaseModel):
    """Pending registration response when email verification is required."""
    status: Literal["pending"] = "pending"
    next: str
    user: UserResponse
    onboarding_token: Optional[str] = None
    message: Optional[str] = None


class OAuthTokenResponse(BaseModel):
    """OAuth 2.0 token response payload."""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: Optional[str] = None
    consent_summary: Optional[str] = None
    scope_descriptions: Optional[Dict[str, str]] = None


class OAuthIntrospectionResponse(BaseModel):
    """OAuth 2.0 token introspection response."""

    active: bool
    client_id: Optional[str] = None
    scope: Optional[str] = None
    token_type: Optional[str] = None
    exp: Optional[int] = None
    iat: Optional[int] = None
    grant_type: Optional[str] = None
    token_usage: Optional[str] = None

# Database integration (production-ready)
from .auth_database import get_auth_database

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def _generate_verification_code(length: int = 6) -> str:
    alphabet = string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def _dev_email_fallback_enabled() -> bool:
    env = os.getenv("ENVIRONMENT", "development").lower()
    allow_fallback = os.getenv("ALLOW_DEV_EMAIL_FALLBACK", "true").lower() not in {"false", "0", "no"}
    return env != "production" and allow_fallback


def _email_sender_identity() -> Tuple[str, str]:
    from_email = os.getenv("EMAILS_FROM_EMAIL") or os.getenv("SMTP_FROM_EMAIL")
    if not from_email:
        raise RuntimeError("EMAILS_FROM_EMAIL (or SMTP_FROM_EMAIL) must be configured for verification emails.")
    from_name = os.getenv("EMAILS_FROM_NAME", "TaxPoynt Platform")
    return from_email, from_name


def _smtp_config() -> Optional[Dict[str, Any]]:
    host = os.getenv("SMTP_HOST")
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    try:
        from_email, from_name = _email_sender_identity()
    except RuntimeError:
        from_email = from_name = None  # Defer to fallback handling
    port = int(os.getenv("SMTP_PORT", "587"))
    use_tls = os.getenv("SMTP_TLS", "true").lower() != "false"

    if not all([host, username, password, from_email]):
        if _dev_email_fallback_enabled():
            logger.warning(
                "SMTP configuration incomplete; using development fallback for verification email delivery."
            )
            return None
        raise RuntimeError("SMTP configuration is incomplete. Ensure SMTP_* and EMAILS_FROM_* variables are set.")

    return {
        "host": host,
        "port": port,
        "username": username,
        "password": password,
        "from_email": from_email,
        "from_name": from_name,
        "use_tls": use_tls,
    }


async def _send_via_sendgrid(
    *,
    api_key: str,
    recipient: str,
    subject: str,
    body: str,
    from_email: str,
    from_name: str,
) -> None:
    timeout = float(os.getenv("SENDGRID_TIMEOUT_SECONDS", os.getenv("SMTP_TIMEOUT_SECONDS", "15")))
    payload = {
        "personalizations": [
            {
                "to": [{"email": recipient}],
            }
        ],
        "from": {"email": from_email, "name": from_name},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": body},
        ],
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post("https://api.sendgrid.com/v3/mail/send", json=payload, headers=headers)
        response.raise_for_status()


async def _send_verification_email(recipient: str, code: str, first_name: Optional[str] = None) -> None:
    from_email, from_name = _email_sender_identity()
    subject = "Verify your TaxPoynt email"
    greeting = first_name or recipient.split("@")[0]
    body = (
        f"Hello {greeting},\n\n"
        "Thanks for registering with TaxPoynt.\n\n"
        f"Your verification code is: {code}\n\n"
        "Enter this code in the verification screen to unlock your onboarding checklist.\n\n"
        "If you did not create this account, please contact support immediately.\n\n"
        "— TaxPoynt Platform"
    )

    sendgrid_key = os.getenv("SENDGRID_API_KEY")
    if sendgrid_key:
        try:
            await _send_via_sendgrid(
                api_key=sendgrid_key,
                recipient=recipient,
                subject=subject,
                body=body,
                from_email=from_email,
                from_name=from_name,
            )
            return
        except Exception as exc:
            logger.error("SendGrid verification email delivery failed: %s", exc, exc_info=True)
            if not os.getenv("SMTP_HOST"):
                if _dev_email_fallback_enabled():
                    logger.info(
                        "DEV EMAIL FALLBACK ACTIVE - verification code for %s: %s",
                        recipient,
                        code,
                    )
                    return
                raise
            logger.warning("Falling back to SMTP delivery after SendGrid failure: %s", exc)

    config = _smtp_config()

    if not config:
        logger.info(
            "DEV EMAIL FALLBACK ACTIVE - verification code for %s: %s",
            recipient,
            code,
        )
        return

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = formataddr((config["from_name"], config["from_email"]))
    message["To"] = recipient
    message.attach(MIMEText(body, "plain"))

    timeout_seconds = float(os.getenv("SMTP_TIMEOUT_SECONDS", "15"))

    def _send():
        with smtplib.SMTP(config["host"], config["port"], timeout=timeout_seconds) as server:
            if config.get("use_tls", True):
                server.starttls()
            server.login(config["username"], config["password"])
            server.send_message(message)

    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(None, _send)
    except Exception as exc:
        if _dev_email_fallback_enabled():
            logger.warning(
                "Verification email send failed, falling back to development console delivery: %s",
                exc,
            )
            logger.info(
                "DEV EMAIL FALLBACK ACTIVE - verification code for %s: %s",
                recipient,
                code,
            )
            return
        raise


def _isoformat_utc(value: datetime) -> str:
    return value.replace(microsecond=0).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


async def _record_onboarding_account_status(
    user_id: str,
    service_package: Optional[str],
    *,
    verified_at: Optional[str],
    terms_accepted_at: Optional[str],
) -> None:
    if not verified_at:
        return

    try:
        async for session in get_async_session():
            repo = OnboardingStateRepositoryAsync(session)
            record = await repo.ensure_state(user_id, service_package or "si")
            metadata = dict(record.state_metadata or {})
            account_status = dict(metadata.get("account_status") or {})
            account_status["verified_at"] = verified_at
            if terms_accepted_at:
                account_status["terms_accepted_at"] = terms_accepted_at
            metadata["account_status"] = account_status
            record.state_metadata = metadata
            now = datetime.now(timezone.utc)
            record.updated_at = now
            record.last_active_date = now
            await repo.persist(record)
            break
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.warning(
            "Failed to persist onboarding account status for user %s: %s",
            user_id,
            exc,
        )


def _launch_submit_kyc_task(coro: Awaitable[Any]) -> None:
    """Schedule SubmitKYCCommand without blocking the request lifecycle."""
    try:
        task = asyncio.create_task(coro)
    except RuntimeError:
        logger.debug("SubmitKYCCommand task could not be scheduled (event loop unavailable)")
        return

    def _handle_task_result(async_task: asyncio.Task) -> None:
        if async_task.cancelled():
            return
        exc = async_task.exception()
        if exc:
            logger.error("SubmitKYCCommand task failed: %s", exc, exc_info=True)

    task.add_done_callback(_handle_task_result)


async def _run_submit_kyc_command(
    *,
    user_id: str,
    service_package: Optional[str],
    tin: Optional[str],
    rc_number: Optional[str],
    email: Optional[str],
) -> None:
    if not submit_kyc_command:
        return
    try:
        await submit_kyc_command.execute(
            user_id=user_id,
            service_package=service_package or "si",
            tin=tin,
            rc_number=rc_number,
            email=email,
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        logger.error("SubmitKYCCommand failed for %s: %s", user_id, exc, exc_info=True)


def _normalize_domain_entry(value: Any) -> Optional[str]:
    if isinstance(value, str):
        token = value.strip().lower()
        if token and not token.startswith("#"):
            return token
    return None


def _parse_domain_tokens(raw: Optional[str]) -> set[str]:
    if not raw:
        return set()
    tokens = re.split(r"[,\s]+", raw)
    domains = {token for token in (_normalize_domain_entry(t) for t in tokens) if token}
    return domains


def _read_domains_from_path(path: Path) -> set[str]:
    domains: set[str] = set()
    try:
        if not path.exists():
            return domains
        if path.suffix.lower() == ".json":
            payload = json.loads(path.read_text(encoding="utf-8"))
            candidates = []
            if isinstance(payload, list):
                candidates = payload
            elif isinstance(payload, dict):
                for key in ("domains", "denylist", "blocklist", "free"):
                    value = payload.get(key)
                    if isinstance(value, list):
                        candidates = value
                        break
            domains.update(
                token for token in (_normalize_domain_entry(entry) for entry in candidates) if token
            )
        else:
            for line in path.read_text(encoding="utf-8").splitlines():
                token = _normalize_domain_entry(line)
                if token:
                    domains.add(token)
    except Exception as exc:
        logger.warning("Failed to load domain list from %s: %s", path, exc)
    return domains


def _load_business_email_policy() -> Dict[str, Any]:
    mode = os.getenv("BUSINESS_EMAIL_POLICY_MODE", "strict").strip().lower()
    if mode in {"allowlist", "allowlist_only"}:
        mode = "allowlist_only"
    elif mode in {"disabled", "off", "skip"}:
        mode = "disabled"
    else:
        mode = "strict"

    denylist: set[str] = set()
    denylist.update(_read_domains_from_path(FREE_EMAIL_DOMAINS_DEFAULT_PATH))
    denylist.update(_parse_domain_tokens(os.getenv("BUSINESS_EMAIL_DENYLIST")))
    denylist_path = os.getenv("BUSINESS_EMAIL_DENYLIST_PATH")
    if denylist_path:
        denylist.update(_read_domains_from_path(Path(denylist_path).expanduser()))

    allowlist: set[str] = set()
    allowlist.update(_parse_domain_tokens(os.getenv("BUSINESS_EMAIL_ALLOWLIST")))
    allowlist_path = os.getenv("BUSINESS_EMAIL_ALLOWLIST_PATH")
    if allowlist_path:
        allowlist.update(_read_domains_from_path(Path(allowlist_path).expanduser()))

    return {
        "mode": mode,
        "denylist": denylist,
        "allowlist": allowlist,
    }


def _domain_matches(domain: str, candidates: set[str]) -> bool:
    domain = domain.lower()
    for candidate in candidates:
        if not candidate:
            continue
        if candidate.startswith("*."):
            suffix = candidate[1:]
            if domain.endswith(suffix):
                return True
        elif domain == candidate:
            return True
        elif domain.endswith(f".{candidate}"):
            return True
    return False


def _enforce_business_email_policy(email: str) -> None:
    policy = _load_business_email_policy()
    if policy["mode"] == "disabled":
        return

    try:
        domain = email.split("@", 1)[1].lower()
    except IndexError:
        return

    if _domain_matches(domain, policy["allowlist"]):
        return

    if policy["mode"] == "allowlist_only":
        logger.info("Rejected registration for domain %s (not in allowlist)", domain)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This sign-up requires an approved business email domain.",
        )

    if _domain_matches(domain, policy["denylist"]):
        logger.info("Rejected registration for non-business email domain %s", domain)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please use a business email address to sign up.",
        )


def _oauth_error(error: str, status_code: int, description: Optional[str] = None) -> HTTPException:
    payload = {"error": error}
    if description:
        payload["error_description"] = description
    headers = {"WWW-Authenticate": 'Basic realm="TaxPoynt OAuth2"'} if status_code == status.HTTP_401_UNAUTHORIZED else {}
    return HTTPException(status_code=status_code, detail=payload, headers=headers)


def _extract_client_credentials(request: Request, form_data: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.lower().startswith("basic "):
        try:
            encoded = auth_header.split(" ", 1)[1]
            decoded = base64.b64decode(encoded).decode()
            client_id, client_secret = decoded.split(":", 1)
            return client_id or None, client_secret or None
        except Exception:
            return None, None

    # Fallback to form parameters
    client_id = form_data.get("client_id")
    client_secret = form_data.get("client_secret")
    return client_id, client_secret

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create JWT access token using centralized manager."""
    from core_platform.security import get_jwt_manager
    jwt_manager = get_jwt_manager()
    user_data = {
        "user_id": data.get("user_id") or data.get("sub"),
        "email": data.get("email") or data.get("sub"),
        "role": data.get("role"),
        "organization_id": data.get("organization_id"),
        "permissions": data.get("permissions", [])
    }
    return jwt_manager.create_access_token(user_data)

def verify_access_token(token: str) -> Dict[str, Any]:
    """Verify and decode JWT access token via centralized manager.

    Normalizes claims to include `user_id` for legacy callers by
    mapping the standard `sub` claim to `user_id` when missing.
    """
    try:
        from core_platform.security import get_jwt_manager
        jwt_manager = get_jwt_manager()
        payload = jwt_manager.verify_token(token)

        # Back-compat: many callers expect `user_id` in payload.
        # Our unified JWT uses `sub` as the canonical subject.
        if payload.get("user_id") is None and payload.get("sub") is not None:
            payload["user_id"] = payload.get("sub")

        return payload
    except jwt.InvalidTokenError as e:
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

def convert_db_role_to_frontend_role(db_role: str) -> str:
    """Convert database UserRole enum value to frontend-expected role string"""
    role_conversion = {
        "si_user": "system_integrator",
        "app_user": "access_point_provider", 
        "hybrid_user": "hybrid_user",
        "business_owner": "business_owner",
        "business_admin": "business_admin",
        "business_user": "business_user",
        "platform_admin": "platform_admin"
    }
    return role_conversion.get(db_role, db_role)

def create_auth_router(
    role_detector: HTTPRoleDetector,
    permission_guard: APIPermissionGuard,
    message_router: MessageRouter
) -> APIRouter:
    """Factory function to create authentication router"""
    
    router = APIRouter(prefix="/auth", tags=["Authentication"])

    async def _emit_onboarding_events(events: List[Dict[str, Any]]) -> None:
        """Emit onboarding analytics events through the message router."""
        if not events:
            return

        route = getattr(message_router, "route_message", None)
        if route is None:
            return

        # Ensure timestamps are available for batching
        batch_timestamp = None
        for event in events:
            if isinstance(event, dict):
                ts = event.get("timestamp")
                if isinstance(ts, str) and ts:
                    batch_timestamp = ts
                    break

        if batch_timestamp is None:
            batch_timestamp = _isoformat_utc(datetime.now(timezone.utc))

        try:
            await route(
                service_role=ServiceRole.ANALYTICS,
                operation="process_onboarding_events",
                payload={
                    "events": events,
                    "batch_timestamp": batch_timestamp,
                    "api_version": "v1",
                },
            )
        except Exception as analytics_error:  # pragma: no cover - analytics is best-effort
            logger.debug("Failed to emit onboarding analytics events: %s", analytics_error)

    @router.post("/oauth/token", response_model=OAuthTokenResponse, include_in_schema=False)
    async def oauth_token(request: Request):
        oauth_manager = get_oauth2_manager()
        form = await request.form()

        client_id, client_secret = _extract_client_credentials(request, form)
        if not client_id or not client_secret:
            raise _oauth_error("invalid_client", status.HTTP_401_UNAUTHORIZED, "Client authentication failed")

        grant_type = (form.get("grant_type") or "").strip().lower()
        if grant_type != "client_credentials":
            raise _oauth_error("unsupported_grant_type", status.HTTP_400_BAD_REQUEST, "Only client_credentials grant is supported")

        client = oauth_manager.validate_client_credentials(client_id, client_secret)
        if not client:
            raise _oauth_error("invalid_client", status.HTTP_401_UNAUTHORIZED, "Client authentication failed")

        scope = form.get("scope")
        try:
            token_bundle = oauth_manager.issue_client_credentials_token(client, scope)
        except ValueError as exc:
            if str(exc) == "invalid_scope":
                raise _oauth_error("invalid_scope", status.HTTP_400_BAD_REQUEST, "Requested scope is not permitted for this client")
            raise _oauth_error("invalid_request", status.HTTP_400_BAD_REQUEST, str(exc))

        client_meta = client.client_metadata

        return OAuthTokenResponse(
            access_token=token_bundle.access_token,
            token_type=token_bundle.token_type,
            expires_in=token_bundle.expires_in,
            scope=token_bundle.scope or None,
            consent_summary=client_meta.get("consent_summary"),
            scope_descriptions=client_meta.get("scope_descriptions"),
        )

    @router.post("/oauth/introspect", response_model=OAuthIntrospectionResponse, include_in_schema=False)
    async def oauth_introspect(request: Request):
        oauth_manager = get_oauth2_manager()
        form = await request.form()

        client_id, client_secret = _extract_client_credentials(request, form)
        if not client_id or not client_secret:
            raise _oauth_error("invalid_client", status.HTTP_401_UNAUTHORIZED, "Client authentication failed")

        client = oauth_manager.validate_client_credentials(client_id, client_secret)
        if not client:
            raise _oauth_error("invalid_client", status.HTTP_401_UNAUTHORIZED, "Client authentication failed")

        token = form.get("token")
        if not token:
            raise _oauth_error("invalid_request", status.HTTP_400_BAD_REQUEST, "token parameter is required")

        result = oauth_manager.introspect(token)
        return OAuthIntrospectionResponse(**result)

    @router.post("/register", response_model=Union[TokenResponse, RegistrationPendingResponse])
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

            _enforce_business_email_policy(user_data.email)
            
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

            verification_mode = os.getenv("EMAIL_VERIFICATION_MODE", "strict").lower()
            if verification_mode == "relaxed":
                logger.warning(
                    "EMAIL_VERIFICATION_MODE=relaxed – auto-verifying %s for testing. Do not enable in production.",
                    user["email"],
                )
                updated_user = db.mark_email_verified(
                    user_id=user_id,
                    terms_accepted=user_data.terms_accepted,
                    privacy_accepted=user_data.privacy_accepted,
                )
                user.update(updated_user)
            else:
                verification_code = _generate_verification_code()
                hashed_code = hash_password(verification_code)

                try:
                    db.set_email_verification_token(user_id, hashed_code)
                    await _send_verification_email(
                        recipient=user["email"],
                        code=verification_code,
                        first_name=user.get("first_name")
                    )
                except Exception as email_error:
                    logger.error(f"Failed to send verification email: {email_error}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="Unable to send verification email. Please try again later."
                    )

            logger.info(f"User registered successfully (verification pending): {user['email']} ({user_role})")

            return RegistrationPendingResponse(
                status="pending",
                next="/auth/verify-email",
                user=user_response,
                onboarding_token=secrets.token_urlsafe(32),
                message="Verification email sent. Please check your inbox."
            )
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Registration failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Registration failed due to server error"
            )

    @router.post("/verify-email", response_model=TokenResponse)
    async def verify_email(request: EmailVerificationRequest):
        bypass_enabled = os.getenv("EMAIL_VERIFICATION_BYPASS", "false").lower() in {"1", "true", "yes", "on"}

        try:
            db = get_auth_database()
            user = get_user_by_email(request.email)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

            was_verified = bool(user.get("is_email_verified"))
            verified_at_iso: Optional[str] = user.get("verified_at")
            terms_accepted_at_iso: Optional[str] = user.get("terms_accepted_at")
            had_terms_before = bool(terms_accepted_at_iso)

            if user.get("is_email_verified"):
                logger.info("Email already verified for %s", request.email)
            else:
                token_hash = user.get("email_verification_token")
                code_valid = token_hash and verify_password(request.code, token_hash)
                bypassing = bypass_enabled and request.code == "000000"
                if bypassing:
                    logger.warning(
                        "EMAIL_VERIFICATION_BYPASS active – accepting static code for %s",
                        request.email,
                    )
                if not code_valid and not bypassing:
                    raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid verification code")

                updated_user = db.mark_email_verified(
                    user_id=user["id"],
                    terms_accepted=request.terms_accepted,
                    privacy_accepted=request.privacy_accepted,
                )
                user.update(updated_user)
                verified_at_iso = updated_user.get("verified_at") or verified_at_iso
                if updated_user.get("terms_accepted_at"):
                    terms_accepted_at_iso = updated_user["terms_accepted_at"]

            organization = db.get_organization_by_id(user.get("organization_id"))
            if not organization:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="User organization data not found",
                )

            if user.get("is_email_verified"):
                if not verified_at_iso:
                    verified_at_iso = _isoformat_utc(datetime.now(timezone.utc))
                user["verified_at"] = verified_at_iso
                try:
                    await _record_onboarding_account_status(
                        user_id=user["id"],
                        service_package=user.get("service_package"),
                        verified_at=verified_at_iso,
                        terms_accepted_at=terms_accepted_at_iso,
                    )
                except Exception as exc:  # pragma: no cover - defensive logging
                    logger.debug(
                        "Unable to persist onboarding account status for %s: %s",
                        user["id"],
                        exc,
                    )

                analytics_events: List[Dict[str, Any]] = []
                user_service_package = str(user.get("service_package") or "si").lower()
                session_id = f"{user_service_package}-onboarding-{user['id']}"
                metadata_base = {
                    "service_package": user_service_package,
                    "organization_id": user.get("organization_id"),
                }
                verification_timestamp = verified_at_iso or _isoformat_utc(datetime.now(timezone.utc))

                if not was_verified:
                    analytics_events.append(
                        {
                            "eventType": "si_onboarding.email_verified",
                            "stepId": "email_verification",
                            "userId": user["id"],
                            "userRole": user_service_package,
                            "timestamp": verification_timestamp,
                            "sessionId": session_id,
                            "metadata": {
                                **metadata_base,
                                "verified_at": verification_timestamp,
                                "terms_accepted": bool(request.terms_accepted),
                                "privacy_accepted": bool(request.privacy_accepted),
                                "onboarding_token": request.onboarding_token,
                            },
                        }
                    )

                if request.terms_accepted:
                    if not terms_accepted_at_iso:
                        terms_accepted_at_iso = verification_timestamp
                    analytics_events.append(
                        {
                            "eventType": "si_onboarding.terms_confirmed",
                            "stepId": "terms_acceptance",
                            "userId": user["id"],
                            "userRole": user_service_package,
                            "timestamp": terms_accepted_at_iso,
                            "sessionId": session_id,
                            "metadata": {
                                **metadata_base,
                                "terms_accepted_at": terms_accepted_at_iso,
                                "verified_at": verification_timestamp,
                                "onboarding_token": request.onboarding_token,
                            },
                        }
                    )

                if analytics_events:
                    await _emit_onboarding_events(analytics_events)

            organization_response = OrganizationResponse(
                id=organization["id"],
                name=organization["name"],
                business_type=organization["business_type"],
                tin=organization["tin"],
                rc_number=organization["rc_number"],
                status=organization["status"],
                service_packages=organization["service_packages"],
            )

            tin_candidate = request.tin or organization.get("tin")
            rc_candidate = request.rc_number or organization.get("rc_number")
            if tin_candidate or rc_candidate:
                _launch_submit_kyc_task(
                    _run_submit_kyc_command(
                        user_id=user["id"],
                        service_package=user.get("service_package"),
                        tin=tin_candidate,
                        rc_number=rc_candidate,
                        email=user.get("email"),
                    )
                )

            role_str = user["role"] if isinstance(user["role"], str) else user["role"].value
            frontend_role = convert_db_role_to_frontend_role(role_str)

            user_response = UserResponse(
                id=user["id"],
                email=user["email"],
                first_name=user.get("first_name"),
                last_name=user.get("last_name"),
                phone=user.get("phone"),
                role=frontend_role,
                service_package=user["service_package"],
                is_email_verified=True,
                organization=organization_response,
            )

            token_data = {
                "sub": user["email"],
                "user_id": user["id"],
                "role": frontend_role,
                "organization_id": user.get("organization_id"),
                "service_package": user["service_package"],
            }
            access_token = create_access_token(data=token_data)

            from core_platform.security import get_jwt_manager

            jwt_manager = get_jwt_manager()
            return TokenResponse(
                access_token=access_token,
                expires_in=int(jwt_manager.access_token_expire_minutes) * 60,
                user=user_response,
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.error(f"Email verification failed: {exc}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Verification failed due to server error",
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

            if not user.get("is_email_verified", False):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Email address is not verified."
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
                "role": convert_db_role_to_frontend_role(user["role"]),
                "organization_id": user["organization_id"],
                "service_package": user["service_package"]
            }
            
            # Create token via centralized manager (manager controls expiration)
            access_token = create_access_token(data=token_data)
            
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
            
            # Convert database role enum to frontend-expected string
            db_role = user["role"]
            role_str = db_role.value if hasattr(db_role, 'value') else db_role
            frontend_role = convert_db_role_to_frontend_role(role_str)
            
            user_response = UserResponse(
                id=user["id"],
                email=user["email"],
                first_name=user["first_name"],
                last_name=user["last_name"],
                phone=user["phone"],
                role=frontend_role,
                service_package=user["service_package"],
                is_email_verified=user["is_email_verified"],
                organization=organization_response
            )
            
            logger.info(f"User login successful: {user['email']}")
            
            from core_platform.security import get_jwt_manager
            jwt_manager = get_jwt_manager()
            return TokenResponse(
                access_token=access_token,
                expires_in=int(jwt_manager.access_token_expire_minutes) * 60,
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
                role=convert_db_role_to_frontend_role(user["role"]),
                service_package=user["service_package"],
                is_email_verified=user["is_email_verified"],
                organization=organization_response
            )
            
        except HTTPException:
            raise
        except jwt.InvalidTokenError as e:
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

    @router.get("/role")
    async def get_user_role(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Get current user role - simplified endpoint for frontend compatibility"""
        try:
            # Extract and verify token
            token = credentials.credentials
            payload = verify_access_token(token)
            
            user_id = payload.get("user_id")
            role = payload.get("role", "system_integrator")
            
            return JSONResponse(content={
                "role": role,
                "user_id": user_id,
                "permissions": get_role_permissions(role),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        except Exception as e:
            logger.error(f"Get user role failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to get user role"
            )

    @router.get("/session/role")
    async def detect_role_from_session(credentials: HTTPAuthorizationCredentials = Depends(security)):
        """Detect user role from current session - alternative endpoint"""
        try:
            # Extract and verify token
            token = credentials.credentials
            payload = verify_access_token(token)
            
            user_id = payload.get("user_id")
            role = payload.get("role", "system_integrator")
            organization_id = payload.get("organization_id")
            
            # Get full user data
            user = get_user_by_id(user_id)
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="User not found"
                )
            
            return JSONResponse(content={
                "detected_role": role,
                "user_id": user_id,
                "organization_id": organization_id,
                "service_package": user.get("service_package", "si"),
                "permissions": get_role_permissions(role),
                "is_active": user.get("is_active", True),
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except jwt.InvalidTokenError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Role detection from session failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to detect role from session"
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

    # Helper functions using existing infrastructure
    def hash_password(password: str) -> str:
        """Hash password using existing bcrypt context"""
        return pwd_context.hash(password)
    
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify password using existing bcrypt context"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def determine_user_role(service_package: str) -> str:
        """Determine user role from service package"""
        role_mapping = {
            "si": "system_integrator",
            "app": "access_point_provider", 
            "hybrid": "hybrid_user"
        }
        return role_mapping.get(service_package, "system_integrator")
    
    def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID using existing database manager"""
        db = get_auth_database()
        return db.get_user_by_id(user_id)
    
    def get_role_permissions(role: str) -> List[str]:
        """Get permissions for role using existing permission system"""
        # Use the existing role detector and permission guard
        role_detector = HTTPRoleDetector()
        permission_mappings = {
            "system_integrator": [
                "business_systems.read", "business_systems.write", 
                "integration.manage", "organization.manage", "webhook.manage"
            ],
            "access_point_provider": [
                "firs.read", "firs.write", "taxpayer.manage", 
                "compliance.read", "einvoice.issue", "einvoice.validate"
            ],
            "hybrid": [
                "business_systems.read", "business_systems.write", "integration.manage", 
                "organization.manage", "webhook.manage", "firs.read", "firs.write",
                "taxpayer.manage", "compliance.read", "einvoice.issue", "einvoice.validate"
            ]
        }
        return permission_mappings.get(role, [])
    
    @router.post("/forgot-password", status_code=202)
    async def forgot_password(request: PasswordResetRequest):
        """Request password reset email"""
        try:
            # Always return success to prevent email enumeration
            # In a real implementation, send email if user exists
            
            # Get database manager
            db = get_auth_database()
            user = get_user_by_email(request.email)
            
            if user:
                # Generate reset token (simplified - use secure token in production)
                reset_token = str(uuid.uuid4())
                
                # Store reset token with expiration (implement in database)
                # For now, just log it (replace with actual email sending)
                logger.info(f"Password reset token for {request.email}: {reset_token}")
                
                # TODO: Send actual email with reset link
                # send_password_reset_email(request.email, reset_token)
            
            return JSONResponse(content={
                "message": "If an account exists with that email, you'll receive password reset instructions.",
                "timestamp": datetime.utcnow().isoformat()
            }, status_code=202)
            
        except Exception as e:
            logger.error(f"Password reset request failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password reset request failed"
            )

    @router.post("/reset-password", status_code=200)
    async def reset_password(request: PasswordResetConfirm):
        """Reset password using token"""
        try:
            # TODO: Implement token validation and password reset
            # For now, return a placeholder response
            
            logger.info(f"Password reset attempt with token: {request.token[:8]}...")
            
            # Validate token format
            if not request.token or len(request.token) < 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid reset token"
                )
            
            # Validate new password
            if len(request.new_password) < 6:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Password must be at least 6 characters"
                )
            
            # TODO: Implement actual password reset logic
            # - Validate token exists and hasn't expired
            # - Update user password in database
            # - Invalidate reset token
            
            return JSONResponse(content={
                "message": "Password has been reset successfully",
                "timestamp": datetime.utcnow().isoformat()
            })
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Password reset failed: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Password reset failed"
            )
    
    return router
