"""Unit tests for OAuth2Manager client credential issuance."""

import os
from pathlib import Path

from api_gateway.role_routing.auth_database import AuthDatabaseManager
from core_platform.security.oauth2_manager import OAuth2Manager


def test_client_credentials_flow(tmp_path, monkeypatch):
    monkeypatch.setenv("JWT_REDIS_DISABLED", "true")

    db_path = Path(tmp_path) / "oauth_test.db"
    db_url = f"sqlite:///{db_path}"
    db_manager = AuthDatabaseManager(database_url=db_url)

    manager = OAuth2Manager(db_manager=db_manager)

    client_id = "test-client"
    client_secret = "super-secret"
    scopes = ["invoices:read", "invoices:submit"]

    manager.register_client(
        client_id=client_id,
        client_secret=client_secret,
        client_name="Test Client",
        allowed_grant_types=["client_credentials"],
        allowed_scopes=scopes,
    )

    validated = manager.validate_client_credentials(client_id, client_secret)
    assert validated is not None

    token_bundle = manager.issue_client_credentials_token(validated, "invoices:read invoices:submit")
    assert token_bundle.access_token
    assert token_bundle.token_type == "Bearer"
    assert token_bundle.scope == "invoices:read invoices:submit"

    introspection = manager.introspect(token_bundle.access_token)
    assert introspection["active"] is True
    assert introspection["client_id"] == client_id
    assert "invoices:read" in introspection.get("scope", "")
    assert introspection.get("grant_type") == "client_credentials"
