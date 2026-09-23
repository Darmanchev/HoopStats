import asyncio
import logging
import signal
from datetime import datetime, timedelta, timezone
from collections.abc import Awaitable, Callable

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import SessionLocal
from app.config import settings
from app.services import (
    sync_games,
    sync_historical_games,
    sync_injuries,
    sync_players,
    sync_predictions,
    sync_schedule,
    sync_team_stats,
    sync_teams,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler(timezone="UTC")
sync_lock = asyncio.Lock()

SyncStep = Callable[[AsyncSession], Awaitable[None]]


async def run_steps(name: str, *steps: SyncStep) -> None:
    if sync_lock.locked():
        logger.warning("Skipping %s sync because another sync is running", name)
        return

    async with sync_lock:
        logger.info("Starting %s sync", name)

        async with SessionLocal() as db:
            for step in steps:
                try:
                    await step(db)
                except Exception:
                    await db.rollback()
                    logger.exception(
                        "%s failed during %s",
                        name,
                        step.__name__,
                    )

        logger.info("Finished %s sync", name)


async def sync_live_job() -> None:
    await run_steps(
        "live games",
        sync_games,
    )


async def sync_schedule_job() -> None:
    await run_steps(
        "schedule and injuries",
        sync_schedule,
        sync_injuries,
    )


async def sync_statistics_job() -> None:
    await run_steps(
        "statistics",
        sync_teams,
        sync_players,
        sync_team_stats,
        sync_historical_games,
        sync_predictions,
    )


def configure_scheduler(
    target: AsyncIOScheduler,
    *,
    now: datetime | None = None,
) -> None:
    """Register staggered synchronization jobs on ``target``."""
    first_run = now or datetime.now(timezone.utc)

    target.add_job(
        sync_live_job,
        trigger=IntervalTrigger(minutes=settings.live_sync_minutes),
        id="live-games",
        next_run_time=first_run,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
        replace_existing=True,
    )

    target.add_job(
        sync_schedule_job,
        trigger=IntervalTrigger(days=1),
        id="schedule-and-injuries",
        next_run_time=first_run + timedelta(minutes=2),
        max_instances=1,
        coalesce=True,
        misfire_grace_time=1800,
        replace_existing=True,
    )

    target.add_job(
        sync_statistics_job,
        trigger=IntervalTrigger(days=1),
        id="statistics",
        next_run_time=first_run + timedelta(minutes=6),
        max_instances=1,
        coalesce=True,
        misfire_grace_time=3600,
        replace_existing=True,
    )


def start_scheduler() -> None:
    configure_scheduler(scheduler)
    scheduler.start()
    logger.info("Synchronization scheduler started")


def stop_scheduler() -> None:
    if scheduler.running:
        scheduler.shutdown()


async def main() -> None:
    """Run one scheduler process, independent from Uvicorn workers."""
    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stop_event.set)

    start_scheduler()
    try:
        await stop_event.wait()
    finally:
        stop_scheduler()


if __name__ == "__main__":
    asyncio.run(main())
