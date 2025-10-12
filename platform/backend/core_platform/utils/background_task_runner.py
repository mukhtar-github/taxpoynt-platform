"""
Lightweight background task runner.

This runner provides a simple wrapper around ``asyncio.create_task`` with retry
and backoff support. It is intended as an interim solution until the Phase-6
job orchestration layer (Celery/RQ/Cloud Tasks) is available.

To migrate to the heavier runner:
1. Replace the ``BackgroundTaskRunner`` instance wiring in ``platform/backend/main.py``
   with the orchestration client (e.g., Celery app).
2. Update services that call ``configure_task_runner`` to pass the new client.
3. Swap usages of ``submit`` with the queue's enqueue method while keeping the
   payload contract identical (operation name + metadata).
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict, Optional, Set

AsyncFunc = Callable[..., Awaitable[Any]]


class BackgroundTaskRunner:
    """Manage best-effort background tasks with retry/backoff semantics."""

    def __init__(
        self,
        *,
        name: str = "background_runner",
        max_concurrency: Optional[int] = None,
        loop: Optional[asyncio.AbstractEventLoop] = None,
    ) -> None:
        self._loop = loop or asyncio.get_event_loop()
        self._logger = logging.getLogger(f"{__name__}.{name}")
        self._semaphore = (
            asyncio.Semaphore(max_concurrency) if max_concurrency else None
        )
        self._tasks: Set[asyncio.Task[Any]] = set()
        self._shutdown = False
        self.name = name

    def submit(
        self,
        async_fn: AsyncFunc,
        *args: Any,
        description: str = "background-task",
        retries: int = 2,
        backoff_base: float = 0.5,
        backoff_factor: float = 2.0,
        max_backoff: float = 10.0,
        **kwargs: Any,
    ) -> asyncio.Task[Any]:
        """
        Schedule an async function to run in the background.

        Args:
            async_fn: Awaitable function to execute.
            *args: Positional arguments passed to ``async_fn``.
            description: Friendly name for logging/observability.
            retries: Number of retry attempts after the initial try.
            backoff_base: Initial delay between retries (seconds).
            backoff_factor: Exponential multiplier applied per retry.
            max_backoff: Maximum delay between attempts (seconds).
            **kwargs: Keyword arguments passed to ``async_fn``.
        """
        if self._shutdown:
            raise RuntimeError("BackgroundTaskRunner is shutting down.")

        task = self._loop.create_task(
            self._run_with_backoff(
                async_fn,
                args,
                kwargs,
                description,
                retries,
                backoff_base,
                backoff_factor,
                max_backoff,
            )
        )
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    async def shutdown(self, *, cancel: bool = True) -> None:
        """Stop accepting new tasks and optionally cancel outstanding work."""
        self._shutdown = True
        if not self._tasks:
            return

        tasks = list(self._tasks)
        if cancel:
            for task in tasks:
                task.cancel()

        await asyncio.gather(*tasks, return_exceptions=True)
        self._tasks.clear()

    def pending_count(self) -> int:
        """Return the number of tracked background tasks."""
        return len(self._tasks)

    async def _run_with_backoff(
        self,
        async_fn: AsyncFunc,
        args: tuple[Any, ...],
        kwargs: Dict[str, Any],
        description: str,
        retries: int,
        backoff_base: float,
        backoff_factor: float,
        max_backoff: float,
    ) -> Any:
        attempts = 0
        delay = max(backoff_base, 0)

        while True:
            try:
                if self._semaphore:
                    async with self._semaphore:
                        return await async_fn(*args, **kwargs)
                return await async_fn(*args, **kwargs)
            except asyncio.CancelledError:
                self._logger.debug("Background task %s was cancelled", description)
                raise
            except Exception as exc:  # pragma: no cover - defensive logging
                if attempts >= retries:
                    self._logger.error(
                        "Background task %s failed after %s attempts: %s",
                        description,
                        attempts + 1,
                        exc,
                        exc_info=True,
                    )
                    raise

                attempts += 1
                sleep_for = min(delay or 0, max_backoff)
                if sleep_for > 0:
                    self._logger.warning(
                        "Background task %s failed (attempt %s/%s): %s. Retrying in %.2fs",
                        description,
                        attempts,
                        retries + 1,
                        exc,
                        sleep_for,
                    )
                    await asyncio.sleep(sleep_for)
                else:
                    self._logger.warning(
                        "Background task %s failed (attempt %s/%s): %s. Retrying immediately.",
                        description,
                        attempts,
                        retries + 1,
                        exc,
                    )

                delay = delay * backoff_factor if delay else backoff_base or 0
                if delay > max_backoff:
                    delay = max_backoff
