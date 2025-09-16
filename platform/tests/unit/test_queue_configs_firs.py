"""
Unit test: verify dedicated FIRS submission queues and retry policy registry.
"""
import os
import sys
import asyncio


def test_firs_queues_and_retry_policies():
    # Ensure backend path
    CURRENT_DIR = os.path.dirname(__file__)
    BACKEND_DIR = os.path.abspath(os.path.join(CURRENT_DIR, "..", "..", "backend"))
    if BACKEND_DIR not in sys.path:
        sys.path.insert(0, BACKEND_DIR)

    from core_platform.messaging.queue_manager import initialize_queue_manager, get_queue_manager

    async def _init():
        qm = await initialize_queue_manager()
        return qm

    qm = asyncio.get_event_loop().run_until_complete(_init())
    try:
        # Queues exist
        assert "firs_submissions_high" in qm.queues
        assert "firs_submissions_retry" in qm.queues

        high_q = qm.queues["firs_submissions_high"]
        retry_q = qm.queues["firs_submissions_retry"]

        # Basic config checks
        assert high_q.config.max_workers >= 8
        assert high_q.config.max_retries >= 5
        assert isinstance(high_q.config.retry_delays, list) and len(high_q.config.retry_delays) >= 3

        assert retry_q.config.max_workers >= 2
        assert retry_q.config.max_retries >= 5

        # Retry policy registry hook: update and verify application
        qm.register_retry_policy("firs_submissions_high", max_retries=7, retry_delays=[1.0, 2.0, 5.0])
        assert high_q.config.max_retries == 7
        assert high_q.config.retry_delays == [1.0, 2.0, 5.0]
    finally:
        # Cleanup loop tasks if needed
        loop = asyncio.get_event_loop()
        loop.run_until_complete(qm.shutdown())

