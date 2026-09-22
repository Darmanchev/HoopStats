import asyncio
import argparse
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

async def full_sync(db):
    print("=== Syncing teams ===")
    await sync_teams(db)
    print("\n=== Syncing today's games ===")
    await sync_games(db)
    print("\n=== Syncing upcoming schedule ===")
    await sync_schedule(db)
    print("\n=== Syncing team stats ===")
    await sync_team_stats(db)
    print("\n=== Syncing historical games ===")
    await sync_historical_games(db)
    print("\n=== Syncing players ===")
    await sync_players(db)
    print("\n=== Syncing injuries ===")
    await sync_injuries(db)
    print("\n=== Predicting upcoming games ===")
    await sync_predictions(db)
    print("\nDone!")

async def partial_sync(db):
    print("Синхронизация команд...")
    await sync_teams(db)
    print("Загрузка исторических игр...")
    await sync_historical_games(db, season="2025-26")
    print("Синхронизация сегодняшних игр...")
    await sync_games(db)
    print("Синхронизация статистики команд...")
    await sync_team_stats(db)
    print("Готово!")

async def load_seasons_sync(db, seasons):
    for season in seasons:
        print(f"\n========== СЕЗОН {season} ==========")
        await sync_historical_games(db, season=season)
    print("\nВсе сезоны загружены.")

async def main():
    parser = argparse.ArgumentParser(description="Утилита синхронизации данных NBA")
    parser.add_argument("--sync", action="store_true", help="Выполнить частичную синхронизацию (teams, historical, today games, stats)")
    parser.add_argument("--seasons", nargs="+", help="Загрузить исторические данные для указанных сезонов (например, 2024-25 2023-24)")
    
    args = parser.parse_args()

    async with SessionLocal() as db:
        if args.seasons:
            await load_seasons_sync(db, args.seasons)
        elif args.sync:
            await partial_sync(db)
        else:
            await full_sync(db)

if __name__ == "__main__":
    asyncio.run(main())
