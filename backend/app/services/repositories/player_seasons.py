from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.player import Player
from app.models.player_season_stat import PlayerSeasonStat
from app.models.team import Team
from app.services.clients.types import (
    ApiNbaPlayerProfileData,
    ApiNbaTeamData,
    PlayerSeasonData,
)


def _normalized_name(name: str) -> str:
    return " ".join(name.split())


async def upsert_player_season(
    db: AsyncSession,
    *,
    season: str,
    teams: list[ApiNbaTeamData],
    profiles: list[ApiNbaPlayerProfileData],
    rows: list[PlayerSeasonData],
) -> tuple[int, int]:
    team_abbrs = {team["abbr"] for team in teams}
    team_ids = {team["api_nba_id"] for team in teams}
    if len(team_abbrs) != len(teams) or len(team_ids) != len(teams):
        raise ValueError("API-NBA teams must have unique IDs and abbreviations")

    profile_by_id: dict[int, ApiNbaPlayerProfileData] = {}
    for profile in profiles:
        player_id = profile["api_nba_id"]
        if player_id in profile_by_id:
            raise ValueError("API-NBA player profiles must have unique IDs")
        if not _normalized_name(profile["name"]):
            raise ValueError("API-NBA player profile name is required")
        profile_by_id[player_id] = profile

    row_by_id: dict[int, PlayerSeasonData] = {}
    for row in rows:
        if row["season"] != season:
            raise ValueError("player row season does not match requested season")
        if row["primary_team_abbr"] not in team_abbrs:
            raise ValueError("player row references an unknown team")
        player_id = row["api_nba_id"]
        if player_id not in profile_by_id:
            raise ValueError("player row has no matching profile")
        if player_id in row_by_id:
            raise ValueError("player season rows must have unique API-NBA IDs")
        row_by_id[player_id] = row
    if set(profile_by_id) != set(row_by_id):
        raise ValueError("every API-NBA player profile must have a season row")

    existing_teams = (
        await db.execute(select(Team).where(Team.abbr.in_(team_abbrs)))
    ).scalars().all()
    db_teams = {team.abbr: team for team in existing_teams}
    missing_teams = team_abbrs - db_teams.keys()
    if missing_teams:
        raise ValueError(f"API-NBA team mapping is missing local team: {sorted(missing_teams)[0]}")

    provider_ids = set(profile_by_id)
    existing_players = (
        await db.execute(select(Player).where(Player.api_nba_id.in_(provider_ids)))
    ).scalars().all()
    player_by_provider_id = {
        player.api_nba_id: player
        for player in existing_players
        if player.api_nba_id is not None
    }

    count_new = 0
    count_updated = 0
    mapped_players: dict[int, Player] = {}
    for provider_id, profile in profile_by_id.items():
        player = player_by_provider_id.get(provider_id)
        name = _normalized_name(profile["name"])
        if player is None:
            fallback = (
                await db.execute(
                    select(Player)
                    .where(Player.api_nba_id.is_(None), Player.name == name)
                    .limit(2)
                )
            ).scalars().all()
            player = fallback[0] if len(fallback) == 1 else None

        row = row_by_id[provider_id]
        if player is None:
            player = Player(
                nba_id=None,
                balldontlie_id=None,
                api_nba_id=provider_id,
                name=name,
                team_abbr=row["primary_team_abbr"],
                position=profile["position"],
                jersey_number=profile["jersey_number"],
                games_played=0,
                pts=0.0,
                reb=0.0,
                ast=0.0,
                stl=0.0,
                blk=0.0,
                fg_pct=0.0,
                fg3_pct=0.0,
                ft_pct=0.0,
                mins=0.0,
                recent_games=0,
            )
            db.add(player)
            count_new += 1
        else:
            player.api_nba_id = provider_id
            player.name = name
            player.team_abbr = row["primary_team_abbr"]
            player.position = profile["position"]
            player.jersey_number = profile["jersey_number"]
            count_updated += 1
        mapped_players[provider_id] = player

    for team_data in teams:
        db_teams[team_data["abbr"]].api_nba_id = team_data["api_nba_id"]

    await db.flush()
    await db.execute(
        delete(PlayerSeasonStat).where(PlayerSeasonStat.season == season)
    )
    for provider_id, row in row_by_id.items():
        db.add(PlayerSeasonStat(
            player_id=mapped_players[provider_id].id,
            season=season,
            primary_team_abbr=row["primary_team_abbr"],
            games_played=row["games_played"],
            pts=row["pts"],
            reb=row["reb"],
            ast=row["ast"],
            stl=row["stl"],
            blk=row["blk"],
            fg_pct=row["fg_pct"],
            fg3_pct=row["fg3_pct"],
            ft_pct=row["ft_pct"],
            mins=row["mins"],
            recent_games=row["recent_games"],
        ))

    return count_new, count_updated


async def list_player_seasons(db: AsyncSession) -> list[str]:
    result = await db.execute(
        select(PlayerSeasonStat.season)
        .distinct()
        .order_by(PlayerSeasonStat.season.desc())
    )
    return list(result.scalars().all())
