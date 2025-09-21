"""
CRM Connector Template (Example)
================================
Use BaseHTTPConnector to implement a resilient CRM connector with retries.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from external_integrations.connector_framework.base_http_connector import BaseHTTPConnector


class ExampleCRMConnector(BaseHTTPConnector):
    def __init__(self, base_url: str, api_key: str):
        super().__init__(base_url=base_url, default_headers={"Authorization": f"Bearer {api_key}"})

    async def list_deals(self, *, limit: int = 50, page: int = 1) -> Dict[str, Any]:
        resp = await self.get(f"/v1/deals", params={"limit": limit, "page": page})
        resp.raise_for_status()
        return resp.json()

    async def create_deal(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        resp = await self.post("/v1/deals", json=payload)
        resp.raise_for_status()
        return resp.json()

