import asyncio
import json
from unittest.mock import AsyncMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from app import scheduler
from app.config import settings
from app.routers.analytics import router
from app.services import sync_status


class MemoryRedis:
    def __init__(self):
        self.values = {}
        self.statuses = {}
        self.expirations = {}

    async def get(self, key):
        return self.values.get(key)

    async def set(self, key, value, *, nx=False, ex=None):
        if nx and key in self.values:
            return False
        self.values[key] = value
        self.expirations[key] = ex
        return True

    async def eval(self, script, key_count, status_key, queue_key, source, timestamp):
        status = sync_status.decode_status(self.statuses.get(source))
        if status.get('state') == 'running':
            return -1
        if queue_key in self.values:
            return 0
        self.values[queue_key] = 'queued'
        self.expirations[queue_key] = None
        status.update(state='queued', queued_at=timestamp)
        self.statuses[source] = json.dumps(status)
        return 1

    async def delete(self, key):
        self.values.pop(key, None)

    async def hget(self, key, name):
        return self.statuses.get(name)

    async def hset(self, key, name, value):
        self.statuses[name] = value

    async def hgetall(self, key):
        return self.statuses.copy()

    async def aclose(self):
        pass


@pytest.fixture
def redis(monkeypatch):
    instance = MemoryRedis()
    monkeypatch.setattr(sync_status.Redis, "from_url", lambda *a, **k: instance)
    monkeypatch.setitem(settings.__dict__, "sync_admin_token", "admin")
    return instance


@pytest.mark.asyncio
async def test_retry_auth_validation_and_deduplication(redis):
    app = FastAPI()
    app.include_router(router)
    app.state.redis = redis
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        for token in [None, "wrong"]:
            headers = {"X-Sync-Token": token} if token else {}
            assert (await client.post("/analytics/sync-retry", json={"source": "sync_games"}, headers=headers)).status_code == 403
        headers = {"X-Sync-Token": "admin"}
        assert (await client.post("/analytics/sync-retry", json={"source": "arbitrary"}, headers=headers)).status_code == 422
        response = await client.post("/analytics/sync-retry", json={"source": "sync_games"}, headers=headers)
        assert response.status_code == 202
        assert response.json() == {"queued": True}
        assert (await client.get("/analytics/sync-status")).json()["sync_games"]["state"] == "queued"
        assert (await client.post("/analytics/sync-retry", json={"source": "sync_games"}, headers=headers)).status_code == 409
        settings.sync_admin_token = ""
        assert (await client.post("/analytics/sync-retry", json={"source": "sync_players"}, headers=headers)).status_code == 403


@pytest.mark.asyncio
async def test_status_timing_preserves_success_and_has_no_error_text(redis):
    await sync_status.record_sync_status("sync_games", "running")
    await sync_status.record_sync_status("sync_games", "success", 4)
    first = json.loads(redis.statuses["sync_games"])
    assert first["started_at"] <= first["finished_at"]
    assert first["duration_seconds"] >= 0
    await sync_status.record_sync_status("sync_games", "queued")
    await sync_status.record_sync_status("sync_games", "running")
    await sync_status.record_sync_status("sync_games", "failed")
    failed = json.loads(redis.statuses["sync_games"])
    assert failed["last_success"] == first["last_success"]
    assert failed["count"] == 4
    assert failed["finished_at"] >= failed["started_at"]
    assert "error" not in failed


@pytest.mark.asyncio
async def test_retry_waits_while_scheduler_busy_then_runs_exact_source(redis, monkeypatch):
    lock = asyncio.Lock()
    monkeypatch.setattr(scheduler, "sync_lock", lock)
    calls = []
    async def execute(name, *steps):
        calls.extend(step.__name__ for step in steps)
        await redis.delete(sync_status.retry_key(steps[0].__name__))
        return True
    monkeypatch.setattr(scheduler, "run_steps", execute)
    await redis.set(sync_status.retry_key("sync_games"), "queued", ex=300)
    async with lock:
        await scheduler.sync_retries_job()
        assert await redis.get(sync_status.retry_key("sync_games"))
        assert calls == []
    await scheduler.sync_retries_job()
    assert calls == ["sync_games"]
    assert await redis.get(sync_status.retry_key("sync_games")) is None


