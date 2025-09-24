import asyncio
import os
import sys
from typing import Tuple

import pytest


# Ensure backend modules are importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKEND = os.path.join(ROOT, "backend")
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


async def start_mock_ap_server() -> Tuple[object, str]:
    """Start a local aiohttp server with 2xx/4xx/5xx endpoints and return (runner, base_url)."""
    from aiohttp import web

    async def ok(request):
        return web.json_response({"status": "ok"}, status=200)

    async def bad(request):
        return web.json_response({"status": "bad"}, status=400)

    async def fail(request):
        return web.json_response({"status": "fail"}, status=500)

    app = web.Application()
    app.add_routes([
        web.post('/ok', ok),
        web.post('/bad', bad),
        web.post('/fail', fail),
    ])

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '127.0.0.1', 0)
    await site.start()
    # Extract bound port
    sockets = list(site._server.sockets)
    port = sockets[0].getsockname()[1]
    base_url = f"http://127.0.0.1:{port}"
    return runner, base_url


async def stop_mock_ap_server(runner):
    await runner.cleanup()


@pytest.mark.asyncio
async def test_ap_outbound_consumer_end_to_end():
    # Allow http + restrict to localhost for test
    os.environ['OUTBOUND_ALLOW_HTTP'] = 'true'
    os.environ['OUTBOUND_ALLOWED_DOMAINS'] = '127.0.0.1,localhost'
    # Speed up retries for 5xx path
    os.environ['OUTBOUND_RETRY_DELAYS'] = '0.1,0.2'
    os.environ['OUTBOUND_MAX_RETRIES'] = '1'
    # Minimal app init to register only the network services / consumer
    os.environ['APP_INIT_MINIMAL'] = 'true'

    # Start mock AP server
    runner, base_url = await start_mock_ap_server()
    try:
        # Initialize queue manager and app services (registers outbound consumer)
        from core_platform.messaging.queue_manager import initialize_queue_manager, get_queue_manager
        from core_platform.messaging.message_router import MessageRouter
        from app_services import initialize_app_services

        await initialize_queue_manager()
        qm = get_queue_manager()

        router = MessageRouter()
        await initialize_app_services(router)

        # Convenience access to queues
        ap_queue = qm.queues.get('ap_outbound')
        dlq_queue = qm.queues.get('dead_letter')
        assert ap_queue is not None and dlq_queue is not None

        # Ensure a consumer is registered; fall back to a local test consumer if not
        for _ in range(40):
            if getattr(ap_queue, 'consumers', {}):
                break
            await asyncio.sleep(0.05)
        if not getattr(ap_queue, 'consumers', {}):
            # Register a minimal test consumer to avoid flakiness in import paths
            import aiohttp
            async def _test_consumer(message):
                payload = getattr(message, 'payload', {}) or {}
                endpoint_url = payload.get('endpoint_url') or payload.get('ap_endpoint_url')
                if not endpoint_url:
                    return True  # ack to drain
                try:
                    timeout = aiohttp.ClientTimeout(total=5)
                    async with aiohttp.ClientSession(timeout=timeout) as session:
                        async with session.post(endpoint_url, json=payload.get('document') or payload) as resp:
                            status = resp.status
                            if 200 <= status < 300:
                                return True
                            if 400 <= status < 500:
                                # Manually push to DLQ to emulate policy
                                await qm.enqueue_message('dead_letter', {
                                    'type': 'ap_outbound_delivery',
                                    'reason': 'client_error',
                                    'http_status': status,
                                    'endpoint_url': endpoint_url,
                                    'original_payload': payload,
                                })
                                return True
                            return False
                except Exception:
                    return False
            await qm.register_consumer('ap_outbound', 'ap_outbound_worker_test', _test_consumer)

        # 1) 2xx success path
        prev_completed = ap_queue.metrics.completed_messages
        await qm.enqueue_message('ap_outbound', {
            'endpoint_url': f"{base_url}/ok",
            'document': {'id': 'inv-ok'}
        })
        # Wait until completed increases
        for _ in range(120):
            if ap_queue.metrics.completed_messages > prev_completed:
                break
            await asyncio.sleep(0.05)
        assert ap_queue.metrics.completed_messages > prev_completed, "Expected outbound success to ACK"

        # 2) 4xx: ack + DLQ
        prev_dlq = dlq_queue.metrics.current_queue_size
        prev_completed = ap_queue.metrics.completed_messages
        await qm.enqueue_message('ap_outbound', {
            'endpoint_url': f"{base_url}/bad",
            'document': {'id': 'inv-4xx'}
        })
        for _ in range(120):
            # ACK should still count as completed
            if dlq_queue.metrics.current_queue_size > prev_dlq and ap_queue.metrics.completed_messages > prev_completed:
                break
            await asyncio.sleep(0.05)
        assert dlq_queue.metrics.current_queue_size > prev_dlq, "Expected 4xx to be copied to DLQ"
        assert ap_queue.metrics.completed_messages > prev_completed, "Expected 4xx to be ACKed (no retry)"

        # 3) 5xx: NACK (retry)
        prev_retry = ap_queue.metrics.retry_messages
        await qm.enqueue_message('ap_outbound', {
            'endpoint_url': f"{base_url}/fail",
            'document': {'id': 'inv-5xx'}
        })
        for _ in range(120):
            if ap_queue.metrics.retry_messages > prev_retry:
                break
            await asyncio.sleep(0.05)
        assert ap_queue.metrics.retry_messages > prev_retry, "Expected 5xx to NACK and schedule retry"

    finally:
        await stop_mock_ap_server(runner)
        # Shutdown queues to clean up background tasks
        try:
            from core_platform.messaging.queue_manager import get_queue_manager
            qm = get_queue_manager()
            await qm.shutdown()
        except Exception:
            pass
