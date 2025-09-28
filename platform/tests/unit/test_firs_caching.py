import asyncio
from types import SimpleNamespace

import pytest

from app_services.firs_communication.firs_api_client import (
    FIRSAPIClient,
    FIRSConfig,
    FIRSResponse,
)
from app_services.firs_communication.party_cache import PartyCache, TINCache


@pytest.mark.asyncio
async def test_party_cache_reuses_response_and_triggers_refresh():
    config = FIRSConfig()
    cache = PartyCache(ttl_minutes=0.0005)  # roughly 0.03 seconds
    client = FIRSAPIClient(config, party_cache=cache)

    call_count = {'count': 0}

    async def fake_make_request(self, endpoint, method="GET", data=None, params=None, headers=None, timeout=None, retry_on_auth_failure=True):
        call_count['count'] += 1
        return FIRSResponse(
            status_code=200,
            headers={},
            data={'partyId': 'P123', 'name': 'Test Party'},
            raw_response='{}',
            success=True,
        )

    client.make_request = fake_make_request.__get__(client, FIRSAPIClient)

    # First call hits FIRS
    response1 = await client.get_party('P123')
    assert response1.success
    assert call_count['count'] == 1

    # Second call served from cache
    response2 = await client.get_party('P123')
    assert response2 is response1
    assert call_count['count'] == 1

    # Allow entry to expire
    await asyncio.sleep(0.05)

    # Third call should return stale value immediately and schedule background refresh
    response3 = await client.get_party('P123')
    assert response3 is response1
    await asyncio.sleep(0.05)
    assert call_count['count'] >= 2

    await client.stop()


@pytest.mark.asyncio
async def test_tin_cache_reuses_verification():
    config = FIRSConfig()
    tin_cache = TINCache(ttl_minutes=0.0005)
    client = FIRSAPIClient(config, tin_cache=tin_cache)

    call_count = {'count': 0}

    async def fake_make_request(self, endpoint, method="POST", data=None, params=None, headers=None, timeout=None, retry_on_auth_failure=True):
        call_count['count'] += 1
        return FIRSResponse(
            status_code=200,
            headers={},
            data={'tin': data.get('tin'), 'valid': True},
            raw_response='{}',
            success=True,
        )

    client.make_request = fake_make_request.__get__(client, FIRSAPIClient)

    payload = {'tin': '12345678-0001'}

    await client.verify_tin(payload)
    assert call_count['count'] == 1

    await client.verify_tin(payload)
    assert call_count['count'] == 1  # cached

    await asyncio.sleep(0.05)
    await client.verify_tin(payload)
    await asyncio.sleep(0.05)
    assert call_count['count'] >= 2

    await client.stop()
