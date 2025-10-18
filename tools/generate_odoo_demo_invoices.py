#!/usr/bin/env python3
"""
Generate demo Odoo invoices via XML-RPC.

This helper creates posted customer invoices (move_type="out_invoice") in the
target Odoo instance using the same environment variables consumed by the
live_odoo_integration_test script:

Required env vars:
  - ODOO_HOST
  - ODOO_DATABASE
  - ODOO_USERNAME
  - ODOO_PASSWORD  (use the API key for SaaS)

Optional:
  - ODOO_PORT (defaults to 443)
  - ODOO_PROTOCOL ("jsonrpc+ssl" for https, anything else will use http)
"""
from __future__ import annotations

import argparse
import os
import random
import ssl
import sys
from datetime import date, timedelta
from typing import Any, Dict, List, Sequence
import xmlrpc.client


ProductLine = Dict[str, Any]


def _get_env(name: str, *, required: bool = True) -> str:
    value = os.getenv(name)
    if required and not value:
        raise SystemExit(f"Environment variable {name} is required.")
    return value or ""


def _build_server_proxies() -> Dict[str, Any]:
    host = _get_env("ODOO_HOST")
    db = _get_env("ODOO_DATABASE")
    username = _get_env("ODOO_USERNAME")
    password = _get_env("ODOO_PASSWORD")
    port = int(os.getenv("ODOO_PORT", "443"))
    protocol = os.getenv("ODOO_PROTOCOL", "jsonrpc+ssl")

    if protocol == "jsonrpc+ssl":
        base = f"https://{host}:{port}"
        context = ssl.create_default_context()
    else:
        base = f"http://{host}:{port}"
        context = None

    common = xmlrpc.client.ServerProxy(
        f"{base}/xmlrpc/2/common",
        context=context,
        allow_none=True,
    )
    models = xmlrpc.client.ServerProxy(
        f"{base}/xmlrpc/2/object",
        context=context,
        allow_none=True,
    )

    uid = common.authenticate(db, username, password, {})
    if not uid:
        raise SystemExit("Authentication failed; check ODOO_* credentials.")

    return {
        "db": db,
        "uid": uid,
        "password": password,
        "models": models,
    }


def _ensure_demo_partner(env: Dict[str, Any]) -> int:
    models = env["models"]
    db = env["db"]
    uid = env["uid"]
    password = env["password"]

    partner_ids = models.execute_kw(
        db,
        uid,
        password,
        "res.partner",
        "search",
        [[("name", "=", "Demo Customer")]],
        {"limit": 1},
    )
    if partner_ids:
        return partner_ids[0]

    partner_id = models.execute_kw(
        db,
        uid,
        password,
        "res.partner",
        "create",
        [
            {
                "name": "Demo Customer",
                "email": "demo.customer@example.com",
                "phone": "+2348000000000",
                "street": "123 Demo Road",
                "city": "Lagos",
                "country_id": _lookup_country(models, db, uid, password, "NG"),
            }
        ],
    )
    return partner_id


def _lookup_country(
    models: Any,
    db: str,
    uid: int,
    password: str,
    code: str,
) -> int | None:
    result = models.execute_kw(
        db,
        uid,
        password,
        "res.country",
        "search",
        [[("code", "=", code)]],
        {"limit": 1},
    )
    return result[0] if result else None


def _select_invoice_lines(seed_products: Sequence[ProductLine], count: int) -> List[ProductLine]:
    return random.sample(seed_products, k=count)


def _create_invoice(
    env: Dict[str, Any],
    partner_id: int,
    product_lines: Sequence[ProductLine],
    invoice_date: date,
    auto_post: bool,
) -> int:
    models = env["models"]
    db = env["db"]
    uid = env["uid"]
    password = env["password"]

    line_commands = [
        (
            0,
            0,
            {
                "name": line["description"],
                "quantity": line["quantity"],
                "price_unit": line["unit_price"],
                "tax_ids": [],
            },
        )
        for line in product_lines
    ]

    invoice_id = models.execute_kw(
        db,
        uid,
        password,
        "account.move",
        "create",
        [
            {
                "move_type": "out_invoice",
                "partner_id": partner_id,
                "invoice_date": invoice_date.isoformat(),
                "invoice_line_ids": line_commands,
            }
        ],
    )

    if auto_post:
        models.execute_kw(
            db,
            uid,
            password,
            "account.move",
            "action_post",
            [[invoice_id]],
        )

    return invoice_id


def generate_demo_invoices(
    count: int,
    *,
    auto_post: bool = True,
    max_lines: int = 3,
    seed: int | None = None,
) -> List[int]:
    if count <= 0:
        raise ValueError("count must be positive")
    if max_lines <= 0:
        raise ValueError("max_lines must be positive")

    rng = random.Random(seed)
    env = _build_server_proxies()
    partner_id = _ensure_demo_partner(env)

    product_catalog: List[ProductLine] = [
        {"description": "Consulting Services", "unit_price": 250000.0, "quantity": 1},
        {"description": "Implementation Support", "unit_price": 150000.0, "quantity": 1},
        {"description": "Training Session", "unit_price": 75000.0, "quantity": 1},
        {"description": "Platform Subscription", "unit_price": 55000.0, "quantity": 1},
        {"description": "Extended Warranty", "unit_price": 45000.0, "quantity": 1},
        {"description": "Integration Maintenance", "unit_price": 60000.0, "quantity": 1},
    ]

    invoice_ids: List[int] = []
    for idx in range(count):
        line_count = rng.randint(1, min(max_lines, len(product_catalog)))
        selected_lines = _select_invoice_lines(product_catalog, line_count)
        invoice_date = date.today() - timedelta(days=rng.randint(0, 14))
        invoice_id = _create_invoice(env, partner_id, selected_lines, invoice_date, auto_post=auto_post)
        invoice_ids.append(invoice_id)
        print(f"✅ Created invoice #{invoice_id} dated {invoice_date.isoformat()} with {line_count} lines.")

    return invoice_ids


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate demo invoices in Odoo.")
    parser.add_argument(
        "--count",
        type=int,
        default=5,
        help="Number of invoices to create (default: 5).",
    )
    parser.add_argument(
        "--draft",
        action="store_true",
        help="Leave invoices in draft instead of posting them.",
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=3,
        help="Maximum number of invoice lines per invoice (default: 3).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional random seed for repeatable results.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    try:
        invoice_ids = generate_demo_invoices(
            args.count,
            auto_post=not args.draft,
            max_lines=args.max_lines,
            seed=args.seed,
        )
    except Exception as exc:  # pragma: no cover - script usage
        print(f"❌ Failed to generate invoices: {exc}", file=sys.stderr)
        return 1

    status = "posted" if not args.draft else "draft"
    print(f"\n🎉 Generated {len(invoice_ids)} {status} invoice(s): {', '.join(map(str, invoice_ids))}")
    return 0


if __name__ == "__main__":  # pragma: no cover - script entry point
    sys.exit(main())

