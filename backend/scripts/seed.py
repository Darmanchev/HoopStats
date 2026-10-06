import asyncio
import argparse
from functools import partial
from app.database import SessionLocal
from app.services import (
    sync_teams,
    sync_games,
    sync_schedule,
    sync_team_stats,
    sync_historical_games,
    sync_injuries,
    sync_players,
    sync_predictions,
)
from app.config import settings
from app.services.live_box_scores import sync_box_scores
from app.services.sync_status import record_sync_status

async def full_sync(db):
    return await run_import_steps(db, [
        ("sync_teams", sync_teams), ("sync_games", sync_games),
        ("sync_box_scores", sync_box_scores), ("sync_schedule", sync_schedule),
        ("sync_historical_games", sync_historical_games),
        ("sync_team_stats", sync_team_stats), ("sync_players", sync_players),
        ("sync_injuries", sync_injuries), ("sync_predictions", sync_predictions),
    ])


async def run_import_steps(db, steps):
    failed = 0
    for name, step in steps:
        print(f"=== {name} ===", flush=True)
        await record_sync_status(name, "running")
        try:
            count = await step(db)
        except Exception as exc:
            await db.rollback()
            failed += 1
            await record_sync_status(name, "failed")
            print(f"FAILED: {name}: {type(exc).__name__}: {exc}", flush=True)
        else:
            await record_sync_status(name, "success", count)
            print(f"OK: {name}" + (f" — {count} records" if count is not None else ""), flush=True)
    print(f"Import finished: {len(steps) - failed} succeeded, {failed} failed.", flush=True)
    return 1 if failed else 0

async def partial_sync(db):
    return await run_import_steps(db, [
        ("sync_teams", sync_teams),
        ("sync_historical_games", partial(sync_historical_games, season=settings.current_season)),
        ("sync_games", sync_games), ("sync_box_scores", sync_box_scores),
        ("sync_team_stats", sync_team_stats),
    ])

async def load_seasons_sync(db, seasons):
    return await run_import_steps(db, [
        (f"historical:{season}", partial(sync_historical_games, season=season))
        for season in seasons
    ])

async def main():
    parser = argparse.ArgumentParser(description="Утилита синхронизации данных NBA")
    parser.add_argument("--sync", action="store_true", help="Выполнить частичную синхронизацию (teams, historical, today games, stats)")
    parser.add_argument("--seasons", nargs="+", help="Загрузить исторические данные для указанных сезонов (например, 2024-25 2023-24)")
    
    args = parser.parse_args()

    async with SessionLocal() as db:
        if args.seasons:
            return await load_seasons_sync(db, args.seasons)
        elif args.sync:
            return await partial_sync(db)
        else:
            return await full_sync(db)

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
