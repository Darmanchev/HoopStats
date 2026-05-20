from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload  # ← НОВОЕ
from ..database import get_db
from ..models.player import Player
from ..schemas.player import PlayerSchema, PlayerDetailSchema
router = APIRouter(prefix="/players", tags=["players"])
@router.get("/", response_model=list[PlayerSchema])
async def get_players(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    sort_by: str = Query("pts", pattern="^(pts|reb|ast|games_played|name)$"),
    team: str | None = None,
    position: str | None = None,
    min_games: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
):
    query = select(Player).where(Player.games_played >= min_games)
    if team:
        query = query.where(Player.team_abbr == team.upper())
    if position:
        query = query.where(Player.position == position.upper())
    sort_map = {
        "pts": Player.pts.desc(),
        "reb": Player.reb.desc(),
        "ast": Player.ast.desc(),
        "games_played": Player.games_played.desc(),
        "name": Player.name.asc(),
    }
    query = query.order_by(sort_map.get(sort_by, Player.pts.desc())).offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
@router.get("/{player_id}", response_model=PlayerDetailSchema)
async def get_player(player_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Player)
        .options(selectinload(Player.team))  # ← eagerly load team
        .where(Player.id == player_id)
    )
    player = result.scalar_one_or_none()
    if not player:
        return None
    return PlayerDetailSchema(
        id=player.id,
        nba_id=player.nba_id,
        name=player.name,
        team_abbr=player.team_abbr,
        position=player.position,
        jersey_number=player.jersey_number,
        games_played=player.games_played,
        pts=player.pts,
        reb=player.reb,
        ast=player.ast,
        stl=player.stl,
        blk=player.blk,
        fg_pct=player.fg_pct,
        fg3_pct=player.fg3_pct,
        ft_pct=player.ft_pct,
        mins=player.mins,
        recent_games=player.recent_games,
        team_name=player.team.name if player.team else None,
        team_city=player.team.city if player.team else None,
        team_color=player.team.color if player.team else None,
        team_accent=player.team.accent if player.team else None,
    )