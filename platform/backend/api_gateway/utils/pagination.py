"""
Pagination Utilities
====================

Helpers to normalize limit/offset pagination into a consistent metadata shape
used across endpoints.
"""
from __future__ import annotations

from typing import Dict
import math


def normalize_pagination(limit: int, offset: int, total: int) -> Dict[str, int | bool]:
    """Return a normalized pagination metadata object.

    Fields:
    - limit: page size
    - offset: starting offset
    - total: total items
    - page: 1-based current page (derived from limit/offset)
    - pages: total pages (ceil(total/limit), >= 1 when total>0)
    - has_next: True if more items ahead
    - has_prev: True if there are items behind
    """
    l = max(1, int(limit))
    o = max(0, int(offset))
    t = max(0, int(total))

    page = (o // l) + 1 if t > 0 else 1
    pages = math.ceil(t / l) if l > 0 else 1
    has_next = (o + l) < t
    has_prev = o > 0

    return {
        "limit": l,
        "offset": o,
        "total": t,
        "page": page,
        "pages": pages if pages > 0 else 1,
        "has_next": has_next,
        "has_prev": has_prev,
    }


__all__ = ["normalize_pagination"]

