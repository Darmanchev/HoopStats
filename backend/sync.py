import asyncio
from app.database import SessionLocal
from app.services.nba_service import sync_teams, sync_games, sync_team_stats, sync_historical_games

async def main():
    async with SessionLocal() as db:
        print("Синхронизация команд...")
        await sync_teams(db)
        print("Загрузка исторических игр...")
        await sync_historical_games(db, season="2025-26")
        print("Синхронизация сегодняшних игр...")
        await sync_games(db)
        print("Синхронизация статистики команд...")
        await sync_team_stats(db)
        print("Готово!")

asyncio.run(main())