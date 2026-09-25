from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.team import Team
from app.services.clients.api_nba import ApiNbaClient, create_client
from app.services.clients.api_nba_normalizers import (
    aggregate_player_season,
    normalize_api_nba_teams,
    season_start_year,
)
from app.services.repositories import player_seasons as player_seasons_repo


def create_api_nba_client() -> ApiNbaClient:
    return create_client()


async def sync_player_season(
    db: AsyncSession,
    season: str,
) -> tuple[int, int]:
    start_year = season_start_year(season)
    try:
        valid_abbrs = set(
            (await db.execute(select(Team.abbr))).scalars().all()
        )
        async with create_api_nba_client() as client:
            teams = normalize_api_nba_teams(
                await client.get_teams(),
                valid_abbrs,
            )
            if len(teams) != 30:
                raise ValueError(f"Expected 30 NBA teams, received {len(teams)}")

            roster_pages: dict[int, list[dict[str, Any]]] = {}
            stat_pages: dict[int, list[dict[str, Any]]] = {}
            for team in teams:
                team_id = team["api_nba_id"]
                roster_pages[team_id] = await client.get_players(
                    team_id=team_id,
                    season=start_year,
                )
                stat_pages[team_id] = await client.get_player_statistics(
                    team_id=team_id,
                    season=start_year,
                )

        profiles, rows = aggregate_player_season(
            season,
            {team["api_nba_id"]: team["abbr"] for team in teams},
            roster_pages,
            stat_pages,
        )
        result = await player_seasons_repo.upsert_player_season(
            db,
            season=season,
            teams=teams,
            profiles=profiles,
            rows=rows,
        )
        await db.commit()
        return result
    except Exception:
        await db.rollback()
        raise
