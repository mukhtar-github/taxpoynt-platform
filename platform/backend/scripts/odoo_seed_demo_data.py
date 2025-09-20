"""
Odoo Demo Data Seeder
=====================
Seeds demo data into an existing Odoo database via OdooRPC:
- CRM: won opportunities (crm.lead)
- ERP: posted customer invoices (account.move)
- E‑commerce: confirmed online sales orders (sale.order)
- POS: paid orders (pos.order) — optional, requires an active session id

Reads connection from environment variables:
- ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_API_KEY | ODOO_PASSWORD
- Optional: ODOO_COMPANY_ID, ODOO_TIMEOUT, ODOO_VERIFY_SSL, ODOO_POS_SESSION_ID

Usage:
  pip install odoorpc
  export ODOO_URL=https://your-odoo
  export ODOO_DB=your_db
  export ODOO_USERNAME=api@yourco.com
  export ODOO_API_KEY=xxxxx
  python platform/backend/scripts/odoo_seed_demo_data.py --invoices 3 --crm 5 --ecom 3
"""
from __future__ import annotations

import os
import sys
import random
import argparse
from datetime import date

try:
    import odoorpc  # type: ignore
except Exception as e:
    print("Missing dependency: odoorpc. Install with: pip install odoorpc", file=sys.stderr)
    sys.exit(1)


def _get_env() -> dict:
    return {
        "url": os.getenv("ODOO_URL"),
        "db": os.getenv("ODOO_DB"),
        "username": os.getenv("ODOO_USERNAME"),
        "key": os.getenv("ODOO_API_KEY") or os.getenv("ODOO_PASSWORD"),
        "pos_session_id": os.getenv("ODOO_POS_SESSION_ID"),
    }


def connect(env: dict):
    if not (env["url"] and env["db"] and env["username"] and env["key"]):
        print("Incomplete Odoo connection env. Set ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_API_KEY|ODOO_PASSWORD", file=sys.stderr)
        sys.exit(2)
    # Basic heuristic for protocol/port
    protocol = "jsonrpc+ssl" if env["url"].startswith("https") else "jsonrpc"
    host = env["url"].split("://", 1)[-1].strip("/")
    odoo = odoorpc.ODOO(host, protocol=protocol)
    odoo.login(env["db"], env["username"], env["key"])
    return odoo


def ensure_partner(odoo) -> int:
    Partner = odoo.env['res.partner']
    ids = Partner.search([('is_company', '=', True)], limit=1) or Partner.search([], limit=1)
    if ids:
        return ids[0]
    # Create a simple partner
    return Partner.create({
        'name': 'Demo Company NG',
        'email': 'info@demo.ng',
        'phone': '+2348012345678',
        'company_type': 'company',
    })


def ensure_product(odoo) -> int:
    Product = odoo.env['product.product']
    ids = Product.search([], limit=1)
    if ids:
        return ids[0]
    return Product.create({
        'name': 'Demo Service',
        'list_price': 15000.0,
        'type': 'service',
    })


def seed_crm(odoo, count: int):
    if count <= 0:
        return 0
    try:
        Lead = odoo.env['crm.lead']
    except Exception:
        print("CRM module not available; skipping CRM seeding")
        return 0
    created = 0
    for i in range(count):
        try:
            Lead.create({
                'name': f'Demo Opportunity #{i+1}',
                'type': 'opportunity',
                'probability': 100,  # Closed Won
                'expected_revenue': random.choice([250000, 500000, 1250000]),
            })
            created += 1
        except Exception as e:
            print(f"CRM seed failed: {e}")
    print(f"CRM: created {created} won opportunities")
    return created


def seed_invoices(odoo, count: int):
    if count <= 0:
        return 0
    try:
        Invoice = odoo.env['account.move']
    except Exception:
        print("Accounting module not available; skipping invoice seeding")
        return 0
    partner_id = ensure_partner(odoo)
    product_id = ensure_product(odoo)
    created = 0
    for i in range(count):
        try:
            inv_id = Invoice.create({
                'move_type': 'out_invoice',
                'partner_id': partner_id,
                'invoice_date': date.today().isoformat(),
                'invoice_line_ids': [(0, 0, {
                    'product_id': product_id,
                    'quantity': random.randint(1, 5),
                    'price_unit': random.choice([5000.0, 15000.0, 25000.0]),
                })],
            })
            # post the invoice (draft → posted)
            Invoice.browse(inv_id).action_post()
            created += 1
        except Exception as e:
            print(f"Invoice seed failed: {e}")
    print(f"ERP: created and posted {created} customer invoices")
    return created


def seed_ecommerce_orders(odoo, count: int):
    if count <= 0:
        return 0
    try:
        Sale = odoo.env['sale.order']
    except Exception:
        print("Sales module not available; skipping e‑commerce seeding")
        return 0
    partner_id = ensure_partner(odoo)
    product_id = ensure_product(odoo)
    created = 0
    for i in range(count):
        try:
            so_id = Sale.create({
                'partner_id': partner_id,
                'website_id': 1,  # assumes default website id exists
                'order_line': [(0, 0, {
                    'product_id': product_id,
                    'product_uom_qty': random.randint(1, 3),
                    'price_unit': random.choice([12000.0, 18000.0, 22000.0]),
                })],
            })
            # confirm order
            Sale.action_confirm([so_id])
            created += 1
        except Exception as e:
            print(f"E‑commerce seed failed: {e}")
    print(f"E‑commerce: created {created} online orders (confirmed)")
    return created


def seed_pos_orders(odoo, count: int, session_id: str | None):
    if count <= 0:
        return 0
    if not session_id:
        print("POS session id not set (ODOO_POS_SESSION_ID); skipping POS seeding")
        return 0
    try:
        PosOrder = odoo.env['pos.order']
    except Exception:
        print("POS module not available; skipping POS seeding")
        return 0
    partner_id = ensure_partner(odoo)
    created = 0
    for i in range(count):
        try:
            order_id = PosOrder.create({
                'name': f'POS/000{random.randint(100,999)}',
                'partner_id': partner_id,
                'amount_total': random.choice([5000.0, 9000.0, 15000.0]),
                'amount_tax': 0.0,
                'state': 'paid',
                'session_id': int(session_id),
            })
            created += 1
        except Exception as e:
            print(f"POS seed failed: {e}")
    print(f"POS: created {created} paid orders")
    return created


def main():
    parser = argparse.ArgumentParser(description="Seed demo data into Odoo via OdooRPC")
    parser.add_argument("--crm", type=int, default=5, help="Number of CRM opportunities to create")
    parser.add_argument("--invoices", type=int, default=3, help="Number of posted invoices to create")
    parser.add_argument("--ecom", type=int, default=3, help="Number of e‑commerce orders to create")
    parser.add_argument("--pos", type=int, default=0, help="Number of POS orders to create (requires ODOO_POS_SESSION_ID)")
    args = parser.parse_args()

    env = _get_env()
    odoo = connect(env)

    total_crm = seed_crm(odoo, args.crm)
    total_inv = seed_invoices(odoo, args.invoices)
    total_ecom = seed_ecommerce_orders(odoo, args.ecom)
    total_pos = seed_pos_orders(odoo, args.pos, env.get("pos_session_id"))

    print("\nSummary:")
    print(f"  CRM: {total_crm}")
    print(f"  Invoices: {total_inv}")
    print(f"  E‑commerce: {total_ecom}")
    print(f"  POS: {total_pos}")


if __name__ == "__main__":
    main()

