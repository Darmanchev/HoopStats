import asyncio
from datetime import datetime, timedelta, timezone

import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app import scheduler as scheduler_module


class FakeSession:
    def __init__(self) -> None:
        self.rollback_count = 0

    async def rollback(self) -> None:
        self.rollback_count += 1


class FakeSessionContext:
    def __init__(self, session: FakeSession) -> None:
        self.session = session

    async def __aenter__(self) -> FakeSession:
        return self.session

    async def __aexit__(self, *_args: object) -> None:
        return None


def test_configure_scheduler_registers_staggered_jobs() -> None:
    target = AsyncIOScheduler(timezone="UTC")
    now = datetime(2026, 1, 1, tzinfo=timezone.utc)

    scheduler_module.configure_scheduler(target, now=now)

    jobs = {job.id: job for job in target.get_jobs()}
    assert set(jobs) == {
        "live-games",
        "schedule-and-injuries",
        "statistics",
    }
    assert jobs["live-games"].func is scheduler_module.sync_live_job
    assert jobs["live-games"].trigger.interval == timedelta(minutes=15)
    assert jobs["live-games"].next_run_time == now
    assert jobs["schedule-and-injuries"].func is scheduler_module.sync_schedule_job
    assert jobs["schedule-and-injuries"].trigger.interval == timedelta(hours=6)
    assert jobs["schedule-and-injuries"].next_run_time == now + timedelta(minutes=2)
    assert jobs["statistics"].func is scheduler_module.sync_statistics_job
    assert jobs["statistics"].trigger.interval == timedelta(hours=12)
    assert jobs["statistics"].next_run_time == now + timedelta(minutes=5)


@pytest.mark.asyncio
async def test_statistics_sync_refreshes_history_before_predictions(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    expected_order = [
        "teams",
        "players",
        "team_stats",
        "historical_games",
        "predictions",
    ]
    session = FakeSession()

    def make_sync(name: str):
        async def sync(_db: object) -> None:
            calls.append(name)

        return sync

    monkeypatch.setattr(
        scheduler_module,
        "SessionLocal",
        lambda: FakeSessionContext(session),
    )
    monkeypatch.setattr(scheduler_module, "sync_lock", asyncio.Lock())
    for name in expected_order:
        monkeypatch.setattr(
            scheduler_module,
            f"sync_{name}",
            make_sync(name),
        )

    await scheduler_module.sync_statistics_job()

    assert calls == expected_order


@pytest.mark.asyncio
async def test_run_steps_rolls_back_failure_and_continues(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[str] = []
    session = FakeSession()

    async def failing_step(_db: object) -> None:
        calls.append("failing")
        raise RuntimeError("external API unavailable")

    async def successful_step(_db: object) -> None:
        calls.append("successful")

    monkeypatch.setattr(
        scheduler_module,
        "SessionLocal",
        lambda: FakeSessionContext(session),
    )
    monkeypatch.setattr(scheduler_module, "sync_lock", asyncio.Lock())

    await scheduler_module.run_steps(
        "test",
        failing_step,
        successful_step,
    )

    assert calls == ["failing", "successful"]
    assert session.rollback_count == 1


@pytest.mark.asyncio
async def test_run_steps_skips_when_another_sync_is_running(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    called = False
    lock = asyncio.Lock()

    async def step(_db: object) -> None:
        nonlocal called
        called = True

    monkeypatch.setattr(scheduler_module, "sync_lock", lock)

    async with lock:
        await scheduler_module.run_steps("test", step)

    assert called is False
