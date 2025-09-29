"""Centralized OAuth 2.0 manager for external client access."""

from __future__ import annotations

import json
import logging
import os
import threading
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any

from passlib.context import CryptContext

from core_platform.data_management.models.oauth_client import (
    OAuthClient,
    OAuthClientStatus,
)
from api_gateway.role_routing.auth_database import get_auth_database, AuthDatabaseManager
from .jwt_manager import get_jwt_manager

logger = logging.getLogger(__name__)


_oauth_client_pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


@dataclass
class OAuthToken:
    """Issued OAuth 2.0 token bundle."""

    access_token: str
    token_type: str
    expires_in: int
    scope: str


class OAuth2Manager:
    """Manages OAuth 2.0 client registry and token issuance."""

    def __init__(self, db_manager: Optional[AuthDatabaseManager] = None):
        self._db = db_manager or get_auth_database()
        self._jwt_manager = get_jwt_manager()
        self._clients: Dict[str, OAuthClient] = {}
        self._lock = threading.RLock()

        self.default_expires_seconds = int(os.getenv("OAUTH2_ACCESS_TOKEN_EXPIRE_SECONDS", "1800"))
        self._load_clients()

    def _load_clients(self) -> None:
        """Load client cache from database."""
        with self._lock:
            try:
                clients = self._db.list_oauth_clients()
                self._clients = {client.client_id: client for client in clients}
                logger.info("OAuth2Manager loaded %d clients", len(self._clients))
            except Exception as exc:
                logger.error("Failed to load OAuth clients: %s", exc)
                self._clients = {}

    @staticmethod
    def hash_secret(secret: str) -> str:
        return _oauth_client_pwd_context.hash(secret)

    @staticmethod
    def verify_secret(secret: str, secret_hash: str) -> bool:
        try:
            return _oauth_client_pwd_context.verify(secret, secret_hash)
        except Exception:
            return False

    def register_client(
        self,
        *,
        client_id: str,
        client_secret: str,
        client_name: str,
        allowed_grant_types: Optional[List[str]] = None,
        allowed_scopes: Optional[List[str]] = None,
        redirect_uris: Optional[List[str]] = None,
        is_confidential: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> OAuthClient:
        """Create or update an OAuth client and refresh cache."""

        secret_hash = self.hash_secret(client_secret)
        grant_types = allowed_grant_types or ["client_credentials"]
        scopes = allowed_scopes or []

        client = self._db.upsert_oauth_client(
            client_id=client_id,
            client_secret_hash=secret_hash,
            client_name=client_name,
            allowed_grant_types=grant_types,
            allowed_scopes=scopes,
            redirect_uris=redirect_uris or [],
            is_confidential=is_confidential,
            status=OAuthClientStatus.ACTIVE,
            metadata=metadata or {},
        )

        with self._lock:
            self._clients[client.client_id] = client

        return client

    def get_client(self, client_id: str) -> Optional[OAuthClient]:
        with self._lock:
            return self._clients.get(client_id)

    def validate_client_credentials(self, client_id: str, client_secret: str) -> Optional[OAuthClient]:
        client = self.get_client(client_id)
        if not client:
            return None
        if client.status != OAuthClientStatus.ACTIVE:
            return None
        if not self.verify_secret(client_secret, client.client_secret_hash):
            return None
        return client

    def ensure_default_clients(self, default_clients: List[Dict[str, Any]]) -> None:
        """Ensure default clients from configuration exist."""
        for entry in default_clients:
            try:
                client_id = entry.get("client_id")
                client_secret = entry.get("client_secret")
                client_name = entry.get("client_name") or client_id
                if not client_id or not client_secret:
                    logger.warning("Skipping default OAuth client with missing credentials")
                    continue
                existing = self.get_client(client_id)
                if existing:
                    continue
                self.register_client(
                    client_id=client_id,
                    client_secret=client_secret,
                    client_name=client_name,
                    allowed_grant_types=entry.get("grant_types") or ["client_credentials"],
                    allowed_scopes=entry.get("scopes") or [],
                    redirect_uris=entry.get("redirect_uris") or [],
                    is_confidential=entry.get("is_confidential", True),
                    metadata=entry.get("metadata") or {},
                )
                logger.info("Registered default OAuth client %s", client_id)
            except Exception as exc:
                logger.error("Failed to register default OAuth client: %s", exc)

    def issue_client_credentials_token(
        self,
        client: OAuthClient,
        scope: Optional[str],
    ) -> OAuthToken:
        scopes_requested = self._normalize_scopes(scope)
        if not client.allows_scopes(scopes_requested):
            raise ValueError("invalid_scope")

        payload = {
            "sub": client.client_id,
            "client_id": client.client_id,
            "scope": " ".join(scopes_requested),
            "token_usage": "external_oauth",
            "grant_type": "client_credentials",
        }
        expires_in = self.default_expires_seconds
        token = self._jwt_manager.create_custom_token(payload, expires_in_seconds=expires_in, token_type="oauth_access")

        return OAuthToken(
            access_token=token,
            token_type="Bearer",
            expires_in=expires_in,
            scope=" ".join(scopes_requested),
        )

    def introspect(self, token: str) -> Dict[str, Any]:
        try:
            payload = self._jwt_manager.verify_token(token)
            return {
                "active": True,
                "client_id": payload.get("client_id") or payload.get("sub"),
                "scope": payload.get("scope", ""),
                "token_type": payload.get("token_type"),
                "exp": payload.get("exp"),
                "iat": payload.get("iat"),
                "grant_type": payload.get("grant_type"),
                "token_usage": payload.get("token_usage"),
            }
        except Exception:
            return {"active": False}

    @staticmethod
    def _normalize_scopes(scope: Optional[str]) -> List[str]:
        if not scope:
            return []
        return [s.strip() for s in scope.split() if s.strip()]


_oauth2_manager: Optional[OAuth2Manager] = None
_oauth2_lock = threading.Lock()


def get_oauth2_manager() -> OAuth2Manager:
    global _oauth2_manager
    if _oauth2_manager is None:
        with _oauth2_lock:
            if _oauth2_manager is None:
                _oauth2_manager = OAuth2Manager()
    return _oauth2_manager


def initialize_oauth2_manager(default_clients: Optional[List[Dict[str, Any]]] = None) -> OAuth2Manager:
    manager = get_oauth2_manager()

    if default_clients is None:
        raw_clients = os.getenv("OAUTH2_DEFAULT_CLIENTS")
        parsed: List[Dict[str, Any]] = []
        if raw_clients:
            try:
                parsed_value = json.loads(raw_clients)
                if isinstance(parsed_value, list):
                    parsed = [entry for entry in parsed_value if isinstance(entry, dict)]
            except json.JSONDecodeError as exc:
                logger.error("Failed to parse OAUTH2_DEFAULT_CLIENTS: %s", exc)
        default_clients = parsed

    if default_clients:
        manager.ensure_default_clients(default_clients)

    return manager
