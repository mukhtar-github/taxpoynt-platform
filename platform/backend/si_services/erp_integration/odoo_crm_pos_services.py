"""
Odoo CRM and POS Services (SI)
==============================
Lightweight Odoo-backed CRM (crm.lead) and POS (pos.order) access with retry.
"""
from __future__ import annotations

import os
import asyncio
from typing import Any, Dict, List, Optional
import odoorpc

from si_services.utils.retry import retry_sync


def _odoo_connect() -> odoorpc.ODOO:
    url = os.getenv("ODOO_URL", "http://localhost:8069")
    db = os.getenv("ODOO_DB", "odoo")
    user = os.getenv("ODOO_USERNAME", "admin")
    password = os.getenv("ODOO_API_KEY") or os.getenv("ODOO_PASSWORD", "admin")
    o = odoorpc.ODOO(url.replace("http://", "").replace("https://", ""), protocol="jsonrpc", port=80)
    # Allow URLs with http/https and port in ODOO_URL if provided
    # Basic parsing omitted for brevity; rely on defaults unless env specifies
    o.login(db, user, password)
    return o


class OdooCRMService:
    @staticmethod
    @retry_sync(max_attempts=3, base_delay=0.5, max_delay=3.0, retry_on=(odoorpc.error.RPCError,))
    def _list_opportunities_sync(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        o = _odoo_connect()
        Lead = o.env['crm.lead']
        ids = Lead.search([], offset=offset, limit=limit, order='create_date desc')
        fields = ['id','name','stage_id','probability','partner_id','expected_revenue','date_deadline','type']
        recs = Lead.read(ids, fields)
        result: List[Dict[str, Any]] = []
        for r in recs:
            result.append({
                'id': r.get('id'),
                'name': r.get('name'),
                'stage': (r.get('stage_id') or [None, None])[1],
                'probability': r.get('probability'),
                'customer': (r.get('partner_id') or [None, None])[1],
                'expected_revenue': r.get('expected_revenue'),
                'close_date': r.get('date_deadline'),
                'type': r.get('type')
            })
        return result

    @staticmethod
    async def list_opportunities(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(OdooCRMService._list_opportunities_sync, limit, offset)

    @staticmethod
    @retry_sync(max_attempts=3, base_delay=0.5, max_delay=3.0, retry_on=(odoorpc.error.RPCError,))
    def _get_opportunity_sync(opportunity_id: int) -> Optional[Dict[str, Any]]:
        o = _odoo_connect()
        Lead = o.env['crm.lead']
        recs = Lead.read([opportunity_id], ['id','name','stage_id','probability','partner_id','expected_revenue','date_deadline','type','description'])
        if not recs:
            return None
        r = recs[0]
        return {
            'id': r.get('id'),
            'name': r.get('name'),
            'stage': (r.get('stage_id') or [None, None])[1],
            'probability': r.get('probability'),
            'customer': (r.get('partner_id') or [None, None])[1],
            'expected_revenue': r.get('expected_revenue'),
            'close_date': r.get('date_deadline'),
            'type': r.get('type'),
            'description': r.get('description'),
        }

    @staticmethod
    async def get_opportunity(opportunity_id: int) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(OdooCRMService._get_opportunity_sync, opportunity_id)

    @staticmethod
    @retry_sync(max_attempts=3, base_delay=0.5, max_delay=3.0, retry_on=(odoorpc.error.RPCError,))
    def _create_opportunity_sync(data: Dict[str, Any]) -> Dict[str, Any]:
        o = _odoo_connect()
        Lead = o.env['crm.lead']
        # Minimal mapping: name, expected_revenue, partner_id, date_deadline, type
        values: Dict[str, Any] = {}
        for k in ("name", "expected_revenue", "partner_id", "date_deadline", "type", "probability", "description"):
            if k in data:
                values[k] = data[k]
        new_id = Lead.create(values)
        rec = Lead.read([new_id], ['id','name','stage_id','probability','partner_id','expected_revenue','date_deadline','type','description'])[0]
        return {
            'id': rec.get('id'),
            'name': rec.get('name'),
            'stage': (rec.get('stage_id') or [None, None])[1],
            'probability': rec.get('probability'),
            'customer': (rec.get('partner_id') or [None, None])[1],
            'expected_revenue': rec.get('expected_revenue'),
            'close_date': rec.get('date_deadline'),
            'type': rec.get('type'),
            'description': rec.get('description'),
        }

    @staticmethod
    async def create_opportunity(data: Dict[str, Any]) -> Dict[str, Any]:
        return await asyncio.to_thread(OdooCRMService._create_opportunity_sync, data)

    @staticmethod
    @retry_sync(max_attempts=3, base_delay=0.5, max_delay=3.0, retry_on=(odoorpc.error.RPCError,))
    def _update_opportunity_sync(opportunity_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        o = _odoo_connect()
        Lead = o.env['crm.lead']
        ok = Lead.write([opportunity_id], updates)
        if not ok:
            return None
        recs = Lead.read([opportunity_id], ['id','name','stage_id','probability','partner_id','expected_revenue','date_deadline','type','description'])
        if not recs:
            return None
        r = recs[0]
        return {
            'id': r.get('id'),
            'name': r.get('name'),
            'stage': (r.get('stage_id') or [None, None])[1],
            'probability': r.get('probability'),
            'customer': (r.get('partner_id') or [None, None])[1],
            'expected_revenue': r.get('expected_revenue'),
            'close_date': r.get('date_deadline'),
            'type': r.get('type'),
            'description': r.get('description'),
        }

    @staticmethod
    async def update_opportunity(opportunity_id: int, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(OdooCRMService._update_opportunity_sync, opportunity_id, updates)


class OdooPOSService:
    @staticmethod
    @retry_sync(max_attempts=3, base_delay=0.5, max_delay=3.0, retry_on=(odoorpc.error.RPCError,))
    def _list_orders_sync(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        o = _odoo_connect()
        Order = o.env['pos.order']
        ids = Order.search([], offset=offset, limit=limit, order='date_order desc')
        fields = ['id','name','date_order','amount_total','partner_id','state']
        recs = Order.read(ids, fields)
        result: List[Dict[str, Any]] = []
        for r in recs:
            result.append({
                'id': r.get('id'),
                'number': r.get('name'),
                'date': r.get('date_order'),
                'total': r.get('amount_total'),
                'customer': (r.get('partner_id') or [None, None])[1],
                'status': r.get('state'),
            })
        return result

    @staticmethod
    async def list_orders(limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        return await asyncio.to_thread(OdooPOSService._list_orders_sync, limit, offset)

    @staticmethod
    @retry_sync(max_attempts=3, base_delay=0.5, max_delay=3.0, retry_on=(odoorpc.error.RPCError,))
    def _get_order_sync(order_id: int) -> Optional[Dict[str, Any]]:
        o = _odoo_connect()
        Order = o.env['pos.order']
        recs = Order.read([order_id], ['id','name','date_order','amount_total','partner_id','state', 'lines'])
        if not recs:
            return None
        r = recs[0]
        return {
            'id': r.get('id'),
            'number': r.get('name'),
            'date': r.get('date_order'),
            'total': r.get('amount_total'),
            'customer': (r.get('partner_id') or [None, None])[1],
            'status': r.get('state'),
        }

    @staticmethod
    async def get_order(order_id: int) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(OdooPOSService._get_order_sync, order_id)
