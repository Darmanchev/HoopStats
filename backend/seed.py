import asyncio
from app.database import SessionLocal
from app.services.nba_service import (
    sync_teams,
    sync_games,
    sync_team_stats,
    sync_historical_games,
    sync_injuries,
    sync_players,
)


async def main():
    async with SessionLocal() as db:
        print("=== Syncing teams ===")
        await sync_teams(db)

        print("\n=== Syncing today's games ===")
        await sync_games(db)

        print("\n=== Syncing team stats ===")
        await sync_team_stats(db)

        print("\n=== Syncing historical games ===")
        await sync_historical_games(db)

        print("\n=== Syncing players ===")
        await sync_players(db)

        print("\n=== Syncing injuries ===")
        await sync_injuries(db)

        print("\nDone!")


asyncio.run(main())