@pytest.mark.asyncio
async def test_running_source_rejects_retry(redis):
    await sync_status.record_sync_status("sync_games", "running")
    app = FastAPI()
    app.include_router(router)
    app.state.redis = redis
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/analytics/sync-retry", json={"source": "sync_games"}, headers={"X-Sync-Token": "admin"})
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_scheduled_step_consumes_retry_and_records_failed_then_success(redis, monkeypatch):
    from contextlib import asynccontextmanager
    session = AsyncMock()
    @asynccontextmanager
    async def database():
        yield session
    monkeypatch.setattr(scheduler, "SessionLocal", database)
    monkeypatch.setattr(scheduler, "sync_lock", asyncio.Lock())
    async def sync_games(db):
        raise RuntimeError("credential=private")
    async def sync_players(db):
        return 8
    await redis.set(sync_status.retry_key("sync_games"), "queued", ex=300)
    await scheduler.run_steps("scheduled", sync_games, sync_players)
    assert await redis.get(sync_status.retry_key("sync_games")) is None
    failed = json.loads(redis.statuses["sync_games"])
    successful = json.loads(redis.statuses["sync_players"])
    assert failed["state"] == "failed"
    assert failed["duration_seconds"] >= 0
    assert "credential" not in redis.statuses["sync_games"]
    assert successful["state"] == "success"
    assert successful["count"] == 8


@pytest.mark.asyncio
async def test_public_status_removes_persisted_sensitive_fields(redis):
    redis.statuses["sync_games"] = json.dumps({"state": "failed", "error": "credential=private"})
    app = FastAPI()
    app.include_router(router)
    app.state.redis = redis
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/analytics/sync-status")
    assert response.json() == {"sync_games": {"state": "failed"}}


@pytest.mark.asyncio
async def test_expired_retry_is_not_reported_as_still_queued(redis):
    await sync_status.record_sync_status("sync_games", "queued")
    app = FastAPI()
    app.include_router(router)
    app.state.redis = redis
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        status = (await client.get("/analytics/sync-status")).json()
    assert status["sync_games"]["state"] == "failed"


@pytest.mark.asyncio
async def test_accepted_retry_does_not_expire_while_long_import_is_busy(redis):
    app = FastAPI()
    app.include_router(router)
    app.state.redis = redis
    async with AsyncClient(transport=ASGITransport(app), base_url='http://test') as client:
        result = await client.post('/analytics/sync-retry', json={'source':'sync_games'}, headers={'X-Sync-Token':'admin'})
    assert result.status_code == 202
    assert redis.expirations[sync_status.retry_key('sync_games')] is None


@pytest.mark.asyncio
@pytest.mark.parametrize('raw', ['[]','null','1','invalid', '{"started_at":"not-a-date"}'])
async def test_corrupt_status_does_not_block_recording_or_endpoints(redis, raw):
    redis.statuses['sync_games'] = raw
    await sync_status.record_sync_status('sync_games', 'failed')
    assert json.loads(redis.statuses['sync_games'])['state'] == 'failed'
    redis.statuses['sync_games'] = raw
    app = FastAPI()
    app.include_router(router)
    app.state.redis = redis
    async with AsyncClient(transport=ASGITransport(app), base_url='http://test') as client:
        response = await client.get('/analytics/sync-status')
        assert response.status_code == 200
        response = await client.post('/analytics/sync-retry', json={'source':'sync_games'}, headers={'X-Sync-Token':'admin'})
        assert response.status_code == 202


@pytest.mark.asyncio
async def test_retry_admission_checks_running_state_atomically(redis, monkeypatch):
    app = FastAPI()
    app.include_router(router)
    app.state.redis = redis
    # Record startup at the admission operation, after any prior status read.
    original_set = redis.set
    async def raced_set(*args, **kwargs):
        redis.statuses['sync_games'] = json.dumps({'state':'running'})
        return await original_set(*args, **kwargs)
    monkeypatch.setattr(redis, 'set', raced_set)
    async def admit(script, key_count, status_key, queue_key, source, timestamp):
        redis.statuses[source] = json.dumps({'state':'running'})
        return -1
    monkeypatch.setattr(redis, 'eval', admit, raising=False)
    async with AsyncClient(transport=ASGITransport(app), base_url='http://test') as client:
        response = await client.post('/analytics/sync-retry', json={'source':'sync_games'}, headers={'X-Sync-Token':'admin'})
    assert response.status_code == 409
    assert json.loads(redis.statuses['sync_games'])['state'] == 'running'
    assert await redis.get(sync_status.retry_key('sync_games')) is None
