"""
Async Retry Utilities for SI Services
====================================
Lightweight exponential backoff with jitter for transient failures.
"""
from __future__ import annotations

import asyncio
import random
from typing import Any, Callable, Iterable, Optional, Type


def retry_async(
    *,
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 5.0,
    retry_on: Optional[Iterable[Type[BaseException]]] = None,
):
    retry_set = tuple(retry_on or (TimeoutError, ConnectionError))

    def decorator(fn: Callable[..., Any]):
        async def wrapper(*args, **kwargs):
            attempt = 0
            delay = base_delay
            while True:
                try:
                    return await fn(*args, **kwargs)
                except retry_set as e:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    # Exponential backoff with jitter
                    sleep_for = min(max_delay, delay * (2 ** (attempt - 1)))
                    sleep_for = sleep_for * (0.5 + random.random() / 2)
                    await asyncio.sleep(sleep_for)
                except Exception:
                    # Do not retry on unexpected exceptions
                    raise
        return wrapper
    return decorator


def retry_sync(
    *,
    max_attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 5.0,
    retry_on: Optional[Iterable[Type[BaseException]]] = None,
):
    retry_set = tuple(retry_on or (TimeoutError, ConnectionError))

    def decorator(fn: Callable[..., Any]):
        def wrapper(*args, **kwargs):
            import time
            attempt = 0
            while True:
                try:
                    return fn(*args, **kwargs)
                except retry_set:
                    attempt += 1
                    if attempt >= max_attempts:
                        raise
                    sleep_for = min(max_delay, base_delay * (2 ** (attempt - 1)))
                    sleep_for = sleep_for * (0.5 + random.random() / 2)
                    time.sleep(sleep_for)
                except Exception:
                    raise
        return wrapper
    return decorator
