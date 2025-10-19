#!/usr/bin/env python3
"""
Utility script to purge System Integrator per-minute rate-limit buckets from Redis.

This is intended for maintenance or emergency clean-up when a runaway client has
filled the limiter with stale keys. It connects using the REDIS_URL environment
variable, scans for the dynamic SI limiter namespace, and deletes any matches.
"""

import os
import sys
from typing import Optional

import redis


RATE_LIMIT_PATTERN = "taxpoynt:rate_limit:dynamic_v1_system_integrator_per_minute:*"
SCAN_BATCH_SIZE = 500


def get_redis_client(url: Optional[str] = None) -> redis.Redis:
    """Create a Redis client using REDIS_URL or the provided URL."""
    redis_url = url or os.environ.get("REDIS_URL")
    if not redis_url:
        raise RuntimeError("REDIS_URL environment variable is required")

    return redis.from_url(redis_url, decode_responses=True)


def purge_si_rate_limits(client: redis.Redis, pattern: str = RATE_LIMIT_PATTERN) -> int:
    """Scan for rate-limit keys matching pattern and delete them."""
    cursor = 0
    deleted = 0

    while True:
        cursor, keys = client.scan(cursor=cursor, match=pattern, count=SCAN_BATCH_SIZE)
        if keys:
            deleted += client.delete(*keys)

        if cursor == 0:
            break

    return deleted


def main() -> int:
    try:
        client = get_redis_client()
    except Exception as exc:
        print(f"Failed to connect to Redis: {exc}", file=sys.stderr)
        return 1

    deleted = purge_si_rate_limits(client)
    print(f"Deleted {deleted} SI rate-limit keys matching '{RATE_LIMIT_PATTERN}'")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
