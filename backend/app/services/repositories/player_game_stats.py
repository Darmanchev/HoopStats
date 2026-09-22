from sqlalchemy import func
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ...models.player_game_stat import PlayerGameStat
from ..clients.types import LivePlayerStatData


async def upsert_player_game_stats(
    db: AsyncSession,
    game_id: str,
    rows: list[LivePlayerStatData],
) -> int:
    """Upsert normalized player rows for one game."""
    if not rows:
        return 0

    values = [{**row, "game_id": game_id} for row in rows]
    statement = insert(PlayerGameStat).values(values)
    excluded = statement.excluded
    statement = statement.on_conflict_do_update(
        index_elements=[PlayerGameStat.game_id, PlayerGameStat.nba_id],
        set_={
            "name": excluded.name,
            "team_abbr": excluded.team_abbr,
            "points": excluded.points,
            "rebounds": excluded.rebounds,
            "assists": excluded.assists,
            "steals": excluded.steals,
            "blocks": excluded.blocks,
            "minutes": excluded.minutes,
            "updated_at": func.now(),
        },
    )
    await db.execute(statement)
    return len(values)
