"""Utility script to seed baseline OAuth 2.0 clients.

Reads secrets from environment variables so credentials never live in git
history. Leveraging the existing `initialize_oauth2_manager` helper keeps the
logic consistent with production startup.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv

from core_platform.security.oauth2_manager import initialize_oauth2_manager


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ENV_FILE = PROJECT_ROOT / ".env"


if ENV_FILE.exists():
    load_dotenv(ENV_FILE)


@dataclass
class SeedSpec:
    client_id: str
    secret_env: str
    client_name: str
    grant_types: List[str]
    scopes: List[str]
    metadata: Dict[str, Any]


DEFAULT_CLIENT_SPECS: List[SeedSpec] = [
    SeedSpec(
        client_id=os.getenv("OAUTH2_MONITORING_CLIENT_ID", "taxpoynt-monitoring-dashboard"),
        secret_env="OAUTH2_MONITORING_CLIENT_SECRET",
        client_name="Monitoring Dashboard",
        grant_types=["client_credentials"],
        scopes=[
            "metrics.read",
            "queues.read",
            "sla.read",
        ],
        metadata={
            "description": "Grafana/Prometheus dashboards for queue throughput and SLA monitoring",
            "owner": "observability",
        },
    ),
    SeedSpec(
        client_id=os.getenv("OAUTH2_PARTICIPANT_GATEWAY_CLIENT_ID", "participant-gateway"),
        secret_env="OAUTH2_PARTICIPANT_GATEWAY_CLIENT_SECRET",
        client_name="Participant Gateway",
        grant_types=["client_credentials"],
        scopes=[
            "invoices.submit",
            "participants.sync",
        ],
        metadata={
            "description": "Store-and-forward participant integration (four-corner support)",
            "owner": "hybrid-services",
        },
    ),
]


def _build_client_payloads() -> List[Dict[str, Any]]:
    payloads: List[Dict[str, Any]] = []
    skipped: List[str] = []

    for spec in DEFAULT_CLIENT_SPECS:
        secret = os.getenv(spec.secret_env)
        if not secret:
            skipped.append(spec.secret_env)
            continue

        payloads.append(
            {
                "client_id": spec.client_id,
                "client_secret": secret,
                "client_name": spec.client_name,
                "grant_types": spec.grant_types,
                "scopes": spec.scopes,
                "metadata": spec.metadata,
            }
        )

    if skipped:
        print(
            "⚠️  Skipped seeding clients because secrets were missing for env vars: "
            + ", ".join(sorted(skipped))
        )

    env_override = os.getenv("OAUTH2_DEFAULT_CLIENTS")
    if env_override:
        try:
            override_payloads = json.loads(env_override)
            if isinstance(override_payloads, list):
                payloads.extend([client for client in override_payloads if isinstance(client, dict)])
        except json.JSONDecodeError as exc:
            print(f"❌ Failed to parse OAUTH2_DEFAULT_CLIENTS override: {exc}")

    return payloads


def main() -> None:
    clients = _build_client_payloads()
    if not clients:
        print("ℹ️  No OAuth clients to seed. Provide secrets via environment variables.")
        return

    initialize_oauth2_manager(default_clients=clients)
    print(f"✅ Seeded {len(clients)} OAuth client(s)")


if __name__ == "__main__":
    main()
