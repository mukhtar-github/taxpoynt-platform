"""
POS Connector Template (Example)
================================
Use BaseHTTPConnector to implement a resilient POS connector with retries.
"""
from __future__ import annotations

from typing import Any, Dict
from external_integrations.connector_framework.base_http_connector import BaseHTTPConnector


class ExamplePOSConnector(BaseHTTPConnector):
    def __init__(self, base_url: str, api_key: str):
        super().__init__(base_url=base_url, default_headers={"Authorization": f"Bearer {api_key}"})

    async def list_orders(self, *, limit: int = 50, page: int = 1) -> Dict[str, Any]:
        resp = await self.get("/v1/orders", params={"limit": limit, "page": page})
        resp.raise_for_status()
        return resp.json()

    async def get_order(self, order_id: str) -> Dict[str, Any]:
        resp = await self.get(f"/v1/orders/{order_id}")
        resp.raise_for_status()
        return resp.json()

