import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ...models.player import Player

logger = logging.getLogger(__name__)


async def upsert_players(
    db: AsyncSession,
    headers: list[str],
    rows: list[list],
) -> tuple[int, int]:
    """Создаёт или обновляет игроков из статистики NBA API.
    
    Возвращает (count_new, count_updated).
    """
    count_new = 0
    count_updated = 0

    for row in rows:
        player_data = dict(zip(headers, row))

        player_id = player_data.get("PLAYER_ID")
        if not player_id:
            continue

        team_abbr = player_data.get("TEAM_ABBREVIATION", "UNK")
        games_played = int(player_data.get("GP", 0))
        if games_played == 0:
            continue

        try:
            pts = float(player_data.get("PTS", 0))
            reb = float(player_data.get("REB", 0))
            ast = float(player_data.get("AST", 0))
            stl = float(player_data.get("STL", 0))
            blk = float(player_data.get("BLK", 0))
            fg_pct = float(player_data.get("FG_PCT", 0)) if player_data.get("FG_PCT") else 0.0
            fg3_pct = float(player_data.get("FG3_PCT", 0)) if player_data.get("FG3_PCT") else 0.0
            ft_pct = float(player_data.get("FT_PCT", 0)) if player_data.get("FT_PCT") else 0.0
            mins = float(player_data.get("MIN", 0)) if player_data.get("MIN") else 0.0
        except (ValueError, TypeError):
            continue

        name = player_data.get("PLAYER_NAME", "Unknown")

        existing = await db.execute(select(Player).where(Player.nba_id == int(player_id)))
        player = existing.scalar_one_or_none()

        if not player:
            db.add(Player(
                nba_id=int(player_id),
                name=name,
                team_abbr=team_abbr,
                position="N/A",
                jersey_number=None,
                games_played=games_played,
                pts=pts, reb=reb, ast=ast, stl=stl, blk=blk,
                fg_pct=fg_pct, fg3_pct=fg3_pct, ft_pct=ft_pct,
                mins=mins,
                recent_games=games_played,
            ))
            count_new += 1
        else:
            player.team_abbr = team_abbr
            # position / jersey_number НЕ трогаем: LeagueDashPlayerStats их не
            # отдаёт. Эти поля наполняются через backfill_positions.py.
            player.games_played = games_played
            player.pts = pts
            player.reb = reb
            player.ast = ast
            player.stl = stl
            player.blk = blk
            player.fg_pct = fg_pct
            player.fg3_pct = fg3_pct
            player.ft_pct = ft_pct
            player.mins = mins
            player.recent_games = games_played
            count_updated += 1

    await db.commit()
    return count_new, count_updated
