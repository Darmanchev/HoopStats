from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.player import Player
from ..clients.types import PlayerProfileData


async def upsert_players(
    db: AsyncSession,
    profiles: list[PlayerProfileData],
) -> tuple[int, int]:
    """Upsert basic profiles while preserving official IDs and statistics."""
    count_new = 0
    count_updated = 0
    for profile in profiles:
        name = " ".join(profile["name"].split())
        result = await db.execute(
            select(Player).where(
                Player.balldontlie_id == profile["balldontlie_id"]
            )
        )
        player = result.scalar_one_or_none()
        if player is None:
            fallback = await db.execute(
                select(Player)
                .where(
                    Player.name == name,
                    Player.team_abbr == profile["team_abbr"],
                )
                .limit(2)
            )
            matches = fallback.scalars().all()
            player = matches[0] if len(matches) == 1 else None

        if player is None:
            db.add(Player(
                nba_id=None,
                balldontlie_id=profile["balldontlie_id"],
                name=name,
                team_abbr=profile["team_abbr"],
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
            ))
            count_new += 1
            continue

        player.balldontlie_id = profile["balldontlie_id"]
        player.name = name
        player.team_abbr = profile["team_abbr"]
        player.position = profile["position"]
        player.jersey_number = profile["jersey_number"]
        count_updated += 1

    return count_new, count_updated
