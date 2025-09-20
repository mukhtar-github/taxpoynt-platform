"""
Odoo Unified Connector
----------------------
Single connector surface to access multiple Odoo modules (ERP, CRM, POS, Sales, eCommerce)
via the same credentials. Designed for demo/testing and light integrations.

Notes:
- Uses Odoo XML-RPC endpoints with API key auth (preferred) or password.
- Async wrappers delegate to xmlrpc.client via asyncio.to_thread to avoid blocking.
- Returned payloads are shaped to what our aggregators expect (lightly normalized).
"""

from __future__ import annotations

import os
import ssl
import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import xmlrpc.client

logger = logging.getLogger(__name__)


class OdooUnifiedConnector:
    def __init__(
        self,
        url: str,
        db: str,
        username: str,
        api_key: Optional[str] = None,
        password: Optional[str] = None,
        verify_ssl: bool = True,
        timeout: int = 120,
        company_id: Optional[int] = None,
    ):
        self.url = url.rstrip("/")
        self.db = db
        self.username = username
        self.api_key = api_key
        self.password = password
        self.verify_ssl = verify_ssl
        self.timeout = timeout
        self.company_id = company_id

        # XML-RPC endpoints
        self._common_endpoint = f"{self.url}/xmlrpc/2/common"
        self._object_endpoint = f"{self.url}/xmlrpc/2/object"

        # Runtime
        self._uid: Optional[int] = None
        self._common = None
        self._models = None

    @classmethod
    def from_env(cls) -> Optional["OdooUnifiedConnector"]:
        url = os.getenv("ODOO_URL") or os.getenv("ODOO_API_URL")
        db = os.getenv("ODOO_DB") or os.getenv("ODOO_DATABASE")
        username = os.getenv("ODOO_USERNAME")
        api_key = os.getenv("ODOO_API_KEY")
        password = os.getenv("ODOO_PASSWORD")
        verify_ssl = str(os.getenv("ODOO_VERIFY_SSL", "true")).lower() in ("1", "true", "yes", "on")
        timeout = int(os.getenv("ODOO_TIMEOUT", "120"))
        company_id = os.getenv("ODOO_COMPANY_ID")
        company_id_int = int(company_id) if company_id and company_id.isdigit() else None

        if not (url and db and username and (api_key or password)):
            logger.debug("Odoo env incomplete; OdooUnifiedConnector disabled")
            return None
        return cls(url, db, username, api_key=api_key, password=password, verify_ssl=verify_ssl, timeout=timeout, company_id=company_id_int)

    def available(self) -> bool:
        return bool(self.url and self.db and self.username and (self.api_key or self.password))

    async def _connect(self) -> Tuple[int, Any, Any]:
        if self._uid and self._common and self._models:
            return self._uid, self._common, self._models

        def _connect_sync():
            context = None
            if self.url.startswith("https"):
                context = ssl._create_unverified_context() if not self.verify_ssl else ssl.create_default_context()
            common = xmlrpc.client.ServerProxy(self._common_endpoint, context=context, allow_none=True)
            models = xmlrpc.client.ServerProxy(self._object_endpoint, context=context, allow_none=True)
            key = self.api_key or self.password or ""
            uid = common.authenticate(self.db, self.username, key, {})
            if not uid:
                raise RuntimeError("Odoo authentication failed (uid is None)")
            return uid, common, models

        self._uid, self._common, self._models = await asyncio.to_thread(_connect_sync)
        return self._uid, self._common, self._models

    async def _execute_kw(self, model: str, method: str, args: List[Any], kw: Optional[Dict[str, Any]] = None) -> Any:
        uid, _, models = await self._connect()
        key = self.api_key or self.password or ""

        def _call():
            return models.execute_kw(self.db, uid, key, model, method, args, kw or {})

        return await asyncio.to_thread(_call)

    # ERP - account.move (customer invoices)
    async def get_invoices_by_date_range(self, start: datetime, end: datetime, limit: int = 200) -> List[Dict[str, Any]]:
        domain = [["move_type", "=", "out_invoice"], ["invoice_date", ">=", start.strftime("%Y-%m-%d")], ["invoice_date", "<=", end.strftime("%Y-%m-%d")]]
        fields = [
            "id",
            "name",
            "invoice_date",
            "partner_id",
            "amount_total",
            "amount_tax",
            "currency_id",
            "invoice_line_ids",
            "state",
            "payment_state",
        ]
        ids = await self._execute_kw("account.move", "search", [domain], {"limit": limit, "order": "invoice_date desc"})
        if not ids:
            return []
        records = await self._execute_kw("account.move", "read", [ids], {"fields": fields})
        # Normalize
        for r in records:
            r["invoice_number"] = r.get("name")
            r["invoice_date"] = r.get("invoice_date")
            r["customer"] = {"name": None}
            # Partner name
            pid = r.get("partner_id")
            if isinstance(pid, list) and len(pid) >= 2:
                r["customer"]["name"] = pid[1]
            r["total_amount"] = float(r.get("amount_total") or 0)
            r["tax_amount"] = float(r.get("amount_tax") or 0)
            # Currency
            cid = r.get("currency_id")
            r["currency"] = (cid[1] if isinstance(cid, list) and len(cid) >= 2 else "NGN")
            r["line_items"] = []
            r["payment_status"] = r.get("payment_state") or r.get("state")
            r["description"] = r.get("name")
        return records

    # CRM - crm.lead (won opportunities)
    async def get_opportunities_by_date_range(self, start: datetime, end: datetime, limit: int = 200) -> List[Dict[str, Any]]:
        # Won opportunities: probability=100 or stage won
        domain = [["type", "=", "opportunity"], ["probability", "=", 100]]
        fields = ["id", "name", "expected_revenue", "date_deadline", "partner_id", "probability"]
        ids = await self._execute_kw("crm.lead", "search", [domain], {"limit": limit, "order": "date_deadline desc"})
        if not ids:
            return []
        records = await self._execute_kw("crm.lead", "read", [ids], {"fields": fields})
        for r in records:
            r["amount"] = float(r.get("expected_revenue") or 0)
            r["stage"] = "Closed Won" if (r.get("probability") == 100) else "Open"
            r["close_date"] = r.get("date_deadline") or datetime.utcnow().strftime("%Y-%m-%d")
            # account/contact
            pid = r.get("partner_id")
            account_name = pid[1] if isinstance(pid, list) and len(pid) >= 2 else None
            r["account"] = {"name": account_name}
            r["contact"] = {}
        return records

    # POS - pos.order (paid/done orders)
    async def get_pos_orders_by_date_range(self, start: datetime, end: datetime, limit: int = 200) -> List[Dict[str, Any]]:
        domain = [["date_order", ">=", start.strftime("%Y-%m-%d %H:%M:%S")], ["date_order", "<=", end.strftime("%Y-%m-%d %H:%M:%S")], ["state", "in", ["paid", "done"]]]
        fields = ["id", "name", "date_order", "amount_total", "amount_tax", "currency_id", "partner_id", "session_id", "state"]
        ids = await self._execute_kw("pos.order", "search", [domain], {"limit": limit, "order": "date_order desc"})
        if not ids:
            return []
        records = await self._execute_kw("pos.order", "read", [ids], {"fields": fields})
        for r in records:
            r["transaction_id"] = r.get("name")
            r["amount"] = float(r.get("amount_total") or 0)
            r["tax_amount"] = float(r.get("amount_tax") or 0)
            r["currency"] = (r.get("currency_id")[1] if isinstance(r.get("currency_id"), list) and len(r.get("currency_id")) >= 2 else "NGN")
            r["customer_name"] = (r.get("partner_id")[1] if isinstance(r.get("partner_id"), list) and len(r.get("partner_id")) >= 2 else "POS Customer")
            r["payment_status"] = "paid"
            r["payment_method"] = "POS"
        return records

    # E-commerce - online orders via sale.order with website_id
    async def get_online_orders_by_date_range(self, start: datetime, end: datetime, limit: int = 200) -> List[Dict[str, Any]]:
        domain = [["website_id", "!=", False], ["date_order", ">=", start.strftime("%Y-%m-%d %H:%M:%S")], ["date_order", "<=", end.strftime("%Y-%m-%d %H:%M:%S")], ["state", "in", ["sale", "done"]]]
        fields = ["id", "name", "date_order", "amount_total", "amount_tax", "currency_id", "partner_id", "state"]
        ids = await self._execute_kw("sale.order", "search", [domain], {"limit": limit, "order": "date_order desc"})
        if not ids:
            return []
        records = await self._execute_kw("sale.order", "read", [ids], {"fields": fields})
        for r in records:
            r["transaction_id"] = r.get("name")
            r["amount"] = float(r.get("amount_total") or 0)
            r["tax_amount"] = float(r.get("amount_tax") or 0)
            r["currency"] = (r.get("currency_id")[1] if isinstance(r.get("currency_id"), list) and len(r.get("currency_id")) >= 2 else "NGN")
            r["customer_name"] = (r.get("partner_id")[1] if isinstance(r.get("partner_id"), list) and len(r.get("partner_id")) >= 2 else "Online Customer")
            r["payment_status"] = "paid" if r.get("state") in ("sale", "done") else "pending"
            r["payment_method"] = "Online"
        return records

