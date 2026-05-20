import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from app.database import SessionLocal
from app.services.nba_service import (
    sync_teams,
    sync_games,
    sync_team_stats,
    sync_injuries,
    sync_players,
)

scheduler = AsyncIOScheduler()

async def run_sync():
    """Запускает полную синхронизацию данных"""
    print(f"\n{'='*50}")
    print(f"ЗАПУСК АВТОМАТИЧЕСКОЙ СИНХРОНИЗАЦИИ: {asyncio.get_event_loop().time()}")
    print(f"{'='*50}\n")
    
    async with SessionLocal() as db:
        try:
            print("=== Syncing teams ===")
            await sync_teams(db)
            
            print("\n=== Syncing today's games ===")
            await sync_games(db)
            
            print("\n=== Syncing team stats ===")
            await sync_team_stats(db)
            
            print("\n=== Syncing players ===")
            await sync_players(db)
            
            print("\n=== Syncing injuries ===")
            await sync_injuries(db)
            
            print(f"\n{'='*50}")
            print("СИНХРОНИЗАЦИЯ ЗАВЕРШЕНА УСПЕШНО")
            print(f"{'='*50}\n")
        except Exception as e:
            print(f"\nОШИБКА СИНХРОНИЗАЦИИ: {type(e).__name__}: {e}\n")

def start_scheduler():
    """Запускает scheduler с интервалом 12 часов"""
    scheduler.add_job(
        run_sync,
        trigger=IntervalTrigger(hours=12),
        id="nba_sync",
        name="NBA Data Sync",
        replace_existing=True,
        max_instances=1,
    )
    scheduler.start()
    print("Scheduler запущен: синхронизация каждые 12 часов")

def stop_scheduler():
    """Останавливает scheduler"""
    scheduler.shutdown()
