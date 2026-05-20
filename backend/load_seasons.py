"""Разовая загрузка прошлых сезонов из NBA API.

sync_historical_games пропускает уже существующие игры, поэтому скрипт
безопасно перезапускать. Запуск:

    docker compose exec backend python load_seasons.py
"""
import asyncio

from app.database import SessionLocal
from app.services.nba_service import sync_historical_games

# 2025-26 уже загружен; догружаем два предыдущих сезона
SEASONS = ["2024-25", "2023-24"]


async def main():
    for season in SEASONS:
        print(f"\n========== СЕЗОН {season} ==========")
        async with SessionLocal() as db:
            await sync_historical_games(db, season=season)
    print("\nВсе сезоны загружены.")


if __name__ == "__main__":
    asyncio.run(main())
