import argparse
import asyncio

from app.database import SessionLocal
from app.services.clients.api_nba import ApiNbaError
from app.services.clients.api_nba_normalizers import season_start_year
from app.services.player_seasons import sync_player_season
from app.services.sync_status import record_sync_status


def season_argument(value: str) -> str:
    try:
        season_start_year(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    return value


async def main(season: str) -> None:
    status_name = f"player_season:{season}"
    await record_sync_status(status_name, "running")
    try:
        async with SessionLocal() as db:
            players, updated = await sync_player_season(db, season)
    except Exception:
        await record_sync_status(status_name, "failed")
        raise
    await record_sync_status(status_name, "success", players + updated)
    print(
        f"Imported {players} new players and updated {updated} players "
        f"for {season}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Import one NBA player season from API-NBA",
    )
    parser.add_argument(
        "--season",
        required=True,
        type=season_argument,
        help="NBA season in YYYY-YY format, for example 2025-26",
    )
    return parser.parse_args()


if __name__ == "__main__":
    arguments = parse_args()
    try:
        asyncio.run(main(arguments.season))
    except (ApiNbaError, ValueError) as exc:
        raise SystemExit(f"Player season import failed: {exc}") from exc
