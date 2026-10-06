"""Exercise Redis Lua admission against real Redis in CI."""
import json
import os
from datetime import datetime, timezone
from uuid import uuid4

import pytest
from redis.asyncio import Redis

from app.services.sync_status import ENQUEUE_RETRY


@pytest.mark.asyncio
@pytest.mark.skipif(not os.environ.get('REDIS_TEST_URL'), reason='Redis integration service not configured')
async def test_real_redis_admission_is_atomic_and_pending_retry_has_no_expiry():
    redis = Redis.from_url(os.environ['REDIS_TEST_URL'], decode_responses=True)
    prefix = f'test:retry:{uuid4().hex}'
    status_key, queue_key = prefix + ':status', prefix + ':queue'
    source = 'sync_games'
    timestamp = datetime.now(timezone.utc).isoformat()
    async def admit():
        return await redis.eval(ENQUEUE_RETRY, 2, status_key, queue_key, source, timestamp)
    try:
        for malformed in ('[]', 'null', '1', 'invalid'):
            await redis.hset(status_key, source, malformed)
            assert await admit() == 1
            assert await redis.ttl(queue_key) == -1
            assert json.loads(await redis.hget(status_key, source))['state'] == 'queued'
            assert await admit() == 0
            await redis.delete(queue_key)
        await redis.hset(status_key, source, json.dumps({'state':'running'}))
        assert await admit() == -1
        assert await redis.get(queue_key) is None
        assert json.loads(await redis.hget(status_key, source))['state'] == 'running'
    finally:
        await redis.delete(status_key, queue_key)
        await redis.aclose()
