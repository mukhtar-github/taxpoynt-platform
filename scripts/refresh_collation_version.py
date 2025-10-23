#!/usr/bin/env python3
from __future__ import annotations

"""
Utility script to refresh the PostgreSQL collation version for the active database.

Railway upgrades occasionally bump the system collation version which causes PostgreSQL
to emit warnings like:

  WARNING:  database "railway" has a collation version mismatch
  DETAIL:   The database was created using collation version 2.36, but the operating system provides version 2.41.

Run this script from the repository root once you have the correct DATABASE_URL exported:

  $ export DATABASE_URL=postgresql://user:pass@host:port/railway
  $ python scripts/refresh_collation_version.py

Use the --reindex flag to reindex the entire database after the refresh (recommended for large
table sets during maintenance windows only).
"""

import argparse
import os
import sys
from typing import Optional

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import connection as PGConnection


def _connect(url: str, autocommit: bool = True) -> PGConnection:
    conn = psycopg2.connect(url)
    conn.autocommit = autocommit
    return conn


def _get_database_name(conn: PGConnection) -> str:
    with conn.cursor() as cur:
        cur.execute("SELECT current_database()")
        row = cur.fetchone()
        if not row or not row[0]:
            raise RuntimeError("Unable to determine current database name")
        return row[0]


def _get_collation_versions(conn: PGConnection) -> Optional[tuple[str, Optional[str], Optional[str]]]:
    query = """
    SELECT datcollate, datctype, datcollversion
    FROM pg_database
    WHERE datname = current_database()
    """
    with conn.cursor() as cur:
        cur.execute(query)
        row = cur.fetchone()
        if not row:
            return None
        datcollate, datctype, datcollversion = row

    # datcollversion is only populated on PostgreSQL 13+
    actual_query = """
    SELECT pg_collation_actual_version(c.oid)
    FROM pg_collation c
    WHERE c.collname = %s
      AND c.collctype = %s
    LIMIT 1
    """
    actual_version: Optional[str] = None
    with conn.cursor() as cur:
        cur.execute(actual_query, (datcollate, datctype))
        result = cur.fetchone()
        if result:
            actual_version = result[0]

    return datcollate, datcollversion, actual_version


def refresh_collation(conn: PGConnection, db_name: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            sql.SQL("ALTER DATABASE {} REFRESH COLLATION VERSION").format(sql.Identifier(db_name))
        )


def reindex_database(conn: PGConnection, db_name: str) -> None:
    with conn.cursor() as cur:
        cur.execute(sql.SQL("REINDEX DATABASE {}").format(sql.Identifier(db_name)))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh PostgreSQL collation version.")
    parser.add_argument(
        "--database-url",
        dest="database_url",
        default=os.getenv("DATABASE_URL"),
        help="Connection string for the target database (defaults to $DATABASE_URL).",
    )
    parser.add_argument(
        "--reindex",
        dest="reindex",
        action="store_true",
        help="Rebuild indexes after refreshing the collation version (requires downtime).",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.database_url:
        print("DATABASE_URL is not set and --database-url was not provided.", file=sys.stderr)
        return 1

    print("Connecting to database...")
    conn = _connect(args.database_url)
    try:
        db_name = _get_database_name(conn)
        print(f"Connected to database: {db_name}")

        versions = _get_collation_versions(conn)
        if versions:
            datcollate, stored_version, actual_version = versions
            print(
                f"Current collation: {datcollate} "
                f"(stored version: {stored_version or 'unknown'}, "
                f"actual version: {actual_version or 'unknown'})"
            )
        else:
            print("Warning: Unable to determine current collation metadata.")

        print("Refreshing collation version...")
        refresh_collation(conn, db_name)
        print("Collation version refreshed successfully.")

        if args.reindex:
            print("Reindex requested. This may take a while...")
            reindex_database(conn, db_name)
            print("Reindex completed.")
        else:
            print("Skipping reindex (use --reindex to enable).")

        print("All done.")
        return 0
    finally:
        conn.close()


if __name__ == "__main__":
    sys.exit(main())
